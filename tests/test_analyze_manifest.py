import json
import pandas as pd
import numpy as np
import pytest
from skimage import io

from src.analyze_manifest import ManifestAuditError, analyze_manifest


def valid_row(image_path, **updates):
    row = {
        "observation_id": "OBS-001",
        "specimen_id": "SPEC-001",
        "image_id": "IMG-001",
        "stage": 12,
        "modality": "synthetic test",
        "view": "2D",
        "section_id": "synthetic",
        "source": "generated for a test",
        "asset_identifier": "local-test-image",
        "license_status": "not_applicable",
        "pixel_size": np.nan,
        "pixel_size_unit": "",
        "segmentation_method": "synthetic threshold test",
        "segmentation_operator": "automated test",
        "quality_flag": "PASS",
        "notes": "Synthetic unit test; not embryonic data.",
        "image_path": str(image_path),
    }
    row.update(updates)
    return row


def make_png(path, object_value=255):
    image = np.zeros((15, 17), dtype=np.uint8)
    image[3:9, 4:11] = object_value
    io.imsave(path, image, check_contrast=False)
    return path


def test_manifest_runs_and_preserves_provenance(tmp_path):
    image = make_png(tmp_path / "test_mask.png")
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame([valid_row(image.name, pixel_size=0.25, pixel_size_unit="mm")]).to_csv(manifest, index=False)
    output = tmp_path / "metrics.csv"

    summary = analyze_manifest(manifest, output)
    result = pd.read_csv(output).iloc[0]

    assert summary["audit_ok"] is True
    assert summary["n_analyzed"] == 1
    assert summary["n_errors"] == 0
    assert result["analysis_status"] == "OK"
    assert result["observation_id"] == "OBS-001"
    assert result["measurement_length_unit"] == "mm"
    assert result["scale_status"] == "scale_declared_in_manifest"
    assert result["area"] == pytest.approx(2.625)  # 42 pixels × 0.25²


def test_unknown_scale_is_explicitly_kept_in_pixels(tmp_path):
    image = make_png(tmp_path / "mask.png")
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame([valid_row(image.name)]).to_csv(manifest, index=False)
    output = tmp_path / "out.csv"

    summary = analyze_manifest(manifest, output)
    result = pd.read_csv(output).iloc[0]

    assert summary["n_errors"] == 0
    assert result["measurement_length_unit"] == "px"
    assert result["scale_status"] == "unknown_scale_kept_in_pixels"


def test_missing_image_is_recorded_not_silently_dropped(tmp_path):
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame([valid_row("missing.png")]).to_csv(manifest, index=False)
    output = tmp_path / "out.csv"

    summary = analyze_manifest(manifest, output)
    result = pd.read_csv(output).iloc[0]

    assert summary["n_analyzed"] == 0
    assert summary["n_errors"] == 1
    assert result["analysis_status"] == "ERROR"
    assert "No se encontró el archivo" in result["analysis_error"]


def test_audit_failure_blocks_analysis_and_saves_audit(tmp_path):
    image = make_png(tmp_path / "mask.png")
    row = valid_row(image.name, license_status="pending")
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame([row]).to_csv(manifest, index=False)
    audit = tmp_path / "audit.json"

    with pytest.raises(ManifestAuditError):
        analyze_manifest(manifest, tmp_path / "out.csv", audit_json=audit)

    assert audit.is_file()
    assert json.loads(audit.read_text(encoding="utf-8"))["ok"] is False
    assert not (tmp_path / "out.csv").exists()


def test_invalid_physical_scale_is_recorded_as_row_error(tmp_path):
    image = make_png(tmp_path / "mask.png")
    manifest = tmp_path / "manifest.csv"
    row = valid_row(image.name, pixel_size=0.0, pixel_size_unit="mm")
    pd.DataFrame([row]).to_csv(manifest, index=False)
    output = tmp_path / "out.csv"

    summary = analyze_manifest(manifest, output)
    result = pd.read_csv(output).iloc[0]

    assert summary["n_errors"] == 1
    assert result["analysis_status"] == "ERROR"
    assert "finito y positivo" in result["analysis_error"]


def test_missing_image_path_column_is_rejected(tmp_path):
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame([{"observation_id": "OBS-001"}]).to_csv(manifest, index=False)
    with pytest.raises(ValueError, match="image_path"):
        analyze_manifest(manifest, tmp_path / "out.csv")
