"""Barridos del certificado vectorial (v0.4): diseños, semillas y observables.

Cuatro conjuntos, todos con la rejilla de H1 (t/h × anisotropía):

* ``cal``     las 10 formas de H6, perfiles ``ideal`` y ``realistic``: de aquí
              salen el modelo topológico y el umbral de deriva, que se CONGELAN.
* ``test``    las mismas formas con semilla nueva (confirmación).
* ``unseen``  mancuerna y copa: formas no convexas que la calibración nunca vio.
* ``shift``   las 10 formas con perfiles de imagen ``blurry`` y ``noisy``, que la
              calibración nunca vio (dominio desplazado).

Los observables se calculan solo con la imagen, el vóxel, la máscara y el nombre
del segmentador: ``cert_extra`` no recibe la verdad.
"""
from __future__ import annotations

import itertools

from .domain import domain_observables
from .experiment import (ANISOTROPY, H6_SHAPES, PROFILES, SHIFT_PROFILES, T_OVER_H, US_PROFILES,
                         US_SHIFT_PROFILES, Condition)
from .phantoms import NEW_NAMES
from .scaleaxis import scale_observables
from .topomargin import intensity_margin, topological_margin

H9_PILOT_SEED = 20261122
H9_CAL_SEED = 20261123
H9_TEST_SEED = 20261124
H9_SHIFT_SEED = 20261125

# v0.5 (H12): ecografía 3D simulada. Semillas nuevas; la rejilla añade dos niveles finos (16 y 24)
# porque con moteado los segmentadores simples necesitan más resolución para entrar en verde.
H12_PILOT_SEED = 20261130
H12_CAL_SEED = 20261131
H12_TEST_SEED = 20261132
H12_SHIFT_SEED = 20261133
T_OVER_H_US = T_OVER_H + (16.0, 24.0)

OBSERVABLE_COLUMNS = ("tau_dil", "tau_ero", "m_lo", "m_hi", "contrast_hat",
                      "dv1", "dv2", "u_v1", "u_v2", "a1", "a2", "snr_hat", "edge_width")


def _design(shapes, profiles, n_reps: int, levels=T_OVER_H) -> list[Condition]:
    return [Condition(s, t, a, p, r)
            for s, t, a, p, r in itertools.product(shapes, levels, ANISOTROPY, profiles,
                                                   range(n_reps))]


def design_cal(n_reps: int) -> list[Condition]:
    return _design(H6_SHAPES, PROFILES, n_reps)


def design_unseen(n_reps: int) -> list[Condition]:
    return _design(NEW_NAMES, PROFILES, n_reps)


def design_shift(n_reps: int) -> list[Condition]:
    return _design(H6_SHAPES, SHIFT_PROFILES, n_reps)


def design_us_cal(n_reps: int) -> list[Condition]:
    return _design(H6_SHAPES, US_PROFILES, n_reps, T_OVER_H_US)


def design_us_unseen(n_reps: int) -> list[Condition]:
    return _design(NEW_NAMES, US_PROFILES, n_reps, T_OVER_H_US)


def design_us_shift(n_reps: int) -> list[Condition]:
    return _design(H6_SHAPES, US_SHIFT_PROFILES, n_reps, T_OVER_H_US)


def cert_extra(image, spacing, mask, seg_name, meas) -> dict:
    """Observables del certificado para una fila del barrido (sin verdad)."""
    out = topological_margin(mask, spacing)
    out.update(intensity_margin(image, spacing, seg_name))
    out.update(scale_observables(image, spacing, seg_name, mask0=mask))
    out.update(domain_observables(image, mask, spacing, meas["area_sdf"]))
    return out
