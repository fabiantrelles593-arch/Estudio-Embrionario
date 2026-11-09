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
