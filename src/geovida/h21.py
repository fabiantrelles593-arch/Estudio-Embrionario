"""H21 (docs/PREREGISTRO_H21.md): ¿Crofton como estimador principal de área en lugar de ``area_sdf``?

Mismo simulador que H1–H6 (``geovida.experiment``) con formas y semilla nuevas. A cada máscara segmentada se
le añade ``area_crofton`` (``geovida.reference.crofton_area``, validado contra ITK en
``docs/COMPARACION_REFERENCIA.md``). La unidad de comparación es la **celda** forma × t/h × anisotropía ×
perfil × segmentador, resumida por la mediana del error relativo con signo de cada estimador.

Todo lo que fija un veredicto está en las constantes de este módulo y en ``verdicts``; no se cambia después
de ver los datos.
"""
from __future__ import annotations

import itertools
import math

import numpy as np
import pandas as pd

from .experiment import Condition
from .phantoms import H21_NAMES
from .reference import crofton_area

SEED = 20262101
SHAPES = H21_NAMES
T_OVER_H = (3.0, 4.0, 6.0, 8.0, 12.0)
ANISOTROPY = (1.0, 2.0)
PROFILES = ("ideal", "realistic", "noisy", "us_compound")
SEGMENTERS = ("global", "otsu", "smoothed_otsu")
REPS = 50

FINE = (8.0, 12.0)            # H21a
COARSE = (3.0, 4.0, 6.0)      # H21b
ANISO_TH = (6.0, 8.0, 12.0)   # H21c, con anisotropía 2
EVALUABLE_VOLUME = 0.20       # celda evaluable: |mediana del error de volumen| ≤ 20 % (la máscara sirve)
NONINFERIORITY = 0.02         # H21b: Crofton no peor que area_sdf en más de 2 puntos
SUPPORT, CONTRARY = 0.75, 0.25
NONINF_SUPPORT = 0.90
MIN_EVALUABLE = {"H21a": 48, "H21b": 72, "H21c": 36}   # la mitad de las celdas de cada hipótesis


def design(reps: int = REPS) -> list[Condition]:
    return [Condition(s, t, a, p, r)
            for s, t, a, p, r in itertools.product(SHAPES, T_OVER_H, ANISOTROPY, PROFILES, range(reps))]


def crofton_extra(image, spacing, mask, seg_name, meas) -> dict:
    """Columna extra del barrido: área de Crofton de la misma máscara que mide ``area_sdf``."""
    return {"area_crofton": crofton_area(mask, spacing)}


CELL = ["shape", "t_over_h", "anisotropy", "profile", "segmenter"]


def cell_table(df: pd.DataFrame) -> pd.DataFrame:
    """Medianas por celda de los errores relativos con signo, y comparaciones de H21a/b/c."""
    d = df.assign(err_area_crofton=(df["area_crofton"] - df["area_true"]) / df["area_true"])
    g = d.groupby(CELL)
    out = pd.DataFrame({
        "n": g.size(),
        "med_err_volume": g["err_volume"].median(),
        "med_err_sdf": g["err_area_sdf"].median(),
        "med_err_crofton": g["err_area_crofton"].median(),
        "med_err_mc": g["err_area_mc"].median(),
    }).reset_index()
    out["evaluable"] = out["med_err_volume"].abs() <= EVALUABLE_VOLUME
    out["crofton_better"] = out["med_err_crofton"].abs() < out["med_err_sdf"].abs()
    out["crofton_noninferior"] = out["med_err_crofton"].abs() <= out["med_err_sdf"].abs() + NONINFERIORITY
    return out


def _subset(cells: pd.DataFrame, t_over_h, anisotropy: float) -> pd.DataFrame:
    return cells[cells["t_over_h"].isin(t_over_h) & (cells["anisotropy"] == anisotropy)]


def _directional(sub: pd.DataFrame, key: str) -> dict:
    ev = sub[sub["evaluable"]]
    n = len(ev)
    frac = float(ev["crofton_better"].mean()) if n else math.nan
    if n < MIN_EVALUABLE[key]:
        verdict = "no_evaluable"
    elif frac >= SUPPORT:
        verdict = "apoyada"
    elif frac <= CONTRARY:
        verdict = "contraria"
    else:
        verdict = "no_concluyente"
    return {"cells": len(sub), "evaluable": n, "fraction_crofton_better": frac, "verdict": verdict}


def verdicts(cells: pd.DataFrame) -> dict:
    """H21a (primaria), H21b y H21c con los umbrales fijados arriba, y la decisión del §8."""
    a = _directional(_subset(cells, FINE, 1.0), "H21a")
    sb = _subset(cells, COARSE, 1.0)
    ev = sb[sb["evaluable"]]
    frac_b = float(ev["crofton_noninferior"].mean()) if len(ev) else math.nan
    if len(ev) < MIN_EVALUABLE["H21b"]:
        vb = "no_evaluable"
    else:
        vb = "apoyada" if frac_b >= NONINF_SUPPORT else "no_apoyada"
    b = {"cells": len(sb), "evaluable": len(ev), "fraction_noninferior": frac_b, "verdict": vb}
    c = _directional(_subset(cells, ANISO_TH, 2.0), "H21c")
    if a["verdict"] == "apoyada" and vb == "apoyada":
        decision = "cambiar_a_crofton"
    elif a["verdict"] == "apoyada":
        decision = "crofton_solo_a_resolucion_fina"
    else:
        decision = "mantener_area_sdf"
    return {"H21a": a, "H21b": b, "H21c": c, "decision": decision}


def descriptive(df: pd.DataFrame) -> pd.DataFrame:
    """Mediana del error con signo por estimador, t/h y perfil (anisotropía 1), para el informe."""
    d = df[df["anisotropy"] == 1.0].assign(
        err_area_crofton=(df["area_crofton"] - df["area_true"]) / df["area_true"])
    return (d.groupby(["profile", "t_over_h"])[["err_area_sdf", "err_area_crofton", "err_area_mc"]]
            .median().reset_index())


def summary_numbers(cells: pd.DataFrame) -> dict:
    """Cifras auxiliares: mediana entre celdas evaluables de |error| de cada estimador, fino y grueso."""
    out = {}
    for name, th in (("fine", FINE), ("coarse", COARSE)):
        ev = _subset(cells, th, 1.0)
        ev = ev[ev["evaluable"]]
        out[name] = {k: float(np.median(ev[c].abs())) if len(ev) else math.nan
                     for k, c in (("sdf", "med_err_sdf"), ("crofton", "med_err_crofton"), ("mc", "med_err_mc"))}
    return out
