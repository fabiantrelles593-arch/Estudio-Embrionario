"""Lectura por losas para MT-A (``geovida.minc.minc_slabs``, ``geovida.atlas_effect.stream_volume``).

Qué falla si leer por partes deja de dar lo mismo que cargar el volumen entero: el submuestreo ×4, el umbral de
Otsu de las puertas G0-a/b o el valor de cada landmark. Volúmenes sintéticos y fantomas MINC escritos aquí.
"""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from geovida import atlas_effect as ae

pytest.importorskip("skimage")
from skimage.filters import threshold_otsu  # noqa: E402

_spec = importlib.util.spec_from_file_location("test_minc_helpers", Path(__file__).with_name("test_minc.py"))


def _volume(shape=(23, 30, 26), seed=0):
    rng = np.random.default_rng(seed)
    z, y, x = np.indices(shape)
    body = ((z - shape[0] / 2) ** 2 / 60 + (y - shape[1] / 2) ** 2 / 90 + (x - shape[2] / 2) ** 2 / 70) < 1
    return (body * 900 + rng.normal(100, 30, shape)).astype(np.float32)


AFFINE = np.array([[0.0, 0.0, 0.03, -0.4], [0.0, -0.05, 0.0, 0.7], [0.04, 0.0, 0.0, -0.2], [0, 0, 0, 1.0]])


def _slabs(arr, size):
    return lambda: ((i, arr[i:i + size]) for i in range(0, len(arr), size))


@pytest.mark.parametrize("factor", [1, 2, 4])
def test_stream_equals_loading_the_whole_volume(factor):
    arr = _volume()
    rng = np.random.default_rng(1)
    pts = (AFFINE[:3, :3] @ (rng.uniform(-2, np.array(arr.shape) + 1, (60, 3))).T).T + AFFINE[:3, 3]
    r = ae.stream_volume(_slabs(arr, factor), arr.shape, AFFINE, factor=factor, points=pts)
    ds, aff = ae.downsample(arr, AFFINE, factor)
    assert r["downsampled"].shape == ds.shape
    assert np.allclose(r["downsampled"], ds, rtol=1e-6, atol=1e-4)
    assert np.allclose(r["affine_ds"], aff)
    assert r["otsu"] == pytest.approx(float(threshold_otsu(arr)), rel=1e-6)
    assert r["inside"] == pytest.approx(ae.fraction_inside(arr, AFFINE, pts))
    idx = np.rint(ae.world_to_index(pts, AFFINE)).astype(int)
    ok = np.all((idx >= 0) & (idx < np.array(arr.shape)), axis=1)
    assert 0 < ok.sum() < len(pts)                                  # hay puntos dentro y fuera del volumen
    assert np.array_equal(r["point_values"][ok], arr[tuple(idx[ok].T)]) and np.isnan(r["point_values"][~ok]).all()


def test_stream_rejects_misaligned_slabs():
    arr = _volume()
    with pytest.raises(ValueError):
        ae.stream_volume(lambda: ((i, arr[i:i + 3]) for i in range(0, len(arr), 3)), arr.shape, AFFINE, factor=4)


@pytest.mark.parametrize("fmt", ["minc1_int", "minc2"])
def test_minc_slabs_match_load_minc(tmp_path, fmt):
    pytest.importorskip("nibabel")
    helpers = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(helpers)
    from geovida import minc
    data = helpers._ball().astype(np.float32) * 700 + np.linspace(0, 50, np.prod(helpers.SHAPE)).reshape(helpers.SHAPE)
    path = tmp_path / "v.mnc"
    if fmt == "minc1_int":
        helpers._write_minc1(path, np.rint(data).astype(np.int16), typecode="h", valid_range=(0, 32767),
                             real_range=(0.0, 1000.0))
    else:
        helpers._write_minc2(path, data)
    full, _, meta = minc.load_minc(path)
    parts = list(minc.minc_slabs(path, 4))
    assert [i for i, _ in parts] == list(range(0, full.shape[0], 4))
    assert np.array_equal(np.concatenate([s for _, s in parts]), full)
    shape, affine, _ = minc.minc_header(path)
    assert shape == full.shape and np.allclose(affine, meta["affine"])
    r = ae.stream_volume(lambda: minc.minc_slabs(path, 4), shape, affine, factor=4)
    assert np.allclose(r["downsampled"], ae.downsample(full, affine, 4)[0], rtol=1e-6, atol=1e-4)
