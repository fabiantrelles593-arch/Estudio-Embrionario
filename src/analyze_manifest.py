"""Analiza imágenes enumeradas en un manifiesto trazable.

El módulo combina auditoría de metadatos, carga de máscaras y métricas 2D.
No sustituye la segmentación anatómica ni verifica licencias fuera del CSV.
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
from src.image_io import load_mask
from src.metrics_2d import measure_mask, metrics_to_dict

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

    Si no se declara escala, se trabaja explícitamente en unidades de píxel.
    Si hay escala física, exige también su unidad.
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
) -> dict:
    """Analiza un manifiesto CSV y escribe una fila de salida por observación.

    Las rutas relativas de `image_path` se resuelven desde el directorio del
    manifiesto. La auditoría de metadatos es un bloqueo: no se analiza ningún
    archivo si el conjunto falla campos requeridos, identificadores, etapa,
    estado de uso o calidad. Los errores individuales de imágenes se conservan
    en la tabla resultante para no ocultar observaciones fallidas.
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
    audit_payload = audit.__dict__
    audit_path = Path(audit_json) if audit_json else Path(output_csv).with_suffix(".audit.json")
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(
        json.dumps(audit_payload, ensure_ascii=False, indent=2), encoding="utf-8"
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
            mask = load_mask(image_path, threshold=float(threshold))
            if not mask.any():
                raise ValueError(
                    "La máscara quedó vacía con este umbral; revisar imagen y segmentación."
                )
            metrics = metrics_to_dict(measure_mask(mask, pixel_size=pixel_size))
            output_rows.append({
                **metadata,
                "resolved_image_path": str(image_path.resolve()),
                "pixel_size_used": pixel_size,
                "measurement_length_unit": unit,
                "scale_status": scale_status,
                **metrics,
                "analysis_status": "OK",
                "analysis_error": "",
            })
        except (OSError, ValueError, TypeError, RuntimeError) as exc:  # preserve row-level failures
            output_rows.append({
                **metadata,
                "resolved_image_path": "",
                "pixel_size_used": np.nan,
                "measurement_length_unit": "",
                "scale_status": "not_available",
                "analysis_status": "ERROR",
                "analysis_error": f"{type(exc).__name__}: {exc}",
            })

    output = Path(output_csv)
    output.parent.mkdir(parents=True, exist_ok=True)
    results = pd.DataFrame(output_rows)
    results.to_csv(output, index=False)
    errors = int((results["analysis_status"] != "OK").sum()) if not results.empty else 0
    summary = {
        "manifest": str(manifest),
        "output_csv": str(output.resolve()),
        "audit_json": str(audit_path.resolve()),
        "audit_ok": bool(audit.ok),
        "n_rows": int(len(results)),
        "n_analyzed": int(len(results) - errors),
        "n_errors": errors,
        "threshold": float(threshold),
        "scientific_note": (
            "El estado OK solo indica que la máscara se pudo medir. No valida la "
            "exactitud anatómica de la segmentación ni una hipótesis biológica."
        ),
    }
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Mide máscaras 2D desde un CSV de metadatos auditado."
    )
    parser.add_argument("manifest", help="CSV con metadatos y columna image_path")
    parser.add_argument("--out", default="results/morphology_results.csv")
    parser.add_argument("--audit-out", default=None)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument(
        "--strict", action="store_true",
        help="Devuelve código 2 si una o más imágenes fallan; conserva el CSV de resultados.",
    )
    args = parser.parse_args(argv)
    try:
        summary = analyze_manifest(args.manifest, args.out, args.audit_out, args.threshold)
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.strict and summary["n_errors"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
