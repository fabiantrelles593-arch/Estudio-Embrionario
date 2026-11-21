"""Guardia de dominio (v0.4): el certificado debe saber cuándo no sabe.

El semáforo de H6 se calibró con dos perfiles de imagen. El piloto de v0.4 mostró
que, con más desenfoque o más ruido que en la calibración, da luz verde falsa
hasta en el 98 % de los casos. La guardia mide en la propia imagen dos índices y
los compara con la envolvente que vio la calibración:

* ``snr_hat``     contraste (media dentro − media del fondo lejano) dividido por
                  el ruido del fondo lejano (desviación robusta por MAD).
* ``edge_width``  grosor de la banda de transición del borde: volumen de los
                  vóxeles cercanos a la frontera con intensidad entre el 25 % y
                  el 75 % del contraste, dividido por el área medida, en vóxeles
                  finos. Crece con el desenfoque.

Fuera de la envolvente no hay luz verde: hay que recalibrar para ese tipo de
imagen. No es un estimador de la PSF ni del ruido; es una alarma.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import ndimage as ndi

DOMAIN_COLUMNS = ("snr_hat", "edge_width")
SNR_CAP = 1000.0          # imagen sin ruido medible
FAR_VOXELS = 3.0          # el fondo «lejano» empieza a 3 vóxeles finos de la máscara
BAND_VOXELS = 3.0         # la banda del borde se busca a menos de 3 vóxeles finos
ENVELOPE_QUANTILES = (0.01, 0.99)


def domain_observables(image: np.ndarray, mask: np.ndarray, spacing, area: float) -> dict:
    """``snr_hat`` y ``edge_width`` de una imagen y su máscara (sin verdad).

    ``area`` es el área medida de la máscara (``area_sdf`` de ``measure_mask``).
    """
    nan = {"snr_hat": math.nan, "edge_width": math.nan}
    mask = np.asarray(mask, dtype=bool)
    if not mask.any() or mask.all():
        return nan
    sp = np.asarray(spacing, dtype=float)
    hmin = float(sp.min())
    img = np.asarray(image, dtype=float)
    outside = ndi.distance_transform_edt(~mask, sampling=sp)
    far = outside > FAR_VOXELS * hmin
    if far.sum() < 30:
        return nan
    bg = img[far]
    mu_bg = float(np.median(bg))
    sigma = 1.4826 * float(np.median(np.abs(bg - mu_bg)))
    contrast = float(img[mask].mean() - mu_bg)
    if not math.isfinite(contrast) or contrast <= 0:
        return nan
    snr = SNR_CAP if sigma <= contrast / SNR_CAP else contrast / sigma
    inside = ndi.distance_transform_edt(mask, sampling=sp)
    near = (outside <= BAND_VOXELS * hmin) & (inside <= BAND_VOXELS * hmin)
    norm = (img - mu_bg) / contrast
    band = near & (norm > 0.25) & (norm < 0.75)
    width = (float(band.sum() * np.prod(sp)) / (area * hmin)) if area > 0 else math.nan
    return {"snr_hat": float(min(snr, SNR_CAP)), "edge_width": width}


def fit_envelopes(df: pd.DataFrame, quantiles=ENVELOPE_QUANTILES) -> dict:
    """Por estrato (segmentador|perfil): intervalo central de cada índice en la calibración."""
    env = {}
    for (seg, prof), g in df.groupby(["segmenter", "profile"]):
        env[f"{seg}|{prof}"] = {
            c: [float(g[c].quantile(quantiles[0])), float(g[c].quantile(quantiles[1]))]
            for c in DOMAIN_COLUMNS}
    return env


def in_domain(obs: dict, envelope: dict) -> bool:
    """True si todos los índices son finitos y caen dentro de la envolvente."""
    for c in DOMAIN_COLUMNS:
        v = obs.get(c, math.nan)
        lo, hi = envelope[c]
        if v is None or not math.isfinite(v) or v < lo - 1e-12 or v > hi + 1e-12:
            return False
    return True


def in_domain_column(df: pd.DataFrame, envelopes: dict, declared_profile=None) -> np.ndarray:
    """Versión vectorizada para tablas de barrido. ``declared_profile`` permite
    declarar un perfil distinto del real (dominio desplazado)."""
    out = np.zeros(len(df), dtype=bool)
    prof = df["profile"] if declared_profile is None else pd.Series(declared_profile, index=df.index)
    for (seg, p), idx in df.groupby([df["segmenter"], prof]).groups.items():
        env = envelopes.get(f"{seg}|{p}")
        if env is None:
            continue
        g = df.loc[idx]
        ok = np.ones(len(g), dtype=bool)
        for c in DOMAIN_COLUMNS:
            v = g[c].to_numpy(float)
            ok &= np.isfinite(v) & (v >= env[c][0] - 1e-12) & (v <= env[c][1] + 1e-12)
        out[df.index.get_indexer(idx)] = ok
    return out
