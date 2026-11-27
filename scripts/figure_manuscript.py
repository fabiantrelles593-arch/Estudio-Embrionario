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
from matplotlib import font_manager  # noqa: E402

# Plantilla de T-USON (27 nov 2026): figuras en color a 300 ppp o más, rótulos en Arial si se puede, resumen gráfico
# con fondo blanco. Si Arial no está instalada se usa la fuente por defecto.
if any(f.name == "Arial" for f in font_manager.fontManager.ttflist):
    plt.rcParams["font.family"] = "Arial"
DPI = 300

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
           "(a) Body, sealed test (H20): 44 cases")
    _strip(axes[1], vent, v_eb, v_bad, 0.5, "boundary error e_b (voxels)",
           "(b) Ventricles, test (H25): 40 cases")
    h_ok = axes[1].scatter([], [], s=36, color="white", edgecolor=INK, label="within tolerance")
    h_bad = axes[1].scatter([], [], s=70, marker="X", color="white", edgecolor=INK, label="failure")
    fig.legend(handles=[h_ok, h_bad], loc="outside lower center", ncol=2, frameon=False, fontsize=8.5)
    fig.savefig(OUT / "manuscript_fig1_lights.png", dpi=DPI)
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
    ax.set_xlabel("s_flip: spread of volume across the 8 flips / $V_0$", color=INK, fontsize=9)
    ax.set_ylabel("s_stage: |stage 1 − stage 2| / $V_0$", color=INK, fontsize=9)
    ax.set_title("Body, sealed test (H20): the two stability signals", color=INK, fontsize=10, loc="left")
    ax.legend(frameon=False, fontsize=8, loc="center right", bbox_to_anchor=(1.0, 0.62))
    _style(ax)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    fig.savefig(OUT / "manuscript_fig2_signals.png", dpi=DPI)
    plt.close(fig)
    graphical_abstract()
    print("figuras escritas en", OUT)


def graphical_abstract():
    """Resumen gráfico de 660 × 295 px (norma de T-USON): el protocolo y dónde se paró cada estudio.
    Los recuentos son los de los documentos de resultados de H19, H20, H23, H24 y H25.
    Escribe además ``manuscript_graphical_abstract_300dpi.png`` (1980 × 885 px, misma proporción) para la caja de la
    plantilla LaTeX, que pide al menos 300 ppp."""
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    fig = plt.figure(figsize=(6.6, 2.95), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 660)
    ax.set_ylim(0, 295)
    ax.axis("off")
    fig.patch.set_facecolor("#ffffff")
    ax.text(14, 276, "A preregistered, sealed-test protocol for per-case reliability flags", fontsize=10.5,
            color=INK, weight="bold", va="center")
    steps = ["Preregister\ntolerance, rule,\nminimums", "Feasibility\ngate (G0)", "Calibration\ngate",
             "Freeze +\nSHA-256\nfingerprint", "Open test\nonce", "Three-state\nverdict"]
    w, h, y, gap = 92, 70, 160, 14
    xs = [14 + i * (w + gap) for i in range(len(steps))]
    for i, (x, s) in enumerate(zip(xs, steps)):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=6",
                                    facecolor="#ffffff", edgecolor=MUTED, linewidth=1))
        ax.text(x + w / 2, y + h / 2, s, ha="center", va="center", fontsize=8, color=INK, linespacing=1.15)
        if i < len(steps) - 1:
            ax.add_patch(FancyArrowPatch((x + w + 1, y + h / 2), (x + w + gap - 1, y + h / 2),
                                         arrowstyle="-|>", mutation_scale=8, color=MUTED, linewidth=1))
    notes = [
        (xs[2], "Stopped here,\ntest not opened:", "#d03b3b",
         "image observables\n(2 of 16 greens failed)\nventricles, first rules\n(0 and 3 greens of 34)"),
        (xs[4], "Opened once:", "#0ca30c",
         "body: 1 of 21 greens\nfailed (CI 0–14%)\nventricles: 19 greens,\nnot evaluable"),
    ]
    for x, head, col, body in notes:
        ax.plot([x + w / 2, x + w / 2], [y - 2, 132], color=col, linewidth=1.2)
        ax.text(x + w / 2, 126, head, ha="center", va="top", fontsize=7.5, color=INK, weight="bold")
        ax.text(x + w / 2, 100, body, ha="center", va="top", fontsize=7.2, color=INK, linespacing=1.15)
    ax.text(xs[5] + w / 2, 126, "Separation needs\n≥ 10 failures\n(rule S-1)", ha="center", va="top", fontsize=7.2,
            color=MUTED, linespacing=1.15)
    ax.text(14, 12, "3D high-frequency ultrasound, mouse embryos (public dataset). No human or clinical data.",
            fontsize=7, color=MUTED)
    fig.savefig(OUT / "manuscript_graphical_abstract.png", dpi=100, facecolor=fig.get_facecolor())
    fig.savefig(OUT / "manuscript_graphical_abstract_300dpi.png", dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    main()
