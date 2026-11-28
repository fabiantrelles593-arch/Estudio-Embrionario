"""Banco de pruebas 4D sintético (pseudo-tiempo).

Un "embrión" no se sigue en el tiempo: cada espécimen se mide una vez y se
asigna a una etapa nominal. El tiempo verdadero de cada uno difiere de la
etapa por un error de estadificación eps ~ N(0, sigma_s) (en unidades de
intervalo entre etapas). Este módulo mide cuánto distorsiona eso la
trayectoria media recuperada y cuándo ayuda corregirlo.

Todos los estimadores son suavizadores lineales ``f_hat = H @ y`` con H fija
para un diseño balanceado, lo que hace exactos y vectorizados el bootstrap
por especímenes y el cálculo de sesgo/varianza.

* ``stage_mean``       media por etapa (sin modelo).
* ``spline``           B-spline cúbica (7 funciones base) sobre la etapa nominal.
* ``spline_corrected`` igual, pero con la base promediada sobre la distribución
  del error de estadificación (calibración de regresión tipo Berkson,
  sigma conocido o supuesto): E[B_j(k + eps)] por cuadratura de Gauss-Hermite.
"""
from __future__ import annotations

import math
from typing import Callable

import numpy as np
import pandas as pd
from scipy.interpolate import BSpline

K_STAGES = 7
_GH_X, _GH_W = np.polynomial.hermite.hermgauss(21)

FEATURES: dict[str, Callable[[np.ndarray], np.ndarray]] = {
    "growth": lambda t: np.exp(0.5 * np.asarray(t, dtype=float)),
    "saturating": lambda t: 0.9 - 0.5 * np.exp(-np.asarray(t, dtype=float) / 2.0),
    "switch": lambda t: 0.2 + 0.6 / (1.0 + np.exp(-(np.asarray(t, dtype=float) - 3.0) / 0.7)),
}


def smoothed_truth(f: Callable, x: np.ndarray, sigma: float) -> np.ndarray:
    """E[f(x + eps)], eps ~ N(0, sigma^2), por cuadratura de Gauss-Hermite."""
    x = np.asarray(x, dtype=float)
    if sigma == 0:
        return np.asarray(f(x), dtype=float)
    pts = x[..., None] + sigma * math.sqrt(2.0) * _GH_X
    return (np.asarray(f(pts)) * _GH_W).sum(-1) / math.sqrt(math.pi)


def simulate_cohort(rng: np.random.Generator, feature: str, n: int, sigma_s: float,
                    cv: float = 0.08, meas: float = 0.0, n_reps: int = 1,
                    n_stages: int = K_STAGES) -> tuple[np.ndarray, np.ndarray]:
    """Cohortes transversales: ``n`` especímenes por etapa, ``n_reps`` réplicas.

    Y = f(tau_verdadero) * (1 + variación entre individuos, CV=cv)
                        * (1 + error de medición relativo, sd=meas)
    """
    nominal = np.repeat(np.arange(n_stages, dtype=float), n)
    size = (n_reps, nominal.size)
    tau = nominal[None, :] + sigma_s * rng.standard_normal(size)
    y = FEATURES[feature](tau) * (1 + cv * rng.standard_normal(size)) \
        * (1 + meas * rng.standard_normal(size))
    return y, tau


def _knots(n_stages: int) -> np.ndarray:
    interior = np.linspace(0, n_stages - 1, 5)[1:-1]
    return np.r_[[0.0] * 4, interior, [float(n_stages - 1)] * 4]


def _basis(x: np.ndarray, n_stages: int) -> np.ndarray:
    t = _knots(n_stages)
    nb = len(t) - 4
    return np.stack([BSpline(t, np.eye(nb)[j], 3, extrapolate=True)(x)
                     for j in range(nb)], axis=-1)


def _smoothed_basis(x: np.ndarray, sigma: float, n_stages: int) -> np.ndarray:
    if sigma == 0:
        return _basis(x, n_stages)
    out = 0.0
    for xi, wi in zip(_GH_X, _GH_W):
        out = out + wi * _basis(x + sigma * math.sqrt(2.0) * xi, n_stages)
    return out / math.sqrt(math.pi)


def estimator_matrix(name: str, n: int, sigma_assumed: float = 0.0,
                     n_stages: int = K_STAGES) -> np.ndarray:
    """Matriz H (n_stages x n_stages*n) tal que estimación = H @ y."""
    if name == "stage_mean":
        H = np.zeros((n_stages, n_stages * n))
        for k in range(n_stages):
            H[k, k * n:(k + 1) * n] = 1.0 / n
        return H
    nominal = np.repeat(np.arange(n_stages, dtype=float), n)
    centers = np.arange(n_stages, dtype=float)
    if name == "spline":
        X = _basis(nominal, n_stages)
    elif name == "spline_corrected":
        X = _smoothed_basis(nominal, sigma_assumed, n_stages)
    else:
        raise ValueError(f"estimador desconocido: {name!r}")
    return _basis(centers, n_stages) @ np.linalg.pinv(X, rcond=1e-12)


def evaluate_cell(feature: str, n: int, sigma_s: float, meas: float, estimator: str,
                  sigma_assumed_ratio: float = 1.0, cv: float = 0.08,
                  n_reps: int = 500, n_boot: int = 200, seed: int = 0) -> dict:
    """Sesgo, varianza, RMSE relativo y cobertura bootstrap en una celda."""
    rng = np.random.default_rng(seed)
    K = K_STAGES
    Y, _ = simulate_cohort(rng, feature, n, sigma_s, cv, meas, n_reps)
    H = estimator_matrix(estimator, n, sigma_assumed=sigma_assumed_ratio * sigma_s)
    stages = np.arange(K, dtype=float)
    truth = FEATURES[feature](stages)

    rel = (Y @ H.T) / truth - 1.0                       # (reps, K)
    rel_bias, rel_var = rel.mean(0), rel.var(0)
    irmse2 = float(np.mean(rel**2))
    out = {
        "rel_bias": rel_bias, "rel_var": rel_var,
        "mean_rel_var": float(rel_var.mean()),
        "max_abs_bias": float(np.abs(rel_bias).max()),
        "int_abs_bias": float(np.abs(rel_bias).mean()),
        "irmse": math.sqrt(irmse2),
        "bias2_share": float(np.mean(rel_bias**2) / irmse2) if irmse2 > 0 else 0.0,
    }

    coverage = np.full(K, np.nan)
    if n_boot > 0 and n >= 2:
        hits = np.zeros(K)
        for r in range(n_reps):
            yr = Y[r].reshape(K, n)
            idx = rng.integers(0, n, size=(n_boot, K, n))
            yb = np.take_along_axis(np.broadcast_to(yr, (n_boot, K, n)), idx, axis=2)
            est_b = yb.reshape(n_boot, K * n) @ H.T
            lo, hi = np.percentile(est_b, [2.5, 97.5], axis=0)
            hits += (lo <= truth) & (truth <= hi)
        coverage = hits / n_reps
    out["coverage"] = coverage
    out["mean_coverage"] = float(np.mean(coverage))
    return out


def measurement_bias_function(df: pd.DataFrame, shape: str, segmenter: str,
                              profile: str, anisotropy: float) -> Callable[[float], float]:
    """Sesgo relativo de V en función de t/h, a partir de los resultados de H1.

    Interpola la mediana del error de volumen en log(t/h) y sujeta a los bordes
    fuera del rango barrido (no extrapola). Conecta la metrología (H1) con la
    trayectoria 4D: un objeto que crece con vóxel fijo cambia su t/h.
    """
    sel = df[(df["shape"] == shape) & (df["segmenter"] == segmenter)
             & (df["profile"] == profile) & (df["anisotropy"] == anisotropy)]
    if sel.empty:
        raise ValueError("no hay filas de H1 para ese estrato")
    med = sel.groupby("t_over_h")["err_volume"].median().sort_index()
    logx, vals = np.log(med.index.to_numpy(dtype=float)), med.to_numpy()
    return lambda t_over_h: float(np.interp(math.log(t_over_h), logx, vals))
