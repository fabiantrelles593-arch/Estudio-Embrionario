"""Auditoría EXPLORATORIA de v0.2 (no preregistrada; se declara así en RESULTADOS_V02.md).

Responde a dos dudas que surgieron después de ver que H3/H4 salieron mejor de lo
predicho:

1. Márgenes de H3a: ¿la ventaja de Q sobre el grosor es mayor que el ruido, y
   cuánto aporta cada modelo frente a no saber nada (tasa base)?
2. Limpieza mínima (otsu_clean): ¿borra también estructuras reales pequeñas?
   Se prueba en las 7 formas de H1 (cáscaras y toros tienen cavidades y túneles
   reales) con una semilla nueva (20261113), perfil realista, vóxel isótropo.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from geovida.analysis import add_predictors, add_vq_predictors, predict_frozen
from geovida.experiment import Condition, run_sweep
from geovida.phantoms import PHANTOM_NAMES

RAW = Path("results/raw/h3_sweep.csv.gz")
FROZEN = Path("results/summary/h3_frozen_models.json")
OUT = Path("results/summary")
EXPLORATORY_SEED = 20261113
REPS = 60
LEVELS = (2.0, 3.0, 4.0, 6.0, 8.0, 12.0)


def _ll(p, y):
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def margins() -> pd.DataFrame:
    df = add_vq_predictors(add_predictors(pd.read_csv(RAW)))
    frozen = json.loads(FROZEN.read_text())["models"]
    rows = []
    for (seg, prof), g in df.groupby(["segmenter", "profile"]):
        key = f"{seg}|{prof}"
        if key not in frozen:      # otsu_clean no tiene modelo congelado
            continue
        y = (g["err_volume"].abs() <= 0.05).to_numpy(float)
        lq = _ll(predict_frozen(frozen[key]["q_model"], g["q_over_hgeo"]), y)
        lt = _ll(predict_frozen(frozen[key]["t_model"], g["t_solid_over_hgeo"]), y)
        p0 = y.mean()
        l0 = _ll(np.full_like(y, p0), y)
        d = lt - lq
        # el error típico se calcula por condición (forma, t/h, anisotropía, perfil):
        # las 200 réplicas de una celda no son independientes en la dirección que importa
        cell = g.assign(d=d).groupby(["shape", "t_over_h", "anisotropy"])["d"].mean()
        rows.append({
            "stratum": key, "n": len(y), "p_ok": p0,
            "logloss_null": l0.mean(), "logloss_q": lq.mean(), "logloss_t": lt.mean(),
            "gain_q_vs_t": d.mean(),
            "gain_se_cells": cell.std(ddof=1) / np.sqrt(len(cell)),
            "cells": len(cell),
            "share_cells_q_better": float((cell > 0).mean()),
        })
    return pd.DataFrame(rows)


def cleaning_on_h1_shapes() -> pd.DataFrame:
    conds = [Condition(s, t, 1.0, "realistic", r)
             for s in PHANTOM_NAMES for t in LEVELS for r in range(REPS)]
    df = run_sweep(conds, n_jobs=2, base_seed=EXPLORATORY_SEED,
                   segmenters=("otsu", "otsu_clean"))
    return (df.groupby(["shape", "segmenter", "t_over_h"])
              .agg(topology_ok=("topology_ok", "mean"),
                   median_abs_err_volume=("err_volume", lambda s: s.abs().median()))
              .reset_index())


def main():
    m = margins()
    m.round(4).to_csv(OUT / "h3_margins_exploratory.csv", index=False)
    print(m.round(4).to_string())
    c = cleaning_on_h1_shapes()
    c.round(4).to_csv(OUT / "otsu_clean_h1_shapes_exploratory.csv", index=False)
    piv = c.pivot_table(index=["shape", "t_over_h"], columns="segmenter", values="topology_ok")
    piv["delta_points"] = 100 * (piv["otsu_clean"] - piv["otsu"])
    print(piv.round(3).to_string())


if __name__ == "__main__":
    main()
