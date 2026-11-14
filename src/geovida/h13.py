"""H13 — biometría fetal temprana simulada con certificado de incertidumbre (Programa B).

Solo investigación y educación. Imágenes sintéticas; sin datos de personas; sin uso clínico.

Flujo (el mismo orden que H12, con commits entre pasos):
  piloto (semilla propia) → preregistro → calibración (semilla propia) → congelar modelos →
  confirmación (semilla propia) → análisis con las reglas escritas de antemano.

Todas las reglas de veredicto de este archivo están en ``docs/PREREGISTRO_H13.md``.
"""
from __future__ import annotations

import math
import multiprocessing as mp

import numpy as np
import pandas as pd

from . import biometry as bio
from . import dating

H13_PILOT_SEED = 20261211
H13_CAL_SEED = 20261212
H13_CONF_SEED = 20261213
BOOT_SEED = 20261214
N_BOOT = 2000

PRIMARY_SEGMENTER = "smoothed_otsu"

# Cuadrícula de calibración: n = píxeles a lo largo de la magnitud medida; f = ancho (FWHM) de la
# función de dispersión del punto en píxeles.
CAL_GRID = {
    bio.BODY: {"n": (50.0, 80.0, 130.0, 210.0, 300.0), "f": (1.0, 2.0, 3.5, 5.0)},
    bio.SLOT: {"n": (10.0, 15.0, 22.0, 33.0, 50.0), "f": (1.0, 1.5, 2.2, 3.3, 5.0)},
}
BODY_SIZE_RANGE_MM = (20.0, 90.0)      # dentro del rango de la fórmula de datación (15–95 mm)
SLOT_SIZE_RANGE_MM = (1.5, 4.5)        # alrededor del umbral ilustrativo de 3.0 mm
OUT_REGIONS = ("n_high", "n_low", "f_high", "f_low")

FALSE_GREEN_MAX = 0.10
GUARD_LEAK_MAX = 0.05
ECE_MAX = 0.10
MIN_GREEN = 30
MIN_OUT = 100
MIN_ECE_N = 200

# Repetibilidad humana publicada de la NT (PubMed 10895448): desviación típica de las diferencias entre
# dos mediciones 0.35 mm (mismo operador) y 0.56 mm (operadores distintos). Una sola medición tiene
# error de desviación típica diferencia/√2.
HUMAN_SD_INTRA_MM = 0.35 / math.sqrt(2.0)
HUMAN_SD_INTER_MM = 0.56 / math.sqrt(2.0)


# --- diseño -----------------------------------------------------------------------------------

def calibration_cases(kind: str, reps: int, base_seed: int, grid: dict | None = None) -> list[dict]:
    g = (grid or CAL_GRID)[kind]
    ki = bio.KINDS.index(kind)
    return [{"kind": kind, "n": float(n), "fwhm_px": float(f), "rep": r, "seed": [base_seed, ki, i, j, r]}
            for i, n in enumerate(g["n"]) for j, f in enumerate(g["f"]) for r in range(reps)]


def confirmation_cases(n_in: int, n_out: int, base_seed: int, grid: dict | None = None) -> list[dict]:
    """``n_in`` casos por tipo con (n, fwhm) al azar DENTRO de la caja calibrada (log-uniforme, fuera de
    los nodos) y ``n_out`` por tipo claramente FUERA (≥ 1.2 veces más allá del borde), repartidos en 4 regiones."""
    grid = grid or CAL_GRID
    cases, idx = [], 0
    for ki, kind in enumerate(bio.KINDS):
        g = grid[kind]
        n_lo, n_hi, f_lo, f_hi = g["n"][0], g["n"][-1], g["f"][0], g["f"][-1]
        s_lo, s_hi = BODY_SIZE_RANGE_MM if kind == bio.BODY else SLOT_SIZE_RANGE_MM
        rng = np.random.default_rng([base_seed, ki, 0])

        def logu(lo, hi):
            return float(np.exp(rng.uniform(math.log(lo), math.log(hi))))

        regions = ["in"] * n_in + [OUT_REGIONS[i % len(OUT_REGIONS)] for i in range(n_out)]
        for r_i, region in enumerate(regions):
            size = float(rng.uniform(s_lo, s_hi))
            n, f = logu(n_lo, n_hi), logu(f_lo, f_hi)
            if region == "n_high":
                n = logu(1.2 * n_hi, 1.5 * n_hi)
            elif region == "n_low":
                n = logu(n_lo / 2.0, n_lo / 1.2)
            elif region == "f_high":
                f = logu(1.2 * f_hi, 2.0 * f_hi)
            elif region == "f_low":
                f = logu(f_lo / 2.0, f_lo / 1.2)
            cases.append({"idx": idx, "kind": kind, "region": region, "size_mm": size, "n": n,
                          "fwhm_px": f, "seed": [base_seed, ki, 1, r_i]})
            idx += 1
    return cases


# --- ejecución --------------------------------------------------------------------------------

def _map(fn, items, n_jobs, initializer=None, initargs=()):
    if n_jobs <= 1:
        if initializer:
            initializer(*initargs)
        return [fn(x) for x in items]
    with mp.get_context("fork").Pool(n_jobs, initializer=initializer, initargs=initargs) as pool:
        return pool.map(fn, items, chunksize=8)


def _cal_worker(case):
    # píxel = 1 mm en la calibración: el error en píxeles no depende de la escala
    r = bio.run_case(case["kind"], case["n"], case["n"], case["fwhm_px"], case["seed"])
    return [{"kind": case["kind"], "segmenter": s, "n": case["n"], "fwhm_px": case["fwhm_px"],
             "rep": case["rep"], "err_px": m - r["truth_mm"]} for s, m in r["measured_mm"].items()]


def run_calibration(reps: int, base_seed: int, n_jobs: int = 1, grid: dict | None = None,
                    kinds=bio.KINDS) -> pd.DataFrame:
    cases = [c for k in kinds for c in calibration_cases(k, reps, base_seed, grid)]
    rows = [row for chunk in _map(_cal_worker, cases, n_jobs) for row in chunk]
    return pd.DataFrame(rows)


def fit_models(df: pd.DataFrame, min_usable_rate: float | None = None) -> dict:
    return {f"{k}|{s}": bio.ErrorModel.from_calibration(df, k, s, min_usable_rate)
            for k in df["kind"].unique() for s in bio.SEGMENTERS}


class ClampedModel:
    """Contrafactual SIN guardia: lleva (n, fwhm) al borde de la caja y predice ahí. Solo para medir qué
    habría pasado si el modelo extrapolara; nunca se usa para certificar."""

    def __init__(self, model: bio.ErrorModel):
        self.m = model

    def predict(self, n, fwhm_px):
        if not (n > 0 and fwhm_px > 0):
            return None
        m = self.m
        return m.predict(min(max(n, m.n_nodes[0]), m.n_nodes[-1]), min(max(fwhm_px, m.f_nodes[0]), m.f_nodes[-1]))


def score_body(truth_mm: float, measured_mm: float, tolerance_days: float = dating.DEFAULT_TOLERANCE_DAYS) -> dict:
    """Error de edad que causa la medida, calculado con la verdad: GA(medido) − GA(verdadero), en días."""
    if not measured_mm > 0:
        return {"ga_err_days": float("nan"), "correct": False}
    err = dating.ga_days_intergrowth(measured_mm) - dating.ga_days_intergrowth(truth_mm)
    return {"ga_err_days": float(err), "correct": bool(abs(err) <= tolerance_days)}


def score_slot(truth_mm: float, measured_mm: float, threshold_mm: float = bio.SLOT_THRESHOLD_MM) -> dict:
    """¿El lado del umbral del valor medido es el del valor verdadero? (en el umbral cuenta como «arriba»)."""
    return {"ga_err_days": float("nan"),
            "correct": bool((truth_mm >= threshold_mm) == (measured_mm >= threshold_mm))}


_MODELS: dict = {}


def _init_models(models):
    _MODELS.clear()
    _MODELS.update(models)


def _certify(kind, measured_mm, h, f, model):
    return (bio.certify_body if kind == bio.BODY else bio.certify_slot)(measured_mm, h, f, model)


def _conf_worker(case):
    kind = case["kind"]
    r = bio.run_case(kind, case["size_mm"], case["n"], case["fwhm_px"], case["seed"], chain=case.get("chain"))
    chain_cols = {f"chain_{k}": v for k, v in case["chain"].items()} if case.get("chain") else {}
    rows = []
    for seg, meas in r["measured_mm"].items():
        model = _MODELS[f"{kind}|{seg}"]
        h, f = r["h_mm"], case["fwhm_px"]
        cert, cert_c = _certify(kind, meas, h, f, model), _certify(kind, meas, h, f, ClampedModel(model))
        score = (score_body if kind == bio.BODY else score_slot)(r["truth_mm"], meas)
        dom = bool(cert["in_domain"])
        rows.append({
            "idx": case["idx"], "kind": kind, "segmenter": seg, "region": case["region"],
            "n_nominal": case["n"], "fwhm_px": f, "truth_mm": r["truth_mm"], "h_mm": h, "measured_mm": meas,
            "in_domain": dom, "light": cert["light"],
            "p": cert.get("p_within_tolerance", cert.get("p_same_side", float("nan"))) if dom else float("nan"),
            "bias_mm": cert["bias_px"] * h if dom else float("nan"),
            "sd_mm": cert["sd_px"] * h if dom else float("nan"),
            "measurement_share": cert.get("measurement_share", float("nan")) if dom else float("nan"),
            "correct": score["correct"], "ga_err_days": score["ga_err_days"],
            "light_clamped": cert_c["light"],
            "p_clamped": cert_c.get("p_within_tolerance", cert_c.get("p_same_side", float("nan")))
            if cert_c["in_domain"] else float("nan"),
            **chain_cols,
        })
    return rows


def run_confirmation(cases: list[dict], models: dict, n_jobs: int = 1) -> pd.DataFrame:
    chunks = _map(_conf_worker, cases, n_jobs, initializer=_init_models, initargs=(models,))
    return pd.DataFrame([row for chunk in chunks for row in chunk])


# --- análisis: reglas fijas de antemano -------------------------------------------------------

def _primary_in(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df["segmenter"] == PRIMARY_SEGMENTER) & (df["region"] == "in")]


def _combine(verdicts) -> str:
    verdicts = list(verdicts)
    if "no apoyada" in verdicts:
        return "no apoyada"
    if "no evaluable" in verdicts:
        return "no evaluable"
    return "apoyada"


def false_green_verdict(df: pd.DataFrame, n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> dict:
    """H13a/H13b: entre las luces verdes (segmentador primario, dentro de la caja) la fracción de aciertos
    fallidos debe ser ≤ 10 %.  Apoyada: límite superior del IC 95 % ≤ 10 %.  No apoyada: límite inferior > 10 %.
    No concluyente: el intervalo contiene el 10 %.  No evaluable: < 30 verdes."""
    d = _primary_in(df)
    green = (d["light"] == "verde").to_numpy()
    wrong = ~d["correct"].to_numpy(dtype=bool)
    n_green = int(green.sum())
    out = {"n_cases": int(len(d)), "n_green": n_green,
           "false_green": float((green & wrong).sum() / n_green) if n_green else float("nan"),
           "ci": None, "verdict": "no evaluable"}
    if n_green < MIN_GREEN:
        return out
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), size=(n_boot, len(d)))
    ng = green[idx].sum(axis=1)
    fr = (green & wrong)[idx].sum(axis=1) / np.maximum(ng, 1)
    lo, hi = np.percentile(fr, [2.5, 97.5])
    out["ci"] = (float(lo), float(hi))
    out["verdict"] = ("apoyada" if hi <= FALSE_GREEN_MAX else
                      "no apoyada" if lo > FALSE_GREEN_MAX else "no concluyente")
    return out


def calibration_verdict(df: pd.DataFrame, n_boot: int = 0, seed: int = BOOT_SEED) -> dict:
    """H13c: error de calibración esperado (10 cubos) de la probabilidad del certificado, con todos los casos
    del segmentador primario dentro de la caja y con certificado.  Apoyada si ECE ≤ 0.10; no evaluable si < 200."""
    d = _primary_in(df)
    d = d[d["in_domain"].astype(bool)]
    out = {"n": int(len(d)), "ece": float("nan"), "ece_ci": None, "verdict": "no evaluable"}
    if len(d) < MIN_ECE_N:
        return out
    p, y = d["p"].to_numpy(float), d["correct"].to_numpy(float)
    out["ece"] = bio.expected_calibration_error(p, y)
    if n_boot > 0:
        rng = np.random.default_rng(seed)
        vals = [bio.expected_calibration_error(p[i], y[i])
                for i in rng.integers(0, len(d), size=(n_boot, len(d)))]
        out["ece_ci"] = (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))
    out["verdict"] = "apoyada" if out["ece"] <= ECE_MAX else "no apoyada"
    return out


def guard_verdict(df: pd.DataFrame, n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> dict:
    """H13d: con (n, fwhm) claramente fuera de la caja calibrada, la guardia debe negarse en casi todos los casos.

    El ``n`` del certificado sale de la medida (medida / píxel), no de la verdad, así que cerca del borde algo
    puede filtrarse y «cero verdes» no se puede garantizar. Criterio: tasa de fuga (fracción de casos fuera de la
    caja con luz verde) ≤ 5 %.  Apoyada: límite superior del IC 95 % ≤ 5 %.  No apoyada: límite inferior > 5 %.
    No concluyente: el intervalo contiene el 5 %.  No evaluable: < 100 casos fuera.
    Se informa, sin criterio, qué tan acertados fueron los verdes filtrados y cuántos falsos verdes habría tenido
    un modelo que extrapola al borde en vez de negarse."""
    d = df[(df["segmenter"] == PRIMARY_SEGMENTER) & (df["region"] != "in")]
    green = (d["light"] == "verde").to_numpy()
    leaked = d[d["light"] == "verde"]
    gc = d[d["light_clamped"] == "verde"]
    out = {"n_out": int(len(d)), "leak_n_green": int(green.sum()),
           "leak_rate": float(green.mean()) if len(d) else float("nan"), "leak_ci": None,
           "leak_false_green": float((~leaked["correct"].astype(bool)).mean()) if len(leaked) else float("nan"),
           "clamped_n_green": int(len(gc)),
           "clamped_false_green": float((~gc["correct"].astype(bool)).mean()) if len(gc) else float("nan"),
           "verdict": "no evaluable"}
    if len(d) < MIN_OUT:
        return out
    rng = np.random.default_rng(seed)
    rates = green[rng.integers(0, len(d), size=(n_boot, len(d)))].mean(axis=1)
    lo, hi = np.percentile(rates, [2.5, 97.5])
    out["leak_ci"] = (float(lo), float(hi))
    out["verdict"] = ("apoyada" if hi <= GUARD_LEAK_MAX else "no apoyada" if lo > GUARD_LEAK_MAX else "no concluyente")
    return out


def _error_stats(d: pd.DataFrame) -> dict:
    err = (d["measured_mm"] - d["bias_mm"] - d["truth_mm"]).to_numpy(float)
    out = {"n": int(len(d))}
    if len(d):
        a = np.abs(err)
        out.update(median_abs_error_mm=float(np.median(a)), p95_abs_error_mm=float(np.percentile(a, 95)),
                   sd_mm=float(err.std(ddof=1)) if len(d) > 1 else float("nan"),
                   share_within_intra=float((a <= HUMAN_SD_INTRA_MM).mean()),
                   share_within_inter=float((a <= HUMAN_SD_INTER_MM).mean()))
    return out


def human_yardstick(df: pd.DataFrame) -> dict:
    """H13e (descriptiva): error de la NT simulada tras corregir el sesgo modelado, en mm, frente a la
    repetibilidad humana publicada: para todos los casos con certificado y solo para los verdes. No dice que
    supere a un operador: la tarea, la imagen y el píxel son otros."""
    d = _primary_in(df[df["kind"] == bio.SLOT])
    d = d[d["in_domain"].astype(bool)]
    return {"human_sd_intra_mm": HUMAN_SD_INTRA_MM, "human_sd_inter_mm": HUMAN_SD_INTER_MM,
            "all": _error_stats(d), "green": _error_stats(d[d["light"] == "verde"])}


def measurement_share_summary(df: pd.DataFrame) -> dict:
    """H13f (descriptiva): fracción de la varianza de la datación que pone la medida (el resto es la
    variación biológica de la fórmula), entre los certificados de CRL con modelo."""
    d = _primary_in(df[df["kind"] == bio.BODY])
    s = d[d["in_domain"].astype(bool)]["measurement_share"].dropna().to_numpy(float)
    out = {"n": int(len(s))}
    if len(s):
        out.update(median=float(np.median(s)), p90=float(np.percentile(s, 90)), share_over_half=float((s > 0.5).mean()))
    return out


def evaluate_h13(df: pd.DataFrame, n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> dict:
    body, slot = df[df["kind"] == bio.BODY], df[df["kind"] == bio.SLOT]
    h13c = {"body": calibration_verdict(body, n_boot, seed), "slot": calibration_verdict(slot, n_boot, seed)}
    h13c["verdict"] = _combine(v["verdict"] for v in h13c.values())
    h13d = {"body": guard_verdict(body, n_boot, seed), "slot": guard_verdict(slot, n_boot, seed)}
    h13d["verdict"] = _combine(v["verdict"] for v in h13d.values())
    return {"h13a": false_green_verdict(body, n_boot, seed), "h13b": false_green_verdict(slot, n_boot, seed),
            "h13c": h13c, "h13d": h13d, "h13e": human_yardstick(df), "h13f": measurement_share_summary(df)}
