import numpy as np
import pandas as pd
import pytest

from geovida.analysis import auc_score
from geovida.budget import (
    add_measured_q, adequacy, h_geo, p_volume_ok, q_hat_over_hgeo, traffic_light,
)
from geovida.experiment import Condition, run_condition


def test_h_geo_is_the_geometric_mean_of_the_spacing():
    assert h_geo((1.0, 1.0, 8.0)) == pytest.approx(2.0)


def test_q_hat_over_hgeo_of_an_exact_ball_is_r_over_3_in_voxels():
    # V/S = r/3 para una bola; con h = 0.1 y r = 1 -> Q/h = 1/3/0.1
    v, s = 4 / 3 * np.pi, 4 * np.pi
    assert q_hat_over_hgeo(v, s, (0.1, 0.1, 0.1)) == pytest.approx(1 / 3 / 0.1)


@pytest.mark.parametrize("v,s", [(0.0, 1.0), (1.0, 0.0), (float("nan"), 1.0), (-1.0, 1.0)])
def test_unmeasurable_input_gives_nan_not_an_exception(v, s):
    assert np.isnan(q_hat_over_hgeo(v, s, (1, 1, 1)))


def test_traffic_light_thresholds_are_the_preregistered_ones():
    assert traffic_light(0.90) == "verde"
    assert traffic_light(0.8999) == "amarillo"
    assert traffic_light(0.50) == "amarillo"
    assert traffic_light(0.4999) == "rojo"
    assert traffic_light(float("nan")) == "rojo"


def test_p_volume_ok_is_zero_when_q_cannot_be_measured():
    assert p_volume_ok(float("nan"), "otsu", "realistic") == 0.0


def test_auc_score_perfect_inverted_and_ties():
    assert auc_score([0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1]) == 1.0
    assert auc_score([0.9, 0.8, 0.2, 0.1], [0, 0, 1, 1]) == 0.0
    assert auc_score([0.5, 0.5, 0.5, 0.5], [0, 1, 0, 1]) == 0.5
    assert np.isnan(auc_score([0.1, 0.2], [1, 1]))


def test_empty_mask_is_red_and_explains_why():
    r = adequacy(np.zeros((8, 8, 8), bool), (1, 1, 1), "otsu", "realistic")
    assert r["light"] == "rojo" and r["p_volume_ok"] == 0.0 and "vacía" in r["motivo"]


def test_measured_q_tracks_true_q_for_a_well_resolved_ball():
    # Piloto (semilla 20261115, global, ideal, aniso 1, t/h = 12): mediana de
    # Q_hat/Q_true = 0.99 en la bola.
    rows = run_condition(Condition("ball", 12.0, 1.0, "ideal", 0), segmenters=("global",))
    df = add_measured_q(pd.DataFrame(rows))
    q_true = df["volume_true"] / df["area_true"] * df["t_over_h"]
    assert df["q_hat_over_hgeo"].iloc[0] / q_true.iloc[0] == pytest.approx(1.0, abs=0.04)


def test_measured_q_is_inflated_at_low_resolution():
    # Piloto: a t/h = 3, Q_hat/Q_true = 1.44 en la bola (area subestimada).
    rows = run_condition(Condition("ball", 3.0, 1.0, "ideal", 0), segmenters=("global",))
    df = add_measured_q(pd.DataFrame(rows))
    q_true = df["volume_true"] / df["area_true"] * df["t_over_h"]
    assert df["q_hat_over_hgeo"].iloc[0] / q_true.iloc[0] > 1.2
