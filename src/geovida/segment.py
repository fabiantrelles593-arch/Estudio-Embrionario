"""Segmentadores preregistrados (los tres comparados en la hipótesis H1).

* ``global``        umbral fijo en la mitad del contraste (0.5; oráculo: se
                    conoce el contraste del fantoma).
* ``otsu``          umbral de Otsu sobre la imagen cruda.
* ``smoothed_otsu`` suavizado gaussiano (sigma = 1 h_xy físico) + Otsu.

No hay limpieza morfológica a propósito: los errores topológicos deben ser
visibles, no corregidos en silencio.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from skimage.filters import threshold_otsu


def _global(image: np.ndarray, spacing) -> np.ndarray:
    return image >= 0.5


def _otsu(image: np.ndarray, spacing) -> np.ndarray:
    return image >= threshold_otsu(image)


def _smoothed_otsu(image: np.ndarray, spacing, sigma: float = 1.0) -> np.ndarray:
    sp = np.asarray(spacing, dtype=float)
    sm = ndi.gaussian_filter(image, sigma=sigma * sp.min() / sp)
    return sm >= threshold_otsu(sm)


SEGMENTERS = {"global": _global, "otsu": _otsu, "smoothed_otsu": _smoothed_otsu}


def segment(name: str, image: np.ndarray, spacing) -> np.ndarray:
    if name not in SEGMENTERS:
        raise ValueError(f"segmentador desconocido: {name!r}; opciones: {tuple(SEGMENTERS)}")
    return SEGMENTERS[name](image, spacing).astype(bool)
