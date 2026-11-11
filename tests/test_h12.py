"""H12: certificado recalibrado para ecografía 3D simulada (v0.5).

Datos fabricados de estructura conocida (como en test_h9); una prueba por comportamiento:
* si ``p_volume`` ignorara los modelos que se le pasan, el certificado recalibrado seguiría
  usando los de v0.4 y fallaría con perfiles ``us_*``;
* si ``certify`` no leyera ``volume_models`` del congelado, no habría certificado para ``us_*``;
* si los veredictos contaran estratos no evaluables como «no apoyada», se rompería la regla
  heredada «no calculable = no evaluable».
"""
import math

import numpy as np
import pandas as pd
import pytest

from geovida import certsweep, h9, h12
from geovida.certificate import certify
from geovida.experiment import T_OVER_H
from geovida.imaging import ULTRASOUND_PROFILES, ULTRASOUND_SHIFTED_PROFILES
from geovida.phantoms import NEW_NAMES
from test_h9 import PROFS, SEGS, _frame

US = tuple(ULTRASOUND_PROFILES)
US_SHIFT = tuple(ULTRASOUND_SHIFTED_PROFILES)


# --- Diseños ------------------------------------------------------------------------------------
def test_us_grid_extends_the_old_one_with_finer_levels():
    assert certsweep.T_OVER_H_US[: len(T_OVER_H)] == T_OVER_H
    assert max(certsweep.T_OVER_H_US) > max(T_OVER_H)


def test_us_designs_use_us_profiles_and_the_right_shapes():
    cal = certsweep.design_us_cal(2)
    assert {c.profile for c in cal} == set(US)
    assert len(cal) == 10 * len(certsweep.T_OVER_H_US) * 3 * len(US) * 2
    assert {c.shape for c in certsweep.design_us_unseen(1)} == set(NEW_NAMES)
    assert {c.profile for c in certsweep.design_us_shift(1)} == set(US_SHIFT)


def test_us_seeds_are_new_and_distinct():
    seeds = {certsweep.H12_PILOT_SEED, certsweep.H12_CAL_SEED, certsweep.H12_TEST_SEED,
             certsweep.H12_SHIFT_SEED}
    old = {certsweep.H9_PILOT_SEED, certsweep.H9_CAL_SEED, certsweep.H9_TEST_SEED,
           certsweep.H9_SHIFT_SEED}
    assert len(seeds) == 4 and not seeds & old


# --- p_volume con modelos propios -----------------------------------------------------------------
def test_p_volume_uses_the_models_it_is_given():
    df = h9.add_features(_frame(n=20, profiles=US))
    always = {f"{s}|{p}": {"intercept": 50.0, "slope": 0.0} for s in SEGS for p in US}
    never = {k: {"intercept": -50.0, "slope": 0.0} for k in always}
    assert (h9.p_volume(df, models=always) > 0.99).all()
    assert (h9.p_volume(df, models=never) < 0.01).all()
    with pytest.raises(KeyError):          # sin modelos propios, v0.4 no conoce los perfiles us_*
        h9.p_volume(df)


# --- Congelado -----------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def frozen_us():
    return h12.freeze_us(_frame(seed=2, profiles=US))


def test_freeze_us_has_volume_models_and_envelopes_for_each_us_stratum(frozen_us):
    keys = {f"{s}|{p}" for s in SEGS for p in US}
    assert set(frozen_us["volume_models"]) == keys
    assert set(frozen_us["models"]) == keys
    for m in frozen_us["volume_models"].values():
        assert math.isfinite(m["intercept"]) and math.isfinite(m["slope"]) and m["slope"] > 0
    assert set(frozen_us["envelopes"]) == {"volume", "topology"}
    assert frozen_us["profiles"] == list(US)


def test_certify_uses_volume_models_of_the_frozen_dict_for_us_profiles(frozen_us):
    from geovida.phantoms import make_phantom
    from geovida.imaging import render, spec_for_t_over_h
    r = render(make_phantom("ball", t=1.0), spec_for_t_over_h(16.0, 1.0, "us_compound"),
               np.random.default_rng(1))
    high = {**frozen_us, "volume_models": {k: {"intercept": 50.0, "slope": 0.0}
                                           for k in frozen_us["volume_models"]}}
    low = {**frozen_us, "volume_models": {k: {"intercept": -50.0, "slope": 0.0}
                                          for k in frozen_us["volume_models"]}}
    a = certify(r.image, r.spacing, "smoothed_otsu", "us_compound", high)
    b = certify(r.image, r.spacing, "smoothed_otsu", "us_compound", low)
    assert a["volume"]["p"] > 0.99 and b["volume"]["p"] < 0.01
    assert b["volume"]["light"] == "rojo"


def test_certify_without_us_models_still_refuses_unknown_profiles():
    from geovida.phantoms import make_phantom
    from geovida.imaging import render, spec_for_t_over_h
    r = render(make_phantom("ball", t=1.0), spec_for_t_over_h(16.0, 1.0, "us_compound"),
               np.random.default_rng(1))
    with pytest.raises(KeyError):
        certify(r.image, r.spacing, "smoothed_otsu", "us_compound")   # congelado de v0.4


# --- Confirmación (primaria) ----------------------------------------------------------------------
def test_confirmation_reports_issued_greens_with_guard_and_the_verdicts(frozen_us):
    df = _frame(seed=3, profiles=US)
    out = h12.evaluate_confirmation(df, frozen_us)
    assert len(out["strata"]) == len(SEGS) * len(US)
    row = out["strata"][0]
    for k in ("n_green_volume", "false_green_volume", "n_green_topology", "false_green_topology",
              "coverage_volume", "coverage_topology", "retained_volume", "retained_topology",
              "auc_volume", "ece_volume", "auc_topology", "ece_topology",
              "evaluable_volume", "evaluable_topology"):
        assert k in row
    assert out["h12c"]["verdict"] in ("apoyada", "no apoyada", "no evaluable")
    assert out["h12d"]["verdict"] in ("apoyada", "parcial", "no apoyada", "no evaluable")


def test_confirmation_of_data_like_the_calibration_is_supported(frozen_us):
    out = h12.evaluate_confirmation(_frame(seed=11, profiles=US), frozen_us)
    assert out["h12c"]["evaluable_strata"] > 0
    assert out["h12c"]["verdict"] == "apoyada"


def test_confirmation_with_no_evaluable_stratum_is_not_evaluable_and_never_not_supported(frozen_us):
    df = _frame(seed=3, n=5, profiles=US)             # 20 filas por estrato: ningún estrato evaluable
    out = h12.evaluate_confirmation(df, frozen_us)
    assert out["h12c"]["verdict"] == "no evaluable"
    assert out["h12c"]["evaluable_strata"] == 0


def test_confirmation_flags_a_broken_stratum_as_not_supported(frozen_us):
    # el éxito de topología cae a 0 en los datos nuevos: los verdes que haya son falsos
    df = _frame(seed=4, profiles=US, p_break=1.0)
    df["err_volume"] = 0.3
    out = h12.evaluate_confirmation(df, frozen_us)
    assert out["h12c"]["evaluable_strata"] > 0          # hay verdes de sobra: se puede juzgar
    assert out["h12c"]["verdict"] == "no apoyada"
    assert out["h12c"]["failing"]


# --- Formas nunca vistas y dominio desplazado --------------------------------------------------------
def test_unseen_and_shift_return_per_stratum_rows_and_verdicts(frozen_us):
    un = h12.evaluate_unseen(_frame(seed=5, profiles=US, shapes=("ball", "tube")), frozen_us)
    assert len(un["strata"]) == len(SEGS) * len(US)
    assert un["h12e"]["verdict"] in ("apoyada", "no apoyada", "no evaluable")
    sh = h12.evaluate_shift(_frame(seed=6, profiles=US_SHIFT), frozen_us, declared="us_compound")
    assert len(sh["strata"]) == len(SEGS) * len(US_SHIFT)
    assert sh["declared"] == "us_compound"
    assert sh["h12f"]["verdict"] in ("apoyada", "no apoyada", "no evaluable")
    assert sh["h12g"]["verdict"] in ("apoyada", "no apoyada", "no evaluable")


def test_shift_without_guard_is_judged_on_ungated_greens_and_with_guard_on_gated_ones(frozen_us):
    sh = h12.evaluate_shift(_frame(seed=6, profiles=US_SHIFT, snr=2.0, edge=3.0), frozen_us,
                            declared="us_compound")
    for r in sh["strata"]:
        assert r["in_domain_volume"] == pytest.approx(0.0)       # snr y borde fuera de envolvente
        assert r["n_green_volume_guard"] == 0                    # la guardia no deja pasar ninguno


# --- v0.4 sobre imágenes de ecografía (línea de base) y la guardia entre modalidades ----------------
@pytest.fixture(scope="module")
def frozen_v04_like():
    return h9.freeze(_frame(seed=7, profiles=PROFS))


def test_baseline_applies_the_v04_certificate_declared_realistic(frozen_v04_like):
    out = h12.evaluate_baseline(_frame(seed=8, profiles=US), frozen_v04_like)
    assert out["declared"] == "realistic"
    assert len(out["strata"]) == len(SEGS) * len(US)
    assert out["h12a"]["verdict"] in ("apoyada", "no apoyada", "no evaluable")
    assert set(out["in_domain_by_segmenter"]) == set(SEGS)


def test_modality_guard_rejects_images_from_the_other_noise_model(frozen_us, frozen_v04_like):
    old = _frame(seed=9, profiles=("realistic",), snr=9.2, edge=0.7)
    far = old.assign(edge_width=old["edge_width"] + 5.0)       # borde mucho más grueso que en us_*
    out = h12.evaluate_modality(far, _frame(seed=8, profiles=US), frozen_us, frozen_v04_like)
    assert out["h12b"]["verdict"] in ("apoyada", "parcial", "no apoyada", "no evaluable")
    assert len(out["checks"]) == len(SEGS) + len(SEGS) * len(US)
    ours = [c for c in out["checks"] if c["direction"] == "realistic_vs_us_guard"]
    assert all(c["in_domain"] == pytest.approx(0.0) for c in ours)


# --- ¿Paga recalibrar? -----------------------------------------------------------------------------
def test_benefit_compares_coverage_of_both_certificates_with_guard(frozen_us, frozen_v04_like):
    out = h12.evaluate_benefit(_frame(seed=10, profiles=US), frozen_us, frozen_v04_like)
    assert len(out["strata"]) == len(SEGS) * len(US)
    r = out["strata"][0]
    assert {"coverage_us", "coverage_v04", "n_green_us", "evaluable"} <= set(r)
    assert out["h12h"]["verdict"] in ("apoyada", "no apoyada", "no evaluable")
