"""v0.4: dos fantomas no convexos con verdad analítica, reservados como formas
NUNCA vistas en la calibración del certificado.

* ``dumbbell`` (mancuerna): dos bolas unidas por un cuello delgado. El volumen
  lo dominan las bolas; la topología (un solo componente) depende del cuello.
* ``cup`` (copa): semicáscara esférica abierta de pared delgada (rasgo laminar),
  con topología trivial (1, 0, 0).

Cada verdad se contrasta con una rasterización fina independiente, como en
``test_phantoms.py``.
"""
import math

import numpy as np
import pytest
from scipy import ndimage as ndi
from skimage.measure import marching_cubes, mesh_surface_area

from geovida.experiment import ALL_SHAPES
from geovida.phantoms import EXTRA_NAMES, NEW_NAMES, PHANTOM_NAMES, make_phantom
from geovida.topology import betti_numbers


def _fine_grid(ph, voxels_per_t, seed=0):
    h = ph.t / voxels_per_t
    hx = np.array(ph.half_extent) + 2 * h
    shift = np.random.default_rng(seed).uniform(-0.5, 0.5, size=3) * h
    axes = [np.arange(-e, e + h, h) + s for e, s in zip(hx, shift)]
    pts = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1)
    return ph.contains(pts), h


def test_new_names_are_registered_without_moving_old_indices():
    assert NEW_NAMES == ("dumbbell", "cup")
    # Las semillas de H1, H3, H6 y H8 dependen de este orden: no puede cambiar.
    assert ALL_SHAPES[:10] == PHANTOM_NAMES + EXTRA_NAMES
    assert ALL_SHAPES[10:] == NEW_NAMES


def test_dumbbell_truth_is_closed_form():
    ph = make_phantom("dumbbell", t=1.0)  # cuello de diámetro 1 (r = 0.5), bolas R = 2, cuello libre 1.5
    r, big_r, l_out = 0.5, 2.0, 1.5
    cap = big_r - math.sqrt(big_r**2 - r**2)
    vol = 2 * 4 / 3 * math.pi * big_r**3 + math.pi * r**2 * l_out
    area = 2 * (4 * math.pi * big_r**2 - 2 * math.pi * big_r * cap) + 2 * math.pi * r * l_out
    assert ph.truth.volume == pytest.approx(vol)
    assert ph.truth.surface_area == pytest.approx(area)
    assert ph.truth.betti == (1, 0, 0) and ph.truth.chi == 1
    assert ph.truth.t_solid == pytest.approx(1.0) and math.isinf(ph.truth.t_void)


def test_cup_truth_is_closed_form():
    ph = make_phantom("cup", t=1.0)  # pared t = 1; Ri = 1.5, Ro = 2.5
    ri, ro = 1.5, 2.5
    assert ph.truth.volume == pytest.approx(2 / 3 * math.pi * (ro**3 - ri**3))
    assert ph.truth.surface_area == pytest.approx(
        2 * math.pi * (ro**2 + ri**2) + math.pi * (ro**2 - ri**2))
    assert ph.truth.betti == (1, 0, 0) and ph.truth.chi == 1
    assert ph.truth.t_solid == pytest.approx(1.0) and math.isinf(ph.truth.t_void)


@pytest.mark.parametrize("name", NEW_NAMES)
def test_new_phantoms_scale_with_t(name):
    a, b = make_phantom(name, t=1.0).truth, make_phantom(name, t=2.0).truth
    assert b.volume == pytest.approx(8 * a.volume)
    assert b.surface_area == pytest.approx(4 * a.surface_area)


@pytest.mark.parametrize("name", NEW_NAMES)
def test_analytic_volume_matches_rasterised_indicator(name):
    ph = make_phantom(name, t=1.0)
    mask, h = _fine_grid(ph, voxels_per_t=16)
    assert mask.sum() * h**3 == pytest.approx(ph.truth.volume, rel=0.01)


@pytest.mark.parametrize("name", NEW_NAMES)
def test_analytic_area_matches_independent_mesh(name):
    ph = make_phantom(name, t=1.0)
    mask, h = _fine_grid(ph, voxels_per_t=16)
    sm = ndi.gaussian_filter(np.pad(mask.astype(float), 2), 1.0)
    verts, faces, _, _ = marching_cubes(sm, level=0.5, spacing=(h, h, h))
    assert mesh_surface_area(verts, faces) == pytest.approx(ph.truth.surface_area, rel=0.04)


@pytest.mark.parametrize("name", NEW_NAMES)
@pytest.mark.parametrize("conn", [6, 26])
def test_declared_topology_matches_fine_raster(name, conn):
    ph = make_phantom(name, t=1.0)
    mask, _ = _fine_grid(ph, voxels_per_t=16)
    assert betti_numbers(mask, connectivity=conn).as_tuple() == ph.truth.betti


@pytest.mark.parametrize("name", NEW_NAMES)
def test_shape_fits_inside_declared_half_extent(name):
    ph = make_phantom(name, t=1.0)
    mask, _ = _fine_grid(ph, voxels_per_t=10)
    idx = np.argwhere(mask)   # la rejilla lleva 2 pasos de margen por lado
    assert idx.min() >= 1
    assert all(idx[:, k].max() <= mask.shape[k] - 2 for k in range(3))
