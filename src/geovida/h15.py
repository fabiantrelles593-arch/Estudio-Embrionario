"""H15 — ¿resiste el certificado una imagen que pasó por pantalla, impresión y foto? (solo simulación)

Reglas en ``docs/PREREGISTRO_H15.md``. Se usan los modelos congelados de H14 (compuerta incluida), sin recalibrar:
los mismos casos se miden sobre la imagen limpia (``clean``) y sobre la imagen transformada por
``geovida.printchain`` (``chain``). El certificado sigue consultándose con el desenfoque y el tamaño **declarados**
(los verdaderos): H15 aísla el efecto de la cadena sobre el error de la medida.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import biometry as bio
from . import h13, printchain

H15_CONF_SEED = 20261216
H15_PILOT_SEED = 20261217
CHAIN_STREAM = 7


def chain_cases(n_in: int, n_out: int, base_seed: int) -> list[dict]:
    """Los casos de H13 (mismos muestreadores) con parámetros de la cadena fijados por caso."""
    cases = h13.confirmation_cases(n_in, n_out, base_seed)
    for c in cases:
        c["chain"] = printchain.sample_chain(np.random.default_rng([base_seed, CHAIN_STREAM, c["idx"]]))
    return cases


def run(cases: list[dict], models: dict, n_jobs: int = 1) -> pd.DataFrame:
    """Mide cada caso sin y con la cadena (mismo render, mismas semillas) y devuelve ambas variantes."""
    clean_cases = [{k: v for k, v in c.items() if k != "chain"} for c in cases]
    parts = []
    for name, cs in (("clean", clean_cases), ("chain", cases)):
        d = h13.run_confirmation(cs, models, n_jobs)
        d["variant"] = name
        parts.append(d)
    return pd.concat(parts, ignore_index=True)


def _as_primary(d: pd.DataFrame, segmenter: str) -> pd.DataFrame:
    """Reetiqueta un segmentador de control como el primario para reutilizar las reglas de H13."""
    return d[d["segmenter"] == segmenter].assign(segmenter=h13.PRIMARY_SEGMENTER)


def paired_shift(df: pd.DataFrame) -> dict:
    """Cambio de la longitud medida por la cadena, mismos casos: (medida con − sin) / verdad, en %."""
    keys = ["idx", "kind", "segmenter", "region"]
    c, k = df[df["variant"] == "chain"], df[df["variant"] == "clean"]
    m = c.merge(k, on=keys, suffixes=("_chain", "_clean"))
    m = m[m["region"] == "in"]
    out = {}
    for (kind, seg), g in m.groupby(["kind", "segmenter"]):
        rel = 100.0 * (g["measured_mm_chain"] - g["measured_mm_clean"]) / g["truth_mm_chain"]
        both = g[g["in_domain_chain"].astype(bool) & g["in_domain_clean"].astype(bool)]
        sd = both["sd_mm_clean"].to_numpy(float)
        shift = (both["measured_mm_chain"] - both["measured_mm_clean"]).abs().to_numpy(float)
        out[f"{kind}|{seg}"] = {
            "n": int(len(g)), "median_pct": float(rel.median()), "mean_pct": float(rel.mean()),
            "p5_pct": float(rel.quantile(0.05)), "p95_pct": float(rel.quantile(0.95)),
            "median_abs_shift_over_model_sd": float(np.nanmedian(shift / sd)) if len(both) and (sd > 0).any() else float("nan")}
    return out


def retention(df: pd.DataFrame) -> dict:
    """Verdes con cadena / verdes sin cadena, mismos casos (segmentador primario, dentro de la caja)."""
    out = {}
    for kind in bio.KINDS:
        d = df[(df["segmenter"] == h13.PRIMARY_SEGMENTER) & (df["region"] == "in") & (df["kind"] == kind)]
        gc = int(((d["variant"] == "chain") & (d["light"] == "verde")).sum())
        gk = int(((d["variant"] == "clean") & (d["light"] == "verde")).sum())
        out[kind] = {"green_clean": gk, "green_chain": gc, "ratio": gc / gk if gk else float("nan")}
    return out


def compression_terciles(df: pd.DataFrame) -> pd.DataFrame:
    """EXPLORATORIO: verdes equivocados por tercil de la compresión logarítmica (solo variante ``chain``)."""
    d = df[(df["variant"] == "chain") & (df["segmenter"] == h13.PRIMARY_SEGMENTER) & (df["region"] == "in")].copy()
    d["compression"] = pd.qcut(d["chain_compression_a"], 3, labels=["baja", "media", "alta"])
    rows = []
    for (kind, c), g in d.groupby(["kind", "compression"], observed=True):
        gr = g[g["light"] == "verde"]
        rows.append({"kind": kind, "compression": c, "n_cases": len(g), "n_green": len(gr),
                     "n_wrong_green": int((~gr["correct"].astype(bool)).sum()),
                     "false_green": float((~gr["correct"].astype(bool)).mean()) if len(gr) else float("nan"),
                     "n_no_cert": int((~g["in_domain"].astype(bool)).sum())})
    return pd.DataFrame(rows)


def evaluate_h15(df: pd.DataFrame, n_boot: int = h13.N_BOOT, seed: int = h13.BOOT_SEED) -> dict:
    c, k = df[df["variant"] == "chain"], df[df["variant"] == "clean"]
    body, slot = c[c["kind"] == bio.BODY], c[c["kind"] == bio.SLOT]
    h15c = {"body": h13.calibration_verdict(body, n_boot, seed), "slot": h13.calibration_verdict(slot, n_boot, seed)}
    h15c["verdict"] = h13._combine(v["verdict"] for v in h15c.values())
    h15e = {kind: h13.false_green_verdict(_as_primary(c[c["kind"] == kind], "otsu"), n_boot, seed)
            for kind in bio.KINDS}
    clean_ref = {kind: h13.false_green_verdict(k[k["kind"] == kind], n_boot, seed) for kind in bio.KINDS}
    return {"h15a": h13.false_green_verdict(body, n_boot, seed), "h15b": h13.false_green_verdict(slot, n_boot, seed),
            "h15c": h15c, "h15d": {"shift": paired_shift(df), "retention": retention(df), "clean_reference": clean_ref},
            "h15e": h15e}
