"""Descriptores invariantes de forma y análisis de sensibilidad del umbral.

Aporta controles de robustez computacional. Sus índices no son probabilidades,
intervalos de confianza biológicos ni validaciones clínicas.
"""
from __future__ import annotations

import math
from numbers import Real
from collections import Counter

import numpy as np
from skimage import measure

from src.metrics_2d import measure_mask, metrics_to_dict

CONTINUOUS_METRICS = ("area", "perimeter", "aspect_ratio", "circularity", "eccentricity")
TOPOLOGY_METRICS = ("beta0", "beta1", "euler_characteristic")


def _largest_component(binary: np.ndarray) -> np.ndarray:
    labels = measure.label(binary, connectivity=2)
    counts = np.bincount(labels.ravel())
    if len(counts) <= 1 or counts[1:].max(initial=0) == 0:
        raise ValueError("La máscara no contiene una componente de objeto.")
    largest_label = int(np.argmax(counts[1:]) + 1)
    return labels == largest_label


def hu_invariant_features(mask: np.ndarray) -> dict[str, float]:
    """Calcula siete momentos invariantes de Hu sobre la componente mayor.

    Devuelve los valores originales (hu_1 a hu_7) y una transformación
    signed-log (hu_log_1 a hu_log_7) para comprimir el rango dinámico. La
    invariancia teórica no elimina efectos de rasterización, discretización,
    ruido o errores en el contorno.
    """
    binary = np.asarray(mask, dtype=bool)
    if binary.ndim != 2 or binary.size == 0 or not binary.any():
        raise ValueError("La máscara debe ser 2D, no vacía y contener objeto.")

    component = _largest_component(binary).astype(np.float64)
    raw = measure.moments(component, order=3)
    mass = float(raw[0, 0])
    if not math.isfinite(mass) or mass <= 0:
        raise ValueError("No fue posible calcular los momentos de la máscara.")

    center = (float(raw[1, 0] / mass), float(raw[0, 1] / mass))
    central = measure.moments_central(component, center=center, order=3)
    normalized = measure.moments_normalized(central, order=3)
    hu = np.asarray(measure.moments_hu(normalized), dtype=np.float64)
    if hu.shape != (7,) or not np.isfinite(hu).all():
        raise ValueError("Los momentos de Hu no son finitos para esta máscara.")

    result: dict[str, float] = {}
    tiny = np.finfo(np.float64).tiny
    for index, value in enumerate(hu, start=1):
        result[f"hu_{index}"] = float(value)
        transformed = 0.0 if abs(float(value)) <= tiny else float(np.sign(value) * np.log10(abs(value)))
        result[f"hu_log_{index}"] = transformed
    return result


def _validated_thresholds(thresholds) -> tuple[float, ...]:
    try:
        parsed = tuple(float(value) for value in thresholds)
    except (TypeError, ValueError) as exc:
        raise ValueError("Los umbrales deben ser números entre 0 y 1.") from exc
    if len(parsed) < 3:
        raise ValueError("Se requieren al menos tres umbrales para evaluar sensibilidad.")
    if any(not math.isfinite(value) or value < 0 or value > 1 for value in parsed):
        raise ValueError("Todos los umbrales deben ser finitos y pertenecer a [0, 1].")
    if len(set(parsed)) != len(parsed):
        raise ValueError("Los umbrales deben ser únicos.")
    return tuple(sorted(parsed))


def analyze_threshold_sensitivity(
    gray_image: np.ndarray,
    thresholds=(0.3, 0.4, 0.5, 0.6, 0.7),
    pixel_size: float = 1.0,
) -> dict:
    """Evalúa cómo cambian las medidas al variar el umbral de intensidad.

    El robustness_index es un índice exploratorio (0–100), no probabilidad ni
    estimación validada de la exactitud anatómica.
    """
    gray = np.asarray(gray_image, dtype=np.float64)
    if gray.ndim != 2 or gray.size == 0:
        raise ValueError("gray_image debe ser una matriz 2D no vacía.")
    if not np.isfinite(gray).all() or gray.min() < 0 or gray.max() > 1:
        raise ValueError("gray_image debe contener intensidades finitas en [0, 1].")
    if (
        isinstance(pixel_size, bool)
        or not isinstance(pixel_size, Real)
        or not math.isfinite(float(pixel_size))
        or pixel_size <= 0
    ):
        raise ValueError("pixel_size debe ser finito y positivo.")

    levels = _validated_thresholds(thresholds)
    runs: list[dict] = []
    for level in levels:
        mask = gray > level
        if not mask.any():
            runs.append({"threshold": level, "status": "EMPTY_MASK"})
            continue
        try:
            metrics = metrics_to_dict(measure_mask(mask, pixel_size=float(pixel_size)))
            record = {"threshold": level, "status": "OK"}
            for metric in (*CONTINUOUS_METRICS, *TOPOLOGY_METRICS):
                value = metrics.get(metric)
                record[metric] = (
                    None if value is None or not math.isfinite(float(value)) else float(value)
                )
            runs.append(record)
        except (ValueError, RuntimeError) as exc:
            runs.append({"threshold": level, "status": "ERROR", "error": str(exc)})

    valid_runs = [run for run in runs if run["status"] == "OK"]
    failed_runs = len(runs) - len(valid_runs)
    summary: dict[str, object] = {
        "thresholds_attempted": len(levels),
        "thresholds_valid": len(valid_runs),
        "thresholds_failed": failed_runs,
        "thresholds": list(levels),
        "topology_states": 0,
        "topology_stability": None,
        "robustness_index": None,
        "metric_summary": {},
        "flags": [],
    }
    if len(valid_runs) < 3:
        summary["flags"].append("INSUFFICIENT_VALID_THRESHOLDS")
    if failed_runs:
        summary["flags"].append("AT_LEAST_ONE_THRESHOLD_FAILED")

    topology_counts = Counter(
        (int(run["beta0"]), int(run["beta1"])) for run in valid_runs
    )
    if topology_counts:
        summary["topology_states"] = len(topology_counts)
        summary["topology_stability"] = float(max(topology_counts.values()) / len(valid_runs))
        if len(topology_counts) > 1:
            summary["flags"].append("TOPOLOGY_CHANGES_ACROSS_THRESHOLDS")

    for metric in CONTINUOUS_METRICS:
        values = np.asarray(
            [run[metric] for run in valid_runs if run.get(metric) is not None],
            dtype=np.float64,
        )
        if values.size == 0:
            summary["metric_summary"][metric] = {
                "mean": None, "std": None, "cv": None, "min": None, "max": None
            }
            continue
        mean = float(np.mean(values))
        std = float(np.std(values, ddof=0))
        cv = float(std / abs(mean)) if abs(mean) > np.finfo(float).eps else None
        summary["metric_summary"][metric] = {
            "mean": mean, "std": std, "cv": cv,
            "min": float(np.min(values)), "max": float(np.max(values)),
        }

    if len(valid_runs) >= 3 and summary["topology_stability"] is not None:
        cv_stabilities = []
        for metric in CONTINUOUS_METRICS:
            cv = summary["metric_summary"][metric]["cv"]
            if cv is not None and math.isfinite(cv):
                cv_stabilities.append(1.0 / (1.0 + max(0.0, float(cv))))
        if cv_stabilities:
            continuous_stability = float(np.mean(cv_stabilities))
            topology_stability = float(summary["topology_stability"])
            summary["continuous_stability"] = continuous_stability
            summary["robustness_index"] = round(
                float(100.0 * (0.5 * topology_stability + 0.5 * continuous_stability)), 4
            )
    return {"summary": summary, "runs": runs}
