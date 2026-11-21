"""Análisis del preregistro P3 (``docs/PREREGISTRO_P3.md``, §4–§6): variación técnica frente a la del espécimen.

Qué hace
--------
* ``select_specimens``: muestreo reproducible (semilla fija) del piloto y del confirmatorio a partir de los
  metadatos de MusMorph, equilibrado por sexo y con prefijo estable (ampliar de 60 a 120 conserva los 60).
* ``degrade_mask``: degrada una máscara por un factor *k* (fracción de ocupación por bloques, umbral 0,5).
* ``condition_table``: mide cada estructura en cada condición técnica (segmentador × factor de resolución).
* ``technical_fraction``: fracción técnica τ por estructura (varianza dentro del espécimen frente a la varianza
  entre especímenes de su media).
* ``groups_from_atlas``: grupos «delgada» y «compacta» fijados sobre el atlas, antes de ver datos de especímenes.
* ``evaluate``: H-P3a (Δ de medianas de τ entre grupos) y H-P3b (el certificado frente al tamaño), con
  intervalos por remuestreo de especímenes y veredictos según los criterios preregistrados.
* ``label_variation``: comprobación previa de que las segmentaciones no están todas en el espacio del atlas.
* ``mixed_technical_fraction`` y ``order_agreement``: sensibilidad de §5.4 (modelo mixto) y comparación de
  órdenes de estructuras (también para la regla ``exact`` de D1).
* ``agreement_rows``: acuerdo entre segmentadores a resolución nativa (§5.8; con o sin la traslación de D3).

Qué NO hace
-----------
No descarga datos, no ejecuta MEMOS y no lee archivos: recibe arreglos ya cargados (p. ej. con
``geovida.minc.load_minc``). La degradación de resolución es simulada sobre la máscara; no equivale a reescanear.
Ninguno de los dos segmentadores de P3 es una verdad anatómica. Solo investigación y educación.
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Mapping

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from .budget import feature_value, p_volume_ok
from .measure import _area_sdf, _mean_depth
from .scaleaxis import block_mean

FACTORS = (1, 2, 4)
SAMPLE_SEED = 20261114
BOOT_SEED = 20261115
N_BOOT = 2000
MIN_UNITS_PER_GROUP = 8
CERT_SEGMENTER = "otsu"       # modelos congelados de v0.4, sin recalibrar (§5.7)
CERT_PROFILE = "realistic"
GROUP_THIN, GROUP_COMPACT = "delgada", "compacta"


# --------------------------------------------------------------------------- muestreo (§4)

def select_specimens(meta: pd.DataFrame, *, seed: int = SAMPLE_SEED, n_pilot: int = 20,
                     n_confirm: int = 60, exclude: Iterable[str] = ()) -> dict:
    """Piloto y confirmatorio disjuntos, mitad hembras y mitad machos, entre silvestres E15.5 del IMPC.

    Cada sexo se ordena por identificador y se permuta con ``seed``; el piloto toma el principio de la
    permutación y el confirmatorio lo siguiente. Por eso ampliar ``n_confirm`` conserva los ya elegidos.
    """
    if n_pilot % 2 or n_confirm % 2:
        raise ValueError("n_pilot y n_confirm deben ser pares (mitad por sexo)")
    excl = set(map(str, exclude))
    ok = meta[(meta["Stage"] == "E15.5") & (meta["Dataset"] == "IMPC")
              & (meta["Zygosity"] == "Wildtype") & meta["Sex"].isin(["F", "M"])]
    ok = ok[~ok["Biosample"].astype(str).isin(excl)]
    rng = np.random.default_rng(seed)
    pilot, confirm = [], []
    hp, hc = n_pilot // 2, n_confirm // 2
    for sex in ("F", "M"):
        ids = sorted(ok.loc[ok["Sex"] == sex, "Biosample"].astype(str))
        if len(ids) < hp + hc:
            raise ValueError(f"solo {len(ids)} elegibles de sexo {sex}; hacen falta {hp + hc}")
        perm = [ids[i] for i in rng.permutation(len(ids))]
        pilot += perm[:hp]
        confirm += perm[hp:hp + hc]
    return {"pilot": pilot, "confirm": confirm, "n_eligible": int(len(ok)), "seed": seed}


# --------------------------------------------------------------------------- medición (§5.1–5.2)

def degrade_mask(mask, k: int) -> np.ndarray:
    """Máscara a resolución 1/k: fracción de ocupación por bloques k×k×k (con relleno al final) y umbral 0,5."""
    m = np.asarray(mask, dtype=bool)
    if k < 1 or k & (k - 1):
        raise ValueError(f"k debe ser una potencia de 2, no {k}")
    if k == 1:
        return m.copy()
    f = np.pad(m, [(0, (-s) % k) for s in m.shape]).astype(np.float32)
    while k > 1:
        f = block_mean(f)
        k //= 2
    return f >= 0.5


def _aligned_box(mask: np.ndarray, block: int = max(FACTORS), margin: int = 1):
    """Caja alrededor de la máscara alineada con la rejilla de bloques del volumen completo."""
    idx = np.nonzero(mask)
    if not idx[0].size:
        return None
    box = []
    for ax, ii in enumerate(idx):
        lo = max(0, (int(ii.min()) // block - margin) * block)
        hi = min(mask.shape[ax], (int(ii.max()) // block + 1 + margin) * block)
        box.append(slice(lo, hi))
    return tuple(box)


def label_boxes(lab: np.ndarray, labels: Iterable[int], block: int = max(FACTORS), margin: int = 1) -> dict:
    """``_aligned_box(lab == s)`` para todas las etiquetas a la vez, con una sola pasada (``ndimage.find_objects``).

    Evita crear una máscara del volumen completo por estructura: en especímenes de 10⁸ vóxeles y 4 GB de RAM,
    eso obligaba a paginar. Devuelve {etiqueta: caja o None}; las cajas son idénticas a las de ``_aligned_box``.
    """
    from scipy import ndimage as ndi

    lab = np.asarray(lab)
    if lab.dtype.kind not in "iu":
        raise ValueError("el mapa de etiquetas debe ser entero")
    labels = [int(s) for s in labels]
    top = max([s for s in labels if s > 0] or [0])
    objs = ndi.find_objects(lab, max_label=top) if top else []  # las etiquetas > top se ignoran
    out = {}
    for s in labels:
        sl = objs[s - 1] if 0 < s <= len(objs) else None
        if sl is None:
            out[s] = None
            continue
        box = []
        for ax, d in enumerate(sl):
            lo = max(0, (d.start // block - margin) * block)
            hi = min(lab.shape[ax], ((d.stop - 1) // block + 1 + margin) * block)
            box.append(slice(lo, hi))
        out[s] = tuple(box)
    return out


def p3_measure(mask, spacing, depth: bool = False) -> dict:
    """Solo las medidas que usa P3: volumen, ``area_sdf``, b0 (conectividad 26) y, si ``depth``, ``d_mean``.

    Da exactamente los mismos valores que ``measure_mask`` para esas claves (lo comprueba una prueba), sin
    calcular ``area_mc``, ``area_faces`` ni la topología completa, que P3 no usa y que en 4 GB de RAM triplicaban
    el tiempo por espécimen.
    """
    from scipy import ndimage as ndi

    mask = np.asarray(mask, dtype=bool)
    sp = np.asarray(spacing, dtype=float)
    out = {"volume": float(mask.sum() * np.prod(sp))}
    if not mask.any():
        out.update(area_sdf=0.0, b0_26=0, d_mean=0.0)
        return out
    out["area_sdf"] = _area_sdf(mask, sp)
    out["b0_26"] = int(ndi.label(mask, structure=ndi.generate_binary_structure(3, 3))[1])
    if depth:
        out["d_mean"] = _mean_depth(mask, sp)
    return out


def specimen_rows(specimen, labelmaps: Mapping[str, np.ndarray], spacing, labels: Iterable[int],
                  factors=FACTORS, cert_segmenter: str | None = None) -> list[dict]:
    """Filas de medida de un espécimen: una por segmentador × estructura × factor."""
    sp = np.asarray(spacing, dtype=float)
    if len({np.shape(v) for v in labelmaps.values()}) != 1:
        raise ValueError(f"{specimen}: los mapas de etiquetas no tienen la misma forma")
    if cert_segmenter is None:
        cert_segmenter = next(iter(labelmaps))
    labels = [int(s) for s in labels]
    rows = []
    for seg, lab in labelmaps.items():
        lab = np.asarray(lab)
        boxes = label_boxes(lab, labels)
        for s in labels:
            box = boxes[s]
            crop = None if box is None else lab[box] == s
            for k in factors:
                if box is None:
                    meas = {"volume": 0.0, "area_sdf": 0.0, "b0_26": 0}
                else:
                    meas = p3_measure(degrade_mask(crop, k), sp * k, depth=(seg == cert_segmenter and k == 1))
                v = float(meas["volume"])
                row = {"specimen": str(specimen), "structure": s, "segmenter": str(seg), "factor": int(k),
                       "volume": v, "log_volume": math.log(v) if v > 0 else math.nan,
                       "area_sdf": float(meas["area_sdf"]), "b0": int(meas["b0_26"]), "p_cert": math.nan}
                if seg == cert_segmenter and k == 1 and box is not None:
                    row["p_cert"] = p_volume_ok(feature_value(meas, sp), CERT_SEGMENTER, CERT_PROFILE)
                rows.append(row)
    return rows


def condition_table(items: Iterable, labels: Iterable[int], factors=FACTORS,
                    cert_segmenter: str | None = None) -> pd.DataFrame:
    """Tabla de condiciones. ``items``: iterable de (espécimen, {segmentador: mapa de etiquetas}, vóxel en mm).

    Acepta un generador, para cargar un espécimen cada vez.
    """
    labels = [int(s) for s in labels]
    rows: list[dict] = []
    for specimen, labelmaps, spacing in items:
        rows += specimen_rows(specimen, labelmaps, spacing, labels, factors, cert_segmenter)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- τ (§5.3)

def _matrices(df: pd.DataFrame, value: str):
    specs = sorted(df["specimen"].astype(str).unique())
    conds = sorted(set(zip(df["segmenter"], df["factor"])))
    cols = pd.MultiIndex.from_tuples(conds, names=["segmenter", "factor"])
    mats = {}
    for s, g in df.groupby("structure"):
        w = g.pivot_table(index="specimen", columns=["segmenter", "factor"], values=value, aggfunc="first")
        mats[int(s)] = w.reindex(index=specs, columns=cols).to_numpy(dtype=float)
    return specs, conds, mats


def _tau(mat: np.ndarray) -> tuple[float, float, float, int]:
    """(τ, varianza dentro, varianza entre, n) usando solo especímenes con las condiciones completas."""
    m = mat[~np.isnan(mat).any(axis=1)]
    n = int(m.shape[0])
    if n < 2 or m.shape[1] < 2:
        return math.nan, math.nan, math.nan, n
    within = float(m.var(axis=1, ddof=1).mean())
    between = float(m.mean(axis=1).var(ddof=1))
    tot = within + between
    return (within / tot if tot > 0 else math.nan), within, between, n


def technical_fraction(df: pd.DataFrame, value: str = "log_volume") -> pd.DataFrame:
    """τ_s = media_i Var_c(y) / [media_i Var_c(y) + Var_i(media_c y)] por estructura.

    Un espécimen al que le falta alguna condición (p. ej. la estructura desaparece a ×4 y su logaritmo no
    existe) se excluye de esa estructura y se cuenta en ``n_dropped``.
    """
    specs, _, mats = _matrices(df, value)
    out = []
    for s in sorted(mats):
        tau, within, between, n = _tau(mats[s])
        out.append({"structure": s, "tau": tau, "within": within, "between": between,
                    "n_specimens": n, "n_dropped": len(specs) - n})
    return pd.DataFrame(out)


# --------------------------------------------------------------------------- grupos (§5.6)

def groups_from_atlas(atlas, spacing, labels: Iterable[int], units: Mapping[int, str] | None = None) -> pd.DataFrame:
    """Profundidad media interior (``d_mean / h_geo``) y volumen de cada unidad sobre el atlas.

    ``units`` agrupa etiquetas (p. ej. izquierda y derecha) en una unidad; sin él, cada etiqueta es su unidad.
    Las unidades por debajo de la mediana de ``d_mean / h_geo`` son «delgada»; las demás, «compacta».
    """
    sp = np.asarray(spacing, dtype=float)
    lab = np.asarray(atlas)
    units = dict(units or {})
    per: dict[str, list[tuple[float, float]]] = {}
    for s in labels:
        m = lab == int(s)
        if not m.any():
            continue
        sub = m[_aligned_box(m)]
        del m
        # Solo hacen falta volumen y d_mean: se evitan área y topología (memoria en atlas grandes).
        meas = {"volume": float(sub.sum() * np.prod(sp)), "d_mean": _mean_depth(sub, sp)}
        del sub
        per.setdefault(units.get(int(s), str(int(s))), []).append((feature_value(meas, sp), meas["volume"]))
    rows = [{"unit": u, "d_over_hgeo": float(np.mean([d for d, _ in v])),
             "log_volume": float(np.log(np.mean([vol for _, vol in v])))} for u, v in per.items()]
    out = pd.DataFrame(rows)
    if out.empty:
        return out.assign(group=pd.Series(dtype=str))
    med = out["d_over_hgeo"].median()
    out["group"] = np.where(out["d_over_hgeo"] < med, GROUP_THIN, GROUP_COMPACT)
    return out


# --------------------------------------------------------------------------- evaluación (§6)

def _finite(a) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    return a[np.isfinite(a)]


def _mean(a) -> float:
    f = _finite(a)
    return float(f.mean()) if f.size else math.nan


def _median(a) -> float:
    f = _finite(a)
    return float(np.median(f)) if f.size else math.nan


def _corr(x, y) -> float:
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.size < 3 or np.ptp(x) == 0 or np.ptp(y) == 0:
        return math.nan
    return float(np.corrcoef(x, y)[0, 1])


def spearman(x, y) -> float:
    """ρ de Spearman (NaN si hay menos de 3 puntos o una variable es constante)."""
    return _corr(rankdata(x), rankdata(y))


def partial_spearman(x, y, z) -> float:
    """Correlación parcial de rangos de x e y controlando z."""
    rx, ry, rz = rankdata(x), rankdata(y), rankdata(z)
    rxy, rxz, ryz = _corr(rx, ry), _corr(rx, rz), _corr(ry, rz)
    den = (1 - rxz ** 2) * (1 - ryz ** 2)
    if not all(math.isfinite(v) for v in (rxy, rxz, ryz)) or den <= 0:
        return math.nan
    return float((rxy - rxz * ryz) / math.sqrt(den))


def _ci(values) -> tuple[float, float]:
    f = _finite(values)
    if not f.size:
        return math.nan, math.nan
    return float(np.percentile(f, 2.5)), float(np.percentile(f, 97.5))


def _p_matrix(df: pd.DataFrame, specs, structs) -> np.ndarray:
    sub = df[np.isfinite(df["p_cert"].astype(float))]
    if sub.empty:
        return np.full((len(specs), len(structs)), np.nan)
    w = sub.pivot_table(index="specimen", columns="structure", values="p_cert", aggfunc="first")
    return w.reindex(index=specs, columns=structs).to_numpy(dtype=float)


def evaluate(df: pd.DataFrame, groups: pd.DataFrame, units: Mapping[int, str] | None = None,
             value: str = "log_volume", n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> dict:
    """H-P3a y H-P3b con remuestreo de especímenes (los mismos índices para todas las estructuras)."""
    specs, _, mats = _matrices(df, value)
    structs = sorted(mats)
    units = dict(units or {})
    unit_of = {s: units.get(s, str(s)) for s in structs}
    g = groups.set_index("unit")
    unit_names = [u for u in dict.fromkeys(unit_of[s] for s in structs) if u in g.index]
    members = {u: [j for j, s in enumerate(structs) if unit_of[s] == u] for u in unit_names}
    group_of = {u: g.at[u, "group"] for u in unit_names}
    size_of = np.array([g.at[u, "log_volume"] for u in unit_names], dtype=float)
    pmat = _p_matrix(df, specs, structs)

    def stats(idx):
        taus = np.array([_tau(mats[s][idx])[0] for s in structs])
        pmed = np.array([_median(pmat[idx, j]) for j in range(len(structs))])
        tu = np.array([_mean(taus[members[u]]) for u in unit_names])
        pu = np.array([_mean(pmed[members[u]]) for u in unit_names])
        thin = _finite([t for t, u in zip(tu, unit_names) if group_of[u] == GROUP_THIN])
        comp = _finite([t for t, u in zip(tu, unit_names) if group_of[u] == GROUP_COMPACT])
        delta = (float(np.median(thin) - np.median(comp))
                 if thin.size >= MIN_UNITS_PER_GROUP and comp.size >= MIN_UNITS_PER_GROUP else math.nan)
        ok = np.isfinite(tu) & np.isfinite(pu) & np.isfinite(size_of)
        rho = spearman(pu[ok], tu[ok])
        rho_p = partial_spearman(pu[ok], tu[ok], size_of[ok])
        return tu, pu, delta, rho, rho_p, (int(thin.size), int(comp.size)), int(ok.sum())

    n = len(specs)
    tu, pu, delta, rho, rho_p, counts, n_ok = stats(np.arange(n))
    rng = np.random.default_rng(seed)
    boot_d, boot_rp = [], []
    for _ in range(n_boot):
        _, _, d, _, rp, _, _ = stats(rng.integers(0, n, n))
        boot_d.append(d)
        boot_rp.append(rp)
    d_lo, d_hi = _ci(boot_d)
    rp_lo, rp_hi = _ci(boot_rp)

    if min(counts) < MIN_UNITS_PER_GROUP or not math.isfinite(d_lo):
        verdict_a = "no_evaluable"
    elif delta > 0 and d_lo > 0:
        verdict_a = "apoyada"
    elif d_hi < 0:
        verdict_a = "contraria"
    else:
        verdict_a = "no_concluyente"

    if n_ok < 2 * MIN_UNITS_PER_GROUP or not (math.isfinite(rho) and math.isfinite(rp_hi)):
        verdict_b = "no_evaluable"
    elif rho <= -0.5 and rp_hi < 0:
        verdict_b = "apoyada"
    else:
        verdict_b = "no_apoyada"

    table = pd.DataFrame({"unit": unit_names, "group": [group_of[u] for u in unit_names], "tau": tu,
                          "p_median": pu, "log_volume_atlas": size_of})
    return {"units": table, "n_specimens": n, "n_boot": n_boot, "seed": seed, "value": value,
            "n_units": {GROUP_THIN: counts[0], GROUP_COMPACT: counts[1]},
            "delta": delta, "delta_ci": (d_lo, d_hi), "verdict_a": verdict_a,
            "rho": rho, "rho_partial": rho_p, "rho_partial_ci": (rp_lo, rp_hi), "verdict_b": verdict_b}


# --------------------------------------------------------------------------- comprobación previa (§3.2)

def label_variation(df: pd.DataFrame, segmenter: str, min_fraction: float = 0.9) -> dict:
    """Fracción de estructuras cuyo volumen nativo varía entre especímenes (CV > 0)."""
    sub = df[(df["segmenter"] == segmenter) & (df["factor"] == 1) & (df["volume"] > 0)]
    cv = sub.groupby("structure")["volume"].agg(
        lambda v: float(v.std(ddof=1) / v.mean()) if len(v) > 1 and v.mean() > 0 else 0.0)
    frac = float((cv > 0).mean()) if len(cv) else 0.0
    return {"fraction_varying": frac, "passed": bool(frac >= min_fraction), "n_structures": int(len(cv))}


# --------------------------------------------------------------------------- sensibilidad (§5.4)

ORDER_AGREEMENT_MIN = 0.7  # §5.4 y D1: ρ de Spearman mínimo entre dos órdenes de estructuras por τ


def mixed_technical_fraction(df: pd.DataFrame, value: str = "log_volume") -> pd.DataFrame:
    """§5.4: modelo mixto ``y ~ C(k) * C(segmentador) + (1 | espécimen)`` por estructura (statsmodels MixedLM, REML).

    Fracción técnica del modelo = (varianza entre condiciones de las predicciones fijas + varianza residual) /
    (eso + varianza del intercepto del espécimen). Usa los mismos especímenes que τ (condiciones completas).
    Es la contrapartida de τ con un modelo; solo se compara su **orden** de estructuras con el de τ.
    """
    import warnings

    import statsmodels.formula.api as smf

    _, conds, mats = _matrices(df, value)
    out = []
    for s in sorted(mats):
        m = mats[s][~np.isnan(mats[s]).any(axis=1)]
        n = int(m.shape[0])
        row = {"structure": s, "tau_mixed": math.nan, "var_fixed": math.nan, "var_resid": math.nan,
               "var_specimen": math.nan, "converged": False, "n_specimens": n}
        if n >= 3 and len(conds) >= 2:
            long = pd.DataFrame({"y": m.ravel(), "spec": np.repeat(np.arange(n), len(conds)),
                                 "seg": [str(c[0]) for c in conds] * n, "k": [int(c[1]) for c in conds] * n})
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    fit = smf.mixedlm("y ~ C(k) * C(seg)", long, groups=long["spec"]).fit(reml=True)
                pred = fit.model.exog[: len(conds)] @ np.asarray(fit.fe_params)
                vf, vr = float(np.var(pred, ddof=1)), float(fit.scale)
                vs = float(np.asarray(fit.cov_re)[0, 0])
                tot = vf + vr + vs
                row.update(tau_mixed=(vf + vr) / tot if tot > 0 else math.nan, var_fixed=vf, var_resid=vr,
                           var_specimen=vs, converged=bool(fit.converged))
            except (ValueError, np.linalg.LinAlgError):
                pass
        out.append(row)
    return pd.DataFrame(out)


def order_agreement(a: pd.DataFrame, b: pd.DataFrame, col_a: str = "tau", col_b: str = "tau") -> dict:
    """ρ de Spearman entre dos columnas de τ por estructura (unidas por ``structure``) y si alcanza 0,7."""
    m = a[["structure", col_a]].merge(b[["structure", col_b]], on="structure", suffixes=("_a", "_b"))
    x = m.iloc[:, 1].to_numpy(dtype=float)
    y = m.iloc[:, 2].to_numpy(dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    rho = spearman(x[ok], y[ok]) if ok.sum() >= 3 else math.nan
    return {"rho": rho, "n_structures": int(ok.sum()),
            "agree": bool(math.isfinite(rho) and rho >= ORDER_AGREEMENT_MIN)}


# --------------------------------------------------------------------------- acuerdo entre segmentadores (§5.8)

def agreement_rows(specimen, ref_labels: np.ndarray, test_labels: np.ndarray, spacing, labels: Iterable[int],
                   translation=(0, 0, 0)) -> list[dict]:
    """§5.8 a resolución nativa: acuerdo de B (``test_labels``) con A (``ref_labels``) por estructura.

    ``translation`` es la traslación entera aplicada a A antes de comparar (D3, forma b); (0, 0, 0) es la forma a.
    El llamador debe dejar margen alrededor de las máscaras: ``np.roll`` recicla los bordes.
    """
    from .agreement import compare_masks

    t = tuple(int(v) for v in translation)
    ref = np.roll(ref_labels, t, (0, 1, 2)) if any(t) else ref_labels
    rows = []
    for s in (int(v) for v in labels):
        a, b = ref == s, test_labels == s
        box = _aligned_box(a | b, block=1, margin=2)
        row = {"specimen": str(specimen), "structure": s, "translation": list(t)}
        if box is None:
            row.update(dice=math.nan, hd95=math.nan, assd=math.nan, vol_diff_rel=math.nan)
        else:
            r = compare_masks(b[box], a[box], spacing=spacing)
            row.update(dice=r["dice"], hd95=r["hd95_pooled"], assd=r["assd"], vol_diff_rel=r["size_diff_rel"])
        rows.append(row)
    return rows
