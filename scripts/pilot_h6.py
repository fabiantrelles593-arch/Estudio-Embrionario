"""Piloto de H6 (semilla 20261115, NO usada en el barrido de H6).

Sirve para (1) comprobar que Q_hat = V_medido / (S_medido h_geo) se comporta como
se espera y (2) fijar las expectativas numericas de las pruebas con datos, no con
intuicion. No decide ningun criterio de H6.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from geovida.analysis import add_predictors, add_vq_predictors, predict_frozen
from geovida.experiment import H6_SHAPES, Condition, run_sweep

PILOT_SEED = 20261115
FROZEN = Path("results/summary/h3_frozen_models.json")


def main():
    conds = [Condition(s, t, a, p, r) for s in H6_SHAPES for t in (1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0)
             for a in (1.0, 3.0) for p in ("ideal", "realistic") for r in range(4)]
    df = run_sweep(conds, n_jobs=2, base_seed=PILOT_SEED,
                   segmenters=("global", "otsu", "smoothed_otsu"))
    df = add_vq_predictors(add_predictors(df))
    h_xy = 1.0 / df["t_over_h"]
    h_geo = h_xy * df["anisotropy"] ** (1 / 3)
    df["q_hat_over_hgeo"] = df["volume"] / df["area_sdf"] / h_geo
    df["ratio"] = df["q_hat_over_hgeo"] / df["q_over_hgeo"]
    frozen = json.loads(FROZEN.read_text())["models"]
    out = []
    for (seg, prof), g in df.groupby(["segmenter", "profile"]):
        m = frozen[f"{seg}|{prof}"]["q_model"]
        g = g.assign(p_true=predict_frozen(m, g["q_over_hgeo"]), p_hat=predict_frozen(m, g["q_hat_over_hgeo"]),
                     v_ok=(g["err_volume"].abs() <= 0.05).astype(float))
        out.append(g)
    d = pd.concat(out)
    pd.set_option("display.width", 200)
    print(d.groupby(["segmenter", "t_over_h"])["ratio"].median().unstack().round(2))
    d["green"] = d["p_hat"] >= 0.90
    print(d[d.green].groupby("segmenter")["v_ok"].agg(["size", "mean"]).round(3))
    print(d.groupby("t_over_h")[["p_true", "p_hat", "v_ok"]].mean().round(2))
    Path("results/raw").mkdir(parents=True, exist_ok=True)
    d.to_csv("results/raw/pilot_h6.csv.gz", index=False)


if __name__ == "__main__":
    main()
