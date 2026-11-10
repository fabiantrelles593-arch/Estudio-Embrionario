"""H7: limpieza 2D que escala con el objeto (``docs/PREREGISTRO_H7.md``).

La regla está fijada en el preregistro: se quitan componentes (8-conexos) y se
rellenan huecos (4-conexos, no el exterior) menores que max(4, ceil(0.005 A))
píxeles, con A = área del componente mayor.
"""
import math

import numpy as np
import pandas as pd
import pytest

from geovida.h7 import evaluate_h7, paired_table
from geovida.twod import (
    ALL_2D, EXTRA_2D, H7_SEED, PHANTOMS_2D, SEGMENTERS_2D, Condition2D, _clean_mask_2d,
    betti_2d, clean_report_2d, design_h7, make_phantom2d, render2d, run_condition_2d,
    run_condition_h7, segment2d, spec2d_for,
)


# --- fantoma nuevo ----------------------------------------------------------

def test_ring_tight_truth_is_closed_form():
    ph = make_phantom2d("ring_tight", t=1.0)  # ancho t, hueco de diámetro t -> ri = 0.5, ro = 1.5
    assert ph.truth.area == pytest.approx(math.pi * (1.5**2 - 0.5**2))
    assert ph.truth.perimeter == pytest.approx(2 * math.pi * 2.0)
    assert ph.truth.outer_perimeter == pytest.approx(2 * math.pi * 1.5)
    assert ph.truth.betti == (1, 1) and ph.truth.chi == 0
    assert ph.truth.t_solid == pytest.approx(1.0) and ph.truth.t_void == pytest.approx(1.0)


def test_ring_tight_does_not_move_the_h5_seed_indices():
    assert PHANTOMS_2D == ("disk", "ellipse", "annulus")      # diseño y semillas de H5 intactos
    assert EXTRA_2D == ("ring_tight",) and ALL_2D == PHANTOMS_2D + EXTRA_2D


def test_h5_rows_are_unchanged_by_the_h7_extension():
    # Los cuatro segmentadores preregistrados de H5 y sus columnas no cambian.
    rows = run_condition_2d(Condition2D("annulus", 8.0, "us_compound", 0))
    assert [r["segmenter"] for r in rows] == list(SEGMENTERS_2D)
    assert "removed_components" not in rows[0]


def test_ring_tight_ideal_render_has_the_declared_topology():
    ph = make_phantom2d("ring_tight", 1.0)
    out = render2d(ph, spec2d_for(12.0, "ideal"), np.random.default_rng(3))
    assert betti_2d(out.coverage >= 0.5).as_tuple() == (1, 1)
    assert out.coverage.sum() * out.spacing**2 == pytest.approx(ph.truth.area, rel=0.01)


# --- regla de limpieza ------------------------------------------------------

def _blank(n=80):
    return np.zeros((n, n), bool)


def test_threshold_is_four_pixels_for_small_objects_and_half_percent_for_large_ones():
    small = _blank()
    small[10:20, 10:20] = True                     # A = 100 -> ceil(0.5) = 1 -> max(4, 1) = 4
    assert _clean_mask_2d(small)[3] == 4
    big = _blank(120)
    big[10:60, 10:60] = True                       # A = 2500 -> ceil(12.5) = 13
    assert _clean_mask_2d(big)[3] == 13


def test_specks_below_the_threshold_are_removed_and_at_the_threshold_are_kept():
    m = _blank()
    m[10:30, 10:30] = True                          # A = 400 -> umbral 4
    m[50, 50:53] = True                             # 3 px  -> se quita
    m[60, 50:54] = True                             # 4 px  -> se queda (no es «menor que»)
    out, removed, filled, thr = _clean_mask_2d(m)
    assert thr == 4 and removed == 1 and filled == 0
    assert not out[50, 50:53].any() and out[60, 50:54].all() and out[10:30, 10:30].all()


def test_pinholes_are_filled_but_a_real_hole_above_the_threshold_survives():
    m = _blank()
    m[10:50, 10:50] = True                          # A ≈ 1600 -> umbral ceil(8) = 8
    m[15, 15] = False                               # hueco de 1 px -> se rellena
    m[30:34, 30:34] = False                         # hueco de 16 px -> se conserva
    out, removed, filled, thr = _clean_mask_2d(m)
    assert thr == 8 and removed == 0 and filled == 1
    assert out[15, 15] and not out[30:34, 30:34].any()
    assert betti_2d(out).as_tuple() == (1, 1)


def test_the_exterior_is_never_filled_and_diagonal_leaks_are_not_holes():
    m = _blank(20)
    m[5:15, 5:15] = True
    m[0, 0] = False                                 # el exterior no es un hueco
    out, _, filled, _ = _clean_mask_2d(m)
    assert filled == 0 and not out[0, 0]


def test_cleaning_erases_a_real_hole_smaller_than_the_threshold():
    # Límite conocido (lección de E11): el criterio es de tamaño, no de significado.
    m = _blank(120)
    yy, xx = np.ogrid[:120, :120]
    r2 = (yy - 60) ** 2 + (xx - 60) ** 2
    m[(r2 <= 40**2) & (r2 > 1.5**2)] = True        # anillo grueso con un hueco real de ~9 px
    assert betti_2d(m).as_tuple() == (1, 1)
    out, _, filled, thr = _clean_mask_2d(m)
    assert thr > 9 and filled == 1 and betti_2d(out).as_tuple() == (1, 0)


def test_empty_mask_is_returned_unchanged():
    out, removed, filled, thr = _clean_mask_2d(_blank(10))
    assert not out.any() and (removed, filled, thr) == (0, 0, 4)


def test_clean_segmenters_are_the_base_mask_cleaned_and_report_matches():
    ph = make_phantom2d("annulus", 1.0)
    out = render2d(ph, spec2d_for(8.0, "us_compound"), np.random.default_rng(5))
    for name in SEGMENTERS_2D:
        base = segment2d(name, out.image, out.spacing)
        cleaned, removed, filled, thr = _clean_mask_2d(base)
        assert np.array_equal(segment2d(name + "_clean", out.image, out.spacing), cleaned)
        assert clean_report_2d(base) == {"removed_components": removed, "filled_holes": filled,
                                         "threshold_px": thr}


# --- diseño y filas ---------------------------------------------------------

def test_design_h7_matches_the_preregistration():
    d = design_h7(100)
    assert len(d) == 4 * 7 * 3 * 100 and H7_SEED == 20261120
    assert {c.shape for c in d} == set(ALL_2D)


def test_h7_rows_are_paired_on_the_same_image():
    rows = run_condition_h7(Condition2D("ring_tight", 6.0, "us_compound", 2))
    names = [r["segmenter"] for r in rows]
    assert names == [n + s for n in SEGMENTERS_2D for s in ("", "_clean")]
    by = {r["segmenter"]: r for r in rows}
    assert by["otsu"]["removed_components"] == 0 and by["otsu"]["filled_holes"] == 0
    assert by["otsu_clean"]["base"] == "otsu" and by["otsu"]["base"] == "otsu"
    assert by["otsu_clean"]["cleaned"] is True and by["otsu"]["cleaned"] is False


# --- veredictos -------------------------------------------------------------

PRIMARY = ("smoothed_otsu", "smoothed_otsu_s2")


def _frame(topo, area=None, n=40):
    """topo[(shape, level, segmenter)] = (base, clean) en fracción de aciertos."""
    rows = []
    for (shape, lvl, seg), (pb, pc) in topo.items():
        eb, ec = (area or {}).get((shape, lvl, seg), (0.02, 0.02))
        for rep in range(n):
            for name, p, e, cl in ((seg, pb, eb, False), (seg + "_clean", pc, ec, True)):
                rows.append({"shape": shape, "t_over_h": lvl, "profile": "us_compound",
                             "rep": rep, "segmenter": name, "base": seg, "cleaned": cl,
                             "topology_ok": rep < round(p * n), "err_area": e})
    return pd.DataFrame(rows)


def _all_cells(value, shapes=("disk", "ellipse", "annulus"), levels=(6.0, 8.0, 12.0, 20.0)):
    return {(s, l, g): value for s in shapes for l in levels for g in PRIMARY}


def test_h7a_supported_when_cleaning_closes_half_the_gap_in_most_cells():
    topo = _all_cells((0.50, 0.80))                                    # cierra 60 % del margen
    topo.update(_all_cells((1.0, 1.0), shapes=("ring_tight",)))
    res = evaluate_h7(_frame(topo))
    assert res["h7a"]["cells_with_margin"] == 18 and res["h7a"]["closed"] == 18
    assert res["h7a"]["verdict"] == "apoyada"


def test_h7a_ignores_cells_without_margin_and_is_not_evaluable_if_none_has_it():
    topo = _all_cells((0.95, 0.95))
    topo.update(_all_cells((1.0, 1.0), shapes=("ring_tight",)))
    res = evaluate_h7(_frame(topo))
    assert res["h7a"]["cells_with_margin"] == 0 and res["h7a"]["verdict"] == "no evaluable"


def test_h7a_grades_partial_and_not_supported_by_the_fraction_closed():
    topo = _all_cells((0.50, 0.80))
    cells = [k for k in topo if k[1] in (8.0, 12.0, 20.0)]
    for k in cells[:8]:                                                # 10 de 18 cierran: 56 %
        topo[k] = (0.50, 0.60)
    topo.update(_all_cells((1.0, 1.0), shapes=("ring_tight",)))
    assert evaluate_h7(_frame(topo))["h7a"]["verdict"] == "parcial"
    for k in cells[:12]:                                               # 6 de 18: 33 %
        topo[k] = (0.50, 0.60)
    assert evaluate_h7(_frame(topo))["h7a"]["verdict"] == "no apoyada"


def test_h7b_checks_the_change_in_median_absolute_area_error():
    topo = _all_cells((0.5, 0.8))
    topo.update(_all_cells((1.0, 1.0), shapes=("ring_tight",)))
    ok = evaluate_h7(_frame(topo))
    assert ok["h7b"]["n"] == 24 and ok["h7b"]["failing"] == 0 and ok["h7b"]["verdict"] == "apoyada"
    area = {("disk", 6.0, "smoothed_otsu"): (0.02, 0.035)}             # cambia 1.5 puntos
    one = evaluate_h7(_frame(topo, area))
    assert one["h7b"]["failing"] == 1 and one["h7b"]["verdict"] == "parcial"
    area[("disk", 8.0, "smoothed_otsu")] = (0.02, -0.04)                # |.| pasa de 0.02 a 0.04
    assert evaluate_h7(_frame(topo, area))["h7b"]["verdict"] == "no apoyada"


def test_h7c_counts_ring_tight_cells_damaged_by_more_than_ten_points():
    topo = _all_cells((0.5, 0.8))
    ring = _all_cells((1.0, 0.95), shapes=("ring_tight",))             # daño de 5 puntos: tolerado
    topo.update(ring)
    assert evaluate_h7(_frame(topo))["h7c"]["verdict"] == "apoyada"
    topo[("ring_tight", 6.0, "smoothed_otsu_s2")] = (0.90, 0.0)
    res = evaluate_h7(_frame(topo))
    assert res["h7c"]["damaged"] == 1 and res["h7c"]["n"] == 8 and res["h7c"]["verdict"] == "parcial"
    topo[("ring_tight", 8.0, "smoothed_otsu")] = (0.90, 0.5)
    assert evaluate_h7(_frame(topo))["h7c"]["verdict"] == "no apoyada"


def test_missing_cells_are_not_evaluable_never_not_supported():
    topo = _all_cells((0.5, 0.8))                                      # sin ring_tight
    res = evaluate_h7(_frame(topo))
    assert res["h7c"]["verdict"] == "no evaluable"


def test_paired_table_counts_images_fixed_and_broken_by_cleaning():
    topo = {("annulus", 8.0, "smoothed_otsu"): (0.5, 0.75)}
    tab = paired_table(_frame(topo, n=40))
    row = tab.iloc[0]
    assert row["n"] == 40 and row["topo_base"] == pytest.approx(0.5)
    assert row["fixed"] == 10 and row["broken"] == 0 and row["topo_clean"] == pytest.approx(0.75)
