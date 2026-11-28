"""H8: el semáforo en la estimación de crecimiento 4D (``docs/PREREGISTRO_H8.md``)."""
import math

import numpy as np
import pandas as pd
import pytest

from geovida.growth import (
    GROWTH_FACTOR, H8_SEED, H8_SHAPES, MIN_STAGES, N_STAGES, T0_OVER_H, TRUE_RATE,
    VOXEL_RULE_MIN, Series, design_h8, evaluate_h8, fit_rate, rates_table, run_series,
    stage_sizes,
)


def test_constants_match_the_preregistration():
    assert (N_STAGES, GROWTH_FACTOR, T0_OVER_H, MIN_STAGES) == (8, 1.35, 2.0, 3)
    assert TRUE_RATE == pytest.approx(3 * math.log(1.35)) and TRUE_RATE == pytest.approx(0.900, abs=5e-4)
    assert H8_SEED == 20261119 and VOXEL_RULE_MIN == 100
    assert H8_SHAPES == ("ball", "ellipsoid", "oblate", "capsule", "cylinder")


def test_stage_sizes_grow_from_2_to_16_3_voxels():
    t = stage_sizes()
    assert len(t) == 8 and t[0] == pytest.approx(2.0) and t[-1] == pytest.approx(16.3, abs=0.05)
    assert np.allclose(t[1:] / t[:-1], 1.35)


def test_design_h8_has_900_series_with_30_reps():
    d = design_h8(30)
    assert len(d) == 5 * 3 * 2 * 30
    assert {s.anisotropy for s in d} == {1.0, 2.0, 3.0} and {s.profile for s in d} == {"ideal", "realistic"}


# --- estimador de la tasa ---------------------------------------------------

def test_fit_rate_recovers_an_exact_exponential():
    k = np.arange(8.0)
    v = 3.0 * np.exp(0.9 * k)
    assert fit_rate(k, v, np.ones(8, bool)) == pytest.approx(0.9)


def test_fit_rate_uses_only_the_kept_stages():
    k = np.arange(8.0)
    v = 3.0 * np.exp(0.9 * k)
    v[:2] *= 5.0                                   # dos etapas iniciales muy sesgadas
    keep = np.array([False, False] + [True] * 6)
    assert fit_rate(k, v, keep) == pytest.approx(0.9)
    assert fit_rate(k, v, np.ones(8, bool)) < 0.85


def test_fit_rate_is_nan_with_fewer_than_three_valid_stages():
    k = np.arange(8.0)
    v = np.exp(k)
    keep = np.zeros(8, bool)
    keep[[1, 5]] = True
    assert math.isnan(fit_rate(k, v, keep))


def test_fit_rate_drops_stages_with_zero_volume_instead_of_taking_log_zero():
    k = np.arange(8.0)
    v = np.exp(0.9 * k)
    v[0] = 0.0                                     # máscara vacía: no tiene logaritmo
    assert fit_rate(k, v, np.ones(8, bool)) == pytest.approx(0.9)
    v[:6] = 0.0
    assert math.isnan(fit_rate(k, v, np.ones(8, bool)))


# --- una serie --------------------------------------------------------------

@pytest.fixture(scope="module")
def ball_rows():
    return pd.DataFrame(run_series(Series("ball", 1.0, "ideal", 0)))


def test_run_series_has_one_row_per_stage_and_segmenter(ball_rows):
    assert len(ball_rows) == 8 * 3
    assert set(ball_rows["segmenter"]) == {"global", "otsu", "smoothed_otsu"}
    assert sorted(ball_rows["stage"].unique()) == list(range(8))
    assert set(ball_rows["light"]) <= {"verde", "amarillo", "rojo"}


def test_voxel_is_fixed_and_the_object_grows(ball_rows):
    g = ball_rows[ball_rows["segmenter"] == "global"].sort_values("stage")
    assert np.allclose(g["h_xy"], 1.0)
    assert np.allclose(g["t_over_h"].to_numpy(), stage_sizes())
    ratio = g["volume_true"].to_numpy()[1:] / g["volume_true"].to_numpy()[:-1]
    assert np.allclose(ratio, 1.35**3)


def test_light_comes_from_the_mask_and_goes_from_red_to_green_as_the_ball_grows(ball_rows):
    g = ball_rows[ball_rows["segmenter"] == "global"].sort_values("stage")
    assert g["light"].iloc[0] == "rojo" and g["light"].iloc[-1] == "verde"
    assert (np.diff(g["p_volume_ok"].to_numpy()) >= -1e-9).all()     # monótona en la profundidad


def test_series_are_reproducible_and_stages_are_independent_draws():
    a = pd.DataFrame(run_series(Series("capsule", 2.0, "realistic", 3)))
    b = pd.DataFrame(run_series(Series("capsule", 2.0, "realistic", 3)))
    pd.testing.assert_frame_equal(a, b)
    c = pd.DataFrame(run_series(Series("capsule", 2.0, "realistic", 4)))
    assert not np.allclose(a["volume"], c["volume"])


# --- tabla de tasas ---------------------------------------------------------

def _series_frame(lights, bias, sid=0, seg="otsu", prof="ideal", nvox=None):
    k = np.arange(8)
    true = np.exp(TRUE_RATE * k)
    return pd.DataFrame({
        "shape": "ball", "anisotropy": 1.0, "profile": prof, "rep": sid, "segmenter": seg,
        "stage": k, "volume_true": true, "volume": true * np.asarray(bias, float),
        "light": lights, "n_voxels": nvox if nvox is not None else np.round(true * 50).astype(int),
    })


def test_oracle_rate_is_exact_and_no_red_removes_the_biased_red_stages():
    lights = ["rojo", "rojo", "amarillo", "verde", "verde", "verde", "verde", "verde"]
    bias = [3.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    row = rates_table(_series_frame(lights, bias)).iloc[0]
    assert row["rate_oracle"] == pytest.approx(TRUE_RATE)
    assert row["err_no_red"] == pytest.approx(0.0, abs=1e-9) and row["err_all"] > 0.05
    assert row["n_no_red"] == 6 and row["n_green"] == 5 and row["n_all"] == 8
    assert row["err_green"] == pytest.approx(0.0, abs=1e-9)


def test_all_estimator_keeps_red_stages():
    # Regresión del fallo del piloto: «todas las etapas» no puede descartar las rojas.
    lights = ["rojo"] * 6 + ["verde"] * 2
    row = rates_table(_series_frame(lights, [1.0] * 8)).iloc[0]
    assert row["n_all"] == 8 and not math.isnan(row["rate_all"])
    assert math.isnan(row["rate_no_red"]) and math.isnan(row["err_no_red"])


def test_voxel_rule_drops_stages_below_100_voxels():
    lights = ["verde"] * 8
    nvox = [10, 99, 100, 300, 900, 2000, 5000, 9000]
    row = rates_table(_series_frame(lights, [4.0, 4.0, 1, 1, 1, 1, 1, 1], nvox=nvox)).iloc[0]
    assert row["n_vox100"] == 6 and row["err_vox100"] == pytest.approx(0.0, abs=1e-9)


# --- veredictos -------------------------------------------------------------

def _rates(per_stratum, n=40):
    """per_stratum[(seg, prof)] = (err_all, err_no_red, fracción sin tasa no_red)."""
    rows = []
    for (seg, prof), (ea, en, miss) in per_stratum.items():
        for i in range(n):
            undefined = i < round(miss * n)
            rows.append({"segmenter": seg, "profile": prof, "shape": "ball", "anisotropy": 1.0,
                         "rep": i, "err_all": ea, "err_no_red": math.nan if undefined else en,
                         "err_green": en, "err_vox100": en, "err_oracle": 0.0})
    return pd.DataFrame(rows)


STRATA = [(s, p) for s in ("global", "otsu", "smoothed_otsu") for p in ("ideal", "realistic")]


def test_h8_supported_when_no_red_is_better_useful_and_cheap():
    res = evaluate_h8(_rates({k: (0.10, 0.02, 0.0) for k in STRATA}))
    assert res["h8a"]["verdict"] == res["h8b"]["verdict"] == res["h8c"]["verdict"] == "apoyada"
    assert res["h8a"]["evaluable"] == 6


def test_h8a_and_h8b_are_graded_over_evaluable_strata_only():
    spec = {k: (0.10, 0.02, 0.0) for k in STRATA}
    spec[("smoothed_otsu", "ideal")] = (0.10, 0.20, 0.5)       # evaluable (20 series) -> no, < 30
    res = evaluate_h8(_rates(spec))
    assert res["h8a"]["evaluable"] == 5 and res["h8a"]["verdict"] == "apoyada"
    spec[("otsu", "ideal")] = (0.02, 0.08, 0.0)                # peor y > 5 %: un estrato falla
    res = evaluate_h8(_rates(spec))
    assert res["h8a"]["verdict"] == "parcial" and res["h8b"]["verdict"] == "parcial"
    spec[("otsu", "realistic")] = (0.02, 0.08, 0.0)
    res = evaluate_h8(_rates(spec))
    assert res["h8a"]["verdict"] == "no apoyada" and res["h8b"]["verdict"] == "no apoyada"


def test_h8_is_not_evaluable_when_no_stratum_has_thirty_defined_series():
    res = evaluate_h8(_rates({k: (0.10, 0.02, 0.9) for k in STRATA}))
    assert res["h8a"]["verdict"] == "no evaluable" and res["h8b"]["verdict"] == "no evaluable"
    assert res["h8c"]["verdict"] == "no apoyada"               # el coste sí es evaluable


def test_h8c_counts_strata_with_at_most_a_quarter_of_series_lost():
    spec = {k: (0.10, 0.02, 0.0) for k in STRATA}
    spec[("smoothed_otsu", "ideal")] = (0.10, 0.02, 0.25)      # justo 25 %: cuenta
    spec[("smoothed_otsu", "realistic")] = (0.10, 0.02, 0.30)
    assert evaluate_h8(_rates(spec))["h8c"]["count"] == 5
    spec[("otsu", "ideal")] = (0.10, 0.02, 0.30)
    spec[("otsu", "realistic")] = (0.10, 0.02, 0.30)
    res = evaluate_h8(_rates(spec))
    assert res["h8c"]["count"] == 3 and res["h8c"]["verdict"] == "parcial"


def test_paired_comparison_uses_only_series_with_no_red_defined():
    rows = []
    for i in range(40):
        defined = i >= 5
        rows.append({"segmenter": "otsu", "profile": "ideal", "shape": "ball", "anisotropy": 1.0,
                     "rep": i, "err_all": 0.04 if defined else 0.90,   # las 5 perdidas tienen err_all enorme
                     "err_no_red": 0.02 if defined else math.nan,
                     "err_green": 0.02, "err_vox100": 0.02, "err_oracle": 0.0})
    res = evaluate_h8(pd.DataFrame(rows))
    s = [r for r in res["strata"] if r["stratum"] == "otsu|ideal"][0]
    assert s["n_defined"] == 35 and s["median_err_all_paired"] == pytest.approx(0.04)
    assert s["frac_undefined"] == pytest.approx(5 / 40)
