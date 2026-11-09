"""Veredictos de la prueba de estrés 2D (``docs/PREREGISTRO_2D.md``)."""
from __future__ import annotations

import math

import pandas as pd

from .analysis import find_t_star


def _verdict(ok: bool | None) -> str:
    return "no evaluable" if ok is None else ("apoyada" if ok else "no apoyada")


def evaluate_h5(df: pd.DataFrame) -> dict:
    out: dict = {}

    # H5a: área con imagen ideal y umbral oráculo
    g = df[(df["profile"] == "ideal") & (df["segmenter"] == "global") & (df["t_over_h"] >= 4.0)]
    if g.empty:
        out["h5a"] = {"verdict": _verdict(None)}
    else:
        med = g.groupby(["shape", "t_over_h"])["err_area"].median().abs()
        out["h5a"] = {"max_abs_median": float(med.max()), "verdict": _verdict(bool((med <= 0.05).all()))}

    # H5b: moteado crudo + Otsu crudo, anillo
    g = df[(df["profile"] == "us_raw") & (df["segmenter"] == "otsu") & (df["shape"] == "annulus")]
    if g.empty:
        out["h5b"] = {"verdict": _verdict(None)}
    else:
        p = g.groupby("t_over_h")["topology_ok"].mean()
        out["h5b"] = {"max_proportion": float(p.max()), "verdict": _verdict(bool((p < 0.5).all()))}

    # H5c: régimen fiable con compounding (t* tipo H1) para algún segmentador
    g = df[(df["profile"] == "us_compound") & (df["shape"] == "annulus")]
    if g.empty:
        out["h5c"] = {"verdict": _verdict(None)}
    else:
        stars = {}
        for seg, gs in g.groupby("segmenter"):
            tab = gs.groupby("t_over_h")["topology_ok"].mean().sort_index()
            stars[seg] = find_t_star(list(tab.index), list(tab.values), 0.95)
        reached = {k: v for k, v in stars.items() if not math.isnan(v)}
        out["h5c"] = {"t_star_by_segmenter": stars, "verdict": _verdict(bool(reached))}

    # H5d: circunferencia estilo calibrador, compounding + smoothed_otsu
    g = df[(df["profile"] == "us_compound") & (df["segmenter"] == "smoothed_otsu")
           & (df["t_over_h"] >= 8.0) & (df["shape"].isin(["disk", "ellipse"]))]
    if g.empty:
        out["h5d"] = {"verdict": _verdict(None)}
    else:
        med = g.groupby(["shape", "t_over_h"])["err_hc"].median().abs()
        out["h5d"] = {"max_abs_median": float(med.max()), "verdict": _verdict(bool((med <= 0.033).all()))}

    # H5e: promediar ayuda (t/h = 8, smoothed_otsu, disk y ellipse)
    g = df[(df["segmenter"] == "smoothed_otsu") & (df["t_over_h"] == 8.0)
           & (df["shape"].isin(["disk", "ellipse"])) & (df["profile"].isin(["us_raw", "us_compound"]))]
    if g.empty or g["profile"].nunique() < 2:
        out["h5e"] = {"verdict": _verdict(None)}
    else:
        med = g.groupby(["shape", "profile"])["err_hc"].apply(lambda s: s.abs().median()).unstack()
        out["h5e"] = {"median_abs_hc": med.round(4).to_dict(),
                      "verdict": _verdict(bool((med["us_raw"] > med["us_compound"]).all()))}
    return out
