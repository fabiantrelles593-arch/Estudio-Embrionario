import numpy as np
import pandas as pd
import pytest

from geovida.experiment import (
    ANISOTROPY, PROFILES, T_OVER_H, Condition, full_design, run_condition, run_sweep,
)
from geovida.phantoms import PHANTOM_NAMES

REQUIRED = {
    "shape", "t_over_h", "anisotropy", "profile", "rep", "segmenter",
    "t_solid_over_hxy", "t_solid_over_hz", "t_solid_over_hmax",
    "t_min_over_hxy", "t_min_over_hz", "t_min_over_hmax",
    "volume_true", "area_true", "volume", "area_mc", "area_faces",
    "err_volume", "err_area_mc", "err_area_faces",
    "err_b0", "err_b1", "err_b2", "topology_ok", "topology_ok_6",
    "dice", "hd95", "msd",
}


def test_design_size_and_levels_are_the_preregistered_ones():
    assert T_OVER_H == (1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0)
    assert ANISOTROPY == (1.0, 2.0, 3.0)
    assert PROFILES == ("ideal", "realistic")
    design = full_design(n_reps=2)
    assert len(design) == len(PHANTOM_NAMES) * 7 * 3 * 2 * 2
    assert len(set(design)) == len(design)


def test_run_condition_returns_one_row_per_segmenter_with_all_columns():
    rows = run_condition(Condition("ball", 6.0, 1.0, "ideal", 0))
    assert [r["segmenter"] for r in rows] == ["global", "otsu", "smoothed_otsu"]
    assert REQUIRED <= set(rows[0])


def test_run_condition_is_deterministic():
    c = Condition("torus", 4.0, 2.0, "realistic", 3)
    a, b = run_condition(c), run_condition(c)
    assert a == b


def test_predictors_use_the_right_voxel_size():
    r = run_condition(Condition("torus_tight", 6.0, 3.0, "ideal", 0))[0]
    # t = 1; h_xy = 1/6; h_z = 3 h_xy; t_min = 0.5 t
    assert r["t_solid_over_hxy"] == pytest.approx(6.0)
    assert r["t_solid_over_hz"] == pytest.approx(2.0)
    assert r["t_solid_over_hmax"] == pytest.approx(2.0)
    assert r["t_min_over_hxy"] == pytest.approx(3.0)
    assert r["t_min_over_hmax"] == pytest.approx(1.0)


def test_well_resolved_clean_ball_is_measured_accurately_by_oracle():
    r = run_condition(Condition("ball", 8.0, 1.0, "ideal", 0))[0]
    assert abs(r["err_volume"]) < 0.03
    assert r["topology_ok"] is True
    assert r["dice"] > 0.95


def test_sweep_is_independent_of_the_number_of_workers():
    conds = [Condition("ball", 4.0, 1.0, "ideal", i) for i in range(3)]
    a = run_sweep(conds, n_jobs=1)
    b = run_sweep(conds, n_jobs=2)
    pd.testing.assert_frame_equal(
        a.sort_values(["rep", "segmenter"]).reset_index(drop=True),
        b.sort_values(["rep", "segmenter"]).reset_index(drop=True),
    )


# --- v0.2: diseno H3 (formas nuevas, semillas nuevas, extension) -------------
from geovida.experiment import BASE_SEED, H3_SEED, h3_design, _rng
from geovida.phantoms import EXTRA_NAMES


def test_h3_design_uses_only_new_shapes_and_the_same_grid():
    d = h3_design(n_reps=2)
    assert {c.shape for c in d} == set(EXTRA_NAMES)
    assert len(d) == len(EXTRA_NAMES) * len(T_OVER_H) * len(ANISOTROPY) * len(PROFILES) * 2


def test_h3_seed_is_fresh_and_streams_do_not_overlap_h1():
    assert H3_SEED != BASE_SEED
    c = Condition("capsule", 4.0, 1.0, "ideal", 0)
    h3 = _rng(c, H3_SEED).random(4)
    h1 = _rng(Condition("ball", 4.0, 1.0, "ideal", 0), BASE_SEED).random(4)
    assert not np.allclose(h3, h1)


def test_extension_segmenter_does_not_perturb_the_preregistered_rows():
    c = Condition("shell", 4.0, 1.0, "realistic", 1)
    base = run_condition(c)
    ext = run_condition(c, segmenters=("global", "otsu", "smoothed_otsu", "otsu_clean"))
    assert [r["segmenter"] for r in ext][-1] == "otsu_clean"
    assert ext[:3] == base


def test_rows_report_the_sdf_area_error():
    r = run_condition(Condition("ball", 6.0, 1.0, "ideal", 0))[0]
    assert {"area_sdf", "err_area_sdf"} <= set(r)


# --- v0.3: diseno H6 (calibracion y confirmacion del semaforo) ---------------
from geovida.experiment import H6_CAL_SEED, H6_SEED, h6_design


def test_h6_design_covers_all_ten_shapes_on_the_same_grid():
    from geovida.phantoms import EXTRA_NAMES, PHANTOM_NAMES
    d = h6_design(n_reps=2)
    assert {c.shape for c in d} == set(PHANTOM_NAMES) | set(EXTRA_NAMES)
    assert len(d) == 10 * len(T_OVER_H) * len(ANISOTROPY) * len(PROFILES) * 2


def test_h6_seeds_are_distinct_from_every_earlier_sweep():
    assert len({BASE_SEED, H3_SEED, H6_SEED, H6_CAL_SEED}) == 4
    assert 20261111 not in (H6_SEED, H6_CAL_SEED)   # semilla del piloto de area
    assert 20261112 not in (H6_SEED, H6_CAL_SEED)   # semilla de 2D
    assert 20261115 not in (H6_SEED, H6_CAL_SEED)   # semilla del piloto de H6
