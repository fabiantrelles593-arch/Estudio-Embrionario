"""H26: replicación con el instrumento congelado de H20 (cuerpo) y H25 (ventrículos) en volúmenes nuevos.

Aplica la base aprobada ``docs/h26/PREREGISTRO_H26_BORRADOR.md`` y las reglas S-1 a S-3 de
``docs/REGLAS_PREREGISTRO.md``. **No ajusta nada:** las redes, las reglas, las guardias y las envolventes son las de los
congelados de H20 y H25, comprobados por su SHA-256. Este módulo solo añade:

* ``g0_datos``: las comprobaciones de los datos nuevos que se hacen con archivos, antes de abrir ninguna imagen
  (columnas, archivos presentes, condiciones de uso por escrito y sin solapamiento con el conjunto público).
* ``separation_s1``: la separación verde / no verde con la evaluabilidad por fallos de S-1.
* ``evaluate_body`` y ``evaluate_ventricle``: R1a–R1g y V1a–V1g.

Solo investigación con datos animales; sin uso clínico.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import h18, h24

FROZEN = {
    "body": {"file": "results/h20/h20_frozen.json",
             "sha256": "66d7ffcf3d9d8397aeefe208aa480deb870d6b616c5cc01c24f8abae7250804e"},
    "ventricle": {"file": "results/h25/h25_frozen.json",
                  "sha256": "91ba4f3dcff06281934e9e07207581db8b8e3c91167202869ac79c9737322f76"},
}
BODY_TOLERANCE = h18.TOLERANCE          # |error de volumen| > 10 % es fallo (H20b)
SEP_MIN_EACH = 5                        # ≥ 5 verdes y ≥ 5 no verdes (como H20d–H25d)
SEP_MIN_FAILS = 10                      # S-1: ≥ 10 fallos en total
SEP_MIN_FAILS_EACH = 1                  # S-1: ≥ 1 fallo en cada grupo
SEP_NO_MAX = 0.05                       # «no separa» si el límite superior ≤ 5 puntos
SEED_G0 = 20261128
N_G0 = 5
MANIFEST_COLUMNS = ("image", "label", "label_value", "embryo_id", "structure")


# --- Fallos -------------------------------------------------------------------------------------------
def body_bad(df: pd.DataFrame) -> np.ndarray:
    """Fallo de cuerpo: |error de volumen| > 10 % (la definición de H20b)."""
    return (df["rel_error_volume"].abs() > BODY_TOLERANCE).to_numpy()


def ventricle_bad(df: pd.DataFrame) -> np.ndarray:
    """Fallo de ventrículo: e_b > 0,5 vóxeles; un e_b no calculable cuenta como fallo (la definición de H24/H25)."""
    return h24.bad(df)


# --- Separación con S-1 -------------------------------------------------------------------------------
def _diff_ci(embryo: np.ndarray, green: np.ndarray, bad: np.ndarray, n_boot: int, seed: int) -> list[float]:
    """IC 95 % por percentiles de Δ = fallos entre no verdes − fallos entre verdes, remuestreando embriones (S-3)."""
    rng = np.random.default_rng(seed)
    emb = pd.unique(embryo)
    idx = {e: np.flatnonzero(embryo == e) for e in emb}
    vals = []
    for _ in range(n_boot):
        rows = np.concatenate([idx[e] for e in rng.choice(emb, len(emb))])
        g, b = green[rows], bad[rows]
        if g.any() and (~g).any():
            vals.append(float(b[~g].mean() - b[g].mean()))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))] if vals else [math.nan, math.nan]


def separation_s1(lit: pd.DataFrame, bad: np.ndarray, n_boot: int = h18.N_BOOT, seed: int = h18.SEED) -> dict:
    """R1d / V1d con S-1: evaluable solo con ≥ 5 verdes, ≥ 5 no verdes, ≥ 10 fallos y ≥ 1 fallo en cada grupo."""
    bad = np.asarray(bad, bool)
    g = (lit["light"] == "verde").to_numpy()
    out = {"n_green": int(g.sum()), "n_not_green": int((~g).sum()), "n_fail": int(bad.sum()),
           "n_fail_green": int(bad[g].sum()), "n_fail_not_green": int(bad[~g].sum())}
    reasons = []
    if out["n_green"] < SEP_MIN_EACH or out["n_not_green"] < SEP_MIN_EACH:
        reasons.append("menos de 5 verdes o de 5 no verdes")
    if out["n_fail"] < SEP_MIN_FAILS:
        reasons.append("menos de 10 fallos (S-1)")
    if out["n_fail_green"] < SEP_MIN_FAILS_EACH or out["n_fail_not_green"] < SEP_MIN_FAILS_EACH:
        reasons.append("algún grupo sin fallos (S-1)")
    if g.any() and (~g).any():
        out["fail_green"] = float(bad[g].mean())
        out["fail_not_green"] = float(bad[~g].mean())
        out["difference"] = out["fail_not_green"] - out["fail_green"]
    if reasons:
        return {**out, "ci": None, "verdict": "no evaluable", "reasons": reasons}
    ci = _diff_ci(lit["embryo_id"].to_numpy(), g, bad, n_boot, seed)
    if not all(math.isfinite(x) for x in ci):
        return {**out, "ci": ci, "verdict": "no evaluable", "reasons": ["IC no calculable"]}
    verdict = "separa" if ci[0] > 0 else ("no separa" if ci[1] <= SEP_NO_MAX else "no concluyente")
    return {**out, "ci": ci, "verdict": verdict, "reasons": []}


# --- Evaluación ---------------------------------------------------------------------------------------
def _common(lit: pd.DataFrame, bad: np.ndarray, free_bad: np.ndarray) -> dict:
    g = lit["light"] == "verde"
    free = (lit["light_without_guard"] == "verde").to_numpy()
    return {
        "a": {"green_fraction": float(g.mean()) if len(lit) else math.nan,
              "lights": lit["light"].value_counts().to_dict()},
        "e": {"in_domain": float(lit["in_domain"].mean()) if len(lit) else math.nan,
              "green_without_guard": int(free.sum()), "green_without_guard_bad": int(free_bad[free].sum())},
        "g": {"fail_all": float(np.mean(bad)) if len(lit) else math.nan},
    }


def evaluate_body(lit: pd.DataFrame, n_boot: int = h18.N_BOOT, seed: int = h18.SEED) -> dict:
    """R1b y R1d (primarias); R1a, R1c, R1e y R1g (descriptivas)."""
    bad = body_bad(lit)
    err = lit["rel_error_volume"].abs()
    c = _common(lit, bad, bad)
    contrast_np = int((~np.isfinite(lit["snr_hat"].to_numpy(float))).sum()) if "snr_hat" in lit else None
    return {
        "n_cases": int(len(lit)), "n_embryos": int(lit["embryo_id"].nunique()),
        "r1b": h18.green_failure(lit, n_boot, seed),
        "r1d": separation_s1(lit, bad, n_boot, seed),
        "r1a": c["a"],
        "r1c": {"abs_error_median": float(err.median()), "ok10": float((err <= BODY_TOLERANCE).mean()),
                "dice_median": float(lit["dice"].median())},
        "r1e": {**c["e"], "guard_not_computable": contrast_np},
        "r1g": c["g"],
    }


def evaluate_ventricle(lit: pd.DataFrame, n_boot: int = h18.N_BOOT, seed: int = h18.SEED) -> dict:
    """V1b y V1d (confirmatorias de ventrículo); V1a, V1c, V1e y V1g (descriptivas)."""
    bad = ventricle_bad(lit)
    eb = lit["e_b"].astype(float)
    c = _common(lit, bad, bad)
    return {
        "n_cases": int(len(lit)), "n_embryos": int(lit["embryo_id"].nunique()),
        "v1b": h24.green_failure(lit, n_boot, seed),
        "v1d": separation_s1(lit, bad, n_boot, seed),
        "v1a": c["a"],
        "v1c": {"e_b_median": float(eb.median()), "ok_half_voxel": float((eb <= h24.TOL_VOXELS).mean()),
                "dice_median": float(lit["dice"].median())},
        "v1e": c["e"],
        "v1g": c["g"],
    }


# --- G0-datos -----------------------------------------------------------------------------------------
def g0_datos(manifest: pd.DataFrame, new_sha: dict, public_sha: dict, public_embryos: set,
             terms_sha: str | None, missing: list[str]) -> dict:
    """Comprobaciones con archivos, antes de abrir ninguna imagen.

    ``new_sha`` y ``public_sha``: archivo → SHA-256 de las imágenes nuevas y de las públicas. ``terms_sha``: huella del
    documento de condiciones de uso (None si no se dio). ``missing``: archivos del manifiesto que no existen.
    Un volumen cuya huella o embrión coincida con el conjunto público se excluye y se informa."""
    cols = [c for c in MANIFEST_COLUMNS if c not in manifest.columns]
    pub_hashes = set(public_sha.values())
    dup_hash = sorted(f for f, s in new_sha.items() if s in pub_hashes)
    dup_emb = sorted(set(manifest["embryo_id"].astype(str)) & {str(e) for e in public_embryos}) if not cols else []
    excluded = set(dup_hash)
    if not cols:
        excluded |= set(manifest.loc[manifest["embryo_id"].astype(str).isin(dup_emb), "image"])
    kept = manifest[~manifest["image"].isin(excluded)] if not cols else manifest.iloc[0:0]
    by = kept.groupby("structure")["embryo_id"].agg(["size", "nunique"]).to_dict("index") if len(kept) else {}
    checks = {
        "columns": not cols,
        "files_present": not missing,
        "terms_of_use": bool(terms_sha),
        "has_body": "body" in by,
    }
    return {"passed": all(checks.values()), "checks": checks, "missing_columns": cols, "missing_files": missing,
            "terms_sha256": terms_sha, "excluded_same_file": dup_hash, "excluded_same_embryo": dup_emb,
            "n_kept": int(len(kept)),
            "counts": {k: {"volumes": int(v["size"]), "embryos": int(v["nunique"])} for k, v in by.items()}}
