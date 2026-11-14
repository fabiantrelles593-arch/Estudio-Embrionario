"""Análisis confirmatorio H3/H4 según docs/PREREGISTRO_H3.md (no cambia criterios)."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import ticker

from geovida.analysis import add_predictors, add_vq_predictors, predict_frozen
from geovida.h3 import evaluate_h3, evaluate_h4

RAW = Path("results/raw/h3_sweep.csv.gz")
FROZEN = Path("results/summary/h3_frozen_models.json")
OUT = Path("results/summary")
FIG = Path("docs/figures")
OKABE = {"capsule": "#0072B2", "cylinder": "#D55E00", "oblate": "#009E73"}


def fmt_log(ax, ticks=(0.25, 0.5, 1, 2, 4, 8, 12)):
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.xaxis.set_minor_formatter(ticker.NullFormatter())
    lo, hi = ax.get_xlim()
    ax.set_xticks([t for t in ticks if lo <= t <= hi])


def main():
    df = add_vq_predictors(add_predictors(pd.read_csv(RAW)))
    frozen = json.loads(FROZEN.read_text())
    h3 = evaluate_h3(df, frozen)
    h4 = evaluate_h4(df)

    pd.DataFrame(h3["strata"]).round(4).to_csv(OUT / "h3_strata.csv", index=False)
    pd.DataFrame(h4["medians"]).to_csv(OUT / "h4_area_medians.csv", index=False)

    # Extensión descriptiva: otsu_clean frente a otsu
    d = df[df["segmenter"].isin(["otsu", "otsu_clean"])].copy()
    d["v_abs_err"] = d["err_volume"].abs()
    ext = (d.groupby(["profile", "segmenter", "t_over_h"])
             .agg(topology_ok=("topology_ok", "mean"), median_err_volume=("err_volume", "median"))
             .reset_index())
    ext.round(4).to_csv(OUT / "h3_extension_otsu_clean.csv", index=False)
    e6 = ext[(ext["profile"] == "realistic") & (ext["t_over_h"] >= 6)]
    piv = e6.pivot(index="t_over_h", columns="segmenter", values="topology_ok")
    pivv = e6.pivot(index="t_over_h", columns="segmenter", values="median_err_volume")
    h3["extension_otsu_clean"] = {
        "topology_gain_points_by_level": {str(k): round(100 * float(v), 1)
                                          for k, v in (piv["otsu_clean"] - piv["otsu"]).items()},
        "volume_error_change_points_by_level": {str(k): round(100 * float(v), 2)
                                                for k, v in (pivv["otsu_clean"] - pivv["otsu"]).items()},
    }

    (OUT / "h3_verdicts.json").write_text(json.dumps({"h3": h3, "h4": h4}, indent=2, default=float))

    # Figura 1: colapso en Q (modelo congelado superpuesto) frente a grosor
    base = df[(df.segmenter == "global") & (df.profile == "ideal")].copy()
    base["v_ok"] = (base.err_volume.abs() <= 0.05).astype(float)
    mdl = frozen["models"]["global|ideal"]
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
    for ax, col, key, lab in [(axs[0], "t_solid_over_hgeo", "t_model", "t_solid / h_geo  (grosor)"),
                              (axs[1], "q_over_hgeo", "q_model", "Q / h_geo = V / (S h_geo)")]:
        for s, c in OKABE.items():
            g = base[base["shape"] == s].groupby(["anisotropy", "t_over_h"]).agg(
                p=("v_ok", "mean"), x=(col, "first")).reset_index()
            ax.scatter(g.x, g.p, s=14, color=c, label=s, alpha=.85)
        xs = np.geomspace(base[col].min(), base[col].max(), 200)
        ax.plot(xs, predict_frozen(mdl[key], xs), color="0.2", lw=1.3, label="modelo congelado de H1")
        ax.axhline(0.95, color="0.7", ls=":"); ax.set_xlabel(lab); fmt_log(ax)
    axs[0].set_ylabel("Proporción con |error de V| ≤ 5 %"); axs[1].legend(fontsize=7, frameon=False)
    fig.suptitle("H3: formas nuevas contra el modelo congelado de H1 (umbral oráculo, imagen ideal)", y=1.02)
    fig.tight_layout(); fig.savefig(FIG / "h3_q_frozen_model_new_shapes.png", dpi=150, bbox_inches="tight")

    # Figura 2: sesgo de área por estimador
    med = pd.DataFrame(h4["medians"])
    fig, axs = plt.subplots(1, 3, figsize=(10, 3.2), sharey=True)
    for ax, s in zip(axs, h4["shapes"]):
        m = med[med["shape"] == s]
        for col, lab, c in [("err_area_faces", "conteo de caras", "#999999"),
                            ("err_area_mc", "marching cubes (v0.1)", "#D55E00"),
                            ("err_area_sdf", "distancia con signo (v0.2)", "#0072B2")]:
            ax.plot(m["t_over_h"], 100 * m[col], marker="o", ms=3.5, color=c, label=lab)
        ax.axhline(0, color="0.5", lw=.8); ax.set_title(s); ax.set_xlabel("t / h"); fmt_log(ax, (1.5, 2, 3, 4, 6, 8, 12))
    axs[0].set_ylabel("Error mediano de área (%)"); axs[0].legend(fontsize=7, frameon=False)
    fig.suptitle("H4: sesgo del área en formas nuevas (oráculo, imagen ideal, vóxel isótropo)", y=1.03)
    fig.tight_layout(); fig.savefig(FIG / "h4_area_bias_new_shapes.png", dpi=150, bbox_inches="tight")

    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "strata" and kk != "medians"}
                      for k, v in {"h3": h3, "h4": h4}.items()}, indent=2, default=float))


if __name__ == "__main__":
    main()
