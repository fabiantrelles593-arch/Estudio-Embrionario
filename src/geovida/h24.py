"""H24: luz de fiabilidad con la tolerancia medida en vóxeles de borde (docs/h24/PREREGISTRO_H24.md).

H23 mostró que, en ventrículos, una capa de un vóxel es el 42 % del volumen: una tolerancia del 10 % queda por debajo
de la resolución. H24 cambia la unidad del error, no la red:

* ``boundary_error``: e_b = |V_M − V_R| / A_R, el desplazamiento uniforme del borde (en vóxeles) que explica la
  diferencia de volumen. Fallo si e_b > 0,5 vóxeles (el límite de redondeo de la discretización).
* ``signals``: las señales de H20 divididas por la superficie de la propia máscara medida, A_M (sin la referencia):
  b_flip = (máx − mín de los 8 volteos) / A_M; b_stage = |V_etapa1 − V_0| / A_M.
* ``rule``: los umbrales de H20 en la misma proporción respecto de la tolerancia (½, 1, 2 y 3 veces 0,5 vóxeles).

Superficies con ``measure._area_sdf`` (el estimador que mantuvo H21) y espaciado (1, 1, 1). Las redes son las de H23,
congeladas por SHA-256. Solo investigación con datos animales publicados; sin uso clínico.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import h18, h19
from .measure import _area_sdf

STRUCTURE = "ventricle"
NETS_SHA256 = {"coarse": "fa7f52117ab5dab3a7918eb53c89b56228c6a71e5931dd57e729436a0ba90038",
               "fine": "fc3f4dfdf9170ea6113acc457d05c389f1fe699ec7479bb66b4299dd92be9cf2"}
TOL_VOXELS = 0.5                     # medio vóxel de borde (25 µm con vóxeles de 50 µm)
GREEN_FLIP = 0.5 * TOL_VOXELS        # H20: ½ · tolerancia
GREEN_STAGE = 1.0 * TOL_VOXELS       # H20: 1 · tolerancia
RED_FLIP = 2.0 * TOL_VOXELS          # H20: 2 · tolerancia
RED_STAGE = 3.0 * TOL_VOXELS         # H20: 3 · tolerancia
MAX_FAIL = 0.10                      # fracción de verdes que pueden fallar (H20b, H23b)
MIN_GREEN, MIN_EMBRYOS_GREEN = h18.MIN_GREEN, h18.MIN_EMBRYOS_GREEN     # 20 verdes en 15 embriones
MIN_GREEN_CAL, MAX_FAIL_CAL = h19.MIN_GREEN_CAL, h19.MAX_FAIL_CAL       # puerta C′: ≥ 10 verdes, ≤ 10 % fallan
S_MIN_OK = 0.50                      # puerta S′
SEP_NO_MAX = 0.05
SEP_MIN_EACH = 5
SEED_G0 = 20261126
N_G0 = 5
G0_MAX_SECONDS = 300

THRESHOLDS = {"tol_voxels": TOL_VOXELS, "green_flip": GREEN_FLIP, "green_stage": GREEN_STAGE,
              "red_flip": RED_FLIP, "red_stage": RED_STAGE}


def area_voxels(mask: np.ndarray) -> float:
    """Superficie en caras de vóxel (espaciado unidad). 0 si la máscara está vacía."""
    return float(_area_sdf(mask.astype(bool), (1.0, 1.0, 1.0))) if mask.any() else 0.0


def boundary_error(v_m: float, v_r: float, a_r: float) -> float:
    """e_b = |V_M − V_R| / A_R en vóxeles; NaN si la referencia no tiene superficie."""
    return abs(float(v_m) - float(v_r)) / float(a_r) if a_r > 0 else math.nan


def signals(volumes: list[float], v_coarse: float, area_m: float) -> dict:
    """b_flip y b_stage en vóxeles de borde; NaN si la máscara medida está vacía o sin superficie."""
    v_id = float(volumes[0])
    if not (v_id > 0 and area_m > 0):
        return {"v_identity": v_id, "area_m": float(area_m), "b_flip": math.nan, "b_stage": math.nan}
    return {"v_identity": v_id, "area_m": float(area_m), "b_flip": (max(volumes) - min(volumes)) / area_m,
            "b_stage": abs(float(v_coarse) - v_id) / area_m}


def rule(b_flip: float, b_stage: float, in_domain: bool = True) -> str:
    """Misma estructura que ``h20.rule``: una señal no calculable nunca da verde ni rojo."""
    if not (math.isfinite(b_flip) and math.isfinite(b_stage)):
        return "amarillo"
    if b_flip > RED_FLIP or b_stage > RED_STAGE:
        return "rojo"
    if in_domain and b_flip <= GREEN_FLIP and b_stage <= GREEN_STAGE:
        return "verde"
    return "amarillo"


def bad(df: pd.DataFrame) -> np.ndarray:
    """Fallo: e_b > 0,5 vóxeles. Un e_b no calculable cuenta como fallo (conservador)."""
    return ~(df["e_b"].to_numpy(float) <= TOL_VOXELS)


def lights(df: pd.DataFrame, envelope: dict) -> pd.DataFrame:
    dom = h18.inside(df, envelope)
    bf, bs = df["b_flip"].to_numpy(float), df["b_stage"].to_numpy(float)
    return df.assign(in_domain=dom,
                     light=[rule(a, b, d) for a, b, d in zip(bf, bs, dom)],
                     light_without_guard=[rule(a, b, True) for a, b in zip(bf, bs)])


def out_of_fold(cal: pd.DataFrame, n_folds: int = h18.N_FOLDS, seed: int = h19.SEED) -> pd.DataFrame:
    """Como ``h20.out_of_fold``: la guardia se ajusta sin el embrión; la regla no tiene parámetros."""
    fold = cal["embryo_id"].map(h18.embryo_folds(cal["embryo_id"], n_folds, seed))
    parts = [lights(cal[fold == k], h18.fit_envelope(cal[fold != k])) for k in range(n_folds) if (fold == k).any()]
    return pd.concat(parts).loc[cal.index]


def g0(rows: list[dict]) -> dict:
    ok = [math.isfinite(r["b_flip"]) and math.isfinite(r["b_stage"]) and r["area_m"] > 0
          and r["identity_matches"] and r["seconds"] <= G0_MAX_SECONDS for r in rows]
    return {"n": len(rows), "passed": bool(rows) and all(ok), "items": rows}


def gate_s(cal: pd.DataFrame) -> dict:
    ok = float((~bad(cal)).mean()) if len(cal) else math.nan
    return {"n": int(len(cal)), "fraction_ok": ok, "passed": bool(len(cal)) and ok >= S_MIN_OK}


def gate_c(lit: pd.DataFrame) -> dict:
    g = lit[lit["light"] == "verde"]
    fail = float(bad(g).mean()) if len(g) else math.nan
    return {"n_green": int(len(g)), "fail": fail,
            "passed": bool(len(g) >= MIN_GREEN_CAL and math.isfinite(fail) and fail <= MAX_FAIL_CAL)}


def green_failure(lit: pd.DataFrame, n_boot: int = h18.N_BOOT, seed: int = h18.SEED) -> dict:
    """H24b: entre las verdes, fracción con e_b > 0,5; IC por embrión (``h18._bootstrap``)."""
    green = lit[lit["light"] == "verde"]
    out = {"n_green": int(len(green)), "n_embryos_green": int(green["embryo_id"].nunique())}
    if out["n_green"] < MIN_GREEN or out["n_embryos_green"] < MIN_EMBRYOS_GREEN:
        return {**out, "estimate": None, "ci": None, "verdict": "no evaluable"}
    b = bad(green)
    est, ci = float(b.mean()), h18._bootstrap(green, b, n_boot, seed)
    verdict = "apoyada" if est <= MAX_FAIL else ("no apoyada" if ci[0] > MAX_FAIL else "no concluyente")
    return {**out, "estimate": est, "ci": ci, "verdict": verdict}


def _diff_bootstrap(lit: pd.DataFrame, n_boot: int, seed: int) -> list[float]:
    rng = np.random.default_rng(seed)
    d = lit.assign(_bad=bad(lit), _g=(lit["light"] == "verde").to_numpy())
    emb = d["embryo_id"].unique()
    by = {e: d[d["embryo_id"] == e] for e in emb}
    vals = []
    for _ in range(n_boot):
        s = pd.concat([by[e] for e in rng.choice(emb, len(emb))])
        g = s["_g"].to_numpy(bool)
        if g.any() and (~g).any():
            b = s["_bad"].to_numpy(bool)
            vals.append(float(b[~g].mean() - b[g].mean()))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))] if vals else [math.nan, math.nan]


def separation(lit: pd.DataFrame, n_boot: int = h18.N_BOOT, seed: int = h18.SEED) -> dict:
    """H24d: Δ = fallos entre no verdes − fallos entre verdes (fallo: e_b > 0,5)."""
    b = bad(lit)
    g = (lit["light"] == "verde").to_numpy()
    out = {"n_green": int(g.sum()), "n_not_green": int((~g).sum())}
    if out["n_green"] < SEP_MIN_EACH or out["n_not_green"] < SEP_MIN_EACH:
        return {**out, "difference": None, "ci": None, "verdict": "no evaluable"}
    diff = float(b[~g].mean() - b[g].mean())
    ci = _diff_bootstrap(lit, n_boot, seed)
    if not all(math.isfinite(x) for x in ci):
        return {**out, "difference": diff, "ci": ci, "verdict": "no evaluable"}
    verdict = "separa" if ci[0] > 0 else ("no separa" if ci[1] <= SEP_NO_MAX else "no concluyente")
    return {**out, "difference": diff, "fail_green": float(b[g].mean()), "fail_not_green": float(b[~g].mean()),
            "ci": ci, "verdict": verdict}


def evaluate_test(lit: pd.DataFrame, n_boot: int = h18.N_BOOT, seed: int = h18.SEED) -> dict:
    """H24b y H24d (primarias); H24a, H24c, H24e y H24g (secundarias, descriptivas)."""
    b = bad(lit)
    g = lit["light"] == "verde"
    free = lit[lit["light_without_guard"] == "verde"]
    eb = lit["e_b"].astype(float)
    rel = lit["rel_error_volume"].abs()
    return {
        "n_cases": int(len(lit)), "n_embryos": int(lit["embryo_id"].nunique()),
        "h24b": green_failure(lit, n_boot, seed),
        "h24d": separation(lit, n_boot, seed),
        "h24a": {"green_fraction": float(g.mean()) if len(lit) else math.nan,
                 "lights": lit["light"].value_counts().to_dict()},
        "h24c": {"e_b_median": float(eb.median()), "ok_half_voxel": float((eb <= TOL_VOXELS).mean()),
                 "ok_quarter_voxel": float((eb <= TOL_VOXELS / 2).mean()), "dice_median": float(lit["dice"].median()),
                 "ok10_volume": float((rel <= 0.10).mean())},
        "h24e": {"in_domain": float(lit["in_domain"].mean()), "green_without_guard": int(len(free)),
                 "green_without_guard_bad": int(bad(free).sum())},
        "h24g": {"fail_all": float(b.mean()) if len(lit) else math.nan},
    }
