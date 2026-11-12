"""Biometría fetal temprana simulada (Programa B, H13).

Solo investigación y educación. No procesa imágenes de personas y no es una herramienta clínica.

Dos fantomas 2D con verdad exacta que imitan dos medidas de la ecografía del primer trimestre:

* ``body``: una cápsula (estadio) de largo ``L`` y ancho ``L/2``. Imita la longitud cráneo-rabadilla
  (CRL). Verdad = ``L``. Medida = diámetro máximo de Feret de la máscara.
* ``slot``: un bloque claro con una ranura oscura de grosor ``T`` y largo ``4T`` rodeada de tejido.
  Imita la translucencia nucal (NT). Verdad = ``T``. Medida = ``2·max(EDT) − 1`` píxeles del hueco
  mayor de la máscara (el diámetro del mayor círculo inscrito).

El **error de medida** (medido − verdad, en píxeles) se calibra en una cuadrícula de dos variables:
``n`` (píxeles a lo largo de la magnitud medida) y ``fwhm_px`` (ancho de la función de dispersión
del punto, en píxeles). El modelo de error interpola sesgo y desviación **linealmente en
(ln n, ln fwhm_px)** y se niega (``None``) fuera de la caja calibrada. Con ese modelo los
certificados de ``geovida.dating`` convierten el error de medida en una probabilidad sobre algo que
importa: el error de edad en días, o si el valor verdadero está del mismo lado de un umbral.

Supuestos que NO están validados con ecografías reales (se declaran en ``docs/PREREGISTRO_H13.md``):
el moteado (``LOOKS`` miradas, grano ``max(2, fwhm)`` píxeles), la relación entre el ancho de la
función de dispersión y el tamaño del píxel, y la forma de la ranura.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from scipy.interpolate import RegularGridInterpolator
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist

from . import dating
from .twod import Phantom2D, Spec2D, Truth2D, render2d, segment2d

BODY, SLOT = "body", "slot"
KINDS = (BODY, SLOT)
SEGMENTERS = ("smoothed_otsu", "otsu")
LOOKS = 3                       # miradas de moteado promediadas (como el perfil us_raw de H12)
MIN_GRAIN_PX = 2.0
SLOT_THRESHOLD_MM = 3.0         # umbral ILUSTRATIVO del certificado de decisión; no es un criterio clínico

_CROSS = ndi.generate_binary_structure(2, 1)
_FULL = ndi.generate_binary_structure(2, 2)
_CORNERS = np.array([[0, 0], [1, 0], [0, 1], [1, 1]])


# --- fantomas ---------------------------------------------------------------------------------

def _stadium_dist2(p: np.ndarray, half_len: float) -> np.ndarray:
    """Distancia al cuadrado al segmento horizontal [−half_len, half_len] × {0}."""
    dx = np.maximum(np.abs(p[..., 0]) - half_len, 0.0)
    return dx * dx + p[..., 1] ** 2


def make_body(length_mm: float) -> Phantom2D:
    """Cápsula de largo ``length_mm`` y ancho ``length_mm / 2``; ``t`` es el largo (la verdad)."""
    if not length_mm > 0:
        raise ValueError("el largo debe ser > 0")
    r = length_mm / 4.0
    a = length_mm / 4.0
    area = 2 * a * 2 * r + math.pi * r * r
    per = 4 * a + 2 * math.pi * r
    truth = Truth2D(area, per, per, (1, 0), 1, 2 * r, math.inf)
    return Phantom2D(BODY, float(length_mm), truth, (length_mm / 2.0, r),
                     lambda p: _stadium_dist2(p, a) <= r * r)


def make_slot(thickness_mm: float) -> Phantom2D:
    """Bloque claro de 7T × 5T con una ranura oscura (estadio de radio T/2, largo total 4T)."""
    if not thickness_mm > 0:
        raise ValueError("el grosor debe ser > 0")
    t = float(thickness_mm)
    r, a = t / 2.0, 1.5 * t
    hx, hy = 3.5 * t, 2.5 * t
    gap_area = 2 * a * 2 * r + math.pi * r * r
    outer = 2 * (2 * hx + 2 * hy)
    truth = Truth2D(4 * hx * hy - gap_area, outer + 4 * a + 2 * math.pi * r, outer, (1, 1), 0, 2 * t, t)

    def inside(p):
        block = (np.abs(p[..., 0]) <= hx) & (np.abs(p[..., 1]) <= hy)
        return block & ~(_stadium_dist2(p, a) <= r * r)

    return Phantom2D(SLOT, t, truth, (hx, hy), inside)


# --- medidas ----------------------------------------------------------------------------------

def largest_component(mask: np.ndarray) -> np.ndarray:
    m = np.asarray(mask, dtype=bool)
    lab, n = ndi.label(m, structure=_FULL)
    if n <= 1:
        return m
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    return lab == int(sizes.argmax())


def feret_length_mm(mask: np.ndarray, h_mm: float) -> float:
    """Diámetro máximo de Feret del mayor componente, medido entre esquinas de píxel (0 si está vacío)."""
    m = largest_component(mask)
    if not m.any():
        return 0.0
    edge = m & ~ndi.binary_erosion(m, structure=_CROSS, border_value=0)
    ys, xs = np.nonzero(edge)
    pts = np.unique((np.stack([xs, ys], axis=1)[:, None, :] + _CORNERS[None]).reshape(-1, 2), axis=0)
    verts = pts[ConvexHull(pts).vertices]
    return float(pdist(verts).max()) * h_mm


def gap_thickness_mm(mask: np.ndarray, h_mm: float) -> float:
    """Grosor del hueco interior mayor del mayor componente: ``2·max(EDT) − 1`` píxeles (0 si no hay hueco).

    Un hueco que toca el borde de la imagen o se abre al exterior no cuenta como hueco.
    """
    m = largest_component(mask)
    hole = ndi.binary_fill_holes(m) & ~m
    lab, n = ndi.label(hole, structure=_CROSS)
    if n == 0:
        return 0.0
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    region = np.pad(lab == int(sizes.argmax()), 1)
    edt = ndi.distance_transform_edt(region)
    return float(2.0 * edt.max() - 1.0) * h_mm


def measure(kind: str, mask: np.ndarray, h_mm: float) -> float:
    if kind == BODY:
        return feret_length_mm(mask, h_mm)
    if kind == SLOT:
        return gap_thickness_mm(mask, h_mm)
    raise ValueError(f"tipo desconocido: {kind!r}; opciones: {KINDS}")


# --- simulación de un caso --------------------------------------------------------------------

def spec_for(h_mm: float, fwhm_px: float, looks: int = LOOKS) -> Spec2D:
    return Spec2D(h_mm, fwhm_px=fwhm_px, looks=looks, grain_fwhm_px=max(MIN_GRAIN_PX, fwhm_px))


def run_case(kind: str, size_mm: float, n: float, fwhm_px: float, seed, looks: int = LOOKS) -> dict:
    """Simula una imagen y mide con cada segmentador.

    ``n`` son los píxeles a lo largo de la magnitud verdadera (``size_mm``), de modo que el píxel
    mide ``h = size_mm / n``. ``seed`` puede ser un entero o una ``SeedSequence``.
    """
    if kind not in KINDS:
        raise ValueError(f"tipo desconocido: {kind!r}; opciones: {KINDS}")
    if not (n > 0 and fwhm_px >= 0):
        raise ValueError("n debe ser > 0 y fwhm_px ≥ 0")
    h = size_mm / n
    ph = make_body(size_mm) if kind == BODY else make_slot(size_mm)
    img = render2d(ph, spec_for(h, fwhm_px, looks), np.random.default_rng(seed)).image
    measured = {s: measure(kind, segment2d(s, img, h), h) for s in SEGMENTERS}
    return {"kind": kind, "size_mm": float(size_mm), "truth_mm": float(size_mm), "h_mm": float(h),
            "n": float(n), "fwhm_px": float(fwhm_px), "measured_mm": measured}


# --- modelo de error --------------------------------------------------------------------------

@dataclass
class ErrorModel:
    """Sesgo y desviación del error de medida (px) interpolados en (ln n, ln fwhm_px)."""
    kind: str
    segmenter: str
    n_nodes: tuple[float, ...]
    f_nodes: tuple[float, ...]
    bias_px: np.ndarray            # forma (len(n_nodes), len(f_nodes))
    sd_px: np.ndarray
    reps_per_cell: int = 0
    # H14: fracción de medidas de la calibración con |error| ≤ 0.5·n («utilizables») y, si se fija
    # ``min_usable_rate``, compuerta que rechaza las condiciones donde esa fracción es menor.
    usable_rate: np.ndarray | None = None
    min_usable_rate: float | None = None

    def __post_init__(self):
        self.bias_px = np.asarray(self.bias_px, dtype=float)
        self.sd_px = np.asarray(self.sd_px, dtype=float)
        axes = (np.log(np.asarray(self.n_nodes, float)), np.log(np.asarray(self.f_nodes, float)))
        kw = dict(method="linear", bounds_error=False, fill_value=np.nan)
        self._ib = RegularGridInterpolator(axes, self.bias_px, **kw)
        self._is = RegularGridInterpolator(axes, self.sd_px, **kw)
        self._iu = None
        if self.usable_rate is not None:
            self.usable_rate = np.asarray(self.usable_rate, dtype=float)
            self._iu = RegularGridInterpolator(axes, self.usable_rate, **kw)

    @classmethod
    def from_calibration(cls, df: pd.DataFrame, kind: str, segmenter: str,
                         min_usable_rate: float | None = None) -> "ErrorModel":
        d = df[(df["kind"] == kind) & (df["segmenter"] == segmenter)].copy()
        if d.empty:
            raise ValueError(f"sin datos de calibración para {kind}|{segmenter}")
        d["usable"] = d["err_px"].abs() <= 0.5 * d["n"]
        g = d.groupby(["n", "fwhm_px"]).agg(mean=("err_px", "mean"), std=("err_px", "std"),
                                            count=("err_px", "size"), usable=("usable", "mean"))
        ns, fs = sorted(d["n"].unique()), sorted(d["fwhm_px"].unique())
        if len(ns) < 2 or len(fs) < 2:
            raise ValueError("la cuadrícula necesita al menos 2 valores de n y 2 de fwhm_px")
        bias = np.full((len(ns), len(fs)), np.nan)
        sd = np.full_like(bias, np.nan)
        usable = np.full_like(bias, np.nan)
        reps = []
        for i, n in enumerate(ns):
            for j, f in enumerate(fs):
                if (n, f) not in g.index:
                    raise ValueError(f"cuadrícula incompleta: falta el nodo n={n}, fwhm_px={f}")
                row = g.loc[(n, f)]
                if row["count"] < 2:
                    raise ValueError(f"el nodo n={n}, fwhm_px={f} necesita ≥ 2 repeticiones")
                bias[i, j], sd[i, j], usable[i, j] = row["mean"], row["std"], row["usable"]
                reps.append(int(row["count"]))
        return cls(kind, segmenter, tuple(map(float, ns)), tuple(map(float, fs)), bias, sd, min(reps),
                   usable, min_usable_rate)

    def predict(self, n: float, fwhm_px: float):
        """(sesgo, desviación) en píxeles, o ``None`` fuera de la caja calibrada."""
        if not (n > 0 and fwhm_px > 0) or math.isnan(n) or math.isnan(fwhm_px):
            return None
        pt = [[math.log(n), math.log(fwhm_px)]]
        b, s = float(self._ib(pt)[0]), float(self._is(pt)[0])
        if math.isnan(b) or math.isnan(s):
            return None
        return b, s

    def usable_rate_at(self, n: float, fwhm_px: float):
        """Fracción de medidas utilizables interpolada, o ``None`` sin tabla o fuera de la caja."""
        if self._iu is None or not (n > 0 and fwhm_px > 0) or math.isnan(n) or math.isnan(fwhm_px):
            return None
        v = float(self._iu([[math.log(n), math.log(fwhm_px)]])[0])
        return None if math.isnan(v) else v

    def to_dict(self) -> dict:
        return {"kind": self.kind, "segmenter": self.segmenter, "n_nodes": list(self.n_nodes),
                "f_nodes": list(self.f_nodes), "bias_px": self.bias_px.tolist(),
                "sd_px": self.sd_px.tolist(), "reps_per_cell": self.reps_per_cell,
                "usable_rate": None if self.usable_rate is None else self.usable_rate.tolist(),
                "min_usable_rate": self.min_usable_rate}

    @classmethod
    def from_dict(cls, d: dict) -> "ErrorModel":
        return cls(d["kind"], d["segmenter"], tuple(d["n_nodes"]), tuple(d["f_nodes"]),
                   np.array(d["bias_px"]), np.array(d["sd_px"]), d.get("reps_per_cell", 0),
                   None if d.get("usable_rate") is None else np.array(d["usable_rate"]), d.get("min_usable_rate"))


def models_to_json(models: dict, meta: dict | None = None) -> str:
    return json.dumps({"meta": meta or {}, "models": {k: m.to_dict() for k, m in models.items()}},
                      indent=2, sort_keys=True)


def models_from_json(text: str) -> dict:
    return {k: ErrorModel.from_dict(v) for k, v in json.loads(text)["models"].items()}


# --- certificados -----------------------------------------------------------------------------

def _out_of_domain(measured_mm: float, reason: str) -> dict:
    return {"light": "amarillo", "in_domain": False, "reason": reason, "measured": float(measured_mm)}


def _predict(measured_mm: float, h_mm: float, fwhm_px: float, model: ErrorModel):
    if not (measured_mm > 0 and h_mm > 0):
        return None, "medida no positiva: no hay nada que certificar"
    n = measured_mm / h_mm
    pred = model.predict(n, fwhm_px)
    if pred is None:
        return None, "fuera de la caja de calibración (n o ancho de la función de dispersión)"
    gate = getattr(model, "min_usable_rate", None)
    if gate is not None:
        rate = model.usable_rate_at(n, fwhm_px)
        if rate is None or rate < gate:
            shown = "sin tabla" if rate is None else f"{rate:.2f}"
            return None, (f"tasa de medidas utilizables baja ({shown} < {gate:.2f}): "
                          "la medida suele fallar en estas condiciones")
    return pred, ""


def certify_body(measured_mm: float, h_mm: float, fwhm_px: float, model: ErrorModel,
                 tolerance_days: float = dating.DEFAULT_TOLERANCE_DAYS) -> dict:
    """Certificado de datación a partir de una CRL medida. Fuera de la caja calibrada: amarillo, nunca verde."""
    pred, why = _predict(measured_mm, h_mm, fwhm_px, model)
    if pred is None:
        return _out_of_domain(measured_mm, why)
    b_px, s_px = pred
    c = dating.certify_dating(measured_mm, b_px * h_mm, s_px * h_mm, tolerance_days)
    c.update(in_domain=True, n_px=measured_mm / h_mm, bias_px=b_px, sd_px=s_px)
    return c


def certify_slot(measured_mm: float, h_mm: float, fwhm_px: float, model: ErrorModel,
                 threshold_mm: float = SLOT_THRESHOLD_MM) -> dict:
    """Certificado de decisión sobre un umbral para un grosor medido. Fuera de la caja: amarillo."""
    pred, why = _predict(measured_mm, h_mm, fwhm_px, model)
    if pred is None:
        return _out_of_domain(measured_mm, why)
    b_px, s_px = pred
    c = dating.certify_side(measured_mm, b_px * h_mm, s_px * h_mm, threshold_mm)
    c.update(in_domain=True, n_px=measured_mm / h_mm, bias_px=b_px, sd_px=s_px)
    return c


# --- calibración probabilística ---------------------------------------------------------------

def expected_calibration_error(p, outcome, n_bins: int = 10) -> float:
    """Error de calibración esperado: Σ (n_b / N) · |media(p) − frecuencia observada| en cubos iguales."""
    p = np.asarray(p, dtype=float)
    y = np.asarray(outcome, dtype=float)
    if p.size == 0 or p.shape != y.shape:
        raise ValueError("p y outcome deben ser no vacíos y del mismo tamaño")
    if np.any(p < 0) or np.any(p > 1) or np.any(np.isnan(p)):
        raise ValueError("las probabilidades deben estar en [0, 1]")
    idx = np.minimum((p * n_bins).astype(int), n_bins - 1)
    ece = 0.0
    for b in range(n_bins):
        sel = idx == b
        if sel.any():
            ece += sel.mean() * abs(p[sel].mean() - y[sel].mean())
    return float(ece)
