"""Análisis de H7 según docs/PREREGISTRO_H7.md (no cambia criterios)."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import ticker

from geovida.h7 import PRIMARY, evaluate_h7, paired_table

RAW = Path("results/raw/h7_sweep.csv.gz")
OUT = Path("results/summary")
FIG = Path("docs/figures")
LEVELS = (2, 3, 4, 6, 8, 12, 20)


def fmt_log(ax):
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.xaxis.set_minor_formatter(ticker.NullFormatter())
    ax.set_xticks(list(LEVELS))


def main():
    df = pd.read_csv(RAW)
    res = evaluate_h7(df)
    tab = paired_table(df)
    tab.round(4).to_csv(OUT / "h7_paired.csv", index=False)

    # Predicción 4 (preregistrada): ring_tight, imagen ideal, t/h = 2, global_clean < 20 %
    cell = tab[(tab["shape"] == "ring_tight") & (tab["profile"] == "ideal")
               & (tab["t_over_h"] == 2.0) & (tab["segmenter"] == "global")]
    res["prediction_ring_tight_ideal_t2_global"] = (
        {"topo_base": float(cell["topo_base"].iloc[0]), "topo_clean": float(cell["topo_clean"].iloc[0]),
         "below_20pct": bool(cell["topo_clean"].iloc[0] < 0.20)} if len(cell) else None)

    # Qué se borra (descriptivo)
    erased = (df[df["cleaned"]].groupby(["shape", "profile", "base", "t_over_h"])
              [["removed_components", "filled_holes", "clean_threshold_px"]].mean().reset_index())
    erased.round(3).to_csv(OUT / "h7_erased_exploratory.csv", index=False)
    (OUT / "h7_verdicts.json").write_text(json.dumps(res, indent=2, default=float))

    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    shapes = ("disk", "ellipse", "annulus", "ring_tight")
    fig, axs = plt.subplots(2, 4, figsize=(12.5, 5.6), sharex=True, sharey=True)
    for i, seg in enumerate(PRIMARY):
        for j, shape in enumerate(shapes):
            ax = axs[i, j]
            t = tab[(tab["segmenter"] == seg) & (tab["shape"] == shape)
                    & (tab["profile"] == "us_compound")].sort_values("t_over_h")
            ax.plot(t["t_over_h"], 100 * t["topo_base"], marker="o", ms=4, color="#D55E00",
                    label="sin limpieza")
            ax.plot(t["t_over_h"], 100 * t["topo_clean"], marker="s", ms=4, color="#0072B2",
                    label="con limpieza")
            ax.axhline(90, color="0.8", lw=.8)
            fmt_log(ax)
            ax.set_title(f"{shape} · {seg}", fontsize=8)
            if i == 1:
                ax.set_xlabel("t / h (píxeles a través del rasgo)")
            if j == 0:
                ax.set_ylabel("topología correcta (%)")
    axs[0, 0].legend(fontsize=7, frameon=False, loc="lower right")
    fig.suptitle("H7: limpieza 2D con moteado «compuesto». Ayuda en disco, elipse y anillo ancho; "
                 "en el anillo de hueco estrecho (derecha) puede dañar", y=1.0, fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "h7_cleaning_help_and_harm.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    short = {k: v for k, v in res.items() if not k.startswith("cells_")}
    print(json.dumps(short, indent=2, default=float))
    view = tab[(tab["profile"] == "us_compound") & tab["segmenter"].isin(PRIMARY)]
    print(view[["shape", "t_over_h", "segmenter", "topo_base", "topo_clean", "fixed", "broken",
                "med_abs_area_base", "med_abs_area_clean"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
