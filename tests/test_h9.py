"""H9/H10: calibración, congelado y veredictos del certificado vectorial (v0.4).

Datos sintéticos de estructura conocida: el éxito topológico depende del margen
(``tau_ero``) y no de la profundidad global (``d_over_hgeo``).
"""
import json
import math

import numpy as np
import pandas as pd
import pytest

from geovida import h9
from geovida.domain import SNR_CAP

SEGS = ("global", "otsu", "smoothed_otsu")
PROFS = ("ideal", "realistic")
SHAPES = ("ball", "torus", "shell", "tube")


def _frame(seed=0, n=400, snr=None, edge=0.7, margin_drives=True, profiles=PROFS, shapes=SHAPES,
           p_break=0.0):
    rng = np.random.default_rng(seed)
    rows = []
    for seg in SEGS:
        for prof in profiles:
            for shape in shapes:
                tau = rng.choice([0.0, 0.6, 1.0, 1.5, 2.0], n)
                d = np.exp(rng.uniform(-1.0, 2.0, n))
                driver = tau if margin_drives else np.log(d) + 1.0
                p = 1 / (1 + np.exp(-6 * (driver - 0.8)))
                ok = rng.random(n) < p * (1 - p_break)
                real = prof if prof in PROFS else "realistic"
                s = SNR_CAP if real == "ideal" else rng.normal(9.2 if snr is None else snr, 0.25, n)
                rows.append(pd.DataFrame({
                    "segmenter": seg, "profile": prof, "shape": shape, "rep": np.arange(n),
                    "t_over_h": rng.choice([2.0, 4.0, 8.0], n), "anisotropy": 1.0,
                    "d_mean": d, "volume": 1.0, "area_sdf": 1.0,       # con t = 1 y h = 1/t_over_h
                    "err_volume": np.where(d * 1.0 > 1.5, 0.01, 0.3),
                    "topology_ok": ok, "tau_dil": 2.0, "tau_ero": tau,
                    "m_lo": rng.choice([0.2, 0.4], n), "m_hi": 0.4,
                    "a1": (tau >= 1.0).astype(float), "a2": rng.integers(0, 2, n).astype(float),
                    "u_v1": 0.01, "snr_hat": s, "edge_width": rng.normal(edge, 0.05, n)}))
    return pd.concat(rows, ignore_index=True)


@pytest.fixture(scope="module")
def frozen():
    return h9.freeze(_frame(seed=1))


def test_feature_sets_are_the_preregistered_ones():
    assert h9.TOPO_SETS["T1"] == ("ln_d",)
    assert h9.TOPO_SETS["T4"] == ("tau_dil", "tau_ero", "m_lo", "m_hi", "a1", "a2")
    assert h9.TOPO_SETS["T7"] == ("ln_d",) + h9.TOPO_SETS["T4"]
    assert h9.without_scale(h9.TOPO_SETS["T7"]) == ("ln_d", "tau_dil", "tau_ero", "m_lo", "m_hi")


def test_add_features_builds_the_response_and_the_log_depth():
    df = h9.add_features(_frame(n=5))
    assert {"t_ok", "ln_d", "v_ok", "d_over_hgeo"} <= set(df.columns)
    assert df["t_ok"].isin([0.0, 1.0]).all()


def test_unmeasurable_rows_get_probability_zero():
    df = h9.add_features(_frame(n=50))
    model = h9.fit_set(df, h9.TOPO_SETS["T4"])
    df.loc[df.index[0], "tau_ero"] = np.nan
    p = h9.predict_set(model, df)
    assert p[0] == 0.0 and (p[1:] > 0).all()


def test_loso_selects_the_margin_set_when_the_margin_drives_success():
    best, tab = h9.select_set(h9.add_features(_frame(seed=2, n=250)))
    assert best in ("T4", "T7") and set(tab["set"]) == {"T1", "T4", "T7"}
    ll = tab.set_index("set")["mean_logloss"]
    assert ll["T1"] > ll[best]


def test_loso_selects_the_global_depth_when_only_depth_matters():
    best, _ = h9.select_set(h9.add_features(_frame(seed=3, n=250, margin_drives=False)))
    assert best in ("T1", "T7")


def test_freeze_payload_is_complete_and_serialisable(frozen):
    assert json.loads(json.dumps(frozen)) == frozen
    assert frozen["selected"] in ("T4", "T7")
    key = "otsu|realistic"
    assert set(frozen["models"][key]) == {"main", "baseline", "no_scale"}
    assert frozen["models"][key]["baseline"]["features"] == ["ln_d"]
    assert "a1" not in frozen["models"][key]["no_scale"]["features"]
    for endpoint in ("volume", "topology"):
        assert set(frozen["envelopes"][endpoint]) == {f"{s}|{p}" for s in SEGS for p in PROFS}
    lo, hi = frozen["envelopes"]["topology"][key]["snr_hat"]
    assert 8.3 < lo < 9.0 < 9.5 < hi < 10.1


def test_envelope_is_none_when_a_stratum_has_too_few_green_rows():
    df = _frame(seed=4, n=30)
    df.loc[df["segmenter"] == "otsu", "tau_ero"] = 0.0      # nunca verde en topología
    fz = h9.freeze(df)
    assert fz["envelopes"]["topology"]["otsu|ideal"] is None


def test_in_domain_evaluation_supports_a_good_model(frozen):
    res = h9.evaluate_in_domain(_frame(seed=5), frozen)
    assert res["h9b"]["verdict"] == "apoyada" and res["h9c"]["verdict"] == "apoyada"
    assert res["h9d"]["verdict"] == "apoyada" and res["h9e"]["verdict"] == "apoyada"
    assert res["h10c"]["verdict"] == "apoyada"
    row = res["strata"][0]
    assert {"auc", "ece", "false_green", "coverage", "retained_topology", "retained_volume",
            "logloss", "logloss_baseline", "logloss_no_scale"} <= set(row)
    assert 0.9 <= row["retained_topology"] <= 1.0


def test_h9d_fails_when_green_lights_are_often_wrong(frozen):
    res = h9.evaluate_in_domain(_frame(seed=6, p_break=0.3), frozen)   # 30 % de fallos imprevisibles
    assert res["h9d"]["verdict"] == "no apoyada"


def test_shift_evaluation_rejects_out_of_domain_images(frozen):
    shifted = _frame(seed=7, snr=4.5, profiles=("noisy",), p_break=0.5)
    res = h9.evaluate_shift(shifted, frozen)
    rows = {r["stratum"]: r for r in res["strata"]}
    r = rows["otsu|noisy"]
    assert r["n_green_topology"] > 100 and r["false_green_topology"] > 0.10
    assert r["n_green_topology_guard"] == 0 and r["in_domain_topology"] == 0.0
    assert res["h10b"]["rejected"] == 3 and res["h10b"]["verdict"] in ("apoyada", "no evaluable")


def test_h10a_counts_strata_where_the_unguarded_volume_light_fails(frozen):
    shifted = _frame(seed=8, snr=4.5, profiles=("noisy",))
    shifted["err_volume"] = 0.3                                        # todo el volumen está mal
    res = h9.evaluate_shift(shifted, frozen)
    assert res["h10a"]["count"] == 3 and res["h10a"]["verdict"] == "apoyada"
    assert all(r["n_green_volume_guard"] == 0 for r in res["strata"])


def test_h10b_fails_if_a_shift_slips_through_the_guard_with_false_greens(frozen):
    slipped = _frame(seed=9, profiles=("mild_blur",), p_break=0.5)     # índices dentro de la envolvente
    slipped["err_volume"] = 0.3
    res = h9.evaluate_shift(slipped, frozen)
    assert res["h10b"]["failing"] == 3 and res["h10b"]["verdict"] == "no apoyada"


def test_unseen_evaluation_uses_the_small_sample_threshold(frozen):
    res = h9.evaluate_unseen(_frame(seed=10, n=200, shapes=("dumbbell", "cup")), frozen)
    assert res["h9f"]["evaluable"] == 6 and res["h9f"]["verdict"] == "apoyada"


def test_silent_failures_table_reports_lights_of_the_failed_measurements(frozen):
    tab = h9.silent_failures(_frame(seed=11), frozen)
    assert {"t_over_h", "n_failures", "green", "yellow", "red"} <= set(tab.columns)
    assert np.allclose(tab[["green", "yellow", "red"]].sum(axis=1), 1.0)


def test_metrics_handle_a_stratum_without_green_lights():
    m = h9.light_metrics(np.array([0.1, 0.2, 0.3]), np.array([0.0, 1.0, 0.0]))
    assert m["n_green"] == 0 and math.isnan(m["false_green"]) and m["coverage"] == 0.0
