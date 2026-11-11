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


# --- v0.5: informe con trazabilidad, congelado recalibrado y NIfTI --------------------------------
import hashlib
import re
from pathlib import Path

import pytest

import geovida
from geovida import h12

ROOT = Path(__file__).resolve().parents[1]


def test_package_version_matches_pyproject():
    declared = re.search(r'^version\s*=\s*"([^"]+)"', (ROOT / "pyproject.toml").read_text(),
                         re.MULTILINE).group(1)
    assert geovida.__version__ == declared


@pytest.fixture(scope="module")
def us_frozen_file(tmp_path_factory):
    from test_h12 import US, _frame
    path = tmp_path_factory.mktemp("frozen") / "us_frozen.json"
    path.write_text(json.dumps(h12.freeze_us(_frame(seed=2, profiles=US))))
    return path


def _ball_npy(tmp_path, profile="us_compound"):
    from geovida.imaging import render, spec_for_t_over_h
    out = render(make_phantom("ball", t=1.0), spec_for_t_over_h(16.0, 1.0, profile),
                 np.random.default_rng(3))
    npy = tmp_path / "volumen_de_paciente_123.npy"          # un nombre que NO debe filtrarse
    np.save(npy, out.image)
    return npy, out.spacing


def test_certify_with_ultrasound_profile_needs_a_matching_frozen_file(tmp_path, us_frozen_file):
    npy, sp = _ball_npy(tmp_path)
    args = ["certify", str(npy), "--spacing", *map(str, sp), "--segmenter", "smoothed_otsu",
            "--profile", "us_compound"]
    with pytest.raises(SystemExit) as exc:
        main(args)                                           # sin --frozen: v0.4 no conoce us_compound
    assert "us_compound" in str(exc.value)
    assert main([*args, "--frozen", str(us_frozen_file)]) == 0


def test_report_records_provenance_and_hides_the_file_name_by_default(tmp_path, us_frozen_file):
    npy, sp = _ball_npy(tmp_path)
    rep = tmp_path / "informe.md"
    assert main(["certify", str(npy), "--spacing", *map(str, sp), "--segmenter", "smoothed_otsu",
                 "--profile", "us_compound", "--frozen", str(us_frozen_file),
                 "--report", str(rep)]) == 0
    text = rep.read_text()
    img_hash = hashlib.sha256(npy.read_bytes()).hexdigest()
    frozen_hash = hashlib.sha256(us_frozen_file.read_bytes()).hexdigest()
    assert img_hash in text and frozen_hash in text
    assert geovida.__version__ in text
    assert "smoothed_otsu" in text and "us_compound" in text
    assert "volumen_de_paciente_123" not in text             # privacidad: sin nombre de archivo
    assert "sin uso clínico" in text and "no es un informe médico" in text.lower()
    assert "Volumen" in text and "Topología" in text


def test_report_can_include_the_file_name_when_asked(tmp_path, us_frozen_file):
    npy, sp = _ball_npy(tmp_path)
    rep = tmp_path / "informe.md"
    main(["certify", str(npy), "--spacing", *map(str, sp), "--segmenter", "smoothed_otsu",
          "--profile", "us_compound", "--frozen", str(us_frozen_file), "--report", str(rep),
          "--include-filename"])
    assert "volumen_de_paciente_123.npy" in rep.read_text()


def test_report_for_packaged_calibration_records_its_hash(tmp_path):
    ph = make_phantom("ball", t=1.0)
    out = render(ph, ImagingSpec(h_xy=1.0 / 12.0, psf_fwhm=1.0, snr=10.0), np.random.default_rng(2))
    npy, rep = tmp_path / "x.npy", tmp_path / "r.json"
    np.save(npy, out.image)
    main(["certify", str(npy), "--spacing", *map(str, out.spacing), "--segmenter", "otsu",
          "--profile", "realistic", "--report", str(rep)])
    data = json.loads(rep.read_text())
    assert data["provenance"]["calibration"]["source"] == "paquete: geovida/frozen/h9_frozen.json"
    assert len(data["provenance"]["calibration"]["sha256"]) == 64
    assert data["provenance"]["input"]["sha256"] == hashlib.sha256(npy.read_bytes()).hexdigest()
    assert data["provenance"]["input"]["file_name"] is None


def test_us_frozen_carries_its_own_limits(us_frozen_file):
    frozen = json.loads(us_frozen_file.read_text())
    assert any("ecografía" in s and "simulada" in s for s in frozen["limits"])
    assert any("sin uso clínico" in s for s in frozen["limits"])


def test_certify_reads_nifti_and_takes_the_voxel_from_its_header(tmp_path, us_frozen_file):
    nib = pytest.importorskip("nibabel")
    npy, sp = _ball_npy(tmp_path)
    arr = np.load(npy)
    nii = tmp_path / "v.nii.gz"
    im = nib.Nifti1Image(arr, np.diag([sp[0], sp[1], sp[2], 1.0]))
    im.header.set_xyzt_units("mm")
    nib.save(im, str(nii))
    js = tmp_path / "c.json"
    assert main(["certify", str(nii), "--segmenter", "smoothed_otsu", "--profile", "us_compound",
                 "--frozen", str(us_frozen_file), "--json", str(js)]) == 0
    cert = json.loads(js.read_text())
    assert cert["spacing"] == pytest.approx(list(sp), rel=1e-5)
