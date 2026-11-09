"""Análisis preregistrado de H1 (ver docs/PREREGISTRO_H1.md, secciones 4-6)."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.special import expit

PREDICTORS = {
    "P1": "t_solid_over_hxy", "P2": "t_solid_over_hgeo", "P3": "t_solid_over_hmax",
    "P4": "t_min_over_hxy", "P5": "t_min_over_hgeo", "P6": "t_min_over_hmax",
}


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def find_t_star(levels, p, threshold: float = 0.95) -> float:
    """Menor nivel con éxito >= umbral en él y en todos los niveles mayores."""
    levels, p = list(levels), list(p)
    star = math.nan
    for lvl, pi in zip(reversed(levels), reversed(p)):
        if pi >= threshold:
            star = lvl
        else:
            break
    return star


def spread_in_steps(levels, tstars) -> float:
    """Rango de t/h* medido en pasos de la rejilla (nan si alguno no se alcanzó)."""
    levels = list(levels)
    if any(isinstance(t, float) and math.isnan(t) for t in tstars):
        return math.nan
    idx = [levels.index(t) for t in tstars]
    return float(max(idx) - min(idx))


def add_predictors(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    f = out["anisotropy"] ** (1.0 / 3.0)
    out["t_solid_over_hgeo"] = out["t_solid_over_hxy"] / f
    out["t_min_over_hgeo"] = out["t_min_over_hxy"] / f
    return out


def success_by_level(df: pd.DataFrame, endpoint: str, by: list[str]) -> pd.DataFrame:
    g = df.groupby(by + ["t_over_h"])[endpoint]
    tab = g.agg(n="size", k="sum").reset_index()
    tab["k"] = tab["k"].astype(int)
    tab["p"] = tab["k"] / tab["n"]
    ci = [wilson_interval(k, n) for k, n in zip(tab["k"], tab["n"])]
    tab["wilson_lo"] = [c[0] for c in ci]
    tab["wilson_hi"] = [c[1] for c in ci]
    return tab


def _fit_logit_ridge(x: np.ndarray, y: np.ndarray, lam: float = 1e-2, iters: int = 100):
    """Logit de 2 parámetros con ridge mínimo sobre la pendiente (evita la
    separación perfecta sin sesgar apreciablemente cuando no la hay)."""
    X = np.column_stack([np.ones_like(x), x])
    b = np.zeros(2)
    pen = np.diag([0.0, lam])
    for _ in range(iters):
        p = expit(X @ b)
        w = np.clip(p * (1 - p), 1e-9, None)
        grad = X.T @ (y - p) - pen @ b
        hess = X.T @ (X * w[:, None]) + pen
        step = np.linalg.solve(hess, grad)
        b = b + step
        if np.abs(step).max() < 1e-10:
            break
    return b, expit(X @ b)


def compare_predictors(df: pd.DataFrame, endpoint: str) -> pd.DataFrame:
    """AIC y pseudo-R² de McFadden de ``Pr(ok) ~ log(P)`` para P1..P6.

    El ajuste es conjunto sobre todas las formas/anisotropías del ``df`` que se
    pase (el llamador lo estratifica por segmentador y perfil): una curva única
    que describa todo es justamente la hipótesis de universalidad.
    """
    df = add_predictors(df) if "t_solid_over_hgeo" not in df else df
    y = df[endpoint].to_numpy(dtype=float)
    p0 = y.mean()
    ll_null = float(np.sum(y * np.log(max(p0, 1e-12)) + (1 - y) * np.log(max(1 - p0, 1e-12))))
    rows = []
    for name, col in PREDICTORS.items():
        x = np.log(df[col].to_numpy(dtype=float))
        x = (x - x.mean()) / (x.std() or 1.0)
        _, p = _fit_logit_ridge(x, y)
        p = np.clip(p, 1e-12, 1 - 1e-12)
        ll = float(np.sum(y * np.log(p) + (1 - y) * np.log(1 - p)))
        rows.append({"predictor": name, "column": col, "n": len(y), "loglik": ll,
                     "aic": -2 * ll + 4,
                     "mcfadden": 1 - ll / ll_null if ll_null < 0 else math.nan})
    return pd.DataFrame(rows)


def t_star_table(tab: pd.DataFrame, strata: list[str], threshold: float = 0.95) -> pd.DataFrame:
    """t/h* (menor nivel con éxito sostenido) por estrato, desde ``success_by_level``."""
    rows = []
    for key, g in tab.groupby(strata):
        g = g.sort_values("t_over_h")
        key = key if isinstance(key, tuple) else (key,)
        rows.append({**dict(zip(strata, key)),
                     "t_star": find_t_star(g["t_over_h"], g["p"], threshold)})
    return pd.DataFrame(rows)


def ratio_spread(values) -> float:
    """Cociente máx/mín de valores positivos (nan si alguno no se alcanzó).

    Se usa cuando los valores viven en rejillas distintas (p. ej. t_min/h* de
    formas con distinta razón t_min/t_solid): «≤ un paso de rejilla» se traduce
    en un cociente ≤ 1.5, el mayor cociente entre niveles adyacentes.
    """
    vals = [float(v) for v in values]
    if any(math.isnan(v) for v in vals):
        return math.nan
    return max(vals) / min(vals)


def add_vq_predictors(df: pd.DataFrame) -> pd.DataFrame:
    """Predictor EXPLORATORIO (post hoc, no preregistrado): Q = V / (S h).

    Es la «longitud volumen/área» del objeto en unidades de vóxel (r/3 en una
    bola). El error relativo del conteo de vóxeles escala con (S/V)·h, no con el
    grosor. Requiere que la unidad de longitud sea t = 1 (como en el barrido),
    de modo que h_xy = 1 / t_over_h.
    """
    out = df.copy()
    h_xy = 1.0 / out["t_over_h"]
    q = out["volume_true"] / out["area_true"]
    out["q_over_hxy"] = q / h_xy
    out["q_over_hgeo"] = q / (h_xy * out["anisotropy"] ** (1.0 / 3.0))
    out["q_over_hmax"] = q / (h_xy * out["anisotropy"])
    return out


# --- v0.2: modelos congelados para la confirmación H3 -----------------------
# Un modelo «congelado» se ajusta una sola vez con los datos de H1 y se evalúa
# SIN reajustar sobre las formas y semillas nuevas de H3: es la prueba de que
# una regla descubierta post hoc generaliza.

def fit_frozen_logit(x, y) -> dict:
    """Logit Pr(ok) = expit(a + b·ln x) con x en su escala original."""
    b, _ = _fit_logit_ridge(np.log(np.asarray(x, float)), np.asarray(y, float))
    return {"intercept": float(b[0]), "slope": float(b[1])}


def predict_frozen(model: dict, x) -> np.ndarray:
    return expit(model["intercept"] + model["slope"] * np.log(np.asarray(x, float)))


def logloss(model: dict, x, y) -> float:
    """Entropía cruzada media (menor es mejor)."""
    p = np.clip(predict_frozen(model, x), 1e-12, 1 - 1e-12)
    y = np.asarray(y, float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def calibration_error(model: dict, x, y, bins: int = 10) -> float:
    """Error de calibración esperado: media ponderada de |p_pred - p_obs| por
    cajas de igual ancho en la probabilidad predicha."""
    p = predict_frozen(model, x)
    y = np.asarray(y, float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    err = 0.0
    for k in range(bins):
        sel = idx == k
        if sel.any():
            err += sel.sum() * abs(p[sel].mean() - y[sel].mean())
    return float(err / len(y))


def x_at_probability(model: dict, prob: float = 0.95) -> float:
    """x tal que Pr(ok) = prob según el modelo (nan si la curva es plana)."""
    if abs(model["slope"]) < 1e-9:
        return math.nan
    return float(math.exp((math.log(prob / (1 - prob)) - model["intercept"]) / model["slope"]))


def tristate_all(values, ok) -> bool | None:
    """True si todos los valores cumplen ``ok``; False si alguno finito no lo
    cumple; None («no evaluable») si no hay incumplimiento pero falta evidencia (NaN).

    Corrige un defecto de v0.1: un NaN se contaba como «no apoyada».
    """
    vals = list(values)
    finite = [v for v in vals if not (isinstance(v, float) and math.isnan(v))]
    if any(not ok(v) for v in finite):
        return False
    return None if len(finite) < len(vals) else True


def status_label(state: bool | None) -> str:
    return "no evaluable" if state is None else ("apoyada" if state else "no apoyada")
