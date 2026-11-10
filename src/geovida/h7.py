"""Veredictos de H7: limpieza 2D que escala con el objeto (``docs/PREREGISTRO_H7.md``).

Aplica los criterios tal como están escritos. La comparación base/limpia es
pareada: las dos máscaras salen de la misma imagen. Un valor no calculable es
«no evaluable», nunca «no apoyada».
"""
from __future__ import annotations

import pandas as pd

PRIMARY = ("smoothed_otsu", "smoothed_otsu_s2")
PROFILE = "us_compound"
HELP_SHAPES = ("disk", "ellipse", "annulus")
HELP_LEVELS = (8.0, 12.0, 20.0)
AREA_LEVELS = (6.0, 8.0, 12.0, 20.0)
HARM_SHAPE = "ring_tight"
HARM_LEVELS = (6.0, 8.0, 12.0, 20.0)
MARGIN_BELOW = 0.90        # una celda tiene margen si la topología base < 0.90
CLOSE_FRACTION = 0.5       # la limpieza «cierra» si recupera >= la mitad del margen
AREA_TOL = 0.01            # cambio máximo del error mediano absoluto de área
DAMAGE_TOL = 0.10          # caída máxima tolerada de topología correcta en ring_tight


def paired_table(df: pd.DataFrame) -> pd.DataFrame:
    """Por celda y segmentador base: aciertos antes y después, e imágenes que la
    limpieza arregla (mal -> bien) y estropea (bien -> mal)."""
    keys = ["shape", "t_over_h", "profile", "base", "rep"]
    base = df[~df["cleaned"]].set_index(keys)
    clean = df[df["cleaned"]].set_index(keys)
    j = base[["topology_ok", "err_area"]].join(
        clean[["topology_ok", "err_area"]], lsuffix="_base", rsuffix="_clean", how="inner")
    j = j.reset_index()
    j["tb"] = j["topology_ok_base"].astype(bool)
    j["tc"] = j["topology_ok_clean"].astype(bool)
    j["fixed"] = ~j["tb"] & j["tc"]
    j["broken"] = j["tb"] & ~j["tc"]
    j["abs_area_base"] = j["err_area_base"].abs()
    j["abs_area_clean"] = j["err_area_clean"].abs()
    g = j.groupby(["shape", "t_over_h", "profile", "base"])
    out = g.agg(n=("tb", "size"), topo_base=("tb", "mean"), topo_clean=("tc", "mean"),
                fixed=("fixed", "sum"), broken=("broken", "sum"),
                med_abs_area_base=("abs_area_base", "median"),
                med_abs_area_clean=("abs_area_clean", "median")).reset_index()
    return out.rename(columns={"base": "segmenter"})


def _cells(tab: pd.DataFrame, shapes, levels) -> pd.DataFrame:
    return tab[(tab["profile"] == PROFILE) & tab["segmenter"].isin(PRIMARY)
               & tab["shape"].isin(shapes) & tab["t_over_h"].isin(levels)]


def evaluate_h7(df: pd.DataFrame) -> dict:
    tab = paired_table(df)

    # H7a: la limpieza ayuda donde hay margen
    a = _cells(tab, HELP_SHAPES, HELP_LEVELS)
    margin = a[a["topo_base"] < MARGIN_BELOW].copy()
    margin["closes"] = (margin["topo_clean"] - margin["topo_base"]
                        >= CLOSE_FRACTION * (1.0 - margin["topo_base"]) - 1e-12)
    n_margin, closed = int(len(margin)), int(margin["closes"].sum())
    if n_margin == 0:
        va, frac = "no evaluable", float("nan")
    else:
        frac = closed / n_margin
        va = "apoyada" if frac >= 0.75 else ("parcial" if frac >= 0.50 else "no apoyada")
    h7a = {"cells": int(len(a)), "cells_with_margin": n_margin, "closed": closed,
           "fraction_closed": frac, "verdict": va}

    # H7b: el área no se distorsiona
    b = _cells(tab, HELP_SHAPES, AREA_LEVELS).copy()
    b["delta"] = (b["med_abs_area_clean"] - b["med_abs_area_base"]).abs()
    failing = int((b["delta"] >= AREA_TOL).sum())
    if len(b) == 0:
        vb = "no evaluable"
    else:
        vb = "apoyada" if failing == 0 else ("parcial" if failing == 1 else "no apoyada")
    h7b = {"n": int(len(b)), "failing": failing,
           "max_delta": float(b["delta"].max()) if len(b) else float("nan"), "verdict": vb}

    # H7c: el daño es acotado donde el rasgo real es pequeño
    c = _cells(tab, (HARM_SHAPE,), HARM_LEVELS).copy()
    c["drop"] = c["topo_base"] - c["topo_clean"]
    damaged = int((c["drop"] > DAMAGE_TOL + 1e-12).sum())
    if len(c) == 0:
        vc = "no evaluable"
    else:
        vc = "apoyada" if damaged == 0 else ("parcial" if damaged == 1 else "no apoyada")
    h7c = {"n": int(len(c)), "damaged": damaged,
           "max_drop": float(c["drop"].max()) if len(c) else float("nan"), "verdict": vc}

    return {"h7a": h7a, "h7b": h7b, "h7c": h7c,
            "cells_h7a": margin.round(4).to_dict(orient="records"),
            "cells_h7c": c.round(4).to_dict(orient="records")}
