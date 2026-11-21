"""Guardia de dominio (v0.4): ¿se parece esta imagen a las que vio la calibración?

Dos índices medidos en la propia imagen, sin verdad: ``snr_hat`` (contraste /
ruido del fondo) y ``edge_width`` (grosor de la banda de transición del borde,
en vóxeles finos). Si alguno cae fuera de la envolvente de la calibración, el
certificado no da luz verde.
"""
import math

import numpy as np
import pandas as pd
import pytest

from geovida.domain import (
    DOMAIN_COLUMNS, SNR_CAP, domain_observables, fit_envelopes, in_domain,
)
from geovida.imaging import ImagingSpec, render
from geovida.measure import measure_mask
from geovida.phantoms import make_phantom
from geovida.segment import segment


def _obs(psf=0.0, snr=None, t_over_h=8.0, shape="ball", seed=0):
    ph = make_phantom(shape, t=1.0)
    out = render(ph, ImagingSpec(h_xy=1.0 / t_over_h, psf_fwhm=psf, snr=snr),
                 np.random.default_rng(seed))
    mask = segment("global", out.image, out.spacing)
    meas = measure_mask(mask, out.spacing)
    return domain_observables(out.image, mask, out.spacing, meas["area_sdf"])


def test_noise_free_image_has_capped_snr():
    assert _obs()["snr_hat"] == SNR_CAP


@pytest.mark.parametrize("snr", [5.0, 10.0, 20.0])
def test_snr_estimate_tracks_the_true_snr(snr):
    est = _obs(psf=1.0, snr=snr, t_over_h=12.0)["snr_hat"]
    assert est == pytest.approx(snr, rel=0.25)


def test_edge_width_grows_with_blur():
    sharp = _obs(psf=0.0, t_over_h=12.0)["edge_width"]
    mid = _obs(psf=1.0, t_over_h=12.0)["edge_width"]
    wide = _obs(psf=2.0, t_over_h=12.0)["edge_width"]
    assert sharp < mid < wide and wide > 1.5 * mid


def test_observables_do_not_depend_on_the_units():
    ph = make_phantom("ball", t=1.0)
    out = render(ph, ImagingSpec(h_xy=0.125, psf_fwhm=1.0, snr=10.0), np.random.default_rng(1))
    mask = segment("global", out.image, out.spacing)
    a = domain_observables(out.image, mask, out.spacing, measure_mask(mask, out.spacing)["area_sdf"])
    sp2 = tuple(8.0 * s for s in out.spacing)
    b = domain_observables(out.image, mask, sp2, measure_mask(mask, sp2)["area_sdf"])
    assert a["snr_hat"] == pytest.approx(b["snr_hat"]) and a["edge_width"] == pytest.approx(b["edge_width"])


def test_empty_or_full_masks_give_nan():
    img = np.zeros((8, 8, 8), np.float32)
    for mask in (np.zeros((8, 8, 8), bool), np.ones((8, 8, 8), bool)):
        o = domain_observables(img, mask, (1.0, 1.0, 1.0), 0.0)
        assert math.isnan(o["snr_hat"]) and math.isnan(o["edge_width"])
    assert DOMAIN_COLUMNS == ("snr_hat", "edge_width")


def _frame():
    rng = np.random.default_rng(0)
    rows = []
    for seg in ("global", "otsu"):
        for prof, snr0 in (("ideal", SNR_CAP), ("realistic", 10.0)):
            n = 1000
            rows.append(pd.DataFrame({
                "segmenter": seg, "profile": prof,
                "snr_hat": snr0 if prof == "ideal" else rng.normal(snr0, 0.5, n),
                "edge_width": rng.normal(0.8, 0.1, n)}))
    return pd.concat(rows, ignore_index=True)


def test_envelope_is_the_central_98_percent_per_stratum():
    env = fit_envelopes(_frame())
    lo, hi = env["otsu|realistic"]["snr_hat"]
    assert lo == pytest.approx(10 - 2.33 * 0.5, abs=0.15) and hi == pytest.approx(10 + 2.33 * 0.5, abs=0.15)
    assert env["global|ideal"]["snr_hat"] == [SNR_CAP, SNR_CAP]
    assert set(env) == {"global|ideal", "global|realistic", "otsu|ideal", "otsu|realistic"}


def test_in_domain_flags_values_outside_the_envelope_and_missing_values():
    env = fit_envelopes(_frame())["otsu|realistic"]
    assert in_domain({"snr_hat": 10.0, "edge_width": 0.8}, env)
    assert not in_domain({"snr_hat": 5.0, "edge_width": 0.8}, env)       # más ruido que la calibración
    assert not in_domain({"snr_hat": 10.0, "edge_width": 1.6}, env)      # más desenfoque
    assert not in_domain({"snr_hat": float("nan"), "edge_width": 0.8}, env)


def test_about_98_percent_of_calibration_rows_stay_in_domain_per_variable():
    df = _frame()
    env = fit_envelopes(df)
    g = df[(df.segmenter == "otsu") & (df.profile == "realistic")]
    inside = [in_domain(r, env["otsu|realistic"]) for r in g.to_dict("records")]
    assert 0.94 <= np.mean(inside) <= 0.985
