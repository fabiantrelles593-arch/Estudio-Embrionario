"""Anonimización local (geovida.deidentify) con imágenes sintéticas.

Qué haría fallar cada prueba: si los metadatos EXIF pasaran a la copia, un nombre o una fecha incrustados en el
archivo sobrevivirían; si las cajas en fracciones no se convirtieran bien, quedaría texto sin tapar; si se pudiera
escribir fuera de data/private/, una imagen podría acabar en el repositorio; si el registro guardara el nombre del
archivo original, ese nombre (que suele llevar el de la paciente) se filtraría. Sin imágenes humanas.
"""
import json

import numpy as np
import pytest

from geovida import deidentify as di

Image = pytest.importorskip("PIL.Image")


@pytest.fixture
def private(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data" / "private").mkdir(parents=True)
    return tmp_path / "data" / "private"


def _jpeg_with_exif(path):
    arr = np.full((60, 80, 3), 200, np.uint8)
    im = Image.fromarray(arr)
    exif = Image.Exif()
    exif[0x010E] = "NOMBRE APELLIDO 12345678"        # ImageDescription
    exif[0x9003] = "2021:07:06 14:10:41"              # DateTimeOriginal
    im.save(path, format="JPEG", exif=exif.tobytes())
    return arr


def test_boxes_in_pixels_and_fractions():
    shape = (100, 200, 3)
    assert di.to_pixel_box([0.0, 0.0, 0.5, 0.25], shape) == (0, 0, 100, 25)
    assert di.to_pixel_box([150, 90, 10, 5], shape) == (10, 5, 150, 90)
    assert di.to_pixel_box([190, 0, 400, 300], shape) == (190, 0, 200, 100)
    with pytest.raises(ValueError):
        di.to_pixel_box([300, 0, 400, 10], shape)
    with pytest.raises(ValueError):
        di.to_pixel_box([1, 2, 3], shape)


def test_redact_blacks_out_only_the_boxes():
    px = np.full((10, 10, 3), 255, np.uint8)
    out = di.redact(px, [[0, 0, 5, 2]])
    assert (out[:2, :5] == 0).all() and (out[2:, :] == 255).all() and (out[:, 5:] == 255).all()
    assert (px == 255).all()


def test_anonymize_strips_exif_and_keeps_no_source_name(private, tmp_path):
    src = tmp_path / "NOMBRE_APELLIDO_ecografia.jpg"
    _jpeg_with_exif(src)
    with Image.open(src) as im:
        assert len(im.getexif()) > 0
    rec = di.anonymize(src, [[0.0, 0.0, 1.0, 0.2]], private / "anon", "CI-001-IMG01")
    out = private / "anon" / "CI-001-IMG01.png"
    assert rec["check"]["clean"] and di.check_clean(out)["clean"]
    log = (private / "anon" / "CI-001-IMG01.json").read_text(encoding="utf-8")
    assert "NOMBRE" not in log and "ecografia.jpg" not in log
    assert json.loads(log)["human_review"] == "pendiente"
    px = di.load_pixels(out)
    assert (px[:12] == 0).all() and px[12:].mean() > 150


def test_refuses_to_write_outside_private(private, tmp_path):
    src = tmp_path / "a.jpg"
    _jpeg_with_exif(src)
    with pytest.raises(ValueError, match="data"):
        di.anonymize(src, [[0, 0, 1, 1]], tmp_path / "docs", "CI-001-IMG01")
    with pytest.raises(ValueError, match="código"):
        di.anonymize(src, [[0, 0, 1, 1]], private / "anon", "nombre apellido")


def test_preview_draws_boxes(private, tmp_path):
    px = np.full((50, 50, 3), 128, np.uint8)
    di.preview(px, [[10, 10, 30, 30]], private / "revision" / "x.png")
    out = di.load_pixels(private / "revision" / "x.png")
    assert tuple(out[10, 20]) == (255, 0, 0)
