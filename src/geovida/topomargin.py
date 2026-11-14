"""Margen de persistencia topológica (v0.4): ¿cuánto aguanta la topología medida?

Dos márgenes, ninguno necesita la verdad:

* **Geométrico** (solo máscara y vóxel): cuánto se puede dilatar (``tau_dil``) o
  erosionar (``tau_ero``) la frontera, en múltiplos del vóxel más fino, sin que
  cambie el triple de Betti. Es la distancia desde el nivel 0 hasta el primer
  evento en la filtración por distancia euclídea con signo, la misma que usan
  Robins et al. (2016) en medios porosos. La idea no es nueva; lo que aquí se
  prueba es su uso como predictor CALIBRADO contra una verdad conocida.
* **De intensidad** (imagen + segmentador): cuánto se puede bajar (``m_lo``) o
  subir (``m_hi``) el umbral, como fracción del contraste medido, sin que cambie
  el triple de Betti (filtración por umbral; Chung y Day 2018).

``critical_sites`` devuelve además DÓNDE ocurre el primer evento cuando es una
separación, una fusión o un componente o cavidad pequeños. Los eventos de túnel
se informan sin localizar.

Límite que el código no oculta («fallo silencioso»): un rasgo que la imagen ya
ha perdido por completo no deja rastro en la máscara, y solo deja rastro en la
intensidad si queda algo de señal. Ningún margen puede detectarlo en ese caso.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage as ndi

from .segment import working_image_and_threshold
from .topology import betti_numbers

MARGIN_GRID = (0.6, 1.0, 1.5, 2.0)        # desfases, en múltiplos del vóxel más fino
INTENSITY_GRID = (0.1, 0.2, 0.3, 0.4)     # desplazamientos del umbral, en fracción del contraste
_PAD = 3
_EPS = 1e-6
_S26 = ndi.generate_binary_structure(3, 3)
_S6 = ndi.generate_binary_structure(3, 1)


def _signed_distance(mask: np.ndarray, sp: np.ndarray) -> np.ndarray:
    """Distancia con signo a la frontera digital (positiva dentro), con ``_PAD``
    vóxeles de margen; la frontera cae a medio paso fino del centro del vóxel."""
    m = np.pad(mask, _PAD)
    inside = ndi.distance_transform_edt(m, sampling=sp)
    outside = ndi.distance_transform_edt(~m, sampling=sp)
    half = 0.5 * sp.min()
    return np.where(m, inside - half, -(outside - half))


def _shifted(sdf: np.ndarray, hmin: float, s: float, erode: bool) -> np.ndarray:
    level = s * hmin * (1.0 + _EPS)
    return (sdf > level) if erode else (sdf >= -level)


def _scan(sdf, hmin, base, erode: bool, connectivity: int):
    """(margen, desfase del primer cambio o None, máscara cambiada o None, Betti nuevo)."""
    tol = 0.0
    for s in MARGIN_GRID:
        shifted = _shifted(sdf, hmin, s, erode)
        b = betti_numbers(shifted, connectivity).as_tuple()
        if b != base:
            return tol, s, shifted, b
        tol = s
    return tol, None, None, base


def topological_margin(mask: np.ndarray, spacing, connectivity: int = 26) -> dict:
    """``tau_dil`` y ``tau_ero``: mayor desfase de ``MARGIN_GRID`` tal que todos los
    desfases hasta él conservan el triple de Betti (0.0 si ya el primero lo
    cambia; el último valor de la rejilla es un valor censurado: «al menos»)."""
    mask = np.asarray(mask, dtype=bool)
    if not mask.any():
        return {"tau_dil": math.nan, "tau_ero": math.nan}
    sp = np.asarray(spacing, dtype=float)
    sdf = _signed_distance(mask, sp)
    base = betti_numbers(mask, connectivity).as_tuple()
    hmin = float(sp.min())
    return {"tau_dil": _scan(sdf, hmin, base, False, connectivity)[0],
            "tau_ero": _scan(sdf, hmin, base, True, connectivity)[0]}


# --- localización -----------------------------------------------------------

def _centroid(sel: np.ndarray) -> tuple[float, float, float] | None:
    idx = np.argwhere(sel)
    if len(idx) == 0:
        return None
    c = idx.mean(axis=0) - _PAD                     # de vuelta a índices de la máscara original
    return (float(c[0]), float(c[1]), float(c[2]))


def _interface(labels: np.ndarray, domain: np.ndarray, sp: np.ndarray) -> np.ndarray:
    """Vóxeles de ``domain`` donde se tocan regiones más cercanas a etiquetas distintas."""
    seeds = labels > 0
    idx = ndi.distance_transform_edt(~seeds, sampling=sp, return_distances=False,
                                     return_indices=True)
    nearest = labels[tuple(idx)]
    nearest = np.where(domain, nearest, 0)
    hi = ndi.maximum_filter(nearest, size=3)
    lo = ndi.minimum_filter(np.where(nearest > 0, nearest, np.iinfo(np.int32).max), size=3)
    return domain & (hi != lo) & (lo != np.iinfo(np.int32).max)


def _erosion_site(m, eroded, base, new, sp, s) -> dict:
    site = {"offset_vox": s, "betti_before": list(base), "betti_after": list(new),
            "kind": "túnel o cavidad", "centroid_vox": None}
    if new[0] > base[0]:                              # la erosión parte un componente: cuello
        lab, _ = ndi.label(eroded, structure=_S26)
        site.update(kind="separación", centroid_vox=_centroid(_interface(lab, m, sp)))
    elif new[0] < base[0]:                            # un componente entero desaparece: mota
        lab, n = ndi.label(m, structure=_S26)
        alive = np.unique(lab[eroded])
        gone = np.isin(lab, np.setdiff1d(np.arange(1, n + 1), alive))
        site.update(kind="componente pequeño", centroid_vox=_centroid(gone))
    return site


def _dilation_site(m, dilated, base, new, sp, s) -> dict:
    site = {"offset_vox": s, "betti_before": list(base), "betti_after": list(new),
            "kind": "túnel o cavidad", "centroid_vox": None}
    if new[0] < base[0]:                              # la dilatación une dos componentes: hueco fino
        lab, _ = ndi.label(m, structure=_S26)
        site.update(kind="fusión", centroid_vox=_centroid(_interface(lab, dilated, sp)))
    elif new[2] < base[2]:                            # una cavidad se rellena
        lab, n = ndi.label(~m, structure=_S6)
        still = np.unique(lab[~dilated])
        gone = np.isin(lab, np.setdiff1d(np.arange(1, n + 1), still))
        site.update(kind="cavidad pequeña", centroid_vox=_centroid(gone))
    return site


def critical_sites(mask: np.ndarray, spacing, connectivity: int = 26) -> dict:
    """Primer evento topológico al erosionar y al dilatar, con su lugar si es
    localizable. ``None`` en un lado significa «ningún cambio hasta el tope»."""
    mask = np.asarray(mask, dtype=bool)
    if not mask.any():
        return {"erosion": None, "dilation": None}
    sp = np.asarray(spacing, dtype=float)
    sdf = _signed_distance(mask, sp)
    m = np.pad(mask, _PAD)
    base = betti_numbers(mask, connectivity).as_tuple()
    hmin = float(sp.min())
    out = {}
    _, s, changed, new = _scan(sdf, hmin, base, True, connectivity)
    out["erosion"] = None if s is None else _erosion_site(m, changed, base, new, sp, s)
    _, s, changed, new = _scan(sdf, hmin, base, False, connectivity)
    out["dilation"] = None if s is None else _dilation_site(m, changed, base, new, sp, s)
    return out


# --- margen de intensidad ---------------------------------------------------

def intensity_margin(image: np.ndarray, spacing, segmenter: str,
                     connectivity: int = 26) -> dict:
    """``m_lo`` / ``m_hi``: cuánto puede bajar / subir el umbral operativo, en
    fracción del contraste medido (media dentro − media fuera de la máscara),
    sin que cambie el triple de Betti. NaN si no hay contraste medible."""
    work, thr = working_image_and_threshold(segmenter, np.asarray(image), spacing)
    mask = work >= thr
    nan = {"m_lo": math.nan, "m_hi": math.nan, "contrast_hat": math.nan}
    if not mask.any() or mask.all():
        return nan
    contrast = float(work[mask].mean() - work[~mask].mean())
    if not math.isfinite(contrast) or contrast <= 0:
        return nan
    base = betti_numbers(mask, connectivity).as_tuple()

    def scan(sign: float) -> float:
        tol = 0.0
        for f in INTENSITY_GRID:
            shifted = work >= thr + sign * f * contrast
            if betti_numbers(shifted, connectivity).as_tuple() != base:
                return tol
            tol = f
        return tol

    return {"m_lo": scan(-1.0), "m_hi": scan(+1.0), "contrast_hat": contrast}
