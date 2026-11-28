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


def gate_tangent(atlas: dict, mean: np.ndarray, limit: float = RHO_MAX_REF) -> dict:
    """G0-t: cada configuración de atlas no está más lejos de la media que el espécimen más lejano de las 597."""
    rho = {s: float(lm.procrustes_distances(atlas[s], mean)["rho"]) for s in STAGES}
    return {"gate": "G0-t", "rho_to_mean": rho, "limit": float(limit),
            "passed": bool(all(v <= limit for v in rho.values()))}


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


# ================================================================ MT-C (PREREGISTRO_HOMOLOGOS.md)
SEED_MTC = 20261125
N_HOMOLOGOUS = 22                  # filas 1–22: landmarks homólogos entre estadios (Devine et al. 2022)
N_SPARSE_STAGE = 25                # filas 23–25: landmarks propios de E15.5 y E18.5 (sensibilidad 1)
TOP_K = 5
CONCENTRATION_MIN = 0.50           # MT-C2: los 5 primeros llevan ≥ 50 % de |a₂₂|²
ORDER_TOL = 1e-4                   # G0-o(a), mm
AREA_MIN = 1e-6                    # G0-o(b), mm²
# Las 21 caras (índices desde 1) sobre las que MusMorph interpola los parches; idénticas en los dos atlas
# (``IMPC_E15.5_Head_Atlas_Patches.tsv`` e ``IMPC_E18.5_Head_Atlas_Patches.tsv`` del repositorio MusMorph).
PATCH_TRIANGLES = ((20, 19, 21), (20, 19, 22), (18, 19, 21), (18, 19, 22), (18, 14, 22), (18, 12, 21),
                   (5, 12, 21), (17, 12, 18), (17, 14, 18), (6, 14, 22), (6, 14, 16), (5, 12, 15), (5, 7, 9),
                   (6, 8, 9), (13, 16, 17), (11, 15, 17), (15, 16, 17), (3, 10, 15), (4, 10, 16), (7, 8, 9),
                   (10, 15, 16))


def subset_rows(configs, n: int) -> np.ndarray:
    """Primeras ``n`` filas de una configuración (k, 3) o de un arreglo de configuraciones (m, k, 3)."""
    x = np.asarray(configs, float)
    if x.shape[-2] < n:
        raise ValueError(f"hacen falta ≥ {n} filas; hay {x.shape[-2]}")
    return x[..., :n, :]


def landmark_contributions(a: np.ndarray, d: np.ndarray, t15: np.ndarray, t18: np.ndarray, *,
                           top_k: int = TOP_K) -> dict:
    """§3 paso 3: parte de cada landmark en |a|² (cᵢ), |aᵢ| / sᵢ, ángulo(aᵢ, dᵢ) y concentración (MT-C2)."""
    A, D = np.asarray(a, float).reshape(-1, 3), np.asarray(d, float).reshape(-1, 3)
    c = (A ** 2).sum(axis=1) / float((A ** 2).sum())
    res = np.concatenate([t15 - t15.mean(axis=0), t18 - t18.mean(axis=0)]).reshape(len(t15) + len(t18), -1, 3)
    s = np.sqrt((res ** 2).sum(axis=2).mean(axis=0))
    order = np.argsort(-c, kind="stable")
    top = order[:top_k]
    share = float(c[top].sum())
    return {"c": c.tolist(), "ratio_to_spread": (np.linalg.norm(A, axis=1) / s).tolist(),
            "angle_a_d_deg": [lm.angle_deg(A[i], D[i]) for i in range(len(A))],
            "top_landmarks": [int(i) + 1 for i in top], "top_share": share,
            "uniform_share": top_k / len(A), "verdict": verdict_mtc2(share)}


def verdict_mtc2(share: float) -> str:
    """§4: apoyada si los 5 landmarks con mayor cᵢ llevan ≥ 50 % de |a₂₂|²."""
    if not math.isfinite(share):
        return "no evaluable"
    return "apoyada" if share >= CONCENTRATION_MIN else "no apoyada"


def gate_order(facebase: dict, github: dict | None, n: int = N_HOMOLOGOUS) -> dict:
    """G0-o: (a) las filas 1–n de cada atlas coinciden con las de la copia de GitHub (si la hay);
    (b) las 21 caras de los parches sobre esas filas no son degeneradas."""
    areas = {}
    for s in STAGES:
        p = np.asarray(facebase[s], float)
        areas[s] = min(0.5 * float(np.linalg.norm(np.cross(p[j - 1] - p[i - 1], p[k - 1] - p[i - 1])))
                       for i, j, k in PATCH_TRIANGLES)
    b_ok = all(v > AREA_MIN for v in areas.values())
    out = {"gate": "G0-o", "min_triangle_area_mm2": areas, "area_min": AREA_MIN, "passed_b": bool(b_ok)}
    if github is None:
        out.update({"compared_with_github": False, "passed": bool(b_ok)})
        return out
    diff = {s: float(np.max(np.abs(subset_rows(facebase[s], n) - subset_rows(github[s], n)))) for s in STAGES}
    a_ok = all(v <= ORDER_TOL for v in diff.values())
    out.update({"compared_with_github": True, "max_abs_diff_mm": diff, "tolerance": ORDER_TOL,
                "passed_a": bool(a_ok), "passed": bool(a_ok and b_ok)})
    return out
