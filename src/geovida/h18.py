"""H18: segmentador y certificado calibrados con ecografía real, validados en embriones no vistos.

Aplica ``docs/PREREGISTRO_H18.md``. H11 y H12R mostraron que el límite no era la calibración sino el
segmentador: con los umbrales de geovida ningún caso de cuerpo quedó a menos de 58 % de la referencia,
así que cualquier modelo calibrado con esos datos daría cero luces verdes. H18 hace, en este orden:

1. ``split_cases``: reparto de los autores del conjunto (``nii_train`` / ``nii_test``) **por embrión**:
   un embrión con casos en las dos carpetas va entero a entrenamiento.
2. ``smooth_lcc`` y ``GRID``: una familia fija de segmentadores (suavizado, Otsu escalado, componente
   mayor, cierre, relleno). Se elige uno solo con el entrenamiento (``select_config``).
3. ``fit_certificate`` y ``feasibility_gate``: modelo de Pr(|error| ≤ 10 %) y envolvente de dominio con
   el entrenamiento; puerta de viabilidad con predicciones fuera de pliegue (pliegues por embrión).
4. ``freeze`` / ``check_frozen``: el certificado se congela y su SHA-256 se anota en el preregistro
   **antes** de abrir la prueba; la prueba se niega a correr con otro archivo.
5. ``evaluate_test``: veredicto primario H18b sobre los embriones de prueba.

La referencia es un contorno humano: se mide acuerdo. Solo investigación con datos animales; sin uso
clínico.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from skimage.filters import threshold_otsu

from .analysis import fit_logit_multi, predict_logit_multi
from .budget import GREEN, RED, traffic_light
from .domain import DOMAIN_COLUMNS, domain_observables

SEED = 20261120
N_BOOT = 2000
N_FOLDS = 5
TOLERANCE = 0.10
MIN_GREEN = 20                 # prueba: unos 44 casos; ver §5 del preregistro
MIN_EMBRYOS_GREEN = 15
FEATURES = ("ln_d_over_hgeo", "ln_snr_hat", "ln_edge_width")
RIDGE = 1.0
ENVELOPE_QUANTILES = (0.01, 0.99)
GRID = tuple({"sigma": s, "thr": t, "close": c}
             for s in (1.0, 2.0, 4.0) for t in (0.9, 1.0, 1.1) for c in (0, 3))
SPLITS = {"nii_train": "train", "nii_test": "test"}


# --- 1. Reparto por embrión -------------------------------------------------------------------------
def split_cases(manifest: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Columna ``split`` desde la primera carpeta de ``image``; los embriones con casos en las dos
    carpetas pasan enteros a ``train`` (nunca el mismo embrión a ambos lados)."""
    df = manifest.copy()
    folder = df["image"].astype(str).str.replace("\\", "/", regex=False).str.split("/").str[0]
    unknown = sorted(set(folder) - set(SPLITS))
    if unknown:
        raise ValueError(f"carpetas sin reparto conocido: {unknown}")
    df["split"] = folder.map(SPLITS)
    both = set(df.loc[df["split"] == "train", "embryo_id"]) & set(df.loc[df["split"] == "test", "embryo_id"])
    moved = int(((df["split"] == "test") & df["embryo_id"].isin(both)).sum())
    df.loc[df["embryo_id"].isin(both), "split"] = "train"
    report = {"embryos_in_both": sorted(both), "test_cases_moved_to_train": moved,
              **{f"{s}_cases": int((df["split"] == s).sum()) for s in ("train", "test")},
              **{f"{s}_embryos": int(df.loc[df["split"] == s, "embryo_id"].nunique()) for s in ("train", "test")}}
    return df, report


# --- 2. Segmentadores --------------------------------------------------------------------------------
def _ball(radius: int) -> np.ndarray:
    r = int(radius)
    zz, yy, xx = np.mgrid[-r:r + 1, -r:r + 1, -r:r + 1]
    return (zz ** 2 + yy ** 2 + xx ** 2) <= r * r


def smooth_lcc(image: np.ndarray, spacing, sigma: float, thr: float, close: int,
               smoothed: np.ndarray | None = None) -> np.ndarray:
    """Suavizado gaussiano (``sigma`` en vóxeles del eje más fino) → umbral ``thr`` × Otsu →
    componente mayor (26-conectividad) → cierre con bola de radio ``close`` vóxeles → relleno de huecos.

    A diferencia de los segmentadores preregistrados de H1, **sí** limpia: el moteado de la ecografía
    deja miles de islas por encima del umbral, que inflan el volumen. Precio: un hueco real del embrión
    (p. ej. una cavidad) se rellena; por eso la topología no se evalúa con este segmentador.
    """
    sp = np.asarray(spacing, dtype=float)
    sm = smoothed if smoothed is not None else ndi.gaussian_filter(
        np.asarray(image, np.float32), sigma=sigma * sp.min() / sp)
    mask = sm >= thr * float(threshold_otsu(sm))
    lab, n = ndi.label(mask, structure=np.ones((3, 3, 3), dtype=bool))
    if n == 0:
        return mask
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    mask = lab == int(sizes.argmax())
    del lab
    if close > 0:
        pad = int(close)
        mask = ndi.binary_closing(np.pad(mask, pad), structure=_ball(close))[pad:-pad, pad:-pad, pad:-pad]
    return ndi.binary_fill_holes(mask)


def grid_rows(image: np.ndarray, spacing, ref: np.ndarray, grid=GRID) -> list[dict]:
    """Error de volumen y Dice de cada configuración de ``grid`` (barato: sin observables)."""
    sp = np.asarray(spacing, dtype=float)
    v_ref = float(ref.sum())
    rows, cache = [], {}
    for cfg in grid:
        if cfg["sigma"] not in cache:
            cache.clear()
            cache[cfg["sigma"]] = ndi.gaussian_filter(np.asarray(image, np.float32),
                                                      sigma=cfg["sigma"] * sp.min() / sp)
        m = smooth_lcc(image, spacing, **cfg, smoothed=cache[cfg["sigma"]])
        v = float(m.sum())
        inter = float(np.logical_and(m, ref).sum())
        rows.append({**cfg, "rel_error_volume": (v - v_ref) / v_ref, "dice": 2 * inter / (v + v_ref)})
    return rows


def config_key(cfg: dict) -> str:
    return f"s{cfg['sigma']:g}_t{cfg['thr']:g}_c{int(cfg['close'])}"


def select_config(table: pd.DataFrame) -> dict:
    """La configuración con más casos de entrenamiento a ≤ 10 % de la referencia. Desempates, en este
    orden: mayor Dice mediano, menor ``sigma``, ``thr`` más cerca de 1, menor ``close``."""
    g = table.assign(ok10=table["rel_error_volume"].abs() <= TOLERANCE).groupby(["sigma", "thr", "close"])
    s = g.agg(ok10=("ok10", "mean"), dice=("dice", "median")).reset_index()
    s["thr_dist"] = (s["thr"] - 1.0).abs()
    s = s.sort_values(["ok10", "dice", "sigma", "thr_dist", "close"],
                      ascending=[False, False, True, True, True], kind="mergesort")
    best = s.iloc[0]
    return {"sigma": float(best["sigma"]), "thr": float(best["thr"]), "close": int(best["close"]),
            "train_ok10": float(best["ok10"]), "train_dice_median": float(best["dice"])}


# --- 3. Certificado ----------------------------------------------------------------------------------
def observables(image: np.ndarray, spacing, mask: np.ndarray) -> dict:
    """Los índices de la guardia (``snr_hat``, ``edge_width``) y ``d_over_hgeo`` de una máscara."""
    from .budget import h_geo
    from .measure import _area_sdf, _mean_depth

    sp = tuple(float(s) for s in spacing)
    if not mask.any():
        return {"d_over_hgeo": math.nan, "snr_hat": math.nan, "edge_width": math.nan}
    area = float(_area_sdf(mask, sp))
    return {"d_over_hgeo": float(_mean_depth(mask, sp) / h_geo(sp)), **domain_observables(image, mask, sp, area)}


def feature_matrix(df: pd.DataFrame) -> np.ndarray:
    cols = [np.log(df[c.removeprefix("ln_")].to_numpy(float)) for c in FEATURES]
    return np.column_stack(cols)


def fit_envelope(df: pd.DataFrame) -> dict:
    return {c: [float(df[c].quantile(ENVELOPE_QUANTILES[0])), float(df[c].quantile(ENVELOPE_QUANTILES[1]))]
            for c in DOMAIN_COLUMNS}


def inside(df: pd.DataFrame, env: dict) -> np.ndarray:
    ok = np.ones(len(df), dtype=bool)
    for c in DOMAIN_COLUMNS:
        v = df[c].to_numpy(float)
        ok &= np.isfinite(v) & (v >= env[c][0] - 1e-12) & (v <= env[c][1] + 1e-12)
    return ok


def fit_certificate(df: pd.DataFrame) -> dict:
    """Logit Pr(|error| ≤ 10 %) sobre ``FEATURES`` y envolvente de dominio, con las filas dadas."""
    X = feature_matrix(df)
    good = np.isfinite(X).all(axis=1)
    y = (df["rel_error_volume"].abs() <= TOLERANCE).to_numpy(float)
    model = fit_logit_multi(X[good], y[good], ridge=RIDGE, features=FEATURES)
    return {"model": model, "envelope": fit_envelope(df[good]), "n_train": int(good.sum())}


def lights(df: pd.DataFrame, cert: dict) -> pd.DataFrame:
    """Probabilidad, dominio y luz (con y sin guardia) de cada fila."""
    X = feature_matrix(df)
    good = np.isfinite(X).all(axis=1)
    p = np.zeros(len(df))
    if good.any():
        p[good] = predict_logit_multi(cert["model"], X[good])
    dom = inside(df, cert["envelope"]) & good
    free = np.array([traffic_light(float(v)) for v in p])
    guarded = np.where((free == "verde") & ~dom, "amarillo", free)
    return df.assign(p_ok10=p, in_domain=dom, light_without_guard=free, light=guarded)


def embryo_folds(embryos, n_folds: int = N_FOLDS, seed: int = SEED) -> dict:
    """Pliegue de cada embrión: permutación con semilla fija, repartida en ``n_folds`` grupos."""
    uniq = sorted(set(embryos))
    order = np.random.default_rng(seed).permutation(len(uniq))
    return {uniq[i]: int(k % n_folds) for k, i in enumerate(order)}


def out_of_fold(df: pd.DataFrame, n_folds: int = N_FOLDS, seed: int = SEED) -> pd.DataFrame:
    """Luces de cada fila de entrenamiento con un certificado ajustado sin su embrión."""
    fold = df["embryo_id"].map(embryo_folds(df["embryo_id"], n_folds, seed))
    parts = []
    for k in range(n_folds):
        held = fold == k
        if not held.any():
            continue
        parts.append(lights(df[held], fit_certificate(df[~held])))
    return pd.concat(parts).loc[df.index]


def _bootstrap(df: pd.DataFrame, bad: np.ndarray, n_boot: int, seed: int) -> list[float]:
    g = pd.DataFrame({"e": df["embryo_id"].to_numpy(), "bad": bad.astype(float)}).groupby("e")["bad"]
    s, c = g.sum().to_numpy(float), g.count().to_numpy(float)
    idx = np.random.default_rng(seed).integers(0, len(s), size=(n_boot, len(s)))
    lo, hi = np.percentile(s[idx].sum(axis=1) / c[idx].sum(axis=1), [2.5, 97.5])
    return [float(lo), float(hi)]


def green_failure(df: pd.DataFrame, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """Entre las filas con luz verde (con guardia): fracción con |error| > 10 %, IC por embrión y
    veredicto con las reglas de H11b y los mínimos de H18."""
    green = df[df["light"] == "verde"]
    out = {"n_green": int(len(green)), "n_embryos_green": int(green["embryo_id"].nunique())}
    if out["n_green"] < MIN_GREEN or out["n_embryos_green"] < MIN_EMBRYOS_GREEN:
        return {**out, "estimate": None, "ci": None, "verdict": "no evaluable"}
    bad = (green["rel_error_volume"].abs() > TOLERANCE).to_numpy()
    est, ci = float(bad.mean()), _bootstrap(green, bad, n_boot, seed)
    verdict = "apoyada" if est <= TOLERANCE else ("no apoyada" if ci[0] > TOLERANCE else "no concluyente")
    return {**out, "estimate": est, "ci": ci, "verdict": verdict}


def feasibility_gate(train: pd.DataFrame, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """Puerta F: con predicciones fuera de pliegue, H18b sería «apoyada» en el propio entrenamiento.
    Si no, la prueba **no se abre** y H18 queda «no evaluable por diseño»."""
    oof = out_of_fold(train)
    res = green_failure(oof, n_boot, seed)
    return {**res, "passed": res["verdict"] == "apoyada"}


# --- 4. Congelar y comprobar ------------------------------------------------------------------------
def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def freeze(path, config: dict, cert: dict, extra: dict) -> str:
    """Escribe el certificado congelado y devuelve su SHA-256 (que se anota en el preregistro)."""
    payload = {"study": "H18", "segmenter": "smooth_lcc", "config": config, **cert,
               "thresholds": {"green": GREEN, "red": RED, "tolerance": TOLERANCE}, **extra}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes((json.dumps(payload, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    return sha256_file(path)


def check_frozen(path, expected_sha: str) -> dict:
    """Carga el congelado solo si su SHA-256 es el anotado. Sin esto la prueba no se abre."""
    found = sha256_file(path)
    if not expected_sha or found != expected_sha.lower():
        raise PermissionError(f"el congelado {path} tiene SHA-256 {found}; el preregistro anota {expected_sha!r}")
    return json.loads(Path(path).read_text(encoding="utf-8"))


# --- 5. Prueba ---------------------------------------------------------------------------------------
def evaluate_test(test: pd.DataFrame, frozen: dict, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """H18b (primaria), H18a (cobertura), H18c (acuerdo) y H18d (guardia) en los embriones de prueba."""
    cert = {"model": frozen["model"], "envelope": frozen["envelope"]}
    lit = lights(test, cert)
    err = lit["rel_error_volume"].abs()
    free = lit[lit["light_without_guard"] == "verde"]
    return {
        "n_cases": int(len(lit)), "n_embryos": int(lit["embryo_id"].nunique()),
        "h18b": green_failure(lit, n_boot, seed),
        "h18a": {"green_fraction": float((lit["light"] == "verde").mean()) if len(lit) else math.nan,
                 "lights": lit["light"].value_counts().to_dict()},
        "h18c": {"dice_median": float(lit["dice"].median()), "abs_error_median": float(err.median()),
                 "ok10": float((err <= TOLERANCE).mean()), "ok5": float((err <= 0.05).mean())},
        "h18d": {"in_domain": float(lit["in_domain"].mean()),
                 "green_without_guard": int(len(free)),
                 "green_without_guard_bad": int((free["rel_error_volume"].abs() > TOLERANCE).sum())},
        "rows": lit,
    }
