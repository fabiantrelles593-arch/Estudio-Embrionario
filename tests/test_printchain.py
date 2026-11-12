"""Cadena pantalla → impresión → foto → JPEG (H15). Solo simulación."""
import numpy as np
import pytest

from geovida import printchain as pc


def _img(seed=0, shape=(90, 120)):
    rng = np.random.default_rng(seed)
    base = np.zeros(shape)
    base[25:65, 30:90] = 1.0
    return base + 0.3 * rng.standard_normal(shape)


def test_sample_chain_is_deterministic_and_inside_declared_ranges():
    a = pc.sample_chain(np.random.default_rng([1, 2, 3]))
    b = pc.sample_chain(np.random.default_rng([1, 2, 3]))
    assert a == b
    lo, hi = pc.RANGES["compression_a"]
    assert lo <= a["compression_a"] <= hi
    assert pc.RANGES["blur_sigma_px"][0] <= a["blur_sigma_px"] <= pc.RANGES["blur_sigma_px"][1]
    assert pc.RANGES["jpeg_quality"][0] <= a["jpeg_quality"] <= pc.RANGES["jpeg_quality"][1]
    assert abs(a["gain_slope"]) <= pc.RANGES["gain_slope"][1]


def test_apply_chain_keeps_shape_range_and_is_deterministic():
    img = _img()
    ch = pc.sample_chain(np.random.default_rng(5))
    out1, out2 = pc.apply_chain(img, ch), pc.apply_chain(img, ch)
    assert out1.shape == img.shape
    assert 0.0 <= out1.min() and out1.max() <= 1.0
    assert np.array_equal(out1, out2)


def test_compression_alone_preserves_rank_order_of_intensities():
    from scipy.stats import spearmanr
    img = _img(shape=(40, 40))
    ch = {"compression_a": 30.0, "gain_slope": 0.0, "blur_sigma_px": 0.0, "noise_sd": 0.0,
          "jpeg_quality": 100, "noise_seed": 1, "upsample": 1}
    out = pc.apply_chain(img, ch)
    assert spearmanr(img.ravel(), out.ravel()).statistic > 0.97     # empates solo por recorte y 8 bits


def test_strong_compression_lifts_dark_levels():
    img = _img(shape=(60, 60))
    weak = pc.apply_chain(img, {"compression_a": 1.0, "gain_slope": 0.0, "blur_sigma_px": 0.0,
                                "noise_sd": 0.0, "jpeg_quality": 100, "noise_seed": 1, "upsample": 1})
    strong = pc.apply_chain(img, {"compression_a": 60.0, "gain_slope": 0.0, "blur_sigma_px": 0.0,
                                  "noise_sd": 0.0, "jpeg_quality": 100, "noise_seed": 1, "upsample": 1})
    assert np.median(strong) > np.median(weak)


def test_blur_reduces_high_frequency_energy():
    img = _img(shape=(80, 80))
    base = {"compression_a": 1.0, "gain_slope": 0.0, "noise_sd": 0.0, "jpeg_quality": 100,
            "noise_seed": 1, "upsample": 3}
    sharp = pc.apply_chain(img, {**base, "blur_sigma_px": 0.0})
    soft = pc.apply_chain(img, {**base, "blur_sigma_px": 1.0})
    assert np.abs(np.diff(soft, axis=1)).mean() < np.abs(np.diff(sharp, axis=1)).mean()


def test_gain_slope_creates_a_vertical_trend():
    img = _img(shape=(80, 40))
    flat = {"compression_a": 1.0, "gain_slope": 0.0, "blur_sigma_px": 0.0, "noise_sd": 0.0,
            "jpeg_quality": 100, "noise_seed": 1, "upsample": 1}
    base = pc.apply_chain(img, flat)
    tilted = pc.apply_chain(img, {**flat, "gain_slope": 0.25})
    # con pendiente positiva las filas de abajo se aclaran y las de arriba se oscurecen
    assert (tilted[-10:].mean() - base[-10:].mean()) > 0 > (tilted[:10].mean() - base[:10].mean())


def test_run_case_with_chain_changes_measurement_but_not_truth():
    from geovida import biometry as bio
    clean = bio.run_case(bio.BODY, 30.0, 100, 2.0, [9, 9, 9])
    ch = pc.sample_chain(np.random.default_rng(3))
    dirty = bio.run_case(bio.BODY, 30.0, 100, 2.0, [9, 9, 9], chain=ch)
    assert clean["truth_mm"] == dirty["truth_mm"] == 30.0
    assert clean["h_mm"] == dirty["h_mm"]
    assert clean["measured_mm"]["smoothed_otsu"] != dirty["measured_mm"]["smoothed_otsu"]
