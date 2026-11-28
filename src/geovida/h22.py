"""H22 (docs/h22/PREREGISTRO_H22.md): ¿puede la guardia distinguir «fuera de dominio» de «inservible»?

El certificado de v0.4 (``geovida.certificate``) solo tiene una respuesta para una imagen fuera de su dominio
de calibración: quitar el verde y dejar amarillo. En H11 eso dejó en amarillo medidas con errores de 3000 %.
H22 prueba, solo con imágenes sintéticas de verdad conocida, una regla fija para un estado nuevo,
**inservible**: algún índice de dominio (``snr_hat`` o ``edge_width``) cae más de un factor ``FACTOR`` fuera de
la envolvente congelada del perfil declarado.

La regla se fijó mirando solo las envolventes congeladas (``geovida/frozen/h9_frozen.json``), sin datos
medidos: la envolvente de ``snr_hat`` es muy estrecha (8,5–9,7 en ``realistic``), así que una distancia
normalizada por su anchura marcaría casi todo; por eso se usa un factor absoluto en escala logarítmica.

Todo lo que fija un veredicto está en las constantes de este módulo y en ``verdicts``; no se cambia después
de ver los datos.
"""
from __future__ import annotations

import itertools
import math

import numpy as np
import pandas as pd

from .budget import FROZEN_H6, feature_value, p_volume_ok, traffic_light
from .domain import DOMAIN_COLUMNS, domain_observables
from .experiment import Condition
from .phantoms import H21_NAMES

SEED = 20262201
BOOT_SEED = 20262202
SHAPES = H21_NAMES                       # nunca usadas para calibrar el certificado
T_OVER_H = (3.0, 4.0, 6.0, 8.0, 12.0)
ANISOTROPY = (1.0,)
PROFILES = ("realistic", "mild_blur", "mild_noise", "blurry", "noisy",
            "us_compound", "us_raw", "us_atten", "us_coarse")
SEGMENTERS = ("global", "otsu", "smoothed_otsu")
REPS = 30
DECLARED = "realistic"                   # el usuario declara el perfil de calibración, como en H11

FACTOR = 2.0                             # inservible: un índice a más de ×2 fuera de la envolvente
SENSITIVITY_FACTORS = (1.5, 3.0)         # solo descriptivo
GROSS = 0.50                             # fallo grosero: |error de volumen| > 50 %
ACCEPTABLE = 0.10                        # medida aceptable: |error de volumen| ≤ 10 %

H22A_MAX, H22A_CONTRARY, H22A_MIN_FLAGGED = 0.05, 0.10, 100
H22B_SUPPORT, H22B_CONTRARY, H22B_MIN_GROSS = 0.50, 0.20, 100
H22C_MAX = 0.01
N_BOOT = 2000

IMAGE = ["shape", "t_over_h", "anisotropy", "profile", "rep"]


def design(reps: int = REPS) -> list[Condition]:
    return [Condition(s, t, a, p, r)
            for s, t, a, p, r in itertools.product(SHAPES, T_OVER_H, ANISOTROPY, PROFILES, range(reps))]


def guard_extra(image, spacing, mask, seg_name, meas) -> dict:
    """Columnas extra del barrido, sin verdad: índices de dominio y variable del semáforo de volumen."""
    out = domain_observables(image, mask, spacing, meas["area_sdf"])
    out["d_over_hgeo"] = feature_value(meas, spacing)
    return out


def log_excess(obs: dict, envelope: dict) -> float:
    """Mayor distancia, en logaritmo natural, de un índice de dominio a su envolvente (0 si está dentro).

    Un índice no finito o no positivo da ``inf``: no se puede comprobar el dominio."""
    worst = 0.0
    for c in DOMAIN_COLUMNS:
        v = obs.get(c, math.nan)
        lo, hi = envelope[c]
        if v is None or not math.isfinite(v) or v <= 0:
            return math.inf
        if lo > 0 and v < lo:
            worst = max(worst, math.log(lo / v))
        if v > hi:
            worst = max(worst, math.log(v / hi))
    return worst


def classify(df: pd.DataFrame, frozen: dict, factor: float = FACTOR, declared: str = DECLARED) -> pd.DataFrame:
    """Luz de volumen del certificado actual (con su tope de dominio) y el estado nuevo.

    Reproduce ``certificate.certify`` para el volumen: máscara vacía → rojo; fuera de dominio, el verde baja a
    amarillo. El estado nuevo ``inservible`` se aplica a máscaras no vacías cuyo exceso logarítmico supera
    ``ln(factor)``; nunca a un verde, que exige estar dentro del dominio."""
    models = frozen.get("volume_models", FROZEN_H6["models"])
    thr = math.log(factor)
    rows = []
    for r in df.itertuples(index=False):
        env = frozen["envelopes"]["volume"][f"{r.segmenter}|{declared}"]
        obs = {c: getattr(r, c) for c in DOMAIN_COLUMNS}
        empty = not (r.volume > 0)
        exc = math.inf if empty else log_excess(obs, env)
        inside = exc == 0.0
        if empty:
            p, light = 0.0, "rojo"
        else:
            p = p_volume_ok(r.d_over_hgeo, r.segmenter, declared, models)
            light = traffic_light(p)
            if light == "verde" and not inside:
                light = "amarillo"
        unusable = (not empty) and exc > thr
        rows.append({"p_volume": p, "light": light, "in_domain": inside, "log_excess": exc,
                     "unusable": unusable, "state": "inservible" if unusable else light})
    return pd.concat([df.reset_index(drop=True), pd.DataFrame(rows)], axis=1)


def _image_index(df: pd.DataFrame) -> np.ndarray:
    return df.groupby(IMAGE, sort=False).ngroup().to_numpy()


def _boot_upper(num: np.ndarray, den: np.ndarray, img: np.ndarray, seed: int = BOOT_SEED,
                n_boot: int = N_BOOT) -> float:
    """Percentil 97,5 de sum(num)/sum(den), remuestreando imágenes (las 3 filas de una imagen van juntas)."""
    n = int(img.max()) + 1
    a = np.bincount(img, weights=num, minlength=n)
    b = np.bincount(img, weights=den, minlength=n)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    tot = b[idx].sum(axis=1)
    ratio = np.where(tot > 0, a[idx].sum(axis=1) / np.where(tot > 0, tot, 1), np.nan)
    return float(np.nanpercentile(ratio, 97.5))


def verdicts(c: pd.DataFrame) -> dict:
    """H22a (primaria), H22b y H22c con los umbrales de este módulo, y la decisión del §8."""
    err = c["err_volume"].abs().to_numpy()
    flag = c["unusable"].to_numpy(bool)
    img = _image_index(c)

    n_flag = int(flag.sum())
    ok_flag = flag & (err <= ACCEPTABLE)
    frac_a = float(ok_flag.sum() / n_flag) if n_flag else math.nan
    up_a = _boot_upper(ok_flag.astype(float), flag.astype(float), img) if n_flag else math.nan
    if n_flag < H22A_MIN_FLAGGED:
        va = "no_evaluable"
    elif up_a <= H22A_MAX:
        va = "apoyada"
    elif frac_a > H22A_CONTRARY:
        va = "contraria"
    else:
        va = "no_concluyente"
    a = {"flagged": n_flag, "acceptable_among_flagged": int(ok_flag.sum()), "fraction": frac_a,
         "upper95": up_a, "verdict": va}

    gross = (err > GROSS) & (c["light"].to_numpy() != "rojo")
    n_gross = int(gross.sum())
    frac_b = float((gross & flag).sum() / n_gross) if n_gross else math.nan
    if n_gross < H22B_MIN_GROSS:
        vb = "no_evaluable"
    elif frac_b >= H22B_SUPPORT:
        vb = "apoyada"
    elif frac_b <= H22B_CONTRARY:
        vb = "contraria"
    else:
        vb = "no_concluyente"
    b = {"gross_not_red": n_gross, "flagged": int((gross & flag).sum()), "fraction": frac_b, "verdict": vb}

    ctrl = (c["profile"] == DECLARED).to_numpy()
    n_ctrl = int(ctrl.sum())
    frac_c = float((ctrl & flag).sum() / n_ctrl) if n_ctrl else math.nan
    vc = "no_evaluable" if not n_ctrl else ("apoyada" if frac_c <= H22C_MAX else "no_apoyada")
    cc = {"control": n_ctrl, "flagged": int((ctrl & flag).sum()), "fraction": frac_c, "verdict": vc}

    if va == "apoyada" and vc == "apoyada":
        decision = "anadir_inservible" if vb == "apoyada" else "anadir_inservible_sensibilidad_baja"
    else:
        decision = "no_anadir"
    return {"H22a": a, "H22b": b, "H22c": cc, "decision": decision}


def by_stratum(c: pd.DataFrame) -> pd.DataFrame:
    """Descriptivo por perfil × segmentador."""
    d = c.assign(abs_err=c["err_volume"].abs())
    g = d.groupby(["profile", "segmenter"])
    return pd.DataFrame({
        "n": g.size(),
        "in_domain": g["in_domain"].mean(),
        "unusable": g["unusable"].mean(),
        "red": g["light"].apply(lambda s: float((s == "rojo").mean())),
        "median_abs_err": g["abs_err"].median(),
        "gross": g["abs_err"].apply(lambda s: float((s > GROSS).mean())),
        "acceptable": g["abs_err"].apply(lambda s: float((s <= ACCEPTABLE).mean())),
    }).reset_index()


def crosstab(c: pd.DataFrame) -> pd.DataFrame:
    """Estado (actual y nuevo) frente a la banda de error de volumen."""
    band = pd.cut(c["err_volume"].abs(), [-np.inf, ACCEPTABLE, GROSS, np.inf],
                  labels=["<=10%", "10-50%", ">50%"])
    return (c.assign(band=band).groupby(["light", "state", "band"], observed=False).size()
            .rename("n").reset_index())


def sensitivity(df: pd.DataFrame, frozen: dict) -> dict:
    """Las mismas tres cifras con otros factores; descriptivo, no cambia ningún veredicto."""
    out = {}
    for f in SENSITIVITY_FACTORS:
        v = verdicts(classify(df, frozen, factor=f))
        out[str(f)] = {k: {kk: v[k][kk] for kk in ("fraction", "verdict")} for k in ("H22a", "H22b", "H22c")}
    return out
