"""Figura de los resultados de H12 (solo lee results/summary/*.csv; no calcula nada nuevo).

Panel A: de las medidas correctas (|error de volumen| ≤ 5 %), qué fracción recibe luz verde, con el
certificado de v0.4 + guardia y con el recalibrado para ecografía simulada.
Panel B: verde falso (intervalo 95 %, Wilson) en `smoothed_otsu`, el único segmentador con envolvente.

Uso:  python scripts/figure_h12.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

S = Path("results/summary")
OUT = Path("docs/figures/h12_ultrasound_certificate.png")
BLUE, ORANGE = "#2a78d6", "#eb6834"      # paleta validada (ΔE CVD 24.7)
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#dcdbd6", "#fcfcfb"


def main():
    test = pd.read_csv(S / "h12_strata_test.csv").set_index("stratum")
    unseen = pd.read_csv(S / "h12_strata_unseen.csv").set_index("stratum")
    shift = pd.read_csv(S / "h12_strata_shift.csv").set_index("stratum")
    ben = pd.read_csv(S / "h12_benefit.csv").set_index("stratum")
    seg = "smoothed_otsu"

    fig, (a, b) = plt.subplots(1, 2, figsize=(11.5, 4.6), gridspec_kw={"width_ratios": [1, 1.55]},
                               facecolor=SURFACE)
    for ax in (a, b):
        ax.set_facecolor(SURFACE)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        for sp in ("left", "bottom"):
            ax.spines[sp].set_color(GRID)
        ax.tick_params(colors=MUTED, labelsize=9)

    # --- Panel A: cobertura ---------------------------------------------------------------
    profiles = ("us_compound", "us_raw")
    xs = range(len(profiles))
    w = 0.34
    v04 = [100 * ben.loc[f"{seg}|{p}", "coverage_v04"] for p in profiles]
    us = [100 * ben.loc[f"{seg}|{p}", "coverage_us"] for p in profiles]
    for i, (c04, cus) in enumerate(zip(v04, us)):
        a.bar(i - w / 2 - 0.01, c04, w, color=ORANGE, label="v0.4 + guardia" if i == 0 else None)
        a.bar(i + w / 2 + 0.01, cus, w, color=BLUE, label="recalibrado (H12)" if i == 0 else None)
        a.text(i - w / 2 - 0.01, c04 + 1.5, f"{c04:.1f} %", ha="center", fontsize=9, color=INK)
        a.text(i + w / 2 + 0.01, cus + 1.5, f"{cus:.1f} %", ha="center", fontsize=9, color=INK)
    a.set_xticks(list(xs), [p.replace("us_", "") for p in profiles])
    a.set_ylim(0, 100)
    a.set_ylabel("medidas correctas que reciben verde (%)", color=MUTED, fontsize=9)
    a.set_title("A · Cobertura (smoothed_otsu)", loc="left", fontsize=11, color=INK)
    a.yaxis.grid(True, color=GRID, linewidth=0.6)
    a.set_axisbelow(True)
    a.legend(frameon=False, fontsize=9, loc="upper left")

    # --- Panel B: verde falso -------------------------------------------------------------
    cu, ra = f"{seg}|us_compound", f"{seg}|us_raw"
    rows = [
        ("Volumen · prueba · compound", test.loc[cu], "volume", True, BLUE),
        ("Volumen · prueba · raw", test.loc[ra], "volume", True, BLUE),
        ("Topología · prueba · compound", test.loc[cu], "topology", True, BLUE),
        ("Volumen · formas nuevas · compound", unseen.loc[cu], "volume", True, BLUE),
        ("Volumen · formas nuevas · raw", unseen.loc[ra], "volume", True, BLUE),
        ("Topología · formas nuevas · compound*", unseen.loc[cu], "topology", False, BLUE),
    ]
    ys = []
    for i, (label, r, ext, ok, color) in enumerate(rows):
        y = len(rows) + 2 - i
        v, lo, hi = (100 * r[f"false_green_{ext}"], 100 * r[f"fg_lo_{ext}"], 100 * r[f"fg_hi_{ext}"])
        b.plot([lo, hi], [y, y], color=color, linewidth=2, solid_capstyle="round")
        b.plot([v], [y], "o", color=color, markersize=7, markerfacecolor=color if ok else SURFACE,
               markeredgewidth=2)
        b.text(max(hi, v) + 0.8, y, f"{v:.1f} %", va="center", fontsize=9, color=INK, zorder=5,
               bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.2))
        ys.append((y, label))
    for j, (name, stratum) in enumerate((("Volumen · desplazado, SIN guardia · atten", "smoothed_otsu|us_atten"),
                                         ("Volumen · desplazado, SIN guardia · coarse", "smoothed_otsu|us_coarse"))):
        y = 2 - j
        v = 100 * shift.loc[stratum, "false_green_volume"]
        b.plot([v], [y], "s", color=ORANGE, markersize=7)
        b.text(v + 0.8, y, f"{v:.1f} %", va="center", fontsize=9, color=INK, zorder=5,
               bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.2))
        ys.append((y, name))
    b.axvline(10, color=MUTED, linestyle=(0, (4, 3)), linewidth=1)
    b.text(10.3, len(rows) + 2.75, "límite 10 %", fontsize=8.5, color=MUTED)
    b.set_yticks([y for y, _ in ys], [t for _, t in ys], fontsize=9, color=INK)
    b.set_xlim(0, 32)
    b.set_ylim(0.3, len(rows) + 3.1)
    b.set_xlabel("luces verdes que eran falsas (%)", color=MUTED, fontsize=9)
    b.set_title("B · Verde falso", loc="left", fontsize=11, color=INK)
    b.xaxis.grid(True, color=GRID, linewidth=0.6)
    b.set_axisbelow(True)
    fig.text(0.012, 0.012,
             "Círculo vacío (*): menos de 100 verdes, no evaluable según el preregistro. Cuadrado naranja: sin guardia, sin intervalo calculado.\n"
             "Solo simulación. global y otsu no producen verdes (siempre rojo). Barras: intervalo 95 % del resultado confirmatorio.",
             fontsize=8.2, color=MUTED, va="bottom", ha="left")

    fig.suptitle("H12 · certificado recalibrado para ecografía simulada", x=0.012, ha="left",
                 fontsize=12.5, color=INK, fontweight="bold")
    fig.tight_layout(rect=(0, 0.075, 1, 0.95))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=170, facecolor=SURFACE)
    print(f"figura guardada en {OUT}")


if __name__ == "__main__":
    main()
