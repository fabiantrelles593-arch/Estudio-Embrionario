"""Segmentadores preregistrados (los tres comparados en la hipótesis H1).

* ``global``        umbral fijo en la mitad del contraste (0.5; oráculo: se
                    conoce el contraste del fantoma).
* ``otsu``          umbral de Otsu sobre la imagen cruda.
* ``smoothed_otsu`` suavizado gaussiano (sigma = 1 h_xy físico) + Otsu.

No hay limpieza morfológica a propósito: los errores topológicos deben ser
visibles, no corregidos en silencio.

Extensión v0.2 (fuera del conjunto preregistrado, que no cambia):

* ``otsu_clean``   Otsu crudo + eliminación de componentes de primer plano
                   y relleno de cavidades de menos de ``CLEAN_MIN_VOXELS``
                   vóxeles. Es la limpieza «mínima» que el informe v0.1 pedía.
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


def working_image_and_threshold(name: str, image: np.ndarray, spacing):
    """Imagen de trabajo y umbral de cada segmentador preregistrado, de modo que
    ``work >= thr`` reproduce exactamente su máscara. Lo usa el margen de
    intensidad (v0.4) para mover el umbral alrededor del operativo."""
    if name == "global":
        return image, 0.5
    if name == "otsu":
        return image, float(threshold_otsu(image))
    if name == "smoothed_otsu":
        sp = np.asarray(spacing, dtype=float)
        sm = ndi.gaussian_filter(image, sigma=1.0 * sp.min() / sp)
        return sm, float(threshold_otsu(sm))
    raise ValueError(f"sin umbral de trabajo para el segmentador {name!r}")


CLEAN_MIN_VOXELS = 8  # 2 x 2 x 2: por debajo no hay rasgo resoluble


def _clean_mask(mask: np.ndarray, min_voxels: int = CLEAN_MIN_VOXELS):
    """Limpieza mínima. Devuelve (máscara, componentes quitados, cavidades rellenadas).

    LÍMITE CONOCIDO (ERRATA E11): el criterio es de tamaño, no de significado.
    Una cavidad o un componente REAL de menos de ``min_voxels`` vóxeles también
    se borra (cáscara fina a 4 vóxeles: la topología pasa de 100 % a 0 %).
    Úsese solo si se sabe que ningún rasgo real es tan pequeño, y mírese
    ``clean_report`` para ver cuánto se borró.
    """
    # primer plano en 26-conectividad: fuera los componentes diminutos
    lab, n = ndi.label(mask, structure=np.ones((3, 3, 3), dtype=bool))
    removed = 0
    if n:
        sizes = np.bincount(lab.ravel())
        small = sizes < min_voxels
        small[0] = False
        removed = int(small.sum())
        mask = mask & ~small[lab]
    # fondo en 6-conectividad: se rellenan las cavidades diminutas (no el exterior)
    padded = np.pad(~mask, 1, constant_values=True)
    lab, n = ndi.label(padded)
    filled = 0
    if n:
        sizes = np.bincount(lab.ravel())
        small = sizes < min_voxels
        small[0] = False
        small[lab[0, 0, 0]] = False  # el exterior toca el marco
        filled = int(small.sum())
        mask = mask | small[lab][1:-1, 1:-1, 1:-1]
    return mask, removed, filled


def _otsu_clean(image: np.ndarray, spacing, min_voxels: int = CLEAN_MIN_VOXELS) -> np.ndarray:
    return _clean_mask(_otsu(image, spacing), min_voxels)[0]


def clean_report(image: np.ndarray, spacing, min_voxels: int = CLEAN_MIN_VOXELS) -> dict:
    """Cuántos componentes y cavidades borraría ``otsu_clean`` (para no limpiar en silencio)."""
    _, removed, filled = _clean_mask(_otsu(image, spacing), min_voxels)
    return {"removed_components": removed, "filled_cavities": filled}


SEGMENTERS = {"global": _global, "otsu": _otsu, "smoothed_otsu": _smoothed_otsu}
EXTENSION_SEGMENTERS = {"otsu_clean": _otsu_clean}


def segment(name: str, image: np.ndarray, spacing) -> np.ndarray:
    registry = {**SEGMENTERS, **EXTENSION_SEGMENTERS}
    if name not in registry:
        raise ValueError(f"segmentador desconocido: {name!r}; opciones: {tuple(registry)}")
    return registry[name](image, spacing).astype(bool)
