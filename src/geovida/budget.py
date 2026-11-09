"""Semáforo de adecuación de resolución (v0.3): el instrumento juzga su propia fiabilidad.

Pregunta: dada solo una máscara y el tamaño del vóxel (sin conocer la forma real),
¿con qué probabilidad el volumen medido tiene error <= 5 %?

Predictor, calculable en datos reales: la profundidad media interior de la máscara,
``d_mean`` (media de la distancia a la frontera sobre los vóxeles del objeto), en
unidades del vóxel geométrico ``h_geo``. Se eligió por validación cruzada (una forma
fuera) entre dos candidatas, con la semilla de calibración 20261116: la otra, el
cociente V/(S·h) medido, era peor porque el área medida colapsa a baja resolución
(``docs/PREREGISTRO_H6.md``, ``results/summary/h6_calibration_loso.csv``).
Los modelos se congelaron con esa calibración y se confirmaron con semillas nuevas.

Límites que el código no oculta:
* Vale solo para el volumen, para este modelo de imagen sintético y para sólidos
  de la familia usada; la topología queda fuera.
* Una máscara vacía o una profundidad no medible dan p = 0 y luz roja, nunca un
  número inventado.
* El modelo depende del segmentador y del perfil de imagen que el usuario declara.
"""
from __future__ import annotations

import math

import numpy as np

from .analysis import predict_frozen
from .measure import measure_mask

GREEN = 0.90   # preregistrado en H6
RED = 0.50

# Pr(|err V| <= 5 %) = expit(a + b ln(d_mean / h_geo)), por segmentador|perfil.
# Copia de results/summary/h6_frozen_models.json (una prueba comprueba que coinciden).
FROZEN_H6: dict = {
    "feature": "F2",
    "column": "d_over_hgeo",
    "models": {
        "global|ideal": {"intercept": 3.8711207594408537, "slope": 5.913882833618431},
        "global|realistic": {"intercept": 3.329914796589346, "slope": 6.301357579588664},
        "otsu|ideal": {"intercept": 2.107940440893577, "slope": 5.651811584827622},
        "otsu|realistic": {"intercept": 2.1961693755426523, "slope": 8.700288375012697},
        "smoothed_otsu|ideal": {"intercept": -3.451501136325328, "slope": 11.762435089554696},
        "smoothed_otsu|realistic": {"intercept": -4.075140297872758, "slope": 12.465451333199491},
    },
}


def h_geo(spacing) -> float:
    return float(np.prod(np.asarray(spacing, float)) ** (1.0 / 3.0))


def q_hat_over_hgeo(volume: float, area: float, spacing) -> float:
    """Q_hat / h_geo = V_hat / (S_hat h_geo); NaN si V o S no son positivos y finitos.

    Es el predictor descartado en la calibración; se conserva como referencia (H6a).
    """
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


def feature_value(meas: dict, spacing) -> float:
    """Variable del semáforo: ``d_mean / h_geo``; NaN si no es positiva y finita."""
    d = meas.get("d_mean", float("nan"))
    if d is None or not math.isfinite(d) or d <= 0:
        return float("nan")
    return float(d / h_geo(spacing))


def p_volume_ok(x: float, segmenter: str, profile: str, models=None) -> float:
    """Pr(|err V| <= 5 %) dado ``x = d_mean / h_geo``; 0 si x no es medible."""
    models = FROZEN_H6["models"] if models is None else models
    if x is None or not math.isfinite(x) or x <= 0:
        return 0.0
    key = f"{segmenter}|{profile}"
    if key not in models:
        raise KeyError(f"sin modelo congelado para {key!r}; hay: {sorted(models)}")
    return float(predict_frozen(models[key], x))


def traffic_light(p: float) -> str:
    if p is None or not math.isfinite(p):
        return "rojo"
    if p >= GREEN:
        return "verde"
    return "amarillo" if p >= RED else "rojo"


def adequacy(mask: np.ndarray, spacing, segmenter: str, profile: str, models=None) -> dict:
    """Informe de adecuación de una máscara. Solo usa la máscara y el vóxel.

    Devuelve también ``measurements`` (todas las medidas) para no medir dos veces.
    """
    mask = np.asarray(mask, bool)
    if not mask.any():
        return {"volume": 0.0, "feature": float("nan"), "p_volume_ok": 0.0, "light": "rojo",
                "motivo": "máscara vacía", "measurements": {}}
    meas = measure_mask(mask, spacing)
    x = feature_value(meas, spacing)
    p = p_volume_ok(x, segmenter, profile, models)
    motivo = "profundidad no medible" if not math.isfinite(x) else ""
    return {"volume": meas["volume"], "feature": x, "p_volume_ok": p,
            "light": traffic_light(p), "motivo": motivo, "measurements": meas}
