"""Estimadores de referencia independientes para verificar el motor 3D (tarea P1 del informe de progreso).

No usan ``skimage.measure`` ni el código de ``measure.py``/``topology.py``: se implementaron desde la
definición matemática para poder contrastar los resultados de ``geovida`` con un cálculo distinto.

* ``euler_cubical``: característica de Euler χ = V − E + F − C del complejo cúbico asociado a la máscara.
  - Conectividad 26 del primer plano (6 del fondo): unión de cubos **cerrados** de lado 1 centrados en los
    vóxeles; se cuentan los vértices, aristas, caras y cubos distintos de esa unión.
  - Conectividad 6 del primer plano (26 del fondo): complejo dual; vértices = vóxeles, aristas = pares
    6-adyacentes, caras = bloques 2×2 llenos, cubos = bloques 2×2×2 llenos.
  χ es un invariante exacto: si difiere del de ``topology.betti_numbers`` hay un error en uno de los dos.
* ``crofton_area``: área de la frontera por la fórmula de Cauchy–Crofton discreta. Se cuentan las
  transiciones objeto/fondo a lo largo de rectas paralelas en 13 direcciones (3 ejes, 6 diagonales de cara,
  4 diagonales de cubo), cada una con el peso de su celda de Voronoi en la esfera, calculado sobre las
  direcciones **físicas** (así admite vóxeles anisótropos). S ≈ 2 · Σ w_i · n_i · a_i, con n_i transiciones
  y a_i = volumen del vóxel / longitud física del paso. Referencia del método: Lehmann y Legland (2012),
  «Efficient N-dimensional surface estimation using Crofton formula and run-length encoding», The Insight
  Journal; aquí no se copió código, solo la idea de la fórmula.
"""
from __future__ import annotations

import itertools
from functools import lru_cache

import numpy as np

DIRECTIONS = tuple(d for d in itertools.product((-1, 0, 1), repeat=3)
                   if d > (0, 0, 0))  # 13 direcciones no orientadas (la primera no nula es positiva)


def _pad(mask) -> np.ndarray:
    m = np.asarray(mask, dtype=bool)
    if m.ndim != 3:
        raise ValueError("se espera una máscara 3D")
    return np.pad(m, 1)


def _any_over(m: np.ndarray, axes: tuple[int, ...]) -> np.ndarray:
    """OR de los vecinos desplazados 0/1 en los ejes dados (elementos de la retícula dual)."""
    out = m
    for ax in axes:
        a = np.take(out, range(0, out.shape[ax] - 1), axis=ax)
        b = np.take(out, range(1, out.shape[ax]), axis=ax)
        out = a | b
    return out


def _all_over(m: np.ndarray, axes: tuple[int, ...]) -> np.ndarray:
    out = m
    for ax in axes:
        a = np.take(out, range(0, out.shape[ax] - 1), axis=ax)
        b = np.take(out, range(1, out.shape[ax]), axis=ax)
        out = a & b
    return out


def euler_cubical(mask, connectivity: int = 26) -> int:
    """Característica de Euler por conteo de celdas (ver el docstring del módulo)."""
    if connectivity not in (6, 26):
        raise ValueError("connectivity debe ser 6 o 26")
    m = _pad(mask)
    if not m.any():
        return 0
    if connectivity == 26:
        # Cubos cerrados: una celda de dimensión k existe si alguno de los vóxeles que la contienen es objeto.
        cubes = int(m.sum())
        faces = sum(int(_any_over(m, (ax,)).sum()) for ax in range(3))
        edges = sum(int(_any_over(m, ax2).sum()) for ax2 in itertools.combinations(range(3), 2))
        verts = int(_any_over(m, (0, 1, 2)).sum())
    else:
        # Complejo dual: una celda existe si todos sus vóxeles son objeto.
        verts = int(m.sum())
        edges = sum(int(_all_over(m, (ax,)).sum()) for ax in range(3))
        faces = sum(int(_all_over(m, ax2).sum()) for ax2 in itertools.combinations(range(3), 2))
        cubes = int(_all_over(m, (0, 1, 2)).sum())
    return verts - edges + faces - cubes


@lru_cache(maxsize=32)
def crofton_weights(spacing: tuple[float, float, float], n_samples: int = 200_000) -> tuple[float, ...]:
    """Peso de cada dirección: fracción de la esfera más cercana a ±d (celdas de Voronoi), por
    muestreo determinista de Fibonacci. Suman 1."""
    sp = np.asarray(spacing, dtype=float)
    dirs = np.array(DIRECTIONS, dtype=float) * sp
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    i = np.arange(n_samples) + 0.5
    phi = np.arccos(1 - 2 * i / n_samples)
    theta = np.pi * (1 + 5 ** 0.5) * i
    pts = np.stack([np.cos(theta) * np.sin(phi), np.sin(theta) * np.sin(phi), np.cos(phi)], axis=1)
    nearest = np.abs(pts @ dirs.T).argmax(axis=1)
    w = np.bincount(nearest, minlength=len(DIRECTIONS)) / n_samples
    return tuple(float(x) for x in w)


def _transitions(m: np.ndarray, d: tuple[int, int, int]) -> int:
    """Pares (p, p + d) con distinto valor; la máscara ya viene rellenada con fondo."""
    sl_a, sl_b = [], []
    for k in d:
        if k == 0:
            sl_a.append(slice(None)); sl_b.append(slice(None))
        elif k == 1:
            sl_a.append(slice(0, -1)); sl_b.append(slice(1, None))
        else:
            sl_a.append(slice(1, None)); sl_b.append(slice(0, -1))
    return int(np.count_nonzero(m[tuple(sl_a)] != m[tuple(sl_b)]))


def crofton_area(mask, spacing) -> float:
    """Área de la frontera por Cauchy–Crofton con 13 direcciones (unidades físicas al cuadrado)."""
    sp = tuple(float(x) for x in spacing)
    m = _pad(mask)
    if not m.any():
        return 0.0
    w = crofton_weights(sp)
    vox = sp[0] * sp[1] * sp[2]
    total = 0.0
    for wi, d in zip(w, DIRECTIONS):
        step = float(np.linalg.norm(np.array(d) * np.array(sp)))
        total += wi * _transitions(m, d) * (vox / step)
    return 2.0 * total


def voxelize(phantom, h: float, rotation: np.ndarray | None = None, spacing_ratio=(1.0, 1.0, 1.0)) -> tuple[np.ndarray, tuple]:
    """Máscara ideal de un fantoma: centro de vóxel dentro o fuera del sólido (sin ruido ni desenfoque).

    ``h`` es el tamaño de vóxel en x; ``spacing_ratio`` permite vóxeles anisótropos; ``rotation`` gira el
    fantoma (matriz 3×3) para que sus ejes no coincidan con la rejilla.
    """
    sp = np.asarray(spacing_ratio, dtype=float) * h
    r = phantom.bounding_radius + 2 * sp.max()
    axes = [np.arange(-r, r + s / 2, s) for s in sp]
    zz, yy, xx = np.meshgrid(*axes, indexing="ij")
    pts = np.stack([zz, yy, xx], axis=-1)
    if rotation is not None:
        pts = pts @ np.asarray(rotation).T
    return phantom.contains(pts), tuple(float(s) for s in sp)
