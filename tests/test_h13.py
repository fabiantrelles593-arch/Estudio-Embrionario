"""H13: diseño del experimento y análisis (biometría con certificado de incertidumbre).

Qué haría fallar cada prueba:
* una semilla mal derivada haría que dos corridas «iguales» difirieran, o que dos casos compartieran ruido;
* un caso «fuera de la caja» que cayera dentro (o al revés) invalidaría la prueba de la guardia;
* una regla de veredicto con un umbral desplazado (≤ vs <, límite superior vs punto) cambiaría conclusiones;
* un cálculo de error de edad o de lado del umbral mal hecho se vería en los casos construidos a mano.
"""
import numpy as np
import pandas as pd
import pytest

from geovida import biometry as bio
from geovida import dating, h13

TINY = {bio.BODY: {"n": (30.0, 50.0), "f": (1.0, 2.0)}, bio.SLOT: {"n": (10.0, 16.0), "f": (1.0, 2.0)}}


# --- diseño -----------------------------------------------------------------------------------

def test_calibration_cases_cover_the_whole_grid_with_distinct_seeds():
    cases = h13.calibration_cases(bio.BODY, reps=3, base_seed=1, grid=TINY)
    assert len(cases) == 2 * 2 * 3
    assert {(c["n"], c["fwhm_px"]) for c in cases} == {(30.0, 1.0), (30.0, 2.0), (50.0, 1.0), (50.0, 2.0)}
    assert len({tuple(c["seed"]) for c in cases}) == len(cases)        # ningún par de casos comparte ruido
    again = h13.calibration_cases(bio.BODY, reps=3, base_seed=1, grid=TINY)
    assert [c["seed"] for c in again] == [c["seed"] for c in cases]
    other_kind = h13.calibration_cases(bio.SLOT, reps=3, base_seed=1, grid=TINY)
    assert not ({tuple(c["seed"]) for c in cases} & {tuple(c["seed"]) for c in other_kind})


def test_default_grids_are_what_the_preregistration_says():
    g = h13.CAL_GRID
    assert g[bio.BODY]["n"] == (50.0, 80.0, 130.0, 210.0, 300.0)
    assert g[bio.BODY]["f"] == (1.0, 2.0, 3.5, 5.0)
    assert g[bio.SLOT]["n"] == (10.0, 15.0, 22.0, 33.0, 50.0)
    assert g[bio.SLOT]["f"] == (1.0, 1.5, 2.2, 3.3, 5.0)


def test_confirmation_cases_are_reproducible_and_split_in_and_out_of_the_box():
    a = h13.confirmation_cases(40, 20, base_seed=9, grid=TINY)
    b = h13.confirmation_cases(40, 20, base_seed=9, grid=TINY)
    assert [(c["kind"], c["n"], c["fwhm_px"], c["size_mm"], c["region"]) for c in a] == \
           [(c["kind"], c["n"], c["fwhm_px"], c["size_mm"], c["region"]) for c in b]
    assert len(a) == 2 * (40 + 20)
    for c in a:
        g = TINY[c["kind"]]
        inside = g["n"][0] <= c["n"] <= g["n"][-1] and g["f"][0] <= c["fwhm_px"] <= g["f"][-1]
        assert (c["region"] == "in") == inside, c
    regions = {c["region"] for c in a}
    assert regions == {"in", "n_high", "n_low", "f_high", "f_low"}


def test_confirmation_sizes_are_in_the_declared_ranges():
    cases = h13.confirmation_cases(60, 20, base_seed=4, grid=TINY)
    for c in cases:
        lo, hi = h13.BODY_SIZE_RANGE_MM if c["kind"] == bio.BODY else h13.SLOT_SIZE_RANGE_MM
        assert lo <= c["size_mm"] <= hi


def test_outside_cases_are_clearly_outside_not_at_the_edge():
    cases = h13.confirmation_cases(10, 40, base_seed=5, grid=TINY)
    for c in cases:
        g = TINY[c["kind"]]
        if c["region"] == "n_high":
            assert c["n"] >= 1.2 * g["n"][-1]
        if c["region"] == "n_low":
            assert c["n"] <= g["n"][0] / 1.2
        if c["region"] == "f_high":
            assert c["fwhm_px"] >= 1.2 * g["f"][-1]
        if c["region"] == "f_low":
            assert c["fwhm_px"] <= g["f"][0] / 1.2


# --- calibración y confirmación de punta a punta (cuadrícula diminuta) -------------------------

@pytest.fixture(scope="module")
def tiny_models():
    df = h13.run_calibration(reps=4, base_seed=21, n_jobs=1, grid=TINY)
    assert set(df.columns) >= {"kind", "segmenter", "n", "fwhm_px", "rep", "err_px"}
    return h13.fit_models(df), df


def test_calibration_makes_one_model_per_kind_and_segmenter(tiny_models):
    models, df = tiny_models
    assert set(models) == {f"{k}|{s}" for k in bio.KINDS for s in bio.SEGMENTERS}
    assert len(df) == (2 * 2 * 4 + 2 * 2 * 4) * len(bio.SEGMENTERS)


def test_confirmation_rows_have_certificates_and_a_clamped_counterfactual(tiny_models):
    models, _ = tiny_models
    cases = h13.confirmation_cases(6, 4, base_seed=22, grid=TINY)
    df = h13.run_confirmation(cases, models, n_jobs=1)
    again = h13.run_confirmation(cases, models, n_jobs=1)
    pd.testing.assert_frame_equal(df, again)
    assert len(df) == len(cases) * len(bio.SEGMENTERS)
    need = {"idx", "kind", "segmenter", "region", "n_nominal", "fwhm_px", "truth_mm", "h_mm", "measured_mm",
            "in_domain", "light", "p", "bias_mm", "sd_mm", "measurement_share", "correct", "ga_err_days",
            "light_clamped", "p_clamped"}
    assert need <= set(df.columns)
    assert df[df["kind"] == bio.SLOT]["ga_err_days"].isna().all()
    body = df[df["kind"] == bio.BODY]
    assert body["measurement_share"].notna().sum() == body["in_domain"].sum()   # solo con certificado
    # la guardia sí se prueba aquí: fuera de la caja nominal el certificado no puede ser verde
    # cuando además el n medido queda fuera; lo que decide es el modelo, así que solo se exige coherencia
    assert (df[~df["in_domain"]]["light"] != "verde").all()


def test_correct_flags_are_computed_from_truth_not_from_the_certificate():
    row = h13.score_body(truth_mm=45.0, measured_mm=45.0 + 0.0)
    assert row["ga_err_days"] == pytest.approx(0.0) and row["correct"]
    d = dating.dga_dcrl(45.0)
    big = h13.score_body(truth_mm=45.0, measured_mm=45.0 + 2.0 / d)       # error de edad ≈ +2 d (1.ª orden)
    assert not big["correct"] and big["ga_err_days"] == pytest.approx(2.0, abs=0.1)
    assert h13.score_slot(truth_mm=3.2, measured_mm=2.9)["correct"] is False        # lados distintos
    assert h13.score_slot(truth_mm=2.0, measured_mm=2.9)["correct"] is True
    assert h13.score_slot(truth_mm=3.0, measured_mm=3.0)["correct"] is True         # en el umbral: «arriba»


# --- veredictos -------------------------------------------------------------------------------

def _frame(kind, flags, region="in", light="verde", p=0.95, in_domain=True, seg="smoothed_otsu"):
    """flags: lista de bool «correct». Una fila por flag, todas del mismo tipo."""
    n = len(flags)
    return pd.DataFrame({"kind": kind, "segmenter": seg, "region": region, "light": light, "p": p,
                         "in_domain": in_domain, "correct": list(flags), "idx": range(n),
                         "bias_mm": 0.0, "sd_mm": 0.1, "truth_mm": 3.0, "measured_mm": 3.0, "h_mm": 0.1,
                         "measurement_share": 0.01, "light_clamped": light, "p_clamped": p,
                         "ga_err_days": np.nan, "n_nominal": 100.0, "fwhm_px": 2.0})


def test_false_green_verdict_rules():
    ok = h13.false_green_verdict(_frame(bio.BODY, [True] * 300), n_boot=300, seed=1)
    assert ok["verdict"] == "apoyada" and ok["n_green"] == 300 and ok["false_green"] == 0.0
    bad = h13.false_green_verdict(_frame(bio.BODY, [True] * 200 + [False] * 100), n_boot=300, seed=1)
    assert bad["verdict"] == "no apoyada" and bad["ci"][0] > 0.10
    few = h13.false_green_verdict(_frame(bio.BODY, [True] * 20), n_boot=300, seed=1)
    assert few["verdict"] == "no evaluable"
    edge = h13.false_green_verdict(_frame(bio.BODY, [True] * 88 + [False] * 12), n_boot=500, seed=1)
    assert edge["verdict"] == "no concluyente" and edge["ci"][0] <= 0.10 <= edge["ci"][1]


def test_false_green_only_counts_green_in_domain_cases_of_the_primary_segmenter():
    df = pd.concat([
        _frame(bio.BODY, [True] * 100),
        _frame(bio.BODY, [False] * 100, light="amarillo"),                 # no verdes: no cuentan
        _frame(bio.BODY, [False] * 100, seg="otsu"),                       # otro segmentador: no es el primario
        _frame(bio.BODY, [False] * 100, region="n_high"),                  # fuera de la caja: no es H13a
    ], ignore_index=True)
    r = h13.false_green_verdict(df[df["kind"] == bio.BODY], n_boot=200, seed=1)
    assert r["n_green"] == 100 and r["false_green"] == 0.0


def test_calibration_verdict_uses_point_ece_and_needs_enough_cases():
    rng = np.random.default_rng(0)
    p = rng.uniform(0.0, 1.0, 600)
    good = _frame(bio.BODY, (rng.uniform(size=600) < p).tolist(), light="amarillo")
    good["p"] = p
    r = h13.calibration_verdict(good)
    assert r["verdict"] == "apoyada" and r["ece"] <= 0.10 and r["n"] == 600
    bad = good.copy()
    bad["correct"] = rng.uniform(size=600) < 0.1        # p dice una cosa y la realidad otra
    assert h13.calibration_verdict(bad)["verdict"] == "no apoyada"
    assert h13.calibration_verdict(good.iloc[:50])["verdict"] == "no evaluable"


def test_guard_verdict_is_about_the_leak_rate_outside_the_box_not_zero_greens():
    # n se estima a partir de la medida, así que cerca del borde algo puede filtrarse: criterio = tasa de fuga ≤ 5 %
    outside = _frame(bio.BODY, [True] * 400, region="n_high", light="amarillo", in_domain=False)
    clean = h13.guard_verdict(outside, n_boot=300, seed=1)
    assert clean["verdict"] == "apoyada" and clean["leak_rate"] == 0.0 and clean["n_out"] == 400
    leaky = outside.copy()
    leaky.loc[:79, "light"] = "verde"                       # 20 % de fuga
    r = h13.guard_verdict(leaky, n_boot=300, seed=1)
    assert r["verdict"] == "no apoyada" and r["leak_n_green"] == 80 and r["leak_ci"][0] > 0.05
    border = outside.copy()
    border.loc[:19, "light"] = "verde"                      # 20/400 = 5 %: el intervalo contiene 5 %
    assert h13.guard_verdict(border, n_boot=500, seed=1)["verdict"] == "no concluyente"
    assert h13.guard_verdict(outside.iloc[:20], n_boot=300, seed=1)["verdict"] == "no evaluable"


def test_guard_verdict_reports_correctness_of_the_leaked_greens():
    outside = _frame(bio.BODY, [True] * 200, region="n_high", light="amarillo", in_domain=False)
    outside.loc[:9, "light"] = "verde"
    outside.loc[:2, "correct"] = False
    r = h13.guard_verdict(outside, n_boot=100, seed=1)
    assert r["leak_n_green"] == 10 and r["leak_false_green"] == pytest.approx(0.3)


def test_guard_verdict_reports_how_often_clamping_would_have_been_a_false_green():
    outside = _frame(bio.BODY, [True] * 60 + [False] * 60, region="n_high", light="amarillo", in_domain=False)
    outside["light_clamped"] = "verde"
    r = h13.guard_verdict(outside, n_boot=100, seed=1)
    assert r["clamped_n_green"] == 120 and r["clamped_false_green"] == pytest.approx(0.5)


def test_human_yardstick_reports_all_in_domain_cases_and_the_green_ones_separately():
    df = _frame(bio.SLOT, [True] * 6)
    df["measured_mm"] = [3.0, 3.1, 2.9, 3.5, 3.0, 2.0]       # errores 0, .1, −.1, .5, 0, −1.0 (bias 0, truth 3.0)
    df["light"] = ["verde"] * 4 + ["amarillo"] * 2
    r = h13.human_yardstick(df)
    assert r["all"]["n"] == 6 and r["green"]["n"] == 4
    assert r["all"]["median_abs_error_mm"] == pytest.approx(0.1)
    assert r["green"]["median_abs_error_mm"] == pytest.approx(0.1)
    assert r["all"]["p95_abs_error_mm"] > r["green"]["p95_abs_error_mm"]
    assert r["human_sd_intra_mm"] == pytest.approx(0.35 / 2 ** 0.5)
    assert r["human_sd_inter_mm"] == pytest.approx(0.56 / 2 ** 0.5)


def test_evaluate_h13_returns_every_hypothesis_key():
    df = pd.concat([_frame(bio.BODY, [True] * 400), _frame(bio.SLOT, [True] * 400)], ignore_index=True)
    out = h13.evaluate_h13(df, n_boot=200, seed=3)
    assert set(out) == {"h13a", "h13b", "h13c", "h13d", "h13e", "h13f"}
    assert out["h13a"]["verdict"] == "apoyada" and out["h13b"]["verdict"] == "apoyada"
