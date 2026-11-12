"""Análisis de H14 con las reglas de docs/PREREGISTRO_H14.md (solo simulación)."""
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from geovida import h13, h14

RAW, SUMMARY = Path("results/raw"), Path("results/summary")


def strata(df):
    """EXPLORATORIO: verdes equivocados por caso y casos sin certificado, por PSF, con y sin compuerta."""
    d = df[df["region"] == "in"].copy()
    d["fbin"] = pd.cut(d["fwhm_px"], [0, 2.0, 3.5, 100], labels=["f<=2", "2<f<=3.5", "f>3.5"])
    rows = []
    for (v, k, s, b), g in d.groupby(["variant", "kind", "segmenter", "fbin"], observed=True):
        wrong = (g["light"] == "verde") & ~g["correct"].astype(bool)
        rows.append({"variant": v, "kind": k, "segmenter": s, "fwhm_bin": b, "n_cases": len(g),
                     "n_green": int((g["light"] == "verde").sum()), "n_wrong_green": int(wrong.sum()),
                     "wrong_green_per_case": float(wrong.mean()), "n_no_cert": int((~g["in_domain"].astype(bool)).sum())})
    return pd.DataFrame(rows)


def main():
    warnings.filterwarnings("ignore")
    df = pd.read_csv(RAW / "h14_conf.csv.gz")
    v = h14.evaluate_h14(df)
    g = df[df["variant"] == "gated"]
    v["gated_h14_descriptive"] = {"h13e": h13.human_yardstick(g), "h13f": h13.measurement_share_summary(g)}
    (SUMMARY / "h14_verdicts.json").write_text(json.dumps(v, indent=2, default=float))
    s = strata(df)
    s.to_csv(SUMMARY / "h14_strata.csv", index=False)
    print(json.dumps(v, indent=2, default=float))
    pd.set_option("display.width", 200)
    print(s[s["segmenter"] == "smoothed_otsu"].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
