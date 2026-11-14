"""Análisis de H13 con las reglas de docs/PREREGISTRO_H13.md.

  python scripts/analyze_h13.py            # lee results/raw/h13_conf.csv.gz, escribe results/summary/h13_*

Solo investigación y educación; todo es simulación.
"""
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from geovida import biometry as bio
from geovida import h13

RAW, SUMMARY = Path("results/raw"), Path("results/summary")


def _bins(df):
    return pd.cut(df["fwhm_px"], [0, 2.0, 3.5, 100], labels=["f<=2", "2<f<=3.5", "f>3.5"])


def _boot_ci(wrong, n_boot=2000, seed=h13.BOOT_SEED):
    wrong = np.asarray(wrong, float)
    if len(wrong) == 0:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    b = wrong[rng.integers(0, len(wrong), size=(n_boot, len(wrong)))].mean(axis=1)
    return tuple(np.percentile(b, [2.5, 97.5]))


def strata(df):
    """EXPLORATORIO (estratificación posterior al preregistro): falsos verdes por tipo, segmentador y ancho de
    la función de dispersión, solo dentro de la caja. Los criterios preregistrados son los agregados."""
    d = df[df["region"] == "in"].copy()
    d["fbin"] = _bins(d)
    rows = []
    for (k, s, b), g in d.groupby(["kind", "segmenter", "fbin"], observed=True):
        gr = g[g["light"] == "verde"]
        wrong = (~gr["correct"].astype(bool)).to_numpy()
        lo, hi = _boot_ci(wrong)
        rows.append({"kind": k, "segmenter": s, "fwhm_bin": b, "n_cases": len(g), "n_green": len(gr),
                     "n_wrong_green": int(wrong.sum()),
                     "false_green": float(wrong.mean()) if len(gr) else np.nan, "fg_lo": lo, "fg_hi": hi,
                     "n_yellow": int((g["light"] == "amarillo").sum()), "n_red": int((g["light"] == "rojo").sum()),
                     "n_no_cert": int((~g["in_domain"].astype(bool)).sum())})
    return pd.DataFrame(rows)


def usable_rate_by_cell():
    """Fracción de las medidas de la calibración que quedan a menos de la mitad de la magnitud verdadera
    (|error| ≤ 0.5·n): una medida «utilizable». Diagnóstico del mecanismo de fallo; no entró en H13."""
    cal = pd.read_csv(RAW / "h13_cal.csv.gz")
    cal["usable"] = cal["err_px"].abs() <= 0.5 * cal["n"]
    return (cal.groupby(["kind", "segmenter", "n", "fwhm_px"])["usable"].mean()
            .rename("usable_rate").reset_index())


def wrong_greens(df):
    d = df[(df["segmenter"] == h13.PRIMARY_SEGMENTER) & (df["region"] == "in") & (df["light"] == "verde")
           & (~df["correct"].astype(bool))].copy()
    d["n_measured"] = d["measured_mm"] / d["h_mm"]
    d["err_px"] = (d["measured_mm"] - d["truth_mm"]) / d["h_mm"]
    cols = ["kind", "n_nominal", "n_measured", "fwhm_px", "truth_mm", "measured_mm", "err_px", "bias_mm", "sd_mm", "p"]
    return d[cols].sort_values(["kind", "fwhm_px", "n_nominal"])


def reliability(df):
    d = df[(df["segmenter"] == h13.PRIMARY_SEGMENTER) & (df["region"] == "in") & df["in_domain"].astype(bool)].copy()
    d["pbin"] = pd.cut(d["p"], np.linspace(0, 1, 11), include_lowest=True)
    out = d.groupby(["kind", "pbin"], observed=True).agg(n=("p", "size"), p_mean=("p", "mean"),
                                                         observed=("correct", "mean")).reset_index()
    out["pbin"] = out["pbin"].astype(str)
    return out


def secondary(df):
    """Control (otsu) con las mismas reglas de H13a/H13b: se espera que casi no tenga verdes."""
    d = df[df["segmenter"] == "otsu"].copy()
    d["segmenter"] = h13.PRIMARY_SEGMENTER           # reutiliza las funciones, que filtran por el primario
    return {k: h13.false_green_verdict(d[d["kind"] == k]) for k in bio.KINDS}


def main():
    warnings.filterwarnings("ignore")
    df = pd.read_csv(RAW / "h13_conf.csv.gz")
    verdicts = h13.evaluate_h13(df)
    verdicts["secondary_otsu"] = secondary(df)
    prim = df[(df["segmenter"] == h13.PRIMARY_SEGMENTER) & (df["region"] == "in")]
    verdicts["lights_in_box"] = {k: g["light"].value_counts().to_dict() for k, g in prim.groupby("kind")}
    verdicts["no_certificate_in_box"] = {k: int((~g["in_domain"].astype(bool)).sum()) for k, g in prim.groupby("kind")}
    SUMMARY.mkdir(parents=True, exist_ok=True)
    (SUMMARY / "h13_verdicts.json").write_text(json.dumps(verdicts, indent=2, default=float))
    strata(df).to_csv(SUMMARY / "h13_strata.csv", index=False)
    reliability(df).to_csv(SUMMARY / "h13_reliability.csv", index=False)
    usable_rate_by_cell().to_csv(SUMMARY / "h13_usable_rate_by_cell.csv", index=False)
    wrong_greens(df).to_csv(SUMMARY / "h13_wrong_greens.csv", index=False)
    print(json.dumps(verdicts, indent=2, default=float))
    pd.set_option("display.width", 200)
    print(strata(df).round(3).to_string(index=False))
    print(reliability(df).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
