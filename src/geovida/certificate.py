"""Certificado vectorial de una medida (v0.4): volumen, topología y dominio.

Dada una imagen 3D, el tamaño del vóxel y el segmentador y perfil que el usuario declara,
devuelve, SIN conocer la verdad:

* la luz del **volumen** (semáforo de H6, por profundidad media);
* la luz de la **topología** (semáforo de H9, por margen de persistencia) y dónde está su punto
  más frágil;
* si la imagen cae **dentro del dominio** en el que se calibraron esos semáforos. Fuera de él no
  hay luz verde: como mucho, amarilla.

Uso previsto: investigación y educación. No es una herramienta clínica ni diagnóstica.
Los modelos se calibraron con un simulador de imagen; una luz verde no es una validación con
datos reales. Un rasgo que la imagen ya perdió por completo no deja rastro y no se detecta.
"""
from __future__ import annotations

import json
import math
from functools import lru_cache
from importlib import resources

import numpy as np

from .analysis import predict_logit_multi
from .budget import FROZEN_H6, GREEN, RED, feature_value, p_volume_ok, traffic_light
from .certsweep import cert_extra
from .domain import in_domain
from .measure import measure_mask
from .segment import SEGMENTERS, segment
from .topomargin import critical_sites

LIMITS = (
    "Calibrado con imágenes sintéticas; no validado con datos reales ni fantomas físicos.",
    "Un rasgo que la imagen perdió por completo no deja rastro: no se detecta.",
    "Fuera del dominio de calibración no hay luz verde.",
    "Solo investigación y educación; sin uso clínico ni diagnóstico.",
)
OUT_OF_DOMAIN = "fuera del dominio de calibración: recalibrar para este tipo de imagen"


@lru_cache(maxsize=1)
def load_frozen() -> dict:
    """Modelos y envolventes congelados en H9/H10 (copia empaquetada de
    ``results/summary/h9_frozen.json``; una prueba comprueba que coinciden)."""
    with resources.files("geovida").joinpath("frozen/h9_frozen.json").open(encoding="utf-8") as fh:
        return json.load(fh)


def _capped(light: str, inside: bool) -> tuple[str, str]:
    if light == "verde" and not inside:
        return "amarillo", OUT_OF_DOMAIN
    return light, ""


def certify(image: np.ndarray, spacing, segmenter: str, profile: str,
            frozen: dict | None = None) -> dict:
    frozen = load_frozen() if frozen is None else frozen
    key = f"{segmenter}|{profile}"
    if segmenter not in SEGMENTERS or key not in frozen["models"]:
        raise KeyError(f"sin calibración para {key!r}; hay: {sorted(frozen['models'])}")
    image = np.asarray(image, dtype=np.float32)
    if image.ndim != 3:
        raise ValueError("se espera una imagen 3D")
    spacing = tuple(float(s) for s in spacing)
    mask = segment(segmenter, image, spacing)
    base = {"declared": {"segmenter": segmenter, "profile": profile}, "spacing": list(spacing),
            "shape": list(image.shape), "limits": list(frozen.get("limits", LIMITS)),
            "thresholds": {"green": GREEN, "red": RED}}
    if not mask.any():
        empty = {"p": 0.0, "light": "rojo", "reason": "máscara vacía", "in_domain": False}
        return {**base, "volume": {"value": 0.0, **empty},
                "topology": {"betti": [0, 0, 0], "critical_sites": {"erosion": None, "dilation": None},
                             **empty},
                "observables": {}}
    meas = measure_mask(mask, spacing)
    obs = cert_extra(image, spacing, mask, segmenter, meas)
    x = feature_value(meas, spacing)
    obs["d_over_hgeo"] = x
    obs["ln_d"] = math.log(x) if math.isfinite(x) and x > 0 else math.nan

    env_v, env_t = frozen["envelopes"]["volume"][key], frozen["envelopes"]["topology"][key]
    dom_v = bool(env_v is not None and in_domain(obs, env_v))
    dom_t = bool(env_t is not None and in_domain(obs, env_t))

    # v0.5: un congelado recalibrado (H12) trae sus propios modelos de volumen
    pv = p_volume_ok(x, segmenter, profile, frozen.get("volume_models", FROZEN_H6["models"]))
    light_v, why_v = _capped(traffic_light(pv), dom_v)

    model = frozen["models"][key]["main"]
    feats = np.array([obs.get(f, math.nan) for f in model["features"]], dtype=float)
    pt = float(predict_logit_multi(model, feats[None, :])[0]) if np.isfinite(feats).all() else 0.0
    light_t, why_t = _capped(traffic_light(pt), dom_t)

    return {
        **base,
        "volume": {"value": float(meas["volume"]), "p": pv, "light": light_v, "reason": why_v,
                   "in_domain": dom_v},
        "topology": {"betti": [int(meas["b0_26"]), int(meas["b1_26"]), int(meas["b2_26"])],
                     "p": pt, "light": light_t, "reason": why_t, "in_domain": dom_t,
                     "critical_sites": critical_sites(mask, spacing)},
        "observables": {k: (None if isinstance(v, float) and not math.isfinite(v) else float(v))
                        for k, v in obs.items()},
        "envelopes": {"volume": env_v, "topology": env_t},
    }


def min_depth_for_green(segmenter: str, profile: str, prob: float = GREEN) -> float:
    """Profundidad media (en vóxeles) a partir de la cual el volumen recibe luz verde."""
    m = FROZEN_H6["models"][f"{segmenter}|{profile}"]
    return float(math.exp((math.log(prob / (1 - prob)) - m["intercept"]) / m["slope"]))


def planning_table() -> list[dict]:
    """Resolución mínima para luz verde de volumen, traducida a tres geometrías sencillas.

    La profundidad media de una bola de diámetro D es D/8; la de un cilindro largo de diámetro D,
    D/6; la de una lámina de grosor T, T/4. Sirve para planificar ANTES de adquirir: es una guía
    derivada de fantomas sintéticos, no una garantía.
    """
    rows = []
    for key in sorted(FROZEN_H6["models"]):
        seg, prof = key.split("|")
        x = min_depth_for_green(seg, prof)
        rows.append({"segmenter": seg, "profile": prof, "min_depth_voxels": x,
                     "ball_diameter_voxels": 8 * x, "cylinder_diameter_voxels": 6 * x,
                     "slab_thickness_voxels": 4 * x})
    return rows
