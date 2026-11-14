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


# ---------------------------------------------------------------- familia B (H16): otra familia de cadena, no un subconjunto de A

def test_family_b_sampler_is_deterministic_and_inside_its_own_declared_ranges():
    a = pc.sample_chain_b(np.random.default_rng([1, 2, 3]))
    b = pc.sample_chain_b(np.random.default_rng([1, 2, 3]))
    assert a == b and a["family"] == "B"
    assert pc.RANGES_B["gamma"][0] <= a["gamma"] <= pc.RANGES_B["gamma"][1]
    for k in ("blur_sigma_px", "noise_sd"):
        assert pc.RANGES_B[k][0] <= a[k] <= pc.RANGES_B[k][1]
    assert pc.RANGES_B["jpeg_quality"][0] <= a["jpeg_quality"] <= pc.RANGES_B["jpeg_quality"][1]
    assert abs(a["gain_slope"]) <= pc.RANGES_B["gain_slope"][1]


def test_family_b_goes_beyond_family_a_on_every_shared_axis():
    # B es un desplazamiento de familia (más desenfoque, más ruido, JPEG más duro, más gradiente), no un subconjunto de A.
    assert pc.RANGES_B["blur_sigma_px"][1] > pc.RANGES["blur_sigma_px"][1]
    assert pc.RANGES_B["noise_sd"][1] > pc.RANGES["noise_sd"][1]
    assert pc.RANGES_B["jpeg_quality"][0] < pc.RANGES["jpeg_quality"][0]
    assert pc.RANGES_B["gain_slope"][1] > pc.RANGES["gain_slope"][1]


def test_tone_b_is_monotone_with_fixed_endpoints_and_gamma_moves_the_dark_levels():
    x = np.linspace(0.0, 1.0, 201)
    for g in (0.5, 1.0, 1.6):
        t = pc.tone_b(x, g)
        assert t[0] == pytest.approx(0.0, abs=1e-9) and t[-1] == pytest.approx(1.0, abs=1e-9)
        assert np.all(np.diff(t) >= -1e-12)
    assert pc.tone_b(np.array([0.2]), 0.5)[0] > 0.2 > pc.tone_b(np.array([0.2]), 1.6)[0]


def test_tone_b_can_darken_which_no_family_a_curve_does():
    # Con gamma bajo, B se parece a una compresión logarítmica suave; lo que A nunca hace es oscurecer.
    x = np.linspace(0.05, 0.95, 19)
    assert np.all(pc.tone_b(x, 1.6) < x)
    for a in (pc.RANGES["compression_a"][0], 10.0, pc.RANGES["compression_a"][1]):
        assert np.all(np.log1p(a * x) / np.log1p(a) > x)


def test_apply_chain_dispatches_on_family_and_defaults_to_a():
    img = _img()
    a = pc.sample_chain(np.random.default_rng(7))
    assert np.array_equal(pc.apply_chain(img, a), pc.apply_chain(img, {**a, "family": "A"}))
    b = pc.sample_chain_b(np.random.default_rng(7))
    out_b = pc.apply_chain(img, b)
    assert out_b.shape == img.shape and 0.0 <= out_b.min() and out_b.max() <= 1.0
    assert np.array_equal(out_b, pc.apply_chain(img, b))
    assert not np.array_equal(out_b, pc.apply_chain(img, a))


def test_run_case_with_family_b_changes_measurement_but_not_truth():
    from geovida import biometry as bio
    clean = bio.run_case(bio.BODY, 30.0, 100, 2.0, [9, 9, 9])
    dirty = bio.run_case(bio.BODY, 30.0, 100, 2.0, [9, 9, 9], chain=pc.sample_chain_b(np.random.default_rng(3)))
    assert clean["truth_mm"] == dirty["truth_mm"] == 30.0
    assert clean["h_mm"] == dirty["h_mm"]
    # la longitud medida es múltiplo de píxel: con un segmentador puede coincidir por azar, no con los dos a la vez
    assert clean["measured_mm"] != dirty["measured_mm"]


def test_family_b_moves_the_measurement_in_most_draws():
    from geovida import biometry as bio
    clean = bio.run_case(bio.BODY, 30.0, 100, 2.0, [9, 9, 9])["measured_mm"]["smoothed_otsu"]
    moved = sum(
        bio.run_case(bio.BODY, 30.0, 100, 2.0, [9, 9, 9], chain=pc.sample_chain_b(np.random.default_rng(k)))
        ["measured_mm"]["smoothed_otsu"] != clean for k in range(8))
    assert moved >= 5
