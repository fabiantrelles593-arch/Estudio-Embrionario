"""Veredictos de la confirmación H3 (Q) y de la evaluación H4 (área SDF).

Aplica los criterios de ``docs/PREREGISTRO_H3.md`` tal como están escritos.
Regla central: un valor no calculable es «no evaluable», nunca «no apoyada».
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .analysis import (
    calibration_error, fit_frozen_logit, logloss, x_at_probability,
)

PREREGISTERED_SEGMENTERS = ("global", "otsu", "smoothed_otsu")
PROFILES = ("ideal", "realistic")
V_TOL = 0.05


def grade(count: int, n: int, supported_min: int, partial_min: int) -> str:
    if n == 0:
        return "no evaluable"
    if count >= supported_min:
        return "apoyada"
    if count >= partial_min:
        return "parcial"
    return "no apoyada"


def evaluate_h3(df: pd.DataFrame, frozen: dict) -> dict:
    rows = []
    for seg in PREREGISTERED_SEGMENTERS:
        for prof in PROFILES:
            key = f"{seg}|{prof}"
            g = df[(df["segmenter"] == seg) & (df["profile"] == prof)]
            y = (g["err_volume"].abs() <= V_TOL).to_numpy(float)
            mdl = frozen["models"][key]
            xq, xt = g["q_over_hgeo"].to_numpy(float), g["t_solid_over_hgeo"].to_numpy(float)
            row = {"stratum": key, "n": int(len(g)), "p_ok": float(y.mean()),
                   "logloss_q": logloss(mdl["q_model"], xq, y),
                   "logloss_t": logloss(mdl["t_model"], xt, y),
                   "ece_q": calibration_error(mdl["q_model"], xq, y),
                   "ece_t": calibration_error(mdl["t_model"], xt, y),
                   "q_star_frozen": mdl["q_star_095"]}
            row["h3a_q_better"] = bool(row["logloss_q"] < row["logloss_t"])
            row["h3b_calibrated"] = bool(row["ece_q"] <= 0.10)
            evaluable = y.min() != y.max()
            q_star = math.nan
            if evaluable:
                refit = fit_frozen_logit(xq, y)
                q_star = x_at_probability(refit, 0.95) if refit["slope"] > 0 else math.nan
            row["q_star_refit"] = q_star
            row["h3c_evaluable"] = bool(evaluable and not math.isnan(q_star))
            ratio = q_star / mdl["q_star_095"] if row["h3c_evaluable"] else math.nan
            row["q_star_ratio"] = ratio
            row["h3c_conserved"] = bool(row["h3c_evaluable"] and 1 / 1.5 <= ratio <= 1.5)
            rows.append(row)
    n = len(rows)
    a = sum(r["h3a_q_better"] for r in rows)
    b = sum(r["h3b_calibrated"] for r in rows)
    c_ok = sum(r["h3c_conserved"] for r in rows)
    c_na = sum(not r["h3c_evaluable"] for r in rows)
    if c_ok >= 4:
        c_verdict = "apoyada"
    elif c_ok + c_na >= 4:
        c_verdict = "no concluyente"
    else:
        c_verdict = "no apoyada"
    return {
        "strata": rows,
        "h3a": {"count": a, "n": n, "verdict": grade(a, n, 6, 4)},
        "h3b": {"count": b, "n": n, "verdict": grade(b, n, 5, 4)},
        "h3c": {"count": c_ok, "not_evaluable": c_na, "n": n, "verdict": c_verdict},
    }


def evaluate_h4(df: pd.DataFrame) -> dict:
    g = df[(df["segmenter"] == "global") & (df["profile"] == "ideal")
           & (df["anisotropy"] == 1.0)]
    med = g.groupby(["shape", "t_over_h"])[["err_area_sdf", "err_area_mc",
                                            "err_area_faces"]].median().reset_index()
    shapes = sorted(med["shape"].unique())
    hi = med[med["t_over_h"] >= 6.0]
    a_ok = bool(len(hi) > 0 and (hi["err_area_sdf"].abs() <= 0.10).all())
    cells = med[med["t_over_h"].isin([4.0, 6.0, 8.0, 12.0])]
    better = ((cells["err_area_sdf"].abs() < cells["err_area_mc"].abs())
              & (cells["err_area_sdf"].abs() < cells["err_area_faces"].abs()))
    lvl4 = med[med["t_over_h"] == 4.0]
    c_ok = bool(len(lvl4) > 0 and (lvl4["err_area_sdf"].abs() <= 0.25).all())
    return {
        "shapes": shapes,
        "medians": med.round(4).to_dict(orient="records"),
        "h4a": {"verdict": "apoyada" if a_ok else ("no evaluable" if len(hi) == 0 else "no apoyada")},
        "h4b": {"count": int(better.sum()), "n": int(len(cells)),
                "verdict": grade(int(better.sum()), int(len(cells)), 10, 10)},
        "h4c": {"verdict": "apoyada" if c_ok else ("no evaluable" if len(lvl4) == 0 else "no apoyada")},
    }
