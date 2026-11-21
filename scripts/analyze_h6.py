"""Análisis confirmatorio H6 según docs/PREREGISTRO_H6.md (no cambia criterios).

Usa los modelos congelados (``h6_frozen_models.json``) y, como ingenuo (A), los de
H1 (``h3_frozen_models.json``) aplicados a Q_hat. No reajusta nada.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from geovida import h6
from geovida.budget import GREEN, RED

RAW = Path("results/raw/h6_sweep.csv.gz")
FROZEN = Path("results/summary/h6_frozen_models.json")
NAIVE = Path("results/summary/h3_frozen_models.json")
OUT = Path("results/summary")
FIG = Path("docs/figures")
LIGHT = {"verde": "#009E73", "amarillo": "#F0E442", "rojo": "#D55E00"}


def reliability(p, y, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    rows = []
    for k in range(bins):
        s = idx == k
        if s.any():
            rows.append((p[s].mean(), y[s].mean(), int(s.sum())))
    return np.array(rows)


def main():
    frozen_all = json.loads(FROZEN.read_text())
    col = frozen_all["column"]
    frozen = frozen_all["models"]
    naive = {k: v["q_model"] for k, v in json.loads(NAIVE.read_text())["models"].items()}
    df = h6.add_features(pd.read_csv(RAW))

    res = h6.evaluate_h6(df, frozen, naive, col)
    res["feature"] = frozen_all["feature"]
    pd.DataFrame(res["strata"]).round(4).to_csv(OUT / "h6_strata.csv", index=False)
    wp = h6.wrong_profile_table(df, frozen, col)
    sh = h6.by_shape_table(df, frozen, col)
    lv = h6.lights_by_level_table(df, frozen, col)
    wp.round(4).to_csv(OUT / "h6_wrong_profile_exploratory.csv", index=False)
    sh.round(4).to_csv(OUT / "h6_false_green_by_shape_exploratory.csv", index=False)
    lv.round(4).to_csv(OUT / "h6_lights_by_level_exploratory.csv", index=False)
    (OUT / "h6_verdicts.json").write_text(json.dumps(res, indent=2, default=float))

    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    strata = [r["stratum"] for r in res["strata"]]

    # Figura 1: fiabilidad (calibración) del modelo congelado y del ingenuo
    fig, axs = plt.subplots(2, 3, figsize=(10, 6.2), sharex=True, sharey=True)
    for ax, key in zip(axs.ravel(), strata):
        seg, prof = key.split("|")
        g = df[(df.segmenter == seg) & (df.profile == prof)]
        y = g["v_ok"].to_numpy(float)
        for p, lab, c, mk in [(h6.predict_p(g[col], frozen[key]), "semáforo congelado", "#0072B2", "o"),
                              (h6.predict_p(g["q_hat_over_hgeo"], naive[key]), "ingenuo (modelo de H1)", "#D55E00", "s")]:
            r = reliability(p, y)
            ax.plot(r[:, 0], r[:, 1], marker=mk, ms=4, color=c, label=lab, lw=1.2)
        ax.plot([0, 1], [0, 1], color="0.6", ls=":")
        ax.axvline(GREEN, color="0.8", lw=.8)
        ax.set_title(key.replace("|", " · "))
    for ax in axs[1]:
        ax.set_xlabel("probabilidad predicha")
    for ax in axs[:, 0]:
        ax.set_ylabel("fracción observada con |error de V| ≤ 5 %")
    axs[0, 0].legend(fontsize=7, frameon=False, loc="upper left")
    fig.suptitle("H6: calibración del semáforo en formas y semillas nuevas (línea vertical: umbral verde 0.90)", y=1.0)
    fig.tight_layout(); fig.savefig(FIG / "h6_reliability.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    # Figura 2: reparto de luces por nivel t/h y acierto observado dentro de cada luz
    fig, axs = plt.subplots(2, 3, figsize=(10, 6.2), sharex=True, sharey=True)
    levels = sorted(lv["t_over_h"].unique())
    x = np.arange(len(levels))
    for ax, key in zip(axs.ravel(), strata):
        seg, prof = key.split("|")
        t = lv[(lv.segmenter == seg) & (lv.profile == prof)]
        bottom = np.zeros(len(levels))
        for light in ("rojo", "amarillo", "verde"):
            s = t[t.light == light].sort_values("t_over_h")["share"].to_numpy()
            ax.bar(x, s, bottom=bottom, color=LIGHT[light], label=light, width=.8, edgecolor="white", lw=.4)
            bottom += s
        gv = t[t.light == "verde"].sort_values("t_over_h")["p_ok_observed"].to_numpy()
        ax.plot(x, gv, color="k", marker="o", ms=3, lw=1, label="acierto observado en verde")
        ax.set_xticks(x); ax.set_xticklabels([f"{v:g}" for v in levels]); ax.set_title(key.replace("|", " · "))
    for ax in axs[1]:
        ax.set_xlabel("t / h (vóxeles a través del rasgo más fino)")
    for ax in axs[:, 0]:
        ax.set_ylabel("proporción de imágenes")
    handles, labels = axs[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=8, frameon=False, ncol=4, loc="lower center",
               bbox_to_anchor=(0.5, -0.04))   # fuera de los paneles: no tapa las barras
    fig.suptitle("H6: qué luz enciende el semáforo según la resolución (barras) y cuánto acierta en verde (línea)", y=1.0)
    fig.tight_layout(); fig.savefig(FIG / "h6_lights_by_resolution.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    # Figura 3: verde falso por forma (exploratorio)
    fig, ax = plt.subplots(figsize=(9, 3.6))
    shapes = sorted(sh["shape"].unique())
    for i, key in enumerate(strata):
        seg, prof = key.split("|")
        t = sh[(sh.segmenter == seg) & (sh.profile == prof)].set_index("shape").reindex(shapes)
        ax.scatter(np.arange(len(shapes)) + (i - 2.5) * 0.12, 100 * t["false_green"], s=16 + t["n_green"] / 40,
                   label=key.replace("|", " · "), alpha=.85)
    ax.axhline(10, color="0.4", ls="--", lw=1)
    ax.set_xticks(np.arange(len(shapes))); ax.set_xticklabels(shapes, rotation=30, ha="right")
    ax.set_ylabel("verde falso (%)"); ax.legend(fontsize=7, frameon=False, ncol=2)
    ax.set_title("H6 (exploratorio): tasa de verde falso por forma (tamaño = filas en verde; línea = 10 %)")
    fig.tight_layout(); fig.savefig(FIG / "h6_false_green_by_shape.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    short = {k: v for k, v in res.items() if k != "strata"}
    print(json.dumps(short, indent=2, default=float))
    print(pd.DataFrame(res["strata"])[["stratum", "n", "auc", "ece", "logloss", "logloss_naive", "n_green",
                                       "false_green", "n_green_naive", "false_green_naive"]].round(3).to_string(index=False))
    print(wp.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
