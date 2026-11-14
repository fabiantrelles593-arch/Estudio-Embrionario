"""H9/H10: semáforo topológico por margen de persistencia y guardia de dominio.

Aplica ``docs/PREREGISTRO_H9_H10.md`` tal como está escrito.

* ``select_set`` elige, por validación cruzada dejando una forma fuera, UN
  conjunto de variables para todos los estratos entre T1 (profundidad global,
  la línea de base), T4 (márgenes de persistencia + acuerdo entre escalas) y
  T7 (los dos).
* ``freeze`` ajusta los modelos finales por estrato y las envolventes de dominio
  (sobre las filas de calibración que reciben luz verde) y devuelve un
  diccionario serializable, que se confirma en git ANTES de los barridos de
  confirmación.
* ``evaluate_*`` no reajustan nada.

Reglas heredadas: un valor no calculable es «no evaluable», nunca «no apoyada»;
una variable no medible da p = 0 (luz roja); fuera de la envolvente no hay luz
verde.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import h6
from .analysis import auc_score, fit_logit_multi, predict_logit_multi, wilson_interval
from .budget import FROZEN_H6, GREEN, RED
from .domain import fit_envelopes, in_domain_column
from .h3 import PREREGISTERED_SEGMENTERS, PROFILES, grade

TOPO_SETS: dict[str, tuple[str, ...]] = {
    "T1": ("ln_d",),
    "T4": ("tau_dil", "tau_ero", "m_lo", "m_hi", "a1", "a2"),
    "T7": ("ln_d", "tau_dil", "tau_ero", "m_lo", "m_hi", "a1", "a2"),
}
SCALE_FEATURES = ("a1", "a2")
RIDGE = 1.0
MIN_GREEN = 200          # filas en verde para evaluar un estrato en dominio (como H6)
MIN_GREEN_SMALL = 100    # ídem en los conjuntos pequeños (formas nuevas, dominio desplazado)
MIN_ENVELOPE_ROWS = 50   # filas verdes de calibración para poder ajustar una envolvente
FALSE_GREEN_MAX = 0.10
AUC_MIN = 0.85
ECE_MAX = 0.10
RETAIN_MIN = 0.90
DECLARED_FOR_SHIFT = "realistic"


def without_scale(features) -> tuple[str, ...]:
    return tuple(f for f in features if f not in SCALE_FEATURES)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = h6.add_features(df)
    out["t_ok"] = out["topology_ok"].astype(bool).astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out["ln_d"] = np.log(out["d_over_hgeo"].where(out["d_over_hgeo"] > 0))
    return out


def _prepared(df: pd.DataFrame) -> pd.DataFrame:
    return df if "ln_d" in df.columns else add_features(df)


def fit_set(df: pd.DataFrame, features, response: str = "t_ok") -> dict:
    X = df[list(features)].to_numpy(float)
    ok = np.isfinite(X).all(axis=1)
    return fit_logit_multi(X[ok], df[response].to_numpy(float)[ok], ridge=RIDGE,
                           features=features)


def predict_set(model: dict, df: pd.DataFrame) -> np.ndarray:
    X = df[model["features"]].to_numpy(float)
    ok = np.isfinite(X).all(axis=1)
    p = np.zeros(len(df))
    if ok.any():
        p[ok] = predict_logit_multi(model, X[ok])
    return p


# --- calibración ------------------------------------------------------------

def loso(df: pd.DataFrame, features) -> pd.DataFrame:
    rows = []
    for (seg, prof), g in df.groupby(["segmenter", "profile"]):
        for shape in sorted(g["shape"].unique()):
            train, test = g[g["shape"] != shape], g[g["shape"] == shape]
            p = predict_set(fit_set(train, features), test)
            rows.append({"segmenter": seg, "profile": prof, "left_out": shape,
                         "logloss": h6.logloss_p(p, test["t_ok"].to_numpy())})
    return pd.DataFrame(rows)


def select_set(df: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    """Menor entropía cruzada media (estratos × formas); a igualdad, menos variables."""
    df = _prepared(df)
    rows = []
    for name, feats in TOPO_SETS.items():
        t = loso(df, feats)
        rows.append({"set": name, "n_features": len(feats),
                     "mean_logloss": float(t["logloss"].mean()), "n_folds": int(len(t))})
    tab = pd.DataFrame(rows)
    best = tab.sort_values(["mean_logloss", "n_features"]).iloc[0]["set"]
    return str(best), tab


def p_volume(df: pd.DataFrame, declared: str | None = None, models: dict | None = None) -> np.ndarray:
    """Semáforo de volumen, con el perfil real o uno declarado. Sin ``models`` usa los congelados
    en H6; v0.5 (H12) pasa los recalibrados para ecografía simulada."""
    models = FROZEN_H6["models"] if models is None else models
    df = _prepared(df)
    out = np.zeros(len(df))
    prof = df["profile"] if declared is None else pd.Series(declared, index=df.index)
    for (seg, p), idx in df.groupby([df["segmenter"], prof]).groups.items():
        pos = df.index.get_indexer(idx)
        out[pos] = h6.predict_p(df["d_over_hgeo"].to_numpy(float)[pos], models[f"{seg}|{p}"])
    return out


def p_topology(df: pd.DataFrame, frozen: dict, which: str = "main",
               declared: str | None = None) -> np.ndarray:
    df = _prepared(df)
    out = np.zeros(len(df))
    prof = df["profile"] if declared is None else pd.Series(declared, index=df.index)
    for (seg, p), idx in df.groupby([df["segmenter"], prof]).groups.items():
        pos = df.index.get_indexer(idx)
        out[pos] = predict_set(frozen["models"][f"{seg}|{p}"][which], df.iloc[pos])
    return out


def _guard(df: pd.DataFrame, envelopes: dict, declared: str | None = None) -> np.ndarray:
    usable = {k: v for k, v in envelopes.items() if v is not None}
    return in_domain_column(df, usable, declared)


def freeze(cal_df: pd.DataFrame, volume_models: dict | None = None) -> dict:
    """Congela modelos topológicos y envolventes. ``volume_models`` (opcional) sustituye a los
    modelos de volumen de H6 y se guarda en el congelado (H12)."""
    df = _prepared(cal_df).reset_index(drop=True)
    best, tab = select_set(df)
    feats = TOPO_SETS[best]
    models = {}
    for (seg, prof), g in df.groupby(["segmenter", "profile"]):
        models[f"{seg}|{prof}"] = {"main": fit_set(g, feats),
                                   "baseline": fit_set(g, TOPO_SETS["T1"]),
                                   "no_scale": fit_set(g, without_scale(feats))}
    frozen = {"selected": best, "features": list(feats), "selection": tab.to_dict("records"),
              "models": models, "green": GREEN, "red": RED, "ridge": RIDGE}
    if volume_models is not None:
        frozen["volume_models"] = volume_models
    lights = {"volume": p_volume(df, models=volume_models) >= GREEN,
              "topology": p_topology(df, frozen) >= GREEN}
    envelopes = {}
    for endpoint, green in lights.items():
        env = fit_envelopes(df[green]) if green.any() else {}
        counts = df[green].groupby(["segmenter", "profile"]).size()
        envelopes[endpoint] = {
            key: (env.get(key) if int(counts.get(tuple(key.split("|")), 0)) >= MIN_ENVELOPE_ROWS
                  else None)
            for key in models}
    frozen["envelopes"] = envelopes
    frozen["envelope_rows"] = "filas de calibración con luz verde (p >= 0.90) en cada medida"
    return frozen


# --- métricas ---------------------------------------------------------------

def light_metrics(p, y, green: float = GREEN) -> dict:
    p, y = np.asarray(p, float), np.asarray(y, float)
    sel = p >= green
    n = int(sel.sum())
    out = {"n_green": n, "false_green": math.nan, "fg_lo": math.nan, "fg_hi": math.nan,
           "coverage": float((sel & (y == 1)).sum() / max(int((y == 1).sum()), 1))}
    if n:
        bad = int((y[sel] == 0).sum())
        lo, hi = wilson_interval(bad, n)
        out.update(false_green=bad / n, fg_lo=lo, fg_hi=hi)
    return out


def _strata(df: pd.DataFrame):
    for seg in PREREGISTERED_SEGMENTERS:
        for prof in sorted(df["profile"].unique(), key=lambda v: (v not in PROFILES, v)):
            g = df[(df["segmenter"] == seg) & (df["profile"] == prof)]
            if len(g):
                yield seg, prof, g


def evaluate_in_domain(df: pd.DataFrame, frozen: dict) -> dict:
    """Confirmación con las formas de la calibración y semilla nueva: H9b-e, H10c, H10d."""
    df = _prepared(df).reset_index(drop=True)
    pt = p_topology(df, frozen)
    pb = p_topology(df, frozen, "baseline")
    pn = p_topology(df, frozen, "no_scale")
    pv = p_volume(df, models=frozen.get("volume_models"))
    dom_t = _guard(df, frozen["envelopes"]["topology"])
    dom_v = _guard(df, frozen["envelopes"]["volume"])
    rows = []
    for seg, prof, g in _strata(df):
        i = g.index.to_numpy()
        y = g["t_ok"].to_numpy(float)
        m = light_metrics(pt[i], y)
        gt, gv = pt[i] >= GREEN, pv[i] >= GREEN
        row = {"stratum": f"{seg}|{prof}", "n": int(len(g)), "p_ok": float(y.mean()),
               "auc": auc_score(pt[i], y), "ece": h6.ece_p(pt[i], y),
               "logloss": h6.logloss_p(pt[i], y),
               "auc_baseline": auc_score(pb[i], y), "logloss_baseline": h6.logloss_p(pb[i], y),
               "false_green_baseline": light_metrics(pb[i], y)["false_green"],
               "n_green_baseline": light_metrics(pb[i], y)["n_green"],
               "coverage_baseline": light_metrics(pb[i], y)["coverage"],
               "logloss_no_scale": h6.logloss_p(pn[i], y), **m,
               "retained_topology": float((gt & dom_t[i]).sum() / gt.sum()) if gt.any() else math.nan,
               "retained_volume": float((gv & dom_v[i]).sum() / gv.sum()) if gv.any() else math.nan}
        row["evaluable"] = bool(m["n_green"] >= MIN_GREEN)
        row["h9b_auc"] = bool(row["auc"] >= AUC_MIN)
        row["h9c_ece"] = bool(row["ece"] <= ECE_MAX)
        row["h9d_ok"] = bool(row["evaluable"] and m["false_green"] <= FALSE_GREEN_MAX)
        row["h9e_better"] = bool(row["logloss"] < row["logloss_baseline"])
        row["h10d_scale_helps"] = bool(row["logloss"] < row["logloss_no_scale"])
        rows.append(row)
    n = len(rows)
    ev = [r for r in rows if r["evaluable"]]
    d_fail = sum(not r["h9d_ok"] for r in ev)
    b, c = sum(r["h9b_auc"] for r in rows), sum(r["h9c_ece"] for r in rows)
    e, s = sum(r["h9e_better"] for r in rows), sum(r["h10d_scale_helps"] for r in rows)
    retained = [v for r in rows for v in (r["retained_topology"], r["retained_volume"])
                if math.isfinite(v)]
    keep_fail = sum(v < RETAIN_MIN for v in retained)
    scale_used = any(f in SCALE_FEATURES for f in frozen["features"])
    return {
        "strata": rows,
        "h9b": {"count": b, "n": n, "verdict": grade(b, n, 5, 4)},
        "h9c": {"count": c, "n": n, "verdict": grade(c, n, 5, 4)},
        "h9d": {"failing": d_fail, "evaluable": len(ev), "n": n,
                "verdict": "no evaluable" if not ev else ("apoyada" if d_fail == 0 else "no apoyada")},
        "h9e": {"count": e, "n": n, "verdict": grade(e, n, 5, 4)},
        "h10c": {"failing": keep_fail, "evaluated": len(retained),
                 "min_retained": min(retained) if retained else math.nan,
                 "verdict": "no evaluable" if not retained
                 else ("apoyada" if keep_fail == 0 else "no apoyada")},
        "h10d": {"count": s, "n": n,
                 "verdict": grade(s, n, 4, 3) if scale_used else "no evaluable"},
    }


def evaluate_unseen(df: pd.DataFrame, frozen: dict) -> dict:
    """Formas que la calibración nunca vio (mancuerna y copa): H9f."""
    df = _prepared(df).reset_index(drop=True)
    pt, pb = p_topology(df, frozen), p_topology(df, frozen, "baseline")
    rows, by_shape = [], []
    for seg, prof, g in _strata(df):
        i = g.index.to_numpy()
        y = g["t_ok"].to_numpy(float)
        m = light_metrics(pt[i], y)
        mb = light_metrics(pb[i], y)
        row = {"stratum": f"{seg}|{prof}", "n": int(len(g)), "p_ok": float(y.mean()),
               "auc": auc_score(pt[i], y), "auc_baseline": auc_score(pb[i], y), **m,
               "false_green_baseline": mb["false_green"], "n_green_baseline": mb["n_green"]}
        row["evaluable"] = bool(m["n_green"] >= MIN_GREEN_SMALL)
        row["h9f_ok"] = bool(row["evaluable"] and m["false_green"] <= FALSE_GREEN_MAX)
        rows.append(row)
        for shape, s in g.groupby("shape"):
            j = s.index.to_numpy()
            by_shape.append({"stratum": row["stratum"], "shape": shape, "p_ok": float(s["t_ok"].mean()),
                             **{k: v for k, v in light_metrics(pt[j], s["t_ok"].to_numpy(float)).items()
                                if k in ("n_green", "false_green", "coverage")},
                             "false_green_baseline":
                                 light_metrics(pb[j], s["t_ok"].to_numpy(float))["false_green"]})
    ev = [r for r in rows if r["evaluable"]]
    fail = sum(not r["h9f_ok"] for r in ev)
    return {"strata": rows, "by_shape": by_shape,
            "h9f": {"failing": fail, "evaluable": len(ev), "n": len(rows),
                    "verdict": "no evaluable" if not ev else ("apoyada" if fail == 0 else "no apoyada")}}


def evaluate_shift(df: pd.DataFrame, frozen: dict, declared: str = DECLARED_FOR_SHIFT) -> dict:
    """Perfiles de imagen que la calibración nunca vio, declarados como ``realistic``:
    H9g (topología sin guardia), H10a (el semáforo de volumen se rompe) y H10b (la
    guardia lo impide)."""
    df = _prepared(df).reset_index(drop=True)
    pt = p_topology(df, frozen, declared=declared)
    pb = p_topology(df, frozen, "baseline", declared=declared)
    pv = p_volume(df, declared=declared, models=frozen.get("volume_models"))
    dom_t = _guard(df, frozen["envelopes"]["topology"], declared)
    dom_v = _guard(df, frozen["envelopes"]["volume"], declared)
    rows = []
    for seg, prof, g in _strata(df):
        i = g.index.to_numpy()
        yt, yv = g["t_ok"].to_numpy(float), g["v_ok"].to_numpy(float)
        mt, mb, mv = light_metrics(pt[i], yt), light_metrics(pb[i], yt), light_metrics(pv[i], yv)
        mtg = light_metrics(np.where(dom_t[i], pt[i], 0.0), yt)
        mvg = light_metrics(np.where(dom_v[i], pv[i], 0.0), yv)
        rows.append({
            "stratum": f"{seg}|{prof}", "n": int(len(g)), "t_ok": float(yt.mean()),
            "v_ok": float(yv.mean()),
            "in_domain_topology": float(dom_t[i].mean()), "in_domain_volume": float(dom_v[i].mean()),
            "n_green_topology": mt["n_green"], "false_green_topology": mt["false_green"],
            "n_green_topology_baseline": mb["n_green"],
            "false_green_topology_baseline": mb["false_green"],
            "n_green_topology_guard": mtg["n_green"], "false_green_topology_guard": mtg["false_green"],
            "n_green_volume": mv["n_green"], "false_green_volume": mv["false_green"],
            "n_green_volume_guard": mvg["n_green"], "false_green_volume_guard": mvg["false_green"]})
    # H9g: topología sin guardia
    ev_t = [r for r in rows if r["n_green_topology"] >= MIN_GREEN_SMALL]
    g_fail = sum(r["false_green_topology"] > FALSE_GREEN_MAX for r in ev_t)
    ev_b = [r for r in rows if r["n_green_topology_baseline"] >= MIN_GREEN_SMALL]
    base_fail = sum(r["false_green_topology_baseline"] > FALSE_GREEN_MAX for r in ev_b)
    # H10a: el semáforo de volumen sin guardia
    ev_v = [r for r in rows if r["n_green_volume"] >= MIN_GREEN_SMALL]
    a_cnt = sum(r["false_green_volume"] > FALSE_GREEN_MAX for r in ev_v)
    # H10b: con guardia, los estratos con verdes suficientes deben ser seguros; el resto se rechaza
    ev_g = [r for r in rows if r["n_green_volume_guard"] >= MIN_GREEN_SMALL]
    b_fail = sum(r["false_green_volume_guard"] > FALSE_GREEN_MAX for r in ev_g)
    rejected = len(rows) - len(ev_g)
    if not rows:
        vb = "no evaluable"
    elif b_fail:
        vb = "no apoyada"
    else:
        vb = "apoyada"
    return {
        "strata": rows, "declared": declared,
        "h9g": {"failing": g_fail, "evaluable": len(ev_t), "n": len(rows),
                "baseline_failing": base_fail, "baseline_evaluable": len(ev_b),
                "verdict": "no evaluable" if not ev_t else ("apoyada" if g_fail == 0 else "no apoyada")},
        "h10a": {"count": a_cnt, "evaluable": len(ev_v), "n": len(rows),
                 "verdict": "no evaluable" if not ev_v else ("apoyada" if a_cnt >= 3 else "no apoyada")},
        "h10b": {"failing": b_fail, "with_greens": len(ev_g), "rejected": rejected, "n": len(rows),
                 "verdict": vb},
    }


def silent_failures(df: pd.DataFrame, frozen: dict) -> pd.DataFrame:
    """De las medidas con topología INCORRECTA, qué luz recibieron, por resolución."""
    df = _prepared(df).reset_index(drop=True)
    pt = p_topology(df, frozen)
    f = df.assign(p=pt)[df["t_ok"] == 0]
    rows = []
    for lvl, g in f.groupby("t_over_h"):
        rows.append({"t_over_h": lvl, "n_failures": int(len(g)),
                     "green": float((g["p"] >= GREEN).mean()),
                     "yellow": float(((g["p"] >= RED) & (g["p"] < GREEN)).mean()),
                     "red": float((g["p"] < RED).mean())})
    return pd.DataFrame(rows)
