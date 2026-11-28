"""Análisis de H15 con las reglas de docs/PREREGISTRO_H15.md (solo simulación)."""
import json
import warnings
from pathlib import Path

import pandas as pd

from geovida import h15

RAW, SUMMARY = Path("results/raw"), Path("results/summary")


def main():
    warnings.filterwarnings("ignore")
    df = pd.read_csv(RAW / "h15_conf.csv.gz")
    v = h15.evaluate_h15(df)
    (SUMMARY / "h15_verdicts.json").write_text(json.dumps(v, indent=2, default=float))
    t = h15.compression_terciles(df)
    t.to_csv(SUMMARY / "h15_compression_terciles.csv", index=False)
    print(json.dumps(v, indent=2, default=float))
    pd.set_option("display.width", 200)
    print(t.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
