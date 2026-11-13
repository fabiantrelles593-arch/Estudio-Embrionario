"""H16 — ¿puede el certificado enterarse, solo con la imagen, de que pasó por una cadena? (solo simulación)

Reglas en ``docs/PREREGISTRO_H16.md``. Se usan los modelos congelados de H14 como línea base (sin recalibrar) y, encima, la guardia de
cadena de ``geovida.chainguard``: se ajusta con un conjunto de entrenamiento de la familia de cadena A (más imágenes sin cadena) y se
evalúa en conjuntos nuevos de la familia A y de la familia B, que la guardia no vio. El certificado ajustado recibe solo el valor medido,
el tamaño de píxel, el desenfoque declarado y dos índices calculados de la propia imagen: ni la verdad ni los parámetros de la cadena.
"""
from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd

from . import biometry as bio
from . import chainguard as cg
from . import h13, printchain

H16_PILOT_SEED = 20261220
H16_TRAIN_SEED = 20261221
H16_CONF_A_SEED = 20261222
H16_CONF_B_SEED = 20261223
CHAIN_STREAM = 7
FAMILIES = ("A", "B")
PRIMARY = h13.PRIMARY_SEGMENTER

RETENTION_MIN = 0.5            # H16d: verdes correctos con la guardia / verdes correctos del semáforo base sobre la imagen limpia
CLEAN_COST_MIN = 0.90          # H16f: verdes con la guardia / verdes del semáforo base, sobre imágenes sin cadena
MIN_REF_GREEN = h13.MIN_GREEN

_SAMPLERS = {"A": printchain.sample_chain, "B": printchain.sample_chain_b}


# --- diseño -----------------------------------------------------------------------------------

def cases(n_in: int, base_seed: int, family: str) -> list[dict]:
    """Los casos de H13 (solo dentro de la caja calibrada) con la cadena de la familia indicada fijada por caso."""
    if family not in _SAMPLERS:
        raise ValueError(f"familia desconocida: {family!r}; opciones: {FAMILIES}")
    cs = h13.confirmation_cases(n_in, 0, base_seed)
    for c in cs:
        c["chain"] = _SAMPLERS[family](np.random.default_rng([base_seed, CHAIN_STREAM, c["idx"]]))
        c["family"] = family
    return cs


# --- ejecución --------------------------------------------------------------------------------

_MODELS: dict = {}


def _init_models(models):
    _MODELS.clear()
    _MODELS.update(models)


def _worker(case):
    kind, h, f = case["kind"], case["size_mm"] / case["n"], case["fwhm_px"]
    ph = bio.make_body(case["size_mm"]) if kind == bio.BODY else bio.make_slot(case["size_mm"])
    img = bio.render2d(ph, bio.spec_for(h, f, bio.LOOKS), np.random.default_rng(case["seed"])).image
    model = _MODELS[f"{kind}|{PRIMARY}"]
    chain_cols = {f"chain_{k}": v for k, v in case["chain"].items() if k != "family"}
    rows = []
    for variant, im in (("clean", img), ("chain", printchain.apply_chain(img, case["chain"]))):
        idx = cg.image_indices(im)
        meas = bio.measure(kind, bio.segment2d(PRIMARY, im, h), h)
        cert = h13._certify(kind, meas, h, f, model)
        score = (h13.score_body if kind == bio.BODY else h13.score_slot)(case["size_mm"], meas)
        dom = bool(cert["in_domain"])
        rows.append({
            "idx": case["idx"], "kind": kind, "family": case["family"], "variant": variant, "region": case["region"],
            "segmenter": PRIMARY, "truth_mm": float(case["size_mm"]), "h_mm": h, "n_nominal": case["n"], "fwhm_px": f,
            "measured_mm": meas, "ln_cv": idx["ln_cv"], "skew": idx["skew"], "in_domain": dom, "light": cert["light"],
            "p": cert.get("p_within_tolerance", cert.get("p_same_side", math.nan)) if dom else math.nan,
            "correct": score["correct"],
            "resid_px": (meas - case["size_mm"]) / h - cert["bias_px"] if dom else math.nan,
            "sd_clean_px": cert["sd_px"] if dom else math.nan,
            **(chain_cols if variant == "chain" else {}),
        })
    return rows


def run(case_list: list[dict], models: dict, n_jobs: int = 1) -> pd.DataFrame:
    """Mide cada caso sin y con la cadena (mismo render): una fila por caso y variante."""
    chunks = h13._map(_worker, case_list, n_jobs, initializer=_init_models, initargs=(models,))
    return pd.DataFrame([row for chunk in chunks for row in chunk])


# --- entrenamiento de la guardia --------------------------------------------------------------

def training_table(df: pd.DataFrame) -> pd.DataFrame:
    """Filas utilizables para ajustar la guardia: dentro de la caja, con certificado base e índices finitos.

    La variante sin cadena entra como régimen ``clean`` y la variante con cadena como régimen ``chain``."""
    d = df[(df["region"] == "in") & df["in_domain"].astype(bool)].dropna(subset=["ln_cv", "skew", "resid_px", "sd_clean_px"])
    t = d.assign(regime=np.where(d["variant"] == "clean", "clean", "chain"))
    return t[["idx", "kind", "family", "regime", "ln_cv", "skew", "resid_px", "sd_clean_px"]]


def fit(train: pd.DataFrame, **kw) -> dict:
    return {k: cg.fit_chain_model(train, k, **kw) for k in bio.KINDS if (train["kind"] == k).any()}


def chain_models_to_json(models: dict, meta: dict | None = None) -> str:
    return json.dumps({"meta": meta or {}, "models": {k: m.to_dict() for k, m in models.items()}}, indent=2, sort_keys=True)


def chain_models_from_json(text: str) -> dict:
    return {k: cg.ChainModel.from_dict(v) for k, v in json.loads(text)["models"].items()}


def apply_chain_aware(df: pd.DataFrame, base_models: dict, chain_models: dict) -> pd.DataFrame:
    """Añade el certificado con la guardia de cadena (``light_cg``, ``p_cg``, ``in_domain_cg``, ``chain_regime``, ``chain_bin``)."""
    light, dom, p, reg, bn = [], [], [], [], []
    for r in df.itertuples(index=False):
        cert = cg.certify(r.kind, r.measured_mm, r.h_mm, r.fwhm_px, base_models[f"{r.kind}|{r.segmenter}"], chain_models[r.kind],
                          {"ln_cv": r.ln_cv, "skew": r.skew})
        ok = bool(cert["in_domain"])
        light.append(cert["light"])
        dom.append(ok)
        p.append(cert.get("p_within_tolerance", cert.get("p_same_side", math.nan)) if ok else math.nan)
        reg.append(cert.get("chain_regime", "") if ok else "")
        bn.append(cert.get("chain_bin", -1) if ok else -1)
    return df.assign(light_cg=light, in_domain_cg=dom, p_cg=p, chain_regime=reg, chain_bin=bn)


# --- análisis: reglas fijas de antemano -------------------------------------------------------

def _view(d: pd.DataFrame, *, guarded: bool) -> pd.DataFrame:
    """Vista con las columnas que esperan las reglas de H13 (``light``, ``in_domain``, ``p``) tomadas del certificado base o del ajustado."""
    d = d[(d["segmenter"] == PRIMARY) & (d["region"] == "in")]
    return pd.DataFrame({"kind": d["kind"], "segmenter": h13.PRIMARY_SEGMENTER, "region": "in",
                         "light": d["light_cg"] if guarded else d["light"],
                         "in_domain": d["in_domain_cg"] if guarded else d["in_domain"],
                         "p": d["p_cg"] if guarded else d["p"], "correct": d["correct"]})


def retention_verdict(df: pd.DataFrame, kind: str, n_boot: int = h13.N_BOOT, seed: int = h13.BOOT_SEED) -> dict:
    """H16d: verdes correctos de la guardia sobre la imagen con cadena / verdes correctos del semáforo base sobre la imagen limpia,
    mismos casos. Apoyada: límite inferior del IC 95 % ≥ 0.5.  No apoyada: límite superior < 0.5.  No concluyente: el intervalo contiene
    0.5.  No evaluable: < 30 verdes correctos de referencia."""
    d = df[(df["segmenter"] == PRIMARY) & (df["region"] == "in") & (df["kind"] == kind)]
    chain, clean = d[d["variant"] == "chain"].set_index("idx"), d[d["variant"] == "clean"].set_index("idx")
    idx = chain.index.intersection(clean.index)
    num = ((chain.loc[idx, "light_cg"] == "verde") & chain.loc[idx, "correct"].astype(bool)).to_numpy(int)
    den = ((clean.loc[idx, "light"] == "verde") & clean.loc[idx, "correct"].astype(bool)).to_numpy(int)
    out = {"n_cases": int(len(idx)), "n_ref_green_correct": int(den.sum()), "n_guard_green_correct": int(num.sum()),
           "ratio": float(num.sum() / den.sum()) if den.sum() else math.nan, "ci": None, "verdict": "no evaluable"}
    if den.sum() < MIN_REF_GREEN:
        return out
    rng = np.random.default_rng(seed)
    ix = rng.integers(0, len(idx), size=(n_boot, len(idx)))
    ratios = num[ix].sum(axis=1) / np.maximum(den[ix].sum(axis=1), 1)
    lo, hi = np.percentile(ratios, [2.5, 97.5])
    out["ci"] = (float(lo), float(hi))
    out["verdict"] = "apoyada" if lo >= RETENTION_MIN else "no apoyada" if hi < RETENTION_MIN else "no concluyente"
    return out


def clean_cost(df: pd.DataFrame, kind: str) -> dict:
    """H16f: sobre imágenes sin cadena, verdes de la guardia / verdes del semáforo base (mismos casos)."""
    d = df[(df["segmenter"] == PRIMARY) & (df["region"] == "in") & (df["kind"] == kind) & (df["variant"] == "clean")]
    gb, gc = int((d["light"] == "verde").sum()), int((d["light_cg"] == "verde").sum())
    return {"n_cases": int(len(d)), "green_base": gb, "green_guard": gc, "ratio": gc / gb if gb else math.nan}


def _by_variant(df: pd.DataFrame, variant: str) -> pd.DataFrame:
    return df[df["variant"] == variant]


def evaluate_h16(df_a: pd.DataFrame, df_b: pd.DataFrame, n_boot: int = h13.N_BOOT, seed: int = h13.BOOT_SEED) -> dict:
    """``df_a`` y ``df_b``: salida de ``run`` + ``apply_chain_aware`` para la familia A (vista al ajustar) y la B (nunca vista)."""
    def fg(df, kind, guarded=True):
        return h13.false_green_verdict(_view(_by_variant(df, "chain")[lambda x: x["kind"] == kind], guarded=guarded), n_boot, seed)

    def ece(df, kind):
        return h13.calibration_verdict(_view(_by_variant(df, "chain")[lambda x: x["kind"] == kind], guarded=True), n_boot, seed)

    h16c = {"A": ece(df_a, bio.BODY), "B": ece(df_b, bio.BODY)}
    h16c["verdict"] = h13._combine(v["verdict"] for v in h16c.values())
    h16d = {"A": retention_verdict(df_a, bio.BODY, n_boot, seed), "B": retention_verdict(df_b, bio.BODY, n_boot, seed)}
    h16d["verdict"] = h13._combine(v["verdict"] for v in h16d.values())
    h16e = {"A": fg(df_a, bio.SLOT), "B": fg(df_b, bio.SLOT)}
    h16e["verdict"] = h13._combine(v["verdict"] for v in h16e.values())
    h16f = {}
    for kind in bio.KINDS:
        cost = clean_cost(df_a, kind)
        fgc = h13.false_green_verdict(_view(_by_variant(df_a, "clean")[lambda x: x["kind"] == kind], guarded=True), n_boot, seed)
        ok = bool(cost["ratio"] >= CLEAN_COST_MIN) and fgc["verdict"] != "no apoyada"
        h16f[kind] = {**cost, "false_green": fgc, "verdict": "apoyada" if ok else "no apoyada"}
    h16f["verdict"] = h13._combine(v["verdict"] for v in h16f.values())

    desc = {"baseline_false_green": {}, "out_of_support": {}, "greens": {}}
    for fam, df in (("A", df_a), ("B", df_b)):
        for kind in bio.KINDS:
            ch = _by_variant(df, "chain")[lambda x: x["kind"] == kind]
            ch = ch[(ch["segmenter"] == PRIMARY) & (ch["region"] == "in")]
            desc["baseline_false_green"][f"{fam}|{kind}"] = h13.false_green_verdict(_view(ch, guarded=False), n_boot, seed)
            base_in = ch[ch["in_domain"].astype(bool)]
            desc["out_of_support"][f"{fam}|{kind}"] = {
                "n_base_in_domain": int(len(base_in)),
                "refused_by_guard": int((~base_in["in_domain_cg"].astype(bool)).sum()),
                "share": float((~base_in["in_domain_cg"].astype(bool)).mean()) if len(base_in) else math.nan}
            desc["greens"][f"{fam}|{kind}"] = {"base_on_chain": int((ch["light"] == "verde").sum()),
                                                "guard_on_chain": int((ch["light_cg"] == "verde").sum()),
                                                "base_on_clean": int((_by_variant(df, "clean")[lambda x: x["kind"] == kind]["light"] == "verde").sum())}
    return {"h16a": fg(df_a, bio.BODY), "h16b": fg(df_b, bio.BODY), "h16c": h16c, "h16d": h16d, "h16e": h16e, "h16f": h16f,
            "descriptive": desc}
