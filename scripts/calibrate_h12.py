"""Calibración de H12: ajusta y congela los modelos de volumen y topología y las envolventes de la
guardia con el barrido de calibración de ecografía simulada. Se ejecuta y se confirma en git ANTES
de los barridos de confirmación (test, unseen, shift)."""
import hashlib
import json
from pathlib import Path

import pandas as pd

from geovida import h9, h12

RAW = Path("results/raw/h12_cal.csv.gz")
OUT = Path("results/summary/h12_frozen.json")
LOSO_OUT = Path("results/summary/h12_calibration_loso.csv")


def main():
    df = h9.add_features(pd.read_csv(RAW))
    frozen = h12.freeze_us(df)
    loso = pd.concat([h9.loso(df, feats).assign(set=name) for name, feats in h9.TOPO_SETS.items()])
    loso.to_csv(LOSO_OUT, index=False)
    frozen["source"] = str(RAW)
    frozen["rows"] = int(len(df))
    frozen["content_sha256"] = hashlib.sha256(
        pd.util.hash_pandas_object(df[["shape", "t_over_h", "anisotropy", "profile", "rep",
                                       "segmenter", "volume"]], index=False).values.tobytes()
    ).hexdigest()
    OUT.write_text(json.dumps(frozen, indent=2, sort_keys=True))
    print(pd.DataFrame(frozen["selection"]).to_string(index=False))
    print("\nElegido:", frozen["selected"], frozen["features"])
    print("\nModelos de volumen (logit de ln(d/h_geo)):")
    for k, m in sorted(frozen["volume_models"].items()):
        print(f"  {k:32s} a={m['intercept']:+.3f} b={m['slope']:.3f} n={m['n']}")
    print(loso.groupby(["set", "segmenter", "profile"])["logloss"].mean().unstack(0).round(3).to_string())
    for endpoint, env in frozen["envelopes"].items():
        print(f"\nEnvolvente ({endpoint}):")
        for k, v in env.items():
            print("  ", k, None if v is None else {c: [round(x, 2) for x in r] for c, r in v.items()})


if __name__ == "__main__":
    main()
