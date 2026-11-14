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
from . import dating

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


# --- diseño 2: recalibración de la probabilidad condicionada a la imagen ----------------------------------------------------
#
# Sumar una varianza media (diseño 1) supone que el error extra de la cadena es gaussiano. El piloto de H16 mostró que no lo es: la
# mayoría de los casos sale bien y unos pocos fallan mucho, y una varianza media los describe mal (casi ningún verde de CRL sobrevive).
# El diseño 2 no supone esa forma: reajusta la probabilidad del certificado con una regresión logística sobre los aciertos observados en
# el entrenamiento, dadas la probabilidad base (en logit) y los dos índices de la imagen, un modelo por régimen. El soporte es la misma
# caja rectangular de ``(ln_cv, skew)`` por régimen; fuera de ella no hay certificado.

LOGIT_EPS = 1e-4
RECAL_REQUIRED = ("kind", "regime", "ln_cv", "skew", "p_base", "correct")
MIN_RECAL_ROWS = 100
RIDGE = 1.0                # penalización L2 de los pesos (no del intercepto) sobre las variables estandarizadas


def _logit(p):
    p = np.clip(np.asarray(p, dtype=float), LOGIT_EPS, 1.0 - LOGIT_EPS)
    return np.log(p / (1.0 - p))


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -35.0, 35.0)))


def _fit_logistic(x: np.ndarray, y: np.ndarray, ridge: float) -> np.ndarray:
    """Regresión logística con L2 (IRLS). Devuelve ``[intercepto, pesos...]`` para variables ya estandarizadas."""
    a = np.column_stack([np.ones(len(x)), x])
    pen = ridge * np.eye(a.shape[1])
    pen[0, 0] = 0.0
    beta = np.zeros(a.shape[1])
    for _ in range(100):
        mu = _sigmoid(a @ beta)
        w = mu * (1.0 - mu) + 1e-9
        step = np.linalg.solve(a.T @ (a * w[:, None]) + pen, a.T @ (y - mu) - pen @ beta)
        beta = beta + step
        if float(np.max(np.abs(step))) < 1e-9:
            break
    return beta


@dataclass(frozen=True)
class RecalRegime:
    name: str
    box: dict                      # índice -> (mínimo, máximo)
    mu: tuple                      # media de las 3 variables (logit p, ln_cv, skew) en el entrenamiento
    sd: tuple
    coef: tuple                    # intercepto y 3 pesos sobre las variables estandarizadas

    def contains(self, idx: dict) -> bool:
        return Regime.contains(self, idx)

    def prob(self, p_base: float, idx: dict) -> float:
        x = (np.array([float(_logit(p_base)), idx["ln_cv"], idx["skew"]]) - np.asarray(self.mu)) / np.asarray(self.sd)
        return float(_sigmoid(self.coef[0] + float(np.dot(self.coef[1:], x))))

    def to_dict(self) -> dict:
        return {"name": self.name, "box": {k: list(v) for k, v in self.box.items()}, "mu": list(self.mu), "sd": list(self.sd),
                "coef": list(self.coef)}

    @classmethod
    def from_dict(cls, d: dict) -> "RecalRegime":
        return cls(d["name"], {k: (float(v[0]), float(v[1])) for k, v in d["box"].items()}, tuple(d["mu"]), tuple(d["sd"]),
                   tuple(d["coef"]))


@dataclass(frozen=True)
class RecalModel:
    kind: str
    regimes: tuple

    def predict_with_regime(self, p_base: float, idx: dict):
        """``(probabilidad recalibrada, nombre del régimen)`` o ``None`` fuera del soporte. Con cajas solapadas, la menor probabilidad."""
        if p_base is None or not math.isfinite(p_base):
            return None
        hits = [(r.prob(p_base, idx), r.name) for r in self.regimes if r.contains(idx)]
        return min(hits) if hits else None

    def predict(self, p_base: float, idx: dict):
        res = self.predict_with_regime(p_base, idx)
        return None if res is None else res[0]

    def to_dict(self) -> dict:
        return {"kind": self.kind, "regimes": [r.to_dict() for r in self.regimes]}

    @classmethod
    def from_dict(cls, d: dict) -> "RecalModel":
        return cls(d["kind"], tuple(RecalRegime.from_dict(r) for r in d["regimes"]))


def fit_recal_model(df: pd.DataFrame, kind: str, *, ridge: float = RIDGE, quantiles=(0.01, 0.99),
                    min_rows: int = MIN_RECAL_ROWS) -> RecalModel:
    """Ajusta la recalibración de un tipo. Columnas: ``kind``, ``regime``, ``ln_cv``, ``skew``, ``p_base`` (probabilidad del
    certificado base) y ``correct`` (si la medida fue correcta, con la verdad de la simulación)."""
    missing = [c for c in RECAL_REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"faltan columnas: {missing}")
    d = df[df["kind"] == kind].dropna(subset=["ln_cv", "skew", "p_base", "correct"])
    if d.empty:
        raise ValueError(f"sin filas de entrenamiento para el tipo {kind!r}")
    regimes = []
    for name, g in sorted(d.groupby("regime"), key=lambda t: str(t[0])):
        if len(g) < min_rows:
            raise ValueError(f"el régimen {name!r} tiene {len(g)} filas (mínimo {min_rows})")
        x = np.column_stack([_logit(g["p_base"].to_numpy(float)), g["ln_cv"].to_numpy(float), g["skew"].to_numpy(float)])
        mu, sd = x.mean(axis=0), x.std(axis=0)
        sd = np.where(sd < 1e-9, 1.0, sd)
        beta = _fit_logistic((x - mu) / sd, g["correct"].to_numpy(float), ridge)
        box = {c: (float(g[c].quantile(quantiles[0])), float(g[c].quantile(quantiles[1]))) for c in INDICES}
        regimes.append(RecalRegime(str(name), box, tuple(float(v) for v in mu), tuple(float(v) for v in sd),
                                   tuple(float(v) for v in beta)))
    return RecalModel(kind, tuple(regimes))


def certify_recal(kind: str, measured_mm: float, h_mm: float, fwhm_px: float, base: bio.ErrorModel,
                  recal: RecalModel, indices: dict) -> dict:
    """Certificado con la probabilidad recalibrada. Lo que rechaza el modelo base (caja, compuerta) se rechaza igual; si la imagen cae
    fuera del soporte de la recalibración, amarillo. Los umbrales de color son los del certificado base (verde ≥ 0.90)."""
    if kind not in bio.KINDS:
        raise ValueError(f"tipo desconocido: {kind!r}; opciones: {bio.KINDS}")
    body = kind == bio.BODY
    cert = (bio.certify_body if body else bio.certify_slot)(measured_mm, h_mm, fwhm_px, base)
    if not cert["in_domain"]:
        return cert
    key = "p_within_tolerance" if body else "p_same_side"
    res = recal.predict_with_regime(cert[key], indices)
    if res is None:
        return bio._out_of_domain(measured_mm, "la imagen no se parece a ninguna cadena vista al ajustar la guardia de cadena "
                                               "(o sus índices no se pudieron calcular)")
    p, name = res
    if p >= dating.GREEN:
        light = "verde"
    elif (p < dating.RED) if body else (p <= dating.RED):          # el empate cuenta como rojo solo en el certificado de decisión
        light = "rojo"
    else:
        light = "amarillo"
    if body and not cert["in_range"] and light == "verde":
        light = "amarillo"
    cert.update({"p_base": cert[key], key: p, "light": light, "chain_regime": name})
    return cert
