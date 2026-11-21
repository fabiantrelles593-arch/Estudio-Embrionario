"""Calibración y veredictos del semáforo H6 (``docs/PREREGISTRO_H6.md``, tal como está escrito).

Regla central: un valor no calculable es «no evaluable», nunca «no apoyada».
Una variable no medible (máscara vacía, área o profundidad <= 0) recibe p = 0
(luz roja); solo para la entropía cruzada la probabilidad se recorta a
[P_FLOOR, 1 - P_FLOOR] (aclaración del 2026-11-09, ver «Desviaciones»).
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .analysis import auc_score, fit_frozen_logit, predict_frozen, wilson_interval
from .budget import GREEN, RED, add_measured_q
from .h3 import PREREGISTERED_SEGMENTERS, PROFILES, V_TOL, grade

FEATURES = {"F1": "q_hat_over_hgeo", "F2": "d_over_hgeo"}
P_FLOOR = 1e-3
MIN_GREEN = 200            # filas en verde para que un estrato sea evaluable en H6a/H6d
FALSE_GREEN_MAX = 0.10
AUC_MIN = 0.85
ECE_MAX = 0.10


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Añade F1, F2 y la respuesta ``v_ok``; las variables no medibles quedan en NaN."""
    out = add_measured_q(df)
    h = (1.0 / out["t_over_h"]) * out["anisotropy"] ** (1.0 / 3.0)
    out["d_over_hgeo"] = (out["d_mean"] / h).where(out["d_mean"] > 0)
    out["v_ok"] = (out["err_volume"].abs() <= V_TOL).astype(float)
    return out


def predict_p(x, model: dict) -> np.ndarray:
    """Pr(V_ok); p = 0 donde la variable no es medible (NaN o <= 0)."""
    x = np.asarray(x, dtype=float)
    p = np.zeros_like(x)
    ok = np.isfinite(x) & (x > 0)
    if ok.any():
        p[ok] = predict_frozen(model, x[ok])
    return p


def logloss_p(p, y, floor: float = P_FLOOR) -> float:
    p = np.clip(np.asarray(p, float), floor, 1.0 - floor)
    y = np.asarray(y, float)
    return float(-np.mean(y * np.log(p) + (1.0 - y) * np.log(1.0 - p)))


def ece_p(p, y, bins: int = 10) -> float:
    """Error de calibración esperado: cajas de igual ancho en la probabilidad."""
    p = np.asarray(p, float)
    y = np.asarray(y, float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    err = 0.0
    for k in range(bins):
        sel = idx == k
        if sel.any():
            err += sel.sum() * abs(p[sel].mean() - y[sel].mean())
    return float(err / len(y))


def false_green(p, y, green: float = GREEN) -> dict:
    """Tasa de verde falso: entre las filas con p >= green, la fracción con V_ok = 0."""
    p = np.asarray(p, float)
    y = np.asarray(y, float)
    sel = p >= green
    n = int(sel.sum())
    if n == 0:
        return {"n_green": 0, "false_green": math.nan, "fg_lo": math.nan, "fg_hi": math.nan}
    bad = int((y[sel] == 0).sum())
    lo, hi = wilson_interval(bad, n)
    return {"n_green": n, "false_green": bad / n, "fg_lo": lo, "fg_hi": hi}


def _fit(g: pd.DataFrame, col: str) -> dict:
    ok = g[np.isfinite(g[col]) & (g[col] > 0)]
    return fit_frozen_logit(ok[col], ok["v_ok"])


def loso_logloss(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Validación cruzada dejando una forma fuera, por estrato (segmentador x perfil)."""
    rows = []
    for (seg, prof), g in df.groupby(["segmenter", "profile"]):
        for shape in sorted(g["shape"].unique()):
            train, test = g[g["shape"] != shape], g[g["shape"] == shape]
            p = predict_p(test[col], _fit(train, col))
            rows.append({"segmenter": seg, "profile": prof, "left_out": shape,
                         "logloss": logloss_p(p, test["v_ok"].to_numpy())})
    return pd.DataFrame(rows)


def select_feature(df: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    """Elige F1 o F2 por la menor entropía cruzada media (6 estratos x 10 formas)."""
    summary = []
    for name, col in FEATURES.items():
        t = loso_logloss(df, col)
        summary.append({"feature": name, "column": col, "mean_logloss": float(t["logloss"].mean()),
                        "n_folds": int(len(t))})
    tab = pd.DataFrame(summary)
    best = tab.sort_values("mean_logloss").iloc[0]["feature"]
    return str(best), tab


def freeze_models(df: pd.DataFrame, col: str) -> dict:
    """Ajuste final por estrato con todas las formas de la calibración."""
    models = {}
    for (seg, prof), g in df.groupby(["segmenter", "profile"]):
        m = _fit(g, col)
        m["n"] = int(len(g))
        models[f"{seg}|{prof}"] = m
    return models


def evaluate_h6(df: pd.DataFrame, frozen: dict, naive: dict, col: str) -> dict:
    """Veredictos H6a-H6e sobre el barrido de confirmación (nada se reajusta)."""
    rows = []
    for seg in PREREGISTERED_SEGMENTERS:
        for prof in PROFILES:
            key = f"{seg}|{prof}"
            g = df[(df["segmenter"] == seg) & (df["profile"] == prof)]
            y = g["v_ok"].to_numpy(float)
            p = predict_p(g[col], frozen[key])
            pa = predict_p(g["q_hat_over_hgeo"], naive[key])
            fg, fga = false_green(p, y), false_green(pa, y)
            row = {"stratum": key, "n": int(len(g)), "p_ok": float(y.mean()),
                   "auc": auc_score(p, y), "ece": ece_p(p, y), "logloss": logloss_p(p, y),
                   "auc_naive": auc_score(pa, y), "ece_naive": ece_p(pa, y),
                   "logloss_naive": logloss_p(pa, y),
                   "n_green": fg["n_green"], "false_green": fg["false_green"],
                   "fg_lo": fg["fg_lo"], "fg_hi": fg["fg_hi"],
                   "n_green_naive": fga["n_green"], "false_green_naive": fga["false_green"],
                   "fg_naive_lo": fga["fg_lo"], "fg_naive_hi": fga["fg_hi"]}
            row["evaluable_green"] = bool(fg["n_green"] >= MIN_GREEN)
            row["evaluable_green_naive"] = bool(fga["n_green"] >= MIN_GREEN)
            row["h6b_auc"] = bool(row["auc"] >= AUC_MIN)       # NaN -> False; no hay NaN con 2 clases
            row["h6c_ece"] = bool(row["ece"] <= ECE_MAX)
            row["h6d_ok"] = bool(row["evaluable_green"] and fg["false_green"] <= FALSE_GREEN_MAX)
            row["h6e_better"] = bool(row["logloss"] < row["logloss_naive"])
            row["h6a_naive_over"] = bool(row["evaluable_green_naive"]
                                         and fga["false_green"] > FALSE_GREEN_MAX)
            rows.append(row)
    n = len(rows)
    ev_a = [r for r in rows if r["evaluable_green_naive"]]
    a_cnt = sum(r["h6a_naive_over"] for r in rows)
    ev_d = [r for r in rows if r["evaluable_green"]]
    d_fail = sum(not r["h6d_ok"] for r in ev_d)
    b = sum(r["h6b_auc"] for r in rows)
    c = sum(r["h6c_ece"] for r in rows)
    e = sum(r["h6e_better"] for r in rows)
    return {
        "strata": rows,
        "h6a": {"count": a_cnt, "evaluable": len(ev_a), "n": n,
                "verdict": "no evaluable" if not ev_a else ("apoyada" if a_cnt >= 1 else "no apoyada")},
        "h6b": {"count": b, "n": n, "verdict": grade(b, n, 5, 4)},
        "h6c": {"count": c, "n": n, "verdict": grade(c, n, 5, 4)},
        "h6d": {"failing": d_fail, "evaluable": len(ev_d), "n": n,
                "verdict": "no evaluable" if not ev_d else ("apoyada" if d_fail == 0 else "no apoyada")},
        "h6e": {"count": e, "n": n, "verdict": grade(e, n, 5, 4)},
    }


# ---- extensiones descriptivas (sin veredicto) -------------------------------

def wrong_profile_table(df: pd.DataFrame, frozen: dict, col: str) -> pd.DataFrame:
    """Aplica el modelo del perfil contrario (el usuario declara mal el perfil de imagen)."""
    other = {"ideal": "realistic", "realistic": "ideal"}
    rows = []
    for seg in PREREGISTERED_SEGMENTERS:
        for prof in PROFILES:
            g = df[(df["segmenter"] == seg) & (df["profile"] == prof)]
            y = g["v_ok"].to_numpy(float)
            right = predict_p(g[col], frozen[f"{seg}|{prof}"])
            wrong = predict_p(g[col], frozen[f"{seg}|{other[prof]}"])
            fr, fw = false_green(right, y), false_green(wrong, y)
            rows.append({"segmenter": seg, "profile": prof,
                         "auc_right": auc_score(right, y), "auc_wrong": auc_score(wrong, y),
                         "ece_right": ece_p(right, y), "ece_wrong": ece_p(wrong, y),
                         "n_green_right": fr["n_green"], "fg_right": fr["false_green"],
                         "n_green_wrong": fw["n_green"], "fg_wrong": fw["false_green"]})
    return pd.DataFrame(rows)


def by_shape_table(df: pd.DataFrame, frozen: dict, col: str) -> pd.DataFrame:
    rows = []
    for seg in PREREGISTERED_SEGMENTERS:
        for prof in PROFILES:
            g = df[(df["segmenter"] == seg) & (df["profile"] == prof)]
            p_all = predict_p(g[col], frozen[f"{seg}|{prof}"])
            for shape in sorted(g["shape"].unique()):
                m = (g["shape"] == shape).to_numpy()
                fg = false_green(p_all[m], g.loc[m, "v_ok"].to_numpy(float))
                rows.append({"segmenter": seg, "profile": prof, "shape": shape,
                             "n_green": fg["n_green"], "false_green": fg["false_green"]})
    return pd.DataFrame(rows)


def lights_by_level_table(df: pd.DataFrame, frozen: dict, col: str) -> pd.DataFrame:
    """Por estrato y nivel t/h: reparto de luces y fracción observada de V_ok en cada luz."""
    rows = []
    for seg in PREREGISTERED_SEGMENTERS:
        for prof in PROFILES:
            g = df[(df["segmenter"] == seg) & (df["profile"] == prof)].copy()
            g["p"] = predict_p(g[col], frozen[f"{seg}|{prof}"])
            g["light"] = np.where(g["p"] >= GREEN, "verde", np.where(g["p"] >= RED, "amarillo", "rojo"))
            for lvl, h in g.groupby("t_over_h"):
                for light in ("verde", "amarillo", "rojo"):
                    s = h[h["light"] == light]
                    rows.append({"segmenter": seg, "profile": prof, "t_over_h": lvl,
                                 "light": light, "share": len(s) / len(h),
                                 "p_ok_observed": float(s["v_ok"].mean()) if len(s) else math.nan})
    return pd.DataFrame(rows)
