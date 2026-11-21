"""Módulo 2D: fantomas con verdad exacta, imagen tipo ecografía (moteado) y medidas.

Las tolerancias de perímetro salen de una exploración previa con discos de
radio 4 a 30 px (conteo Crofton de 4 direcciones: -1.4 % a +0.8 %; contorno de
distancia con signo: +2 a +3 %); ver docs/PREREGISTRO_2D.md.
"""
import math

import numpy as np
import pytest
from scipy import integrate, ndimage as ndi

from geovida.twod import (
    PHANTOMS_2D, PROFILES_2D, SEGMENTERS_2D, Condition2D, betti_2d, make_phantom2d,
    measure_mask_2d, render2d, run_condition_2d, segment2d, spec2d_for,
)


def test_disk_truth_is_closed_form():
    tr = make_phantom2d("disk", t=2.0).truth  # radio 1
    assert tr.area == pytest.approx(math.pi) and tr.perimeter == pytest.approx(2 * math.pi)
    assert tr.outer_perimeter == pytest.approx(2 * math.pi)
    assert tr.betti == (1, 0) and tr.chi == 1


def test_ellipse_perimeter_matches_independent_quadrature():
    ph = make_phantom2d("ellipse", t=2.0)  # b = 1, a = 1.25
    a, b = 1.25, 1.0
    ref, _ = integrate.quad(lambda u: math.hypot(a * math.sin(u), b * math.cos(u)), 0, 2 * math.pi,
                            epsabs=1e-12)
    assert ph.truth.perimeter == pytest.approx(ref, rel=1e-9)
    assert ph.truth.area == pytest.approx(math.pi * a * b)
    assert ph.truth.t_solid == pytest.approx(2.0)


def test_annulus_truth_has_one_hole_and_two_boundaries():
    ph = make_phantom2d("annulus", t=1.0)  # ancho t, diametro interior 3t -> ri = 1.5, ro = 2.5
    assert ph.truth.betti == (1, 1) and ph.truth.chi == 0
    assert ph.truth.area == pytest.approx(math.pi * (2.5**2 - 1.5**2))
    assert ph.truth.perimeter == pytest.approx(2 * math.pi * 4.0)
    assert ph.truth.outer_perimeter == pytest.approx(2 * math.pi * 2.5)
    assert ph.truth.t_void == pytest.approx(3.0) and ph.truth.t_min == pytest.approx(1.0)


def test_invalid_phantom_or_size_is_rejected():
    with pytest.raises(ValueError):
        make_phantom2d("hexagon", 1.0)
    with pytest.raises(ValueError):
        make_phantom2d("disk", 0.0)


@pytest.mark.parametrize("name", PHANTOMS_2D)
def test_ideal_coverage_integrates_to_the_true_area(name):
    ph = make_phantom2d(name, t=1.0)
    out = render2d(ph, spec2d_for(16.0, "ideal"), np.random.default_rng(0))
    assert out.coverage.sum() * out.spacing**2 == pytest.approx(ph.truth.area, rel=0.01)


def test_rendering_is_deterministic_per_seed_and_varies_across_seeds():
    ph = make_phantom2d("ellipse", 1.0)
    spec = spec2d_for(8.0, "us_compound")
    a = render2d(ph, spec, np.random.default_rng(3)).image
    b = render2d(ph, spec, np.random.default_rng(3)).image
    c = render2d(ph, spec, np.random.default_rng(4)).image
    assert np.array_equal(a, b) and not np.array_equal(a, c)


def test_speckle_statistics_follow_the_number_of_looks():
    ph = make_phantom2d("disk", 1.0)
    delta = 0.75  # la imagen se normaliza por (1 - fondo): cv_imagen = cv_moteado / 0.75
    for profile, cv_speckle in (("us_raw", 1.0), ("us_compound", 0.5)):
        out = render2d(ph, spec2d_for(120.0, profile), np.random.default_rng(1))
        core = ndi.binary_erosion(out.coverage > 0.999, iterations=6)
        vals = out.image[core]
        assert vals.std() / vals.mean() == pytest.approx(cv_speckle / delta, rel=0.15)


def test_ideal_profile_is_a_clean_two_level_image():
    ph = make_phantom2d("disk", 1.0)
    out = render2d(ph, spec2d_for(10.0, "ideal"), np.random.default_rng(0))
    assert out.image.min() == pytest.approx(0.0) and out.image.max() == pytest.approx(1.0)


def test_betti_2d_ring_hole_and_diagonal_pairs():
    ring = np.zeros((12, 12), bool)
    ring[2:10, 2:10] = True
    ring[4:8, 4:8] = False
    assert betti_2d(ring).as_tuple() == (1, 1)
    diag = np.zeros((4, 4), bool)
    diag[0, 0] = diag[1, 1] = True
    assert betti_2d(diag, fg_connectivity=8).as_tuple() == (1, 0)
    assert betti_2d(diag, fg_connectivity=4).as_tuple() == (2, 0)
    assert betti_2d(np.zeros((5, 5), bool)).as_tuple() == (0, 0)


def test_measure_mask_of_a_fine_disk_matches_the_truth():
    ph = make_phantom2d("disk", t=30.0)  # radio 15 px con h = 1
    n = 80
    yy, xx = np.mgrid[:n, :n]
    mask = (yy - (n - 1) / 2 + 0.2) ** 2 + (xx - (n - 1) / 2 - 0.1) ** 2 <= 15.0**2
    r = measure_mask_2d(mask, spacing=1.0)
    assert r["area"] == pytest.approx(ph.truth.area, rel=0.02)
    assert r["perim_crofton"] == pytest.approx(ph.truth.perimeter, rel=0.015)
    assert r["hc_ellipse"] == pytest.approx(ph.truth.outer_perimeter, rel=0.015)
    assert (r["b0"], r["b1"]) == (1, 0)


def test_measure_of_an_empty_mask_is_zeros_not_errors():
    r = measure_mask_2d(np.zeros((6, 6), bool), spacing=1.0)
    assert r["area"] == 0.0 and r["hc_ellipse"] == 0.0 and (r["b0"], r["b1"]) == (0, 0)


def test_registries_are_declared():
    assert set(PHANTOMS_2D) == {"disk", "ellipse", "annulus"}
    assert set(PROFILES_2D) == {"ideal", "us_compound", "us_raw"}
    assert set(SEGMENTERS_2D) == {"global", "otsu", "smoothed_otsu", "smoothed_otsu_s2"}


def test_oracle_threshold_recovers_the_ideal_disk():
    ph = make_phantom2d("disk", 1.0)
    out = render2d(ph, spec2d_for(20.0, "ideal"), np.random.default_rng(0))
    mask = segment2d("global", out.image, out.spacing)
    assert mask.sum() * out.spacing**2 == pytest.approx(ph.truth.area, rel=0.02)


def test_run_condition_2d_is_deterministic_and_complete():
    c = Condition2D("annulus", 8.0, "us_compound", 2)
    a, b = run_condition_2d(c), run_condition_2d(c)
    assert a == b
    assert [r["segmenter"] for r in a] == list(SEGMENTERS_2D)
    need = {"shape", "t_over_h", "profile", "rep", "err_area", "err_perim_crofton",
            "err_hc", "topology_ok", "t_min_over_h"}
    assert need <= set(a[0])
