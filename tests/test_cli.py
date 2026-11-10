"""Línea de órdenes de geovida."""
import json

import numpy as np

from geovida.cli import main
from geovida.imaging import ImagingSpec, render
from geovida.phantoms import make_phantom


def test_plan_prints_one_row_per_calibrated_stratum(capsys):
    assert main(["plan"]) == 0
    out = capsys.readouterr().out
    assert out.count("realistic") == 3 and out.count("ideal") == 3 and "bola" in out


def test_certify_writes_a_json_certificate_and_prints_the_lights(tmp_path, capsys):
    ph = make_phantom("torus", t=1.0)
    out = render(ph, ImagingSpec(h_xy=1.0 / 10.0, psf_fwhm=1.0, snr=10.0), np.random.default_rng(2))
    npy, js = tmp_path / "img.npy", tmp_path / "cert.json"
    np.save(npy, out.image)
    code = main(["certify", str(npy), "--spacing", *map(str, out.spacing),
                 "--segmenter", "smoothed_otsu", "--profile", "realistic", "--json", str(js)])
    assert code == 0
    cert = json.loads(js.read_text())
    assert cert["topology"]["betti"] == [1, 1, 0] and cert["declared"]["segmenter"] == "smoothed_otsu"
    text = capsys.readouterr().out
    assert "Volumen" in text and "Topología" in text and "sin uso clínico" in text
