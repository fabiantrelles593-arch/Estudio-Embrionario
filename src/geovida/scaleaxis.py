"""Eje de escala de medición (v0.4): la misma imagen, medida otra vez más gruesa.

Cada imagen se degrada ×2 y ×4 (promedio de bloques, como un detector de píxel
más grande) y se vuelve a segmentar y medir con el mismo segmentador. Lo que
cambia entre escalas es un indicio de que la medida nativa no ha convergido. Es
una transferencia de ideas conocidas: el Grid Convergence Index de la mecánica
de fluidos computacional (Roache 1994), la convergencia multimalla de los
estimadores digitales (Coeurjolly, Lachaud y Roussillon 2012) y, en estadística,
SIMEX (Cook y Stefanski 1994). Aquí solo se puede engrosar, no refinar, y eso
cambia la lógica: una deriva pequeña es NECESARIA pero no SUFICIENTE.

Límites que el código no oculta:
* Un rasgo que la imagen nativa ya perdió es invisible a todas las escalas.
* El promedio de bloques reduce el ruido y no reproduce la PSF de una
  adquisición real a menor resolución.
* Los números de Betti son discretos: no se extrapolan, solo se comprueba si
  coinciden entre escalas.

En bioimagen «5D» ya significa x, y, z, canal y tiempo (OME-NGFF). Este eje no
es eso: es una dimensión de la MEDICIÓN, no del espécimen.
"""
from __future__ import annotations

import math
import warnings

import numpy as np

from .segment import segment
from .topology import betti_numbers

DRIFT_CAP = 2.0      # tope de |ln(V_k / V_0)|; también el valor si el objeto desaparece
N_LEVELS = 2


def block_mean(image: np.ndarray) -> np.ndarray:
    """Promedio de bloques 2×2×2 (se recorta el borde si el tamaño es impar)."""
    nx, ny, nz = (s // 2 * 2 for s in image.shape)
    c = image[:nx, :ny, :nz]
    return c.reshape(nx // 2, 2, ny // 2, 2, nz // 2, 2).mean(axis=(1, 3, 5))


def pyramid_levels(image: np.ndarray, spacing, segmenter: str,
                   mask0: np.ndarray | None = None, n_levels: int = N_LEVELS) -> list[dict]:
    """Volumen y Betti a la escala nativa y a ×2, ×4 (mismo segmentador)."""
    sp = tuple(float(s) for s in spacing)
    img = np.asarray(image)
    levels = []
    for k in range(n_levels + 1):
        factor = 2**k
        sp_k = tuple(s * factor for s in sp)
        if k > 0:
            if min(img.shape) < 2:                   # ya no queda rejilla que promediar
                levels.append({"factor": factor, "spacing": sp_k, "volume": 0.0,
                               "betti": (0, 0, 0)})
                continue
            img = block_mean(img)
        if k == 0 and mask0 is not None:
            mask = np.asarray(mask0, dtype=bool)
        elif img.max() == img.min():                  # imagen constante: Otsu no está definido
            mask = np.zeros(img.shape, dtype=bool)
        else:
            with warnings.catch_warnings():           # Otsu avisa con rejillas de 3 vóxeles
                warnings.simplefilter("ignore", UserWarning)
                mask = segment(segmenter, img, sp_k)
        levels.append({"factor": factor, "spacing": sp_k,
                       "volume": float(mask.sum() * np.prod(sp_k)),
                       "betti": betti_numbers(mask, 26).as_tuple()})
    return levels


def _signed_drift(v0: float, vk: float) -> float:
    if v0 <= 0:
        return math.nan
    if vk <= 0:
        return -DRIFT_CAP
    return float(np.clip(math.log(vk / v0), -DRIFT_CAP, DRIFT_CAP))


def scale_observables(image: np.ndarray, spacing, segmenter: str,
                      mask0: np.ndarray | None = None) -> dict:
    """Deriva del volumen entre escalas (``dv*`` con signo, ``u_v*`` absoluta) y
    acuerdo del triple de Betti (``a*`` = 1.0 si coincide con la escala nativa)."""
    levels = pyramid_levels(image, spacing, segmenter, mask0=mask0)
    base = levels[0]
    out = {}
    for k in (1, 2):
        d = _signed_drift(base["volume"], levels[k]["volume"])
        out[f"dv{k}"] = d
        out[f"u_v{k}"] = abs(d) if math.isfinite(d) else math.nan
        out[f"a{k}"] = float(base["volume"] > 0 and levels[k]["betti"] == base["betti"])
    return out
