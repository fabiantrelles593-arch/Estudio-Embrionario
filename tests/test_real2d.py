"""Pruebas de la rama de imagen 2D real (solo investigación y educación).

Se prueba con una «foto» sintética de verdad conocida; no se usa ninguna imagen de personas.
"""
import json
import math
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from geovida import biometry as bio
from geovida import real2d
from geovida.twod import render2d

FROZEN = Path(__file__).resolve().parents[1] / "results" / "summary" / "h14_frozen.json"


@pytest.fixture(scope="module")
def models():
    return bio.models_from_json(FROZEN.read_text())


def synthetic_photo(length_mm=30.0, native_h_mm=0.05, blur_mm=0.4, seed=11, margin=60):
    """Una «foto»: cápsula de verdad conocida, píxel nativo fino y margen oscuro alrededor."""
    f_px = blur_mm / native_h_mm
    ph = bio.make_body(length_mm)
    img = render2d(ph, bio.spec_for(native_h_mm, f_px), np.random.default_rng(seed)).image
    lo, hi = float(np.percentile(img, 1)), float(np.percentile(img, 99.5))
    g = np.clip((img - lo) / (hi - lo), 0, 1)
    canvas = np.pad(g, margin, mode="constant", constant_values=0.0)
    roi = (margin, margin, margin + g.shape[1], margin + g.shape[0])
    return canvas, roi


# --- escala -----------------------------------------------------------------------------------

def test_scale_from_ruler_two_points():
    s = real2d.scale_from_ruler((10, 10), (10, 110), length_mm=20.0)
    assert s.mm_per_px == pytest.approx(0.2)
    assert s.source == "regla"


def test_scale_from_ticks_uses_median_and_reports_spread():
    ticks = [0, 50.2, 99.8, 150.1, 199.9]
    s = real2d.scale_from_ticks(ticks, spacing_mm=10.0)
    assert s.mm_per_px == pytest.approx(0.2, rel=0.01)
    assert 0 <= s.spread_rel < 0.02


def test_scale_from_ticks_needs_at_least_three_marks():
    with pytest.raises(ValueError):
        real2d.scale_from_ticks([0, 50], spacing_mm=10.0)


def test_scale_rejects_degenerate_ruler():
    with pytest.raises(ValueError):
        real2d.scale_from_ruler((5, 5), (5, 5), length_mm=10.0)
    with pytest.raises(ValueError):
        real2d.scale_from_ruler((0, 0), (0, 10), length_mm=-1.0)


def test_caliper_distance_in_mm():
    s = real2d.Scale(mm_per_px=0.1, source="declarada", spread_rel=0.0)
    assert real2d.caliper_mm((0, 0), (30, 40), s) == pytest.approx(5.0)


# --- privacidad -------------------------------------------------------------------------------

def test_load_gray_drops_metadata_and_hashes_the_file(tmp_path):
    arr = (np.random.default_rng(0).random((40, 60)) * 255).astype(np.uint8)
    im = Image.fromarray(arr)
    exif = Image.Exif()
    exif[0x010E] = "NOMBRE PACIENTE SECRETO"         # ImageDescription
    p = tmp_path / "hermano_ecografia.jpg"
    im.save(p, exif=exif)
    loaded = real2d.load_gray(p)
    assert loaded.gray.shape == (40, 60)
    assert 0.0 <= loaded.gray.min() and loaded.gray.max() <= 1.0
    assert len(loaded.sha256) == 64
    assert "SECRETO" not in repr(loaded) and "hermano" not in repr(loaded)
    assert not hasattr(loaded, "exif") and not hasattr(loaded, "path")


def test_report_contains_no_path_or_filename(tmp_path, models):
    canvas, roi = synthetic_photo()
    p = tmp_path / "caso_privado_123.png"
    Image.fromarray((canvas * 255).astype(np.uint8)).save(p)
    loaded = real2d.load_gray(p)
    res = real2d.measure_roi(loaded.gray, roi, real2d.Scale(0.05, "declarada", 0.0), models=models)
    text = real2d.report_markdown(res, sha256=loaded.sha256, image_shape=loaded.gray.shape)
    assert "caso_privado" not in text and str(tmp_path) not in text
    assert loaded.sha256 in text
    json.dumps(real2d.report_dict(res, sha256=loaded.sha256, image_shape=loaded.gray.shape))


# --- geometría de trabajo ---------------------------------------------------------------------

def test_working_geometry_lands_inside_the_calibration_box():
    n, f_px, h = real2d.working_geometry(length_mm=20.0, blur_mm=0.5)
    assert 50 <= n <= 300 and 1 <= f_px <= 5
    assert f_px / n == pytest.approx(0.5 / 20.0, rel=1e-6)
    assert h == pytest.approx(20.0 / n)


def test_working_geometry_none_when_blur_is_too_large_for_the_object():
    assert real2d.working_geometry(length_mm=5.0, blur_mm=1.5) is None     # f/n = 0.30 > 0.10
    assert real2d.working_geometry(length_mm=300.0, blur_mm=0.1) is None   # f/n < 1/300


# --- medida de una foto sintética -------------------------------------------------------------

def test_measure_recovers_known_length_within_tolerance(models):
    canvas, roi = synthetic_photo(length_mm=30.0, native_h_mm=0.05, blur_mm=0.4)
    res = real2d.measure_roi(canvas, roi, real2d.Scale(0.05, "declarada", 0.0), models=models,
                             blur_mm_grid=(0.25, 0.5, 1.0))
    rows = [r for r in res["rows"] if r["in_box"]]
    assert rows, "debería haber al menos un desenfoque dentro de lo calibrado"
    for r in rows:
        assert abs(r["measured_mm"] - 30.0) / 30.0 < 0.06, r
    assert res["native"]["n_px"] > 400


def test_real_images_never_get_green_even_when_simulation_would(models):
    canvas, roi = synthetic_photo(length_mm=40.0, native_h_mm=0.05, blur_mm=0.4)
    res = real2d.measure_roi(canvas, roi, real2d.Scale(0.05, "declarada", 0.0), models=models,
                             blur_mm_grid=(0.25, 0.5))
    assert res["validated_on_real"] is False
    assert all(r["light"] != "verde" for r in res["rows"])
    # el semáforo que daría la simulación se conserva, rotulado como tal
    assert any(r.get("light_if_simulation_held") == "verde" for r in res["rows"])


def test_out_of_domain_rows_explain_why(models):
    canvas, roi = synthetic_photo(length_mm=30.0, native_h_mm=0.05, blur_mm=0.4)
    res = real2d.measure_roi(canvas, roi, real2d.Scale(0.05, "declarada", 0.0), models=models,
                             blur_mm_grid=(12.0,))
    (row,) = res["rows"]
    assert row["in_box"] is False and row["light"] == "amarillo"
    assert "caja" in row["reason"] or "desenfoque" in row["reason"]


def test_qc_flags_object_cut_by_the_region_of_interest(models):
    canvas, roi = synthetic_photo(length_mm=30.0, native_h_mm=0.05, blur_mm=0.4)
    x0, y0, x1, y1 = roi
    cut = (x0 + (x1 - x0) // 3, y0, x1, y1)           # recorta un tercio del objeto
    res = real2d.measure_roi(canvas, cut, real2d.Scale(0.05, "declarada", 0.0), models=models,
                             blur_mm_grid=(0.5,))
    assert res["qc"]["touches_roi_border"] is True


def test_bias_corrected_length_is_closer_to_truth_on_average(models):
    errs_raw, errs_cor = [], []
    for seed in range(6):
        canvas, roi = synthetic_photo(length_mm=30.0, native_h_mm=0.05, blur_mm=0.4, seed=100 + seed)
        res = real2d.measure_roi(canvas, roi, real2d.Scale(0.05, "declarada", 0.0), models=models,
                                 blur_mm_grid=(0.5,))
        r = res["rows"][0]
        assert "bias_corrected_mm" in r
        errs_raw.append(abs(r["measured_mm"] - 30.0))
        errs_cor.append(abs(r["bias_corrected_mm"] - 30.0))
    assert np.mean(errs_cor) <= np.mean(errs_raw) + 1e-9


def test_dating_block_is_informative_not_certified(models):
    canvas, roi = synthetic_photo(length_mm=40.0, native_h_mm=0.05, blur_mm=0.4)
    res = real2d.measure_roi(canvas, roi, real2d.Scale(0.05, "declarada", 0.0), models=models,
                             blur_mm_grid=(0.5,))
    d = res["dating_formula"]
    assert d["in_formula_range"] is True
    assert d["ga_days_intergrowth"] == pytest.approx(
        40.9041 + 3.21585 * math.sqrt(res["rows"][0]["measured_mm"]) + 0.348956 * res["rows"][0]["measured_mm"], rel=0.02)
    assert "sd_ga_days" in d and "certificado" not in d


def test_comparison_with_printed_measurement_is_descriptive():
    c = real2d.compare_printed(measured_mm=21.0, printed_mm=20.0)
    assert c["diff_mm"] == pytest.approx(1.0) and c["diff_pct"] == pytest.approx(5.0)
    assert "criterio" not in c      # con n = 1 no hay regla de éxito


def test_overlay_is_written(tmp_path, models):
    canvas, roi = synthetic_photo()
    res = real2d.measure_roi(canvas, roi, real2d.Scale(0.05, "declarada", 0.0), models=models,
                             blur_mm_grid=(0.5,))
    out = tmp_path / "overlay.png"
    real2d.save_overlay(canvas, roi, res["native"]["mask"], out)
    assert out.exists() and out.stat().st_size > 1000


# --- línea de órdenes -------------------------------------------------------------------------

def _write_photo(tmp_path):
    canvas, roi = synthetic_photo(length_mm=30.0, native_h_mm=0.05, blur_mm=0.4)
    p = tmp_path / "foto.png"
    Image.fromarray((canvas * 255).astype(np.uint8)).save(p)
    return p, roi


def test_cli_refuses_human_image_without_authorization_note(tmp_path, capsys):
    from geovida import cli
    p, roi = _write_photo(tmp_path)
    argv = ["real2d", str(p), "--roi", *map(str, roi), "--mm-per-px", "0.05", "--human",
            "--frozen", str(FROZEN), "--out", str(tmp_path / "out")]
    assert cli.main(argv) != 0
    assert not (tmp_path / "out" / "informe.md").exists()


def test_cli_runs_with_authorization_note_and_writes_private_report(tmp_path):
    from geovida import cli
    p, roi = _write_photo(tmp_path)
    out = tmp_path / "out"
    argv = ["real2d", str(p), "--roi", *map(str, roi), "--mm-per-px", "0.05", "--human",
            "--authorization-note", "declarado por el usuario; documento no verificado",
            "--printed-crl-mm", "30", "--frozen", str(FROZEN), "--out", str(out)]
    assert cli.main(argv) == 0
    text = (out / "informe.md").read_text()
    assert "declarado por el usuario" in text
    assert "foto.png" not in text and str(tmp_path) not in text
    assert (out / "superposicion.png").exists()
