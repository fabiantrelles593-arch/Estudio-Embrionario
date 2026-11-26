"""H25: la luz de H24 con una guardia de dominio que no depende del signo del contraste (docs/h25/PREREGISTRO_H25.md).

H24 se paró porque, en 27 de 34 casos de ventrículo, la guardia no pudo calcular sus índices: el ventrículo es más
oscuro que el fondo lejano y ``domain.domain_observables`` declara no calculable cualquier contraste ≤ 0. H25 cambia
solo eso:

* ``domain_observables_abs``: los mismos ``snr_hat`` y ``edge_width``, con ``snr_hat = |C| / σ`` y no calculable solo
  si C = 0. Donde C > 0 da exactamente lo mismo que la guardia antigua; con la imagen invertida da lo mismo que con la
  original.
* Error, señales, regla, puertas y criterios: los de ``geovida.h24``, sin tocar un número.

``domain.py`` no se modifica, para que los estudios anteriores sigan siendo reproducibles. Solo investigación con datos
animales publicados; sin uso clínico.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import ndimage as ndi

from . import h18, h24
from .domain import BAND_VOXELS, FAR_VOXELS, SNR_CAP, domain_observables
from .measure import _area_sdf

NETS_SHA256 = h24.NETS_SHA256
THRESHOLDS = h24.THRESHOLDS
SEED_G0, N_G0 = h24.SEED_G0, h24.N_G0
OLD = {"snr_hat": "snr_hat_h24", "edge_width": "edge_width_h24"}


def domain_observables_abs(image: np.ndarray, mask: np.ndarray, spacing, area: float) -> dict:
    """``domain.domain_observables`` con el contraste en valor absoluto (§5.1 del preregistro)."""
    nan = {"snr_hat": math.nan, "edge_width": math.nan, "contrast": math.nan}
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
    if not math.isfinite(contrast) or contrast == 0:
        return {**nan, "contrast": contrast}
    c = abs(contrast)
    snr = SNR_CAP if sigma <= c / SNR_CAP else c / sigma
    inside = ndi.distance_transform_edt(mask, sampling=sp)
    near = (outside <= BAND_VOXELS * hmin) & (inside <= BAND_VOXELS * hmin)
    norm = (img - mu_bg) / contrast
    band = near & (norm > 0.25) & (norm < 0.75)
    width = (float(band.sum() * np.prod(sp)) / (area * hmin)) if area > 0 else math.nan
    return {"snr_hat": float(min(snr, SNR_CAP)), "edge_width": width, "contrast": contrast}


def observables(image: np.ndarray, spacing, mask: np.ndarray) -> dict:
    """Índices de la guardia nueva (``snr_hat``, ``edge_width``) y de la antigua (``*_h24``, para H25h)."""
    sp = tuple(float(s) for s in spacing)
    if not mask.any():
        return {"snr_hat": math.nan, "edge_width": math.nan, "contrast": math.nan,
                "snr_hat_h24": math.nan, "edge_width_h24": math.nan}
    area = float(_area_sdf(mask, sp))
    old = domain_observables(image, mask, sp, area)
    return {**domain_observables_abs(image, mask, sp, area), **{OLD[k]: v for k, v in old.items()}}


def old_guard_view(df: pd.DataFrame) -> pd.DataFrame:
    """La misma tabla con los índices de la guardia antigua en las columnas que lee ``h18.inside``."""
    return df.drop(columns=list(OLD)).rename(columns={v: k for k, v in OLD.items()})


def positive(r: dict) -> bool:
    return math.isfinite(r["contrast"]) and r["contrast"] > 0


def g0(rows: list[dict], extra: list[dict] | None = None) -> dict:
    """G0 de H24 más: guardia nueva calculable en los 5 y, en los casos con C > 0, idéntica a la antigua.

    Si ninguno de los 5 tiene C > 0, ``extra`` trae los siguientes casos de ajuste (mismo orden con semilla) hasta el
    primero con C > 0; solo se usan para esa comprobación."""
    base = h24.g0(rows)
    guard_ok = [math.isfinite(r["snr_hat"]) and math.isfinite(r["edge_width"]) for r in rows]
    same_ok = [r["snr_hat"] == r["snr_hat_h24"] and r["edge_width"] == r["edge_width_h24"]
               for r in rows + (extra or []) if positive(r)]
    return {**base, "guard_computable": guard_ok, "n_positive_contrast": len(same_ok), "same_as_old": same_ok,
            "passed": bool(base["passed"] and all(guard_ok) and same_ok and all(same_ok))}


def out_of_fold(cal: pd.DataFrame) -> pd.DataFrame:
    return h24.out_of_fold(cal)


def evaluate_test(lit: pd.DataFrame, old_envelope: dict, n_boot: int = h18.N_BOOT, seed: int = h18.SEED) -> dict:
    """H25b y H25d (primarias); H25a, c, e, g y h (descriptivas). Mismos cálculos que ``h24.evaluate_test``."""
    ev = h24.evaluate_test(lit, n_boot, seed)
    out = {k.replace("h24", "h25"): v for k, v in ev.items()}
    old = h24.lights(old_guard_view(lit.drop(columns=["in_domain", "light", "light_without_guard"])), old_envelope)
    g_old = old[old["light"] == "verde"]
    out["h25h"] = {"in_domain_old_guard": float(old["in_domain"].mean()),
                   "lights_old_guard": old["light"].value_counts().to_dict(),
                   "green_old_guard": int(len(g_old)), "green_old_guard_bad": int(h24.bad(g_old).sum())}
    return out
