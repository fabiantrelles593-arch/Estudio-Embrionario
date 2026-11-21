"""Renderizado de fantomas a imágenes con volumen parcial, anisotropía, PSF y ruido."""
import numpy as np
import pytest

from geovida.imaging import IMAGING_PROFILES, ImagingSpec, render, spec_for_t_over_h
from geovida.phantoms import PHANTOM_NAMES, make_phantom


def _voxel_volume(spacing):
    return float(np.prod(spacing))


@pytest.mark.parametrize("name", PHANTOM_NAMES)
@pytest.mark.parametrize("aniso", [1.0, 2.0])
def test_partial_volume_integrates_to_analytic_volume(name, aniso):
    ph = make_phantom(name, t=1.0)
    spec = spec_for_t_over_h(t_over_h=10, anisotropy=aniso, profile="ideal")
    out = render(ph, spec, np.random.default_rng(3))
    vol = out.coverage.sum() * _voxel_volume(out.spacing)
    assert vol == pytest.approx(ph.truth.volume, rel=0.02)


def test_spacing_follows_anisotropy():
    spec = spec_for_t_over_h(t_over_h=4, anisotropy=3.0, profile="ideal", t=2.0)
    assert spec.h_xy == pytest.approx(0.5)
    assert spec.spacing == pytest.approx((0.5, 0.5, 1.5))


@pytest.mark.parametrize("name", ["tube", "torus", "ellipsoid"])
def test_object_is_never_clipped_by_the_grid(name):
    ph = make_phantom(name, t=1.0)
    spec = spec_for_t_over_h(t_over_h=6, anisotropy=2.0, profile="realistic")
    for seed in range(15):
        out = render(ph, spec, np.random.default_rng(seed))
        c = out.coverage
        assert c[0].sum() == 0 and c[-1].sum() == 0
        assert c[:, 0].sum() == 0 and c[:, -1].sum() == 0
        assert c[:, :, 0].sum() == 0 and c[:, :, -1].sum() == 0


def test_rendering_is_deterministic_per_seed_and_varies_across_seeds():
    ph = make_phantom("ellipsoid", t=1.0)
    spec = spec_for_t_over_h(5, 1.0, "realistic")
    a = render(ph, spec, np.random.default_rng(7))
    b = render(ph, spec, np.random.default_rng(7))
    c = render(ph, spec, np.random.default_rng(8))
    assert np.array_equal(a.image, b.image)
    assert a.image.shape != c.image.shape or not np.allclose(a.image, c.image)


def test_ideal_profile_has_no_noise_and_no_blur():
    ph = make_phantom("ball", t=1.0)
    spec = spec_for_t_over_h(8, 1.0, "ideal")
    out = render(ph, spec, np.random.default_rng(0))
    assert np.allclose(out.image, out.coverage)


def test_noise_level_matches_snr_in_the_background():
    ph = make_phantom("ball", t=1.0)
    spec = ImagingSpec(h_xy=0.1, anisotropy=1.0, psf_fwhm=0.0, snr=5.0)
    out = render(ph, spec, np.random.default_rng(1))
    bg = out.image[out.coverage == 0]
    assert bg.std() == pytest.approx(1 / 5.0, rel=0.05)
    assert bg.mean() == pytest.approx(0.0, abs=0.01)


def test_psf_blurs_but_conserves_total_intensity():
    ph = make_phantom("ball", t=1.0)
    ideal = ImagingSpec(h_xy=0.25, psf_fwhm=0.0, snr=None)
    blur = ImagingSpec(h_xy=0.25, psf_fwhm=2.0, snr=None)
    a = render(ph, ideal, np.random.default_rng(0))
    b = render(ph, blur, np.random.default_rng(0))
    assert b.image.max() < a.image.max()
    assert b.image.sum() == pytest.approx(a.image.sum(), rel=1e-3)


def test_profiles_are_declared():
    assert set(IMAGING_PROFILES) == {"ideal", "realistic"}
    assert IMAGING_PROFILES["ideal"]["snr"] is None


def test_invalid_specs_are_rejected():
    with pytest.raises(ValueError):
        ImagingSpec(h_xy=0.0)
    with pytest.raises(ValueError):
        ImagingSpec(h_xy=1.0, anisotropy=0.5)
    with pytest.raises(ValueError):
        spec_for_t_over_h(4, 1.0, "no_existe")
