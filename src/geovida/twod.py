"""Módulo 2D (v0.2): fantomas planos con verdad exacta, imagen tipo ecografía
(moteado multiplicativo) y medidas de área, perímetro, circunferencia por elipse
(estilo calibrador de ecografía) y topología.

Es una prueba de estrés del *instrumento de medida* sobre imágenes sintéticas.
No procesa ni representa ecografías reales y no tiene uso clínico.

Convenciones
------------
* ``t`` es el menor grosor sólido: diámetro del disco, eje menor de la elipse
  (semieje mayor = 1.25 × semieje menor, como un corte craneal con índice
  cefálico 0.8) y ancho del anillo (diámetro interior = 3 t).
* La imagen se normaliza para que el fondo valga 0 y el primer plano 1 en
  media; así el umbral oráculo es 0.5 en todos los perfiles.
* Moteado: campo complejo gaussiano suavizado (grano ~ 2 px) cuya intensidad
  se promedia en ``looks`` realizaciones independientes (compounding);
  coeficiente de variación = 1/sqrt(looks). Es un modelo, no una ecografía.
"""
from __future__ import annotations

import itertools
import math
import multiprocessing as mp
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from scipy.special import ellipe
from skimage.filters import threshold_otsu
from skimage.measure import perimeter_crofton, regionprops

PHANTOMS_2D = ("disk", "ellipse", "annulus")
# v0.3 (H7): anillo con el hueco tan estrecho como la pared (ancho t, hueco de
# diámetro t). No entra en el diseño de H5 ni mueve sus índices de semilla.
EXTRA_2D = ("ring_tight",)
ALL_2D = PHANTOMS_2D + EXTRA_2D
PROFILES_2D = ("ideal", "us_compound", "us_raw")
T_OVER_H_2D = (2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 20.0)
BASE_SEED_2D = 20261112
H7_SEED = 20261120
CLEAN2D_MIN_PX = 4          # preregistrado en H7
CLEAN2D_FRACTION = 0.005    # preregistrado en H7
BG_LEVEL = 0.25  # fondo a 25 % del primer plano (contraste 4:1)
FWHM_TO_SIGMA = 1.0 / (2.0 * math.sqrt(2.0 * math.log(2.0)))


@dataclass(frozen=True)
class Truth2D:
    area: float
    perimeter: float        # longitud total de frontera
    outer_perimeter: float  # contorno exterior (lo que mide un calibrador)
    betti: tuple[int, int]
    chi: int
    t_solid: float
    t_void: float

    @property
    def t_min(self) -> float:
        return min(self.t_solid, self.t_void)


@dataclass(frozen=True)
class Phantom2D:
    name: str
    t: float
    truth: Truth2D
    half_extent: tuple[float, float]
    _inside: Callable[[np.ndarray], np.ndarray]

    def contains(self, pts: np.ndarray) -> np.ndarray:
        return self._inside(np.asarray(pts, dtype=float))

    @property
    def bounding_radius(self) -> float:
        return float(math.hypot(*self.half_extent))


def make_phantom2d(name: str, t: float) -> Phantom2D:
    if not t > 0:
        raise ValueError("t debe ser > 0")
    if name == "disk":
        r = t / 2
        truth = Truth2D(math.pi * r * r, 2 * math.pi * r, 2 * math.pi * r, (1, 0), 1, t, math.inf)
        return Phantom2D(name, t, truth, (r, r), lambda p: (p**2).sum(-1) <= r * r)
    if name == "ellipse":
        b = t / 2
        a = 1.25 * b
        per = 4 * a * ellipe(1 - (b / a) ** 2)
        truth = Truth2D(math.pi * a * b, float(per), float(per), (1, 0), 1, t, math.inf)
        return Phantom2D(name, t, truth, (a, b),
                         lambda p: (p[..., 0] / a) ** 2 + (p[..., 1] / b) ** 2 <= 1.0)
    if name == "annulus":
        ri, ro = 1.5 * t, 2.5 * t
        truth = Truth2D(math.pi * (ro**2 - ri**2), 2 * math.pi * (ro + ri),
                        2 * math.pi * ro, (1, 1), 0, t, 3.0 * t)

        def inside(p):
            d2 = (p**2).sum(-1)
            return (d2 <= ro * ro) & (d2 >= ri * ri)

        return Phantom2D(name, t, truth, (ro, ro), inside)
    if name == "ring_tight":
        ri, ro = 0.5 * t, 1.5 * t
        truth = Truth2D(math.pi * (ro**2 - ri**2), 2 * math.pi * (ro + ri),
                        2 * math.pi * ro, (1, 1), 0, t, t)

        def inside_tight(p):
            d2 = (p**2).sum(-1)
            return (d2 <= ro * ro) & (d2 >= ri * ri)

        return Phantom2D(name, t, truth, (ro, ro), inside_tight)
    raise ValueError(f"fantoma 2D desconocido: {name!r}; opciones: {ALL_2D}")


# --- imagen -----------------------------------------------------------------

@dataclass(frozen=True)
class Spec2D:
    h: float
    fwhm_px: float = 0.0
    looks: int = 0            # 0 = sin moteado
    grain_fwhm_px: float = 2.0
    bg_level: float = BG_LEVEL
    supersample: int = 4
    margin_px: int = 8


@dataclass(frozen=True)
class Rendered2D:
    image: np.ndarray
    coverage: np.ndarray
    spacing: float


def spec2d_for(t_over_h: float, profile: str, t: float = 1.0) -> Spec2D:
    h = t / t_over_h
    if profile == "ideal":
        return Spec2D(h)
    if profile == "us_compound":
        return Spec2D(h, fwhm_px=1.0, looks=4)
    if profile == "us_raw":
        return Spec2D(h, fwhm_px=1.0, looks=1)
    raise ValueError(f"perfil 2D desconocido: {profile!r}; opciones: {PROFILES_2D}")


def _speckle(shape: tuple[int, int], looks: int, grain_fwhm_px: float,
             rng: np.random.Generator) -> np.ndarray:
    sigma = grain_fwhm_px * FWHM_TO_SIGMA
    acc = np.zeros(shape)
    for _ in range(looks):
        re = ndi.gaussian_filter(rng.standard_normal(shape), sigma)
        im = ndi.gaussian_filter(rng.standard_normal(shape), sigma)
        inten = re * re + im * im
        acc += inten / inten.mean()
    return acc / looks


def render2d(ph: Phantom2D, spec: Spec2D, rng: np.random.Generator) -> Rendered2D:
    h, s = spec.h, spec.supersample
    n = int(math.ceil(2 * ph.bounding_radius / h)) + 2 * spec.margin_px + 2
    theta = rng.uniform(0.0, 2.0 * math.pi)
    off = rng.uniform(-0.5, 0.5, size=2) * h
    c, sn = math.cos(theta), math.sin(theta)
    fine = (np.arange(n * s) + 0.5) / s - n / 2
    X, Y = np.meshgrid(fine * h - off[0], fine * h - off[1], indexing="ij")
    # al marco canónico: rotación inversa
    pts = np.stack([c * X + sn * Y, -sn * X + c * Y], axis=-1)
    inside = ph.contains(pts)
    coverage = inside.reshape(n, s, n, s).mean(axis=(1, 3))
    cov = ndi.gaussian_filter(coverage, spec.fwhm_px * FWHM_TO_SIGMA) if spec.fwhm_px > 0 else coverage
    delta = 1.0 - spec.bg_level
    signal = spec.bg_level + delta * cov
    if spec.looks > 0:
        signal = signal * _speckle((n, n), spec.looks, spec.grain_fwhm_px, rng)
    image = (signal - spec.bg_level) / delta
    return Rendered2D(image=image.astype(np.float32), coverage=coverage, spacing=h)


# --- segmentación -----------------------------------------------------------

_CROSS = ndi.generate_binary_structure(2, 1)
_FULL = ndi.generate_binary_structure(2, 2)

def _g(image, spacing):
    return image >= 0.5


def _o(image, spacing):
    return image >= threshold_otsu(image)


def _so(sigma):
    def f(image, spacing):
        sm = ndi.gaussian_filter(image, sigma)
        return sm >= threshold_otsu(sm)
    return f


SEGMENTERS_2D = {"global": _g, "otsu": _o, "smoothed_otsu": _so(1.0), "smoothed_otsu_s2": _so(2.0)}


_CLEAN_SUFFIX = "_clean"


def segment2d(name: str, image: np.ndarray, spacing) -> np.ndarray:
    """Segmenta con uno de los cuatro preregistrados de H5 o con su versión
    ``<nombre>_clean`` (H7: la misma máscara pasada por ``_clean_mask_2d``)."""
    base = name[: -len(_CLEAN_SUFFIX)] if name.endswith(_CLEAN_SUFFIX) else name
    if base not in SEGMENTERS_2D:
        options = tuple(SEGMENTERS_2D) + tuple(n + _CLEAN_SUFFIX for n in SEGMENTERS_2D)
        raise ValueError(f"segmentador 2D desconocido: {name!r}; opciones: {options}")
    mask = SEGMENTERS_2D[base](image, spacing).astype(bool)
    return _clean_mask_2d(mask)[0] if base != name else mask


# --- limpieza que escala con el objeto (H7) ---------------------------------

def _clean_mask_2d(mask: np.ndarray):
    """Limpieza preregistrada en H7. Devuelve (máscara, componentes quitados,
    huecos rellenados, umbral en píxeles).

    Se quitan los componentes (8-conexos) y se rellenan los huecos (4-conexos,
    nunca el exterior) de menos de ``max(4, ceil(0.005 A))`` píxeles, con A el
    área del componente mayor de la máscara de entrada.

    LÍMITE CONOCIDO (lección de ERRATA E11): el criterio es de tamaño, no de
    significado. Un hueco REAL más pequeño que el umbral también se rellena.
    """
    m = np.asarray(mask, dtype=bool)
    lab, n = ndi.label(m, structure=_FULL)
    if n == 0:
        return m.copy(), 0, 0, CLEAN2D_MIN_PX
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    thr = max(CLEAN2D_MIN_PX, int(math.ceil(CLEAN2D_FRACTION * int(sizes.max()))))
    small = sizes < thr
    small[0] = False
    removed = int(small.sum())
    out = m & ~small[lab]
    padded = np.pad(~out, 1, constant_values=True)
    lab_bg, n_bg = ndi.label(padded, structure=_CROSS)
    filled = 0
    if n_bg:
        bg_sizes = np.bincount(lab_bg.ravel())
        small_bg = bg_sizes < thr
        small_bg[0] = False
        small_bg[lab_bg[0, 0]] = False          # el exterior toca el marco
        filled = int(small_bg.sum())
        out = out | small_bg[lab_bg][1:-1, 1:-1]
    return out, removed, filled, thr


def clean_report_2d(mask: np.ndarray) -> dict:
    """Qué borraría la limpieza de H7 en esta máscara (para no limpiar en silencio)."""
    _, removed, filled, thr = _clean_mask_2d(mask)
    return {"removed_components": removed, "filled_holes": filled, "threshold_px": thr}


# --- medidas ----------------------------------------------------------------

@dataclass(frozen=True)
class Betti2D:
    b0: int
    b1: int

    def as_tuple(self) -> tuple[int, int]:
        return (self.b0, self.b1)

    @property
    def chi(self) -> int:
        return self.b0 - self.b1


def betti_2d(mask: np.ndarray, fg_connectivity: int = 8) -> Betti2D:
    """b0 = componentes; b1 = huecos (fondo no conectado al exterior), con
    adyacencias complementarias: (8,4) primaria, (4,8) secundaria."""
    if fg_connectivity not in (4, 8):
        raise ValueError("fg_connectivity debe ser 4 u 8")
    m = np.asarray(mask, dtype=bool)
    if m.ndim != 2:
        raise ValueError("se espera una máscara 2D")
    if not m.any():
        return Betti2D(0, 0)
    fg, bg = (_FULL, _CROSS) if fg_connectivity == 8 else (_CROSS, _FULL)
    _, b0 = ndi.label(m, structure=fg)
    _, nbg = ndi.label(np.pad(~m, 1, constant_values=True), structure=bg)
    return Betti2D(int(b0), int(nbg - 1))


def _hc_ellipse(mask: np.ndarray, spacing: float) -> float:
    """Perímetro (Ramanujan II) de la elipse equivalente del mayor componente,
    con huecos rellenos: lo que haría un calibrador ajustando el contorno exterior."""
    lab, n = ndi.label(mask, structure=_FULL)
    if n == 0:
        return 0.0
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    big = ndi.binary_fill_holes(lab == sizes.argmax())
    p = regionprops(big.astype(np.uint8))[0]
    a, b = p.axis_major_length / 2 * spacing, p.axis_minor_length / 2 * spacing
    if a <= 0 or b <= 0:
        return 0.0
    return float(math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b))))


def measure_mask_2d(mask: np.ndarray, spacing: float) -> dict:
    mask = np.asarray(mask, dtype=bool)
    out = {"area": float(mask.sum() * spacing**2)}
    if not mask.any():
        out.update(perim_crofton=0.0, hc_ellipse=0.0)
    else:
        out.update(perim_crofton=float(perimeter_crofton(mask, 4) * spacing),
                   hc_ellipse=_hc_ellipse(mask, spacing))
    for conn, suffix in ((8, ""), (4, "_4")):
        b = betti_2d(mask, conn)
        out[f"b0{suffix}"], out[f"b1{suffix}"] = b.b0, b.b1
    return out


def relative_errors_2d(meas: dict, truth: Truth2D) -> dict:
    out = {"err_area": (meas["area"] - truth.area) / truth.area,
           "err_perim_crofton": (meas["perim_crofton"] - truth.perimeter) / truth.perimeter,
           "err_hc": (meas["hc_ellipse"] - truth.outer_perimeter) / truth.outer_perimeter}
    for suffix in ("", "_4"):
        d = (meas[f"b0{suffix}"] - truth.betti[0], meas[f"b1{suffix}"] - truth.betti[1])
        out[f"err_b0{suffix}"], out[f"err_b1{suffix}"] = int(d[0]), int(d[1])
        out[f"topology_ok{suffix}"] = bool(d == (0, 0))
    return out


# --- experimento ------------------------------------------------------------

@dataclass(frozen=True)
class Condition2D:
    shape: str
    t_over_h: float
    profile: str
    rep: int


def design_2d(n_reps: int) -> list[Condition2D]:
    return [Condition2D(s, t, p, r)
            for s, t, p, r in itertools.product(PHANTOMS_2D, T_OVER_H_2D, PROFILES_2D, range(n_reps))]


def _rng2d(c: Condition2D, base_seed: int) -> np.random.Generator:
    key = [base_seed, ALL_2D.index(c.shape), int(round(c.t_over_h * 100)),
           PROFILES_2D.index(c.profile), c.rep]
    return np.random.default_rng(np.random.SeedSequence(key))


def _row_2d(c: Condition2D, seg: str, mask: np.ndarray, ref: np.ndarray, tr: Truth2D,
            spacing: float) -> dict:
    meas = measure_mask_2d(mask, spacing)
    tot = mask.sum() + ref.sum()
    return {
        "shape": c.shape, "t_over_h": c.t_over_h, "profile": c.profile, "rep": c.rep,
        "segmenter": seg, "t_min_over_h": tr.t_min * c.t_over_h,
        "area_true": tr.area, "perimeter_true": tr.perimeter,
        "outer_perimeter_true": tr.outer_perimeter,
        **meas, **relative_errors_2d(meas, tr),
        "dice": 1.0 if tot == 0 else float(2.0 * np.logical_and(mask, ref).sum() / tot),
    }


def run_condition_2d(c: Condition2D, base_seed: int = BASE_SEED_2D) -> list[dict]:
    ph = make_phantom2d(c.shape, 1.0)
    out = render2d(ph, spec2d_for(c.t_over_h, c.profile), _rng2d(c, base_seed))
    ref = out.coverage >= 0.5
    return [_row_2d(c, seg, segment2d(seg, out.image, out.spacing), ref, ph.truth, out.spacing)
            for seg in SEGMENTERS_2D]


def design_h7(n_reps: int) -> list[Condition2D]:
    """Diseño de H7: las tres formas de H5 más ``ring_tight``, misma rejilla y perfiles."""
    return [Condition2D(s, t, p, r)
            for s, t, p, r in itertools.product(ALL_2D, T_OVER_H_2D, PROFILES_2D, range(n_reps))]


def run_condition_h7(c: Condition2D, base_seed: int = H7_SEED) -> list[dict]:
    """Cada segmentador de H5 y su versión limpia sobre LA MISMA imagen (pareado)."""
    ph = make_phantom2d(c.shape, 1.0)
    out = render2d(ph, spec2d_for(c.t_over_h, c.profile), _rng2d(c, base_seed))
    ref = out.coverage >= 0.5
    rows = []
    for seg in SEGMENTERS_2D:
        base = segment2d(seg, out.image, out.spacing)
        cleaned, removed, filled, thr = _clean_mask_2d(base)
        for name, mask, is_clean in ((seg, base, False), (seg + _CLEAN_SUFFIX, cleaned, True)):
            row = _row_2d(c, name, mask, ref, ph.truth, out.spacing)
            row.update(base=seg, cleaned=is_clean,
                       removed_components=removed if is_clean else 0,
                       filled_holes=filled if is_clean else 0,
                       clean_threshold_px=thr)
            rows.append(row)
    return rows


def _worker(args):
    fn, cond, base_seed = args
    return fn(cond, base_seed)


def run_sweep_2d(conditions: list[Condition2D], n_jobs: int = 1,
                 base_seed: int = BASE_SEED_2D, condition_fn=run_condition_2d) -> pd.DataFrame:
    jobs = [(condition_fn, c, base_seed) for c in conditions]
    if n_jobs <= 1:
        chunks = [_worker(j) for j in jobs]
    else:
        with mp.get_context("fork").Pool(n_jobs) as pool:
            chunks = pool.map(_worker, jobs, chunksize=8)
    return pd.DataFrame([r for chunk in chunks for r in chunk])
