"""Logit de varias variables con ridge, serializable, para los modelos congelados de v0.4."""
import json

import numpy as np
import pytest

from geovida.analysis import fit_logit_multi, predict_logit_multi


def test_recovers_known_coefficients():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(40000, 2))
    true = np.array([0.5, 1.5, -1.0])
    p = 1 / (1 + np.exp(-(true[0] + X @ true[1:])))
    y = (rng.random(len(p)) < p).astype(float)
    model = fit_logit_multi(X, y, ridge=1e-3)
    got = np.array([model["intercept"], *model["coef"]])
    assert got == pytest.approx(true, abs=0.08)


def test_predictions_are_probabilities_and_the_model_survives_json():
    rng = np.random.default_rng(2)
    X = rng.normal(size=(500, 3))
    y = (X[:, 0] + 0.3 * rng.normal(size=500) > 0).astype(float)
    model = fit_logit_multi(X, y, features=("a", "b", "c"))
    p = predict_logit_multi(model, X)
    assert ((p > 0) & (p < 1)).all() and model["features"] == ["a", "b", "c"]
    assert predict_logit_multi(json.loads(json.dumps(model)), X) == pytest.approx(p)


def test_ridge_keeps_coefficients_finite_under_perfect_separation():
    x = np.linspace(-1, 1, 200)[:, None]
    y = (x[:, 0] > 0).astype(float)
    model = fit_logit_multi(x, y)
    assert np.isfinite(model["coef"]).all() and abs(model["coef"][0]) < 1e3


def test_a_constant_column_gets_a_zero_coefficient_instead_of_failing():
    rng = np.random.default_rng(3)
    X = np.column_stack([rng.normal(size=400), np.full(400, 2.0)])
    y = (X[:, 0] > 0).astype(float)
    model = fit_logit_multi(X, y)
    assert model["coef"][1] == pytest.approx(0.0, abs=1e-9)


def test_one_dimensional_input_is_accepted():
    rng = np.random.default_rng(4)
    x = rng.normal(size=300)
    y = (x > 0).astype(float)
    model = fit_logit_multi(x, y)
    assert predict_logit_multi(model, x).shape == (300,)
