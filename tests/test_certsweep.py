"""Diseños, semillas y filas de los barridos del certificado (v0.4)."""
import math

import pytest

from geovida.certsweep import (
    H9_CAL_SEED, H9_PILOT_SEED, H9_SHIFT_SEED, H9_TEST_SEED, OBSERVABLE_COLUMNS, cert_extra,
    design_cal, design_shift, design_unseen,
)
from geovida.experiment import (
    ANISOTROPY, BASE_SEED, H3_SEED, H6_CAL_SEED, H6_SEED, H6_SHAPES, PROFILES, SHIFT_PROFILES,
    T_OVER_H, Condition, h6_design, run_condition,
)
from geovida.growth import H8_PILOT_SEED, H8_SEED
from geovida.phantoms import NEW_NAMES
from geovida.twod import BASE_SEED_2D, H7_SEED


def test_h6_design_still_has_the_ten_original_shapes():
    assert len(h6_design(1)) == 10 * 7 * 3 * 2          # añadir formas no cambia H6
    assert {c.shape for c in h6_design(1)} == set(H6_SHAPES)


def test_designs_use_the_documented_shapes_and_profiles():
    grid = len(T_OVER_H) * len(ANISOTROPY)
    assert len(design_cal(2)) == 10 * grid * 2 * 2
    assert {c.shape for c in design_cal(1)} == set(H6_SHAPES)
    assert {c.profile for c in design_cal(1)} == set(PROFILES)
    assert {c.shape for c in design_unseen(1)} == set(NEW_NAMES)
    assert {c.profile for c in design_shift(1)} == set(SHIFT_PROFILES)
    assert {c.shape for c in design_shift(1)} == set(H6_SHAPES)


def test_every_seed_in_the_project_is_distinct():
    seeds = [BASE_SEED, H3_SEED, BASE_SEED_2D, H6_SEED, H6_CAL_SEED, H7_SEED, H8_SEED,
             H8_PILOT_SEED, H9_PILOT_SEED, H9_CAL_SEED, H9_TEST_SEED, H9_SHIFT_SEED]
    assert len(set(seeds)) == len(seeds)


def test_extra_columns_are_added_without_touching_the_existing_ones():
    cond = Condition("capsule", 6.0, 2.0, "realistic", 1)
    plain = run_condition(cond, H9_PILOT_SEED, segmenters=("otsu",))[0]
    rich = run_condition(cond, H9_PILOT_SEED, segmenters=("otsu",), extra=cert_extra)[0]
    for k, v in plain.items():
        assert rich[k] == v or (isinstance(v, float) and math.isnan(v) and math.isnan(rich[k]))
    assert set(rich) - set(plain) == set(OBSERVABLE_COLUMNS)


def test_shifted_profiles_render_and_do_not_reuse_calibration_streams():
    a = run_condition(Condition("ball", 6.0, 1.0, "blurry", 0), H9_SHIFT_SEED,
                      segmenters=("otsu",), extra=cert_extra)[0]
    b = run_condition(Condition("ball", 6.0, 1.0, "noisy", 0), H9_SHIFT_SEED,
                      segmenters=("otsu",), extra=cert_extra)[0]
    assert a["volume"] != b["volume"] and a["profile"] == "blurry"


def test_observables_are_computed_without_the_truth():
    import inspect
    assert set(inspect.signature(cert_extra).parameters) == {
        "image", "spacing", "mask", "seg_name", "meas"}
