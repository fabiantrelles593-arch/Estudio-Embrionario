"""Datos del piloto P3: qué archivos hacen falta y comprobaciones previas (``docs/PREREGISTRO_P3.md`` §3).

Qué hace
--------
* ``required_files``: nombres de archivo de MusMorph IMPC E15.5 que hay que descargar para unos especímenes
  (imagen ``<ID>.mnc`` y segmentación ``<ID>_Segs.mnc``, según el catálogo de FaceBase, registro 3-JZA6).
* ``index_folder``: localiza esos archivos dentro de una descarga (BDBag los deja en carpetas anidadas).
* ``precheck``: comprobaciones 3.1 (existencia ≥ 80 %) y 3.2 (las segmentaciones están en el espacio de
  cada espécimen: el volumen de cada etiqueta varía entre especímenes en ≥ 90 % de las etiquetas), más el
  vóxel, la orientación y las etiquetas presentes. Solo lee las segmentaciones, no las imágenes.

Qué NO hace
-----------
No descarga nada (la descarga la hace el autor con su cuenta de FaceBase) y no mira ningún resultado de
las hipótesis: estas comprobaciones pueden detener el estudio antes de medir nada.
"""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd

from .minc import load_minc
from .p3 import label_variation

IMAGE_SUFFIX = ".mnc"
SEG_SUFFIX = "_Segs.mnc"
MIN_EXISTENCE = 0.80
MIN_VARYING = 0.90


def required_files(ids: Iterable[str]) -> list[str]:
    """Imagen y segmentación de cada espécimen, en el orden dado."""
    out = []
    for i in ids:
        out += [f"{i}{IMAGE_SUFFIX}", f"{i}{SEG_SUFFIX}"]
    return out


def index_folder(folder) -> dict[str, Path]:
    """{nombre de archivo: ruta} de todos los .mnc bajo ``folder``. Un nombre repetido es un error."""
    idx: dict[str, Path] = {}
    for p in sorted(Path(folder).rglob("*.mnc")):
        if p.name in idx:
            raise ValueError(f"archivo repetido en la descarga: {p.name}")
        idx[p.name] = p
    return idx


def _labels(arr: np.ndarray) -> np.ndarray:
    lab = np.rint(arr)
    if not np.allclose(lab, arr, atol=1e-3):
        raise ValueError("la segmentación no contiene etiquetas enteras")
    return lab.astype(np.int32)


def precheck(folder, ids: Iterable[str]) -> dict:
    """Comprobaciones previas 3.1 y 3.2 sobre las segmentaciones descargadas."""
    ids = [str(i) for i in ids]
    idx = index_folder(folder)
    rows, per_specimen = [], []
    for i in ids:
        img, seg = idx.get(f"{i}{IMAGE_SUFFIX}"), idx.get(f"{i}{SEG_SUFFIX}")
        rec = {"specimen": i, "image": img is not None, "segmentation": seg is not None}
        if seg is not None:
            arr, spacing, meta = load_minc(seg)
            lab = _labels(arr)
            vox = float(np.prod(spacing))
            values, counts = np.unique(lab[lab > 0], return_counts=True)
            rec.update(spacing_mm=[round(s, 6) for s in spacing], world_axes=meta["world_axes"],
                       n_labels=int(values.size))
            rows += [{"specimen": i, "structure": int(v), "segmenter": "A", "factor": 1,
                      "volume": float(c) * vox} for v, c in zip(values, counts)]
        per_specimen.append(rec)
    complete = [r for r in per_specimen if r["image"] and r["segmentation"]]
    existence = len(complete) / len(ids) if ids else 0.0
    vol = pd.DataFrame(rows, columns=["specimen", "structure", "segmenter", "factor", "volume"])
    variation = label_variation(vol, "A", MIN_VARYING) if len(vol) else \
        {"fraction_varying": 0.0, "passed": False, "n_structures": 0}
    spacings = sorted({tuple(r["spacing_mm"]) for r in per_specimen if "spacing_mm" in r})
    labels_all = sorted(vol["structure"].unique().tolist()) if len(vol) else []
    return {
        "n_requested": len(ids), "n_complete": len(complete),
        "existence_fraction": existence, "check_3_1_passed": bool(existence >= MIN_EXISTENCE),
        "label_variation": variation, "check_3_2_passed": bool(variation["passed"]),
        "spacings_mm": [list(s) for s in spacings], "labels_present": labels_all,
        "missing": [r["specimen"] for r in per_specimen if not (r["image"] and r["segmentation"])],
        "per_specimen": per_specimen, "volumes": vol,
    }
