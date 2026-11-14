"""Análisis de la prueba de estrés 2D según docs/PREREGISTRO_2D.md."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import ticker

from geovida.h5 import evaluate_h5

RAW = Path("results/raw/h5_sweep.csv.gz")
OUT = Path("results/summary")
FIG = Path("docs/figures")
COL = {"ideal": "#009E73", "us_compound": "#0072B2", "us_raw": "#D55E00"}


def fmt_log(ax, ticks=(2, 3, 4, 6, 8, 12, 20)):
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.xaxis.set_minor_formatter(ticker.NullFormatter())
    ax.set_xticks(list(ticks))


def main():
    df = pd.read_csv(RAW)
    res = evaluate_h5(df)
    (OUT / "h5_verdicts.json").write_text(json.dumps(res, indent=2, default=float))
    summ = (df.groupby(["shape", "profile", "segmenter", "t_over_h"])
              .agg(median_err_area=("err_area", "median"),
                   median_err_perim=("err_perim_crofton", "median"),
                   median_err_hc=("err_hc", "median"),
                   topology_ok=("topology_ok", "mean"), dice=("dice", "mean")).reset_index())
    summ.round(4).to_csv(OUT / "h5_summary.csv", index=False)

    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    # Fig 1: error de circunferencia (elipse) por perfil, smoothed_otsu
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.3), sharey=True)
    for ax, shape in zip(axs, ("disk", "ellipse")):
        for prof, c in COL.items():
            m = summ[(summ["shape"] == shape) & (summ["profile"] == prof) & (summ["segmenter"] == "smoothed_otsu")]
            ax.plot(m["t_over_h"], 100 * m["median_err_hc"], marker="o", ms=3.5, color=c, label=prof)
        ax.axhspan(-3.3, 3.3, color="0.9", zorder=0); ax.axhline(0, color="0.5", lw=.8)
        ax.set_ylim(-15, 60)
        ax.annotate("fuera de escala: hasta +380 % a t/h = 2", xy=(0.97, 0.95), xycoords="axes fraction",
                    ha="right", va="top", fontsize=7, color="0.35")
        ax.set_title(shape); ax.set_xlabel("t / h (píxeles de grosor)"); fmt_log(ax)
    axs[0].set_ylabel("Error mediano de la circunferencia (%)"); axs[0].legend(fontsize=7, frameon=False)
    fig.suptitle("2D: circunferencia por elipse con suavizado + Otsu (banda gris = ±3.3 %)", y=1.03)
    fig.tight_layout(); fig.savefig(FIG / "h5_hc_error_by_profile.png", dpi=150, bbox_inches="tight")

    # Fig 2: topología del anillo por segmentador y perfil
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.3), sharey=True)
    for ax, prof in zip(axs, ("us_compound", "us_raw")):
        for seg, c in zip(("global", "otsu", "smoothed_otsu", "smoothed_otsu_s2"),
                          ("#999999", "#D55E00", "#0072B2", "#009E73")):
            m = summ[(summ["shape"] == "annulus") & (summ["profile"] == prof) & (summ["segmenter"] == seg)]
            ax.plot(m["t_over_h"], m["topology_ok"], marker="o", ms=3.5, color=c, label=seg)
        ax.axhline(0.95, color="0.7", ls=":"); ax.set_title(prof); ax.set_xlabel("t / h"); fmt_log(ax)
    axs[0].set_ylabel("Proporción con topología correcta (anillo)"); axs[1].legend(fontsize=7, frameon=False)
    fig.suptitle("2D: el moteado y la topología del anillo", y=1.03)
    fig.tight_layout(); fig.savefig(FIG / "h5_annulus_topology.png", dpi=150, bbox_inches="tight")
    print(json.dumps(res, indent=2, default=float))


if __name__ == "__main__":
    main()
