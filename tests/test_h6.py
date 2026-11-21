import math

import numpy as np
import pandas as pd
import pytest

from geovida import h6
from geovida.h3 import PREREGISTERED_SEGMENTERS, PROFILES

SHAPES = [f"s{i}" for i in range(10)]


def _h6_frame(n_per_stratum=400, informative=True, seed=0, y_const=None):
    """Tabla sintética con las columnas que usa h6: 6 estratos x 10 formas."""
    rng = np.random.default_rng(seed)
    rows = []
    for seg in PREREGISTERED_SEGMENTERS:
        for prof in PROFILES:
            for shape in SHAPES:
                x = np.exp(rng.uniform(-1.0, 3.0, n_per_stratum // len(SHAPES)))
                if y_const is not None:
                    y = (rng.random(len(x)) < y_const).astype(float)
                elif informative:
                    y = (np.log(x) > 1.0).astype(float)
                else:
                    y = (rng.random(len(x)) < 0.5).astype(float)
                rows.append(pd.DataFrame({
                    "segmenter": seg, "profile": prof, "shape": shape, "v_ok": y,
                    "d_over_hgeo": x, "q_hat_over_hgeo": np.exp(rng.normal(size=len(x)))}))
    return pd.concat(rows, ignore_index=True)


def test_add_features_scales_depth_by_geometric_voxel_and_flags_unmeasurable():
    df = pd.DataFrame({"t_over_h": [4.0, 4.0, 4.0], "anisotropy": [1.0, 8.0, 1.0],
                       "volume": [100.0, 100.0, 0.0], "area_sdf": [50.0, 50.0, float("nan")],
                       "d_mean": [0.5, 0.5, 0.0], "err_volume": [0.05, -0.0501, -1.0]})
    out = h6.add_features(df)
    # h_geo = h_xy * a^(1/3), h_xy = 1/4
    assert out["d_over_hgeo"].iloc[0] == pytest.approx(0.5 / 0.25)
    assert out["d_over_hgeo"].iloc[1] == pytest.approx(0.5 / (0.25 * 2.0))
    assert math.isnan(out["d_over_hgeo"].iloc[2])
    assert list(out["v_ok"]) == [1.0, 0.0, 0.0]          # el borde 0.05 cuenta como acierto


def test_predict_p_is_zero_where_the_variable_is_not_measurable():
    p = h6.predict_p([float("nan"), 0.0, -1.0, 2.0], {"intercept": 0.0, "slope": 1.0})
    assert list(p[:3]) == [0.0, 0.0, 0.0]
    assert p[3] == pytest.approx(2.0 / 3.0)               # expit(ln 2) = 2/3


def test_logloss_floor_keeps_a_zero_probability_finite():
    assert h6.logloss_p([0.0], [1.0]) == pytest.approx(-math.log(h6.P_FLOOR))
    assert h6.logloss_p([0.0], [0.0]) == pytest.approx(-math.log(1 - h6.P_FLOOR))


def test_ece_p_zero_when_calibrated_and_large_when_overconfident():
    y = np.array([1.0, 0.0] * 50)
    assert h6.ece_p(np.full(100, 0.5), y) == pytest.approx(0.0)
    assert h6.ece_p(np.full(100, 0.95), np.zeros(100)) == pytest.approx(0.95)


def test_false_green_counts_only_rows_at_or_above_the_threshold():
    p = np.array([0.95, 0.90, 0.89, 0.2, 0.99])
    y = np.array([1.0, 0.0, 0.0, 0.0, 1.0])
    fg = h6.false_green(p, y)
    assert fg["n_green"] == 3 and fg["false_green"] == pytest.approx(1 / 3)
    none = h6.false_green(np.array([0.1]), np.array([1.0]))
    assert none["n_green"] == 0 and math.isnan(none["false_green"])


def test_select_feature_picks_the_informative_one():
    best, tab = h6.select_feature(_h6_frame(informative=True))
    assert best == "F2"
    row = tab.set_index("feature")["mean_logloss"]
    assert row["F2"] < row["F1"] and (tab["n_folds"] == 60).all()


def test_freeze_models_one_per_stratum_with_positive_slope_when_informative():
    models = h6.freeze_models(_h6_frame(informative=True), "d_over_hgeo")
    assert sorted(models) == sorted(f"{s}|{p}" for s in PREREGISTERED_SEGMENTERS for p in PROFILES)
    assert all(m["slope"] > 1.0 for m in models.values())


def _unit_models(a, b):
    return {f"{s}|{p}": {"intercept": a, "slope": b} for s in PREREGISTERED_SEGMENTERS for p in PROFILES}


def test_evaluate_h6_flags_overconfident_models_and_naive_override():
    # p ~ 1 en todas partes con 50 % de aciertos: verde falso 0.5 en frozen y en naive
    df = _h6_frame(n_per_stratum=1000, y_const=0.5)
    res = h6.evaluate_h6(df, _unit_models(10.0, 0.0), _unit_models(10.0, 0.0), "d_over_hgeo")
    assert res["h6d"]["verdict"] == "no apoyada" and res["h6d"]["failing"] == 6
    assert res["h6a"]["verdict"] == "apoyada"
    assert res["h6e"]["verdict"] == "no apoyada"           # empate no es mejora estricta


def test_evaluate_h6_without_green_rows_is_not_evaluable_never_unsupported():
    df = _h6_frame(n_per_stratum=1000, y_const=0.5)
    res = h6.evaluate_h6(df, _unit_models(-10.0, 0.0), _unit_models(-10.0, 0.0), "d_over_hgeo")
    assert res["h6d"]["verdict"] == "no evaluable" and res["h6a"]["verdict"] == "no evaluable"


def test_evaluate_h6_auc_and_ece_gradings():
    # 4 estratos con señal perfecta y 2 sin señal: AUC >= 0.85 solo en 4 -> «parcial»
    good = _h6_frame(informative=True, seed=1)
    noise = _h6_frame(informative=False, seed=2)
    noisy_keys = {("otsu", "ideal"), ("otsu", "realistic")}
    mask = [(s, p) in noisy_keys for s, p in zip(good["segmenter"], good["profile"])]
    df = good.copy()
    df.loc[mask, "v_ok"] = noise.loc[mask, "v_ok"].to_numpy()
    res = h6.evaluate_h6(df, _unit_models(-3.0, 3.0), _unit_models(-3.0, 3.0), "d_over_hgeo")
    assert res["h6b"]["count"] == 4 and res["h6b"]["verdict"] == "parcial"


def test_wrong_profile_and_lights_tables_have_consistent_shapes():
    df = _h6_frame(n_per_stratum=600, informative=True)
    frozen = _unit_models(-3.0, 3.0)
    wp = h6.wrong_profile_table(df, frozen, "d_over_hgeo")
    assert len(wp) == 6 and {"auc_right", "auc_wrong", "fg_wrong"} <= set(wp.columns)
    lights = h6.lights_by_level_table(df.assign(t_over_h=1.0), frozen, "d_over_hgeo")
    shares = lights.groupby(["segmenter", "profile", "t_over_h"])["share"].sum()
    assert np.allclose(shares, 1.0)
    shp = h6.by_shape_table(df, frozen, "d_over_hgeo")
    assert len(shp) == 6 * len(SHAPES)
