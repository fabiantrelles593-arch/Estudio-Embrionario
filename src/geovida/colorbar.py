"""Linealización de un mapa de color con la barra de color de la propia captura (solo investigación y educación).

Una ecografía con tinte (naranja, sepia) no es una escala de grises: el color es una función de la intensidad, y la barra
de color que trae la captura muestra esa función. Convertir a gris con la luminancia de siempre trata el tinte como si fuera
lineal; este módulo lo trata como lo que la barra dice que es.

Qué hace: ``lut_from_bar`` lee la barra (mediana por fila, suavizado, remuestreo) y devuelve una curva de colores de la
intensidad baja a la alta; ``linearize`` asigna a cada píxel la posición del color más cercano de esa curva (distancia en
RGB) y marca como «fuera del mapa» los que quedan lejos (texto, calibradores, marcas).

Lo que NO hace: no corrige la exposición ni la viñeta de una foto, no sabe si la barra de la captura corresponde al
mapa realmente aplicado a la imagen, y no convierte la posición en una magnitud física (la barra no trae unidades).
La orientación «auto» supone que el extremo más oscuro es el de menor intensidad; si la luminancia de la barra no sube
de forma monótona, lo avisa. Usarlo sobre una medida real es un análisis de **sensibilidad**, no una calibración.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

LUMA = np.array([0.299, 0.587, 0.114])
MIN_BAR_ROWS, MIN_BAR_COLS = 8, 3
DEFAULT_OFF_LUT = 0.12            # distancia RGB (0–1) por encima de la cual un color no pertenece al mapa
MONOTONE_FLOOR = 0.9


@dataclass(frozen=True)
class ColorLUT:
    colors: np.ndarray            # (n, 3), valores en [0, 1], de la intensidad baja a la alta
    n_rows: int
    lum_monotone_fraction: float
    warnings: tuple


def _as_unit_rgb(img) -> np.ndarray:
    a = np.asarray(img)
    if a.ndim != 3 or a.shape[2] != 3:
        raise ValueError("la imagen debe ser RGB (alto, ancho, 3)")
    if a.dtype == np.uint8:
        return a.astype(np.float64) / 255.0
    a = a.astype(np.float64)
    return a / 255.0 if a.max() > 1.0 else a


def lut_from_bar(rgb, box, *, orientation: str = "auto", n_points: int = 256, margin_cols: int = 1) -> ColorLUT:
    """Curva de colores de una barra vertical. ``box`` = (x0, y0, x1, y1), semiabierta.

    ``orientation``: ``"auto"`` (el extremo más oscuro es la intensidad baja), ``"top_high"`` o ``"bottom_high"``.
    """
    img = _as_unit_rgb(rgb)
    x0, y0, x1, y1 = (int(v) for v in box)
    if not (0 <= x0 < x1 <= img.shape[1] and 0 <= y0 < y1 <= img.shape[0]):
        raise ValueError(f"la caja {box} no cabe en la imagen {img.shape[:2]} o está invertida")
    if y1 - y0 < MIN_BAR_ROWS or x1 - x0 < MIN_BAR_COLS:
        raise ValueError(f"la barra es demasiado pequeña (mínimo {MIN_BAR_ROWS} filas y {MIN_BAR_COLS} columnas)")
    if orientation not in ("auto", "top_high", "bottom_high"):
        raise ValueError("orientation debe ser 'auto', 'top_high' o 'bottom_high'")
    crop = img[y0:y1, x0:x1]
    if crop.shape[1] > 2 * margin_cols + 1:
        crop = crop[:, margin_cols:crop.shape[1] - margin_cols]
    rows = np.median(crop, axis=1)                                   # (h, 3), de arriba abajo
    rows = ndi.uniform_filter1d(rows, size=3, axis=0, mode="nearest")
    if orientation == "bottom_high":
        pass
    elif orientation == "top_high":
        rows = rows[::-1]
    else:
        third = max(1, len(rows) // 3)
        if (rows[:third] @ LUMA).mean() > (rows[-third:] @ LUMA).mean():      # arriba más claro: invertir
            rows = rows[::-1]
    pos = np.linspace(0.0, 1.0, len(rows))
    grid = np.linspace(0.0, 1.0, int(n_points))
    colors = np.clip(np.stack([np.interp(grid, pos, rows[:, c]) for c in range(3)], axis=1), 0.0, 1.0)
    lum = colors @ LUMA
    frac = float((np.diff(lum) >= -1e-3).mean())
    warnings = []
    if frac < MONOTONE_FLOOR:
        warnings.append(f"la luminancia de la barra no es monótona (fracción de pasos que suben: {frac:.2f}); "
                        "la orientación automática no es fiable y la barra puede no ser una rampa de intensidad")
    return ColorLUT(colors=colors, n_rows=int(y1 - y0), lum_monotone_fraction=frac, warnings=tuple(warnings))


def linearize(rgb, lut: ColorLUT, *, off_lut_threshold: float = DEFAULT_OFF_LUT) -> dict:
    """Posición en [0, 1] de cada píxel sobre la curva de la barra, y qué píxeles quedan fuera del mapa."""
    img = _as_unit_rgb(rgb)
    tree = cKDTree(lut.colors)
    dist, idx = tree.query(img.reshape(-1, 3))
    n = len(lut.colors)
    linear = (idx / (n - 1)).reshape(img.shape[:2])
    off = (dist > off_lut_threshold).reshape(img.shape[:2])
    return {"linear": linear, "off_lut": off, "off_lut_fraction": float(off.mean()),
            "residual_median": float(np.median(dist)), "off_lut_threshold": float(off_lut_threshold)}
