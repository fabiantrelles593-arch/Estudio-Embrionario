"""Acuerdo entre dos segmentaciones y entre dos lectores (solo investigación y educación).

Viene de ``docs/INTEGRACION_PDF_EXTERNO.md`` §3: ninguna métrica sola cuenta la historia, y el acuerdo entre personas fija el piso
de lo que se le puede pedir a una máquina. Este módulo **no valida nada por sí mismo**: calcula, con definiciones escritas,
cantidades que luego se comparan con un criterio fijado de antemano.

Convenciones (hay más de una en uso; esta es la de este proyecto):

* ``compare_masks(a, b)``: ``b`` es la **referencia**. ``size_diff_rel = (tamaño(a) − tamaño(b)) / tamaño(b)``, con signo.
  El tamaño es el número de píxeles o vóxeles por el producto del espaciado (mm² en 2D, mm³ en 3D).
* ``hd95_pooled``: percentil 95 de **todas** las distancias de superficie, en los dos sentidos juntas (la convención de
  ``geovida.measure``). ``hd95_max``: el mayor de los dos percentiles 95 direccionales (la convención de Taha y Hanbury).
* ``assd``: media de todas las distancias de superficie en los dos sentidos juntas. ``msd_mean_of_means``: promedio de las dos
  medias direccionales (la que usa ``geovida.measure``). Coinciden solo si ambas superficies tienen igual número de píxeles.
* Una máscara vacía no tiene distancia de superficie: se devuelve ``nan``, nunca cero.
* ``bland_altman(x, y)``: ``x − y``; límites de acuerdo ``sesgo ± 1.96·SD``; intervalos de confianza de Bland y Altman (1999) con la
  distribución t. La unidad es el **individuo**: varias lecturas de un mismo individuo no son individuos distintos.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage as ndi
from scipy import stats

from .measure import dice as _dice, _surface

LOA_Z = 1.96


def _check_spacing(a: np.ndarray, spacing) -> tuple[float, ...]:
    sp = tuple(float(s) for s in spacing)
    if len(sp) != a.ndim:
        raise ValueError(f"el espaciado tiene {len(sp)} valores y las máscaras {a.ndim} dimensiones")
    if not all(math.isfinite(s) and s > 0 for s in sp):
        raise ValueError("el espaciado debe ser finito y positivo")
    return sp


def compare_masks(a, b, *, spacing) -> dict:
    """Acuerdo de la máscara ``a`` (medida) con ``b`` (referencia). Ver las convenciones en el docstring del módulo."""
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    if a.shape != b.shape:
        raise ValueError(f"las máscaras tienen formas distintas: {a.shape} y {b.shape}")
    sp = _check_spacing(a, spacing)
    unit = float(np.prod(sp))
    size_a, size_b = float(a.sum()) * unit, float(b.sum()) * unit
    inter = int(np.logical_and(a, b).sum())
    union = int(np.logical_or(a, b).sum())
    out = {"dice": _dice(a, b), "iou": 1.0 if union == 0 else inter / union,
           "size_a": size_a, "size_b": size_b,
           "size_diff_rel": (size_a - size_b) / size_b if size_b > 0 else math.nan}
    if not a.any() or not b.any():
        out.update({"hd95_pooled": math.nan, "hd95_max": math.nan, "assd": math.nan, "msd_mean_of_means": math.nan})
        return out
    sa, sb = _surface(a), _surface(b)
    d_ab = ndi.distance_transform_edt(~sb, sampling=sp)[sa]      # de cada punto de la superficie de a a la superficie de b
    d_ba = ndi.distance_transform_edt(~sa, sampling=sp)[sb]
    both = np.concatenate([d_ab, d_ba])
    out.update({"hd95_pooled": float(np.percentile(both, 95)),
                "hd95_max": float(max(np.percentile(d_ab, 95), np.percentile(d_ba, 95))),
                "assd": float(both.mean()),
                "msd_mean_of_means": float(0.5 * (d_ab.mean() + d_ba.mean()))})
    return out


def bland_altman(x, y, *, confidence: float = 0.95) -> dict:
    """Sesgo y límites de acuerdo entre dos lectores (``x − y``) sobre los mismos individuos."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.ndim != 1 or x.shape != y.shape:
        raise ValueError("x e y deben ser vectores de la misma longitud")
    n = int(x.size)
    if n < 2:
        raise ValueError("hacen falta al menos dos individuos")
    if not (np.isfinite(x).all() and np.isfinite(y).all()):
        raise ValueError("hay valores no finitos")
    if not (0.0 < confidence < 1.0):
        raise ValueError("la confianza debe estar entre 0 y 1")
    d = x - y
    bias, sd = float(d.mean()), float(d.std(ddof=1))
    t = float(stats.t.ppf(0.5 + confidence / 2.0, n - 1))
    se_bias = sd / math.sqrt(n)
    se_loa = sd * math.sqrt(1.0 / n + LOA_Z ** 2 / (2.0 * (n - 1)))
    lo, hi = bias - LOA_Z * sd, bias + LOA_Z * sd
    pair_mean = (x + y) / 2.0
    rel = float((d / pair_mean).mean() * 100.0) if np.all(pair_mean != 0) else math.nan
    return {"n": n, "confidence": float(confidence), "bias": bias,
            "bias_ci": (bias - t * se_bias, bias + t * se_bias), "sd_diff": sd,
            "loa_lower": lo, "loa_upper": hi,
            "loa_lower_ci": (lo - t * se_loa, lo + t * se_loa), "loa_upper_ci": (hi - t * se_loa, hi + t * se_loa),
            "rel_bias_pct": rel,
            "notes": ["La unidad es el individuo: varias lecturas de un mismo individuo no son individuos distintos.",
                      "Con pocos individuos los intervalos de los límites de acuerdo son anchos; no se interpretan como precisión del método."]}
