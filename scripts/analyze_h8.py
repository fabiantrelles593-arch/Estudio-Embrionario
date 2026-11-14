"""Análisis de H8 según docs/PREREGISTRO_H8.md (no cambia criterios)."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from geovida.growth import TRUE_RATE, evaluate_h8, rates_table, stage_sizes

RAW = Path("results/raw/h8_sweep.csv.gz")
OUT = Path("results/summary")
FIG = Path("docs/figures")
LIGHT = {"verde": "#009E73", "amarillo": "#F0E442", "rojo": "#D55E00"}


def main():
    df = pd.read_csv(RAW)
    rates = rates_table(df)
    rates.round(5).to_csv(OUT / "h8_rates.csv", index=False)
    res = evaluate_h8(rates)
    assert rates["err_oracle"].max() < 1e-9, "el oráculo debe dar la tasa exacta"
    (OUT / "h8_verdicts.json").write_text(json.dumps(res, indent=2, default=float))
    strata = pd.DataFrame(res["strata"])
    strata.round(4).to_csv(OUT / "h8_strata.csv", index=False)

    lights = (df.groupby(["segmenter", "profile", "stage", "light"]).size()
              .unstack(fill_value=0))
    lights = lights.div(lights.sum(axis=1), axis=0).reset_index()
    lights.round(4).to_csv(OUT / "h8_lights_by_stage_exploratory.csv", index=False)
    df["rel_err_v"] = df["volume"] / df["volume_true"] - 1.0
    bias = df.groupby(["segmenter", "profile", "stage"])["rel_err_v"].median().reset_index()

    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    keys = [r["stratum"] for r in res["strata"]]
    sizes = stage_sizes()

    # Figura 1: qué luz recibe cada etapa y sesgo mediano del volumen
    fig, axs = plt.subplots(2, 3, figsize=(10.5, 6.2), sharex=True)
    for ax, key in zip(axs.ravel(), keys):
        seg, prof = key.split("|")
        t = lights[(lights.segmenter == seg) & (lights.profile == prof)].sort_values("stage")
        bottom = np.zeros(len(t))
        for light in ("rojo", "amarillo", "verde"):
            vals = t[light].to_numpy() if light in t else np.zeros(len(t))
            ax.bar(t["stage"], vals, bottom=bottom, color=LIGHT[light], width=.8,
                   edgecolor="white", lw=.4, label=light)
            bottom += vals
        b = bias[(bias.segmenter == seg) & (bias.profile == prof)].sort_values("stage")
        ax2 = ax.twinx()
        ax2.plot(b["stage"], 100 * b["rel_err_v"], color="k", marker="o", ms=3, lw=1)
        ax2.axhline(0, color="0.5", lw=.6, ls=":")
        ax2.set_ylim(-100, 100)
        ax2.spines["top"].set_visible(False)
        if ax in axs[:, -1]:
            ax2.set_ylabel("sesgo mediano de V (%)  (línea)")
        ax.set_title(key.replace("|", " · "))
        ax.set_xticks(range(len(sizes)))
        ax.set_xticklabels([f"{v:.1f}" for v in sizes], fontsize=7)
    for ax in axs[1]:
        ax.set_xlabel("etapa (grosor en vóxeles)")
    for ax in axs[:, 0]:
        ax.set_ylabel("proporción de etapas  (barras)")
    for ax in axs.ravel():
        ax.set_ylim(0, 1)
    handles, labels = axs[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=8, frameon=False, ncol=3, loc="lower center",
               bbox_to_anchor=(0.5, -0.04))
    fig.suptitle("H8: luz del semáforo en cada etapa de una serie que crece con vóxel fijo "
                 "(sesgo recortado a ±100 %)", y=1.0)
    fig.tight_layout()
    fig.savefig(FIG / "h8_lights_by_stage.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Figura 2: error de la tasa por estimador (mediana y percentil 90)
    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    x = np.arange(len(keys))
    w = 0.26
    series = [("todas las etapas (pareado)", "median_err_all_paired", "#D55E00"),
              ("sin rojas (semáforo)", "median_err_no_red", "#0072B2"),
              ("regla ≥ 100 vóxeles", "median_err_vox100", "#999999")]
    for i, (lab, col, c) in enumerate(series):
        ax.bar(x + (i - 1) * w, 100 * strata[col], width=w, color=c, label=lab)
    ax.axhline(5, color="0.3", ls="--", lw=1)
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{k.replace('|', ' · ')}\nseries sin tasa: {100 * r['frac_undefined']:.0f} %"
                        for k, r in zip(keys, res["strata"])], fontsize=8)
    ax.set_ylabel("error mediano de la tasa (%)")
    ax.legend(fontsize=7, frameon=False)
    ax.set_title(f"H8: error de la tasa de crecimiento (verdad = {TRUE_RATE:.3f} por etapa); "
                 "línea = 5 %")
    fig.tight_layout()
    fig.savefig(FIG / "h8_rate_error.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    short = {k: v for k, v in res.items() if k != "strata"}
    print(json.dumps(short, indent=2, default=float))
    cols = ["stratum", "n_series", "n_defined", "frac_undefined", "median_err_all_paired",
            "median_err_no_red", "median_err_green", "median_err_vox100", "frac_undefined_vox100",
            "median_err_no_red_both", "median_err_vox100_both", "p90_err_no_red", "frac_no_red_wins"]
    print(strata[cols].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
