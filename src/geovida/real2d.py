"""Rama de imagen 2D real: medir una longitud sobre una ecografía fotografiada o exportada.

Solo investigación y educación; **no es una herramienta clínica**. La calibración del certificado
viene solo de simulación (``docs/RESULTADOS_V06.md``), así que sobre una imagen real el semáforo **nunca
sale verde**: se conserva el que daría la simulación, rotulado como tal (``light_if_simulation_held``).

Lo que hace:

* **Escala** a partir de la regla impresa en la ecografía (dos puntos y su longitud, o marcas
  igualmente espaciadas) o declarada (mm por píxel).
* **Medida** de la longitud máxima (Feret) del objeto dentro de una región de interés (ROI) que da la persona,
  con el mismo segmentador (``smoothed_otsu``) y la misma medida que la calibración.
* **Desenfoque desconocido.** La foto no dice cuál es la función de dispersión (PSF). Un estimador por
  perfil de borde se probó y se descartó (subestimaba 28–47 % con PSF ≥ 3.5 px; ``docs/REAL2D_METODO.md``).
  En su lugar se calcula el certificado **para cada desenfoque posible en milímetros**, remuestreando la
  imagen a una escala de trabajo que cae dentro de la caja calibrada (n entre 50 y 300 px, PSF entre 1 y 5 px).
* **Privacidad.** Los metadatos (EXIF, GPS, nombres) se descartan al cargar; los informes llevan
  solo el SHA-256 del archivo y nunca su nombre ni su ruta.

Limitaciones declaradas (no verificadas): moteado y PSF reales frente al simulador; compresión
logarítmica y ganancia del equipo; impresión, fotografía y JPEG; el objeto lo delimita la ROI que se da.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage as ndi

from . import biometry as bio
from . import dating
from .twod import segment2d

SEGMENTER = "smoothed_otsu"
DEFAULT_BLUR_MM_GRID = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0)
FALLBACK_BOX = {"n": (50.0, 300.0), "f": (1.0, 5.0)}
ASSUMPTIONS = (
    "El error de la medida se calibró solo con fantomas simulados (cápsula 2D, moteado y PSF gaussiana).",
    "El desenfoque real no se conoce: se informa para cada valor de la rejilla, no para uno estimado.",
    "No se modelan la compresión logarítmica, la ganancia, la impresión, la fotografía ni el JPEG.",
    "La región de interés la elige una persona; si incluye otras estructuras brillantes, la medida es de otra cosa.",
    "El tamaño de trabajo (n) sale de la propia medida nativa: la circularidad que H14 dejó abierta sigue ahí.",
)


# --- escala -----------------------------------------------------------------------------------

@dataclass(frozen=True)
class Scale:
    mm_per_px: float
    source: str            # "regla" | "marcas" | "declarada"
    spread_rel: float = 0.0  # dispersión relativa de la regla (0 si es declarada)


def scale_from_ruler(p1, p2, length_mm: float) -> Scale:
    if not (length_mm > 0):
        raise ValueError("la longitud de la regla debe ser > 0 mm")
    d = math.dist(p1, p2)
    if d <= 0:
        raise ValueError("los dos puntos de la regla coinciden")
    return Scale(mm_per_px=float(length_mm) / d, source="regla", spread_rel=0.0)


def scale_from_ticks(tick_px, spacing_mm: float) -> Scale:
    """Escala a partir de marcas igualmente espaciadas (posiciones en píxeles a lo largo de la regla)."""
    t = np.sort(np.asarray(tick_px, dtype=float))
    if t.size < 3:
        raise ValueError("hacen falta al menos 3 marcas para estimar la escala y su dispersión")
    if not (spacing_mm > 0):
        raise ValueError("el espaciado entre marcas debe ser > 0 mm")
    gaps = np.diff(t)
    med = float(np.median(gaps))
    if med <= 0:
        raise ValueError("marcas repetidas")
    return Scale(mm_per_px=float(spacing_mm) / med, source="marcas",
                 spread_rel=float((gaps.max() - gaps.min()) / med))


def caliper_mm(p1, p2, scale: Scale) -> float:
    """Distancia entre dos puntos marcados a mano, en mm."""
    return math.dist(p1, p2) * scale.mm_per_px


# --- carga (sin metadatos) --------------------------------------------------------------------

@dataclass(frozen=True, repr=False)
class LoadedImage:
    gray: np.ndarray
    sha256: str

    def __repr__(self) -> str:        # nunca la ruta, el nombre ni los metadatos
        return f"LoadedImage(shape={self.gray.shape}, sha256={self.sha256[:12]}…)"


def load_gray(path) -> LoadedImage:
    """Carga una imagen en escala de grises [0, 1]. Aplica la orientación y descarta todo metadato."""
    raw = Path(path).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    with Image.open(Path(path)) as im:
        im = ImageOps.exif_transpose(im)
        g = np.asarray(im.convert("L"), dtype=np.float64) / 255.0
    return LoadedImage(gray=g, sha256=sha)


# --- geometría de trabajo ---------------------------------------------------------------------

def working_geometry(length_mm: float, blur_mm: float, n_range=None, f_range=None):
    """Tamaño ``n`` (px), PSF ``f_px`` y píxel ``h_mm`` de trabajo para que la imagen caiga en la caja.

    Remuestrear multiplica por el mismo factor el tamaño y la PSF, así que lo que se conserva es el
    cociente ``r = blur/longitud``; hay solución solo si existe ``n`` con ``n·r`` y ``n`` dentro de la caja.
    """
    n_lo, n_hi = n_range or FALLBACK_BOX["n"]
    f_lo, f_hi = f_range or FALLBACK_BOX["f"]
    if not (length_mm > 0 and blur_mm > 0):
        return None
    r = blur_mm / length_mm
    lo, hi = max(n_lo, f_lo / r), min(n_hi, f_hi / r)
    if lo > hi:
        return None
    n = math.sqrt(lo * hi)
    return n, r * n, length_mm / n


def _box_of(model):
    if model is None:
        return FALLBACK_BOX["n"], FALLBACK_BOX["f"]
    return (float(model.n_nodes[0]), float(model.n_nodes[-1])), (float(model.f_nodes[0]), float(model.f_nodes[-1]))


# --- medida -----------------------------------------------------------------------------------

def _resize(img: np.ndarray, s: float) -> np.ndarray:
    interp = cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR
    return cv2.resize(img, dsize=None, fx=s, fy=s, interpolation=interp)


def _qc(crop: np.ndarray, mask: np.ndarray) -> dict:
    lab, n = ndi.label(mask, structure=np.ones((3, 3)))
    sizes = np.bincount(lab.ravel())[1:] if n else np.array([0])
    big = int(sizes.max()) if n else 0
    main = bio.largest_component(mask)
    ys, xs = np.nonzero(main)
    touches = bool(main.any() and (xs.min() == 0 or ys.min() == 0 or xs.max() == mask.shape[1] - 1
                                   or ys.max() == mask.shape[0] - 1))
    ring = ndi.binary_dilation(main, iterations=6) & ~ndi.binary_dilation(main, iterations=2)
    inside = ndi.binary_erosion(main, iterations=2)
    inside = inside if inside.any() else main
    mu_in = float(crop[inside].mean()) if inside.any() else float("nan")
    mu_out = float(crop[ring].mean()) if ring.any() else float("nan")
    sd_out = float(crop[ring].std()) if ring.any() else float("nan")
    return {"touches_roi_border": touches,
            "area_fraction": float(main.mean()),
            "n_components_ge_5pct_of_largest": int((sizes >= 0.05 * big).sum()) if big else 0,
            "contrast_inside_minus_outside": mu_in - mu_out,
            "contrast_to_noise": (mu_in - mu_out) / sd_out if sd_out and sd_out > 0 else float("nan")}


def _jsonable(x):
    if isinstance(x, dict):
        return {k: _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    return x


def measure_roi(gray: np.ndarray, roi, scale: Scale, models: dict, *, segmenter: str = SEGMENTER,
                bright: bool = True, blur_mm_grid=DEFAULT_BLUR_MM_GRID) -> dict:
    """Mide la longitud del objeto dentro de ``roi = (x0, y0, x1, y1)`` y certifica por desenfoque en mm."""
    x0, y0, x1, y1 = (int(v) for v in roi)
    if not (0 <= x0 < x1 <= gray.shape[1] and 0 <= y0 < y1 <= gray.shape[0]):
        raise ValueError("la ROI debe estar dentro de la imagen: (x0, y0, x1, y1) con x0<x1, y0<y1")
    crop = np.asarray(gray[y0:y1, x0:x1], dtype=np.float64)
    if not bright:
        crop = crop.max() - crop
    model = models.get(f"body|{segmenter}")
    n_rng, f_rng = _box_of(model)

    mask0 = segment2d(segmenter, crop, scale.mm_per_px)
    length0 = bio.feret_length_mm(mask0, scale.mm_per_px)
    native = {"length_mm": float(length0), "n_px": float(length0 / scale.mm_per_px), "mask": mask0}
    qc = _qc(crop, mask0)

    rows = []
    for blur_mm in blur_mm_grid:
        geo = working_geometry(length0, blur_mm, n_rng, f_rng)
        if geo is None:
            rows.append({"blur_mm": float(blur_mm), "in_box": False, "light": "amarillo", "in_domain": False,
                         "reason": ("razón desenfoque/tamaño fuera de la caja calibrada "
                                    f"(desenfoque {blur_mm:g} mm sobre {length0:.1f} mm)"),
                         "measured_mm": None, "n_px": None, "fwhm_px": None, "h_mm": None,
                         "light_if_simulation_held": None})
            continue
        n_target, _, _ = geo
        s = n_target * scale.mm_per_px / length0
        work = _resize(crop, s)
        h_work = scale.mm_per_px / s
        mask = segment2d(segmenter, work, h_work)
        measured = bio.feret_length_mm(mask, h_work)
        f_px = blur_mm / h_work
        row = {"blur_mm": float(blur_mm), "in_box": True, "measured_mm": float(measured),
               "n_px": float(measured / h_work) if h_work > 0 else None, "fwhm_px": float(f_px),
               "h_mm": float(h_work), "work_scale": float(s)}
        if model is None:
            cert = {"light": "amarillo", "in_domain": False, "reason": f"no hay modelo para body|{segmenter}"}
        else:
            cert = bio.certify_body(measured, h_work, f_px, model)
        sim_light = cert.get("light")
        if cert.get("in_domain") and cert.get("bias_px") is not None:
            row["bias_corrected_mm"] = float(measured - cert["bias_px"] * h_work)   # mejor estimación puntual
        capped = sim_light == "verde"
        row.update(in_domain=bool(cert.get("in_domain", False)),
                   light="amarillo" if capped else sim_light,
                   light_if_simulation_held=sim_light,
                   reason=("calibración solo con simulación; sin validación en imagen real"
                           if capped else cert.get("reason", "")),
                   simulation_certificate={k: v for k, v in cert.items() if k not in ("light", "reason")})
        rows.append(row)

    ok = [r["measured_mm"] for r in rows if r.get("in_box") and r["measured_mm"]]
    crl = float(np.median(ok)) if ok else float(length0)
    dating_block = {"crl_mm_used": crl, "in_formula_range": dating.in_formula_range(crl)}
    if crl > 0:
        ga, sd = dating.ga_days_intergrowth(crl), dating.sd_ga_days_intergrowth(crl)
        dating_block.update(ga_days_intergrowth=ga, sd_ga_days=sd, ga_weeks_days=dating.weeks_days(ga),
                            ga_days_robinson=dating.ga_days_robinson(crl),
                            note=("fórmula publicada y dispersión biológica; no incluye el error de medida "
                                  "ni valida la imagen"))
    return {"scale": {"mm_per_px": scale.mm_per_px, "source": scale.source, "spread_rel": scale.spread_rel},
            "roi": [x0, y0, x1, y1], "segmenter": segmenter, "bright_object": bool(bright),
            "native": native, "qc": qc, "rows": rows, "dating_formula": dating_block,
            "validated_on_real": False, "assumptions": list(ASSUMPTIONS)}


def compare_printed(measured_mm: float, printed_mm: float) -> dict:
    """Diferencia con la medida impresa por el equipo o por un operador. Descriptiva: con n = 1 no hay regla de éxito."""
    d = float(measured_mm) - float(printed_mm)
    return {"measured_mm": float(measured_mm), "printed_mm": float(printed_mm), "diff_mm": d,
            "diff_pct": 100.0 * d / float(printed_mm)}


# --- salida -----------------------------------------------------------------------------------

def save_overlay(gray: np.ndarray, roi, mask: np.ndarray, out) -> None:
    """Superposición local (contorno rojo del objeto, rectángulo amarillo de la ROI) para revisar a ojo."""
    x0, y0, x1, y1 = (int(v) for v in roi)
    rgb = cv2.cvtColor((np.clip(gray, 0, 1) * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    m = bio.largest_component(mask).astype(np.uint8)
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    thick = max(1, int(round(max(gray.shape) / 400)))
    cv2.drawContours(rgb[y0:y1, x0:x1], cnts, -1, (0, 0, 255), thick)
    cv2.rectangle(rgb, (x0, y0), (x1 - 1, y1 - 1), (0, 255, 255), thick)
    if not cv2.imwrite(str(out), rgb):
        raise OSError("no se pudo escribir la superposición")


def report_dict(res: dict, *, sha256: str, image_shape, authorization_note: str | None = None,
                printed: dict | None = None, caliper: dict | None = None, version: str | None = None) -> dict:
    native = {k: v for k, v in res["native"].items() if k != "mask"}
    return _jsonable({"version": version, "image": {"sha256": sha256, "shape": list(image_shape)},
                      "authorization_note": authorization_note, "scale": res["scale"], "roi": res["roi"],
                      "segmenter": res["segmenter"], "native": native, "qc": res["qc"], "rows": res["rows"],
                      "dating_formula": res["dating_formula"], "printed_comparison": printed,
                      "caliper_manual": caliper, "validated_on_real": res["validated_on_real"],
                      "assumptions": res["assumptions"]})


def report_markdown(res: dict, *, sha256: str, image_shape, authorization_note: str | None = None,
                    printed: dict | None = None, caliper: dict | None = None, version: str | None = None) -> str:
    d = report_dict(res, sha256=sha256, image_shape=image_shape, authorization_note=authorization_note,
                    printed=printed, caliper=caliper, version=version)
    L = ["# Medida sobre imagen 2D real — informe (solo investigación y educación)", "",
         "> No es un resultado clínico. La calibración viene solo de simulación; sobre imagen real el semáforo no sale verde.",
         "", f"* Imagen: SHA-256 `{sha256}`, {image_shape[1]}×{image_shape[0]} px (no se guarda nombre, ruta ni metadatos).",
         f"* Autorización: {authorization_note or 'no aplica (no se declaró imagen humana)'}",
         f"* Escala: {d['scale']['mm_per_px']:.5f} mm/px (fuente: {d['scale']['source']}; dispersión de la regla {100*d['scale']['spread_rel']:.1f} %)",
         f"* ROI: {d['roi']}; segmentador: `{d['segmenter']}`",
         f"* Medida nativa (Feret): {d['native']['length_mm']:.2f} mm ({d['native']['n_px']:.0f} px)", ""]
    q = d["qc"]
    L += ["## Control de calidad", "",
          f"* El objeto toca el borde de la ROI: **{'SÍ (recortado: la medida no vale)' if q['touches_roi_border'] else 'no'}**",
          f"* Fracción de la ROI ocupada: {100*q['area_fraction']:.1f} %; componentes grandes: {q['n_components_ge_5pct_of_largest']}",
          f"* Contraste dentro−fuera: {q['contrast_inside_minus_outside']:.3f}; contraste/ruido: {q['contrast_to_noise']:.1f}", ""]
    L += ["## Medida y semáforo por desenfoque (en mm)", "",
          "| Desenfoque (mm) | En la caja | Medida (mm) | Corregida por sesgo (mm) | n (px) | PSF (px) | Semáforo | Si la simulación valiera | Motivo |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in d["rows"]:
        f = lambda v, p=2: "—" if v is None else f"{v:.{p}f}"
        L.append(f"| {r['blur_mm']:g} | {'sí' if r['in_box'] else 'no'} | {f(r['measured_mm'])} | {f(r.get('bias_corrected_mm'))} | {f(r['n_px'], 0)} | "
                 f"{f(r['fwhm_px'], 1)} | {r['light']} | {r.get('light_if_simulation_held') or '—'} | {r.get('reason', '')} |")
    dt = d["dating_formula"]
    L += ["", "## Edad por la fórmula (informativa, no certificada)", ""]
    if "ga_days_intergrowth" in dt:
        w, dd = dt["ga_weeks_days"]
        L += [f"* CRL usada: {dt['crl_mm_used']:.1f} mm; INTERGROWTH-21st: {dt['ga_days_intergrowth']:.1f} d ({w}+{dd}), "
              f"dispersión biológica ±{dt['sd_ga_days']:.1f} d; dentro del rango de la fórmula (15–95 mm): "
              f"**{'sí' if dt['in_formula_range'] else 'no'}**; Robinson: {dt['ga_days_robinson']:.1f} d.", f"* {dt['note']}."]
    else:
        L += ["* No hay una longitud positiva para fechar."]
    if printed:
        L += ["", "## Comparación con la medida impresa (descriptiva, n = 1, sin regla de éxito)", "",
              f"* Impresa: {printed['printed_mm']:.2f} mm; medida aquí: {printed['measured_mm']:.2f} mm; "
              f"diferencia {printed['diff_mm']:+.2f} mm ({printed['diff_pct']:+.1f} %)."]
    if caliper:
        L += ["", "## Calibrador manual sobre la imagen", "", f"* {caliper['length_mm']:.2f} mm (dos puntos marcados a mano)."]
    L += ["", "## Supuestos no verificados", ""] + [f"* {a}" for a in d["assumptions"]]
    if version:
        L += ["", f"_geovida {version}_"]
    return "\n".join(L) + "\n"
