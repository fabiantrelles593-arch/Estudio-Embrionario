"""Figura de la trayectoria de referencia (no es una predicción). Lee `trayectoria.json` de `geovida trajectory`.

    python scripts/figure_trajectory.py trayectoria.json docs/figures/trajectory_example.png
"""
import json
import sys

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from geovida import trajectory as tj

BLUE, ORANGE, GREY = "#0072B2", "#D55E00", "#6b6b6b"      # Okabe-Ito: distinguibles con daltonismo
Z97 = 1.88                                                # el artículo dibuja los percentiles 3 y 97 como media ± 1.88 SD


def main(src, dst):
    p0 = json.load(open(src))
    # misma medida y mismas semillas, pero un horizonte por día para que la banda no tenga esquinas
    p = tj.projection(p0["crl_mm_measured"], crl_rel_sd=p0["crl_rel_sd"], crl_rel_bias=p0["crl_rel_bias"],
                      horizons_days=tuple(range(1, 46)), n_draws=p0["n_draws"], seed=p0["seed"], coverage=p0["coverage"])
    ga = np.linspace(58, 105, 100)
    mean = np.array([tj.crl_mean_mm(g) for g in ga])
    sd = np.array([tj.crl_sd_mm(g) for g in ga])
    ga0 = p["ga_now"]
    rows = [r for r in p["rows"] if r["in_source_range"]]
    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.8), gridspec_kw={"width_ratios": [2.1, 1]})
    a = ax[0]
    a.fill_between(ga, mean - Z97 * sd, mean + Z97 * sd, color=BLUE, alpha=0.13, lw=0, label="referencia poblacional, percentiles 3–97")
    a.plot(ga, mean, color=BLUE, lw=1.8, label="media poblacional")
    xs = [ga0["median_days"]] + [r["ga_days"] for r in rows]
    lo = [p["crl_mm_measured"]] + [r["envelope"]["lo"] for r in rows]
    hi = [p["crl_mm_measured"]] + [r["envelope"]["hi"] for r in rows]
    a.fill_between(xs, lo, hi, color=ORANGE, alpha=0.28, lw=0, label=f"envolvente de los dos escenarios ({int(round(100*p['coverage']))} %)")
    a.errorbar([ga0["median_days"]], [p["crl_mm_measured"]], xerr=[[ga0["median_days"] - ga0["lo_days"]], [ga0["hi_days"] - ga0["median_days"]]],
               yerr=p["crl_rel_sd"] * p["crl_mm_measured"] * 1.645, fmt="o", color="black", ms=6, capsize=3, label="medida y su incertidumbre")
    a.set_xlim(58, 105)
    a.set_xticks([63, 70, 77, 84, 91, 98, 105], ["9+0", "10+0", "11+0", "12+0", "13+0", "14+0", "15+0"])
    a.set_xlabel("edad gestacional (semanas+días)")
    a.set_ylabel("longitud cráneo-rabadilla (mm)")
    a.set_title("A · Franja de referencia a partir de una medida (no es una predicción)", fontsize=10)
    a.legend(frameon=False, fontsize=8.5, loc="upper left")
    a.spines[["top", "right"]].set_visible(False)

    b = ax[1]
    weeks = [(10, 70), (12, 84), (14, 98)]
    labels = [f"{w}+0" for w, _ in weeks]
    vals = [tj.crl_mean_mm(g) for _, g in weeks]
    y = np.arange(len(weeks))[::-1]
    b.barh(y, vals, color=BLUE, height=0.5)
    for yy, v in zip(y, vals):
        b.text(2, yy, f"{v:.0f} mm", va="center", fontsize=9.5, color="white", fontweight="bold")
    b.axvline(p["crl_mm_measured"], color="black", lw=1.2, ls="--")
    b.text(p["crl_mm_measured"] + 1.5, y[-1] - 0.62, f"medida: {p['crl_mm_measured']:.1f} mm", fontsize=8.5)
    b.set_ylim(y[-1] - 0.85, y[0] + 0.55)
    b.set_yticks(y, labels)
    b.set_xlim(0, 105)
    b.set_xlabel("longitud (mm): solo el tamaño, no el aspecto")
    b.set_title("B · Tamaño medio de referencia", fontsize=10)
    b.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Trayectoria de referencia (INTERGROWTH-21st). Solo investigación y educación", fontsize=11, y=1.0)
    fig.tight_layout()
    fig.savefig(dst, dpi=150, bbox_inches="tight")


if __name__ == "__main__":
    main(*sys.argv[1:3])
