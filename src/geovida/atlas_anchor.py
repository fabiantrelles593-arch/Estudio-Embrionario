"""MT-B (docs/morpho_trace/PREREGISTRO_ANCLAJE_ATLAS.md): ¿la separación entre estadios es la diferencia entre atlas?

Sin registro. En el espacio tangente del GPA de las configuraciones publicadas:

* d = t̄₁₈ − t̄₁₅ (separación entre estadios),
* a = t(A₁₈) − t(A₁₅) (diferencia entre las configuraciones de landmarks de los dos atlas),
* e_s = t̄_s − t(A_s) (cuánto se aparta la media publicada del estadio s de su atlas),

con d = a + e₁₈ − e₁₅ por construcción. Estimando primario r = |d − a| / |d|.
"""
from __future__ import annotations

import math

import numpy as np

from . import landmarks as lm

SEED = 20261124
N_BOOT = 2000
N_BOOT_REGPA = 200
SUPPORT_MAX, REFUTE_MIN = 0.25, 0.50          # MT-B1: apoyada si IC sup ≤ 0,25; refutada si IC inf ≥ 0,50
D_REF, D_TOL = 0.15678486981634399, 1e-4       # G0-d‴: |d| de G0-d′ de v2
PROJ_TOL = 1e-8                                # G0-p
RHO_MAX_REF = 0.1572760162630266               # G0-t: ρ máxima de las 597 a su media (G0-d′ de v2)
N_PROJ_CHECK = 5
STAGES = ("E15.5", "E18.5")


# ---------------------------------------------------------------- espacio de forma
def project_to_tangent(config: np.ndarray, mean: np.ndarray) -> np.ndarray:
    """Preforma de ``config``, rotación sin reflexión sobre ``mean`` y proyección tangente (vector aplanado).

    Es la operación que ``landmarks.gpa`` + ``tangent_coordinates`` aplican a cada configuración del ajuste,
    aplicada a una que no entra en él."""
    m = lm.preshape(mean)
    z = lm.preshape(config)
    r, _ = lm._rotation(z, m)
    v = (z @ r).ravel()
    fm = m.ravel()
    return v - (v @ fm) * fm


def shape_space(pub15: np.ndarray, pub18: np.ndarray) -> dict:
    """GPA de las publicadas (E15.5 primero) y sus coordenadas tangentes, como en G0-d′ de v2."""
    pub15, pub18 = np.asarray(pub15, float), np.asarray(pub18, float)
    g = lm.gpa(np.concatenate([pub15, pub18]))
    t, rho_max = lm.tangent_coordinates(g["aligned"], g["mean"])
    n15 = len(pub15)
    return {"mean": g["mean"], "t15": t[:n15], "t18": t[n15:], "rho_max": float(rho_max),
            "converged": bool(g["converged"])}


# ---------------------------------------------------------------- estimandos
def decompose(t15: np.ndarray, t18: np.ndarray, a15: np.ndarray, a18: np.ndarray) -> dict:
    """Vectores de la descomposición d = a + e₁₈ − e₁₅ y escalares de §4 (MT-B1, MT-B2, MT-B3)."""
    m15, m18 = t15.mean(axis=0), t18.mean(axis=0)
    d = m18 - m15
    a = a18 - a15
    e15, e18 = m15 - a15, m18 - a18
    dl = float(np.linalg.norm(d))
    dh = d / dl
    return {
        "d": d, "a": a, "e15": e15, "e18": e18,
        "d_length": dl,
        "r": float(np.linalg.norm(d - a)) / dl,
        "f_a": float(a @ dh) / dl,
        "a_ratio": float(np.linalg.norm(a)) / dl,
        "angle_a_d_deg": lm.angle_deg(a, d),
        "e15_ratio": float(np.linalg.norm(e15)) / dl,
        "e18_ratio": float(np.linalg.norm(e18)) / dl,
        "ediff_along_d": float((e18 - e15) @ dh) / dl,
        "e_norm": {"E15.5": float(np.linalg.norm(e15)), "E18.5": float(np.linalg.norm(e18))},
        "median_spread": {"E15.5": float(np.median(np.linalg.norm(t15 - m15, axis=1))),
                          "E18.5": float(np.median(np.linalg.norm(t18 - m18, axis=1)))},
    }


SCALARS = ("r", "f_a", "a_ratio", "angle_a_d_deg", "e15_ratio", "e18_ratio", "ediff_along_d", "d_length")


def _scalars(dec: dict) -> dict:
    out = {k: dec[k] for k in SCALARS}
    out.update({f"e_norm_{s}": dec["e_norm"][s] for s in STAGES})
    out.update({f"median_spread_{s}": dec["median_spread"][s] for s in STAGES})
    return out


def verdict_mtb1(lo: float, hi: float) -> str:
    """§4: apoyada si el límite superior de r ≤ 0,25; refutada si el inferior ≥ 0,50; si no, no concluyente."""
    if not (math.isfinite(lo) and math.isfinite(hi)):
        return "no evaluable"
    if hi <= SUPPORT_MAX:
        return "apoyada"
    if lo >= REFUTE_MIN:
        return "refutada"
    return "no concluyente"


def verdict_mtb2(e_norm: dict, median_spread: dict) -> str:
    """§4: apoyada si |e_s| < mediana de |t(x) − t̄_s| en los dos estadios (punto estimado)."""
    vals = [e_norm[s] for s in STAGES] + [median_spread[s] for s in STAGES]
    if not all(math.isfinite(v) for v in vals):
        return "no evaluable"
    return "apoyada" if all(e_norm[s] < median_spread[s] for s in STAGES) else "no apoyada"


def anchor_decomposition(t15: np.ndarray, t18: np.ndarray, a15: np.ndarray, a18: np.ndarray, *,
                         n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """Puntos estimados, IC 95 % por remuestreo de especímenes dentro de cada estadio (tangentes y atlas fijos)
    y veredictos de MT-B1 y MT-B2."""
    t15, t18 = np.asarray(t15, float), np.asarray(t18, float)
    if len(t15) < 2 or len(t18) < 2:
        raise ValueError("hacen falta ≥ 2 especímenes por estadio")
    dec = decompose(t15, t18, a15, a18)
    point = _scalars(dec)
    rng = np.random.default_rng(seed)
    boot = {k: [] for k in point}
    for _ in range(n_boot):
        b = _scalars(decompose(t15[rng.integers(0, len(t15), len(t15))],
                               t18[rng.integers(0, len(t18), len(t18))], a15, a18))
        for k, v in b.items():
            boot[k].append(v)
    ci = {k: [float(x) for x in np.percentile(v, [2.5, 97.5])] for k, v in boot.items()}
    lo, hi = ci["r"]
    return {
        "n": {"E15.5": int(len(t15)), "E18.5": int(len(t18))},
        "point": point, "ci": ci,
        "identity_error": float(np.max(np.abs(dec["d"] - (dec["a"] + dec["e18"] - dec["e15"])))),
        "mtb1": {"r": point["r"], "ci": [lo, hi], "verdict": verdict_mtb1(lo, hi)},
        "mtb2": {"e_norm": dec["e_norm"], "median_spread": dec["median_spread"],
                 "verdict": verdict_mtb2(dec["e_norm"], dec["median_spread"])},
        "n_boot": n_boot, "seed": seed,
    }


# ---------------------------------------------------------------- puertas
def gate_d(d_length: float) -> dict:
    return {"gate": "G0-d‴", "d_length": float(d_length), "reference": D_REF, "tolerance": D_TOL,
            "passed": bool(abs(d_length - D_REF) <= D_TOL)}


def gate_projection(configs: np.ndarray, tangents: np.ndarray, mean: np.ndarray) -> dict:
    """G0-p: proyectar configuraciones que estaban en el GPA reproduce sus coordenadas tangentes."""
    diff = max(float(np.max(np.abs(project_to_tangent(c, mean) - t))) for c, t in zip(configs, tangents))
    return {"gate": "G0-p", "n": int(len(configs)), "max_abs_diff": diff, "tolerance": PROJ_TOL,
            "passed": bool(diff <= PROJ_TOL)}


def gate_tangent(atlas: dict, mean: np.ndarray) -> dict:
    """G0-t: cada configuración de atlas no está más lejos de la media que el espécimen más lejano de las 597."""
    rho = {s: float(lm.procrustes_distances(atlas[s], mean)["rho"]) for s in STAGES}
    return {"gate": "G0-t", "rho_to_mean": rho, "limit": RHO_MAX_REF,
            "passed": bool(all(v <= RHO_MAX_REF for v in rho.values()))}


# ---------------------------------------------------------------- sensibilidad
def sensitivity_in_gpa(pub15: np.ndarray, pub18: np.ndarray, atlas: dict) -> dict:
    """§6.1: los dos atlas dentro del GPA (n + 2 configuraciones)."""
    pub15, pub18 = np.asarray(pub15, float), np.asarray(pub18, float)
    g = lm.gpa(np.concatenate([pub15, pub18, [atlas["E15.5"]], [atlas["E18.5"]]]))
    t, _ = lm.tangent_coordinates(g["aligned"], g["mean"])
    n15, n18 = len(pub15), len(pub18)
    dec = decompose(t[:n15], t[n15:n15 + n18], t[-2], t[-1])
    return {"r": dec["r"], "f_a": dec["f_a"]}


def sensitivity_regpa(pub15: np.ndarray, pub18: np.ndarray, atlas: dict, *,
                      n_boot: int = N_BOOT_REGPA, seed: int = SEED) -> dict:
    """§6.2: IC de r rehaciendo el GPA (y la proyección de los atlas) en cada réplica."""
    pub15, pub18 = np.asarray(pub15, float), np.asarray(pub18, float)
    rng = np.random.default_rng(seed)
    rs = []
    for _ in range(n_boot):
        s = shape_space(pub15[rng.integers(0, len(pub15), len(pub15))],
                        pub18[rng.integers(0, len(pub18), len(pub18))])
        rs.append(decompose(s["t15"], s["t18"], project_to_tangent(atlas["E15.5"], s["mean"]),
                            project_to_tangent(atlas["E18.5"], s["mean"]))["r"])
    return {"n_boot": n_boot, "seed": seed, "ci": [float(x) for x in np.percentile(rs, [2.5, 97.5])]}


def split_halves(n: int, seed: int = SEED) -> tuple[np.ndarray, np.ndarray]:
    """§6.3: partición fija de 0..n−1 en dos mitades con la semilla."""
    perm = np.random.default_rng(seed).permutation(n)
    h = n // 2
    return np.sort(perm[:h]), np.sort(perm[h:2 * h])


def sensitivity_halves(t15: np.ndarray, t18: np.ndarray, a15: np.ndarray, a18: np.ndarray, *,
                       n_boot: int = N_BOOT, seed: int = SEED) -> list[dict]:
    """§6.3: MT-B1 con cada mitad de E18.5 (tangentes fijas)."""
    out = []
    for half in split_halves(len(t18), seed):
        res = anchor_decomposition(t15, t18[half], a15, a18, n_boot=n_boot, seed=seed)
        out.append({"n18": int(len(half)), **res["mtb1"]})
    return out
