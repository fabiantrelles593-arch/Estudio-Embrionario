"""Datación por longitud cráneo-rabadilla (CRL) con presupuesto de incertidumbre de medida.

Fórmulas verificadas en fuentes abiertas:
* INTERGROWTH-21st (Papageorghiou 2014): GA(días) = 40.9041 + 3.21585·√CRL + 0.348956·CRL,
  SD(GA) = 2.39102 + 0.0193474·CRL, CRL 15–95 mm, n = 4265.
* Robinson (1973/1975), citada en arXiv 1110.6631: GA(días) = 8.052·√CRL + 23.73 (sin SD en esa fuente).

Qué haría fallar cada prueba:
* un coeficiente cambiado rompería los valores calculados a mano;
* una derivada mal calculada se vería contra la diferencia numérica;
* una probabilidad que no sumara bien (simetría, sd → 0) delataría un error en la normal.
"""
import math

import pytest

from geovida import dating


def test_intergrowth_mean_matches_hand_computation():
    crl = 37.4
    expect = 40.9041 + 3.21585 * math.sqrt(crl) + 0.348956 * crl
    assert dating.ga_days_intergrowth(crl) == pytest.approx(expect, rel=1e-12)
    assert 73.0 < expect < 74.0            # ≈ 10 semanas + 4 días


def test_intergrowth_sd_matches_hand_computation():
    assert dating.sd_ga_days_intergrowth(45.0) == pytest.approx(2.39102 + 0.0193474 * 45.0)


def test_robinson_formula():
    assert dating.ga_days_robinson(36.0) == pytest.approx(8.052 * 6.0 + 23.73)


def test_derivative_matches_numeric_difference():
    for crl in (20.0, 45.0, 84.0):
        eps = 1e-5
        num = (dating.ga_days_intergrowth(crl + eps) - dating.ga_days_intergrowth(crl - eps)) / (2 * eps)
        assert dating.dga_dcrl(crl) == pytest.approx(num, rel=1e-6)


def test_weeks_days_rounds_to_whole_days():
    assert dating.weeks_days(73.62) == (10, 4)
    assert dating.weeks_days(70.0) == (10, 0)


def test_range_and_input_checks():
    assert dating.INTERGROWTH_RANGE_MM == (15.0, 95.0)
    assert dating.in_formula_range(15.0) and dating.in_formula_range(95.0)
    assert not dating.in_formula_range(14.9) and not dating.in_formula_range(95.1)
    for bad in (0.0, -3.0, float("nan")):
        with pytest.raises(ValueError):
            dating.ga_days_intergrowth(bad)


# --- certificado ------------------------------------------------------------------------------

def test_prob_within_tolerance_is_symmetric_and_bounded():
    p = dating.prob_within(bias=0.0, sd=1.0, tol=1.0)
    assert p == pytest.approx(math.erf(1.0 / math.sqrt(2.0)), rel=1e-12)      # ±1 sd = 0.6827
    assert dating.prob_within(bias=0.0, sd=0.0, tol=1.0) == 1.0
    assert dating.prob_within(bias=2.0, sd=0.0, tol=1.0) == 0.0
    assert dating.prob_within(0.5, 1.0, 1.0) == pytest.approx(dating.prob_within(-0.5, 1.0, 1.0))


def test_certificate_green_when_measurement_error_is_small_and_in_range():
    c = dating.certify_dating(crl_mm=45.0, bias_mm=0.0, sd_mm=0.3)
    assert c["light"] == "verde" and c["in_range"] and c["p_within_tolerance"] >= 0.90
    assert c["sd_formula_days"] == pytest.approx(2.39102 + 0.0193474 * 45.0)
    assert 0.0 <= c["measurement_share"] <= 1.0
    assert c["ga_weeks_days"][0] >= 10


def test_certificate_red_when_measurement_error_dominates():
    c = dating.certify_dating(crl_mm=45.0, bias_mm=0.0, sd_mm=8.0)
    assert c["light"] == "rojo" and c["measurement_share"] > 0.5


def test_certificate_never_green_outside_formula_range():
    c = dating.certify_dating(crl_mm=10.0, bias_mm=0.0, sd_mm=0.01)
    assert not c["in_range"] and c["light"] != "verde"
    c2 = dating.certify_dating(crl_mm=120.0, bias_mm=0.0, sd_mm=0.01)
    assert not c2["in_range"] and c2["light"] != "verde"


def test_measurement_share_is_variance_fraction():
    c = dating.certify_dating(crl_mm=45.0, bias_mm=0.0, sd_mm=1.0)
    s_meas = abs(dating.dga_dcrl(45.0)) * 1.0
    s_form = dating.sd_ga_days_intergrowth(45.0)
    assert c["measurement_share"] == pytest.approx(s_meas**2 / (s_meas**2 + s_form**2))


# --- decisión respecto de un umbral -----------------------------------------------------------

def test_side_certificate_half_at_threshold_and_high_far_from_it():
    at = dating.certify_side(measured=3.0, bias=0.0, sd=0.3, threshold=3.0)
    assert at["p_same_side"] == pytest.approx(0.5, abs=1e-9) and at["light"] == "rojo"
    far = dating.certify_side(measured=4.5, bias=0.0, sd=0.3, threshold=3.0)
    assert far["p_same_side"] > 0.999 and far["light"] == "verde"
    near_below = dating.certify_side(measured=2.0, bias=0.0, sd=0.3, threshold=3.0)
    assert near_below["side"] == "debajo" and near_below["p_same_side"] > 0.999


def test_side_certificate_uses_bias_to_move_the_posterior_mean():
    # el método mide 0.3 mm de menos: un valor medido de 2.9 corresponde a ~3.2 (arriba del umbral).
    # El umbral queda a (3.2 − 3.0)/0.1 = 2 desviaciones de la media posterior, así que la probabilidad
    # de que el lado medido («debajo») sea el verdadero es Φ(−2) = 0.0227501319 (no < 0.01: esa cota
    # de la primera versión de esta prueba era un error de aritmética, no del código).
    c = dating.certify_side(measured=2.9, bias=-0.3, sd=0.1, threshold=3.0)
    assert c["side"] == "debajo" and c["light"] == "rojo"
    assert c["p_same_side"] == pytest.approx(0.0227501319, abs=1e-9)
    assert c["posterior_mean"] == pytest.approx(3.2)


def test_side_certificate_zero_sd_is_certain_or_impossible():
    assert dating.certify_side(2.0, 0.0, 0.0, 3.0)["p_same_side"] == 1.0
    assert dating.certify_side(3.5, -1.0, 0.0, 3.0)["p_same_side"] == 1.0   # media posterior 4.5
