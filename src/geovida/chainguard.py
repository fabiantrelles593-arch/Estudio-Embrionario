"""Guardia de cadena (H16): el certificado condiciona su incertidumbre a lo que la propia imagen delata (solo investigación y educación).

H15 mostró que el certificado de datación no resiste una imagen que pasó por pantalla, impresión y foto, y que el semáforo «no se
entera» (776 contra 774 verdes). Este módulo intenta que se entere, **usando solo la imagen y el tamaño de píxel**, nunca la cadena
declarada ni la verdad:

* ``image_indices`` mide dos huellas de la imagen: ``ln_cv`` (logaritmo de la variación local mediana en zonas sin bordes; baja cuando
  una compresión tonal aplana el grano) y ``skew`` (asimetría de las intensidades).
* ``fit_chain_model`` aprende, con casos de entrenamiento medidos con y sin cadena, el **desplazamiento medio** y la **varianza extra**
  del error de longitud (en píxeles) por régimen (``clean``, ``chain``, …) y por tramo de ``ln_cv``; y la caja de ``(ln_cv, skew)`` que cubre
  cada régimen.
* ``locate`` dice a qué régimen y tramo se parece una imagen, o ``None`` si cae fuera de todas las cajas (incluido el hueco entre
  regímenes): en ese caso no hay ajuste inventado, **no hay luz verde**.
* ``AdjustedModel`` envuelve un ``ErrorModel`` con ese ajuste (sesgo + desplazamiento; las varianzas se suman, no las desviaciones) y
  ``certify`` lo usa con los certificados de ``geovida.biometry``.

Lo que NO hace: no estima los parámetros de la cadena ni la curva de tono; solo reconoce si la imagen se parece a lo que vio y, si es así,
cuánto error extra se observó en imágenes parecidas. El desplazamiento medio y la varianza extra son **promedios sobre las condiciones de
entrenamiento** (no dependen de ``n`` ni del desenfoque) y la caja es rectangular: ambos son supuestos que el análisis de H16 pone a prueba.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import ndimage as ndi

from . import biometry as bio

INDICES = ("ln_cv", "skew")
WINDOW = 7                 # ventana (px) de la variación local
MIN_SIDE = 32              # lado mínimo (px) de la imagen: por debajo no hay base para ningún índice
MIN_FLAT_PX = 200          # píxeles «planos» mínimos para medir ln_cv
MIN_MEAN = 0.02            # media local mínima, relativa al percentil 99.5 de la imagen
MIN_SD = 1e-4
REQUIRED = ("kind", "regime", "ln_cv", "skew", "resid_px", "sd_clean_px")
SINGLE_BIN_REGIMES = ("clean",)
NAN_INDICES = {"ln_cv": math.nan, "skew": math.nan}


def image_indices(img) -> dict:
    """``ln_cv`` y ``skew`` de una imagen 2D (sin verdad, sin cadena declarada). ``nan`` si no hay base para medirlos."""
    a = np.asarray(img, dtype=float)
    if a.ndim != 2:
        raise ValueError("la imagen debe ser 2D (alto, ancho)")
    if not np.isfinite(a).all() or min(a.shape) < MIN_SIDE:
        return dict(NAN_INDICES)
    scale = float(np.percentile(a, 99.5))
    if not scale > 0:
        return dict(NAN_INDICES)
    x = a / scale
    sd_img = float(x.std())
    skew = float(((x - x.mean()) ** 3).mean() / sd_img ** 3) if sd_img > 1e-12 else math.nan
    m, m2 = ndi.uniform_filter(x, WINDOW), ndi.uniform_filter(x * x, WINDOW)
    sd = np.sqrt(np.maximum(m2 - m * m, 0.0))
    gy, gx = np.gradient(ndi.gaussian_filter(x, 1.5))
    g = np.hypot(gx, gy)
    ok = (g < np.percentile(g, 50)) & (m > MIN_MEAN) & (sd > MIN_SD)
    if int(ok.sum()) < MIN_FLAT_PX:
        return {"ln_cv": math.nan, "skew": skew}
    cv = float(np.median(sd[ok] / m[ok]))
    return {"ln_cv": math.log(cv) if cv > 0 else math.nan, "skew": skew}


@dataclass(frozen=True)
class Regime:
    name: str
    box: dict                      # índice -> (mínimo, máximo) de lo visto en este régimen
    edges: tuple                   # bordes interiores de los tramos de ln_cv
    mean_px: tuple                 # desplazamiento medio del error (px) por tramo
    extra_var_px2: tuple           # varianza extra del error (px²) por tramo, ≥ 0
    n: tuple                       # casos de entrenamiento por tramo

    def contains(self, idx: dict) -> bool:
        for c, (lo, hi) in self.box.items():
            v = idx.get(c, math.nan)
            if v is None or not math.isfinite(v) or v < lo - 1e-12 or v > hi + 1e-12:
                return False
        return True

    def bin_of(self, ln_cv: float) -> int:
        return int(np.searchsorted(np.asarray(self.edges, float), ln_cv, side="right"))

    def to_dict(self) -> dict:
        return {"name": self.name, "box": {k: list(v) for k, v in self.box.items()}, "edges": list(self.edges),
                "mean_px": list(self.mean_px), "extra_var_px2": list(self.extra_var_px2), "n": list(self.n)}

    @classmethod
    def from_dict(cls, d: dict) -> "Regime":
        return cls(d["name"], {k: (float(v[0]), float(v[1])) for k, v in d["box"].items()}, tuple(d["edges"]),
                   tuple(d["mean_px"]), tuple(d["extra_var_px2"]), tuple(d["n"]))


@dataclass(frozen=True)
class ChainModel:
    kind: str
    regimes: tuple

    def locate(self, idx: dict):
        """``(régimen, tramo)`` al que se parece la imagen, o ``None`` si cae fuera de todas las cajas.

        Si cae en más de una, se toma la de mayor varianza extra (la más conservadora), y a igual varianza la de mayor desplazamiento."""
        hits = []
        for r in self.regimes:
            if r.contains(idx):
                b = r.bin_of(idx["ln_cv"])
                hits.append((r.extra_var_px2[b], abs(r.mean_px[b]), r, b))
        if not hits:
            return None
        _, _, r, b = max(hits, key=lambda t: (t[0], t[1]))
        return r, b

    def adjustment(self, idx: dict):
        """``(desplazamiento_px, varianza_extra_px2)`` o ``None`` fuera del soporte."""
        loc = self.locate(idx)
        if loc is None:
            return None
        r, b = loc
        return r.mean_px[b], r.extra_var_px2[b]

    def to_dict(self) -> dict:
        return {"kind": self.kind, "regimes": [r.to_dict() for r in self.regimes]}

    @classmethod
    def from_dict(cls, d: dict) -> "ChainModel":
        return cls(d["kind"], tuple(Regime.from_dict(r) for r in d["regimes"]))


def fit_chain_model(df: pd.DataFrame, kind: str, *, n_bins: int = 3, quantiles=(0.01, 0.99),
                    min_per_bin: int = 30) -> ChainModel:
    """Ajusta el modelo de un tipo (``body`` o ``slot``) con una tabla de entrenamiento.

    Columnas: ``kind``, ``regime``, ``ln_cv``, ``skew``, ``resid_px`` (error de longitud con la imagen **menos** el sesgo que predice
    el modelo limpio, en px) y ``sd_clean_px`` (la desviación que predice el modelo limpio en ese caso). La varianza extra de un tramo
    es ``max(var(resid) − media(sd_clean²), 0)``."""
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"faltan columnas: {missing}")
    d = df[df["kind"] == kind].dropna(subset=["ln_cv", "skew", "resid_px", "sd_clean_px"])
    if d.empty:
        raise ValueError(f"sin filas de entrenamiento para el tipo {kind!r}")
    regimes = []
    for name, g in sorted(d.groupby("regime"), key=lambda t: str(t[0])):
        bins = 1 if name in SINGLE_BIN_REGIMES else int(n_bins)
        u = g["ln_cv"].to_numpy(float)
        edges = tuple(float(q) for q in np.quantile(u, [k / bins for k in range(1, bins)])) if bins > 1 else ()
        which = np.searchsorted(np.asarray(edges, float), u, side="right")
        means, extra, counts = [], [], []
        for b in range(bins):
            sel = which == b
            if int(sel.sum()) < min_per_bin:
                raise ValueError(f"el régimen {name!r} tiene {int(sel.sum())} casos en el tramo {b} (mínimo {min_per_bin})")
            r = g["resid_px"].to_numpy(float)[sel]
            s2 = float((g["sd_clean_px"].to_numpy(float)[sel] ** 2).mean())
            means.append(float(r.mean()))
            extra.append(max(float(r.var(ddof=1)) - s2, 0.0))
            counts.append(int(sel.sum()))
        box = {c: (float(g[c].quantile(quantiles[0])), float(g[c].quantile(quantiles[1]))) for c in INDICES}
        regimes.append(Regime(str(name), box, edges, tuple(means), tuple(extra), tuple(counts)))
    return ChainModel(kind, tuple(regimes))


class AdjustedModel:
    """``ErrorModel`` con el desplazamiento y la varianza extra de una cadena (mismo interfaz para los certificados)."""

    def __init__(self, base: bio.ErrorModel, mean_px: float, extra_var_px2: float):
        if not (math.isfinite(mean_px) and math.isfinite(extra_var_px2)) or extra_var_px2 < 0:
            raise ValueError("el desplazamiento debe ser finito y la varianza extra finita y ≥ 0")
        self.base, self.mean_px, self.extra_var_px2 = base, float(mean_px), float(extra_var_px2)
        self.kind, self.segmenter = base.kind, base.segmenter

    @property
    def min_usable_rate(self):
        return getattr(self.base, "min_usable_rate", None)

    def usable_rate_at(self, n, fwhm_px):
        return self.base.usable_rate_at(n, fwhm_px)

    def predict(self, n, fwhm_px):
        p = self.base.predict(n, fwhm_px)
        if p is None:
            return None
        b, s = p
        return b + self.mean_px, math.sqrt(s * s + self.extra_var_px2)


def certify(kind: str, measured_mm: float, h_mm: float, fwhm_px: float, base: bio.ErrorModel,
            chain_model: ChainModel, indices: dict) -> dict:
    """Certificado con el modelo ajustado a lo que la imagen delata; fuera del soporte de la guardia: amarillo."""
    if kind not in bio.KINDS:
        raise ValueError(f"tipo desconocido: {kind!r}; opciones: {bio.KINDS}")
    loc = chain_model.locate(indices)
    if loc is None:
        return bio._out_of_domain(measured_mm, "la imagen no se parece a ninguna cadena vista al ajustar la guardia de cadena "
                                               "(o sus índices no se pudieron calcular)")
    regime, b = loc
    adj = AdjustedModel(base, regime.mean_px[b], regime.extra_var_px2[b])
    fn = bio.certify_body if kind == bio.BODY else bio.certify_slot
    cert = fn(measured_mm, h_mm, fwhm_px, adj)
    cert.update(chain_regime=regime.name, chain_bin=b)
    return cert
