"""Certificado vectorial (v0.4): API ``certify`` y tabla de planificación.

Usa los modelos y envolventes congelados de verdad (copia empaquetada de
``results/summary/h9_frozen.json``).
"""
import json
import math
from pathlib import Path

import numpy as np
import pytest

from geovida.certificate import (
    OUT_OF_DOMAIN, certify, load_frozen, min_depth_for_green, planning_table,
)
from geovida.budget import FROZEN_H6
from geovida.imaging import ImagingSpec, render
from geovida.phantoms import make_phantom

ROOT = Path(__file__).resolve().parents[1]


def _image(shape="ball", t_over_h=12.0, psf=1.0, snr=10.0, seed=0):
    ph = make_phantom(shape, t=1.0)
    out = render(ph, ImagingSpec(h_xy=1.0 / t_over_h, psf_fwhm=psf, snr=snr),
                 np.random.default_rng(seed))
    return out.image, out.spacing


def test_packaged_frozen_models_match_the_versioned_summary():
    summary = json.loads((ROOT / "results" / "summary" / "h9_frozen.json").read_text())
    assert load_frozen() == summary


def test_well_resolved_in_domain_ball_is_green_in_volume_and_topology():
    # Con Otsu, una bola de 12 vóxeles dentro del dominio da verde en las dos medidas
    # (sonda previa: p_V = 0.99 y p_T = 0.92–0.98 en tres semillas). Con `smoothed_otsu` el
    # volumen de esa misma bola se queda en amarillo (p ≈ 0.55), como ya mostraba H6.
    img, sp = _image("ball", 12.0)
    c = certify(img, sp, "otsu", "realistic")
    assert c["volume"]["light"] == "verde" and c["volume"]["in_domain"]
    assert c["topology"]["betti"] == [1, 0, 0] and c["topology"]["light"] == "verde"
    assert c["volume"]["reason"] == "" and len(c["limits"]) >= 3


def test_smoothed_otsu_needs_more_voxels_than_otsu_for_a_green_volume():
    img, sp = _image("ball", 12.0)
    c = certify(img, sp, "smoothed_otsu", "realistic")
    assert c["volume"]["light"] == "amarillo" and 0.5 <= c["volume"]["p"] < 0.9


def test_barely_resolved_object_is_red():
    img, sp = _image("ball", 2.0)
    c = certify(img, sp, "smoothed_otsu", "realistic")
    assert c["volume"]["light"] == "rojo" and c["volume"]["p"] < 0.5


def test_noisier_image_than_calibration_never_gets_a_green_light():
    img, sp = _image("ball", 12.0, snr=4.0)                 # mucho más ruido que «realistic»
    c = certify(img, sp, "smoothed_otsu", "realistic")
    assert not c["volume"]["in_domain"] and c["volume"]["light"] != "verde"
    if c["volume"]["p"] >= 0.9:
        assert c["volume"]["light"] == "amarillo" and c["volume"]["reason"] == OUT_OF_DOMAIN


def test_blurrier_image_than_calibration_never_gets_a_green_light():
    img, sp = _image("ball", 12.0, psf=2.5)
    c = certify(img, sp, "smoothed_otsu", "realistic")
    assert not c["volume"]["in_domain"] and c["volume"]["light"] != "verde"


def test_empty_image_is_red_with_a_reason_not_an_error():
    c = certify(np.zeros((12, 12, 12), np.float32), (1.0, 1.0, 1.0), "global", "ideal")
    assert c["volume"]["light"] == "rojo" and c["topology"]["light"] == "rojo"
    assert c["volume"]["reason"] == "máscara vacía" and c["volume"]["value"] == 0.0


def test_certificate_is_json_serialisable_and_reports_the_fragile_site():
    ph = make_phantom("dumbbell", t=1.0)
    out = render(ph, ImagingSpec(h_xy=1.0 / 3.0), np.random.default_rng(1))
    c = certify(out.image, out.spacing, "global", "ideal")
    again = json.loads(json.dumps(c))
    assert again["topology"]["betti"] == [1, 0, 0]
    site = again["topology"]["critical_sites"]["erosion"]
    assert site["kind"] == "separación" and len(site["centroid_vox"]) == 3


def test_unknown_calibration_is_refused():
    img, sp = _image("ball", 8.0)
    with pytest.raises(KeyError):
        certify(img, sp, "otsu", "blurry")
    with pytest.raises(ValueError):
        certify(np.zeros((4, 4)), (1, 1, 1), "otsu", "ideal")


def test_min_depth_inverts_the_frozen_volume_model():
    for key, m in FROZEN_H6["models"].items():
        seg, prof = key.split("|")
        x = min_depth_for_green(seg, prof)
        assert 1 / (1 + math.exp(-(m["intercept"] + m["slope"] * math.log(x)))) == pytest.approx(0.90)


def test_planning_table_translates_depth_into_simple_geometries():
    rows = planning_table()
    assert len(rows) == 6
    r = next(r for r in rows if r["segmenter"] == "global" and r["profile"] == "ideal")
    assert r["ball_diameter_voxels"] == pytest.approx(8 * r["min_depth_voxels"])
    assert r["cylinder_diameter_voxels"] == pytest.approx(6 * r["min_depth_voxels"])
    assert r["slab_thickness_voxels"] == pytest.approx(4 * r["min_depth_voxels"])
    smooth = next(r for r in rows if r["segmenter"] == "smoothed_otsu" and r["profile"] == "realistic")
    assert smooth["min_depth_voxels"] > r["min_depth_voxels"]      # el suavizado exige más vóxeles
