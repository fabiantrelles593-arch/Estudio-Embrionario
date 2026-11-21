"""Congela, con los datos de H1, los modelos que H3 evaluará SIN reajustar.

Para cada estrato (segmentador x perfil) se ajusta Pr(|error de V| <= 5 %) como
logit de ln(Q/h_geo) (modelo Q) y de ln(t_solid/h_geo) (modelo de grosor).
Se guarda también el hash de los datos de H1 usados. Debe ejecutarse y
commitearse ANTES de correr el barrido H3.
"""
import hashlib
import json
from pathlib import Path

import pandas as pd

from geovida.analysis import add_predictors, add_vq_predictors, fit_frozen_logit, x_at_probability

RAW = Path("results/raw/h1_sweep.csv.gz")
OUT = Path("results/summary/h3_frozen_models.json")


def main():
    df = add_vq_predictors(add_predictors(pd.read_csv(RAW)))
    df["v_ok"] = (df["err_volume"].abs() <= 0.05).astype(float)
    models = {}
    for (seg, prof), g in df.groupby(["segmenter", "profile"]):
        q = fit_frozen_logit(g["q_over_hgeo"], g["v_ok"])
        t = fit_frozen_logit(g["t_solid_over_hgeo"], g["v_ok"])
        models[f"{seg}|{prof}"] = {
            "n": int(len(g)), "q_model": q, "t_model": t,
            "q_star_095": x_at_probability(q, 0.95),
            "t_star_095": x_at_probability(t, 0.95),
        }
    payload = {
        "source": str(RAW), "sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "endpoint": "|err_volume| <= 0.05", "models": models,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True))
    for k, v in models.items():
        print(f"{k:28s} Q*={v['q_star_095']:.2f}  t*={v['t_star_095']:.2f}  "
              f"q=({v['q_model']['intercept']:.2f},{v['q_model']['slope']:.2f})")


if __name__ == "__main__":
    main()
