"""Piloto de H9/H10 (semilla 20261122, NO usada en calibración ni confirmación).

Sirve para (1) medir el coste por réplica, (2) ver cómo se comportan los
observables y (3) escribir las predicciones del preregistro con números citados.
Nada de lo que imprime cuenta como resultado.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from geovida import h6
from geovida.analysis import auc_score, fit_logit_multi, predict_logit_multi
from geovida.budget import FROZEN_H6, GREEN

RAW = Path("results/raw")
SEGS = ("global", "otsu", "smoothed_otsu")


def load(name):
    p = RAW / f"h9_{name}.csv.gz"
    if not p.exists():
        return None
    df = h6.add_features(pd.read_csv(p))
    df["t_ok"] = df["topology_ok"].astype(float)
    df["ln_d"] = np.log(df["d_over_hgeo"])
    return df


FEATS = {"T1 ln(d/h)": ["ln_d"],
         "T2 geom": ["tau_dil", "tau_ero"],
         "T3 geom+int": ["tau_dil", "tau_ero", "m_lo", "m_hi"],
         "T4 geom+int+esc": ["tau_dil", "tau_ero", "m_lo", "m_hi", "a1", "a2"]}


def logloss(p, y, floor=1e-3):
    p = np.clip(p, floor, 1 - floor)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def predict(model, g, cols):
    X = g[cols].to_numpy(float)
    ok = np.isfinite(X).all(axis=1)
    p = np.zeros(len(g))
    if ok.any():
        p[ok] = predict_logit_multi(model, X[ok])
    return p


def fit(g, cols):
    X = g[cols].to_numpy(float)
    ok = np.isfinite(X).all(axis=1)
    return fit_logit_multi(X[ok], g["t_ok"].to_numpy(float)[ok], features=cols)


def main():
    cal = load("pilot")
    for name in ("pilot", "pilot_unseen", "pilot_shift"):
        m = Path(f"results/summary/h9_{name}_manifest.json")
        if m.exists():
            j = json.loads(m.read_text())
            print(f"{name}: {j['elapsed_s']} s, {j['reps']} réplicas, {j['rows']} filas")
    if cal is None:
        sys.exit("falta el piloto")
    print("\nTasa de topología correcta y de V_ok por estrato:")
    print(cal.groupby(["segmenter", "profile"])[["t_ok", "v_ok"]].mean().round(3).to_string())

    print("\nLOSO (una forma fuera), entropía cruzada media por conjunto de variables:")
    rows = []
    for (seg, prof), g in cal.groupby(["segmenter", "profile"]):
        for name, cols in FEATS.items():
            ll, aucs = [], []
            for shape in sorted(g["shape"].unique()):
                tr, te = g[g["shape"] != shape], g[g["shape"] == shape]
                p = predict(fit(tr, cols), te, cols)
                ll.append(logloss(p, te["t_ok"].to_numpy()))
            p_all = predict(fit(g, cols), g, cols)
            rows.append({"stratum": f"{seg}|{prof}", "set": name, "loso_logloss": np.mean(ll),
                         "auc_in_sample": auc_score(p_all, g["t_ok"].to_numpy())})
    tab = pd.DataFrame(rows)
    print(tab.pivot(index="stratum", columns="set", values="loso_logloss").round(3).to_string())
    print(tab.groupby("set")["loso_logloss"].mean().round(4).to_string())
    print(tab.pivot(index="stratum", columns="set", values="auc_in_sample").round(3).to_string())

    print("\nEje de escala: V_ok según la deriva u_v1 (todas las filas del piloto):")
    cal["u_bin"] = pd.cut(cal["u_v1"].fillna(9), [-1, 0.02, 0.05, 0.10, 0.20, 0.5, 10])
    print(cal.groupby("u_bin", observed=True)["v_ok"].agg(["mean", "size"]).round(3).to_string())
    for delta in (0.02, 0.03, 0.05, 0.08, 0.10):
        sel = cal["u_v1"] <= delta
        byst = cal[sel].groupby(["segmenter", "profile"])["v_ok"].agg(["mean", "size"])
        print(f"delta={delta}: verde {sel.mean():.3f}, acierto {cal.loc[sel, 'v_ok'].mean():.3f}, "
              f"peor estrato {byst['mean'].min():.3f}")

    for name in ("pilot_unseen", "pilot_shift"):
        df = load(name)
        if df is None:
            continue
        print(f"\n=== {name} ===")
        print(df.groupby(["segmenter", "profile"])[["t_ok", "v_ok"]].mean().round(3).to_string())
        for (seg, prof), g in df.groupby(["segmenter", "profile"]):
            declared = prof if prof in ("ideal", "realistic") else "realistic"
            base = cal[(cal.segmenter == seg) & (cal.profile == declared)]
            out = {}
            for nm, cols in FEATS.items():
                p = predict(fit(base, cols), g, cols)
                green = p >= GREEN
                out[nm] = (auc_score(p, g["t_ok"].to_numpy()), int(green.sum()),
                           float((g["t_ok"].to_numpy()[green] == 0).mean()) if green.any() else np.nan)
            pv = h6.predict_p(g["d_over_hgeo"], FROZEN_H6["models"][f"{seg}|{declared}"])
            gv = pv >= GREEN
            y = g["v_ok"].to_numpy()
            both = gv & (g["u_v1"].to_numpy() <= 0.05)
            fg = lambda s: float((y[s] == 0).mean()) if s.any() else np.nan
            print(f"{seg}|{prof}: topo " + "; ".join(f"{k}: auc {v[0]:.3f} verdes {v[1]} vf {v[2]:.3f}"
                                                  for k, v in out.items()))
            print(f"    volumen: semáforo H6 verdes {int(gv.sum())} vf {fg(gv):.3f} | "
                  f"+escala(0.05) verdes {int(both.sum())} vf {fg(both):.3f}")
        if name == "pilot_unseen":
            print(df.groupby(["shape", "segmenter", "profile", "t_over_h"])["t_ok"].mean()
                  .unstack().round(2).to_string())


if __name__ == "__main__":
    main()
