"""Figura de H16: la guardia de cadena frente al semáforo base, con cadenas vistas (A) y no vistas (B) (solo simulación)."""
import json
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SUMMARY, FIG = Path("results/summary"), Path("docs/figures")
BLUE, ORANGE, GREY = "#0072B2", "#D55E00", "#6b6b6b"      # Okabe-Ito: distinguibles con daltonismo
MIN_GREEN = 30


def whisker(ax, x, val, ci, color, marker, label=None, hollow=False):
    lo, hi = ci
    ax.errorbar(x, 100 * val, yerr=[[100 * (val - lo)], [100 * (hi - val)]], fmt=marker, color=color, capsize=3, ms=7, lw=1.6,
                mfc="white" if hollow else color, label=label)


def main():
    v = json.loads((SUMMARY / "h16_verdicts.json").read_text())["principal_recalibracion"]
    g = pd.read_csv(SUMMARY / "h16_gamma_strata_rc.csv")
    d = v["descriptive"]["baseline_false_green"]
    fig, ax = plt.subplots(1, 3, figsize=(14.5, 4.8), gridspec_kw={"width_ratios": [1, 1, 1.25]})

    a = ax[0]
    for i, (fam, key, name) in enumerate((("A", "h16a", "cadena vista (A)"), ("B", "h16b", "cadena no vista (B)"))):
        b0, g0 = d[f"{fam}|body"], v[key]
        whisker(a, i - 0.08, b0["false_green"], b0["ci"], ORANGE, "s", "semáforo base" if i == 0 else None)
        whisker(a, i + 0.08, g0["false_green"], g0["ci"], BLUE, "o", "con la guardia" if i == 0 else None)
        a.text(i - 0.08, 100 * b0["ci"][1] + 1.2, f"{b0['n_green']} verdes", ha="center", fontsize=8.5, color=ORANGE)
        a.text(i + 0.08, 100 * g0["ci"][1] + 1.2, f"{g0['n_green']} verdes", ha="center", fontsize=8.5, color=BLUE)
    a.axhline(10, color="black", lw=1, ls="--")
    a.text(1.45, 10.4, "límite 10 %", ha="right", fontsize=8.5)
    a.set_xticks([0, 1], ["cadena vista (A)", "cadena no vista (B)"])
    a.set_xlim(-0.5, 1.5)
    a.set_ylim(0, 20)
    a.set_ylabel("falsos verdes entre los verdes (%), IC 95 %")
    a.set_title("A · Datación: la guardia baja los falsos verdes", fontsize=10)
    a.legend(frameon=False, loc="upper right", fontsize=8.5)
    a.spines[["top", "right"]].set_visible(False)

    b = ax[1]
    for i, (fam, name) in enumerate((("A", "cadena vista (A)"), ("B", "cadena no vista (B)"))):
        r = v["h16d"][fam]
        whisker(b, i, r["ratio"], r["ci"], BLUE, "o")
        b.text(i, 100 * r["ci"][1] + 3, f"{100 * r['ratio']:.0f} %", ha="center", fontsize=9)
    b.axhline(50, color="black", lw=1, ls="--")
    b.text(1.45, 51.5, "umbral 50 %", ha="right", fontsize=8.5)
    b.set_xticks([0, 1], ["cadena vista (A)", "cadena no vista (B)"])
    b.set_xlim(-0.5, 1.5)
    b.set_ylim(0, 100)
    b.set_ylabel("verdes correctos que se conservan (%), IC 95 %")
    b.set_title("B · El precio: con cadenas nuevas se conserva menos", fontsize=10)
    b.spines[["top", "right"]].set_visible(False)

    c = ax[2]
    body = g[g["kind"] == "body"].reset_index(drop=True)
    labels = ["compresiva\n(γ < 0.8)", "intermedia\n(0.8–1.25)", "oscurecedora\n(γ > 1.25)"]
    for i, row in body.iterrows():
        c.plot(i - 0.08, 100 * row["base_false_green"], "s", color=ORANGE, ms=8, label="semáforo base" if i == 0 else None)
        hollow = row["guard_green"] < MIN_GREEN
        c.plot(i + 0.08, 100 * (row["guard_false_green"] if row["guard_green"] else 0.0), "o", color=BLUE, ms=8, mfc="white" if hollow else BLUE,
               label="con la guardia" if i == 0 else None)
        c.text(i + 0.14, 100 * (row["guard_false_green"] if row["guard_green"] else 0.0) + 1.0,
               f"{int(row['guard_green'])} verdes" + (" (no se interpreta)" if hollow else ""), ha="left", fontsize=8, color=BLUE)
        c.text(i - 0.14, 100 * row["base_false_green"] + 1.0, f"{int(row['base_green'])} verdes", ha="right", fontsize=8, color=ORANGE)
    c.axhline(10, color="black", lw=1, ls="--")
    c.set_xticks(range(3), labels)
    c.set_xlim(-0.95, 3.0)
    c.set_ylim(0, 20)
    c.set_ylabel("falsos verdes entre los verdes (%)")
    c.set_title("C · Cadena no vista, por curva de tono (exploratorio)", fontsize=10)
    c.legend(frameon=False, loc="upper right", fontsize=8.5)
    c.spines[["top", "right"]].set_visible(False)

    fig.suptitle("H16 (simulación): el certificado de datación, con y sin guardia de cadena (diseño principal: recalibración condicionada a la imagen)",
                 fontsize=11, y=1.02)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "h16_guard.png", dpi=150, bbox_inches="tight")
    print("figura:", FIG / "h16_guard.png")


if __name__ == "__main__":
    main()
