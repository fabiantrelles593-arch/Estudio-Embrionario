"""H14 — compuerta de «tasa de medidas utilizables» sobre el certificado de H13.

Solo investigación y educación; todo es simulación. Reglas en ``docs/PREREGISTRO_H14.md``.

La compuerta se diseñó **viendo** los resultados de confirmación de H13 (ver ``docs/RESULTADOS_V06.md`` §3), así
que H14 se prueba con casos nuevos (semilla propia) y compara, sobre los mismos casos, el modelo con compuerta
(``gated``) y sin ella (``ungated``).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import biometry as bio
from . import h13

H14_FREEZE_MIN_USABLE = 0.90
H14_CONF_SEED = 20261215
WRONG_GREEN_RATE_MAX = 0.02      # verdes equivocados por caso (no por verde)
MIN_CASES = 100
RETAIN_MIN = {bio.SLOT: 0.80, bio.BODY: 0.95}
WIDE_PSF_PX = 3.5


def _in_box(df: pd.DataFrame, segmenter: str, kind: str | None = None, variant: str | None = None) -> pd.DataFrame:
    d = df[(df["segmenter"] == segmenter) & (df["region"] == "in")]
    if kind is not None:
        d = d[d["kind"] == kind]
    if variant is not None:
        d = d[d["variant"] == variant]
    return d


def wide_psf_slot(df: pd.DataFrame, segmenter: str = h13.PRIMARY_SEGMENTER, variant: str | None = None) -> pd.DataFrame:
    d = _in_box(df, segmenter, bio.SLOT, variant)
    return d[d["fwhm_px"] > WIDE_PSF_PX]


def wrong_green_rate_verdict(d: pd.DataFrame, n_boot: int = h13.N_BOOT, seed: int = h13.BOOT_SEED) -> dict:
    """Verdes equivocados por caso (denominador: todos los casos). Apoyada: límite superior del IC 95 % ≤ 2 %.
    No apoyada: límite inferior > 2 %. No concluyente: el IC contiene el 2 %. No evaluable: < 100 casos."""
    n = len(d)
    wrong = ((d["light"] == "verde") & ~d["correct"].astype(bool)).to_numpy()
    out = {"n_cases": int(n), "n_green": int((d["light"] == "verde").sum()), "n_wrong_green": int(wrong.sum()),
           "rate": float(wrong.mean()) if n else float("nan"), "ci": None, "verdict": "no evaluable"}
    if n < MIN_CASES:
        return out
    rng = np.random.default_rng(seed)
    rates = wrong[rng.integers(0, n, size=(n_boot, n))].mean(axis=1)
    lo, hi = np.percentile(rates, [2.5, 97.5])
    out["ci"] = (float(lo), float(hi))
    out["verdict"] = ("apoyada" if hi <= WRONG_GREEN_RATE_MAX else
                      "no apoyada" if lo > WRONG_GREEN_RATE_MAX else "no concluyente")
    return out


def retention(df: pd.DataFrame) -> dict:
    """Costo de cobertura: verdes con compuerta / verdes sin compuerta, sobre los mismos casos (segmentador
    primario, dentro de la caja). Apoyada si ≥ 80 % en la ranura y ≥ 95 % en el cuerpo."""
    out = {}
    for kind in (bio.SLOT, bio.BODY):
        u = _in_box(df, h13.PRIMARY_SEGMENTER, kind, "ungated")
        g = _in_box(df, h13.PRIMARY_SEGMENTER, kind, "gated")
        nu, ng = int((u["light"] == "verde").sum()), int((g["light"] == "verde").sum())
        r = ng / nu if nu else float("nan")
        verdict = "no evaluable" if nu == 0 else ("apoyada" if r >= RETAIN_MIN[kind] else "no apoyada")
        out[kind] = {"ungated_green": nu, "gated_green": ng, "retained": r, "min": RETAIN_MIN[kind], "verdict": verdict}
    return out


def _combine(vs) -> str:
    return h13._combine(vs)


def evaluate_h14(df: pd.DataFrame, n_boot: int = h13.N_BOOT, seed: int = h13.BOOT_SEED) -> dict:
    g, u = df[df["variant"] == "gated"], df[df["variant"] == "ungated"]
    h14a = wrong_green_rate_verdict(wide_psf_slot(g), n_boot, seed)
    h14a["ungated_rate"] = wrong_green_rate_verdict(wide_psf_slot(u), n_boot, seed)["rate"]
    h14c = {k: h13.false_green_verdict(g[g["kind"] == k], n_boot, seed) for k in bio.KINDS}
    h14c["verdict"] = _combine(v["verdict"] for v in h14c.values())
    otsu = _in_box(g, "otsu", bio.SLOT)
    h14d = wrong_green_rate_verdict(otsu, n_boot, seed)
    h14d["ungated_rate"] = wrong_green_rate_verdict(_in_box(u, "otsu", bio.SLOT), n_boot, seed)["rate"]
    h14e = {k: h13.guard_verdict(g[g["kind"] == k], n_boot, seed) for k in bio.KINDS}
    h14e["verdict"] = _combine(v["verdict"] for v in h14e.values())
    return {"h14a": h14a, "h14b": retention(df), "h14c": h14c, "h14d": h14d, "h14e": h14e}
