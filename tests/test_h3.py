import numpy as np
import pandas as pd
import pytest

from geovida.h3 import evaluate_h3, evaluate_h4, grade

SEGS = ("global", "otsu", "smoothed_otsu")
PROFS = ("ideal", "realistic")


def test_grade_thresholds():
    assert grade(6, 6, supported_min=6, partial_min=4) == "apoyada"
    assert grade(5, 6, supported_min=6, partial_min=4) == "parcial"
    assert grade(3, 6, supported_min=6, partial_min=4) == "no apoyada"
    assert grade(0, 0, supported_min=6, partial_min=4) == "no evaluable"


def _frozen(q_models_same=True):
    models = {}
    for s in SEGS:
        for p in PROFS:
            models[f"{s}|{p}"] = {
                "q_model": {"intercept": -3.0, "slope": 4.0},
                "t_model": {"intercept": -3.0, "slope": 1.0},
                "q_star_095": float(np.exp((np.log(0.95 / 0.05) + 3.0) / 4.0)),
            }
    return {"models": models}


def _h3_frame(seed=0, n=1500, q_truth=True):
    rng = np.random.default_rng(seed)
    rows = []
    for s in SEGS:
        for p in PROFS:
            q = np.exp(rng.uniform(np.log(0.3), np.log(6.0), n))
            prob = 1 / (1 + np.exp(-(-3.0 + 4.0 * np.log(q)))) if q_truth else np.full(n, 0.5)
            ok = rng.random(n) < prob
            # el grosor no lleva informacion util en estos datos sinteticos
            t = np.exp(rng.uniform(np.log(1.5), np.log(12.0), n))
            rows.append(pd.DataFrame({
                "segmenter": s, "profile": p, "q_over_hgeo": q, "t_solid_over_hgeo": t,
                "err_volume": np.where(ok, 0.01, 0.2)}))
    return pd.concat(rows, ignore_index=True)


def test_h3_is_supported_when_the_frozen_q_model_is_true_and_t_is_uninformative():
    res = evaluate_h3(_h3_frame(), _frozen())
    assert res["h3a"]["verdict"] == "apoyada"
    assert res["h3b"]["verdict"] == "apoyada"
    assert res["h3c"]["verdict"] == "apoyada"
    assert len(res["strata"]) == 6


def test_h3_fails_when_q_carries_no_information():
    res = evaluate_h3(_h3_frame(q_truth=False), _frozen())
    assert res["h3a"]["verdict"] != "apoyada"
    assert res["h3b"]["verdict"] == "no apoyada"


def test_h3c_counts_nan_refit_as_not_evaluable_not_as_failure():
    df = _h3_frame()
    df.loc[(df.segmenter == "global") & (df.profile == "ideal"), "err_volume"] = 0.01  # sin variacion
    res = evaluate_h3(df, _frozen())
    row = next(r for r in res["strata"] if r["stratum"] == "global|ideal")
    assert row["h3c_evaluable"] is False


def _h4_frame(sdf_bias):
    rows = []
    for shape in ("capsule", "cylinder", "oblate"):
        for lvl in (3.0, 4.0, 6.0, 8.0, 12.0):
            for rep in range(5):
                rows.append({"shape": shape, "t_over_h": lvl, "anisotropy": 1.0,
                             "profile": "ideal", "segmenter": "global",
                             "err_area_sdf": sdf_bias, "err_area_mc": -0.3,
                             "err_area_faces": 0.5})
    return pd.DataFrame(rows)


def test_h4_supported_for_a_small_bias_and_fails_for_a_large_one():
    good = evaluate_h4(_h4_frame(0.03))
    assert good["h4a"]["verdict"] == "apoyada" and good["h4b"]["verdict"] == "apoyada"
    assert good["h4c"]["verdict"] == "apoyada"
    bad = evaluate_h4(_h4_frame(0.40))
    assert bad["h4a"]["verdict"] == "no apoyada" and bad["h4c"]["verdict"] == "no apoyada"
