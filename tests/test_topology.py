"""Pruebas de topología digital con la adyacencia explícita (6,26) / (26,6).

Los casos mínimos están construidos a mano: su topología se deduce a ojo y
no depende del código bajo prueba.
"""
import numpy as np
import pytest

from geovida.topology import betti_numbers


def _empty(n=7):
    return np.zeros((n, n, n), dtype=bool)


def test_single_voxel_is_a_point_in_both_adjacencies():
    m = _empty()
    m[3, 3, 3] = True
    for conn in (6, 26):
        b = betti_numbers(m, connectivity=conn)
        assert (b.b0, b.b1, b.b2, b.chi) == (1, 0, 0, 1)


def test_corner_touching_voxels_are_one_component_in_26_but_two_in_6():
    m = _empty()
    m[2, 2, 2] = True
    m[3, 3, 3] = True
    assert betti_numbers(m, connectivity=26).b0 == 1
    assert betti_numbers(m, connectivity=6).b0 == 2


def test_diagonal_ring_is_a_loop_in_26_and_four_points_in_6():
    # Cuatro voxeles en diamante alrededor de un hueco central (plano z=3).
    m = _empty()
    for x, y in [(2, 3), (3, 2), (4, 3), (3, 4)]:
        m[x, y, 3] = True
    b26 = betti_numbers(m, connectivity=26)
    assert (b26.b0, b26.b1, b26.b2) == (1, 1, 0)
    b6 = betti_numbers(m, connectivity=6)
    assert (b6.b0, b6.b1, b6.b2) == (4, 0, 0)


def test_hollow_cube_has_one_cavity():
    m = _empty(9)
    m[2:7, 2:7, 2:7] = True
    m[3:6, 3:6, 3:6] = False
    for conn in (6, 26):
        b = betti_numbers(m, connectivity=conn)
        assert (b.b0, b.b1, b.b2, b.chi) == (1, 0, 1, 2)


def test_square_frame_has_one_tunnel():
    m = _empty(9)
    m[2:7, 2:7, 4] = True
    m[3:6, 3:6, 4] = False  # marco plano de 1 voxel de espesor
    for conn in (6, 26):
        b = betti_numbers(m, connectivity=conn)
        assert (b.b0, b.b1, b.b2, b.chi) == (1, 1, 0, 0)


def test_object_touching_array_border_is_still_closed():
    m = np.ones((4, 4, 4), dtype=bool)
    for conn in (6, 26):
        b = betti_numbers(m, connectivity=conn)
        assert (b.b0, b.b1, b.b2, b.chi) == (1, 0, 0, 1)


def test_empty_image_has_no_topology():
    b = betti_numbers(_empty(), connectivity=26)
    assert (b.b0, b.b1, b.b2, b.chi) == (0, 0, 0, 0)


def test_two_nested_shells_count_two_cavities():
    m = _empty(15)
    m[1:14, 1:14, 1:14] = True
    m[2:13, 2:13, 2:13] = False   # cavidad grande
    m[4:11, 4:11, 4:11] = True    # cáscara interior
    m[6:9, 6:9, 6:9] = False      # cavidad pequeña
    b = betti_numbers(m, connectivity=26)
    assert (b.b0, b.b1, b.b2) == (2, 0, 2)


def test_invalid_connectivity_is_rejected():
    with pytest.raises(ValueError):
        betti_numbers(_empty(), connectivity=18)


def test_non_3d_input_is_rejected():
    with pytest.raises(ValueError):
        betti_numbers(np.zeros((5, 5), dtype=bool), connectivity=26)
