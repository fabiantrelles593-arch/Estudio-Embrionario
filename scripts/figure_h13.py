"""Figura de los resultados de H13 (solo lee results/summary/h13_*.csv; no calcula nada nuevo).

Panel A: calibración. Probabilidad que dice el certificado frente a la frecuencia de acierto observada.
Panel B: falso verde por ancho de la función de dispersión (estratificación POSTERIOR al preregistro).

Uso:  python scripts/figure_h13.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

S = Path("results/summary")
OUT = Path("docs/figures/h13_certificate.png")
BLUE, ORANGE = "#2a78d6", "#eb6834"      # paleta validada en la figura de H12
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#dcdbd6", "#fcfcfb"
COLORS = {"body": BLUE, "slot": ORANGE}
MIN_BIN = 20            # cubos con menos casos no se dibujan
NAMES = {"body": "Cuerpo (CRL → edad)", "slot": "Ranura (NT → lado del umbral)"}


def main():
    rel = pd.read_csv(S / "h13_reliability.csv")
    st = pd.read_csv(S / "h13_strata.csv")
    st = st[st["segmenter"] == "smoothed_otsu"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.5, 4.8), gridspec_kw={"width_ratios": [1, 1.25]}, facecolor=SURFACE)
    for ax in (a, b):
        ax.set_facecolor(SURFACE)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        for sp in ("left", "bottom"):
            ax.spines[sp].set_color(GRID)
        ax.tick_params(colors=MUTED, labelsize=9)

    # --- A: fiabilidad --------------------------------------------------------------------
    a.plot([0, 1], [0, 1], color=GRID, lw=1.5, zorder=1)
    a.text(0.62, 0.52, "calibración perfecta", color=MUTED, fontsize=8.5, rotation=38, ha="center")
    for k, g in rel.groupby("kind"):
        top_n = int(g.iloc[-1]["n"])                       # cubo de p > 0.9
        g = g[g["n"] >= MIN_BIN]                           # un cubo con pocos casos no dice nada
        a.plot(g["p_mean"], g["observed"], "-o", color=COLORS[k], lw=2, ms=6, zorder=3,
               label=f"{NAMES[k]} · cubo > 0.9: {top_n} casos")
    a.set_xlim(0, 1.02)
    a.set_ylim(0, 1.05)
    a.set_xlabel("probabilidad que dice el certificado", color=INK, fontsize=10)
    a.set_ylabel("frecuencia de acierto observada", color=INK, fontsize=10)
    a.set_title("A · Fiable en lo alto; pesimista en el medio (cuerpo)", loc="left", fontsize=10, color=INK)
    a.legend(frameon=False, fontsize=8.5, loc="lower right", bbox_to_anchor=(1.0, 0.0))
    a.grid(color=GRID, lw=0.6, zorder=0)

    # --- B: falso verde por estrato ---------------------------------------------------------
    order = ["f<=2", "2<f<=3.5", "f>3.5"]
    labels = ["PSF ≤ 2 px", "2 – 3.5 px", "> 3.5 px"]
    w = 0.34
    greens = {}
    for j, k in enumerate(("body", "slot")):
        g = st[st["kind"] == k].set_index("fwhm_bin").loc[order]
        xs = [i + (j - 0.5) * (w + 0.02) for i in range(3)]
        vals = 100 * g["false_green"]
        err = [100 * (g["false_green"] - g["fg_lo"]), 100 * (g["fg_hi"] - g["false_green"])]
        b.bar(xs, vals, w, color=COLORS[k], label=NAMES[k], zorder=3)
        b.errorbar(xs, vals, yerr=err, fmt="none", ecolor=INK, elinewidth=1, capsize=3, zorder=4)
        for x, v, hi in zip(xs, vals, 100 * g["fg_hi"]):
            b.text(x, hi + 0.7, f"{v:.1f} %", ha="center", va="bottom", fontsize=9, color=INK)
        greens[k] = [int(n) for n in g["n_green"]]
    b.axhline(10, color=MUTED, ls="--", lw=1.2, zorder=2)
    b.text(-0.48, 10.7, "límite preregistrado 10 %", ha="left", fontsize=8.5, color=MUTED)
    b.set_xticks(range(3))
    b.set_xticklabels([f"{lab}\nverdes: cuerpo {greens['body'][i]} · ranura {greens['slot'][i]}"
                       for i, lab in enumerate(labels)], fontsize=8.5)
    b.set_ylim(0, 36)
    b.set_ylabel("falso verde (intervalo 95 %)", color=INK, fontsize=10)
    b.set_title("B · El agregado pasa; la ranura con PSF > 3.5 px no es fiable", loc="left", fontsize=10, color=INK)
    b.legend(frameon=False, fontsize=9, loc="upper left", bbox_to_anchor=(0.0, 0.93))
    b.grid(axis="y", color=GRID, lw=0.6, zorder=0)
    fig.text(0.01, 0.01, "Todo es simulación (segmentador smoothed_otsu, dentro de la caja calibrada). "
             "El panel B es una estratificación posterior al preregistro: exploratoria. Panel A: cubos con < 20 casos omitidos.", fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, facecolor=SURFACE)
    print("figura en", OUT)


if __name__ == "__main__":
    main()
