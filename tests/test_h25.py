"""Pruebas sintéticas de H25 (docs/h25/PREREGISTRO_H25.md, §5)."""
import math

import numpy as np
import pandas as pd

from geovida import h24, h25
from geovida.domain import domain_observables
from geovida.measure import _area_sdf


def _sphere(n=40, r=9, bright=100.0, bg=20.0, noise=5.0, seed=0):
    z, y, x = np.mgrid[:n, :n, :n]
    mask = (z - n / 2) ** 2 + (y - n / 2) ** 2 + (x - n / 2) ** 2 <= r * r
    rng = np.random.default_rng(seed)
    img = np.where(mask, bright, bg) + rng.normal(0, noise, mask.shape)
    return img, mask


def _obs(fn, img, mask):
    sp = (1.0, 1.0, 1.0)
    return fn(img, mask, sp, float(_area_sdf(mask, sp)))


def test_igual_que_la_antigua_con_contraste_positivo():
    img, mask = _sphere()
    old, new = _obs(domain_observables, img, mask), _obs(h25.domain_observables_abs, img, mask)
    assert new["contrast"] > 0
    assert new["snr_hat"] == old["snr_hat"] and new["edge_width"] == old["edge_width"]


def test_estructura_oscura_antigua_nan_nueva_calculable():
    img, mask = _sphere(bright=10.0, bg=80.0)
    old, new = _obs(domain_observables, img, mask), _obs(h25.domain_observables_abs, img, mask)
    assert math.isnan(old["snr_hat"]) and math.isnan(old["edge_width"])
    assert new["contrast"] < 0 and math.isfinite(new["snr_hat"]) and math.isfinite(new["edge_width"])


def test_invertir_la_imagen_no_cambia_la_guardia():
    img, mask = _sphere()
    a, b = _obs(h25.domain_observables_abs, img, mask), _obs(h25.domain_observables_abs, -img, mask)
    assert math.isclose(a["snr_hat"], b["snr_hat"], rel_tol=1e-9)
    assert math.isclose(a["edge_width"], b["edge_width"], rel_tol=1e-9)


def test_contraste_cero_no_calculable():
    mask = _sphere()[1]
    img = np.full(mask.shape, 50.0)
    new = _obs(h25.domain_observables_abs, img, mask)
    assert math.isnan(new["snr_hat"]) and math.isnan(new["edge_width"])


def test_observables_trae_ambas_guardias():
    img, mask = _sphere(bright=10.0, bg=80.0)
    o = h25.observables(img, (1.0, 1.0, 1.0), mask)
    assert set(o) == {"snr_hat", "edge_width", "contrast", "snr_hat_h24", "edge_width_h24"}
    assert math.isfinite(o["snr_hat"]) and math.isnan(o["snr_hat_h24"])


def test_umbrales_y_redes_son_los_de_h24():
    assert h25.THRESHOLDS == h24.THRESHOLDS and h25.NETS_SHA256 == h24.NETS_SHA256


def _row(contrast, same=True):
    return {"b_flip": 0.1, "b_stage": 0.2, "area_m": 10.0, "identity_matches": True, "seconds": 5.0,
            "contrast": contrast, "snr_hat": 1.0, "edge_width": 0.3,
            "snr_hat_h24": 1.0 if same else math.nan, "edge_width_h24": 0.3 if same else math.nan}


def test_g0_exige_coincidencia_con_contraste_positivo():
    assert h25.g0([_row(-3.0, same=False), _row(4.0)])["passed"]
    assert not h25.g0([_row(4.0, same=False)])["passed"]
    assert not h25.g0([_row(-3.0, same=False)])["passed"]      # ningún caso con C > 0: no se comprobó
    assert h25.g0([_row(-3.0, same=False)], extra=[_row(2.0)])["passed"]
    assert not h25.g0([_row(-3.0, same=False)], extra=[_row(2.0, same=False)])["passed"]


def test_evaluate_test_renombra_y_anade_h25h():
    rng = np.random.default_rng(1)
    n = 30
    df = pd.DataFrame({"embryo_id": [f"e{i}" for i in range(n)], "b_flip": rng.uniform(0, 0.4, n),
                       "b_stage": rng.uniform(0, 0.6, n), "e_b": rng.uniform(0, 0.8, n),
                       "rel_error_volume": rng.normal(0, 0.1, n), "dice": rng.uniform(0.8, 0.95, n),
                       "snr_hat": rng.uniform(0.1, 1, n), "edge_width": rng.uniform(0.1, 0.5, n),
                       "snr_hat_h24": np.nan, "edge_width_h24": np.nan})
    env = {"snr_hat": [0.0, 2.0], "edge_width": [0.0, 1.0]}
    out = h25.evaluate_test(h24.lights(df, env), env, n_boot=50)
    assert {"h25a", "h25b", "h25c", "h25d", "h25e", "h25g", "h25h"} <= set(out)
    assert out["h25h"]["green_old_guard"] == 0 and out["h25h"]["in_domain_old_guard"] == 0.0
