"""H12: certificado recalibrado para ecografía 3D simulada (v0.5). Aplica ``docs/PREREGISTRO_H12.md``.

Qué hace
--------
* ``freeze_us``: con el barrido de calibración de ecografía simulada (moteado, atenuación) ajusta
  los modelos de volumen y de topología y las envolventes de la guardia, y devuelve un diccionario
  serializable con la misma forma que el congelado de v0.4 más ``volume_models`` y ``profiles``.
* ``evaluate_*``: no reajustan nada. Una luz verde **emitida** es la que el certificado daría al
  usuario: probabilidad >= 0.90 **y** dentro de la envolvente de la guardia.

Reglas heredadas: un valor no calculable es «no evaluable», nunca «no apoyada»; los estratos sin
verdes suficientes no se evalúan y se listan, no se esconden.

Qué NO es: una validación con ecografías reales. El simulador de moteado es mínimo (sin compresión
logarítmica, sombras acústicas ni reverberaciones) y sus parámetros son supuestos de diseño.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import h6, h9
from .analysis import auc_score
from .budget import GREEN
from .certificate import LIMITS
from .experiment import US_PROFILES
from .h9 import (AUC_MIN, ECE_MAX, FALSE_GREEN_MAX, MIN_GREEN, MIN_GREEN_SMALL, light_metrics)

MIN_CALIB_ROWS = 200       # filas por estrato para evaluar AUC y ECE
MIN_MINORITY = 0.05        # la clase minoritaria debe ser >= 5 % para que AUC y ECE signifiquen algo
IN_DOMAIN_MAX = 0.50       # H12b: una imagen de otra modalidad entra en el dominio en <= 50 %
US_LIMITS = (
    "Calibrado con ecografía 3D simulada (moteado completamente desarrollado, atenuación en z, "
    "fondo no nulo); no validado con ecografías reales ni con fantomas físicos.",
    "El simulador no incluye compresión logarítmica, sombras acústicas ni reverberaciones.",
    *LIMITS[1:],
)
SUPPORTED_FRACTION = 5 / 6
PARTIAL_FRACTION = 4 / 6


def freeze_us(cal_df: pd.DataFrame) -> dict:
    """Modelos de volumen (logit sobre d/h_geo), modelos topológicos y envolventes de dominio."""
    df = h9.add_features(cal_df).reset_index(drop=True)
    volume_models = h6.freeze_models(df, "d_over_hgeo")
    frozen = h9.freeze(df, volume_models=volume_models)
    present = set(df["profile"].unique())
    frozen["profiles"] = [p for p in US_PROFILES if p in present]
    frozen["limits"] = list(US_LIMITS)
    return frozen


# --- utilidades -----------------------------------------------------------------------------------

def _issued(p: np.ndarray, dom: np.ndarray) -> np.ndarray:
    """p con la guardia aplicada: fuera de la envolvente no hay luz verde."""
    return np.where(dom, p, 0.0)


def _endpoint(prefix: str, p, y, dom, min_green: int) -> dict:
    """Métricas de un extremo (volumen o topología) en un estrato."""
    p, y = np.asarray(p, float), np.asarray(y, float)
    issued = light_metrics(_issued(p, dom), y)
    free = p >= GREEN
    n_free = int(free.sum())
    kept = int((free & dom).sum())
    minority = float(min(y.mean(), 1.0 - y.mean())) if len(y) else 0.0
    calib_ok = bool(len(y) >= MIN_CALIB_ROWS and minority >= MIN_MINORITY)
    auc = auc_score(p, y) if calib_ok else math.nan
    ece = h6.ece_p(p, y) if calib_ok else math.nan
    return {
        f"n_green_{prefix}": issued["n_green"],
        f"false_green_{prefix}": issued["false_green"],
        f"fg_lo_{prefix}": issued["fg_lo"], f"fg_hi_{prefix}": issued["fg_hi"],
        f"coverage_{prefix}": issued["coverage"],
        f"n_green_free_{prefix}": n_free,
        f"retained_{prefix}": kept / n_free if n_free else math.nan,
        f"in_domain_{prefix}": float(dom.mean()) if len(dom) else math.nan,
        f"auc_{prefix}": auc, f"ece_{prefix}": ece,
        f"p_ok_{prefix}": float(y.mean()) if len(y) else math.nan,
        f"calibration_evaluable_{prefix}": calib_ok,
        f"evaluable_{prefix}": bool(issued["n_green"] >= min_green),
    }


def _safe(row: dict, prefix: str) -> bool:
    """El extremo es seguro si no es evaluable o su verde falso emitido es <= 10 %."""
    return (not row[f"evaluable_{prefix}"]) or row[f"false_green_{prefix}"] <= FALSE_GREEN_MAX


def _verdict_all(rows: list[dict], flag) -> tuple[str, int, list[str]]:
    """«apoyada» si todos los estratos con algún extremo evaluable lo cumplen; «no evaluable» si
    ninguno es evaluable. Devuelve (veredicto, nº evaluables, estratos que fallan)."""
    ev = [r for r in rows if r["evaluable_volume"] or r["evaluable_topology"]]
    if not ev:
        return "no evaluable", 0, []
    failing = [r["stratum"] for r in ev if not flag(r)]
    return ("apoyada" if not failing else "no apoyada"), len(ev), failing


def _grade_fraction(passed: int, n: int) -> str:
    if n == 0:
        return "no evaluable"
    f = passed / n
    return "apoyada" if f >= SUPPORTED_FRACTION else ("parcial" if f >= PARTIAL_FRACTION else "no apoyada")


def _volume_topology_rows(df: pd.DataFrame, frozen: dict, declared: str | None, min_green: int,
                          volume_models: dict | None = None):
    """Filas por estrato con las luces emitidas de volumen y topología."""
    df = h9.add_features(df).reset_index(drop=True)
    models = frozen.get("volume_models") if volume_models is None else volume_models
    pv = h9.p_volume(df, declared=declared, models=models)
    pt = h9.p_topology(df, frozen, declared=declared)
    dom_v = h9._guard(df, frozen["envelopes"]["volume"], declared)
    dom_t = h9._guard(df, frozen["envelopes"]["topology"], declared)
    rows = []
    for seg, prof, g in h9._strata(df):
        i = g.index.to_numpy()
        row = {"stratum": f"{seg}|{prof}", "n": int(len(g))}
        row.update(_endpoint("volume", pv[i], g["v_ok"].to_numpy(float), dom_v[i], min_green))
        row.update(_endpoint("topology", pt[i], g["t_ok"].to_numpy(float), dom_t[i], min_green))
        rows.append(row)
    return df, rows, (pv, pt, dom_v, dom_t)


# --- H12c (primaria) y H12d: confirmación con las mismas formas y semilla nueva ---------------------

def evaluate_confirmation(df: pd.DataFrame, frozen: dict) -> dict:
    _, rows, _ = _volume_topology_rows(df, frozen, None, MIN_GREEN)
    verdict, n_ev, failing = _verdict_all(rows, lambda r: _safe(r, "volume") and _safe(r, "topology"))
    pairs, passed = 0, 0
    for r in rows:
        for pre in ("volume", "topology"):
            if r[f"calibration_evaluable_{pre}"]:
                pairs += 1
                passed += int(r[f"auc_{pre}"] >= AUC_MIN and r[f"ece_{pre}"] <= ECE_MAX)
    retained = [v for r in rows for v in (r["retained_volume"], r["retained_topology"])
                if math.isfinite(v)]
    return {
        "strata": rows,
        "h12c": {"verdict": verdict, "evaluable_strata": n_ev, "n": len(rows), "failing": failing,
                 "not_evaluable": [r["stratum"] for r in rows
                                   if not (r["evaluable_volume"] or r["evaluable_topology"])]},
        "h12d": {"verdict": _grade_fraction(passed, pairs), "passed": passed, "pairs": pairs},
        "retained_min": min(retained) if retained else math.nan,
    }


# --- H12e: formas que la calibración nunca vio -------------------------------------------------------

def evaluate_unseen(df: pd.DataFrame, frozen: dict) -> dict:
    d, rows, (pv, pt, dom_v, dom_t) = _volume_topology_rows(df, frozen, None, MIN_GREEN_SMALL)
    verdict, n_ev, failing = _verdict_all(rows, lambda r: _safe(r, "volume") and _safe(r, "topology"))
    by_shape = []
    for seg, prof, g in h9._strata(d):
        for shape, s in g.groupby("shape"):
            j = s.index.to_numpy()
            mv = light_metrics(_issued(pv[j], dom_v[j]), s["v_ok"].to_numpy(float))
            mt = light_metrics(_issued(pt[j], dom_t[j]), s["t_ok"].to_numpy(float))
            by_shape.append({"stratum": f"{seg}|{prof}", "shape": shape,
                             "n_green_volume": mv["n_green"], "false_green_volume": mv["false_green"],
                             "n_green_topology": mt["n_green"],
                             "false_green_topology": mt["false_green"]})
    return {"strata": rows, "by_shape": by_shape,
            "h12e": {"verdict": verdict, "evaluable_strata": n_ev, "n": len(rows), "failing": failing}}


# --- H12f y H12g: perfiles de ecografía que la calibración nunca vio ----------------------------------

def evaluate_shift(df: pd.DataFrame, frozen: dict, declared: str = "us_compound") -> dict:
    """Se declara ``declared`` aunque la imagen sea de otro perfil (el usuario no conoce el suyo).

    H12f: con guardia, los estratos con >= 100 verdes emitidos tienen verde falso <= 10 %.
    H12g: sin guardia, el semáforo de volumen supera 10 % de verde falso en al menos la mitad de
    los estratos evaluables (>= 100 verdes) y al menos en uno: la guardia hace falta."""
    d = h9.add_features(df).reset_index(drop=True)
    raw = h9.evaluate_shift(d, frozen, declared=declared)
    rows = raw["strata"]
    guarded = [r for r in rows if r["n_green_volume_guard"] >= MIN_GREEN_SMALL
               or r["n_green_topology_guard"] >= MIN_GREEN_SMALL]
    f_fail = [r["stratum"] for r in guarded
              if (r["n_green_volume_guard"] >= MIN_GREEN_SMALL
                  and r["false_green_volume_guard"] > FALSE_GREEN_MAX)
              or (r["n_green_topology_guard"] >= MIN_GREEN_SMALL
                  and r["false_green_topology_guard"] > FALSE_GREEN_MAX)]
    vf = "no evaluable" if not rows else ("no apoyada" if f_fail else "apoyada")
    ev = [r for r in rows if r["n_green_volume"] >= MIN_GREEN_SMALL]
    broken = [r["stratum"] for r in ev if r["false_green_volume"] > FALSE_GREEN_MAX]
    vg = ("no evaluable" if not ev else
          ("apoyada" if broken and len(broken) >= math.ceil(len(ev) / 2) else "no apoyada"))
    return {
        "strata": rows, "declared": declared,
        "h12f": {"verdict": vf, "strata_with_greens": len(guarded),
                 "rejected_or_without_greens": len(rows) - len(guarded), "n": len(rows),
                 "failing": f_fail},
        "h12g": {"verdict": vg, "breaking": len(broken), "evaluable": len(ev), "n": len(rows),
                 "strata": broken},
    }


# --- H12a y H12b (v0.4 sobre ecografía; la guardia entre modalidades) -------------------------------

def evaluate_baseline(df: pd.DataFrame, frozen_v04: dict, declared: str = "realistic") -> dict:
    """El certificado de v0.4, declarado ``realistic``, sobre imágenes de ecografía simulada.

    H12a: sin guardia, el semáforo de volumen de v0.4 da verde falso > 10 % en al menos la mitad
    de los estratos evaluables (>= 100 verdes) y al menos en uno."""
    d = h9.add_features(df).reset_index(drop=True)
    pv = h9.p_volume(d, declared=declared)
    pt = h9.p_topology(d, frozen_v04, declared=declared)
    dom_v = h9._guard(d, frozen_v04["envelopes"]["volume"], declared)
    dom_t = h9._guard(d, frozen_v04["envelopes"]["topology"], declared)
    rows = []
    for seg, prof, g in h9._strata(d):
        i = g.index.to_numpy()
        yv, yt = g["v_ok"].to_numpy(float), g["t_ok"].to_numpy(float)
        mv, mt = light_metrics(pv[i], yv), light_metrics(pt[i], yt)
        mvg = light_metrics(_issued(pv[i], dom_v[i]), yv)
        mtg = light_metrics(_issued(pt[i], dom_t[i]), yt)
        rows.append({"stratum": f"{seg}|{prof}", "n": int(len(g)), "v_ok": float(yv.mean()),
                     "t_ok": float(yt.mean()),
                     "in_domain_volume": float(dom_v[i].mean()), "in_domain_topology": float(dom_t[i].mean()),
                     "n_green_volume": mv["n_green"], "false_green_volume": mv["false_green"],
                     "n_green_volume_guard": mvg["n_green"], "false_green_volume_guard": mvg["false_green"],
                     "n_green_topology": mt["n_green"], "false_green_topology": mt["false_green"],
                     "n_green_topology_guard": mtg["n_green"],
                     "false_green_topology_guard": mtg["false_green"]})
    ev = [r for r in rows if r["n_green_volume"] >= MIN_GREEN_SMALL]
    broken = [r["stratum"] for r in ev if r["false_green_volume"] > FALSE_GREEN_MAX]
    verdict = ("no evaluable" if not ev else
               ("apoyada" if broken and len(broken) >= math.ceil(len(ev) / 2) else "no apoyada"))
    share = {}
    for seg in sorted(set(d["segmenter"])):
        m = (d["segmenter"] == seg).to_numpy()
        share[seg] = float(dom_v[m].mean()) if m.any() else math.nan
    return {"strata": rows, "declared": declared, "in_domain_by_segmenter": share,
            "h12a": {"verdict": verdict, "breaking": len(broken), "evaluable": len(ev), "n": len(rows),
                     "strata": broken}}


def _share(df: pd.DataFrame, envelopes: dict, declared: str, seg: str) -> tuple[int, float]:
    sub = df[df["segmenter"] == seg].reset_index(drop=True)
    if not len(sub):
        return 0, math.nan
    return int(len(sub)), float(h9._guard(sub, envelopes, declared).mean())


def evaluate_modality(old_df: pd.DataFrame, us_df: pd.DataFrame, frozen_us: dict,
                      frozen_v04: dict) -> dict:
    """H12b: la guardia distingue las dos modalidades en ambos sentidos.

    (i) imágenes de ecografía simulada frente a la envolvente de v0.4 (declarado ``realistic``);
    (ii) imágenes de ruido gaussiano (``realistic``) frente a la envolvente recalibrada, declarando
    cada perfil de ecografía. Cada comprobación pasa si entra en el dominio <= 50 %."""
    checks = []
    env_v04 = frozen_v04["envelopes"]["volume"]
    env_us = frozen_us["envelopes"]["volume"]
    for seg in h9.PREREGISTERED_SEGMENTERS:
        n, s = _share(us_df, env_v04, "realistic", seg)
        checks.append({"direction": "us_vs_v04_guard", "segmenter": seg, "declared": "realistic",
                       "n": n, "in_domain": s, "ok": bool(n and s <= IN_DOMAIN_MAX)})
    realistic = old_df[old_df["profile"] == "realistic"]
    for seg in h9.PREREGISTERED_SEGMENTERS:
        for prof in frozen_us["profiles"]:
            n, s = _share(realistic, env_us, prof, seg)
            checks.append({"direction": "realistic_vs_us_guard", "segmenter": seg, "declared": prof,
                           "n": n, "in_domain": s, "ok": bool(n and s <= IN_DOMAIN_MAX)})
    valid = [c for c in checks if c["n"]]
    passed = sum(c["ok"] for c in valid)
    if not valid:
        verdict = "no evaluable"
    elif passed == len(valid):
        verdict = "apoyada"
    else:
        verdict = "parcial" if passed / len(valid) >= 0.75 else "no apoyada"
    return {"checks": checks, "h12b": {"verdict": verdict, "passed": passed, "checks": len(valid)}}


# --- H12h: ¿paga recalibrar? --------------------------------------------------------------------------

def evaluate_benefit(df: pd.DataFrame, frozen_us: dict, frozen_v04: dict) -> dict:
    """Entre las medidas correctas (|error de volumen| <= 5 %), la fracción que recibe luz verde
    emitida (con guardia): certificado recalibrado frente al de v0.4 declarado ``realistic``.
    Apoyada si, en todos los estratos donde el recalibrado es evaluable (>= 200 verdes), cubre más."""
    d = h9.add_features(df).reset_index(drop=True)
    p_us = h9.p_volume(d, models=frozen_us["volume_models"])
    dom_us = h9._guard(d, frozen_us["envelopes"]["volume"])
    p_old = h9.p_volume(d, declared="realistic")
    dom_old = h9._guard(d, frozen_v04["envelopes"]["volume"], "realistic")
    rows = []
    for seg, prof, g in h9._strata(d):
        i = g.index.to_numpy()
        y = g["v_ok"].to_numpy(float)
        mu = light_metrics(_issued(p_us[i], dom_us[i]), y)
        mo = light_metrics(_issued(p_old[i], dom_old[i]), y)
        rows.append({"stratum": f"{seg}|{prof}", "n": int(len(g)), "v_ok": float(y.mean()),
                     "coverage_us": mu["coverage"], "coverage_v04": mo["coverage"],
                     "n_green_us": mu["n_green"], "false_green_us": mu["false_green"],
                     "n_green_v04": mo["n_green"], "false_green_v04": mo["false_green"],
                     "evaluable": bool(mu["n_green"] >= MIN_GREEN)})
    ev = [r for r in rows if r["evaluable"]]
    worse = [r["stratum"] for r in ev if not r["coverage_us"] > r["coverage_v04"]]
    verdict = "no evaluable" if not ev else ("apoyada" if not worse else "no apoyada")
    return {"strata": rows,
            "h12h": {"verdict": verdict, "evaluable": len(ev), "n": len(rows), "not_better": worse}}
