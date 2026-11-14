"""Lector de volúmenes MINC (.mnc) para el piloto con MusMorph (ADR-005).

Qué hace
--------
* ``minc_format``: distingue MINC1 (NetCDF clásico) de MINC2 (HDF5) por la firma del archivo.
* ``load_minc``: lee el volumen con nibabel y devuelve la imagen en float32, el tamaño del vóxel en
  milímetros por eje del arreglo y los metadatos de orientación: afín vóxel→mundo, pasos con signo,
  nombres de las dimensiones y unidades declaradas.
* ``world_axes``: para cada eje del arreglo, el eje del mundo (con signo) al que más se parece.

Convenciones
------------
El arreglo se devuelve en el orden en que está guardado (en MINC suele ser z, y, x, del eje más lento
al más rápido); no se transpone. ``spacing`` sigue ese mismo orden. La afín lleva los índices
(i, j, k) del arreglo a coordenadas del mundo en mm, como en nibabel. Un paso negativo en el archivo
da un espaciado positivo y queda registrado con su signo en ``meta["steps"]``. Si una dimensión
espacial declara unidades distintas de mm, la lectura se rechaza en vez de adivinar un factor.

Qué NO hace
-----------
No escribe MINC, no remuestrea ni reorienta. No admite espaciado irregular ni volúmenes 4D. No
incluye código de MusMorph (GPL-3.0; ver ADR-005). Las pruebas usan fantomas sintéticos: que el
lector funcione con ellos no valida ninguna imagen real.
"""
from __future__ import annotations

import gzip
from pathlib import Path

import numpy as np

MINC_SUFFIXES = (".mnc", ".mnc.gz")
_MAGIC = {b"CDF\x01": "MINC1", b"\x89HDF": "MINC2"}
_MM = {"mm", "millimeter", "millimeters", "millimetre", "millimetres"}


def _nib():
    try:
        import nibabel
    except ImportError as exc:  # pragma: no cover
        raise ImportError("para leer MINC instala nibabel: pip install 'geovida[real]'") from exc
    return nibabel


def minc_format(path) -> str:
    """'MINC1' o 'MINC2' según los cuatro primeros bytes (descomprime .gz si hace falta)."""
    path = Path(path)
    opener = gzip.open if path.name.lower().endswith(".gz") else open
    with opener(path, "rb") as fh:
        head = fh.read(4)
    if head not in _MAGIC:
        raise ValueError(f"{path}: no parece un archivo MINC (firma {head!r})")
    return _MAGIC[head]


def world_axes(affine) -> list[str]:
    """Eje del mundo, con signo, al que apunta cada eje del arreglo; p. ej. ['+z', '-y', '+x']."""
    a = np.asarray(affine, dtype=float)[:3, :3]
    out = []
    for j in range(3):
        col = a[:, j]
        i = int(np.argmax(np.abs(col)))
        out.append(("+" if col[i] >= 0 else "-") + "xyz"[i])
    return out


def _text(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode("latin-1")
    return str(value).strip("\x00 ")


def _dimensions(img) -> list[tuple[str, object]]:
    """(nombre, variable) de cada dimensión, en el orden del archivo.

    Usa atributos internos de nibabel (``_dim_names`` y ``_dims``). Si una versión futura no los
    expone, devuelve una lista vacía y las unidades y los pasos con signo quedan como desconocidos.
    """
    mf = getattr(img.dataobj, "minc_file", None)
    names = list(getattr(mf, "_dim_names", None) or [])
    dims = list(getattr(mf, "_dims", None) or [])
    if len(names) != len(dims):
        return []
    return list(zip(names, dims))


def load_minc(path) -> tuple[np.ndarray, tuple[float, float, float], dict]:
    """Imagen 3D (float32), vóxel en mm por eje del arreglo y metadatos de orientación."""
    path = Path(path)
    fmt = minc_format(path)
    nib = _nib()
    if fmt == "MINC2":
        try:
            import h5py  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise ImportError("MINC2 (HDF5) necesita h5py: pip install 'geovida[real]'") from exc
    img = nib.load(str(path))
    arr = np.asarray(img.get_fdata(dtype=np.float32))
    if arr.ndim != 3:
        raise ValueError(f"{path}: se esperaba un volumen 3D, forma {arr.shape}")
    affine = np.asarray(img.affine, dtype=float)
    zooms = tuple(float(z) for z in img.header.get_zooms()[:3])
    norms = np.linalg.norm(affine[:3, :3], axis=0)
    if not np.allclose(norms, zooms, rtol=1e-4, atol=0.0):
        raise ValueError(f"{path}: la afín ({norms.tolist()}) no coincide con los pasos "
                         f"({list(zooms)}); ¿cosenos directores sin normalizar?")
    spatial = [(n, d) for n, d in _dimensions(img) if n.endswith("space")]
    units = [_text(getattr(d, "units", None)) for _, d in spatial]
    bad = sorted({u for u in units if u and u.lower() not in _MM})
    if bad:
        raise ValueError(f"{path}: unidades espaciales {bad}; solo se admiten mm")
    meta = {
        "format": fmt,
        "unit": "mm",
        "unit_known": bool(units) and all(units),
        "units_declared": units,
        "dim_names": [n for n, _ in spatial],
        "steps": [float(getattr(d, "step", 1.0)) for _, d in spatial] if spatial else None,
        "dtype": str(img.get_data_dtype()),
        "zooms_raw": list(zooms),
        "affine": affine.tolist(),
        "world_axes": world_axes(affine),
    }
    return arr, zooms, meta
