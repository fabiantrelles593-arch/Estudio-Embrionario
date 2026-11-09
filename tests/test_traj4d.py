"""Banco de pruebas 4D sintético: simulador de cohortes y estimadores lineales."""
import math

import numpy as np
import pandas as pd
import pytest

from geovida.traj4d import (
    FEATURES, K_STAGES, estimator_matrix, evaluate_cell, measurement_bias_function,
    simulate_cohort, smoothed_truth,
)


def test_features_have_the_declared_shape():
    g, s, w = FEATURES["growth"], FEATURES["saturating"], FEATURES["switch"]
    assert g(np.array([0.0]))[0] == pytest.approx(1.0)
    assert g(np.array([2.0]))[0] == pytest.approx(math.exp(1.0))
    taus = np.linspace(-1, 7, 50)
    assert np.all(np.diff(s(taus)) > 0)
    assert w(np.array([3.0]))[0] == pytest.approx(0.5)
    for f in FEATURES.values():
        assert np.all(f(taus) > 0)


def test_cohort_without_noise_equals_the_truth_at_nominal_stages():
    rng = np.random.default_rng(0)
    Y, tau = simulate_cohort(rng, "growth", n=4, sigma_s=0.0, cv=0.0, meas=0.0, n_reps=3)
    assert Y.shape == (3, K_STAGES * 4)
    nominal = np.repeat(np.arange(K_STAGES), 4)
    assert np.allclose(tau, nominal)
    assert np.allclose(Y, FEATURES["growth"](nominal)[None, :])


def test_staging_error_has_the_requested_spread():
    rng = np.random.default_rng(1)
    _, tau = simulate_cohort(rng, "growth", n=200, sigma_s=0.25, cv=0.0, meas=0.0, n_reps=20)
    nominal = np.repeat(np.arange(K_STAGES), 200)
    assert (tau - nominal).std() == pytest.approx(0.25, rel=0.05)


def test_stage_mean_matrix_averages_within_stage_only():
    H = estimator_matrix("stage_mean", n=3)
    assert H.shape == (K_STAGES, K_STAGES * 3)
    assert np.allclose(H.sum(axis=1), 1.0)
    assert np.allclose(H[2, 6:9], 1 / 3) and H[2, :6].sum() == 0


def test_spline_reproduces_a_cubic_exactly_without_staging_error():
    f = lambda t: 0.1 * t**3 - t**2 + 3 * t + 2
    n = 3
    nominal = np.repeat(np.arange(K_STAGES), n).astype(float)
    H = estimator_matrix("spline", n=n)
    assert np.allclose(H @ f(nominal), f(np.arange(K_STAGES)), atol=1e-8)


def test_corrected_spline_removes_the_staging_smoothing_bias():
    f = lambda t: 0.1 * t**3 - t**2 + 3 * t + 2
    sigma, n = 0.5, 3
    nominal = np.repeat(np.arange(K_STAGES), n).astype(float)
    # Valor esperado de lo observado: E[f(k + eps)] (cuadratura exacta p/ polinomio)
    expected_obs = smoothed_truth(f, nominal, sigma)
    truth = f(np.arange(K_STAGES).astype(float))
    naive = estimator_matrix("spline", n=n) @ expected_obs
    corrected = estimator_matrix("spline_corrected", n=n, sigma_assumed=sigma) @ expected_obs
    assert np.abs(naive - truth).max() > 0.05          # sesgo real del ingenuo
    assert np.allclose(corrected, truth, atol=1e-6)    # el corregido lo elimina


def test_corrected_spline_with_zero_sigma_is_the_plain_spline():
    a = estimator_matrix("spline", n=2)
    b = estimator_matrix("spline_corrected", n=2, sigma_assumed=0.0)
    assert np.allclose(a, b)


def test_cell_bias_matches_the_analytic_smoothing_bias():
    sigma = 0.5
    res = evaluate_cell("switch", n=100, sigma_s=sigma, meas=0.0, cv=0.0,
                        estimator="stage_mean", n_reps=40, n_boot=0, seed=3)
    f = FEATURES["switch"]
    stages = np.arange(K_STAGES, dtype=float)
    analytic = smoothed_truth(f, stages, sigma) / f(stages) - 1.0
    assert np.allclose(res["rel_bias"], analytic, atol=0.01)


def test_mse_decomposition_identity():
    res = evaluate_cell("growth", n=3, sigma_s=0.25, meas=0.02, cv=0.08,
                        estimator="stage_mean", n_reps=300, n_boot=0, seed=4)
    assert 0.0 <= res["bias2_share"] <= 1.0
    # irmse^2 = media(sesgo^2) + varianza media
    assert res["irmse"] ** 2 == pytest.approx(
        np.mean(res["rel_bias"] ** 2) + res["mean_rel_var"], rel=1e-9)


def test_bootstrap_coverage_is_near_nominal_when_there_is_no_staging_error():
    res = evaluate_cell("saturating", n=20, sigma_s=0.0, meas=0.02, cv=0.08,
                        estimator="stage_mean", n_reps=400, n_boot=200, seed=5)
    assert 0.90 <= res["mean_coverage"] <= 0.99


def test_bootstrap_is_not_reported_for_one_specimen_per_stage():
    res = evaluate_cell("growth", n=1, sigma_s=0.1, meas=0.02, cv=0.08,
                        estimator="stage_mean", n_reps=20, n_boot=50, seed=6)
    assert np.isnan(res["mean_coverage"])


def test_measurement_bias_function_interpolates_the_median_error():
    rows = []
    for t in (2.0, 4.0, 8.0):
        for e in (0.9, 1.0, 1.1):
            rows.append({"shape": "ball", "segmenter": "otsu", "profile": "ideal",
                         "anisotropy": 1.0, "t_over_h": t, "err_volume": e * 0.2 / t})
    rows.append({"shape": "torus", "segmenter": "otsu", "profile": "ideal",
                 "anisotropy": 1.0, "t_over_h": 4.0, "err_volume": 9.9})
    fn = measurement_bias_function(pd.DataFrame(rows), "ball", "otsu", "ideal", 1.0)
    assert fn(4.0) == pytest.approx(0.05)
    expected = 0.1 + (0.05 - 0.1) * math.log(3 / 2) / math.log(2)  # lineal en log(t/h)
    assert fn(3.0) == pytest.approx(expected)
    assert fn(100.0) == pytest.approx(0.2 / 8.0)  # fuera de rango: se sujeta al borde
