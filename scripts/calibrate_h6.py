"""Calibración H6: elige la variable por validación cruzada (una forma fuera) y congela los modelos.

Debe ejecutarse y commitearse ANTES del barrido de confirmación (``run_h6.py --phase test``).
"""
import hashlib
import json
from pathlib import Path

import pandas as pd

from geovida.h6 import FEATURES, add_features, freeze_models, loso_logloss, select_feature

RAW = Path("results/raw/h6cal_sweep.csv.gz")
OUT = Path("results/summary/h6_frozen_models.json")
LOSO_OUT = Path("results/summary/h6_calibration_loso.csv")


def main():
    df = add_features(pd.read_csv(RAW))
    best, tab = select_feature(df)
    col = FEATURES[best]
    loso = pd.concat([loso_logloss(df, c).assign(feature=n) for n, c in FEATURES.items()])
    loso.to_csv(LOSO_OUT, index=False)
    models = freeze_models(df, col)
    payload = {"source": str(RAW), "sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
               "endpoint": "|err_volume| <= 0.05", "feature": best, "column": col,
               "selection": tab.to_dict(orient="records"), "models": models}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(tab.to_string(index=False))
    print("\nElegida:", best, f"({col})")
    for k, m in models.items():
        print(f"{k:28s} a={m['intercept']:+.2f}  b={m['slope']:+.2f}  n={m['n']}")
    by_stratum = loso.groupby(["feature", "segmenter", "profile"])["logloss"].mean().unstack(0)
    print("\nlogloss LOSO por estrato:\n", by_stratum.round(3).to_string())


if __name__ == "__main__":
    main()
