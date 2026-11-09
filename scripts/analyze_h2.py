"""Veredictos preregistrados de H2 y figuras."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OKABE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"]


def pick(df, **kw):
    sel = df
    for k, v in kw.items():
        sel = sel[np.isclose(sel[k], v)] if isinstance(v, float) else sel[sel[k] == v]
    return sel


def one(df, col, **kw):
    sel = pick(df, **kw)
    assert len(sel) == 1, (kw, len(sel))
    return float(sel[col].iloc[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", default="results/summary/h2_cells.csv")
    ap.add_argument("--outdir", default="results/summary")
    ap.add_argument("--figdir", default="docs/figures")
    a = ap.parse_args()
    df = pd.read_csv(a.cells)
    out, figs = Path(a.outdir), Path(a.figdir); figs.mkdir(parents=True, exist_ok=True)
    v = {}

    base = dict(sigma_s=0.5, n=20, meas=0.02)
    sm = {f: one(df, "max_abs_bias", feature=f, estimator="stage_mean", **base)
          for f in ("growth", "saturating", "switch")}
    v["H2a"] = {"max_abs_bias_stage_mean_sigma0.5_n20": sm,
                "supported": bool(sm["switch"] > 0.05 and sm["growth"] < 0.05)}

    cov = {}
    for sg in (0.25, 0.5):
        c3 = one(df, "mean_coverage", feature="switch", estimator="stage_mean", sigma_s=sg, n=3, meas=0.02)
        c20 = one(df, "mean_coverage", feature="switch", estimator="stage_mean", sigma_s=sg, n=20, meas=0.02)
        cov[str(sg)] = {"coverage_n3": c3, "coverage_n20": c20}
    v["H2b"] = {"mean_coverage_switch": cov,
                "supported": bool(all(c["coverage_n20"] < c["coverage_n3"] and c["coverage_n20"] < 0.90
                                      for c in cov.values()))}

    kw = dict(feature="switch", sigma_s=0.5, n=20, meas=0.02)
    b_mean = one(df, "max_abs_bias", estimator="stage_mean", **kw)
    b_spl = one(df, "max_abs_bias", estimator="spline", **kw)
    b_cor = {str(r): one(df, "max_abs_bias", estimator="spline_corrected", sigma_ratio=r, **kw)
             for r in (0.5, 1.0, 2.0)}
    v["H2c"] = {"max_abs_bias": {"stage_mean": b_mean, "spline": b_spl, "spline_corrected_by_sigma_ratio": b_cor},
                "supported": bool(b_cor["1.0"] <= 0.5 * min(b_mean, b_spl))}

    shares = {}
    for f in ("growth", "saturating", "switch"):
        for sg in (0.25, 0.5):
            for n in (1, 3):
                shares[f"{f}/sigma{sg}/n{n}"] = one(df, "bias2_share", feature=f, estimator="stage_mean",
                                                    sigma_s=sg, n=n, meas=0.02)
    v["H2d"] = {"bias2_share": shares, "supported": bool(all(s < 0.5 for s in shares.values()))}

    # Predicciones (sección 7)
    preds = {}
    preds["P1_growth_saturating_lt_2pct_switch_gt_10pct"] = bool(
        sm["growth"] < 0.02 and sm["saturating"] < 0.02 and sm["switch"] > 0.10)
    preds["P2_switch_coverage_lt_60pct_n20_sigma0.5"] = bool(cov["0.5"]["coverage_n20"] < 0.60)
    irm = {e: one(df, "irmse", feature="switch", estimator=e, sigma_s=0.5, n=3, meas=0.02,
                  **({"sigma_ratio": 1.0} if e == "spline_corrected" else {}))
           for e in ("stage_mean", "spline", "spline_corrected")}
    preds["P3_corrected_has_higher_variance_than_stage_mean_n3"] = bool(
        irm["spline_corrected"] > irm["stage_mean"])
    preds["P4_overcorrection_x2_worse_than_correct"] = bool(b_cor["2.0"] > b_cor["1.0"])
    v["predictions_check"] = {"irmse_switch_sigma0.5_n3": irm, **preds}
    (out / "h2_verdicts.json").write_text(json.dumps(v, indent=2))

    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    stages = np.arange(7)
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.3), sharey=True)
    for ax, f in zip(axs, ("growth", "saturating", "switch")):
        for est, ratio, c, lab in (("stage_mean", 1.0, OKABE[0], "media por etapa"),
                                   ("spline", 1.0, OKABE[1], "spline ingenuo"),
                                   ("spline_corrected", 1.0, OKABE[2], "spline corregido (σ correcto)"),
                                   ("spline_corrected", 2.0, OKABE[3], "corregido, σ supuesto ×2")):
            r = pick(df, feature=f, estimator=est, sigma_s=0.5, n=20, meas=0.02, sigma_ratio=ratio).iloc[0]
            ax.plot(stages, [100 * r[f"bias_s{k}"] for k in stages], "-o", ms=3, color=c, label=lab)
        ax.axhline(0, color="0.5", lw=.8); ax.axhspan(-5, 5, color="0.93", zorder=0); ax.set_title(f)
        ax.set_xlabel("etapa nominal")
    axs[0].set_ylabel("Sesgo relativo (%) — σ_s = 0.5, n = 20"); axs[2].legend(fontsize=7, frameon=False)
    fig.tight_layout(); fig.savefig(figs / "h2_bias_by_stage.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(5, 3.4))
    for sg, c in zip((0.0, 0.1, 0.25, 0.5), OKABE):
        g = pick(df, feature="switch", estimator="stage_mean", sigma_s=sg, meas=0.02).sort_values("n")
        g = g[g.n >= 3]
        ax.plot(g.n, 100 * g.mean_coverage, "-o", ms=3, color=c, label=f"σ_s = {sg:g}")
    ax.axhline(95, color="0.5", ls=":"); ax.set_xscale("log"); ax.set_xlabel("especímenes por etapa (n)")
    ax.set_ylabel("Cobertura del IC bootstrap al 95 % (%)"); ax.legend(fontsize=7, frameon=False)
    ax.set_title("Transición ('switch'): más n, más engañoso")
    fig.tight_layout(); fig.savefig(figs / "h2_coverage_vs_n.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(5, 3.4))
    for est, ratio, c, lab in (("stage_mean", 1.0, OKABE[0], "media por etapa"),
                               ("spline", 1.0, OKABE[1], "spline ingenuo"),
                               ("spline_corrected", 1.0, OKABE[2], "spline corregido")):
        g = pick(df, feature="switch", estimator=est, sigma_s=0.5, meas=0.02, sigma_ratio=ratio).sort_values("n")
        ax.plot(g.n, 100 * g.irmse, "-o", ms=3, color=c, label=lab)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("especímenes por etapa (n)")
    ax.set_ylabel("RMSE relativo integrado (%)"); ax.legend(fontsize=7, frameon=False)
    ax.set_title("Costo de corregir: varianza (σ_s = 0.5, switch)")
    fig.tight_layout(); fig.savefig(figs / "h2_irmse_vs_n.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    print(json.dumps(v, indent=2))


if __name__ == "__main__":
    main()
