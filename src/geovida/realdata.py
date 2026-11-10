"""Lector y comparador para imágenes reales (v0.5).

Qué hace
--------
* ``load_volume``: lee un volumen NIfTI (.nii o .nii.gz) y devuelve la imagen, el tamaño del
  vóxel en milímetros y los metadatos de unidades.
* ``datasheet``: resumen descriptivo de un volumen (forma, vóxel, intensidades, etiquetas). **No
  calcula nada contra una referencia**: sirve para leer la estructura de un conjunto antes de fijar
  los criterios.
* ``scan``: recorre una carpeta o un .zip con volúmenes NIfTI y devuelve su ficha, sin suponer qué
  archivo es imagen y cuál es etiqueta.
* ``compare_case``: aplica el certificado congelado de v0.4 (sin reajustar nada) a una imagen real y
  compara la medida con la referencia dibujada por una persona experta.

Qué NO es
---------
La referencia de una imagen real es un contorno humano, no una verdad exacta: lo que se mide es
**acuerdo con esa referencia**, que tiene su propia variabilidad. Los modelos del certificado se
calibraron con imágenes sintéticas; usarlos aquí es justamente la prueba de si transfieren. Solo
investigación y educación; sin uso clínico. Con imágenes humanas, ver docs/DATOS_REALES_Y_ETICA.md.
"""
from __future__ import annotations

import math
import tempfile
import zipfile
from pathlib import Path

import numpy as np

from .budget import traffic_light
from .certificate import certify
from .measure import dice, measure_mask
from .segment import segment

NII_SUFFIXES = (".nii", ".nii.gz")
_UNIT_TO_MM = {"meter": 1000.0, "mm": 1.0, "micron": 1e-3}
MAX_LABELS = 32


def _nib():
    try:
        import nibabel
    except ImportError as exc:  # pragma: no cover
        raise ImportError("para leer NIfTI instala nibabel: pip install 'geovida[real]'") from exc
    return nibabel


def load_volume(path) -> tuple[np.ndarray, tuple[float, float, float], dict]:
    """Imagen 3D (float32), vóxel en mm y metadatos. Descarta dimensiones de tamaño 1."""
    nib = _nib()
    im = nib.load(str(path))
    arr = np.squeeze(np.asarray(im.get_fdata(dtype=np.float32)))
    if arr.ndim != 3:
        raise ValueError(f"{path}: se esperaba un volumen 3D, forma {arr.shape}")
    zooms = tuple(float(z) for z in im.header.get_zooms()[:3])
    unit = im.header.get_xyzt_units()[0]
    factor = _UNIT_TO_MM.get(unit, 1.0)
    meta = {"unit": unit, "unit_known": unit in _UNIT_TO_MM, "dtype": str(im.get_data_dtype()),
            "zooms_raw": list(zooms)}
    return arr, tuple(z * factor for z in zooms), meta


def datasheet(arr: np.ndarray, spacing, name: str = "") -> dict:
    """Ficha descriptiva de un volumen. No compara con ninguna referencia."""
    a = np.asarray(arr)
    sp = tuple(float(s) for s in spacing)
    vox_mm3 = float(np.prod(sp))
    out = {"name": name, "shape": list(a.shape), "spacing_mm": list(sp),
           "voxel_mm3": vox_mm3, "extent_mm": [float(n * s) for n, s in zip(a.shape, sp)]}
    finite = a[np.isfinite(a)]
    integral = bool(finite.size and np.all(finite == np.round(finite)))
    uniq = np.unique(finite) if integral else np.array([])
    label_like = bool(integral and uniq.size <= MAX_LABELS)
    out["label_like"] = label_like
    if label_like:
        counts = {str(int(v)): int((a == v).sum()) for v in uniq}
        out["labels"] = counts
        out["labels_volume_mm3"] = {k: c * vox_mm3 for k, c in counts.items()}
    else:
        for q in (1, 25, 50, 75, 99):
            out[f"p{q}"] = float(np.percentile(finite, q)) if finite.size else math.nan
        out["mean"] = float(finite.mean()) if finite.size else math.nan
        out["std"] = float(finite.std()) if finite.size else math.nan
    out["nan_fraction"] = float(1 - finite.size / a.size) if a.size else 0.0
    return out


def _iter_nii(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name.lower().endswith(NII_SUFFIXES):
            yield p


def scan(source) -> list[dict]:
    """Ficha de cada volumen NIfTI de una carpeta o un .zip. Sin suponer pares imagen-etiqueta."""
    source = Path(source)
    rows: list[dict] = []

    def one(path: Path, shown: str):
        try:
            arr, sp, meta = load_volume(path)
            rows.append({**datasheet(arr, sp, Path(shown).name), "path": shown, **meta})
        except Exception as exc:  # un archivo ilegible no detiene el recorrido
            rows.append({"name": Path(shown).name, "path": shown, "error": f"{type(exc).__name__}: {exc}"})

    if source.is_dir():
        for p in _iter_nii(source):
            one(p, str(p.relative_to(source)))
    elif zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as z, tempfile.TemporaryDirectory() as tmp:
            for info in z.infolist():
                if info.is_dir() or not info.filename.lower().endswith(NII_SUFFIXES):
                    continue
                target = z.extract(info, tmp)
                one(Path(target), info.filename)
                Path(target).unlink()
    elif source.name.lower().endswith(NII_SUFFIXES):
        one(source, source.name)
    else:
        raise ValueError(f"{source}: ni carpeta, ni .zip, ni NIfTI")
    return rows


def crop_to_reference(image: np.ndarray, ref_mask: np.ndarray, margin: float = 0.25):
    """Recorta imagen y referencia a la caja de la referencia, dilatada ``margin`` por lado.

    Sirve para estructuras que un umbral de toda la imagen no puede aislar (p. ej. un ventrículo).
    **Usa la referencia para elegir dónde medir y favorece al método**: debe declararse siempre.
    """
    ref = np.asarray(ref_mask).astype(bool)
    idx = np.nonzero(ref)
    lo, hi = [], []
    for ax, ii in enumerate(idx):
        a0, a1 = int(ii.min()), int(ii.max()) + 1
        pad = int(math.ceil(margin * (a1 - a0)))
        lo.append(max(0, a0 - pad))
        hi.append(min(ref.shape[ax], a1 + pad))
    sl = tuple(slice(l, h) for l, h in zip(lo, hi))
    return np.asarray(image)[sl], ref[sl]


def compare_case(image: np.ndarray, spacing, ref_mask: np.ndarray, segmenter: str,
                 profile: str = "realistic", frozen: dict | None = None,
                 tolerances=(0.05, 0.10), roi_margin: float | None = None) -> dict:
    """Certifica una imagen real con los modelos congelados y compara con la referencia experta.

    No reajusta nada. ``ok5`` y ``ok10``: el volumen medido está dentro de 5 % y de 10 % del
    volumen de la referencia. Con ``roi_margin`` (p. ej. 0.25) se mide dentro de una caja alrededor
    de la referencia; eso favorece al método y queda registrado en ``roi_margin``.
    """
    image = np.asarray(image, dtype=np.float32)
    ref = np.asarray(ref_mask).astype(bool)
    if ref.shape != image.shape:
        raise ValueError(f"imagen {image.shape} y referencia {ref.shape} no coinciden")
    if not ref.any():
        raise ValueError("la referencia está vacía")
    if roi_margin is not None:
        image, ref = crop_to_reference(image, ref, roi_margin)
    sp = tuple(float(s) for s in spacing)
    cert = certify(image, sp, segmenter, profile, frozen)
    mask = segment(segmenter, image, sp)
    ref_meas = measure_mask(ref, sp)
    v_ref = float(ref_meas["volume"])
    v_meas = float(cert["volume"]["value"])
    rel = (v_meas - v_ref) / v_ref
    betti_ref = [int(ref_meas["b0_26"]), int(ref_meas["b1_26"]), int(ref_meas["b2_26"])]
    betti_meas = [int(b) for b in cert["topology"]["betti"]]
    obs = cert.get("observables", {})
    p_v = float(cert["volume"].get("p", 0.0))
    return {
        "segmenter": segmenter, "profile": profile, "shape": list(image.shape), "spacing_mm": list(sp),
        "roi_margin": roi_margin,
        "volume_mm3_measured": v_meas, "volume_mm3_reference": v_ref, "rel_error_volume": rel,
        "ok5": bool(abs(rel) <= tolerances[0]), "ok10": bool(abs(rel) <= tolerances[1]),
        "dice": float(dice(mask, ref)),
        "betti_measured": betti_meas, "betti_reference": betti_ref,
        "betti_ref": betti_ref, "topology_ok": betti_meas == betti_ref,
        "p_volume": p_v, "light_volume": cert["volume"]["light"],
        "light_volume_without_guard": traffic_light(p_v) if mask.any() else "rojo",
        "in_domain_volume": bool(cert["volume"].get("in_domain", False)),
        "p_topology": float(cert["topology"].get("p", 0.0)), "light_topology": cert["topology"]["light"],
        "in_domain_topology": bool(cert["topology"].get("in_domain", False)),
        "snr_hat": obs.get("snr_hat"), "edge_width": obs.get("edge_width"),
        "d_over_hgeo": obs.get("d_over_hgeo"),
    }
