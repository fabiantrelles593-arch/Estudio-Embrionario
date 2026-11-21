"""ONTO-MAP, piloto P4 (``docs/onto_map/PROTOCOLO_ONTOMAP.md``): selección, comprobaciones y análisis.

Pregunta: ¿la alometría estática dentro de un estadio (a15, a18) apunta en la dirección del cambio
de forma entre estadios (d = media E18.5 − media E15.5)? Todo en el espacio tangente de una GPA
conjunta de los dos estadios.

Decisión de implementación: la GPA se hace una vez con todos los especímenes y el remuestreo
(por espécimen, dentro de cada estadio) se aplica a las coordenadas tangentes. Con cientos de
especímenes la media de Procrustes apenas cambia entre réplicas, y repetir la GPA 2000 veces no
cambia la pregunta.

Solo investigación; no es una herramienta clínica.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from geovida import landmarks as lm

SEED = 20261116
STAGES = ("E15.5", "E18.5")
N_POINTS = 540
SUPPORT_MAX, CONTRARY_MIN = 45.0, 60.0


def landmark_name(biosample: str) -> str:
    return f"{biosample}_Head_Landmarks.tag"


def select(meta: pd.DataFrame, available: Iterable[str], *, seed: int = SEED,
           n_pilot_per_stage: int = 20) -> dict:
    """Piloto (mitad por sexo y estadio) y confirmatorio (el resto), disjuntos.

    Elegibles: IMPC, silvestre, C57BL/6N, sexo conocido, estadio E15.5 o E18.5 y archivo de
    landmarks en ``available`` (nombres de archivo del catálogo).
    """
    if n_pilot_per_stage % 2:
        raise ValueError("n_pilot_per_stage debe ser par")
    avail = set(available)
    ok = meta[(meta["Dataset"] == "IMPC") & (meta["Zygosity"] == "Wildtype")
              & (meta["Genotype"] == "C57BL/6N") & meta["Sex"].isin(["F", "M"])
              & meta["Stage"].isin(STAGES)]
    ok = ok[ok["Biosample"].astype(str).map(landmark_name).isin(avail)]
    rng = np.random.default_rng(seed)
    out = {"pilot": {}, "confirm": {}, "n_eligible": {}, "seed": seed}
    half = n_pilot_per_stage // 2
    for st in STAGES:
        pilot, confirm = [], []
        for sex in ("F", "M"):
            ids = sorted(ok.loc[(ok["Stage"] == st) & (ok["Sex"] == sex), "Biosample"].astype(str))
            if len(ids) <= half:
                raise ValueError(f"{st} {sex}: solo {len(ids)} elegibles")
            perm = [ids[i] for i in rng.permutation(len(ids))]
            pilot += perm[:half]
            confirm += perm[half:]
        out["pilot"][st], out["confirm"][st] = pilot, confirm
        out["n_eligible"][st] = int((ok["Stage"] == st).sum())
    return out


def prechecks(configs: dict) -> dict:
    """Comprobaciones previas de §6: ``configs`` = {estadio: arreglo (n, k, 3)}."""
    a, b = (np.asarray(configs[s], float) for s in STAGES)
    counts = sorted({x.shape[0] for x in a} | {x.shape[0] for x in b})
    n_points_ok = counts == [N_POINTS]
    res = {"point_counts": counts, "check4_points": bool(n_points_ok)}
    if not n_points_ok:
        res["pass"] = False
        return res
    g = lm.gpa(np.concatenate([a, b]))
    res["check2_gpa_converged"] = bool(g["converged"])
    _, rho_max = lm.tangent_coordinates(g["aligned"], g["mean"])
    res["rho_max"] = rho_max
    res["check3_tangent"] = bool(rho_max < 0.3)
    mean_a, mean_b = lm.gpa(a)["mean"], lm.gpa(b)["mean"]
    corr = [lm.correspondence_check(x, mean_b, n_perm=50)["corresponds"] for x in a]
    corr += [lm.correspondence_check(x, mean_a, n_perm=50)["corresponds"] for x in b]
    res["correspondence_fraction"] = float(np.mean(corr))
    res["check1_correspondence"] = bool(res["correspondence_fraction"] >= 0.95)
    res["pass"] = all(res[k] for k in ("check1_correspondence", "check2_gpa_converged",
                                       "check3_tangent", "check4_points"))
    return res


def verdict(lo: float, hi: float) -> str:
    if hi < SUPPORT_MAX:
        return "apoyada"
    if lo > CONTRARY_MIN:
        return "contraria"
    return "no concluyente"


def _angles(t15, t18, cs15, cs18) -> dict:
    a15 = lm.allometry_vector(t15, np.log(cs15))
    a18 = lm.allometry_vector(t18, np.log(cs18))
    d = t18.mean(axis=0) - t15.mean(axis=0)
    return {"a15_d": lm.angle_deg(a15, d), "a18_d": lm.angle_deg(a18, d), "a15_a18": lm.angle_deg(a15, a18)}


def analyze(configs: dict, *, n_boot: int = 2000, seed: int = SEED) -> dict:
    """Ángulos de §5 con IC 95 % por remuestreo de especímenes dentro de cada estadio."""
    a, b = (np.asarray(configs[s], float) for s in STAGES)
    g = lm.gpa(np.concatenate([a, b]))
    tan, rho_max = lm.tangent_coordinates(g["aligned"], g["mean"])
    n15 = len(a)
    t15, t18 = tan[:n15], tan[n15:]
    cs15, cs18 = g["centroid_size"][:n15], g["centroid_size"][n15:]
    obs = _angles(t15, t18, cs15, cs18)
    rng = np.random.default_rng(seed)
    boot = {k: [] for k in obs}
    for _ in range(n_boot):
        i = rng.integers(0, n15, n15)
        j = rng.integers(0, len(b), len(b))
        try:
            r = _angles(t15[i], t18[j], cs15[i], cs18[j])
        except ValueError:  # réplica sin variación de tamaño
            continue
        for k, v in r.items():
            boot[k].append(v)
    ev = np.linalg.svd(tan - tan.mean(axis=0), compute_uv=False) ** 2
    dim95 = int(np.searchsorted(np.cumsum(ev) / ev.sum(), 0.95) + 1)
    res = {"n": {"E15.5": n15, "E18.5": len(b)}, "rho_max": rho_max, "dim95": dim95,
           "null_q01_deg": lm.random_angle_quantile(max(dim95, 2), 0.01),
           "cs_mean": {"E15.5": float(cs15.mean()), "E18.5": float(cs18.mean())},
           "n_boot_valid": len(boot["a15_d"]), "angles": {}}
    for k, v in obs.items():
        lo, hi = (float(x) for x in np.percentile(boot[k], [2.5, 97.5]))
        res["angles"][k] = {"deg": v, "ci95": [lo, hi], "verdict": verdict(lo, hi)}
    return res
