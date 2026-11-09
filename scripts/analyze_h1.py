"""Análisis preregistrado de H1: tablas, veredictos y figuras."""
import argparse
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from geovida.analysis import (
    add_predictors, compare_predictors, ratio_spread, success_by_level, t_star_table,
)

OKABE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000"]
STEP = 1.5  # un paso de rejilla = cociente <= 1.5 (ver PREREGISTRO_H1, aclaración A1)
REF = {"profile": "ideal", "anisotropy": 1.0, "segmenter": "global"}


def _ref(df):
    return df[(df.profile == REF["profile"]) & (df.anisotropy == REF["anisotropy"])
              & (df.segmenter == REF["segmenter"])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="results/raw/h1_sweep.csv.gz")
    ap.add_argument("--outdir", default="results/summary")
    ap.add_argument("--figdir", default="docs/figures")
    a = ap.parse_args()
    out, figs = Path(a.outdir), Path(a.figdir)
    out.mkdir(parents=True, exist_ok=True); figs.mkdir(parents=True, exist_ok=True)

    df = add_predictors(pd.read_csv(a.raw))
    df["v_ok"] = df["err_volume"].abs() <= 0.05
    df["topology_ok"] = df["topology_ok"].astype(bool)
    df["ratio_min_solid"] = df["t_min_over_hxy"] / df["t_solid_over_hxy"]
    strata = ["shape", "segmenter", "anisotropy", "profile"]

    tab_v = success_by_level(df, "v_ok", strata)
    tab_t = success_by_level(df, "topology_ok", strata)
    tab_v.assign(endpoint="v_ok").pipe(lambda d: pd.concat([d, tab_t.assign(endpoint="topology_ok")])) \
        .to_csv(out / "h1_success_by_level.csv", index=False)

    ratio = df.groupby("shape")["ratio_min_solid"].first()
    def with_pred(ts):
        ts = ts.copy()
        ts["ratio"] = ts["shape"].map(ratio)
        ts["P1"] = ts["t_star"]
        ts["P3"] = ts["t_star"] / ts["anisotropy"]
        ts["P4"] = ts["t_star"] * ts["ratio"]
        ts["P6"] = ts["t_star"] * ts["ratio"] / ts["anisotropy"]
        return ts
    ts_v, ts_t = with_pred(t_star_table(tab_v, strata)), with_pred(t_star_table(tab_t, strata))
    pd.concat([ts_v.assign(endpoint="v_ok"), ts_t.assign(endpoint="topology_ok")]) \
        .to_csv(out / "h1_t_star.csv", index=False)

    def refrows(ts):
        return ts[(ts.profile == REF["profile"]) & (ts.anisotropy == REF["anisotropy"])
                  & (ts.segmenter == REF["segmenter"])]
    rv, rt = refrows(ts_v), refrows(ts_t)

    verdict = {}
    # H1a
    sp_v = ratio_spread(rv["P1"])
    verdict["H1a"] = {
        "t_star_by_shape": dict(zip(rv["shape"], rv["t_star"])),
        "all_reached": bool(rv["t_star"].notna().all()),
        "max_t_star": float(rv["t_star"].max()) if rv["t_star"].notna().any() else None,
        "ratio_spread_t_solid": sp_v,
        "supported": bool(rv["t_star"].notna().all() and rv["t_star"].max() <= 6 and sp_v <= STEP),
    }
    # H1b
    sp_min, sp_solid = ratio_spread(rt["P4"]), ratio_spread(rt["P1"])
    verdict["H1b"] = {
        "t_star_by_shape_in_t_solid_over_h": dict(zip(rt["shape"], rt["t_star"])),
        "t_min_over_h_star_by_shape": dict(zip(rt["shape"], rt["P4"])),
        "ratio_spread_t_min": sp_min, "ratio_spread_t_solid": sp_solid,
        "supported": bool(sp_min <= STEP),
        "solid_predictor_spread_ge_2_steps_as_expected": bool(sp_solid >= 2.25 if not math.isnan(sp_solid) else False),
    }
    # H1c: colapso por anisotropía (estrato ideal/global) + AIC
    h1c = {}
    for name, ts, pcol in (("v_ok", ts_v, "P3"), ("topology_ok", ts_t, "P6")):
        sub = ts[(ts.profile == "ideal") & (ts.segmenter == "global")]
        per_shape = {s: ratio_spread(g[pcol]) for s, g in sub.groupby("shape")}
        per_shape_xy = {s: ratio_spread(g["P1" if name == "v_ok" else "P4"]) for s, g in sub.groupby("shape")}
        h1c[name] = {"max_ratio_spread_hmax_predictor": per_shape, "max_ratio_spread_hxy_predictor": per_shape_xy}
    aic_rows = []
    for (seg, prof), g in df.groupby(["segmenter", "profile"]):
        for ep in ("v_ok", "topology_ok"):
            t = compare_predictors(g, ep); t["segmenter"], t["profile"], t["endpoint"] = seg, prof, ep
            aic_rows.append(t)
    aic = pd.concat(aic_rows); aic.to_csv(out / "h1_predictor_comparison.csv", index=False)
    ref_aic = aic[(aic.segmenter == "global") & (aic.profile == "ideal")].set_index(["endpoint", "predictor"])["aic"]
    h1c["delta_aic_ref"] = {ep: {"P3_minus_P1": float(ref_aic[(ep, "P3")] - ref_aic[(ep, "P1")]),
                                "P6_minus_P4": float(ref_aic[(ep, "P6")] - ref_aic[(ep, "P4")]),
                                "best": str(ref_aic[ep].idxmin())} for ep in ("v_ok", "topology_ok")}
    ok_aic = all(h1c["delta_aic_ref"][ep][k] < 0 for ep in ("v_ok", "topology_ok")
                 for k in ("P3_minus_P1", "P6_minus_P4"))
    def finite_max(d):
        v = [x for x in d.values()]
        return math.nan if any(math.isnan(x) for x in v) else max(v)
    h1c["max_spread_hmax"] = {ep: finite_max(h1c[ep]["max_ratio_spread_hmax_predictor"]) for ep in ("v_ok", "topology_ok")}
    verdict["H1c"] = {**h1c, "supported": bool(ok_aic and all(
        not math.isnan(v) and v <= STEP for v in h1c["max_spread_hmax"].values()))}
    # H1d: segmentadores (perfil ideal, a=1)
    h1d = {}
    for name, ts, pcol in (("v_ok", ts_v, "P1"), ("topology_ok", ts_t, "P4")):
        sub = ts[(ts.profile == "ideal") & (ts.anisotropy == 1.0)]
        h1d[name] = {s: ratio_spread(g[pcol]) for s, g in sub.groupby("shape")}
    verdict["H1d"] = {**{k: v for k, v in h1d.items()},
                      "supported": bool(all((not math.isnan(x)) and x <= STEP
                                            for d in h1d.values() for x in d.values()))}
    # Chequeo de consistencia (Horner-like)
    b = df[(df["shape"] == "ball") & (df.profile == "ideal") & (df.anisotropy == 1.0)
           & (df.segmenter == "global")].copy()
    b["diam_err"] = (1 + b["err_volume"]) ** (1 / 3) - 1
    med = b.groupby("t_over_h")["diam_err"].apply(lambda s: float(np.median(np.abs(s))))
    verdict["horner_consistency"] = {"median_abs_diameter_error_by_t_over_h": med.to_dict(),
                                     "pass_ge_6": bool((med[med.index >= 6] <= 0.02 + 0.005).all())}
    (out / "h1_verdicts.json").write_text(json.dumps(verdict, indent=2, default=float))

    # Resumen de error con signo de V (para el informe)
    summ = df.groupby(["shape", "segmenter", "profile", "anisotropy", "t_over_h"]).agg(
        err_volume_median=("err_volume", "median"),
        err_volume_q25=("err_volume", lambda s: s.quantile(.25)),
        err_volume_q75=("err_volume", lambda s: s.quantile(.75)),
        err_area_mc_median=("err_area_mc", "median"),
        err_area_faces_median=("err_area_faces", "median"),
        dice_median=("dice", "median"), hd95_median=("hd95", "median")).reset_index()
    summ.to_csv(out / "h1_error_summary.csv", index=False)

    # ---------- Figuras ----------
    shapes = list(df["shape"].unique())
    col = dict(zip(shapes, OKABE))
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

    fig, axs = plt.subplots(1, 3, figsize=(11, 3.4), sharey=True)
    for ax, seg in zip(axs, ["global", "otsu", "smoothed_otsu"]):
        for s in shapes:
            g = summ[(summ["shape"] == s) & (summ.segmenter == seg) & (summ.profile == "ideal") & (summ.anisotropy == 1.0)]
            ax.plot(g.t_over_h, 100 * g.err_volume_median, "-o", ms=3, color=col[s], label=s)
        ax.axhspan(-5, 5, color="0.9", zorder=0); ax.set_xscale("log"); ax.set_title(seg)
        ax.set_xlabel("t / h_xy (vóxeles por grosor)")
    axs[0].set_ylabel("Error mediano de volumen (%)"); axs[0].legend(fontsize=7, frameon=False)
    fig.suptitle("Error de volumen vs resolución (perfil ideal, vóxel isótropo); banda gris = ±5 %", y=1.02)
    fig.tight_layout(); fig.savefig(figs / "h1_volume_error.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    fig, axs = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
    for ax, (pcol, lab) in zip(axs, [("t_solid_over_hxy", "t_solid / h_xy"), ("t_min_over_hxy", "t_min / h_xy")]):
        for s in shapes:
            g = _ref(df[df["shape"] == s]).groupby("t_over_h").agg(p=("topology_ok", "mean"), x=(pcol, "first"))
            ax.plot(g.x, g.p, "-o", ms=3, color=col[s], label=s)
        ax.axhline(0.95, color="0.6", ls=":"); ax.set_xscale("log"); ax.set_xlabel(lab)
    axs[0].set_ylabel("Topología correcta (proporción)"); axs[1].legend(fontsize=7, frameon=False)
    fig.suptitle("¿Colapsan las clases de forma? (ideal, isótropo, umbral oráculo)", y=1.02)
    fig.tight_layout(); fig.savefig(figs / "h1_topology_collapse_shape.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    fig, axs = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
    base = df[(df.profile == "ideal") & (df.segmenter == "global")]
    for ax, (pcol, lab) in zip(axs, [("t_min_over_hxy", "t_min / h_xy"), ("t_min_over_hmax", "t_min / h_max")]):
        for an, c in zip((1.0, 2.0, 3.0), OKABE[:3]):
            g = base[base.anisotropy == an].groupby(["shape", "t_over_h"]).agg(p=("topology_ok", "mean"), x=(pcol, "first")).reset_index()
            ax.scatter(g.x, g.p, s=14, color=c, label=f"h_z/h_xy = {an:g}", alpha=.8)
        ax.axhline(0.95, color="0.6", ls=":"); ax.set_xscale("log"); ax.set_xlabel(lab)
    axs[0].set_ylabel("Topología correcta (proporción)"); axs[1].legend(fontsize=7, frameon=False)
    fig.suptitle("¿Colapsa la anisotropía con el vóxel peor? (cada punto = forma x nivel)", y=1.02)
    fig.tight_layout(); fig.savefig(figs / "h1_topology_collapse_anisotropy.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    fig, axs = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
    for ax, prof in zip(axs, ["ideal", "realistic"]):
        for seg, c in zip(["global", "otsu", "smoothed_otsu"], OKABE[:3]):
            g = summ[(summ["shape"] == "ellipsoid") & (summ.segmenter == seg) & (summ.profile == prof) & (summ.anisotropy == 1.0)]
            ax.plot(g.t_over_h, 100 * g.err_volume_median, "-o", ms=3, color=c, label=seg)
            ax.fill_between(g.t_over_h, 100 * g.err_volume_q25, 100 * g.err_volume_q75, color=c, alpha=.15)
        ax.axhspan(-5, 5, color="0.9", zorder=0); ax.set_xscale("log"); ax.set_title(f"elipsoide, perfil {prof}")
        ax.set_xlabel("t / h_xy")
    axs[0].set_ylabel("Error de volumen (%) mediana e IQR"); axs[0].legend(fontsize=7, frameon=False)
    fig.tight_layout(); fig.savefig(figs / "h1_segmenter_bias.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    print(json.dumps(verdict, indent=2, default=float))


if __name__ == "__main__":
    main()
