"""H20: certificado con señales de fiabilidad de la propia red de H19, con una regla fija sin ajuste.

Aplica ``docs/h20/PREREGISTRO_H20.md``. H19 dejó una red que mide bien el volumen del cuerpo (24 de 27 casos de
calibración a ≤ 10 %), pero un certificado cuyos observables de imagen no anticipan cuándo falla (fila «S sí, C no»
de su §7). H20 **no toca la red ni la medida**: la medida es la de ``h19.segment_full`` sobre la imagen tal cual. Solo
cambia el certificado:

* ``flip_volumes``: la red se entrenó con volteos al azar en los tres ejes (``h19.train``), así que los 8 volteos de la
  imagen son entradas igual de válidas. El volumen no cambia al voltear: la dispersión entre las 8 respuestas
  (``s_flip``) mide la inestabilidad de la propia medida.
* ``coarse_volume``: la etapa 1 da su propio volumen a ¼ de resolución; el desacuerdo con la etapa 2 (``s_stage``)
  es una segunda señal gratuita.
* ``rule``: umbrales fijados desde la tolerancia del 10 % antes de calcular ninguna señal; no se ajusta nada con los
  datos (con 27 casos y 3 fallos, un ajuste aprendería ruido).

Solo investigación con datos animales publicados; sin uso clínico.
"""
from __future__ import annotations

import itertools
import math

import numpy as np
import pandas as pd
from scipy import ndimage as ndi

from . import h18, h19

TOLERANCE = h18.TOLERANCE                                   # 10 %
GREEN_FLIP = 0.05                                           # la mitad de la tolerancia para la inestabilidad visible
GREEN_STAGE = 0.10                                          # dos estimadores distintos: hasta la tolerancia entera
RED_FLIP = 0.20                                             # dos veces la tolerancia
RED_STAGE = 0.30                                            # tres: la etapa 1 (¼ de resolución) tiene sesgo de volumen parcial
FLIPS = tuple(c for r in range(4) for c in itertools.combinations((0, 1, 2), r))   # () primero: la identidad
SEED_G0 = 20261123
N_G0 = 5
G0_MAX_SECONDS = 300                                        # por caso: 71 casos en menos de 6 h


def largest_component(mask: np.ndarray) -> np.ndarray:
    """La pieza conectada mayor (26-vecindad), como hace ``h19.segment_full`` con la máscara fina."""
    lab, n = ndi.label(mask, structure=np.ones((3, 3, 3), bool))
    if n <= 1:
        return mask.astype(bool)
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    return lab == int(sizes.argmax())


def coarse_volume(coarse_net, image: np.ndarray) -> float:
    """Volumen (vóxeles a resolución completa) de la etapa 1 sola, con el mismo umbral y la misma limpieza."""
    pc = h19.predict(coarse_net, h19.coarse_sample(image)[0])
    full = h19.upsample_prob(pc, h19.COARSE, image.shape) >= 0.5
    return float(largest_component(full).sum())


def flip_volumes(coarse_net, fine_net, image: np.ndarray, segment=h19.segment_full) -> list[float]:
    """Volumen de la máscara con cada uno de los 8 volteos (la identidad primero)."""
    out = []
    for axes in FLIPS:
        im = np.ascontiguousarray(np.flip(image, axes)) if axes else image
        mask, _ = segment(coarse_net, fine_net, im)
        out.append(float(mask.sum()))
    return out


def signals(volumes: list[float], v_coarse: float) -> dict:
    """``s_flip`` = (máx − mín) / identidad; ``s_stage`` = |etapa 1 − identidad| / identidad. NaN si la máscara es vacía."""
    v_id = float(volumes[0])
    if not v_id > 0:
        return {"v_identity": v_id, "s_flip": math.nan, "s_stage": math.nan}
    return {"v_identity": v_id, "s_flip": (max(volumes) - min(volumes)) / v_id, "s_stage": abs(v_coarse - v_id) / v_id}


def rule(s_flip: float, s_stage: float, in_domain: bool = True) -> str:
    """Verde solo dentro del dominio y con las dos señales bajo su umbral; rojo si una supera el suyo; si no, amarillo.
    Una señal no calculable nunca da verde ni rojo."""
    if not (math.isfinite(s_flip) and math.isfinite(s_stage)):
        return "amarillo"
    if s_flip > RED_FLIP or s_stage > RED_STAGE:
        return "rojo"
    if in_domain and s_flip <= GREEN_FLIP and s_stage <= GREEN_STAGE:
        return "verde"
    return "amarillo"


def lights(df: pd.DataFrame, envelope: dict) -> pd.DataFrame:
    dom = h18.inside(df, envelope)
    sf, ss = df["s_flip"].to_numpy(float), df["s_stage"].to_numpy(float)
    return df.assign(in_domain=dom,
                     light=[rule(a, b, d) for a, b, d in zip(sf, ss, dom)],
                     light_without_guard=[rule(a, b, True) for a, b in zip(sf, ss)])


def out_of_fold(cal: pd.DataFrame, n_folds: int = h18.N_FOLDS, seed: int = h19.SEED) -> pd.DataFrame:
    """Luces de la calibración con la envolvente de dominio ajustada sin el embrión (los mismos pliegues que H19).
    La regla no tiene parámetros: lo único que se ajusta es la guardia."""
    fold = cal["embryo_id"].map(h18.embryo_folds(cal["embryo_id"], n_folds, seed))
    parts = [lights(cal[fold == k], h18.fit_envelope(cal[fold != k])) for k in range(n_folds) if (fold == k).any()]
    return pd.concat(parts).loc[cal.index]


def gate_c(lit: pd.DataFrame) -> dict:
    """Puerta C de H19, sin cambiar: ≥ 10 verdes y como mucho el 10 % de ellas con |error| > 10 %."""
    g = lit[lit["light"] == "verde"]
    fail = float((g["rel_error_volume"].abs() > TOLERANCE).mean()) if len(g) else math.nan
    return {"n_green": int(len(g)), "fail": fail,
            "passed": bool(len(g) >= h19.MIN_GREEN_CAL and math.isfinite(fail) and fail <= h19.MAX_FAIL_CAL)}


def g0(rows: list[dict]) -> dict:
    """Puerta G0 (casos de ajuste, que la red ya vio): solo factibilidad. Señales calculables, la identidad reproduce
    exactamente la medida de H19 y el tiempo cabe. Los valores de las señales no cambian ningún umbral."""
    ok = [math.isfinite(r["s_flip"]) and math.isfinite(r["s_stage"]) and r["identity_matches_h19"]
          and r["seconds"] <= G0_MAX_SECONDS for r in rows]
    return {"n": len(rows), "passed": bool(rows) and all(ok), "items": rows}


def _diff_bootstrap(df: pd.DataFrame, n_boot: int, seed: int) -> list[float]:
    rng = np.random.default_rng(seed)
    emb = df["embryo_id"].unique()
    by = {e: df[df["embryo_id"] == e] for e in emb}
    vals = []
    for _ in range(n_boot):
        s = pd.concat([by[e] for e in rng.choice(emb, len(emb))])
        bad = s["rel_error_volume"].abs() > TOLERANCE
        g = s["light"] == "verde"
        if g.any() and (~g).any():
            vals.append(float(bad[~g].mean() - bad[g].mean()))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))] if vals else [math.nan, math.nan]


def evaluate_test(lit: pd.DataFrame, n_boot: int = h18.N_BOOT, seed: int = h18.SEED) -> dict:
    """H20b (primaria, reglas de H18b/H19b), H20a cobertura, H20c acuerdo de la red, H20d separación verde/no verde."""
    err = lit["rel_error_volume"].abs()
    bad = err > TOLERANCE
    g = lit["light"] == "verde"
    free = lit[lit["light_without_guard"] == "verde"]
    sep = {"fail_green": float(bad[g].mean()) if g.any() else math.nan,
           "fail_not_green": float(bad[~g].mean()) if (~g).any() else math.nan}
    sep["difference"] = sep["fail_not_green"] - sep["fail_green"]
    sep["difference_ci"] = _diff_bootstrap(lit, n_boot, seed)
    return {
        "n_cases": int(len(lit)), "n_embryos": int(lit["embryo_id"].nunique()),
        "h20b": h18.green_failure(lit, n_boot, seed),
        "h20a": {"green_fraction": float(g.mean()) if len(lit) else math.nan,
                 "lights": lit["light"].value_counts().to_dict()},
        "h20c": {"dice_median": float(lit["dice"].median()), "abs_error_median": float(err.median()),
                 "ok10": float((err <= TOLERANCE).mean()), "ok5": float((err <= 0.05).mean())},
        "h20d": {**sep, "in_domain": float(lit["in_domain"].mean()), "green_without_guard": int(len(free)),
                 "green_without_guard_bad": int((free["rel_error_volume"].abs() > TOLERANCE).sum())},
    }


THRESHOLDS = {"green_flip": GREEN_FLIP, "green_stage": GREEN_STAGE, "red_flip": RED_FLIP, "red_stage": RED_STAGE,
              "tolerance": TOLERANCE, "flips": [list(f) for f in FLIPS]}
