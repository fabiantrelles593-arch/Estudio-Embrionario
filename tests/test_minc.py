"""Pruebas del lector MINC (ADR-005) con fantomas sintéticos escritos en MINC1 y MINC2.

No hay ningún archivo de MusMorph en el repositorio. Cada fantoma es una bola de radio conocido,
definida en coordenadas del mundo, dentro de una rejilla con espaciado anisótropo, un paso negativo,
origen desplazado y, en un caso, ejes oblicuos. Se comprueba que el lector devuelve exactamente esa
geometría: forma, orden de ejes, espaciado, afín, orientación, intensidades y volumen.
"""
import gzip
import math
import shutil

import numpy as np
import pytest

pytest.importorskip("nibabel")
from nibabel.externals.netcdf import netcdf_file  # noqa: E402

from geovida import minc, realdata  # noqa: E402

DIMS = ("zspace", "yspace", "xspace")  # orden en disco: z el más lento, x el más rápido
SHAPE = (40, 44, 48)
STEPS = {"zspace": 0.054, "yspace": -0.027, "xspace": 0.036}  # mm; y con paso negativo
STARTS = {"zspace": -1.0, "yspace": 0.6, "xspace": -0.85}  # mm
IDENTITY = {"xspace": (1.0, 0.0, 0.0), "yspace": (0.0, 1.0, 0.0), "zspace": (0.0, 0.0, 1.0)}
RADIUS = 0.5  # mm; bola centrada en el origen del mundo
BALL_MM3 = 4.0 / 3.0 * math.pi * RADIUS ** 3


def _rotated_z(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return {"xspace": (c, s, 0.0), "yspace": (-s, c, 0.0), "zspace": (0.0, 0.0, 1.0)}


def _affine(dircos):
    """Afín esperada, calculada aquí a partir de la definición de MINC y no con el lector."""
    aff = np.eye(4)
    for j, d in enumerate(DIMS):
        u = np.asarray(dircos[d], dtype=float)
        aff[:3, j] = u * STEPS[d]
        aff[:3, 3] += u * STARTS[d]
    return aff


def _ball(dircos=IDENTITY):
    aff = _affine(dircos)
    idx = np.indices(SHAPE).reshape(3, -1).astype(float)
    world = aff[:3, :3] @ idx + aff[:3, 3:4]
    return (np.linalg.norm(world, axis=0) <= RADIUS).reshape(SHAPE)


def _scalar(f, name, typecode, value):
    # assignValue() de la copia de NetCDF en nibabel usa ndarray.itemset, que NumPy 2 ya no tiene
    v = f.createVariable(name, typecode, ())
    v.data[()] = value
    return v


def _write_minc1(path, data, dircos=IDENTITY, *, typecode="f", valid_range=None,
                 real_range=None, units=b"mm"):
    f = netcdf_file(str(path), "w")
    try:
        for d, n in zip(DIMS, SHAPE):
            f.createDimension(d, n)
        for d in DIMS:
            v = _scalar(f, d, "i", 0)
            v.step = np.float64(STEPS[d])
            v.start = np.float64(STARTS[d])
            v.direction_cosines = np.asarray(dircos[d], dtype=np.float64)
            v.spacing = b"regular__"
            v.units = units
        img = f.createVariable("image", typecode, DIMS)
        img[:] = data
        img.signtype = b"signed__"
        if valid_range is not None:
            img.valid_range = np.asarray(valid_range, dtype=np.float64)
        lo, hi = real_range if real_range is not None else (float(data.min()), float(data.max()))
        _scalar(f, "image-min", "d", lo)
        _scalar(f, "image-max", "d", hi)
    finally:
        f.close()


def _write_minc2(path, data, dircos=IDENTITY):
    h5py = pytest.importorskip("h5py")
    with h5py.File(str(path), "w") as f:
        root = f.create_group("minc-2.0")
        dims = root.create_group("dimensions")
        for d, n in zip(DIMS, SHAPE):
            ds = dims.create_dataset(d, data=np.int32(0))
            ds.attrs["length"] = np.int32(n)
            ds.attrs["step"] = np.float64(STEPS[d])
            ds.attrs["start"] = np.float64(STARTS[d])
            ds.attrs["direction_cosines"] = np.asarray(dircos[d], dtype=np.float64)
            ds.attrs["spacing"] = np.bytes_(b"regular__")
            ds.attrs["units"] = np.bytes_(b"mm")
        g = root.create_group("image").create_group("0")
        im = g.create_dataset("image", data=np.asarray(data, dtype=np.float32))
        im.attrs["dimorder"] = np.bytes_(",".join(DIMS).encode())
        g.create_dataset("image-min", data=np.float64(data.min()))
        g.create_dataset("image-max", data=np.float64(data.max()))


def _check_geometry(arr, spacing, meta, inside, dircos=IDENTITY):
    assert arr.shape == SHAPE and arr.dtype == np.float32
    assert spacing == pytest.approx((0.054, 0.027, 0.036), rel=1e-12)
    assert meta["steps"] == pytest.approx([0.054, -0.027, 0.036], rel=1e-12)
    assert meta["dim_names"] == list(DIMS)
    assert np.allclose(meta["affine"], _affine(dircos), atol=1e-12)
    assert meta["world_axes"] == ["+z", "-y", "+x"]
    assert meta["unit"] == "mm" and meta["unit_known"]
    assert np.array_equal(arr > 0.5, inside)
    vol = inside.sum() * float(np.prod(spacing))
    assert vol == pytest.approx(BALL_MM3, rel=0.02)


def test_minc_format_detects_both_versions_and_rejects_others(tmp_path):
    inside = _ball()
    data = (0.1 + 0.8 * inside).astype(np.float32)
    _write_minc1(tmp_path / "a.mnc", data)
    assert minc.minc_format(tmp_path / "a.mnc") == "MINC1"
    with open(tmp_path / "a.mnc", "rb") as src, gzip.open(tmp_path / "a.mnc.gz", "wb") as dst:
        shutil.copyfileobj(src, dst)
    assert minc.minc_format(tmp_path / "a.mnc.gz") == "MINC1"
    (tmp_path / "x.mnc").write_bytes(b"no soy MINC")
    with pytest.raises(ValueError):
        minc.minc_format(tmp_path / "x.mnc")
    _write_minc2(tmp_path / "b.mnc", data)
    assert minc.minc_format(tmp_path / "b.mnc") == "MINC2"


def test_minc1_float_phantom_keeps_geometry(tmp_path):
    inside = _ball()
    data = (0.1 + 0.8 * inside).astype(np.float32)
    _write_minc1(tmp_path / "bola.mnc", data)
    arr, spacing, meta = minc.load_minc(tmp_path / "bola.mnc")
    assert meta["format"] == "MINC1"
    _check_geometry(arr, spacing, meta, inside)
    assert np.allclose(arr, data)


def test_minc1_gzip_reads_the_same(tmp_path):
    inside = _ball()
    data = (0.1 + 0.8 * inside).astype(np.float32)
    _write_minc1(tmp_path / "bola.mnc", data)
    with open(tmp_path / "bola.mnc", "rb") as src, gzip.open(tmp_path / "bola.mnc.gz", "wb") as dst:
        shutil.copyfileobj(src, dst)
    arr, spacing, meta = minc.load_minc(tmp_path / "bola.mnc.gz")
    _check_geometry(arr, spacing, meta, inside)


def test_minc1_integer_data_are_rescaled_to_real_values(tmp_path):
    inside = _ball()
    raw = np.where(inside, 1000, 100).astype(np.int16)
    _write_minc1(tmp_path / "int.mnc", raw, typecode="h", valid_range=(0, 1000),
                 real_range=(0.0, 2.0))
    arr, _, meta = minc.load_minc(tmp_path / "int.mnc")
    assert "i2" in meta["dtype"]
    assert np.allclose(arr[inside], 2.0) and np.allclose(arr[~inside], 0.2)


def test_minc2_phantom_keeps_geometry(tmp_path):
    inside = _ball()
    data = (0.1 + 0.8 * inside).astype(np.float32)
    _write_minc2(tmp_path / "bola2.mnc", data)
    arr, spacing, meta = minc.load_minc(tmp_path / "bola2.mnc")
    assert meta["format"] == "MINC2"
    _check_geometry(arr, spacing, meta, inside)


def test_oblique_direction_cosines_enter_the_affine(tmp_path):
    rot = _rotated_z(30.0)
    inside = _ball(rot)
    data = (0.1 + 0.8 * inside).astype(np.float32)
    _write_minc1(tmp_path / "obl.mnc", data, rot)
    arr, spacing, meta = minc.load_minc(tmp_path / "obl.mnc")
    _check_geometry(arr, spacing, meta, inside, rot)
    assert not np.allclose(meta["affine"], _affine(IDENTITY))


def test_non_millimetre_units_are_rejected(tmp_path):
    inside = _ball()
    _write_minc1(tmp_path / "cm.mnc", inside.astype(np.float32), units=b"cm")
    with pytest.raises(ValueError, match="mm"):
        minc.load_minc(tmp_path / "cm.mnc")


def test_label_phantom_volume_through_datasheet(tmp_path):
    inside = _ball()
    _write_minc1(tmp_path / "lab.mnc", inside.astype(np.int16), typecode="h",
                 valid_range=(0, 1), real_range=(0.0, 1.0))
    arr, spacing, _ = minc.load_minc(tmp_path / "lab.mnc")
    sheet = realdata.datasheet(arr, spacing, "lab")
    assert sheet["label_like"] and sheet["labels"]["1"] == int(inside.sum())
    assert sheet["labels_volume_mm3"]["1"] == pytest.approx(BALL_MM3, rel=0.02)
