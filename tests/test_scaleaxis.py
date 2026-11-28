"""Eje de escala de medición (v0.4): volver a medir la misma imagen degradada
×2 y ×4 (promedio de bloques + el mismo segmentador) y mirar cuánto cambia."""
import math

import numpy as np
import pytest

from geovida.imaging import render, spec_for_t_over_h
from geovida.phantoms import make_phantom
from geovida.scaleaxis import DRIFT_CAP, block_mean, pyramid_levels, scale_observables
from geovida.segment import segment


def _image(shape="ball", t_over_h=12.0, profile="ideal", seed=0, anisotropy=1.0):
    ph = make_phantom(shape, t=1.0)
    return render(ph, spec_for_t_over_h(t_over_h, anisotropy, profile), np.random.default_rng(seed))


def test_block_mean_preserves_the_mean_and_halves_even_shapes():
    a = np.arange(4 * 6 * 8, dtype=float).reshape(4, 6, 8)
    b = block_mean(a)
    assert b.shape == (2, 3, 4) and b.mean() == pytest.approx(a.mean())
    assert b[0, 0, 0] == pytest.approx(a[:2, :2, :2].mean())


def test_block_mean_crops_odd_sizes():
    assert block_mean(np.ones((5, 7, 9))).shape == (2, 3, 4)


def test_pyramid_doubles_the_spacing_at_each_level():
    out = _image()
    levels = pyramid_levels(out.image, out.spacing, "global")
    assert [lv["factor"] for lv in levels] == [1, 2, 4]
    assert levels[1]["spacing"] == pytest.approx(tuple(2 * s for s in out.spacing))
    assert levels[2]["spacing"] == pytest.approx(tuple(4 * s for s in out.spacing))


def test_native_level_reuses_the_given_mask():
    out = _image()
    mask = segment("otsu", out.image, out.spacing)
    lv0 = pyramid_levels(out.image, out.spacing, "otsu", mask0=mask)[0]
    assert lv0["volume"] == pytest.approx(mask.sum() * np.prod(out.spacing))


def test_volume_is_stable_across_scales_for_a_well_resolved_ball():
    out = _image(t_over_h=16.0)
    obs = scale_observables(out.image, out.spacing, "global")
    assert obs["u_v1"] < 0.05 and obs["a1"] == 1.0


def test_volume_drifts_when_the_ball_is_barely_resolved():
    out = _image(t_over_h=2.0)
    obs = scale_observables(out.image, out.spacing, "global")
    assert obs["u_v2"] > 0.2


def test_drift_is_capped_when_the_object_vanishes_at_a_coarser_scale():
    # Bola de 3 vóxeles: a ×4 ocupa 0.75 vóxeles y el umbral 0.5 ya no la ve.
    out = _image(t_over_h=3.0, seed=3)
    obs = scale_observables(out.image, out.spacing, "global")
    assert obs["dv2"] == -DRIFT_CAP and obs["u_v2"] == DRIFT_CAP and obs["a2"] == 0.0


def test_topology_agreement_flags_a_feature_lost_at_the_coarser_scale():
    out = _image(shape="torus_tight", t_over_h=4.0)   # hueco de 2 vóxeles: se pierde al degradar
    mask = segment("global", out.image, out.spacing)
    obs = scale_observables(out.image, out.spacing, "global", mask0=mask)
    assert obs["a1"] == 0.0 or obs["a2"] == 0.0


def test_observables_are_nan_for_an_empty_native_mask():
    img = np.zeros((8, 8, 8), np.float32)
    obs = scale_observables(img, (1.0, 1.0, 1.0), "global")
    assert all(math.isnan(obs[k]) for k in ("dv1", "dv2", "u_v1", "u_v2"))
    assert obs["a1"] == 0.0 and obs["a2"] == 0.0


def test_keys_are_the_documented_ones():
    out = _image(t_over_h=6.0)
    assert set(scale_observables(out.image, out.spacing, "smoothed_otsu")) == {
        "dv1", "dv2", "u_v1", "u_v2", "a1", "a2"}
