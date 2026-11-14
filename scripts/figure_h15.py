"""Figura de H15: falsos verdes por compresión y calibración con y sin la cadena (solo simulación)."""
import warnings
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from geovida import biometry as bio
from geovida import h13, h15

RAW, FIG = Path("results/raw"), Path("docs/figures")
BLUE, ORANGE, GREY = "#0072B2", "#D55E00", "#6b6b6b"      # Okabe-Ito: distinguibles con daltonismo


def reliability(d, bins=10):
    p, y = d["p"].to_numpy(float), d["correct"].to_numpy(float)
    edges = np.linspace(0, 1, bins + 1)
    k = np.clip(np.digitize(p, edges) - 1, 0, bins - 1)
    out = [(p[k == i].mean(), y[k == i].mean(), int((k == i).sum())) for i in range(bins) if (k == i).sum() >= 20]
    return np.array(out)


def main():
    warnings.filterwarnings("ignore")
    df = pd.read_csv(RAW / "h15_conf.csv.gz")
    prim = df[(df["segmenter"] == h13.PRIMARY_SEGMENTER) & (df["region"] == "in")]
    body = prim[(prim["kind"] == bio.BODY) & prim["in_domain"].astype(bool)]
    stats = {}
    for v in ("clean", "chain"):
        for kind in bio.KINDS:
            d = prim[(prim["variant"] == v) & (prim["kind"] == kind) & prim["in_domain"].astype(bool)]
            stats[(v, kind)] = (bio.expected_calibration_error(d["p"].to_numpy(float), d["correct"].to_numpy(float)),
                                float(d["p"].mean()), float(d["correct"].mean()), len(d))
    for k, (ece, mp, acc, n) in stats.items():
        print(f"{k}: ECE={ece:.3f}  p media={mp:.3f}  acierto observado={acc:.3f}  n={n}")

    t = h15.compression_terciles(df)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
    a = ax[0]
    labels = ["baja", "media", "alta"]
    x = np.arange(3)
    for j, (kind, col, name) in enumerate(((bio.BODY, ORANGE, "Datación (cuerpo)"), (bio.SLOT, BLUE, "Decisión (ranura)"))):
        vals = [100 * t[(t.kind == kind) & (t.compression == c)]["false_green"].iloc[0] for c in labels]
        ns = [int(t[(t.kind == kind) & (t.compression == c)]["n_green"].iloc[0]) for c in labels]
        bars = a.bar(x + (j - 0.5) * 0.36, vals, 0.34, color=col, label=name)
        for b, v, n in zip(bars, vals, ns):
            a.text(b.get_x() + b.get_width() / 2, v + 0.6, f"{v:.1f} %", ha="center", fontsize=8.5,
                   bbox=dict(facecolor="white", edgecolor="none", pad=0.8))
    a.axhline(10, color="black", lw=1, ls="--")
    a.text(2.62, 10.4, "límite 10 %", ha="right", fontsize=8.5)
    a.set_xticks(x, [f"compresión {c}" for c in labels])
    a.set_ylabel("falsos verdes entre los verdes (%)")
    a.set_title("A · Con la cadena, el error crece con la compresión logarítmica", fontsize=10)
    a.set_ylim(0, 26)
    a.legend(frameon=False, loc="upper left")
    a.spines[["top", "right"]].set_visible(False)

    b = ax[1]
    b.plot([0, 1], [0, 1], color=GREY, lw=1)
    b.text(0.55, 0.47, "calibración perfecta", color=GREY, fontsize=8.5, rotation=36, ha="center")
    for v, col, mk, name in (("clean", BLUE, "o", "sin cadena"), ("chain", ORANGE, "s", "con cadena")):
        r = reliability(body[body["variant"] == v])
        b.plot(r[:, 0], r[:, 1], marker=mk, color=col, lw=1.6, ms=5, label=f"{name} · ECE {stats[(v, bio.BODY)][0]:.3f}")
    b.set_xlabel("probabilidad que dice el certificado (datación)")
    b.set_ylabel("acierto observado")
    b.set_title("B · Con la cadena la probabilidad se vuelve optimista", fontsize=10)
    b.legend(frameon=False, loc="lower right")
    b.set_xlim(0, 1.02)
    b.set_ylim(0, 1.02)
    b.spines[["top", "right"]].set_visible(False)
    fig.suptitle("H15 (simulación): el certificado de datación frente a una imagen que pasó por pantalla, impresión y foto",
                 fontsize=11, y=1.0)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "h15_chain.png", dpi=150, bbox_inches="tight")
    print("figura:", FIG / "h15_chain.png")


if __name__ == "__main__":
    main()
