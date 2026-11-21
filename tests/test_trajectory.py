"""Rama de trayectoria de referencia (solo investigación y educación).

No predice el crecimiento ni el aspecto de nadie: calcula dónde cae el tamaño de referencia poblacional en semanas
posteriores, con la incertidumbre de la medida y de la edad propagada. Las ecuaciones son las publicadas por
INTERGROWTH-21st (Papageorghiou et al. 2014; CRL dada la edad, 58 a 105 días); la Tabla 2 de ese artículo sirve de
comprobación de consistencia.
"""
import json

import numpy as np
import pytest

from geovida import dating, trajectory


# Tabla 2 del artículo: CRL media por semana completa, comparada con la ecuación en el día central de la semana.
TABLE2 = [(66.5, 27.47), (73.5, 36.23), (80.5, 49.39), (87.5, 60.78), (94.5, 72.53)]


def test_mean_crl_equation_is_consistent_with_published_weekly_table():
    for ga, published in TABLE2:
        assert abs(trajectory.crl_mean_mm(ga) - published) < 2.0, (ga, trajectory.crl_mean_mm(ga), published)


def test_mean_crl_known_values():
    # −50.6562 + 0.815118·GA + 0.00535302·GA²
    assert trajectory.crl_mean_mm(74.0) == pytest.approx(-50.6562 + 0.815118 * 74 + 0.00535302 * 74 ** 2)
    assert trajectory.crl_sd_mm(74.0) == pytest.approx(-2.21626 + 0.0984894 * 74)


def test_equations_refuse_ages_outside_the_published_range():
    for bad in (57.9, 105.1, 0.0, float("nan")):
        with pytest.raises(ValueError):
            trajectory.crl_mean_mm(bad)
        with pytest.raises(ValueError):
            trajectory.crl_sd_mm(bad)


def test_sd_is_positive_and_growing_across_the_range():
    sds = [trajectory.crl_sd_mm(g) for g in range(58, 106)]
    assert min(sds) > 0 and all(b > a for a, b in zip(sds, sds[1:]))


def test_the_two_published_equations_agree_with_each_other():
    """Edad dada la CRL y CRL dada la edad son dos regresiones distintas: no se invierten una a otra, pero deben quedar cerca."""
    for crl in (20.0, 37.4, 60.0, 80.0):
        back = trajectory.crl_mean_mm(dating.ga_days_intergrowth(crl))
        assert abs(back - crl) < 2.5, (crl, back)


def test_projection_without_any_uncertainty_and_known_age_is_a_single_line():
    p = trajectory.projection(40.0, ga_known_days=75.0, horizons_days=(7,), crl_rel_sd=0.0, n_draws=2000)
    row = p["rows"][0]
    z0 = (40.0 - trajectory.crl_mean_mm(75.0)) / trajectory.crl_sd_mm(75.0)
    want = trajectory.crl_mean_mm(82.0) + z0 * trajectory.crl_sd_mm(82.0)
    assert row["persistence"]["median"] == pytest.approx(want, abs=0.05)
    assert row["persistence"]["hi"] - row["persistence"]["lo"] < 0.1       # sin incertidumbre: un punto
    assert row["regression"]["hi"] - row["regression"]["lo"] > 5.0         # sin persistencia: toda la dispersión poblacional


def test_envelope_contains_both_scenarios_and_the_population_mean():
    p = trajectory.projection(37.6, crl_rel_sd=0.02, horizons_days=(7, 14, 21), n_draws=4000)
    for r in p["rows"]:
        assert r["envelope"]["lo"] <= min(r["persistence"]["lo"], r["regression"]["lo"]) + 1e-9
        assert r["envelope"]["hi"] >= max(r["persistence"]["hi"], r["regression"]["hi"]) - 1e-9
        assert r["envelope"]["lo"] <= r["population_mean_mm"] <= r["envelope"]["hi"]


def test_more_measurement_uncertainty_gives_a_wider_persistence_band():
    narrow = trajectory.projection(37.6, crl_rel_sd=0.005, horizons_days=(14,), n_draws=6000)["rows"][0]["persistence"]
    wide = trajectory.projection(37.6, crl_rel_sd=0.06, horizons_days=(14,), n_draws=6000)["rows"][0]["persistence"]
    assert (wide["hi"] - wide["lo"]) > (narrow["hi"] - narrow["lo"])


def test_age_dated_from_this_same_length_carries_the_formula_spread():
    p = trajectory.projection(37.4, crl_rel_sd=0.0, horizons_days=(7,), n_draws=6000)
    ga = p["ga_now"]
    assert ga["source"] == "estimada con esta misma CRL"
    assert ga["median_days"] == pytest.approx(dating.ga_days_intergrowth(37.4), abs=0.3)
    want_width = 2 * 1.645 * dating.sd_ga_days_intergrowth(37.4)         # intervalo 90 % de una normal con la SD de la fórmula
    assert (ga["hi_days"] - ga["lo_days"]) == pytest.approx(want_width, abs=0.6)


def test_horizons_beyond_the_published_range_are_flagged_not_computed():
    p = trajectory.projection(37.4, horizons_days=(7, 70), n_draws=1000)
    far = [r for r in p["rows"] if r["days_ahead"] == 70][0]
    assert far["in_source_range"] is False
    assert far["envelope"] is None and far["population_mean_mm"] is None


def test_length_outside_the_dating_range_is_refused_when_age_must_be_estimated():
    with pytest.raises(ValueError):
        trajectory.projection(10.0, n_draws=100)
    # con la edad dada por otra vía no hace falta que la CRL esté en el rango de la fórmula de edad
    trajectory.projection(10.0, ga_known_days=60.0, horizons_days=(7,), n_draws=100)


def test_projection_is_reproducible_for_a_given_seed():
    a = trajectory.projection(37.6, crl_rel_sd=0.02, horizons_days=(7,), n_draws=3000, seed=5)
    b = trajectory.projection(37.6, crl_rel_sd=0.02, horizons_days=(7,), n_draws=3000, seed=5)
    assert a == b


def test_report_states_what_it_does_not_predict():
    p = trajectory.projection(37.6, crl_rel_sd=0.02, horizons_days=(7, 14), n_draws=2000)
    text = trajectory.report_markdown(p)
    assert "no predice" in text and "aspecto" in text
    assert "persistencia" in text and "sin validar" in text
    json.dumps(p)


def test_cli_trajectory_runs_and_writes_outputs(tmp_path):
    from geovida import cli
    out = tmp_path / "t"
    assert cli.main(["trajectory", "--crl", "37.6", "--crl-rel-sd", "0.02", "--out", str(out), "--draws", "2000"]) == 0
    assert (out / "trayectoria.md").exists() and (out / "trayectoria.json").exists()
    assert "no predice" in (out / "trayectoria.md").read_text()


def test_cli_trajectory_refuses_a_length_outside_the_range(tmp_path):
    from geovida import cli
    assert cli.main(["trajectory", "--crl", "9", "--out", str(tmp_path / "x")]) != 0
