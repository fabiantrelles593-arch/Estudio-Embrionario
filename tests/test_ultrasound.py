"""Pruebas del simulador de ecografía 3D (H12): moteado (speckle), atenuación y fondo no nulo.

Cada prueba nombra el cambio de producción que la haría fallar:
* si el moteado dejara de ser multiplicativo con media 1, el contraste no seguiría 1/sqrt(looks);
* si la atenuación dependiera del azar o no fuera monótona, el cociente imagen/sin-atenuación
  dejaría de ser exp(-atten·z);
* si los perfiles de ecografía alteraran los índices de semilla, las tablas de v0.1-v0.4 cambiarían.
"""
import hashlib

import numpy as np
import pytest
from scipy import ndimage as ndi

from geovida import experiment
from geovida.imaging import (ImagingSpec, IMAGING_PROFILES, SHIFTED_PROFILES, ULTRASOUND_PROFILES,
                             ULTRASOUND_SHIFTED_PROFILES, render, spec_for_t_over_h)
from geovida.phantoms import make_phantom

# --- Huellas del simulador antiguo (calculadas antes de tocar imaging.py) -----------------------
LEGACY_HASHES = {"ideal": "783f900c2a5630af", "realistic": "81835140b60c10c7",
                 "blurry": "9f4145e6e194891a"}


@pytest.mark.parametrize("profile", sorted(LEGACY_HASHES))
def test_legacy_profiles_render_bit_identical(profile):
    spec = spec_for_t_over_h(8.0, 1.0, profile)
    r = render(make_phantom("ball", t=1.0), spec, np.random.default_rng(123))
    assert hashlib.sha256(r.image.tobytes()).hexdigest()[:16] == LEGACY_HASHES[profile]


def test_seed_profile_indices_of_old_profiles_are_unchanged():
    old = ("ideal", "realistic", "blurry", "noisy", "mild_blur", "mild_noise")
    assert experiment._SEED_PROFILES[: len(old)] == old
    for name in list(ULTRASOUND_PROFILES) + list(ULTRASOUND_SHIFTED_PROFILES):
        assert name in experiment._SEED_PROFILES[len(old):]


# --- Validación --------------------------------------------------------------------------------
@pytest.mark.parametrize("kw", [{"looks": -1}, {"looks": 2, "grain_fwhm": 0.0},
                                {"atten": -0.1}, {"bg_level": -0.01}, {"bg_level": 1.0}])
def test_invalid_ultrasound_parameters_raise(kw):
    with pytest.raises(ValueError):
        ImagingSpec(h_xy=0.1, **kw)


def test_ultrasound_profiles_are_known_and_distinct_from_old_ones():
    assert not set(ULTRASOUND_PROFILES) & set(IMAGING_PROFILES)
    assert not set(ULTRASOUND_SHIFTED_PROFILES) & set(SHIFTED_PROFILES)
    for name in {**ULTRASOUND_PROFILES, **ULTRASOUND_SHIFTED_PROFILES}:
        spec = spec_for_t_over_h(12.0, 1.0, name)
        assert spec.looks >= 1 and spec.grain_fwhm > 0


# --- Moteado -----------------------------------------------------------------------------------
def _interior_values(image, coverage, erode=4):
    inner = ndi.binary_erosion(coverage >= 1.0, iterations=erode)
    return image[inner]


@pytest.mark.parametrize("looks,expected", [(1, 1.0), (4, 0.5), (16, 0.25)])
def test_speckle_contrast_follows_one_over_sqrt_looks(looks, expected):
    spec = ImagingSpec(h_xy=1.0 / 40, looks=looks, grain_fwhm=1.5)
    r = render(make_phantom("ball", t=1.0), spec, np.random.default_rng(7))
    vals = _interior_values(r.image, r.coverage)
    assert vals.size > 5000
    assert vals.mean() == pytest.approx(1.0, rel=0.08)
    assert vals.std() / vals.mean() == pytest.approx(expected, rel=0.15)


def test_speckle_is_spatially_correlated_at_the_grain_scale():
    fine = ImagingSpec(h_xy=1.0 / 40, looks=1, grain_fwhm=1.0)
    coarse = ImagingSpec(h_xy=1.0 / 40, looks=1, grain_fwhm=3.0)
    ph = make_phantom("ball", t=1.0)

    def lag1(spec):
        r = render(ph, spec, np.random.default_rng(3))
        inner = ndi.binary_erosion(r.coverage >= 1.0, iterations=4)
        a = r.image[:-1, :, :][inner[:-1] & inner[1:]]
        b = r.image[1:, :, :][inner[:-1] & inner[1:]]
        return float(np.corrcoef(a, b)[0, 1])

    assert lag1(coarse) > lag1(fine) + 0.15


def test_speckle_render_is_deterministic_for_a_seed_and_differs_between_seeds():
    spec = ImagingSpec(h_xy=1.0 / 16, looks=3, grain_fwhm=1.5, psf_fwhm=1.0)
    ph = make_phantom("ball", t=1.0)
    a = render(ph, spec, np.random.default_rng(5)).image
    b = render(ph, spec, np.random.default_rng(5)).image
    c = render(ph, spec, np.random.default_rng(6)).image
    assert a.dtype == np.float32
    assert np.array_equal(a, b)
    assert a.shape != c.shape or not np.array_equal(a, c)


# --- Atenuación y fondo ------------------------------------------------------------------------
def test_attenuation_multiplies_image_by_exp_minus_atten_times_depth_fraction():
    ph = make_phantom("ball", t=1.0)
    base = render(ph, ImagingSpec(h_xy=1.0 / 16, bg_level=0.1), np.random.default_rng(9)).image
    att = render(ph, ImagingSpec(h_xy=1.0 / 16, bg_level=0.1, atten=0.8),
                 np.random.default_rng(9)).image
    assert att.shape == base.shape
    ratio_profile = (att.sum(axis=(0, 1)) / base.sum(axis=(0, 1)))
    assert ratio_profile[0] == pytest.approx(1.0, abs=1e-6)
    assert ratio_profile[-1] == pytest.approx(np.exp(-0.8), abs=1e-5)
    assert np.all(np.diff(ratio_profile) < 0)


def test_attenuation_does_not_consume_random_numbers():
    ph = make_phantom("ball", t=1.0)
    r1, r2 = np.random.default_rng(11), np.random.default_rng(11)
    render(ph, ImagingSpec(h_xy=1.0 / 16, snr=10.0), r1)
    render(ph, ImagingSpec(h_xy=1.0 / 16, snr=10.0, atten=1.0), r2)
    assert r1.random() == r2.random()


def test_background_level_lifts_the_empty_region_and_keeps_object_at_one():
    ph = make_phantom("ball", t=1.0)
    r = render(ph, ImagingSpec(h_xy=1.0 / 16, bg_level=0.2), np.random.default_rng(2))
    assert r.image.min() == pytest.approx(0.2, abs=1e-6)
    assert r.image.max() == pytest.approx(1.0, abs=1e-6)


def test_ultrasound_profile_renders_with_visible_speckle_and_attenuation():
    spec = spec_for_t_over_h(24.0, 1.0, "us_compound")
    r = render(make_phantom("ball", t=1.0), spec, np.random.default_rng(4))
    vals = _interior_values(r.image, r.coverage, erode=3)
    assert vals.size > 1000
    assert vals.std() / vals.mean() > 0.2          # moteado visible
    assert r.image.min() >= 0.0 or spec.snr is not None
