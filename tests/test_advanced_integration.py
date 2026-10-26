import numpy as np
import pandas as pd
import pytest
from skimage import io

from src.analyze_manifest import analyze_manifest, main


def valid_row(image_path):
    return {
        "observation_id": "ADV-001",
        "specimen_id": "ADV-S1",
        "image_id": "ADV-I1",
        "stage": 12,
        "modality": "synthetic test",
        "view": "2D",
        "section_id": "synthetic",
        "source": "generated for a unit test",
        "asset_identifier": "local-mask",
        "license_status": "not_applicable",
        "pixel_size": np.nan,
        "pixel_size_unit": "",
        "segmentation_method": "binary synthetic mask",
        "segmentation_operator": "test",
        "quality_flag": "PASS",
        "notes": "Synthetic unit test; not embryonic data.",
        "image_path": str(image_path),
    }


def make_manifest(tmp_path):
    image = tmp_path / "mask.png"
    pixels = np.zeros((30, 30), dtype=np.uint8)
    pixels[6:23, 7:25] = 240
    io.imsave(image, pixels, check_contrast=False)
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame([valid_row(image.name)]).to_csv(manifest, index=False)
    return manifest


def test_advanced_manifest_adds_hu_and_robustness_metrics(tmp_path):
    manifest = make_manifest(tmp_path)
    output = tmp_path / "advanced.csv"
    summary = analyze_manifest(
        manifest, output, sensitivity=True,
        sensitivity_thresholds=(0.2, 0.35, 0.5, 0.65, 0.8),
    )
    result = pd.read_csv(output).iloc[0]
    assert summary["n_errors"] == 0
    assert summary["sensitivity_enabled"] is True
    assert result["analysis_status"] == "OK"
    assert result["sensitivity_status"] == "OK"
    assert result["topology_stability"] == pytest.approx(1.0)
    assert result["robustness_index"] == pytest.approx(100.0)
    assert np.isfinite(result["hu_1"])
    assert np.isfinite(result["hu_log_1"])
    assert result["thresholds_attempted"] == 5
    assert result["thresholds_valid"] == 5
    assert result["thresholds_failed"] == 0
    assert isinstance(result["threshold_sensitivity_json"], str)


def test_strict_mode_fails_when_sensitivity_profile_has_invalid_thresholds(tmp_path, capsys):
    manifest = make_manifest(tmp_path)
    output = tmp_path / "advanced.csv"
    code = main([
        str(manifest), "--out", str(output), "--sensitivity", "--strict",
        "--sensitivity-thresholds", "0.2,0.2,0.8",
    ])
    result = pd.read_csv(output).iloc[0]
    assert code == 2
    assert result["analysis_status"] == "OK"
    assert result["sensitivity_status"] == "ERROR"
    assert "únicos" in result["sensitivity_error"]
    assert capsys.readouterr().out.strip()
