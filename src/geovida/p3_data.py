"""Datos del piloto P3: qué archivos hacen falta y comprobaciones previas (``docs/PREREGISTRO_P3.md`` §3).

Qué hace
--------
* ``required_files``: nombres de archivo de MusMorph IMPC E15.5 que hay que descargar para unos especímenes
  (imagen ``<ID>.mnc`` y segmentación ``<ID>_Segs.mnc``, según el catálogo de FaceBase, registro 3-JZA6).
* ``index_folder``: localiza esos archivos dentro de una descarga (BDBag los deja en carpetas anidadas).
* ``precheck``: comprobaciones 3.1 (existencia ≥ 80 %) y 3.2 (las segmentaciones están en el espacio de
  cada espécimen: el volumen de cada etiqueta varía entre especímenes en ≥ 90 % de las etiquetas), más el
  vóxel, la orientación y las etiquetas presentes. Solo lee las segmentaciones, no las imágenes.
* ``recover_labels`` / ``load_labels``: etiquetas enteras a partir de las segmentaciones de MusMorph, que
  se remuestrearon con interpolación trilineal (desviación D1 del preregistro).

Qué NO hace
-----------
No descarga nada (de eso se encarga ``scripts/p3_pilot.py download``; FaceBase sirve estos archivos sin
autenticación) y no mira ningún resultado de las hipótesis: estas comprobaciones pueden detener el estudio
antes de medir nada.
"""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import ndimage

from .minc import load_minc
from .p3 import label_variation

IMAGE_SUFFIX = ".mnc"
SEG_SUFFIX = "_Segs.mnc"
MIN_EXISTENCE = 0.80
MIN_VARYING = 0.90
# Etiquetas con ≥ 490 vóxeles exactos en cada uno de los 20 especímenes del piloto (results/p3/diagnostico_segs.json);
# los demás enteros > 48 aparecen en 1 o 2 vóxeles: son coincidencias de la interpolación (desviación D1).
MUSMORPH_LABELS = tuple(range(1, 49)) + (102, 103)


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


RULES = ("nearest", "exact")
_K26 = np.ones((3, 3, 3), bool)


def recover_labels(arr: np.ndarray, allowed: Iterable[int] | None = None, rule: str = "nearest",
                   tol: float = 1e-3) -> tuple[np.ndarray, dict]:
    """Etiquetas enteras a partir de un mapa de etiquetas remuestreado con interpolación trilineal.

    MusMorph propagó el atlas con ``mincresample`` sin ``-nearest_neighbour`` (desviación D1 de
    ``docs/PREREGISTRO_P3.md``): en los bordes el valor es una mezcla de números de etiqueta, no una
    etiqueta. Un vóxel con valor entero (a ``tol``) de ``allowed`` (o > 0 si ``allowed`` es None) conserva
    esa etiqueta; el valor 0 es fondo. Para el resto:

    * ``rule="nearest"``: entre los candidatos del vecindario 26 (el fondo y las etiquetas enteras
      vecinas) se elige la de valor más cercano. Con dos candidatos equivale a quedarse con la que pesa
      ≥ 0,5 en la mezcla (el mismo umbral que §5.1); con tres o más es una aproximación y se cuenta.
    * ``rule="exact"``: el vóxel pasa a fondo (análisis de sensibilidad: erosiona cada borde).

    Devuelve (etiquetas int16, recuento) sin modificar ``arr``.
    """
    if rule not in RULES:
        raise ValueError(f"regla desconocida: {rule!r}; use {RULES}")
    a = np.asarray(arr)
    r = np.rint(a)
    exact = np.abs(a - r) < tol
    ok = exact & (r > 0)
    if allowed is not None:
        ok &= np.isin(r, np.asarray(sorted(set(int(x) for x in allowed))))
    background = exact & (r == 0) | (a <= tol)
    lab = np.zeros(a.shape, np.int16)
    lab[ok] = r[ok].astype(np.int16)
    mixed = ~(ok | background)
    info = {"n_labelled_exact": int(ok.sum()), "n_mixed": int(mixed.sum()),
            "n_mixed_ambiguous": 0, "n_mixed_orphan": 0, "rule": rule}
    total = info["n_labelled_exact"] + info["n_mixed"]
    info["frac_mixed"] = info["n_mixed"] / total if total else 0.0
    if rule == "exact" or not mixed.any():
        return lab, info
    coords = np.nonzero(mixed)
    vals = a[coords].astype(np.float64)
    best_l, best_d, n_cand = _nearest_candidate(vals, coords, lab, background, radius=1)
    orphan = np.isinf(best_d)
    info["n_mixed_radius2"] = int(orphan.sum())
    if orphan.any():  # sin vecino exacto a 1 vóxel (estructuras finas): se busca a 2 vóxeles
        sub = tuple(c[orphan] for c in coords)
        l2, d2, _ = _nearest_candidate(vals[orphan], sub, lab, background, radius=2)
        best_l[orphan], best_d[orphan] = l2, d2
    lab[coords] = best_l
    info["n_mixed_ambiguous"] = int((n_cand >= 3).sum())
    info["n_mixed_orphan"] = int(np.isinf(best_d).sum())
    return lab, info


def _nearest_candidate(vals, coords, lab, background, radius):
    """Para cada vóxel mezclado, la etiqueta exacta (o el fondo) a ≤ ``radius`` vóxeles de valor más cercano."""
    def grow(mask):  # cubo de lado 2·radius + 1 = radius dilataciones del cubo 3×3×3 (idéntico y ~3 veces más rápido)
        return ndimage.binary_dilation(mask, structure=_K26, iterations=radius)

    best_d = np.full(vals.size, np.inf)
    best_l = np.zeros(vals.size, np.int16)
    n_cand = np.zeros(vals.size, np.int16)
    hit = grow(background)[coords]
    n_cand += hit
    best_d[hit] = np.abs(vals[hit])
    for L, sl in enumerate(ndimage.find_objects(lab.astype(np.int32)), start=1):
        if sl is None:
            continue
        sl = tuple(slice(max(s.start - radius, 0), min(s.stop + radius, n)) for s, n in zip(sl, lab.shape))
        inside = np.ones(vals.size, bool)
        for ax, s in enumerate(sl):
            inside &= (coords[ax] >= s.start) & (coords[ax] < s.stop)
        if not inside.any():
            continue
        near = grow(lab[sl] == L)
        hit = np.zeros(vals.size, bool)
        hit[inside] = near[tuple(coords[ax][inside] - s.start for ax, s in enumerate(sl))]
        n_cand += hit
        d = np.where(hit, np.abs(vals - L), np.inf)
        upd = d < best_d
        best_d[upd], best_l[upd] = d[upd], L
    return best_l, best_d, n_cand


def _crop_box(arr: np.ndarray, tol: float = 1e-3) -> tuple[slice, ...]:
    """Caja mínima (con 1 vóxel de margen) que contiene los valores > tol."""
    m = arr > tol
    if not m.any():
        return tuple(slice(0, 0) for _ in arr.shape)
    out = []
    for ax in range(arr.ndim):
        hit = np.nonzero(m.any(axis=tuple(i for i in range(arr.ndim) if i != ax)))[0]
        out.append(slice(max(int(hit[0]) - 1, 0), min(int(hit[-1]) + 2, arr.shape[ax])))
    return tuple(out)


def load_labels(path, allowed: Iterable[int] | None = None, rule: str = "nearest"):
    """Lee una segmentación MINC, la recorta a su caja y recupera etiquetas enteras.

    Devuelve (etiquetas, caja dentro del volumen completo, espaciado, metadatos, recuento).
    """
    arr, spacing, meta = load_minc(path)
    box = _crop_box(arr)
    crop = np.array(arr[box], dtype=np.float32)
    del arr
    lab, info = recover_labels(crop, allowed=allowed, rule=rule)
    return lab, box, spacing, meta, info


def precheck(folder, ids: Iterable[str], allowed: Iterable[int] | None = None, rule: str = "nearest",
             log=None) -> dict:
    """Comprobaciones previas 3.1 y 3.2 sobre las segmentaciones descargadas (``log``: función de avance)."""
    ids = [str(i) for i in ids]
    idx = index_folder(folder)
    rows, per_specimen = [], []
    for i in ids:
        img, seg = idx.get(f"{i}{IMAGE_SUFFIX}"), idx.get(f"{i}{SEG_SUFFIX}")
        rec = {"specimen": i, "image": img is not None, "segmentation": seg is not None}
        if seg is not None:
            lab, _, spacing, meta, info = load_labels(seg, allowed=allowed, rule=rule)
            vox = float(np.prod(spacing))
            values, counts = np.unique(lab[lab > 0], return_counts=True)
            rec.update(spacing_mm=[round(s, 6) for s in spacing], world_axes=meta["world_axes"],
                       n_labels=int(values.size), label_recovery=info)
            if log:
                log(f"{i}: {values.size} etiquetas, {info['frac_mixed']:.1%} de vóxeles mezclados")
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
    mixed = [r["label_recovery"]["frac_mixed"] for r in per_specimen if "label_recovery" in r]
    return {
        "label_recovery_rule": rule,
        "frac_mixed_median": float(np.median(mixed)) if mixed else None,
        "n_requested": len(ids), "n_complete": len(complete),
        "existence_fraction": existence, "check_3_1_passed": bool(existence >= MIN_EXISTENCE),
        "label_variation": variation, "check_3_2_passed": bool(variation["passed"]),
        "spacings_mm": [list(s) for s in spacings], "labels_present": labels_all,
        "missing": [r["specimen"] for r in per_specimen if not (r["image"] and r["segmentation"])],
        "per_specimen": per_specimen, "volumes": vol,
    }
