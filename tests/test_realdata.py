"""Pruebas del lector de datos reales (v0.5). Usan volúmenes sintéticos guardados como NIfTI:
no hay ninguna imagen real en el repositorio."""
import numpy as np
import pytest

nib = pytest.importorskip("nibabel")

from geovida import realdata  # noqa: E402


def _ball_volume(n=48, radius=14.0, sigma=1.2, seed=0):
    zz, yy, xx = np.mgrid[:n, :n, :n]
    c = (n - 1) / 2
    inside = ((zz - c) ** 2 + (yy - c) ** 2 + (xx - c) ** 2) <= radius ** 2
    from scipy.ndimage import gaussian_filter
    img = gaussian_filter(inside.astype(np.float32), sigma)
    img = 0.1 + 0.8 * img + np.random.default_rng(seed).normal(0, 0.02, img.shape)
    return img.astype(np.float32), inside


def _save(path, arr, zooms, dtype=None):
    data = arr if dtype is None else arr.astype(dtype)
    aff = np.diag([*zooms, 1.0])
    im = nib.Nifti1Image(data, aff)
    im.header.set_xyzt_units("mm")
    nib.save(im, str(path))


def test_load_volume_reads_spacing_and_squeezes(tmp_path):
    img, _ = _ball_volume()
    p = tmp_path / "a.nii.gz"
    _save(p, img[..., None], (0.05, 0.06, 0.07))
    arr, spacing, meta = realdata.load_volume(p)
    assert arr.shape == img.shape and arr.dtype == np.float32
    assert spacing == pytest.approx((0.05, 0.06, 0.07))
    assert meta["unit"] == "mm"


def test_load_volume_converts_micrometres(tmp_path):
    img, _ = _ball_volume()
    p = tmp_path / "a.nii"
    aff = np.diag([50.0, 50.0, 50.0, 1.0])
    im = nib.Nifti1Image(img, aff)
    im.header.set_xyzt_units("micron")
    nib.save(im, str(p))
    _, spacing, meta = realdata.load_volume(p)
    assert spacing == pytest.approx((0.05, 0.05, 0.05))
    assert meta["unit"] == "micron"


def test_datasheet_recognises_labels_and_intensities():
    img, inside = _ball_volume()
    lab = inside.astype(np.uint8) * 2
    d_lab = realdata.datasheet(lab, (0.1, 0.1, 0.1), "lab")
    assert d_lab["label_like"]
    assert d_lab["labels"] == {"0": int((~inside).sum()), "2": int(inside.sum())}
    assert d_lab["labels_volume_mm3"]["2"] == pytest.approx(inside.sum() * 1e-3)
    d_img = realdata.datasheet(img, (0.1, 0.1, 0.1), "img")
    assert not d_img["label_like"] and d_img["p50"] < d_img["p99"]
    # el resumen no calcula nada contra una referencia
    assert not any("dice" in k or "error" in k for k in d_img)


def test_compare_case_ball_is_certified_and_close_to_reference():
    img, inside = _ball_volume(n=64, radius=20.0)
    out = realdata.compare_case(img, (1.0, 1.0, 1.0), inside, "otsu", "realistic")
    assert abs(out["rel_error_volume"]) < 0.10
    assert out["dice"] > 0.9
    assert out["betti_ref"] == [1, 0, 0] and out["betti_measured"] == [1, 0, 0]
    assert out["light_volume"] in ("verde", "amarillo", "rojo")
    assert out["ok5"] in (True, False) and out["ok10"] in (True, False)
    assert out["volume_mm3_measured"] == pytest.approx(out["volume_mm3_reference"], rel=0.15)


def test_compare_case_rejects_bad_reference():
    img, inside = _ball_volume()
    with pytest.raises(ValueError):
        realdata.compare_case(img, (1, 1, 1), np.zeros_like(inside), "otsu", "realistic")
    with pytest.raises(ValueError):
        realdata.compare_case(img, (1, 1, 1), inside[:-1], "otsu", "realistic")


def test_scan_lists_files_without_pairing(tmp_path):
    img, inside = _ball_volume()
    _save(tmp_path / "x_img.nii.gz", img, (0.1, 0.1, 0.1))
    _save(tmp_path / "x_lab.nii.gz", inside, (0.1, 0.1, 0.1), dtype=np.uint8)
    rows = realdata.scan(tmp_path)
    assert {r["name"] for r in rows} == {"x_img.nii.gz", "x_lab.nii.gz"}
    assert next(r for r in rows if r["name"] == "x_lab.nii.gz")["label_like"]


def test_roi_margin_crops_around_reference_and_is_recorded():
    img, inside = _ball_volume(n=64, radius=12.0)
    out = realdata.compare_case(img, (1.0, 1.0, 1.0), inside, "otsu", "realistic", roi_margin=0.25)
    assert out["roi_margin"] == 0.25
    assert max(out["shape"]) < 64
    ci, cr = realdata.crop_to_reference(img, inside, 0.25)
    assert ci.shape == cr.shape and cr.sum() == inside.sum()
