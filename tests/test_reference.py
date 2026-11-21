"""Estimadores de referencia independientes: casos construidos a mano y fantomas analíticos."""
import math

import numpy as np
import pytest

from geovida import reference as ref
from geovida.phantoms import make_phantom
from geovida.topology import betti_numbers


def _cube(n=3):
    return np.ones((n, n, n), bool)


def test_single_voxel_and_solid_cube_have_chi_one():
    assert ref.euler_cubical(np.ones((1, 1, 1), bool), 26) == 1
    assert ref.euler_cubical(np.ones((1, 1, 1), bool), 6) == 1
    assert ref.euler_cubical(_cube(4), 26) == 1 and ref.euler_cubical(_cube(4), 6) == 1


def test_hollow_cube_has_cavity_chi_two():
    m = _cube(5)
    m[2, 2, 2] = False
    assert ref.euler_cubical(m, 26) == 2
    assert ref.euler_cubical(m, 6) == 2


def test_square_ring_has_tunnel_chi_zero():
    m = np.zeros((1, 3, 3), bool)
    m[0] = True
    m[0, 1, 1] = False
    assert ref.euler_cubical(m, 26) == 0 and ref.euler_cubical(m, 6) == 0


def test_diagonal_voxels_depend_on_connectivity():
    m = np.zeros((2, 2, 2), bool)
    m[0, 0, 0] = m[1, 1, 1] = True
    assert ref.euler_cubical(m, 26) == 1   # un solo componente (comparten un vértice)
    assert ref.euler_cubical(m, 6) == 2    # dos componentes


def test_empty_mask():
    z = np.zeros((3, 3, 3), bool)
    assert ref.euler_cubical(z) == 0 and ref.crofton_area(z, (1, 1, 1)) == 0.0


@pytest.mark.parametrize("conn", [6, 26])
def test_chi_agrees_with_topology_module_on_random_masks(conn):
    rng = np.random.default_rng(0)
    for _ in range(20):
        m = rng.random((7, 8, 9)) < 0.45
        assert ref.euler_cubical(m, conn) == betti_numbers(m, conn).chi


def test_crofton_weights_sum_to_one_and_are_symmetric_for_isotropic_voxels():
    w = np.array(ref.crofton_weights((1.0, 1.0, 1.0)))
    assert abs(w.sum() - 1) < 1e-12
    axes = [w[ref.DIRECTIONS.index(d)] for d in ((0, 0, 1), (0, 1, 0), (1, 0, 0))]
    assert max(axes) - min(axes) < 2e-3


def test_crofton_area_of_a_large_ball_is_close_to_analytic():
    ph = make_phantom("ball", 40.0)
    mask, sp = ref.voxelize(ph, 1.0)
    a = ref.crofton_area(mask, sp)
    assert abs(a / ph.truth.surface_area - 1) < 0.03


def test_crofton_area_handles_anisotropic_voxels():
    ph = make_phantom("ball", 40.0)
    mask, sp = ref.voxelize(ph, 1.0, spacing_ratio=(2.0, 1.0, 1.0))
    a = ref.crofton_area(mask, sp)
    assert abs(a / ph.truth.surface_area - 1) < 0.04


def test_voxelize_volume_converges():
    ph = make_phantom("ball", 30.0)
    mask, sp = ref.voxelize(ph, 0.75)
    v = mask.sum() * math.prod(sp)
    assert abs(v / ph.truth.volume - 1) < 0.01
