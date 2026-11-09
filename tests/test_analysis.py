import numpy as np
import pandas as pd
import pytest

from geovida.analysis import (
    PREDICTORS, add_predictors, compare_predictors, find_t_star, spread_in_steps,
    success_by_level, wilson_interval,
)

LEVELS = (1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0)


def test_wilson_interval_known_values():
    lo, hi = wilson_interval(50, 100)
    assert (lo, hi) == pytest.approx((0.4038, 0.5962), abs=1e-3)
    lo, hi = wilson_interval(200, 200)
    assert hi == pytest.approx(1.0) and 0.98 < lo < 1.0
    assert wilson_interval(0, 0) == (0.0, 1.0)


def test_t_star_requires_success_at_that_level_and_all_higher_ones():
    p = [0.1, 0.5, 0.96, 0.94, 0.99, 1.0, 1.0]
    assert find_t_star(LEVELS, p) == 6.0           # 4.0 falla, así que baja a 6.0
    p = [0.1, 0.5, 0.96, 0.97, 0.99, 1.0, 1.0]
    assert find_t_star(LEVELS, p) == 3.0
    assert np.isnan(find_t_star(LEVELS, [0.1] * 7))
    assert np.isnan(find_t_star(LEVELS, [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9]))


def test_spread_is_measured_in_grid_steps():
    assert spread_in_steps(LEVELS, [3.0, 4.0, 3.0]) == 1
    assert spread_in_steps(LEVELS, [2.0, 6.0]) == 3
    assert np.isnan(spread_in_steps(LEVELS, [3.0, np.nan]))
    assert spread_in_steps(LEVELS, [4.0]) == 0


def _synthetic(n_per=60, seed=0):
    """Éxito gobernado por t_min/h_max (la hipótesis H1b/H1c cierta)."""
    rng = np.random.default_rng(seed)
    rows = []
    shapes = {"ball": 1.0, "torus_tight": 0.5}      # t_min / t_solid
    for shape, ratio in shapes.items():
        for a in (1.0, 2.0, 3.0):
            for t in LEVELS:
                for _ in range(n_per):
                    t_min_hmax = t * ratio / a
                    p = 1 / (1 + np.exp(-4.0 * (np.log(t_min_hmax) - np.log(2.5))))
                    rows.append({"shape": shape, "anisotropy": a, "t_over_h": t,
                                 "segmenter": "global", "profile": "ideal",
                                 "t_solid_over_hxy": t, "t_min_over_hxy": t * ratio,
                                 "t_solid_over_hmax": t / a, "t_min_over_hmax": t * ratio / a,
                                 "topology_ok": bool(rng.random() < p)})
    return add_predictors(pd.DataFrame(rows))


def test_success_by_level_counts_and_proportions():
    df = _synthetic(n_per=10)
    tab = success_by_level(df, "topology_ok", ["shape", "anisotropy"])
    assert set(tab.columns) >= {"shape", "anisotropy", "t_over_h", "n", "k", "p", "wilson_lo"}
    assert (tab["n"] == 10).all()
    assert ((tab["p"] >= 0) & (tab["p"] <= 1)).all()


def test_geo_predictor_is_added():
    df = _synthetic(n_per=1)
    assert np.allclose(df["t_solid_over_hgeo"], df["t_solid_over_hxy"] / df["anisotropy"] ** (1 / 3))
    assert set(PREDICTORS) == {"P1", "P2", "P3", "P4", "P5", "P6"}


def test_model_comparison_recovers_the_true_predictor():
    df = _synthetic(n_per=80)
    tab = compare_predictors(df, "topology_ok")
    best = tab.sort_values("aic").iloc[0]["predictor"]
    assert best == "P6"                                   # t_min / h_max
    worst_solid_xy = tab.set_index("predictor").loc["P1", "aic"]
    assert worst_solid_xy > tab.set_index("predictor").loc["P6", "aic"] + 20


def test_model_comparison_survives_perfect_separation():
    df = _synthetic(n_per=5)
    df["topology_ok"] = df["t_min_over_hmax"] >= 2.5      # separable por completo
    tab = compare_predictors(df, "topology_ok")
    assert np.isfinite(tab["aic"]).all()
    assert tab.sort_values("aic").iloc[0]["predictor"] == "P6"


def test_t_star_table_per_stratum_and_ratio_spread():
    from geovida.analysis import ratio_spread, t_star_table
    df = _synthetic(n_per=200, seed=1)
    tab = success_by_level(df, "topology_ok", ["shape", "anisotropy"])
    ts = t_star_table(tab, ["shape", "anisotropy"])
    assert set(ts.columns) == {"shape", "anisotropy", "t_star"}
    # La verdad sintética pide t_min/h_max ~ 2.5: ball a=1 -> nivel 3 o 4;
    # torus_tight (ratio 0.5) a=1 exige el doble de t/h que ball.
    ball = ts[(ts["shape"] == "ball") & (ts["anisotropy"] == 1.0)]["t_star"].item()
    tight = ts[(ts["shape"] == "torus_tight") & (ts["anisotropy"] == 1.0)]["t_star"].item()
    assert tight > ball
    assert ratio_spread([3.0, 4.0, 3.0]) == pytest.approx(4 / 3)
    assert np.isnan(ratio_spread([3.0, np.nan]))


def test_volume_to_area_length_predictor_for_the_ball():
    from geovida.analysis import add_vq_predictors
    # Bola de t = 1 (r = 0.5): V/S = r/3. Con h_xy = 1/6 -> Q_xy = (1/6)/(1/6) = 1.
    df = pd.DataFrame({"t_over_h": [6.0, 6.0], "anisotropy": [1.0, 3.0],
                       "volume_true": [4 / 3 * np.pi * 0.125] * 2,
                       "area_true": [4 * np.pi * 0.25] * 2})
    out = add_vq_predictors(df)
    assert out["q_over_hxy"].iloc[0] == pytest.approx(1.0)
    assert out["q_over_hgeo"].iloc[1] == pytest.approx(1.0 / 3 ** (1 / 3))
    assert out["q_over_hmax"].iloc[1] == pytest.approx(1.0 / 3.0)


# --- v0.2: modelos congelados para la confirmacion H3 ------------------------
from geovida.analysis import (
    calibration_error, fit_frozen_logit, logloss, predict_frozen, x_at_probability,
)


def _logistic_sample(b0=-3.0, b1=4.0, n=4000, seed=1):
    rng = np.random.default_rng(seed)
    x = np.exp(rng.uniform(np.log(0.3), np.log(6.0), n))
    p = 1 / (1 + np.exp(-(b0 + b1 * np.log(x))))
    return x, (rng.random(n) < p).astype(float), p


def test_frozen_fit_recovers_known_coefficients():
    x, y, _ = _logistic_sample()
    b = fit_frozen_logit(x, y)
    assert b["intercept"] == pytest.approx(-3.0, abs=0.35)
    assert b["slope"] == pytest.approx(4.0, abs=0.45)


def test_x_at_probability_inverts_the_fitted_curve():
    b = {"intercept": -3.0, "slope": 4.0}
    x95 = x_at_probability(b, 0.95)
    assert predict_frozen(b, np.array([x95]))[0] == pytest.approx(0.95)


def test_logloss_prefers_the_true_model_out_of_sample():
    x, y, _ = _logistic_sample(seed=2)
    true = {"intercept": -3.0, "slope": 4.0}
    wrong = {"intercept": -1.0, "slope": 1.0}
    assert logloss(true, x, y) < logloss(wrong, x, y)


def test_calibration_error_is_small_for_the_true_model_and_large_for_a_shifted_one():
    x, y, _ = _logistic_sample(seed=3)
    true = {"intercept": -3.0, "slope": 4.0}
    shifted = {"intercept": 0.0, "slope": 4.0}
    assert calibration_error(true, x, y) < 0.05
    assert calibration_error(shifted, x, y) > 0.2


def test_x_at_probability_is_nan_for_a_flat_curve():
    assert np.isnan(x_at_probability({"intercept": 0.0, "slope": 0.0}, 0.95))
