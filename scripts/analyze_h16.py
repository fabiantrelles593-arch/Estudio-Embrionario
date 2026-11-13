"""Análisis de H16 con las reglas de docs/PREREGISTRO_H16.md (solo simulación). Un solo análisis, sobre los dos conjuntos de confirmación."""
import json
import warnings
from pathlib import Path

import pandas as pd

from geovida import h16

RAW, SUMMARY = Path("results/raw"), Path("results/summary")


def main():
    warnings.filterwarnings("ignore")
    a, b = pd.read_csv(RAW / "h16_conf_a.csv.gz"), pd.read_csv(RAW / "h16_conf_b.csv.gz")
    v = {"principal_recalibracion": h16.evaluate_h16(a, b, guard="rc"), "secundario_parametrico": h16.evaluate_h16(a, b, guard="cg")}
    (SUMMARY / "h16_verdicts.json").write_text(json.dumps(v, indent=2, default=float))
    print(json.dumps(v, indent=2, default=float))


if __name__ == "__main__":
    main()
