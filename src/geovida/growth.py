"""H8: el semáforo de adecuación en la estimación de crecimiento 4D.

Un objeto que crece con vóxel fijo empieza por debajo de la resolución. La tasa
de crecimiento (pendiente de ln V frente a la etapa) se estima con todas las
etapas, sin las que el semáforo marca en rojo, o solo con las verdes, y se
compara con la tasa verdadera exacta (``docs/PREREGISTRO_H8.md``).

* Cada etapa es un espécimen independiente (pseudo-tiempo transversal).
* La luz sale de ``budget.adequacy``: solo máscara y vóxel, con el modelo
  congelado en H6. Aquí no se reajusta nada.
* Con menos de 3 etapas válidas la tasa es NaN («no evaluable»), nunca un número.
* Una etapa con máscara vacía (V = 0) no tiene logaritmo: no entra en ningún
  ajuste (aclaración escrita en el preregistro antes de correr).
"""
from __future__ import annotations

import itertools
import math
import multiprocessing as mp
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .budget import adequacy
from .experiment import ALL_SHAPES, ANISOTROPY, PROFILES
from .h3 import PREREGISTERED_SEGMENTERS
from .imaging import IMAGING_PROFILES, ImagingSpec, render
from .phantoms import make_phantom
from .segment import segment

H8_SEED = 20261119
H8_PILOT_SEED = 20261118
N_STAGES = 8
GROWTH_FACTOR = 1.35
T0_OVER_H = 2.0
TRUE_RATE = 3.0 * math.log(GROWTH_FACTOR)     # 0.900 por etapa
H8_SHAPES = ("ball", "ellipsoid", "oblate", "capsule", "cylinder")
MIN_STAGES = 3
VOXEL_RULE_MIN = 100        # regla simple sin semáforo (extensión descriptiva)
MIN_DEFINED = 30            # series con tasa no_red definida para que un estrato sea evaluable
USEFUL_ERR = 0.05
MAX_UNDEFINED = 0.25


@dataclass(frozen=True)
class Series:
    shape: str
    anisotropy: float
    profile: str
    rep: int


def stage_sizes() -> np.ndarray:
    """Grosor del objeto en cada etapa, en vóxeles (h_xy = 1)."""
    return T0_OVER_H * GROWTH_FACTOR ** np.arange(N_STAGES)


def design_h8(n_reps: int) -> list[Series]:
    return [Series(s, a, p, r)
            for s, a, p, r in itertools.product(H8_SHAPES, ANISOTROPY, PROFILES, range(n_reps))]


def _rng(series: Series, stage: int, base_seed: int) -> np.random.Generator:
    key = [base_seed, ALL_SHAPES.index(series.shape), int(round(series.anisotropy * 10)),
           PROFILES.index(series.profile), series.rep, stage]
    return np.random.default_rng(np.random.SeedSequence(key))


def run_series(series: Series, base_seed: int = H8_SEED,
               segmenters: tuple[str, ...] = PREREGISTERED_SEGMENTERS) -> list[dict]:
    rows = []
    for stage, t in enumerate(stage_sizes()):
        ph = make_phantom(series.shape, t=float(t))
        spec = ImagingSpec(h_xy=1.0, anisotropy=series.anisotropy,
                           **IMAGING_PROFILES[series.profile])
        out = render(ph, spec, _rng(series, stage, base_seed))
        for seg in segmenters:
            mask = segment(seg, out.image, out.spacing)
            rep = adequacy(mask, out.spacing, seg, series.profile)
            rows.append({
                "shape": series.shape, "anisotropy": series.anisotropy,
                "profile": series.profile, "rep": series.rep, "stage": stage,
                "t_over_h": float(t), "h_xy": 1.0, "segmenter": seg,
                "volume_true": ph.truth.volume, "volume": rep["volume"],
                "n_voxels": int(mask.sum()), "feature": rep["feature"],
                "p_volume_ok": rep["p_volume_ok"], "light": rep["light"],
            })
    return rows


def _worker(args):
    return run_series(*args)


def run_h8(design: list[Series], n_jobs: int = 1, base_seed: int = H8_SEED) -> pd.DataFrame:
    jobs = [(s, base_seed) for s in design]
    if n_jobs <= 1:
        chunks = [_worker(j) for j in jobs]
    else:
        with mp.get_context("fork").Pool(n_jobs) as pool:
            chunks = pool.map(_worker, jobs, chunksize=4)
    return pd.DataFrame([r for chunk in chunks for r in chunk])


# --- tasas ------------------------------------------------------------------

def fit_rate(stages, volumes, keep) -> float:
    """Pendiente de mínimos cuadrados de ln V sobre la etapa, con las etapas
    ``keep`` de volumen positivo; NaN si quedan menos de ``MIN_STAGES``."""
    k = np.asarray(stages, dtype=float)
    v = np.asarray(volumes, dtype=float)
    sel = np.asarray(keep, dtype=bool) & np.isfinite(v) & (v > 0)
    if int(sel.sum()) < MIN_STAGES:
        return math.nan
    return float(np.polyfit(k[sel], np.log(v[sel]), 1)[0])


SERIES_KEYS = ["shape", "anisotropy", "profile", "rep", "segmenter"]


def rates_table(df: pd.DataFrame) -> pd.DataFrame:
    """Una fila por serie y segmentador con las tasas de cada estimador y su error."""
    rows = []
    for key, g in df.groupby(SERIES_KEYS, sort=True):
        g = g.sort_values("stage")
        k, v = g["stage"].to_numpy(float), g["volume"].to_numpy(float)
        light = g["light"].to_numpy()
        ones = np.ones(len(g), dtype=bool)
        masks = {"all": ones, "no_red": light != "rojo", "green": light == "verde",
                 "vox100": g["n_voxels"].to_numpy() >= VOXEL_RULE_MIN}
        row = dict(zip(SERIES_KEYS, key))
        for name, keep in masks.items():
            rate = fit_rate(k, v, keep)
            row[f"rate_{name}"] = rate
            row[f"err_{name}"] = abs(rate / TRUE_RATE - 1.0) if math.isfinite(rate) else math.nan
            row[f"n_{name}"] = int((keep & (v > 0)).sum())
        oracle = fit_rate(k, g["volume_true"].to_numpy(float), ones)
        row["rate_oracle"] = oracle
        row["err_oracle"] = abs(oracle / TRUE_RATE - 1.0)
        rows.append(row)
    return pd.DataFrame(rows)


def _grade_all_but(fails: int, evaluable: int) -> str:
    if evaluable == 0:
        return "no evaluable"
    return "apoyada" if fails == 0 else ("parcial" if fails == 1 else "no apoyada")


def evaluate_h8(rates: pd.DataFrame) -> dict:
    strata = []
    for seg in PREREGISTERED_SEGMENTERS:
        for prof in PROFILES:
            g = rates[(rates["segmenter"] == seg) & (rates["profile"] == prof)]
            if g.empty:
                continue
            defined = g[g["err_no_red"].notna()]
            n, nd = int(len(g)), int(len(defined))
            row = {"stratum": f"{seg}|{prof}", "n_series": n, "n_defined": nd,
                   "frac_undefined": 1.0 - nd / n, "evaluable": bool(nd >= MIN_DEFINED)}

            def med(col, frame=defined):
                s = frame[col].dropna()
                return float(s.median()) if len(s) else math.nan

            row["median_err_no_red"] = med("err_no_red")
            row["median_err_all_paired"] = med("err_all")
            row["median_err_all_everything"] = med("err_all", g)
            row["median_err_green"] = med("err_green", g)
            row["median_err_vox100"] = med("err_vox100", g)
            row["frac_undefined_vox100"] = float(g["err_vox100"].isna().mean())
            both = g[g["err_no_red"].notna() & g["err_vox100"].notna()]
            row["median_err_no_red_both"] = med("err_no_red", both)
            row["median_err_vox100_both"] = med("err_vox100", both)
            row["p90_err_no_red"] = (float(defined["err_no_red"].quantile(0.9))
                                     if nd else math.nan)
            row["p90_err_all_paired"] = float(defined["err_all"].quantile(0.9)) if nd else math.nan
            row["frac_no_red_wins"] = (float((defined["err_no_red"] < defined["err_all"]).mean())
                                       if nd else math.nan)
            row["h8a_better"] = bool(row["evaluable"]
                                     and row["median_err_no_red"] < row["median_err_all_paired"])
            row["h8b_useful"] = bool(row["evaluable"] and row["median_err_no_red"] <= USEFUL_ERR)
            row["h8c_cheap"] = bool(row["frac_undefined"] <= MAX_UNDEFINED + 1e-12)
            strata.append(row)
    ev = [r for r in strata if r["evaluable"]]
    a_fail = sum(not r["h8a_better"] for r in ev)
    b_fail = sum(not r["h8b_useful"] for r in ev)
    c_cnt = sum(r["h8c_cheap"] for r in strata)
    if not strata:
        vc = "no evaluable"
    else:
        vc = "apoyada" if c_cnt >= 4 else ("parcial" if c_cnt == 3 else "no apoyada")
    vox_wins = sum(r["median_err_vox100_both"] <= r["median_err_no_red_both"]
                   for r in strata if math.isfinite(r["median_err_vox100_both"])
                   and math.isfinite(r["median_err_no_red_both"]))
    return {
        "strata": strata,
        "h8a": {"failing": a_fail, "evaluable": len(ev), "n": len(strata),
                "verdict": _grade_all_but(a_fail, len(ev))},
        "h8b": {"failing": b_fail, "evaluable": len(ev), "n": len(strata),
                "verdict": _grade_all_but(b_fail, len(ev))},
        "h8c": {"count": c_cnt, "n": len(strata), "verdict": vc},
        "extension_vox100_at_least_as_good_strata": int(vox_wins),
    }
