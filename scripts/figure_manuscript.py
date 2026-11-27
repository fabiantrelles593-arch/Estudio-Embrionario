"""Figuras del borrador del manuscrito, solo a partir de resultados ya publicados (sin análisis nuevos).

    python scripts/figure_manuscript.py

Lee ``results/h20/test_cases.csv`` y ``results/h25/test_cases.csv`` (fuera de git; los escriben las órdenes ``test``
de H20 y H25) y escribe en ``docs/figures``:

* ``manuscript_fig1_lights.png``: error de cada caso de prueba según su luz. Cuerpo (H20, |error de volumen|) y
  ventrículo (H25, e_b en vóxeles de borde), con la tolerancia de cada estudio.
* ``manuscript_fig2_signals.png``: las dos señales de H20 en la prueba de cuerpo, con los umbrales de la regla.

Comprueba antes que los recuentos coinciden con los publicados (21/22/1 luces y 3 fallos en H20; 19/17/4 y 2 fallos
en H25) y se niega a dibujar si no.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

OUT = Path("docs/figures")
ORDER = ["verde", "amarillo", "rojo"]
LABEL = {"verde": "green", "amarillo": "yellow", "rojo": "red"}
COLOR = {"verde": "#0ca30c", "amarillo": "#fab219", "rojo": "#d03b3b"}   # paleta de estado de la guía de gráficos
INK, MUTED, GRID = "#1f1f1e", "#6b6b68", "#e6e6e3"
EXPECTED = {"h20": ({"verde": 21, "amarillo": 22, "rojo": 1}, 3), "h25": ({"verde": 19, "amarillo": 17, "rojo": 4}, 2)}


def _check(df: pd.DataFrame, bad: np.ndarray, key: str):
    lights, fails = EXPECTED[key]
    got = df["light"].value_counts().to_dict()
    if got != lights or int(bad.sum()) != fails:
        raise SystemExit(f"{key}: los recuentos ({got}, {int(bad.sum())} fallos) no son los publicados")


def _style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelcolor=INK, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _strip(ax, df, value, bad, tol, ylabel, title):
    rng = np.random.default_rng(0)
    for i, light in enumerate(ORDER):
        m = (df["light"] == light).to_numpy()
        x = i + rng.uniform(-0.18, 0.18, m.sum())
        y = value[m]
        b = bad[m]
        ax.scatter(x[~b], y[~b], s=36, color=COLOR[light], edgecolor=INK, linewidth=0.6, zorder=3)
        ax.scatter(x[b], y[b], s=70, marker="X", color=COLOR[light], edgecolor=INK, linewidth=0.9, zorder=4)
    ax.axhline(tol, color=INK, linewidth=1, linestyle=(0, (4, 3)), zorder=2)
    ax.text(2.45, tol, " tolerance", va="bottom", ha="right", fontsize=8, color=MUTED)
    ax.set_xticks(range(3))
    ax.set_xticklabels([f"{LABEL[k]}\n(n = {(df['light'] == k).sum()})" for k in ORDER])
    ax.set_xlim(-0.6, 2.6)
    ax.set_ylabel(ylabel, color=INK, fontsize=9)
    ax.set_title(title, color=INK, fontsize=10, loc="left")
    _style(ax)


def main():
    body = pd.read_csv("results/h20/test_cases.csv")
    vent = pd.read_csv("results/h25/test_cases.csv")
    b_err = body["rel_error_volume"].abs().to_numpy() * 100
    b_bad = b_err > 10
    v_eb = vent["e_b"].to_numpy(float)
    v_bad = ~(v_eb <= 0.5)
    _check(body, b_bad, "h20")
    _check(vent, v_bad, "h25")
    OUT.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.8), constrained_layout=True)
    _strip(axes[0], body, b_err, b_bad, 10, "|volume error| (%)",
           "A. Body, sealed test (H20): 44 cases")
    _strip(axes[1], vent, v_eb, v_bad, 0.5, "boundary error e_b (voxels)",
           "B. Ventricles, test (H25): 40 cases")
    h_ok = axes[1].scatter([], [], s=36, color="white", edgecolor=INK, label="within tolerance")
    h_bad = axes[1].scatter([], [], s=70, marker="X", color="white", edgecolor=INK, label="failure")
    fig.legend(handles=[h_ok, h_bad], loc="outside lower center", ncol=2, frameon=False, fontsize=8.5)
    fig.savefig(OUT / "manuscript_fig1_lights.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.2, 4.0), constrained_layout=True)
    for light in ORDER:
        m = (body["light"] == light).to_numpy()
        ok, bad = m & ~b_bad, m & b_bad
        ax.scatter(body.loc[ok, "s_flip"], body.loc[ok, "s_stage"], s=36, color=COLOR[light], edgecolor=INK,
                   linewidth=0.6, zorder=3, label=f"{LABEL[light]} (n = {m.sum()})")
        ax.scatter(body.loc[bad, "s_flip"], body.loc[bad, "s_stage"], s=80, marker="X", color=COLOR[light],
                   edgecolor=INK, linewidth=0.9, zorder=4)
    ax.set_xlim(0, 0.345)
    ax.set_ylim(0, 0.12)
    for x, txt in ((0.05, "τ/2"), (0.20, "2τ")):
        ax.axvline(x, color=MUTED, linewidth=0.9, linestyle=(0, (4, 3)))
        ax.text(x, 0.118, f" {txt}", va="top", fontsize=8, color=MUTED)
    ax.axhline(0.10, color=MUTED, linewidth=0.9, linestyle=(0, (4, 3)))
    ax.text(0.003, 0.101, "τ", va="bottom", ha="left", fontsize=8, color=MUTED)
    ax.scatter([], [], s=80, marker="X", color="white", edgecolor=INK, label="failure (|error| > 10%)")
    ax.set_xlabel("s_flip: spread of volume across the 8 flips / V₀", color=INK, fontsize=9)
    ax.set_ylabel("s_stage: |stage 1 − stage 2| / V₀", color=INK, fontsize=9)
    ax.set_title("Body, sealed test (H20): the two stability signals", color=INK, fontsize=10, loc="left")
    ax.legend(frameon=False, fontsize=8, loc="center right", bbox_to_anchor=(1.0, 0.62))
    _style(ax)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    fig.savefig(OUT / "manuscript_fig2_signals.png", dpi=200)
    plt.close(fig)
    print("figuras escritas en", OUT)


if __name__ == "__main__":
    main()
