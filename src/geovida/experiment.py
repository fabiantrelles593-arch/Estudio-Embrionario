"""Barrido factorial de H1: ¿t/h predice el error de V, S y topología?

Unidad experimental = una realización independiente (forma x orientación/
desplazamiento aleatorios x ruido), nunca un voxel ni un corte. Cada
realización se renderiza una sola vez y se mide con los tres segmentadores
(medidas repetidas sobre la misma imagen; el análisis lo tiene en cuenta).
"""
from __future__ import annotations

import itertools
import multiprocessing as mp
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .imaging import render, spec_for_t_over_h
from .measure import measure_mask, relative_errors, surface_distance_stats, dice
from .phantoms import EXTRA_NAMES, NEW_NAMES, PHANTOM_NAMES, make_phantom
from .segment import SEGMENTERS, segment

T_OVER_H = (1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0)
ANISOTROPY = (1.0, 2.0, 3.0)
PROFILES = ("ideal", "realistic")
BASE_SEED = 20261109
H3_SEED = 20261110  # semilla propia de la confirmación H3 (formas y flujos nuevos)
H6_SHAPES = PHANTOM_NAMES + EXTRA_NAMES   # las 10 formas de H6 (y de la calibración de H9)
ALL_SHAPES = H6_SHAPES + NEW_NAMES        # índice de semilla; los índices previos no cambian
# v0.4: perfiles de imagen «desplazados», nunca usados para calibrar. Sirven para
# medir cuánto depende el certificado del simulador con el que se calibró.
SHIFT_PROFILES = ("blurry", "noisy")
_SEED_PROFILES = PROFILES + SHIFT_PROFILES


@dataclass(frozen=True)
class Condition:
    shape: str
    t_over_h: float
    anisotropy: float
    profile: str
    rep: int


def full_design(n_reps: int) -> list[Condition]:
    return [Condition(s, t, a, p, r)
            for s, t, a, p, r in itertools.product(
                PHANTOM_NAMES, T_OVER_H, ANISOTROPY, PROFILES, range(n_reps))]


H6_SEED = 20261114      # confirmación del semáforo (H6)
H6_CAL_SEED = 20261116  # calibración del semáforo (elige la variable y congela el modelo)


def h6_design(n_reps: int) -> list[Condition]:
    """Diseño de H6: las 10 formas, misma rejilla que H1 y H3."""
    return [Condition(s, t, a, p, r)
            for s, t, a, p, r in itertools.product(
                H6_SHAPES, T_OVER_H, ANISOTROPY, PROFILES, range(n_reps))]


def h3_design(n_reps: int) -> list[Condition]:
    """Diseño de la confirmación H3: formas nuevas, misma rejilla que H1."""
    return [Condition(s, t, a, p, r)
            for s, t, a, p, r in itertools.product(
                EXTRA_NAMES, T_OVER_H, ANISOTROPY, PROFILES, range(n_reps))]


def _rng(cond: Condition, base_seed: int) -> np.random.Generator:
    key = [base_seed, ALL_SHAPES.index(cond.shape), int(round(cond.t_over_h * 100)),
           int(round(cond.anisotropy * 10)), _SEED_PROFILES.index(cond.profile), cond.rep]
    return np.random.default_rng(np.random.SeedSequence(key))


def run_condition(cond: Condition, base_seed: int = BASE_SEED,
                  segmenters: tuple[str, ...] | None = None,
                  extra=None) -> list[dict]:
    """Una realización medida con cada segmentador.

    ``extra(image, spacing, mask, seg_name, meas) -> dict`` (opcional; función de
    módulo, para poder usarse con multiprocessing) añade columnas a cada fila sin
    tocar las existentes. v0.4 lo usa para los observables del certificado.
    """
    segmenters = tuple(SEGMENTERS) if segmenters is None else tuple(segmenters)
    t = 1.0
    ph = make_phantom(cond.shape, t=t)
    spec = spec_for_t_over_h(cond.t_over_h, cond.anisotropy, cond.profile, t=t)
    out = render(ph, spec, _rng(cond, base_seed))
    ref = out.coverage >= 0.5
    h_xy, h_z = spec.spacing[0], spec.spacing[2]
    tr = ph.truth
    rows = []
    for seg_name in segmenters:
        mask = segment(seg_name, out.image, out.spacing)
        meas = measure_mask(mask, out.spacing)
        row = {
            "shape": cond.shape, "t_over_h": cond.t_over_h,
            "anisotropy": cond.anisotropy, "profile": cond.profile,
            "rep": cond.rep, "segmenter": seg_name,
            "t_solid_over_hxy": tr.t_solid / h_xy,
            "t_solid_over_hz": tr.t_solid / h_z,
            "t_solid_over_hmax": tr.t_solid / max(h_xy, h_z),
            "t_min_over_hxy": tr.t_min / h_xy,
            "t_min_over_hz": tr.t_min / h_z,
            "t_min_over_hmax": tr.t_min / max(h_xy, h_z),
            "volume_true": tr.volume, "area_true": tr.surface_area,
            **meas, **relative_errors(meas, tr),
            "dice": dice(mask, ref),
            **surface_distance_stats(mask, ref, out.spacing),
        }
        if extra is not None:
            row.update(extra(out.image, out.spacing, mask, seg_name, meas))
        rows.append(row)
    return rows


def _worker(args):
    cond, base_seed, segmenters, extra = args
    return run_condition(cond, base_seed, segmenters, extra)


def run_sweep(conditions: list[Condition], n_jobs: int = 1,
              base_seed: int = BASE_SEED,
              segmenters: tuple[str, ...] | None = None,
              extra=None) -> pd.DataFrame:
    jobs = [(c, base_seed, segmenters, extra) for c in conditions]
    if n_jobs <= 1:
        chunks = [_worker(j) for j in jobs]
    else:
        with mp.get_context("fork").Pool(n_jobs) as pool:
            chunks = pool.map(_worker, jobs, chunksize=4)
    return pd.DataFrame([r for chunk in chunks for r in chunk])
