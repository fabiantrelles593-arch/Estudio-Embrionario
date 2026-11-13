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
    pd.set_option("display.width", 200)
    for g in h16.GUARDS:                                    # EXPLORATORIO (§6 del preregistro): por tipo de curva de tono de la familia B
        t = h16.gamma_strata(b, g)
        t.to_csv(SUMMARY / f"h16_gamma_strata_{g}.csv", index=False)
        print(f"\nEXPLORATORIO, familia B por curva de tono, guardia {g}")
        print(t.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
