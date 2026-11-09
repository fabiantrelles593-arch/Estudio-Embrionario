"""Estimadores sobre una máscara binaria y comparación con la verdad.

Área: ``area_mc`` (marching cubes sobre la máscara suavizada, sigma = 1 voxel
físico) es el estimador principal; ``area_faces`` (conteo de caras expuestas)
es el estimador ingenuo de referencia, con sesgo conocido (~ +50 % en esferas).
v0.2 añade ``area_sdf``: marching cubes sobre una superficie de distancia con
signo (ligeramente suavizada), que evita el encogimiento que el suavizado de
la máscara impone a los objetos pequeños (sesgo de ``area_mc`` de -64 % a 4
vóxeles). El valor de suavizado (0.5 vóxel) se eligió con un piloto
(``scripts/pilot_area_sdf.py``) y se evalúa con semillas y formas nuevas.
Topología: se informa con ambos pares de adyacencia; el principal
preregistrado es (26,6).
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage as ndi
from skimage.measure import marching_cubes, mesh_surface_area

from .phantoms import Truth
from .topology import betti_numbers


def _area_faces(mask: np.ndarray, spacing) -> float:
    m = np.pad(mask, 1).astype(np.int8)
    hx, hy, hz = spacing
    area = 0.0
    for axis, face in enumerate((hy * hz, hx * hz, hx * hy)):
        area += np.count_nonzero(np.diff(m, axis=axis)) * face
    return float(area)


def _area_mc(mask: np.ndarray, spacing) -> float:
    sp = np.asarray(spacing, dtype=float)
    sm = ndi.gaussian_filter(np.pad(mask, 2).astype(np.float32), sigma=sp.min() / sp)
    try:
        verts, faces, _, _ = marching_cubes(sm, level=0.5, spacing=tuple(spacing))
    except (ValueError, RuntimeError):  # el objeto desaparece tras el suavizado
        return 0.0
    return float(mesh_surface_area(verts, faces))


SDF_SIGMA_VOXELS = 0.5


def _area_sdf(mask: np.ndarray, spacing, sigma: float = SDF_SIGMA_VOXELS) -> float:
    sp = np.asarray(spacing, dtype=float)
    m = np.pad(mask, 3)
    inside = ndi.distance_transform_edt(m, sampling=sp)
    outside = ndi.distance_transform_edt(~m, sampling=sp)
    half = 0.5 * sp.min()  # la frontera cae a medio paso entre centros de vóxel
    sdf = np.where(m, inside - half, -(outside - half)).astype(np.float32)
    if sigma > 0:
        sdf = ndi.gaussian_filter(sdf, sigma=sigma * sp.min() / sp)
    try:
        verts, faces, _, _ = marching_cubes(sdf, level=0.0, spacing=tuple(sp))
    except (ValueError, RuntimeError):
        return 0.0
    return float(mesh_surface_area(verts, faces))


def _mean_depth(mask: np.ndarray, spacing) -> float:
    """Profundidad media interior: media, sobre los vóxeles del objeto, de la
    distancia a la frontera (física; la frontera cae a medio paso del centro del
    vóxel de borde). No usa ningún estimador de área. Bola de radio r: ~ r/4."""
    sp = np.asarray(spacing, dtype=float)
    m = np.pad(mask, 1)
    inside = ndi.distance_transform_edt(m, sampling=sp)
    return float((inside[m] - 0.5 * sp.min()).mean())


def measure_mask(mask: np.ndarray, spacing) -> dict:
    mask = np.asarray(mask, dtype=bool)
    out = {"volume": float(mask.sum() * np.prod(spacing))}
    if not mask.any():
        out.update(area_mc=0.0, area_faces=0.0, area_sdf=0.0, d_mean=0.0)
    else:
        out.update(area_mc=_area_mc(mask, spacing), area_faces=_area_faces(mask, spacing),
                   area_sdf=_area_sdf(mask, spacing), d_mean=_mean_depth(mask, spacing))
    for conn in (26, 6):
        b = betti_numbers(mask, connectivity=conn)
        out.update({f"b0_{conn}": b.b0, f"b1_{conn}": b.b1,
                    f"b2_{conn}": b.b2, f"chi_{conn}": b.chi})
    return out


def relative_errors(meas: dict, truth: Truth) -> dict:
    """Errores con signo (medido - verdad) / verdad; diferencias para Betti."""
    out = {"err_volume": (meas["volume"] - truth.volume) / truth.volume}
    for key in ("area_mc", "area_faces", "area_sdf"):
        if key in meas:
            out[f"err_{key}"] = (meas[key] - truth.surface_area) / truth.surface_area
    for conn, suffix in ((26, ""), (6, "_6")):
        if f"b0_{conn}" not in meas:
            continue
        diffs = [meas[f"b{i}_{conn}"] - truth.betti[i] for i in range(3)]
        for i, d in enumerate(diffs):
            out[f"err_b{i}{suffix}"] = int(d)
        out[f"topology_ok{suffix}"] = bool(all(d == 0 for d in diffs))
    return out


def dice(a: np.ndarray, b: np.ndarray) -> float:
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    tot = a.sum() + b.sum()
    return 1.0 if tot == 0 else float(2.0 * np.logical_and(a, b).sum() / tot)


def _surface(mask: np.ndarray) -> np.ndarray:
    return mask & ~ndi.binary_erosion(mask, border_value=0)


def surface_distance_stats(a: np.ndarray, b: np.ndarray, spacing) -> dict:
    """HD95 y distancia media simétrica entre superficies de dos máscaras."""
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    if not a.any() or not b.any():
        return {"hd95": math.nan, "msd": math.nan}
    sa, sb = _surface(a), _surface(b)
    d_to_b = ndi.distance_transform_edt(~sb, sampling=spacing)[sa]
    d_to_a = ndi.distance_transform_edt(~sa, sampling=spacing)[sb]
    both = np.concatenate([d_to_b, d_to_a])
    return {"hd95": float(np.percentile(both, 95)),
            "msd": float(0.5 * (d_to_b.mean() + d_to_a.mean()))}
