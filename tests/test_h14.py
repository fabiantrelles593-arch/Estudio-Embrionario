"""H14: compuerta de «tasa de medidas utilizables» sobre el certificado de H13.

Qué haría fallar cada prueba:
* una tasa por caso mal definida (denominador = verdes en vez de casos) volvería a esconder un estrato
  que casi se cierra: con pocos verdes el cociente parecería bueno o «no evaluable»;
* un umbral desplazado (≤ vs <) cambiaría un veredicto;
* una retención mal calculada ocultaría el costo de cobertura de la compuerta.
"""
import numpy as np
import pandas as pd
import pytest

from geovida import biometry as bio
from geovida import h14


def _rows(kind, n, wrong_green=0, green_ok=0, closed=0, seg="smoothed_otsu", region="in", fwhm=2.0, variant="gated"):
    """n casos: wrong_green verdes equivocados, green_ok verdes acertados, closed sin certificado, el resto amarillos."""
    light = ["verde"] * (wrong_green + green_ok) + ["amarillo"] * (n - wrong_green - green_ok)
    correct = [False] * wrong_green + [True] * (n - wrong_green)
    in_dom = [True] * (n - closed) + [False] * closed
    return pd.DataFrame({"kind": kind, "segmenter": seg, "region": region, "fwhm_px": fwhm, "variant": variant,
                         "light": light, "correct": correct, "in_domain": in_dom, "idx": range(n), "p": 0.95,
                         "bias_mm": 0.0, "sd_mm": 0.1, "truth_mm": 3.0, "measured_mm": 3.0, "h_mm": 0.1,
                         "measurement_share": 0.01, "light_clamped": "amarillo", "p_clamped": 0.5,
                         "ga_err_days": np.nan, "n_nominal": 100.0})


def test_per_case_wrong_green_rate_uses_all_cases_as_denominator():
    d = _rows(bio.SLOT, 400, wrong_green=0, green_ok=3)           # solo 3 verdes: la tasa condicional no sería evaluable
    r = h14.wrong_green_rate_verdict(d, n_boot=300, seed=1)
    assert r["n_cases"] == 400 and r["n_wrong_green"] == 0 and r["rate"] == 0.0
    assert r["verdict"] == "apoyada"


def test_wrong_green_rate_verdict_rules_against_a_two_percent_limit():
    ok = h14.wrong_green_rate_verdict(_rows(bio.SLOT, 400, wrong_green=2), n_boot=500, seed=1)
    assert ok["verdict"] == "apoyada" and ok["ci"][1] <= 0.02
    bad = h14.wrong_green_rate_verdict(_rows(bio.SLOT, 400, wrong_green=40), n_boot=500, seed=1)
    assert bad["verdict"] == "no apoyada" and bad["ci"][0] > 0.02
    edge = h14.wrong_green_rate_verdict(_rows(bio.SLOT, 400, wrong_green=8), n_boot=500, seed=1)   # 2 %
    assert edge["verdict"] == "no concluyente"
    assert h14.wrong_green_rate_verdict(_rows(bio.SLOT, 50), n_boot=300, seed=1)["verdict"] == "no evaluable"


def test_the_stratum_selector_keeps_only_in_box_primary_cases_of_the_wide_psf_stratum():
    df = pd.concat([_rows(bio.SLOT, 200, wrong_green=0, fwhm=5.0),
                    _rows(bio.SLOT, 200, wrong_green=100, fwhm=1.0),          # otro estrato: no cuenta
                    _rows(bio.SLOT, 200, wrong_green=100, fwhm=5.0, region="n_high"),   # fuera de la caja
                    _rows(bio.SLOT, 200, wrong_green=100, fwhm=5.0, seg="otsu")], ignore_index=True)
    sel = h14.wide_psf_slot(df, segmenter="smoothed_otsu")
    assert len(sel) == 200 and (sel["fwhm_px"] > 3.5).all()


def test_retention_is_gated_greens_over_ungated_greens_on_the_same_cases():
    ung = pd.concat([_rows(bio.SLOT, 400, green_ok=300, variant="ungated"),
                     _rows(bio.BODY, 400, green_ok=200, variant="ungated")], ignore_index=True)
    gat = pd.concat([_rows(bio.SLOT, 400, green_ok=255, variant="gated"),
                     _rows(bio.BODY, 400, green_ok=200, variant="gated")], ignore_index=True)
    r = h14.retention(pd.concat([ung, gat], ignore_index=True))
    assert r["slot"]["ungated_green"] == 300 and r["slot"]["gated_green"] == 255
    assert r["slot"]["retained"] == pytest.approx(0.85) and r["slot"]["verdict"] == "apoyada"     # ≥ 0.80
    assert r["body"]["retained"] == pytest.approx(1.0) and r["body"]["verdict"] == "apoyada"      # ≥ 0.95
    low = pd.concat([ung, gat.assign(light=lambda d: np.where(d["kind"] == "slot", "amarillo", d["light"]))])
    assert h14.retention(low)["slot"]["verdict"] == "no apoyada"


def test_evaluate_h14_has_every_hypothesis_key_and_reuses_the_h13_rules():
    ung = pd.concat([_rows(bio.SLOT, 600, green_ok=500, variant="ungated"),
                     _rows(bio.BODY, 600, green_ok=500, variant="ungated")], ignore_index=True)
    gat = pd.concat([_rows(bio.SLOT, 600, green_ok=450, variant="gated"),
                     _rows(bio.BODY, 600, green_ok=500, variant="gated")], ignore_index=True)
    gat_out = pd.concat([_rows(bio.SLOT, 400, region="n_high", variant="gated", closed=400),
                         _rows(bio.BODY, 400, region="n_high", variant="gated", closed=400)], ignore_index=True)
    wide = _rows(bio.SLOT, 300, fwhm=5.0, variant="gated")
    out = h14.evaluate_h14(pd.concat([ung, gat, gat_out, wide], ignore_index=True), n_boot=200, seed=3)
    assert set(out) == {"h14a", "h14b", "h14c", "h14d", "h14e"}
    assert out["h14c"]["slot"]["verdict"] == "apoyada" and out["h14e"]["verdict"] == "apoyada"
