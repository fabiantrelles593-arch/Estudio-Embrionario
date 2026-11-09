import math

import numpy as np
import pytest

from geovida.imaging import render, spec_for_t_over_h
from geovida.measure import dice, measure_mask, relative_errors, surface_distance_stats
from geovida.phantoms import make_phantom


def _block(shape=(20, 20, 20), lo=(5, 5, 5), hi=(11, 12, 14)):
    m = np.zeros(shape, dtype=bool)
    m[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]] = True
    return m


def test_volume_is_voxel_count_times_voxel_volume():
    m = _block()
    r = measure_mask(m, (0.5, 0.5, 1.5))
    assert r["volume"] == pytest.approx(m.sum() * 0.5 * 0.5 * 1.5)


def test_face_count_area_is_exact_for_a_box():
    m = _block(lo=(5, 5, 5), hi=(8, 10, 12))  # 3 x 5 x 7 voxeles
    hx, hy, hz = 1.0, 2.0, 3.0
    r = measure_mask(m, (hx, hy, hz))
    ax, ay, az = 3 * hx, 5 * hy, 7 * hz
    expected = 2 * (ay * az + ax * az + ax * ay)
    assert r["area_faces"] == pytest.approx(expected)


def test_marching_cubes_area_of_fine_ball_is_close():
    ph = make_phantom("ball", t=1.0)
    out = render(ph, spec_for_t_over_h(24, 1.0, "ideal"), np.random.default_rng(0))
    mask = out.coverage >= 0.5
    r = measure_mask(mask, out.spacing)
    assert r["area_mc"] == pytest.approx(ph.truth.surface_area, rel=0.03)
    # el conteo de caras sobrestima de forma conocida (~ 3/2 en la esfera)
    assert r["area_faces"] > 1.3 * ph.truth.surface_area


def test_topology_is_reported_for_both_adjacencies():
    m = np.zeros((9, 9, 9), dtype=bool)
    m[2, 2, 2] = m[3, 3, 3] = True
    r = measure_mask(m, (1, 1, 1))
    assert r["b0_26"] == 1 and r["b0_6"] == 2


def test_empty_mask_gives_zeros_not_errors():
    r = measure_mask(np.zeros((6, 6, 6), dtype=bool), (1, 1, 1))
    assert r["volume"] == 0 and r["area_mc"] == 0 and r["area_faces"] == 0
    assert (r["b0_26"], r["b1_26"], r["b2_26"]) == (0, 0, 0)


def test_relative_errors_and_topology_flag():
    ph = make_phantom("shell", t=1.0)
    t = ph.truth
    meas = {"volume": t.volume * 1.04, "area_mc": t.surface_area * 0.9,
            "b0_26": 1, "b1_26": 0, "b2_26": 1, "chi_26": 2}
    e = relative_errors(meas, t)
    assert e["err_volume"] == pytest.approx(0.04)
    assert e["err_area_mc"] == pytest.approx(-0.10)
    assert e["topology_ok"] is True
    meas["b2_26"] = 0
    assert relative_errors(meas, t)["topology_ok"] is False
    assert relative_errors(meas, t)["err_b2"] == -1


def test_dice_bounds():
    a = _block()
    assert dice(a, a) == 1.0
    assert dice(a, ~a) == 0.0
    assert dice(np.zeros_like(a), np.zeros_like(a)) == 1.0


def test_surface_distance_of_shifted_block_equals_the_shift():
    a = _block(shape=(40, 40, 40), lo=(10, 10, 10), hi=(30, 30, 30))
    b = np.roll(a, 2, axis=0)
    s = surface_distance_stats(a, b, (0.5, 0.5, 0.5))
    assert s["hd95"] == pytest.approx(1.0, abs=0.25)   # 2 voxeles * 0.5
    assert surface_distance_stats(a, a, (1, 1, 1))["hd95"] == 0.0
    assert surface_distance_stats(a, a, (1, 1, 1))["msd"] == 0.0


def test_surface_distance_with_empty_mask_is_nan():
    a = _block()
    s = surface_distance_stats(a, np.zeros_like(a), (1, 1, 1))
    assert math.isnan(s["hd95"])
