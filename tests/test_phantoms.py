"""Los fantomas deben cumplir su verdad analítica contra una comprobación
independiente (rasterización fina del propio indicador)."""
import math

import numpy as np
import pytest
from scipy import integrate, ndimage as ndi
from skimage.measure import marching_cubes, mesh_surface_area

from geovida.phantoms import PHANTOM_NAMES, make_phantom
from geovida.topology import betti_numbers


def _fine_grid(ph, voxels_per_t=20, seed=0):
    """Rasteriza el indicador con paso h = t/voxels_per_t (centros de voxel,
    desplazamiento aleatorio para no alinear caras con la rejilla)."""
    t = ph.t
    h = t / voxels_per_t
    hx = np.array(ph.half_extent) + 2 * h
    rng = np.random.default_rng(seed)
    shift = rng.uniform(-0.5, 0.5, size=3) * h
    axes = [np.arange(-e, e + h, h) + s for e, s in zip(hx, shift)]
    X, Y, Z = np.meshgrid(*axes, indexing="ij")
    pts = np.stack([X, Y, Z], axis=-1)
    return ph.contains(pts), h


def test_all_expected_classes_exist():
    assert set(PHANTOM_NAMES) == {
        "ball", "ellipsoid", "shell", "torus", "tube", "shell_tight", "torus_tight"
    }


def test_ball_truth_is_closed_form():
    tr = make_phantom("ball", t=2.0).truth  # r = 1
    assert tr.volume == pytest.approx(4 / 3 * math.pi)
    assert tr.surface_area == pytest.approx(4 * math.pi)
    assert tr.betti == (1, 0, 0) and tr.chi == 1


def test_torus_truth_is_closed_form():
    ph = make_phantom("torus", t=2.0)  # r = 1, hueco = 1.5 t = 3 -> R = r + 1.5
    r, R = 1.0, 2.5
    assert ph.truth.volume == pytest.approx(2 * math.pi**2 * R * r**2)
    assert ph.truth.surface_area == pytest.approx(4 * math.pi**2 * R * r)
    assert ph.truth.betti == (1, 1, 0) and ph.truth.chi == 0


def test_shell_truth_is_closed_form():
    ph = make_phantom("shell", t=1.0)  # cavidad 4t -> Ri = 2, Ro = 3
    assert ph.truth.volume == pytest.approx(4 / 3 * math.pi * (27 - 8))
    assert ph.truth.surface_area == pytest.approx(4 * math.pi * (9 + 4))
    assert ph.truth.betti == (1, 0, 1) and ph.truth.chi == 2


def test_tube_truth_is_closed_form():
    ph = make_phantom("tube", t=1.0)  # lumen 2t -> Ri = 1, Ro = 2, L = 5
    assert ph.truth.volume == pytest.approx(math.pi * (4 - 1) * 5)
    assert ph.truth.surface_area == pytest.approx(
        2 * math.pi * (2 + 1) * 5 + 2 * math.pi * (4 - 1)
    )
    assert ph.truth.betti == (1, 1, 0) and ph.truth.chi == 0


def test_ellipsoid_area_matches_independent_quadrature():
    ph = make_phantom("ellipsoid", t=2.0)  # c = 1, b = 1.5, a = 2
    a, b, c = 2.0, 1.5, 1.0

    def integrand(v, u):  # u: polar, v: azimutal
        fx = b * c * math.sin(u) ** 2 * math.cos(v)
        fy = a * c * math.sin(u) ** 2 * math.sin(v)
        fz = a * b * math.sin(u) * math.cos(u)
        return math.sqrt(fx**2 + fy**2 + fz**2)

    ref, _ = integrate.dblquad(integrand, 0, math.pi, 0, 2 * math.pi, epsabs=1e-9)
    assert ph.truth.surface_area == pytest.approx(ref, rel=1e-6)
    assert ph.truth.volume == pytest.approx(4 / 3 * math.pi * a * b * c)


@pytest.mark.parametrize("name", [
    "ball", "ellipsoid", "shell", "torus", "tube", "shell_tight", "torus_tight"
])
def test_analytic_volume_matches_rasterised_indicator(name):
    ph = make_phantom(name, t=1.0)
    mask, h = _fine_grid(ph, voxels_per_t=24)
    est = mask.sum() * h**3
    assert est == pytest.approx(ph.truth.volume, rel=0.01)


@pytest.mark.parametrize("name", [
    "ball", "ellipsoid", "shell", "torus", "tube", "shell_tight", "torus_tight"
])
def test_analytic_area_matches_independent_mesh(name):
    ph = make_phantom(name, t=1.0)
    mask, h = _fine_grid(ph, voxels_per_t=24)
    sm = ndi.gaussian_filter(np.pad(mask.astype(float), 2), 1.0)
    verts, faces, _, _ = marching_cubes(sm, level=0.5, spacing=(h, h, h))
    assert mesh_surface_area(verts, faces) == pytest.approx(
        ph.truth.surface_area, rel=0.03
    )


@pytest.mark.parametrize("name", [
    "ball", "ellipsoid", "shell", "torus", "tube", "shell_tight", "torus_tight"
])
@pytest.mark.parametrize("conn", [6, 26])
def test_declared_topology_matches_fine_raster(name, conn):
    ph = make_phantom(name, t=1.0)
    mask, _ = _fine_grid(ph, voxels_per_t=24)
    b = betti_numbers(mask, connectivity=conn)
    assert b.as_tuple() == ph.truth.betti
    assert b.chi == ph.truth.chi


def test_feature_sizes_are_declared():
    assert make_phantom("ball", t=2.0).truth.t_void == math.inf
    assert make_phantom("torus_tight", t=2.0).truth.t_void == pytest.approx(1.0)
    assert make_phantom("torus_tight", t=2.0).truth.t_min == pytest.approx(1.0)
    assert make_phantom("shell", t=2.0).truth.t_min == pytest.approx(2.0)
    assert make_phantom("ellipsoid", t=2.0).truth.t_solid == pytest.approx(2.0)


def test_invalid_inputs_are_rejected():
    with pytest.raises(ValueError):
        make_phantom("ball", t=0.0)
    with pytest.raises(ValueError):
        make_phantom("dodecahedron", t=1.0)


# --- v0.2: formas nuevas para la confirmacion H3 (capsula, cilindro, oblato) --
from geovida.phantoms import EXTRA_NAMES

NEW = ["capsule", "cylinder", "oblate"]


def test_extra_names_are_new_and_do_not_change_the_preregistered_set():
    assert tuple(EXTRA_NAMES) == ("capsule", "cylinder", "oblate")
    assert not set(EXTRA_NAMES) & set(PHANTOM_NAMES)
    assert len(PHANTOM_NAMES) == 7


def test_capsule_truth_is_closed_form():
    ph = make_phantom("capsule", t=2.0)  # r = 1, tramo cilindrico 3 t = 6
    assert ph.truth.volume == pytest.approx(math.pi * 6 + 4 / 3 * math.pi)
    assert ph.truth.surface_area == pytest.approx(2 * math.pi * 6 + 4 * math.pi)
    assert ph.truth.betti == (1, 0, 0) and ph.truth.chi == 1
    assert ph.truth.t_solid == pytest.approx(2.0) and ph.truth.t_void == math.inf


def test_cylinder_truth_is_closed_form():
    ph = make_phantom("cylinder", t=2.0)  # r = 1, altura 3 t = 6
    assert ph.truth.volume == pytest.approx(math.pi * 6)
    assert ph.truth.surface_area == pytest.approx(2 * math.pi * 6 + 2 * math.pi)
    assert ph.truth.betti == (1, 0, 0)


def test_oblate_area_matches_independent_quadrature():
    ph = make_phantom("oblate", t=2.0)  # c = 1, a = b = 5
    a, b, c = 5.0, 5.0, 1.0

    def integrand(v, u):
        fx = b * c * math.sin(u) ** 2 * math.cos(v)
        fy = a * c * math.sin(u) ** 2 * math.sin(v)
        fz = a * b * math.sin(u) * math.cos(u)
        return math.sqrt(fx**2 + fy**2 + fz**2)

    ref, _ = integrate.dblquad(integrand, 0, math.pi, 0, 2 * math.pi, epsabs=1e-9)
    assert ph.truth.surface_area == pytest.approx(ref, rel=1e-6)
    assert ph.truth.volume == pytest.approx(4 / 3 * math.pi * a * b * c)
    assert ph.truth.t_solid == pytest.approx(2.0)


@pytest.mark.parametrize("name", NEW)
def test_new_volume_matches_rasterised_indicator(name):
    ph = make_phantom(name, t=1.0)
    mask, h = _fine_grid(ph, voxels_per_t=24)
    assert mask.sum() * h**3 == pytest.approx(ph.truth.volume, rel=0.01)


@pytest.mark.parametrize("name", NEW)
def test_new_area_matches_independent_mesh(name):
    ph = make_phantom(name, t=1.0)
    mask, h = _fine_grid(ph, voxels_per_t=24)
    sm = ndi.gaussian_filter(np.pad(mask.astype(float), 2), 1.0)
    verts, faces, _, _ = marching_cubes(sm, level=0.5, spacing=(h, h, h))
    assert mesh_surface_area(verts, faces) == pytest.approx(ph.truth.surface_area, rel=0.03)


@pytest.mark.parametrize("name", NEW)
@pytest.mark.parametrize("conn", [6, 26])
def test_new_topology_matches_fine_raster(name, conn):
    ph = make_phantom(name, t=1.0)
    mask, _ = _fine_grid(ph, voxels_per_t=24)
    b = betti_numbers(mask, connectivity=conn)
    assert b.as_tuple() == ph.truth.betti and b.chi == ph.truth.chi
