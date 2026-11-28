"""ANÁLISIS EXPLORATORIO POST HOC (no preregistrado) tras ver los resultados de H1.

Pregunta surgida de los datos: el volumen no colapsa en t/h (H1a falsada). ¿Lo
hace en Q = V/(S h), la longitud volumen/área en vóxeles? Hipótesis generada
aquí; necesita confirmarse con un barrido nuevo y preregistrado.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from geovida.analysis import add_predictors, add_vq_predictors, _fit_logit_ridge

COLS = {"P1": "t_solid_over_hxy", "P2": "t_solid_over_hgeo", "P3": "t_solid_over_hmax",
        "Q1": "q_over_hxy", "Q2": "q_over_hgeo", "Q3": "q_over_hmax"}


def aic(g, col, ep="v_ok"):
    y = g[ep].to_numpy(float)
    x = np.log(g[col].to_numpy(float)); x = (x - x.mean()) / x.std()
    _, p = _fit_logit_ridge(x, y); p = np.clip(p, 1e-12, 1 - 1e-12)
    return float(-2 * np.sum(y * np.log(p) + (1 - y) * np.log(1 - p)) + 4)


def fmt_log(fig):
    """Etiquetas legibles (0.5, 1, 2, 4...) en ejes logarítmicos."""
    from matplotlib import ticker
    for ax in fig.axes:
        if ax.get_xscale() == "log":
            ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:g}"))
            ax.xaxis.set_minor_formatter(ticker.NullFormatter())
            lo, hi = ax.get_xlim()
            ax.set_xticks([t for t in (0.5, 0.75, 1, 1.5, 2, 3, 4, 6, 8, 12, 20) if lo <= t <= hi])


def main():
    df = add_vq_predictors(add_predictors(pd.read_csv("results/raw/h1_sweep.csv.gz")))
    df["v_ok"] = df["err_volume"].abs() <= 0.05
    rows = []
    for (seg, prof), g in df.groupby(["segmenter", "profile"]):
        rows.append({"segmenter": seg, "profile": prof, **{k: aic(g, c) for k, c in COLS.items()}})
    tab = pd.DataFrame(rows)
    tab["best"] = tab[list(COLS)].idxmin(axis=1)
    tab["delta_aic_best_Q_vs_best_P"] = tab[["Q1", "Q2", "Q3"]].min(axis=1) - tab[["P1", "P2", "P3"]].min(axis=1)
    Path("results/summary").mkdir(exist_ok=True)
    tab.round(1).to_csv("results/summary/h1_exploratory_vq_aic.csv", index=False)
    print(tab.round(0).to_string(index=False))

    # Valor de Q (en h_geo) donde p(V_ok) >= 0.95 sostenido, por forma (global, ideal, a=1)
    base = df[(df.segmenter == "global") & (df.profile == "ideal")]
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    okabe = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000"]
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
    for ax, (col, lab) in zip(axs, [("t_solid_over_hgeo", "t_solid / h_geo  (grosor)"),
                                    ("q_over_hgeo", "Q / h_geo = V / (S h_geo)  (volumen/área)")]):
        for s, c in zip(base["shape"].unique(), okabe):
            g = base[base["shape"] == s].groupby(["anisotropy", "t_over_h"]).agg(
                p=("v_ok", "mean"), x=(col, "first")).reset_index()
            ax.scatter(g.x, g.p, s=12, color=c, label=s, alpha=.85)
        ax.axhline(0.95, color="0.6", ls=":"); ax.set_xscale("log"); ax.set_xlabel(lab)
    axs[0].set_ylabel("Proporción con |error de V| ≤ 5 %"); axs[1].legend(fontsize=7, frameon=False)
    fig.suptitle("EXPLORATORIO (post hoc): el volumen colapsa en V/(S·h), no en t/h", y=1.02)
    fmt_log(fig); fig.tight_layout(); fig.savefig("docs/figures/h1_exploratory_volume_collapse.png", dpi=150, bbox_inches="tight")
    json.dump({"note": "post hoc; no confirmatorio"}, open("results/summary/h1_exploratory_note.json", "w"))


if __name__ == "__main__":
    main()
