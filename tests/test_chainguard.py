"""Guardia de cadena (H16): el certificado condiciona su incertidumbre a lo que la propia imagen delata (solo investigación y educación).

H15 mostró que el semáforo «no se entera» de que la imagen pasó por pantalla, impresión y foto. Aquí se prueba, con datos sintéticos
construidos a propósito, que (1) los índices de imagen no usan la verdad ni la cadena declarada, (2) la tabla de ajuste recupera el
desplazamiento y la varianza extra que se le pusieron, (3) una imagen que no se parece a nada de lo visto al ajustar se rechaza en vez de
recibir un ajuste inventado, y (4) el modelo ajustado se comporta como un ``ErrorModel`` para los certificados existentes.
Ninguna prueba usa una imagen real.
"""
import math

import numpy as np
import pandas as pd
import pytest

from geovida import biometry as bio
from geovida import chainguard as cg


def _speckle(rng, shape=(120, 140)):
    """Imagen sintética de intensidad con grano multiplicativo (como el render sin cadena)."""
    base = np.full(shape, 0.05)
    base[30:90, 40:100] = 0.5
    return base * rng.exponential(1.0, shape)


def _compress(x, a):
    x = x / np.percentile(x, 99.5)
    x = np.clip(x, 0, 1)
    return np.log1p(a * x) / np.log1p(a)


# --------------------------------------------------------------------------- índices de imagen

def test_indices_are_finite_deterministic_and_use_only_the_image():
    img = _speckle(np.random.default_rng(1))
    a, b = cg.image_indices(img), cg.image_indices(img.copy())
    assert set(a) == {"ln_cv", "skew"} and a == b
    assert all(math.isfinite(v) for v in a.values())


def test_compression_lowers_the_local_variation_index():
    img = _speckle(np.random.default_rng(2))
    raw = cg.image_indices(img)["ln_cv"]
    mild, strong = cg.image_indices(_compress(img, 5.0))["ln_cv"], cg.image_indices(_compress(img, 60.0))["ln_cv"]
    assert raw > mild > strong


def test_skew_index_is_positive_for_a_right_tailed_image_and_lower_after_compression():
    img = _speckle(np.random.default_rng(3))
    assert cg.image_indices(img)["skew"] > 1.0
    assert cg.image_indices(_compress(img, 30.0))["skew"] < cg.image_indices(img)["skew"]


def test_indices_of_a_flat_or_tiny_image_are_nan_not_zero():
    flat = cg.image_indices(np.full((60, 60), 0.4))
    assert all(math.isnan(v) for v in flat.values())
    tiny = cg.image_indices(np.random.default_rng(4).random((8, 8)))
    assert all(math.isnan(v) for v in tiny.values())


def test_indices_reject_non_2d_input():
    with pytest.raises(ValueError):
        cg.image_indices(np.zeros((4, 4, 3)))


# --------------------------------------------------------------------------- ajuste de la tabla

def _train_table(rng, n_clean=300, n_chain=600, extra_sd=(0.4, 1.0, 2.0), shift=(0.2, 0.6, 1.2)):
    """Tabla de entrenamiento construida: dos regímenes separados en ln_cv; en el régimen «chain» el residuo depende del tercil."""
    rows = []
    for _ in range(n_clean):
        rows.append({"kind": "body", "regime": "clean", "ln_cv": rng.uniform(1.1, 1.4), "skew": rng.uniform(2.0, 2.6),
                     "resid_px": rng.normal(0.0, 0.5), "sd_clean_px": 0.5})
    third = n_chain // 3
    for k in range(3):
        for _ in range(third):
            u = rng.uniform(-1.9 + 0.5 * k, -1.9 + 0.5 * (k + 1) - 1e-9)
            rows.append({"kind": "body", "regime": "chain", "ln_cv": u, "skew": rng.uniform(0.4, 1.2),
                         "resid_px": rng.normal(shift[k], math.sqrt(0.25 + extra_sd[k] ** 2)), "sd_clean_px": 0.5})
    return pd.DataFrame(rows)


def test_fit_recovers_the_shift_and_the_extra_variance_per_bin():
    cm = cg.fit_chain_model(_train_table(np.random.default_rng(10)), "body")
    chain = next(r for r in cm.regimes if r.name == "chain")
    assert len(chain.mean_px) == 3
    # tolerancia = 4 errores estándar de la media de cada tramo (200 casos, desviación sqrt(0.25 + extra²)): el tercer tramo es el más ruidoso
    se = np.sqrt(0.25 + np.array([0.4, 1.0, 2.0]) ** 2) / math.sqrt(200)
    assert np.all(np.abs(np.array(chain.mean_px) - (0.2, 0.6, 1.2)) < 4 * se)
    assert np.allclose(np.sqrt(chain.extra_var_px2), (0.4, 1.0, 2.0), atol=0.35)
    clean = next(r for r in cm.regimes if r.name == "clean")
    assert len(clean.mean_px) == 1 and abs(clean.mean_px[0]) < 0.2 and clean.extra_var_px2[0] < 0.2


def test_the_extra_variance_is_never_negative_even_when_the_chain_adds_nothing():
    df = _train_table(np.random.default_rng(11), extra_sd=(0.0, 0.0, 0.0), shift=(0.0, 0.0, 0.0))
    df["resid_px"] = np.random.default_rng(12).normal(0.0, 0.3, len(df))      # menos que el sd limpio declarado (0.5)
    cm = cg.fit_chain_model(df, "body")
    assert all(v >= 0.0 for r in cm.regimes for v in r.extra_var_px2)


def test_fit_uses_only_the_rows_of_the_requested_kind():
    df = _train_table(np.random.default_rng(13))
    other = df.copy()
    other["kind"] = "slot"
    other["resid_px"] += 50.0
    cm = cg.fit_chain_model(pd.concat([df, other], ignore_index=True), "body")
    assert all(abs(m) < 5.0 for r in cm.regimes for m in r.mean_px)


def test_fit_refuses_missing_columns_and_thin_bins():
    df = _train_table(np.random.default_rng(14))
    with pytest.raises(ValueError):
        cg.fit_chain_model(df.drop(columns=["resid_px"]), "body")
    with pytest.raises(ValueError):
        cg.fit_chain_model(df.groupby("regime").head(40), "body")                   # 40 por régimen: terciles de ~13 < 30
    with pytest.raises(ValueError):
        cg.fit_chain_model(df, "slot")                                              # no hay filas de ese tipo


# --------------------------------------------------------------------------- soporte (qué se parece a lo visto)

def test_locate_assigns_regime_and_bin_inside_the_support_and_none_outside():
    cm = cg.fit_chain_model(_train_table(np.random.default_rng(20)), "body")
    r, b = cm.locate({"ln_cv": -1.2, "skew": 0.8})
    assert r.name == "chain" and b == 1
    r, b = cm.locate({"ln_cv": 1.25, "skew": 2.3})
    assert r.name == "clean" and b == 0
    assert cm.locate({"ln_cv": 0.0, "skew": 1.0}) is None                           # en el hueco entre los dos regímenes
    assert cm.locate({"ln_cv": -1.2, "skew": 2.3}) is None                          # ln_cv de «chain» pero asimetría de «clean»
    assert cm.locate({"ln_cv": -5.0, "skew": 0.8}) is None
    assert cm.locate({"ln_cv": float("nan"), "skew": 0.8}) is None


def test_when_two_regimes_overlap_the_more_conservative_adjustment_is_used():
    rng = np.random.default_rng(23)
    rows = []
    for name, shift, extra in (("a", 0.1, 0.2), ("b", 1.0, 1.5)):
        for _ in range(100):
            rows.append({"kind": "body", "regime": name, "ln_cv": rng.uniform(-1.0, 0.0), "skew": rng.uniform(0.5, 1.5),
                         "resid_px": rng.normal(shift, math.sqrt(0.25 + extra ** 2)), "sd_clean_px": 0.5})
    cm = cg.fit_chain_model(pd.DataFrame(rows), "body", n_bins=1)
    reg, _ = cm.locate({"ln_cv": -0.5, "skew": 1.0})
    assert reg.name == "b"


def test_adjustment_is_none_outside_the_support_and_a_pair_inside():
    cm = cg.fit_chain_model(_train_table(np.random.default_rng(21)), "body")
    assert cm.adjustment({"ln_cv": 0.0, "skew": 1.0}) is None
    m, ev = cm.adjustment({"ln_cv": -0.7, "skew": 0.8})
    assert m > 0.5 and ev > 0.5


def test_model_round_trips_through_dict():
    cm = cg.fit_chain_model(_train_table(np.random.default_rng(22)), "body")
    cm2 = cg.ChainModel.from_dict(cm.to_dict())
    probe = {"ln_cv": -1.2, "skew": 0.8}
    assert cm2.adjustment(probe) == cm.adjustment(probe) and cm2.locate({"ln_cv": 0.0, "skew": 1.0}) is None


# --------------------------------------------------------------------------- modelo ajustado y certificado

def _base_model(kind=bio.BODY):
    ns, fs = (50.0, 100.0, 300.0), (1.0, 3.0, 5.0)
    return bio.ErrorModel(kind, "smoothed_otsu", ns, fs, np.full((3, 3), 0.3), np.full((3, 3), 0.8), 20)


def test_adjusted_model_adds_the_shift_and_adds_variances_not_sds():
    base = _base_model()
    adj = cg.AdjustedModel(base, mean_px=0.5, extra_var_px2=0.36)
    b0, s0 = base.predict(100.0, 3.0)
    b1, s1 = adj.predict(100.0, 3.0)
    assert b1 == pytest.approx(b0 + 0.5) and s1 == pytest.approx(math.sqrt(s0 ** 2 + 0.36))


def test_adjusted_model_keeps_the_box_and_the_gate_of_the_base_model():
    base = _base_model()
    assert cg.AdjustedModel(base, 0.1, 0.1).predict(5000.0, 3.0) is None
    assert cg.AdjustedModel(base, 0.1, 0.1).predict(100.0, 100.0) is None
    gated = bio.ErrorModel(bio.BODY, "smoothed_otsu", (50.0, 100.0, 300.0), (1.0, 3.0, 5.0), np.full((3, 3), 0.3),
                           np.full((3, 3), 0.8), 20, usable_rate=np.full((3, 3), 0.5), min_usable_rate=0.9)
    adj = cg.AdjustedModel(gated, 0.0, 0.0)
    assert adj.min_usable_rate == 0.9 and adj.usable_rate_at(100.0, 3.0) == pytest.approx(0.5)


def test_extra_variance_must_be_nonnegative():
    with pytest.raises(ValueError):
        cg.AdjustedModel(_base_model(), 0.0, -0.1)


def test_certify_refuses_green_for_an_image_that_resembles_nothing_seen():
    cm = cg.fit_chain_model(_train_table(np.random.default_rng(30)), "body")
    cert = cg.certify(bio.BODY, 30.0, 0.3, 3.0, _base_model(), cm, {"ln_cv": 0.0, "skew": 1.0})
    assert cert["light"] == "amarillo" and cert["in_domain"] is False and "cadena" in cert["reason"]


def test_certify_inside_the_support_matches_the_manual_adjusted_certificate():
    cm = cg.fit_chain_model(_train_table(np.random.default_rng(31)), "body")
    base, idx = _base_model(), {"ln_cv": -0.7, "skew": 0.8}
    cert = cg.certify(bio.BODY, 30.0, 0.3, 3.0, base, cm, idx)
    m, ev = cm.adjustment(idx)
    manual = bio.certify_body(30.0, 0.3, 3.0, cg.AdjustedModel(base, m, ev))
    assert cert["in_domain"] and cert["p_within_tolerance"] == pytest.approx(manual["p_within_tolerance"])
    assert cert["chain_regime"] == "chain" and cert["chain_bin"] == 2
    assert cert["sd_px"] > bio.certify_body(30.0, 0.3, 3.0, base)["sd_px"]


def test_certify_works_for_the_decision_certificate_too():
    df = _train_table(np.random.default_rng(32))
    df["kind"] = "slot"
    cm = cg.fit_chain_model(df, "slot")
    cert = cg.certify(bio.SLOT, 3.2, 0.03, 1.5, _base_model(bio.SLOT), cm, {"ln_cv": -1.2, "skew": 0.8})      # n = 107 px, dentro de la caja
    assert cert["in_domain"] and "p_same_side" in cert


def test_certify_rejects_unknown_kinds():
    cm = cg.fit_chain_model(_train_table(np.random.default_rng(33)), "body")
    with pytest.raises(ValueError):
        cg.certify("otra_cosa", 30.0, 0.3, 3.0, _base_model(), cm, {"ln_cv": -1.2, "skew": 0.8})


# --------------------------------------------------------------------------- recalibración condicionada a la imagen (diseño 2)
#
# El piloto de H16 mostró que sumar varianza (diseño 1) casi nunca deja pasar un verde de CRL: el error que añade la cadena no es
# gaussiano (la mayoría de los casos sale bien y unos pocos fallan mucho) y una varianza media lo describe mal. El diseño 2 no supone
# una forma: reajusta la probabilidad del certificado con la frecuencia de aciertos observada en el entrenamiento, dada la probabilidad
# base y los índices de la imagen.

def _sig(x):
    return 1.0 / (1.0 + np.exp(-x))


def _logit(p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def _recal_table(rng, n=3000, a=-1.2, b=0.6, c=0.8, regime="chain", kind="body"):
    p = rng.uniform(0.3, 0.999, n)
    u = rng.uniform(-1.8, -0.5, n)
    sk = rng.uniform(0.4, 1.2, n)
    y = rng.random(n) < _sig(a + b * _logit(p) + c * (u + 1.15))
    return pd.DataFrame({"kind": kind, "regime": regime, "ln_cv": u, "skew": sk, "p_base": p, "correct": y})


def test_recalibration_recovers_the_true_probability_of_a_correct_measurement():
    df = _recal_table(np.random.default_rng(40))
    rm = cg.fit_recal_model(df, "body")
    grid = [(p, u) for p in (0.5, 0.8, 0.95, 0.995) for u in (-1.6, -1.1, -0.7)]
    err = [abs(rm.predict(p, {"ln_cv": u, "skew": 0.8}) - _sig(-1.2 + 0.6 * _logit(p) + 0.8 * (u + 1.15))) for p, u in grid]
    assert max(err) < 0.06 and np.mean(err) < 0.03


def test_recalibration_does_not_distort_a_probability_that_was_already_calibrated():
    rng = np.random.default_rng(41)
    p = rng.uniform(0.3, 0.999, 4000)
    df = pd.DataFrame({"kind": "body", "regime": "clean", "ln_cv": rng.uniform(0.0, 1.0, 4000), "skew": rng.uniform(2.0, 2.6, 4000),
                       "p_base": p, "correct": rng.random(4000) < p})
    rm = cg.fit_recal_model(df, "body")
    for q in (0.4, 0.7, 0.9, 0.99):
        assert abs(rm.predict(q, {"ln_cv": 0.5, "skew": 2.3}) - q) < 0.06


def test_recalibration_is_monotone_in_the_base_probability_when_the_data_say_so():
    rm = cg.fit_recal_model(_recal_table(np.random.default_rng(42)), "body")
    ps = [rm.predict(p, {"ln_cv": -1.1, "skew": 0.8}) for p in (0.4, 0.6, 0.8, 0.9, 0.99)]
    assert all(b >= a for a, b in zip(ps, ps[1:]))


def test_recalibration_stays_finite_and_inside_zero_one_when_everything_was_correct():
    df = _recal_table(np.random.default_rng(43))
    df["correct"] = True
    rm = cg.fit_recal_model(df, "body")
    p = rm.predict(0.95, {"ln_cv": -1.1, "skew": 0.8})
    assert 0.9 < p < 1.0 and math.isfinite(p)


def test_recalibration_support_is_the_box_of_each_regime_and_nothing_else():
    df = pd.concat([_recal_table(np.random.default_rng(44)), _recal_table(np.random.default_rng(45), regime="clean").assign(
        ln_cv=lambda d: d["ln_cv"] + 2.5, skew=lambda d: d["skew"] + 1.8)], ignore_index=True)
    rm = cg.fit_recal_model(df, "body")
    assert rm.predict(0.9, {"ln_cv": -1.1, "skew": 0.8}) is not None
    assert rm.predict(0.9, {"ln_cv": 1.0, "skew": 2.4}) is not None
    assert rm.predict(0.9, {"ln_cv": -0.1, "skew": 1.5}) is None             # el hueco entre los regímenes
    assert rm.predict(0.9, {"ln_cv": float("nan"), "skew": 0.8}) is None
    assert rm.predict(float("nan"), {"ln_cv": -1.1, "skew": 0.8}) is None


def test_recalibration_fit_refuses_missing_columns_few_rows_and_missing_kind():
    df = _recal_table(np.random.default_rng(46))
    with pytest.raises(ValueError):
        cg.fit_recal_model(df.drop(columns=["p_base"]), "body")
    with pytest.raises(ValueError):
        cg.fit_recal_model(df.head(50), "body")
    with pytest.raises(ValueError):
        cg.fit_recal_model(df, "slot")


def test_recalibration_round_trips_through_dict():
    rm = cg.fit_recal_model(_recal_table(np.random.default_rng(47)), "body")
    rm2 = cg.RecalModel.from_dict(rm.to_dict())
    probe = {"ln_cv": -1.0, "skew": 0.7}
    assert rm2.predict(0.93, probe) == pytest.approx(rm.predict(0.93, probe))


def test_certify_recal_takes_the_light_from_the_recalibrated_probability():
    rm = cg.fit_recal_model(_recal_table(np.random.default_rng(48), b=1.2, a=-0.5, c=0.0), "body")
    base = _base_model()
    idx = {"ln_cv": -1.1, "skew": 0.8}
    cert = cg.certify_recal(bio.BODY, 30.0, 0.3, 3.0, base, rm, idx)
    raw = bio.certify_body(30.0, 0.3, 3.0, base)
    assert cert["in_domain"] and cert["p_base"] == pytest.approx(raw["p_within_tolerance"])
    assert cert["p_within_tolerance"] == pytest.approx(rm.predict(raw["p_within_tolerance"], idx))
    p = cert["p_within_tolerance"]
    assert cert["light"] == ("verde" if p >= 0.90 else "rojo" if p < 0.50 else "amarillo")


def test_certify_recal_refuses_what_the_base_model_refuses_and_what_resembles_nothing_seen():
    rm = cg.fit_recal_model(_recal_table(np.random.default_rng(49)), "body")
    far = cg.certify_recal(bio.BODY, 5000.0, 0.3, 3.0, _base_model(), rm, {"ln_cv": -1.1, "skew": 0.8})      # n fuera de la caja
    assert far["light"] == "amarillo" and far["in_domain"] is False and "caja" in far["reason"]
    nowhere = cg.certify_recal(bio.BODY, 30.0, 0.3, 3.0, _base_model(), rm, {"ln_cv": 3.0, "skew": 5.0})
    assert nowhere["light"] == "amarillo" and nowhere["in_domain"] is False and "cadena" in nowhere["reason"]


def test_certify_recal_never_gives_green_to_a_crl_outside_the_formula_range():
    rm = cg.fit_recal_model(_recal_table(np.random.default_rng(50), b=2.0, a=3.0, c=0.0), "body")
    cert = cg.certify_recal(bio.BODY, 12.0, 0.05, 3.0, _base_model(), rm, {"ln_cv": -1.1, "skew": 0.8})      # 12 mm < 15 mm
    assert cert["light"] != "verde"


def test_certify_recal_works_for_the_decision_certificate_and_rejects_unknown_kinds():
    rm = cg.fit_recal_model(_recal_table(np.random.default_rng(51), kind="slot"), "slot")
    cert = cg.certify_recal(bio.SLOT, 3.2, 0.03, 1.5, _base_model(bio.SLOT), rm, {"ln_cv": -1.1, "skew": 0.8})
    assert cert["in_domain"] and "p_same_side" in cert and "p_base" in cert
    with pytest.raises(ValueError):
        cg.certify_recal("otra_cosa", 3.2, 0.03, 1.5, _base_model(bio.SLOT), rm, {"ln_cv": -1.1, "skew": 0.8})


def test_overlapping_recal_regimes_give_the_lower_probability():
    rng = np.random.default_rng(60)
    hi = _recal_table(rng, regime="a", a=2.5, b=0.0, c=0.0)                  # acierta casi siempre
    lo = _recal_table(rng, regime="b", a=-1.0, b=0.0, c=0.0)                 # acierta poco
    rm = cg.fit_recal_model(pd.concat([hi, lo], ignore_index=True), "body")
    idx = {"ln_cv": -1.1, "skew": 0.8}
    p_hi = next(r for r in rm.regimes if r.name == "a").prob(0.9, idx)
    p_lo = next(r for r in rm.regimes if r.name == "b").prob(0.9, idx)
    assert p_hi > 0.85 and p_lo < 0.4
    assert rm.predict(0.9, idx) == pytest.approx(p_lo)


def test_an_intermediate_recalibrated_probability_is_yellow_not_green():
    rm = cg.fit_recal_model(_recal_table(np.random.default_rng(61), a=0.85, b=0.0, c=0.0), "body")      # acierta ~70 %
    cert = cg.certify_recal(bio.BODY, 30.0, 0.3, 3.0, _base_model(), rm, {"ln_cv": -1.1, "skew": 0.8})
    assert 0.5 <= cert["p_within_tolerance"] < 0.9 and cert["light"] == "amarillo"


def test_the_intercept_is_not_shrunk_so_a_small_sample_keeps_its_observed_rate():
    rng = np.random.default_rng(62)
    n = 150
    y = np.zeros(n, dtype=bool)
    y[:143] = True
    rng.shuffle(y)
    df = pd.DataFrame({"kind": "body", "regime": "chain", "ln_cv": rng.uniform(-1.8, -0.5, n), "skew": rng.uniform(0.4, 1.2, n),
                       "p_base": rng.uniform(0.5, 0.99, n), "correct": y})
    rm = cg.fit_recal_model(df, "body")
    assert abs(rm.predict(0.8, {"ln_cv": -1.15, "skew": 0.8}) - 143 / 150) < 0.012
