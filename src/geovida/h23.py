"""H23: las señales de fiabilidad de H20, sin cambios, en ventrículos cerebrales (docs/h23/PREREGISTRO_H23.md).

Lo único nuevo respecto de H19/H20 es la estructura (ventrículo en lugar de cuerpo), dos puertas y el criterio de
separación que faltó en H20:

* ``g0_scale``: antes de entrenar, el ventrículo de referencia reducido a ¼ (como lo ve la etapa 1) tiene
  ≥ 27 vóxeles en ≥ 90 % de los casos de ajuste.
* ``gate_s``: ≥ 50 % de los casos de calibración a ≤ 10 % de la referencia (la puerta S de H19).
* ``separation``: Δ = fallos entre no verdes − fallos entre verdes, IC por remuestreo de embriones; «separa» si el
  límite inferior > 0, «no separa» si el superior ≤ 0,05.

Desviación D-1 (aprobada antes de entrenar): ``segment_all`` y ``coarse_volume_all`` cuentan todas las piezas de la
máscara en lugar de la mayor, porque el ventrículo de referencia no es una sola pieza.

Red, señales, regla, guardia y puerta C son las de ``h19`` y ``h20`` sin tocar. Solo investigación con datos animales
publicados; sin uso clínico.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import h18, h19, h20

STRUCTURE = "ventricle"
SEED_G0 = 20261124
MIN_COARSE_VOXELS = 27            # un cubo de 3³ a ¼ de resolución
MIN_COARSE_FRACTION = 0.90
S_MIN_OK = 0.50                   # puerta S de H19
SEP_NO_MAX = 0.05                 # «no separa» si el límite superior de Δ no pasa de 5 puntos
SEP_MIN_EACH = 5                  # evaluable con ≥ 5 verdes y ≥ 5 no verdes


def cases(manifest: str, split: str) -> tuple[pd.DataFrame, dict]:
    """Casos de ventrículo del reparto de los autores, por embrión (``h18.split_cases``)."""
    m = pd.read_csv(manifest)
    df, rep = h18.split_cases(m[m["structure"] == STRUCTURE])
    sel = df[df["split"] == split].reset_index(drop=True)
    assert set(sel["split"]) <= {split}
    return sel, rep


def coarse_voxels(ref: np.ndarray) -> int:
    """Vóxeles del objetivo de la etapa 1: la referencia reducida a ¼ con umbral 0,5 (``h19.coarse_sample``)."""
    return int((h19.downsample(ref.astype(np.float32), h19.COARSE) >= 0.5).sum())


def largest_fraction(ref: np.ndarray) -> float:
    """Fracción de la referencia en su pieza conectada mayor (descriptivo: ``segment_full`` se queda con una)."""
    n = float(ref.sum())
    return float(h20.largest_component(ref).sum()) / n if n else math.nan


def segment_all(coarse_net, fine_net, image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Desviación D-1: la medida de ``h19.segment_full`` sin quedarse con la pieza mayor. El ventrículo de referencia
    tiene varias piezas (mediana 77 % en la mayor en los casos de ajuste), así que se cuentan todas."""
    _, prob = h19.segment_full(coarse_net, fine_net, image)
    return prob >= 0.5, prob


def coarse_volume_all(coarse_net, image: np.ndarray) -> float:
    """D-1: volumen de la etapa 1 sola (umbral 0,5) sin quedarse con la pieza mayor."""
    pc = h19.predict(coarse_net, h19.coarse_sample(image)[0])
    return float((h19.upsample_prob(pc, h19.COARSE, image.shape) >= 0.5).sum())


def g0_scale(counts: list[int]) -> dict:
    ok = np.asarray(counts) >= MIN_COARSE_VOXELS
    frac = float(ok.mean()) if len(ok) else math.nan
    return {"n": int(len(ok)), "fraction_ok": frac, "min_voxels": MIN_COARSE_VOXELS,
            "passed": bool(len(ok)) and frac >= MIN_COARSE_FRACTION}


def gate_s(cal: pd.DataFrame) -> dict:
    ok = float((cal["rel_error_volume"].abs() <= h20.TOLERANCE).mean()) if len(cal) else math.nan
    return {"n": int(len(cal)), "fraction_ok10": ok, "passed": bool(len(cal)) and ok >= S_MIN_OK}


def separation(lit: pd.DataFrame, n_boot: int = h18.N_BOOT, seed: int = h18.SEED) -> dict:
    bad = lit["rel_error_volume"].abs() > h20.TOLERANCE
    g = lit["light"] == "verde"
    out = {"n_green": int(g.sum()), "n_not_green": int((~g).sum())}
    if out["n_green"] < SEP_MIN_EACH or out["n_not_green"] < SEP_MIN_EACH:
        return {**out, "difference": None, "ci": None, "verdict": "no evaluable"}
    diff = float(bad[~g].mean() - bad[g].mean())
    ci = h20._diff_bootstrap(lit, n_boot, seed)
    if not all(math.isfinite(x) for x in ci):
        return {**out, "difference": diff, "ci": ci, "verdict": "no evaluable"}
    verdict = "separa" if ci[0] > 0 else ("no separa" if ci[1] <= SEP_NO_MAX else "no concluyente")
    return {**out, "difference": diff, "fail_green": float(bad[g].mean()), "fail_not_green": float(bad[~g].mean()),
            "ci": ci, "verdict": verdict}


def evaluate_test(lit: pd.DataFrame, n_boot: int = h18.N_BOOT, seed: int = h18.SEED) -> dict:
    """H23b (= H20b), H23d (separación), H23a cobertura, H23c rendimiento, H23e verdes sin guardia."""
    base = h20.evaluate_test(lit, n_boot, seed)
    return {"n_cases": base["n_cases"], "n_embryos": base["n_embryos"],
            "h23b": base["h20b"], "h23d": separation(lit, n_boot, seed), "h23a": base["h20a"], "h23c": base["h20c"],
            "h23e": {k: base["h20d"][k] for k in ("in_domain", "green_without_guard", "green_without_guard_bad")}}
