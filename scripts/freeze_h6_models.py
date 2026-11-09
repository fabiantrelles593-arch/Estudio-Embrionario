"""Congela los modelos del semáforo (H6) con los datos de H3. Antes del barrido H6.

Ajusta, por estrato (segmentador x perfil, los 3 preregistrados), Pr(|err V| <= 5 %)
como logit de ln(Q_hat/h_geo), con Q_hat medido sobre la máscara (V contado,
S = area_sdf). Las filas con Q_hat no medible no entran en el ajuste: en la
evaluación reciben p = 0 (luz roja). Guarda el hash de los datos usados.
"""
import hashlib
import json
from pathlib import Path

import pandas as pd

from geovida.analysis import fit_frozen_logit
from geovida.budget import add_measured_q

RAW = Path("results/raw/h3_sweep.csv.gz")
OUT = Path("results/summary/h6_frozen_models.json")
SEGMENTERS = ("global", "otsu", "smoothed_otsu")


def main():
    df = add_measured_q(pd.read_csv(RAW))
    df = df[df["segmenter"].isin(SEGMENTERS)]
    df["v_ok"] = (df["err_volume"].abs() <= 0.05).astype(float)
    models = {}
    for (seg, prof), g in df.groupby(["segmenter", "profile"]):
        fit = g[g["q_hat_over_hgeo"].notna()]
        m = fit_frozen_logit(fit["q_hat_over_hgeo"], fit["v_ok"])
        models[f"{seg}|{prof}"] = {**m, "n_fit": int(len(fit)), "n_unmeasurable": int(len(g) - len(fit))}
    payload = {"source": str(RAW), "sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
               "endpoint": "|err_volume| <= 0.05", "feature": "ln(Q_hat/h_geo), Q_hat = V/area_sdf",
               "models": models}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True))
    for k, v in models.items():
        print(f"{k:26s} a={v['intercept']:.3f} b={v['slope']:.3f} n={v['n_fit']} sin_medir={v['n_unmeasurable']}")


if __name__ == "__main__":
    main()
