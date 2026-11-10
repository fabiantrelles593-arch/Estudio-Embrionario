"""Margen de persistencia topológica (v0.4).

El margen geométrico es la distancia, en la filtración por distancia con signo
(Robins et al. 2016), desde la máscara hasta el primer cambio del triple de
Betti; el de intensidad es lo mismo en la filtración por umbral (Chung y Day
2018). Aquí se prueba el comportamiento en casos construidos a mano.
"""
import math

import numpy as np
import pytest

from geovida.imaging import render, spec_for_t_over_h
from geovida.phantoms import make_phantom
from geovida.segment import SEGMENTERS, segment, working_image_and_threshold
from geovida.topomargin import (
    INTENSITY_GRID, MARGIN_GRID, critical_sites, intensity_margin, topological_margin,
)

ISO = (1.0, 1.0, 1.0)


def _ball(radius, pad=6):
    n = 2 * (int(radius) + pad) + 1
    c = n // 2
    z, y, x = np.ogrid[:n, :n, :n]
    return (x - c) ** 2 + (y - c) ** 2 + (z - c) ** 2 <= radius**2


def _torus(big_r, r, pad=5):
    n = 2 * (int(big_r + r) + pad) + 1
    c = n // 2
    z, y, x = np.ogrid[:n, :n, :n]
    return (np.hypot(x - c, y - c) - big_r) ** 2 + (z - c) ** 2 <= r * r


def _two_cubes(bridge_width=0, gap=6):
    m = np.zeros((14, 14, 22 + gap), bool)
    m[3:11, 3:11, 3:11] = True
    m[3:11, 3:11, 11 + gap:19 + gap] = True
    if bridge_width:
        a = 7 - bridge_width // 2
        m[a:a + bridge_width, a:a + bridge_width, 11:11 + gap] = True
    return m


# --- margen geométrico ------------------------------------------------------

def test_grids_are_the_documented_ones():
    assert MARGIN_GRID == (0.6, 1.0, 1.5, 2.0) and INTENSITY_GRID == (0.1, 0.2, 0.3, 0.4)


def test_margin_of_a_large_ball_reaches_the_cap_on_both_sides():
    m = topological_margin(_ball(12), ISO)
    assert m["tau_dil"] == 2.0 and m["tau_ero"] == 2.0


def test_one_voxel_bridge_breaks_under_the_smallest_erosion():
    m = topological_margin(_two_cubes(bridge_width=1), ISO)
    assert m["tau_ero"] == 0.0 and m["tau_dil"] == 2.0


def test_thicker_bridge_tolerates_more_erosion():
    thin = topological_margin(_two_cubes(bridge_width=2), ISO)["tau_ero"]
    thick = topological_margin(_two_cubes(bridge_width=4), ISO)["tau_ero"]
    assert thin < thick


def test_narrow_gap_closes_under_dilation():
    # Los centros de las capas de un hueco de g vóxeles quedan a 0.5, 1.5, 2.5...
    # de la frontera digital (distancia al centro del vóxel sólido más cercano
    # menos medio vóxel). g = 2: dos capas a 0.5, las cierra el primer desfase
    # (0.6). g = 3 y 4: la capa interior está a 1.5; aguantan 1.0 y caen en 1.5.
    # g = 5: capa central a 2.5, más allá del tope. Valores comprobados con una
    # sonda antes de escribirlos (dos expectativas mías previas, sin derivar,
    # eran falsas: regla de ERRATA E1).
    expected = {2: 0.0, 3: 1.0, 4: 1.0, 5: 2.0}
    for gap, tau in expected.items():
        m = topological_margin(_two_cubes(gap=gap), ISO)
        assert m["tau_dil"] == tau and m["tau_ero"] == 2.0


def test_small_torus_hole_closes_under_dilation_before_the_cap():
    m = topological_margin(_torus(big_r=5.0, r=3.0), ISO)   # hueco de radio 2
    assert 1.0 <= m["tau_dil"] < 2.0


def test_margin_is_invariant_to_a_global_change_of_units():
    mask = _torus(5.0, 3.0)
    assert topological_margin(mask, ISO) == topological_margin(mask, (0.25, 0.25, 0.25))


def test_margin_of_an_empty_mask_is_nan():
    m = topological_margin(np.zeros((8, 8, 8), bool), ISO)
    assert math.isnan(m["tau_dil"]) and math.isnan(m["tau_ero"])


def test_a_single_noise_voxel_makes_the_topology_fragile():
    m = _ball(8)
    m[1, 1, 1] = True                                     # mota aislada: b0 = 2
    assert topological_margin(m, ISO)["tau_ero"] == 0.0


# --- localización del evento crítico ----------------------------------------

def test_critical_site_of_a_thin_bridge_is_in_the_bridge():
    mask = _two_cubes(bridge_width=2, gap=6)
    sites = critical_sites(mask, ISO)
    ero = sites["erosion"]
    assert ero["kind"] == "separación"
    cz = ero["centroid_vox"][2]
    assert 11 <= cz <= 16 and abs(ero["centroid_vox"][0] - 6.5) <= 1.5   # centro del puente
    assert sites["dilation"] is None                      # nada cambia al dilatar hasta el tope


def test_critical_site_of_a_gap_is_between_the_two_parts():
    sites = critical_sites(_two_cubes(gap=2), ISO)
    dil = sites["dilation"]
    assert dil["kind"] == "fusión" and 10.5 <= dil["centroid_vox"][2] <= 12.5


def test_critical_site_of_a_speck_points_at_the_speck():
    m = _ball(8)
    m[1, 1, 1] = True
    ero = critical_sites(m, ISO)["erosion"]
    assert ero["kind"] == "componente pequeño"
    assert ero["centroid_vox"] == pytest.approx((1.0, 1.0, 1.0))


def test_tunnel_events_are_reported_but_not_localised():
    dil = critical_sites(_torus(5.0, 3.0), ISO)["dilation"]
    assert dil["kind"] == "túnel o cavidad" and dil["centroid_vox"] is None


def test_dumbbell_neck_is_found_at_the_centre_of_the_image():
    ph = make_phantom("dumbbell", t=1.0)
    out = render(ph, spec_for_t_over_h(3.0, 1.0, "ideal"), np.random.default_rng(1))
    mask = segment("global", out.image, out.spacing)
    ero = critical_sites(mask, out.spacing)["erosion"]
    centre = (np.array(mask.shape) - 1) / 2
    assert ero["kind"] == "separación"
    assert np.linalg.norm(np.array(ero["centroid_vox"]) - centre) <= 2.5


# --- umbral de trabajo y margen de intensidad -------------------------------

@pytest.mark.parametrize("name", list(SEGMENTERS))
def test_working_image_and_threshold_reproduce_the_segmenter(name):
    ph = make_phantom("torus", t=1.0)
    out = render(ph, spec_for_t_over_h(6.0, 2.0, "realistic"), np.random.default_rng(4))
    work, thr = working_image_and_threshold(name, out.image, out.spacing)
    assert np.array_equal(work >= thr, segment(name, out.image, out.spacing))


def test_intensity_margin_of_a_clean_large_ball_reaches_the_cap():
    ph = make_phantom("ball", t=1.0)
    out = render(ph, spec_for_t_over_h(12.0, 1.0, "ideal"), np.random.default_rng(0))
    m = intensity_margin(out.image, out.spacing, "global")
    assert m["m_lo"] == 0.4 and m["m_hi"] == 0.4 and m["contrast_hat"] == pytest.approx(1.0, abs=0.1)


def test_intensity_margin_sees_a_faint_bridge_that_the_mask_does_not_contain():
    img = np.zeros((14, 14, 28), np.float32)
    img[3:11, 3:11, 3:11] = 1.0
    img[3:11, 3:11, 17:25] = 1.0
    img[6:8, 6:8, 11:17] = 0.35                           # puente tenue: no entra en la máscara
    mask = img >= 0.5
    assert topological_margin(mask, ISO)["tau_dil"] == 2.0   # la máscara sola no lo ve
    m = intensity_margin(img, ISO, "global")
    assert m["m_lo"] == pytest.approx(0.1) and m["m_hi"] == 0.4


def test_intensity_margin_is_nan_without_contrast():
    m = intensity_margin(np.zeros((6, 6, 6), np.float32), ISO, "global")
    assert math.isnan(m["m_lo"]) and math.isnan(m["m_hi"])
