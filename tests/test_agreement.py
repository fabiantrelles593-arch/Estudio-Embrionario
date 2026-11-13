"""Acuerdo entre dos segmentaciones y entre dos lectores (``docs/INTEGRACION_PDF_EXTERNO.md`` §3 y §4).

Solapamiento (Dice, IoU), distancia de contorno (HD95, ASSD) y diferencia relativa de tamaño entre una máscara y una
referencia; y Bland–Altman (sesgo y límites de acuerdo) entre dos lectores que miden lo mismo en varios individuos.
Las convenciones se escriben y se prueban: HD95 y «distancia media» tienen más de una definición en uso.
"""
import math

import numpy as np
import pytest

from geovida import agreement, measure


def _square(shape=(40, 40), top=5, left=5, size=10):
    m = np.zeros(shape, bool)
    m[top:top + size, left:left + size] = True
    return m


# ---------------------------------------------------------------- solapamiento y distancia

def test_identical_masks_agree_perfectly():
    a = _square()
    r = agreement.compare_masks(a, a.copy(), spacing=(1.0, 1.0))
    assert r["dice"] == 1.0 and r["iou"] == 1.0
    assert r["hd95_pooled"] == 0.0 and r["hd95_max"] == 0.0 and r["assd"] == 0.0
    assert r["size_diff_rel"] == 0.0


def test_disjoint_masks_have_zero_overlap():
    r = agreement.compare_masks(_square(left=2), _square(left=25), spacing=(1.0, 1.0))
    assert r["dice"] == 0.0 and r["iou"] == 0.0
    assert r["hd95_pooled"] > 10


def test_half_overlap_has_exact_dice_and_iou():
    a, b = _square(left=5), _square(left=10)            # 100 px cada una, 50 px en común
    r = agreement.compare_masks(a, b, spacing=(1.0, 1.0))
    assert r["dice"] == pytest.approx(2 * 50 / 200)
    assert r["iou"] == pytest.approx(50 / 150)


def test_distances_scale_with_spacing_but_overlap_does_not():
    a, b = _square(left=5), _square(left=9)
    r1 = agreement.compare_masks(a, b, spacing=(1.0, 1.0))
    r2 = agreement.compare_masks(a, b, spacing=(2.0, 2.0))
    assert r2["dice"] == r1["dice"] and r2["iou"] == r1["iou"]
    assert r2["hd95_pooled"] == pytest.approx(2 * r1["hd95_pooled"])
    assert r2["assd"] == pytest.approx(2 * r1["assd"])
    assert r2["size_diff_rel"] == pytest.approx(r1["size_diff_rel"])      # el cociente no depende de la escala


def test_size_difference_is_relative_to_the_reference_and_signed():
    big, small = _square(size=10), _square(size=10)
    small[5:15, 5:10] = False                             # la mitad izquierda queda fuera: 50 px
    r = agreement.compare_masks(big, small, spacing=(1.0, 1.0))      # a = medida, b = referencia
    assert r["size_diff_rel"] == pytest.approx((100 - 50) / 50)
    r_inv = agreement.compare_masks(small, big, spacing=(1.0, 1.0))
    assert r_inv["size_diff_rel"] == pytest.approx((50 - 100) / 100)


def test_size_is_reported_in_physical_units():
    a = _square(size=10)
    r = agreement.compare_masks(a, a, spacing=(0.5, 0.5))
    assert r["size_a"] == pytest.approx(100 * 0.25)       # mm² en 2D


def test_conventions_match_the_ones_already_in_measure():
    # La consistencia con el código previo importa: si alguien compara una cifra con la de `measure`, debe saber
    # cuál convención es. HD95 «agrupada» y la media de las dos medias direccionales son las de `measure`.
    a, b = _square(left=5), _square(left=9, top=6, size=12)
    ref = measure.surface_distance_stats(a, b, (1.0, 1.0))
    r = agreement.compare_masks(a, b, spacing=(1.0, 1.0))
    assert r["hd95_pooled"] == pytest.approx(ref["hd95"])
    assert r["msd_mean_of_means"] == pytest.approx(ref["msd"])


def test_assd_pooled_differs_from_mean_of_means_when_surfaces_have_unequal_size():
    # Con superficies de distinto número de píxeles la media agrupada pesa más a la superficie más grande;
    # la media de las dos medias, no. Es la diferencia de convención que el informe debe poder ver.
    a = _square(size=20)
    b = np.zeros_like(a)
    b[8:12, 8:12] = True                                  # un cuadrado pequeño dentro: superficie mucho menor
    r = agreement.compare_masks(a, b, spacing=(1.0, 1.0))
    assert abs(r["assd"] - r["msd_mean_of_means"]) > 0.1


def test_hd95_max_is_never_below_the_pooled_one_in_a_clear_asymmetric_case():
    a = _square(size=20)
    b = a.copy()
    b[12:14, 25:38] = True                                # un «espolón» fino que solo existe en b
    r = agreement.compare_masks(a, b, spacing=(1.0, 1.0))
    assert r["hd95_max"] >= r["hd95_pooled"] - 1e-9


def test_empty_mask_gives_nan_distances_not_a_fake_zero():
    a, empty = _square(), np.zeros((40, 40), bool)
    r = agreement.compare_masks(a, empty, spacing=(1.0, 1.0))
    assert r["dice"] == 0.0 and r["iou"] == 0.0
    assert math.isnan(r["hd95_pooled"]) and math.isnan(r["assd"])
    both = agreement.compare_masks(empty, empty, spacing=(1.0, 1.0))
    assert both["dice"] == 1.0 and both["iou"] == 1.0     # convención ya usada por measure.dice


def test_shape_mismatch_and_bad_spacing_raise():
    with pytest.raises(ValueError):
        agreement.compare_masks(_square((40, 40)), _square((30, 30)), spacing=(1.0, 1.0))
    with pytest.raises(ValueError):
        agreement.compare_masks(_square(), _square(), spacing=(1.0,))
    with pytest.raises(ValueError):
        agreement.compare_masks(_square(), _square(), spacing=(1.0, -1.0))


def test_works_in_three_dimensions():
    a = np.zeros((20, 20, 20), bool)
    a[4:12, 4:12, 4:12] = True
    b = np.zeros_like(a)
    b[4:12, 4:12, 6:14] = True
    r = agreement.compare_masks(a, b, spacing=(1.0, 1.0, 1.0))
    assert r["dice"] == pytest.approx(2 * (8 * 8 * 6) / (2 * 512))
    assert r["size_a"] == pytest.approx(512)


# ---------------------------------------------------------------- Bland–Altman

X = np.array([10.0, 12.0, 14.0, 16.0])
Y = np.array([9.0, 12.0, 13.0, 17.0])


def test_bland_altman_known_values():
    r = agreement.bland_altman(X, Y)
    d = X - Y                                              # [1, 0, 1, -1]
    assert r["n"] == 4
    assert r["bias"] == pytest.approx(0.25)
    assert r["sd_diff"] == pytest.approx(math.sqrt(2.75 / 3))
    assert r["loa_lower"] == pytest.approx(0.25 - 1.96 * math.sqrt(2.75 / 3))
    assert r["loa_upper"] == pytest.approx(0.25 + 1.96 * math.sqrt(2.75 / 3))
    assert r["bias"] == pytest.approx(d.mean())


def test_bland_altman_sign_is_first_minus_second():
    r = agreement.bland_altman(X + 2.0, X)
    assert r["bias"] == pytest.approx(2.0) and r["sd_diff"] == pytest.approx(0.0)
    r2 = agreement.bland_altman(X, X + 2.0)
    assert r2["bias"] == pytest.approx(-2.0)


def test_bland_altman_perfect_agreement_collapses_to_zero():
    r = agreement.bland_altman(X, X)
    assert r["bias"] == 0.0 and r["sd_diff"] == 0.0
    assert r["loa_lower"] == 0.0 and r["loa_upper"] == 0.0


def test_bland_altman_confidence_intervals_shrink_with_more_individuals():
    small = agreement.bland_altman(X, Y)
    big = agreement.bland_altman(np.tile(X, 8), np.tile(Y, 8))
    w = lambda r: r["bias_ci"][1] - r["bias_ci"][0]
    assert w(big) < w(small)
    lw = lambda r: r["loa_upper_ci"][1] - r["loa_upper_ci"][0]
    assert lw(big) < lw(small)


def test_bland_altman_loa_interval_is_wider_than_bias_interval_and_contains_its_estimate():
    r = agreement.bland_altman(X, Y)
    assert r["loa_upper_ci"][0] < r["loa_upper"] < r["loa_upper_ci"][1]
    assert r["loa_lower_ci"][0] < r["loa_lower"] < r["loa_lower_ci"][1]
    assert (r["loa_upper_ci"][1] - r["loa_upper_ci"][0]) > (r["bias_ci"][1] - r["bias_ci"][0])


def test_bland_altman_relative_difference_uses_the_pair_mean():
    r = agreement.bland_altman(np.array([11.0, 22.0, 33.0]), np.array([9.0, 18.0, 27.0]))
    # d / media del par: 2/10, 4/20, 6/30 = 20 % en las tres
    assert r["rel_bias_pct"] == pytest.approx(20.0)


def test_bland_altman_needs_at_least_two_individuals_and_finite_equal_length_data():
    with pytest.raises(ValueError):
        agreement.bland_altman([1.0], [1.0])
    with pytest.raises(ValueError):
        agreement.bland_altman([1.0, 2.0], [1.0, 2.0, 3.0])
    with pytest.raises(ValueError):
        agreement.bland_altman([1.0, float("nan"), 3.0], [1.0, 2.0, 3.0])
    with pytest.raises(ValueError):
        agreement.bland_altman(X, Y, confidence=1.5)


def test_bland_altman_states_that_repeated_measures_of_one_individual_are_not_individuals():
    # La unidad es el individuo (INTEGRACION_PDF_EXTERNO.md §4): el resultado lo recuerda para quien lea el JSON.
    r = agreement.bland_altman(X, Y)
    assert any("individuo" in n for n in r["notes"])
