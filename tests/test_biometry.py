"""Biometría fetal temprana simulada (Programa B, H13): fantomas 2D con verdad exacta, medidas,
modelo de error por interpolación y certificados de datación y de decisión.

Solo investigación y educación. Las imágenes son sintéticas; no hay datos de personas.

Qué haría fallar cada prueba:
* una verdad mal definida (longitud de la cápsula, grosor de la ranura) desplazaría todas las comparaciones;
* una medida de Feret o de grosor con un error de ±1 píxel se vería en los casos de forma exacta;
* una interpolación mal hecha se vería en el punto medio entre nodos de la tabla;
* un certificado que diera verde fuera de la zona calibrada rompería la guardia de dominio.
"""
import itertools
import json
import math

import numpy as np
import pandas as pd
import pytest

from geovida import biometry as bio


# --- fantomas ---------------------------------------------------------------------------------

def test_body_phantom_is_a_capsule_with_exact_length():
    ph = bio.make_body(40.0)
    assert ph.t == 40.0 and ph.half_extent == (20.0, 10.0)
    inside = ph.contains(np.array([[19.99, 0.0], [20.01, 0.0], [0.0, 9.99], [0.0, 10.01],
                                   [14.0, 7.0], [17.0, 8.0], [-19.99, 0.0]]))
    assert inside.tolist() == [True, False, True, False, True, False, True]
    assert ph.truth.betti == (1, 0) and ph.truth.chi == 1


def test_slot_phantom_has_a_dark_gap_of_exact_thickness():
    ph = bio.make_slot(3.0)
    assert ph.t == 3.0 and ph.half_extent == (10.5, 7.5)
    pts = np.array([[0.0, 0.0], [0.0, 1.4], [0.0, 1.6], [5.9, 0.0], [6.1, 0.0], [10.4, 0.0], [10.6, 0.0]])
    # claro = bloque y no ranura; la ranura es un estadio de radio T/2 y largo total 4T
    assert ph.contains(pts).tolist() == [False, False, True, False, True, True, False]
    assert ph.truth.betti == (1, 1) and ph.truth.t_void == 3.0


@pytest.mark.parametrize("bad", [0.0, -1.0])
def test_phantoms_reject_non_positive_size(bad):
    with pytest.raises(ValueError):
        bio.make_body(bad)
    with pytest.raises(ValueError):
        bio.make_slot(bad)


# --- medidas ----------------------------------------------------------------------------------

def test_feret_of_a_rectangle_is_its_diagonal_in_pixel_corners():
    m = np.zeros((20, 30), bool)
    m[5:8, 4:14] = True                      # 3 × 10 píxeles
    assert bio.feret_length_mm(m, 0.5) == pytest.approx(math.hypot(10, 3) * 0.5)


def test_feret_of_one_pixel_and_of_empty_mask():
    m = np.zeros((5, 5), bool)
    m[2, 2] = True
    assert bio.feret_length_mm(m, 2.0) == pytest.approx(math.sqrt(2) * 2.0)
    assert bio.feret_length_mm(np.zeros((5, 5), bool), 1.0) == 0.0


def test_feret_matches_brute_force_on_a_random_blob():
    rng = np.random.default_rng(7)
    m = np.zeros((40, 40), bool)
    m[10:30, 8:35] = rng.random((20, 27)) > 0.3
    ys, xs = np.nonzero(bio.largest_component(m))
    corners = np.array([(x + dx, y + dy) for x, y in zip(xs, ys) for dx in (0, 1) for dy in (0, 1)], float)
    brute = max(math.dist(a, b) for a, b in itertools.combinations(map(tuple, corners), 2))
    assert bio.feret_length_mm(m, 1.0) == pytest.approx(brute)


@pytest.mark.parametrize("width", [3, 5, 7])
def test_gap_thickness_of_an_odd_channel_is_exact(width):
    m = np.ones((40, 70), bool)
    r0 = 20 - width // 2
    m[r0:r0 + width, 10:60] = False          # canal cerrado: no toca el borde
    assert bio.gap_thickness_mm(m, 0.1) == pytest.approx(width * 0.1)


def test_gap_thickness_is_zero_without_a_hole_and_uses_the_biggest_hole():
    full = np.ones((30, 30), bool)
    assert bio.gap_thickness_mm(full, 1.0) == 0.0
    m = np.ones((60, 80), bool)
    m[10:13, 10:40] = False                  # 3 de ancho
    m[35:40, 10:40] = False                  # 5 de ancho (más área)
    assert bio.gap_thickness_mm(m, 1.0) == pytest.approx(5.0)


def test_gap_open_to_the_border_is_not_a_hole():
    m = np.ones((20, 30), bool)
    m[8:11, :] = False                       # atraviesa: separa el bloque, no es un hueco
    assert bio.gap_thickness_mm(m, 1.0) == 0.0


# --- simulación y medida de punta a punta -----------------------------------------------------

def test_run_case_is_reproducible_and_depends_on_the_seed():
    a = bio.run_case(bio.BODY, 40.0, 100, 2.0, seed=11)
    b = bio.run_case(bio.BODY, 40.0, 100, 2.0, seed=11)
    c = bio.run_case(bio.BODY, 40.0, 100, 2.0, seed=12)
    assert a == b and a != c
    assert set(a["measured_mm"]) == set(bio.SEGMENTERS)
    assert a["h_mm"] == pytest.approx(0.4) and a["truth_mm"] == 40.0


@pytest.mark.parametrize("kind,size,n", [(bio.BODY, 40.0, 120), (bio.SLOT, 3.0, 24)])
def test_without_noise_and_with_small_blur_the_error_is_about_a_pixel(kind, size, n):
    r = bio.run_case(kind, size, n, 1.0, seed=5, looks=0)
    h = r["h_mm"]
    for seg, meas in r["measured_mm"].items():
        assert abs(meas - size) / h <= 2.5, (seg, meas)


def test_a_gap_much_thinner_than_the_blur_is_not_found():
    # grosor 8 px y PSF de 16 px (el doble). Con PSF 6 px el hueco todavía se ve (≈ 6 px, sesgo bajo):
    # la primera versión de esta prueba no ponía el hueco por debajo de lo que el desenfoque borra.
    r = bio.run_case(bio.SLOT, 3.0, 8, 16.0, seed=3, looks=0)
    assert r["measured_mm"]["smoothed_otsu"] < 3.0 * 0.6


# --- modelo de error --------------------------------------------------------------------------

N_NODES = (30.0, 60.0, 120.0)
F_NODES = (1.0, 2.0, 4.0)


def _table(kind="body", segmenter="smoothed_otsu", bias=lambda n, f: 0.1 * math.log(n) + 0.2 * f,
           sd=lambda n, f: 0.5 + 0.1 * f):
    rows = []
    for n, f in itertools.product(N_NODES, F_NODES):
        b, d = bias(n, f), sd(n, f)
        for e in (b - d, b, b + d):          # media b, desviación (ddof=1) d
            rows.append({"kind": kind, "segmenter": segmenter, "n": n, "fwhm_px": f, "err_px": e})
    return pd.DataFrame(rows)


def test_error_model_recovers_node_values_exactly():
    model = bio.ErrorModel.from_calibration(_table(), "body", "smoothed_otsu")
    for n, f in itertools.product(N_NODES, F_NODES):
        b, s = model.predict(n, f)
        assert b == pytest.approx(0.1 * math.log(n) + 0.2 * f)
        assert s == pytest.approx(0.5 + 0.1 * f)


def test_error_model_interpolates_linearly_in_log_n_and_log_fwhm():
    model = bio.ErrorModel.from_calibration(_table(), "body", "smoothed_otsu")
    n_mid, f_mid = math.sqrt(30.0 * 60.0), math.sqrt(1.0 * 2.0)       # punto medio en escala log
    corners = [(30.0, 1.0), (30.0, 2.0), (60.0, 1.0), (60.0, 2.0)]
    expect_b = np.mean([0.1 * math.log(n) + 0.2 * f for n, f in corners])
    expect_s = np.mean([0.5 + 0.1 * f for n, f in corners])
    b, s = model.predict(n_mid, f_mid)
    assert b == pytest.approx(expect_b) and s == pytest.approx(expect_s)


def test_error_model_refuses_outside_the_calibrated_box():
    model = bio.ErrorModel.from_calibration(_table(), "body", "smoothed_otsu")
    assert model.predict(30.0, 1.0) is not None and model.predict(120.0, 4.0) is not None   # bordes: dentro
    for n, f in [(29.0, 2.0), (121.0, 2.0), (60.0, 0.9), (60.0, 4.1), (0.0, 2.0), (-5.0, 2.0)]:
        assert model.predict(n, f) is None


def test_error_model_needs_a_complete_grid_and_two_reps():
    df = _table()
    with pytest.raises(ValueError):
        bio.ErrorModel.from_calibration(df.iloc[3:], "body", "smoothed_otsu")           # falta un nodo
    with pytest.raises(ValueError):
        bio.ErrorModel.from_calibration(df.drop_duplicates(["n", "fwhm_px"]), "body", "smoothed_otsu")


def test_models_roundtrip_through_json_without_changing_predictions():
    m1 = bio.ErrorModel.from_calibration(_table(), "body", "smoothed_otsu")
    m2 = bio.ErrorModel.from_calibration(_table("slot", "otsu"), "slot", "otsu")
    text = bio.models_to_json({"body|smoothed_otsu": m1, "slot|otsu": m2}, meta={"seed": 1})
    back = bio.models_from_json(text)
    assert set(back) == {"body|smoothed_otsu", "slot|otsu"}
    assert back["body|smoothed_otsu"].predict(45.0, 1.5) == pytest.approx(m1.predict(45.0, 1.5))
    assert json.loads(text)["meta"] == {"seed": 1}


# --- certificados -----------------------------------------------------------------------------

def _flat_model(kind, bias_px=0.0, sd_px=0.2, n_nodes=N_NODES, f_nodes=F_NODES):
    rows = [{"kind": kind, "segmenter": "smoothed_otsu", "n": n, "fwhm_px": f, "err_px": e}
            for n, f in itertools.product(n_nodes, f_nodes) for e in (bias_px - sd_px, bias_px, bias_px + sd_px)]
    return bio.ErrorModel.from_calibration(pd.DataFrame(rows), kind, "smoothed_otsu")


def test_body_certificate_is_green_when_the_model_says_the_error_is_tiny():
    model = _flat_model("body", sd_px=0.2)
    c = bio.certify_body(45.0, 0.45, 2.0, model)            # n = 100 px, sd = 0.09 mm
    assert c["in_domain"] and c["light"] == "verde" and c["p_within_tolerance"] >= 0.90


def test_body_certificate_never_green_outside_the_calibrated_box_or_formula_range():
    model = _flat_model("body", sd_px=0.2)
    out = bio.certify_body(45.0, 0.01, 2.0, model)           # n = 4500 px: no calibrado
    assert not out["in_domain"] and out["light"] == "amarillo"
    short = bio.certify_body(10.0, 0.3, 2.0, model)          # n = 33 px: dentro de la caja, CRL < 15 mm
    assert short["in_domain"] and short["light"] != "verde"
    assert bio.certify_body(0.0, 0.3, 2.0, model)["in_domain"] is False


def test_body_certificate_uses_the_bias_in_days_not_only_the_spread():
    model = _flat_model("body", bias_px=8.0, sd_px=0.2)       # 8 px × 0.45 mm = 3.6 mm de sesgo ≈ 2 d
    assert bio.certify_body(45.0, 0.45, 2.0, model)["light"] == "rojo"


def test_slot_certificate_depends_on_the_side_and_the_distance_to_the_threshold():
    model = _flat_model("slot", sd_px=0.5, n_nodes=(10.0, 20.0, 40.0), f_nodes=(1.0, 2.0, 4.0))
    far = bio.certify_slot(4.5, 0.1, 2.0, model)             # n = 45 → fuera de la caja (40 máx.)
    assert not far["in_domain"]
    far = bio.certify_slot(4.0, 0.15, 2.0, model)            # n ≈ 26.7: dentro
    assert far["in_domain"] and far["side"] == "arriba" and far["light"] == "verde"
    at = bio.certify_slot(3.0, 0.15, 2.0, model)
    assert at["light"] == "rojo" and at["p_same_side"] == pytest.approx(0.5, abs=1e-9)
    assert bio.certify_slot(0.0, 0.15, 2.0, model)["in_domain"] is False


def test_slot_certificate_moves_the_posterior_by_the_modelled_bias():
    model = _flat_model("slot", bias_px=-2.0, sd_px=0.5, n_nodes=(10.0, 20.0, 40.0), f_nodes=(1.0, 2.0, 4.0))
    c = bio.certify_slot(2.9, 0.15, 2.0, model)               # sesgo −2 px = −0.3 mm → verdadero ≈ 3.2
    assert c["posterior_mean"] == pytest.approx(3.2)
    assert c["side"] == "debajo" and c["light"] == "rojo"


# --- calibración probabilística --------------------------------------------------------------

def test_expected_calibration_error_is_zero_when_frequencies_match_and_one_when_opposite():
    p = np.array([0.9] * 10 + [0.1] * 10)
    y = np.array([1] * 9 + [0] + [1] + [0] * 9)
    assert bio.expected_calibration_error(p, y) == pytest.approx(0.0, abs=1e-12)
    assert bio.expected_calibration_error(np.ones(5), np.zeros(5)) == pytest.approx(1.0)


def test_expected_calibration_error_rejects_bad_input():
    with pytest.raises(ValueError):
        bio.expected_calibration_error(np.array([0.5, 1.2]), np.array([1, 0]))
    with pytest.raises(ValueError):
        bio.expected_calibration_error(np.array([]), np.array([]))
