import numpy as np
import pytest

from src.advanced_morphology import analyze_threshold_sensitivity, hu_invariant_features


def _ellipse(height=25, width=31):
    y, x = np.ogrid[:height, :width]
    return ((y - 12) / 8) ** 2 + ((x - 15) / 10) ** 2 <= 1


def test_hu_feature_vector_has_seven_raw_and_log_descriptors():
    result = hu_invariant_features(_ellipse())
    assert len([k for k in result if k.startswith("hu_") and not k.startswith("hu_log_")]) == 7
    assert len([k for k in result if k.startswith("hu_log_")]) == 7
    assert all(np.isfinite(value) for value in result.values())


def test_hu_invariants_are_stable_under_translation():
    shape = _ellipse()
    first = np.zeros((80, 90), dtype=bool)
    second = np.zeros((80, 90), dtype=bool)
    first[5:30, 7:38] = shape
    second[37:62, 40:71] = shape
    a, b = hu_invariant_features(first), hu_invariant_features(second)
    for i in range(1, 8):
        assert a[f"hu_{i}"] == pytest.approx(b[f"hu_{i}"], rel=1e-8, abs=1e-12)


def test_hu_invariants_are_stable_under_right_angle_rotation():
    shape = _ellipse()
    a, b = hu_invariant_features(shape), hu_invariant_features(np.rot90(shape))
    for i in range(1, 8):
        assert a[f"hu_{i}"] == pytest.approx(b[f"hu_{i}"], rel=1e-6, abs=1e-12)


def test_hu_moments_use_largest_component_consistently():
    shape = _ellipse()
    noisy = np.zeros((60, 70), dtype=bool)
    noisy[3:28, 4:35] = shape
    noisy[50, 60] = True
    baseline, result = hu_invariant_features(shape), hu_invariant_features(noisy)
    for i in range(1, 8):
        assert result[f"hu_{i}"] == pytest.approx(baseline[f"hu_{i}"], rel=1e-8, abs=1e-12)


def test_stable_threshold_sweep_returns_index_100():
    gray = np.zeros((40, 50), dtype=float) + 0.1
    gray[8:30, 10:38] = 0.9
    summary = analyze_threshold_sensitivity(gray, (0.2, 0.35, 0.5, 0.65, 0.8))["summary"]
    assert summary["thresholds_valid"] == 5
    assert summary["thresholds_failed"] == 0
    assert summary["topology_states"] == 1
    assert summary["topology_stability"] == 1.0
    assert summary["robustness_index"] == pytest.approx(100.0)
    assert not summary["flags"]


def test_threshold_sweep_reports_empty_masks_and_low_valid_count():
    gray = np.zeros((20, 20), dtype=float)
    gray[5:15, 5:15] = 0.5
    summary = analyze_threshold_sensitivity(gray, (0.1, 0.3, 0.6, 0.8, 0.95))["summary"]
    assert summary["thresholds_valid"] == 2
    assert summary["thresholds_failed"] == 3
    assert "AT_LEAST_ONE_THRESHOLD_FAILED" in summary["flags"]
    assert "INSUFFICIENT_VALID_THRESHOLDS" in summary["flags"]
    assert summary["robustness_index"] is None


@pytest.mark.parametrize(
    "levels",
    [(0.2, 0.5), (0.2, 0.2, 0.8), (-0.1, 0.4, 0.8), (0.1, float("nan"), 0.9)],
)
def test_invalid_threshold_grids_are_rejected(levels):
    with pytest.raises(ValueError):
        analyze_threshold_sensitivity(_ellipse().astype(float), thresholds=levels)


def test_invalid_image_range_is_rejected():
    gray = np.zeros((10, 10), dtype=float)
    gray[1, 1] = 1.5
    with pytest.raises(ValueError):
        analyze_threshold_sensitivity(gray)
