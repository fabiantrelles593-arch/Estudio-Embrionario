"""Analiza imágenes enumeradas en un manifiesto trazable.

Integra auditoría de metadatos, métricas 2D, momentos de Hu y sensibilidad opcional
a umbrales. No sustituye la segmentación anatómica.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.audit_dataset import audit_dataframe
from src.image_io import load_grayscale_image
from src.metrics_2d import measure_mask, metrics_to_dict
from src.advanced_morphology import hu_invariant_features, analyze_threshold_sensitivity

REQUIRED_MANIFEST_COLUMNS = {"image_path"}
OUTPUT_CONTEXT_FIELDS = [
    "observation_id", "specimen_id", "image_id", "stage", "modality", "view",
    "section_id", "source", "asset_identifier", "license_status",
    "pixel_size", "pixel_size_unit", "segmentation_method",
    "segmentation_operator", "quality_flag", "notes", "image_path",
]


class ManifestAuditError(ValueError):
    """El manifiesto no superó la auditoría requerida para analizarlo."""


def _optional_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _scale_from_row(row: dict) -> tuple[float, str, str]:
    """Devuelve (unidades_por_pixel, unidad, estado_de_escala).

    Si no se declara escala, las medidas permanecen en píxeles. Si se declara
    escala física, exige unidad y valor finito positivo.
    """
    raw_scale = row.get("pixel_size")
    raw_unit = _optional_text(row.get("pixel_size_unit", ""))
    absent = raw_scale is None or pd.isna(raw_scale) or _optional_text(raw_scale) == ""
    if absent:
        if raw_unit:
            raise ValueError("pixel_size_unit está indicada, pero pixel_size está vacío.")
        return 1.0, "px", "unknown_scale_kept_in_pixels"

    try:
        scale = float(raw_scale)
    except (TypeError, ValueError) as exc:
        raise ValueError("pixel_size debe ser un número positivo.") from exc
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("pixel_size debe ser finito y positivo.")
    if not raw_unit:
        raise ValueError("pixel_size_unit es obligatoria cuando se declara pixel_size.")
    return scale, raw_unit, "scale_declared_in_manifest"


def analyze_manifest(
    manifest_path: str | Path,
    output_csv: str | Path,
    audit_json: str | Path | None = None,
    threshold: float = 0.5,
    sensitivity: bool = False,
    sensitivity_thresholds: tuple[float, ...] | None = None,
) -> dict:
    """Analiza un manifiesto CSV y escribe una fila por observación.

    Rutas relativas se resuelven desde el directorio del manifiesto. Si la
    auditoría del dataset falla, el análisis queda bloqueado. Los errores por
    imagen se conservan en el CSV para no ocultar observaciones fallidas.
    """
    manifest = Path(manifest_path).expanduser().resolve()
    if not manifest.is_file():
        raise FileNotFoundError(f"No se encontró el manifiesto: {manifest}")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float, np.number)):
        raise ValueError("threshold debe ser un número finito en [0, 1].")
    if not np.isfinite(threshold) or threshold < 0 or threshold > 1:
        raise ValueError("threshold debe ser un número finito en [0, 1].")

    frame = pd.read_csv(manifest, dtype={"observation_id": "string"})
    missing_columns = sorted(REQUIRED_MANIFEST_COLUMNS - set(frame.columns))
    if missing_columns:
        raise ValueError(
            "Faltan columnas del manifiesto necesarias para procesar imágenes: "
            + ", ".join(missing_columns)
        )

    audit = audit_dataframe(frame)
    audit_path = Path(audit_json) if audit_json else Path(output_csv).with_suffix(".audit.json")
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(
        json.dumps(audit.__dict__, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if not audit.ok:
        raise ManifestAuditError(
            f"La auditoría no fue aprobada; no se analizaron imágenes. Revisa {audit_path}."
        )

    output_rows = []
    for row in frame.to_dict(orient="records"):
        metadata = {field: row.get(field, "") for field in OUTPUT_CONTEXT_FIELDS}
        try:
            image_value = _optional_text(row.get("image_path"))
            if not image_value:
                raise ValueError("image_path está vacío.")
            image_path = Path(image_value).expanduser()
            if not image_path.is_absolute():
                image_path = manifest.parent / image_path

            pixel_size, unit, scale_status = _scale_from_row(row)
            gray = load_grayscale_image(image_path)
            mask = gray > float(threshold)
            if not mask.any():
                raise ValueError("La máscara quedó vacía con este umbral; revisar imagen y segmentación.")

            metrics = metrics_to_dict(measure_mask(mask, pixel_size=pixel_size))
            hu_features = hu_invariant_features(mask)
            record = {
                **metadata,
                "resolved_image_path": str(image_path.resolve()),
                "pixel_size_used": pixel_size,
                "measurement_length_unit": unit,
                "scale_status": scale_status,
                **metrics,
                **hu_features,
                "analysis_status": "OK",
                "analysis_error": "",
            }
            if sensitivity:
                levels = sensitivity_thresholds
                if levels is None:
                    levels = tuple(sorted({
                        float(np.clip(float(threshold) + offset, 0.0, 1.0))
                        for offset in (-0.2, -0.1, 0.0, 0.1, 0.2)
                    }))
                try:
                    profile = analyze_threshold_sensitivity(
                        gray, thresholds=levels, pixel_size=pixel_size
                    )
                    sensitivity_summary = profile["summary"]
                    metric_summary = sensitivity_summary.get("metric_summary", {})
                    record.update({
                        "sensitivity_status": "OK",
                        "sensitivity_error": "",
                        "robustness_index": sensitivity_summary.get("robustness_index"),
                        "topology_stability": sensitivity_summary.get("topology_stability"),
                        "topology_states": sensitivity_summary.get("topology_states"),
                        "thresholds_attempted": sensitivity_summary.get("thresholds_attempted"),
                        "thresholds_valid": sensitivity_summary.get("thresholds_valid"),
                        "thresholds_failed": sensitivity_summary.get("thresholds_failed"),
                        "area_cv": metric_summary.get("area", {}).get("cv"),
                        "perimeter_cv": metric_summary.get("perimeter", {}).get("cv"),
                        "aspect_ratio_cv": metric_summary.get("aspect_ratio", {}).get("cv"),
                        "circularity_cv": metric_summary.get("circularity", {}).get("cv"),
                        "sensitivity_flags": ";".join(sensitivity_summary.get("flags", [])),
                        "threshold_sensitivity_json": json.dumps(
                            profile, ensure_ascii=False, allow_nan=False
                        ),
                    })
                except (ValueError, TypeError, RuntimeError) as sensitivity_exc:
                    record.update({
                        "sensitivity_status": "ERROR",
                        "sensitivity_error": f"{type(sensitivity_exc).__name__}: {sensitivity_exc}",
                    })
            else:
                record["sensitivity_status"] = "NOT_REQUESTED"
                record["sensitivity_error"] = ""
            output_rows.append(record)
        except (OSError, ValueError, TypeError, RuntimeError) as exc:
            output_rows.append({
                **metadata,
                "resolved_image_path": "",
                "pixel_size_used": np.nan,
                "measurement_length_unit": "",
                "scale_status": "not_available",
                "analysis_status": "ERROR",
                "analysis_error": f"{type(exc).__name__}: {exc}",
                "sensitivity_status": "NOT_RUN",
                "sensitivity_error": "No se calculó sensibilidad porque falló el análisis base.",
            })

    output = Path(output_csv)
    output.parent.mkdir(parents=True, exist_ok=True)
    results = pd.DataFrame(output_rows)
    results.to_csv(output, index=False)
    errors = int((results["analysis_status"] != "OK").sum()) if not results.empty else 0
    sensitivity_errors = int(
        (results.get("sensitivity_status", pd.Series(dtype=str)) == "ERROR").sum()
    )
    return {
        "manifest": str(manifest),
        "output_csv": str(output.resolve()),
        "audit_json": str(audit_path.resolve()),
        "audit_ok": bool(audit.ok),
        "n_rows": int(len(results)),
        "n_analyzed": int(len(results) - errors),
        "n_errors": errors,
        "threshold": float(threshold),
        "sensitivity_enabled": bool(sensitivity),
        "n_sensitivity_errors": sensitivity_errors,
        "scientific_note": (
            "El estado OK solo indica que la máscara se pudo medir. No valida "
            "la exactitud anatómica de la segmentación ni una hipótesis biológica."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Mide máscaras 2D desde un CSV de metadatos auditado."
    )
    parser.add_argument("manifest", help="CSV con metadatos y columna image_path")
    parser.add_argument("--out", default="results/morphology_results.csv")
    parser.add_argument("--audit-out", default=None)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument(
        "--sensitivity", action="store_true",
        help="Calcula momentos de Hu y sensibilidad morfológica/topológica a varios umbrales.",
    )
    parser.add_argument(
        "--sensitivity-thresholds", default=None,
        help="Umbrales separados por comas entre 0 y 1; por defecto usa el umbral principal ±0.1 y ±0.2.",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Devuelve código 2 si falla una medición base o la sensibilidad opcional.",
    )
    args = parser.parse_args(argv)
    try:
        sensitivity_levels = None
        if args.sensitivity_thresholds:
            try:
                sensitivity_levels = tuple(
                    float(item.strip()) for item in args.sensitivity_thresholds.split(",")
                )
            except ValueError as exc:
                raise ValueError(
                    "--sensitivity-thresholds debe ser una lista numérica separada por comas."
                ) from exc
        summary = analyze_manifest(
            args.manifest, args.out, args.audit_out, args.threshold,
            sensitivity=args.sensitivity,
            sensitivity_thresholds=sensitivity_levels,
        )
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.strict and (summary["n_errors"] or summary["n_sensitivity_errors"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
