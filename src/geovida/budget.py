"""Semáforo de adecuación de resolución (v0.3): el instrumento juzga su propia fiabilidad.

Pregunta: dada solo una máscara y el tamaño del vóxel (sin conocer la forma real),
¿con qué probabilidad el volumen medido tiene error <= 5 %?

Predictor, calculable en datos reales: Q_hat / h_geo = V_hat / (S_hat · h_geo),
con V_hat = conteo de vóxeles y S_hat = ``area_sdf``. Los modelos logísticos se
ajustaron UNA vez con los datos de H3 (``scripts/freeze_h6_models.py``) y se
evalúan en H6 con semillas y formas nuevas (``docs/PREREGISTRO_H6.md``).

Límites que el código no oculta:
* A baja resolución S_hat subestima y Q_hat sale inflado (piloto: ×1.4 a 3 vóxeles,
  ×2–3 a 1.5); por eso el modelo se ajusta sobre Q_hat, no sobre Q verdadero.
* Una máscara vacía o un área no medible dan p = 0 y luz roja, nunca un número inventado.
* El modelo depende del segmentador y del perfil de imagen declarados.
"""
from __future__ import annotations

import math

import numpy as np

from .analysis import predict_frozen
from .measure import measure_mask

GREEN = 0.90   # preregistrado en H6
RED = 0.50

# Coeficientes de Pr(|err V| <= 5 %) = expit(a + b ln(Q_hat/h_geo)), por segmentador|perfil.
# Se llenan desde results/summary/h6_frozen_models.json (hay una prueba que lo verifica).
FROZEN_H6: dict[str, dict[str, float]] = {}


def h_geo(spacing) -> float:
    return float(np.prod(np.asarray(spacing, float)) ** (1.0 / 3.0))


def q_hat_over_hgeo(volume: float, area: float, spacing) -> float:
    """Q_hat / h_geo; NaN si el volumen o el área no son positivos y finitos."""
    if not (math.isfinite(volume) and math.isfinite(area)) or volume <= 0 or area <= 0:
        return float("nan")
    return float(volume / area / h_geo(spacing))


def add_measured_q(df):
    """Añade ``q_hat_over_hgeo`` a una tabla de barrido (t = 1; h_xy = 1/t_over_h)."""
    out = df.copy()
    h = (1.0 / out["t_over_h"]) * out["anisotropy"] ** (1.0 / 3.0)
    ok = (out["volume"] > 0) & (out["area_sdf"] > 0)
    q = (out["volume"] / out["area_sdf"]).where(ok) / h
    out["q_hat_over_hgeo"] = q
    return out


def p_volume_ok(q_over_hgeo: float, segmenter: str, profile: str, models=None) -> float:
    models = FROZEN_H6 if models is None else models
    if q_over_hgeo is None or not math.isfinite(q_over_hgeo) or q_over_hgeo <= 0:
        return 0.0
    key = f"{segmenter}|{profile}"
    if key not in models:
        raise KeyError(f"sin modelo congelado para {key!r}; hay: {sorted(models)}")
    return float(predict_frozen(models[key], q_over_hgeo))


def traffic_light(p: float) -> str:
    if p is None or not math.isfinite(p):
        return "rojo"
    if p >= GREEN:
        return "verde"
    return "amarillo" if p >= RED else "rojo"


def adequacy(mask: np.ndarray, spacing, segmenter: str, profile: str, models=None) -> dict:
    """Informe de adecuación de una máscara. Solo usa la máscara y el vóxel."""
    mask = np.asarray(mask, bool)
    if not mask.any():
        return {"volume": 0.0, "area_sdf": float("nan"), "q_hat_over_hgeo": float("nan"),
                "p_volume_ok": 0.0, "light": "rojo", "motivo": "máscara vacía"}
    meas = measure_mask(mask, spacing)
    q = q_hat_over_hgeo(meas["volume"], meas["area_sdf"], spacing)
    p = p_volume_ok(q, segmenter, profile, models)
    motivo = "área no medible" if not math.isfinite(q) else ""
    return {"volume": meas["volume"], "area_sdf": meas["area_sdf"], "q_hat_over_hgeo": q,
            "p_volume_ok": p, "light": traffic_light(p), "motivo": motivo}
