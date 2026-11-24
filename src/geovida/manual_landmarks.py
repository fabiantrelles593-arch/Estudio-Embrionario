"""MT-D (docs/morpho_trace/PREREGISTRO_ANOTACION_MANUAL.md): anotación manual independiente de los landmarks 17–22.

Qué hace
--------
* Lee los puntos que una persona coloca en 3D Slicer (``.mrk.json``), en la convención que declare el archivo
  (LPS o RAS), y los devuelve en coordenadas de mundo RAS, que son las de los ``.tag`` y de la afín de nibabel.
* Exporta volúmenes a NIfTI conservando la afín de mundo (con recorte opcional a una caja) y construye el fantoma de
  esferas de la puerta G0-c.
* Calcula las cantidades de §4 del preregistro: medias y error de repetición, discrepancia con MusMorph, **a**ᵐᵃⁿ
  (filas 17–22 de cada atlas sustituidas por las manuales, proyectadas sobre el espacio tangente de MT-C), q y rᵐᵃⁿ
  con su remuestreo, y las puertas G0-e, G0-c, G0-ε y G0-r.

Qué NO hace
-----------
No coloca, corrige ni sugiere landmarks: todos los puntos manuales vienen de una persona (D1). No registra
imágenes entre sí. Las pruebas usan datos sintéticos; que pasen no valida ninguna anotación real.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from . import atlas_anchor as aa
from . import landmarks as lm

SEED_MTD = 20261126
N_BOOT = 2000
TARGETS = (17, 18, 19, 20, 21, 22)
N_REFERENCES = 4
REFERENCE_POOL = 16                      # las referencias salen de los landmarks 1–16
N_REPEATS_ATLAS = 5
N_SPECIMENS_PER_STAGE = 8
N_SPECIMEN_REPEATS = 2
MIN_REPEATS = 3                          # mínimo de repeticiones válidas por landmark y atlas para evaluar
Q_LOW, Q_HIGH, Q_NOT = 0.75, 1.25, 0.50  # MT-D1
EPS_FACTOR = 0.5                         # G0-ε: εᵢ ≤ 0,5 · |aᵢ|
REF_RATIO_MAX = 3.0                      # G0-r: mediana de δ/ε en las referencias ≤ 3
PHANTOM_TOL_VOX = 1.0                    # G0-c: error ≤ 1 vóxel
PHANTOM_RADII_VOX = (3, 5, 7)            # P1 < P2 < P3, para que se distingan a simple vista
STAGES = aa.STAGES


# ---------------------------------------------------------------- etiquetas y lectura de Slicer
def label(i: int) -> str:
    """Etiqueta que el anotador da al landmark i (índice desde 1): 'L17'."""
    return f"L{int(i)}"


def parse_label(text: str) -> int | None:
    t = str(text).strip().upper()
    if t.startswith("L"):
        t = t[1:]
    return int(t) if t.isdigit() else None


def read_markups(path) -> dict[int, np.ndarray]:
    """{landmark: posición RAS (mm)} de un ``.mrk.json`` de Slicer.

    Se ignoran los puntos sin posición definida (``positionStatus`` distinto de 'defined'). Una etiqueta repetida o
    una convención desconocida es un error; nunca se adivina."""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    out: dict[int, np.ndarray] = {}
    for mk in doc.get("markups", []):
        cs = str(mk.get("coordinateSystem", "LPS")).upper()
        if cs not in ("LPS", "RAS"):
            raise ValueError(f"{path}: sistema de coordenadas desconocido {cs!r}")
        units = str(mk.get("coordinateUnits", "mm")).lower()
        if units != "mm":
            raise ValueError(f"{path}: unidades {units!r}; solo mm")
        flip = np.array([-1.0, -1.0, 1.0]) if cs == "LPS" else np.ones(3)
        for cp in mk.get("controlPoints", []):
            if cp.get("positionStatus", "defined") != "defined" or cp.get("position") is None:
                continue
            i = parse_label(cp.get("label", ""))
            if i is None:
                raise ValueError(f"{path}: etiqueta no reconocida {cp.get('label')!r}")
            if i in out:
                raise ValueError(f"{path}: etiqueta repetida {label(i)}")
            out[i] = np.asarray(cp["position"], float) * flip
    return out


def write_markups(path, points: dict[int, np.ndarray], coordinate_system: str = "LPS") -> None:
    """Escribe un ``.mrk.json`` mínimo (para pruebas y para las plantillas vacías del anotador)."""
    flip = np.array([-1.0, -1.0, 1.0]) if coordinate_system.upper() == "LPS" else np.ones(3)
    cps = [{"id": str(n + 1), "label": label(i), "position": (np.asarray(p, float) * flip).tolist(),
            "positionStatus": "defined"} for n, (i, p) in enumerate(sorted(points.items()))]
    doc = {"@schema": "https://raw.githubusercontent.com/slicer/slicer/master/Modules/Loadable/Markups/Resources/"
                      "Schema/markups-schema-v1.0.3.json#",
           "markups": [{"type": "Fiducial", "coordinateSystem": coordinate_system.upper(), "coordinateUnits": "mm",
                        "controlPoints": cps}]}
    Path(path).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")


def points_array(points: dict[int, np.ndarray], landmarks) -> np.ndarray:
    """(len(landmarks), 3) con NaN donde falta un landmark."""
    return np.array([points.get(int(i), np.full(3, np.nan)) for i in landmarks], float)


# ---------------------------------------------------------------- volúmenes
def box_slices(shape, affine, lo, hi) -> tuple[slice, slice, slice]:
    """Índices del subvolumen que contiene la caja de mundo [lo, hi] (sin calcular el mundo de cada vóxel)."""
    a = np.asarray(affine, float)
    inv = np.linalg.inv(a)
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    idx = corners @ inv[:3, :3].T + inv[:3, 3]
    i0 = np.clip(np.floor(idx.min(axis=0)).astype(int), 0, None)
    i1 = np.minimum(np.ceil(idx.max(axis=0)).astype(int) + 1, np.asarray(shape))
    if np.any(i1 <= i0):
        raise ValueError("la caja no corta el volumen")
    return tuple(slice(int(b), int(e)) for b, e in zip(i0, i1))


def shifted_affine(affine, slices) -> np.ndarray:
    """Afín del subvolumen: el mismo punto del mundo cae en el mismo vóxel del original."""
    a = np.asarray(affine, float).copy()
    i0 = np.array([s.start for s in slices], float)
    a[:3, 3] = a[:3, :3] @ i0 + a[:3, 3]
    return a


def save_nifti(arr: np.ndarray, affine, path) -> None:
    import nibabel as nib
    img = nib.Nifti1Image(np.asarray(arr, np.float32), np.asarray(affine, float))
    img.set_sform(np.asarray(affine, float), code=1)
    img.set_qform(np.asarray(affine, float), code=1)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    nib.save(img, str(path))


def world_to_index(points, affine) -> np.ndarray:
    inv = np.linalg.inv(np.asarray(affine, float))
    return np.asarray(points, float) @ inv[:3, :3].T + inv[:3, 3]


def phantom(affine3: np.ndarray, shape=(96, 96, 96)) -> tuple[np.ndarray, np.ndarray, dict[int, np.ndarray]]:
    """Volumen con tres esferas (P1 < P2 < P3) y la misma matriz de dirección y paso que ``affine3`` (3 × 3).

    Devuelve (volumen, afín 4 × 4, {1: centro RAS, 2: …, 3: …}). Los centros caen en centros de vóxel."""
    shape = tuple(int(s) for s in shape)
    a = np.eye(4)
    a[:3, :3] = np.asarray(affine3, float)[:3, :3]
    centres_idx = [np.array([0.30, 0.35, 0.40]), np.array([0.65, 0.40, 0.55]), np.array([0.45, 0.68, 0.35])]
    vol = np.zeros(shape, np.float32)
    grid = np.indices(shape).astype(float)
    truth = {}
    for k, (frac, rad) in enumerate(zip(centres_idx, PHANTOM_RADII_VOX), start=1):
        c = np.round(frac * (np.asarray(shape) - 1))
        r2 = sum((grid[j] - c[j]) ** 2 for j in range(3))
        vol[r2 <= rad ** 2] = 1000.0
        truth[k] = a[:3, :3] @ c + a[:3, 3]
    return vol, a, truth


# ---------------------------------------------------------------- puertas previas
def gate_space(points: np.ndarray, shape, affine, values_at, threshold: float) -> dict:
    """G0-e para una imagen: cada punto dentro de los límites y con intensidad (vóxel más cercano) > umbral.

    ``values_at(idx)`` devuelve las intensidades en los índices enteros ``idx`` (n, 3)."""
    idx = np.rint(world_to_index(points, affine)).astype(int)
    inside = np.all((idx >= 0) & (idx < np.asarray(shape)), axis=1)
    vals = np.full(len(points), np.nan)
    if inside.any():
        vals[inside] = values_at(idx[inside])
    above = inside & (vals > threshold)
    return {"n_points": int(len(points)), "n_inside": int(inside.sum()), "n_above_otsu": int(above.sum()),
            "otsu": float(threshold), "failed_landmarks": [int(i) + 1 for i in np.flatnonzero(~above)],
            "passed": bool(above.all())}


def gate_phantom(truth: dict[int, np.ndarray], placed: dict[int, np.ndarray], voxel_mm: float) -> dict:
    """G0-c: error de cada esfera ≤ 1 vóxel. ``placed`` usa las etiquetas 1–3 (P1–P3 se leen como L1–L3 o 1–3)."""
    err = {int(k): (float(np.linalg.norm(placed[k] - truth[k])) if k in placed else math.inf) for k in truth}
    return {"error_mm": err, "voxel_mm": float(voxel_mm), "tolerance_mm": PHANTOM_TOL_VOX * float(voxel_mm),
            "passed": bool(all(e <= PHANTOM_TOL_VOX * voxel_mm for e in err.values()))}


# ---------------------------------------------------------------- referencias y muestra
def choose_references(ratio_to_spread, n: int = N_REFERENCES, pool: int = REFERENCE_POOL) -> dict:
    """§3.1: los n landmarks de 1–pool con menor |aᵢ| / sᵢ de MT-C; el resto, en orden, como suplentes."""
    r = np.asarray(ratio_to_spread, float)[:pool]
    order = [int(i) + 1 for i in np.argsort(r, kind="stable")]
    return {"references": order[:n], "spares": order[n:n + 3],
            "ratios": {int(i): float(r[i - 1]) for i in order[:n + 3]}}


def plan_sessions(ids: dict[str, list[str]], seed: int = SEED_MTD) -> dict:
    """§3.3–3.4: especímenes, repeticiones, códigos y orden de las sesiones (sin ver ninguna imagen)."""
    rng = np.random.default_rng(seed)
    chosen, repeats = {}, {}
    for st in STAGES:
        pool = sorted(ids[st])
        pick = sorted(rng.choice(len(pool), N_SPECIMENS_PER_STAGE, replace=False).tolist())
        chosen[st] = [pool[i] for i in pick]
        repeats[st] = sorted(rng.choice(chosen[st], N_SPECIMEN_REPEATS, replace=False).tolist())
    n_tasks = N_REPEATS_ATLAS * len(STAGES) + N_SPECIMENS_PER_STAGE * len(STAGES) + N_SPECIMEN_REPEATS * len(STAGES)
    n_vol = len(STAGES) * (1 + N_SPECIMENS_PER_STAGE)
    nums = rng.choice(9000, n_tasks + n_vol, replace=False) + 1000
    vol_codes = [f"V{c:04d}" for c in nums[:n_vol]]
    codes = [f"T{c:04d}" for c in nums[n_vol:]]
    volume = {("atlas", st): vol_codes[k] for k, st in enumerate(STAGES)}
    k = 2
    for st in STAGES:
        for sid in chosen[st]:
            volume[("specimen", sid)] = vol_codes[k]
            k += 1
    sessions: list[list[dict]] = [[] for _ in range(N_REPEATS_ATLAS)]
    for rep in range(N_REPEATS_ATLAS):
        for st in STAGES:
            sessions[rep].append({"kind": "atlas", "stage": st, "id": f"atlas_{st}", "repeat": rep + 1})
    originals = [{"kind": "specimen", "stage": st, "id": sid, "repeat": 1} for st in STAGES for sid in chosen[st]]
    originals = [originals[i] for i in rng.permutation(len(originals))]
    per = len(originals) // (N_REPEATS_ATLAS - 1)
    for s in range(N_REPEATS_ATLAS - 1):
        sessions[s].extend(originals[s * per:(s + 1) * per])
    sessions[-1].extend({"kind": "specimen", "stage": st, "id": sid, "repeat": 2} for st in STAGES for sid in repeats[st])
    out, c = [], 0
    for s, tasks in enumerate(sessions, start=1):
        tasks = [tasks[i] for i in rng.permutation(len(tasks))]
        for t in tasks:
            key = ("atlas", t["stage"]) if t["kind"] == "atlas" else ("specimen", t["id"])
            t.update({"session": s, "task": codes[c], "volume": volume[key]})
            c += 1
        out.extend(tasks)
    return {"seed": seed, "specimens": chosen, "specimen_repeats": repeats, "tasks": out}


# ---------------------------------------------------------------- estadística de repeticiones
def repeat_stats(reps: np.ndarray) -> dict:
    """reps (R, L, 3) con NaN si falta. Media por landmark, error de repetición εᵢ (mm) y repeticiones válidas."""
    reps = np.asarray(reps, float)
    ok = ~np.isnan(reps).any(axis=2)
    n = ok.sum(axis=0)
    with np.errstate(invalid="ignore"):
        mean = np.nanmean(reps, axis=0)
        eps = np.sqrt(np.nanmean(((reps - mean) ** 2).sum(axis=2), axis=0))
    return {"mean": mean, "eps_mm": eps, "n_valid": n}


def replace_rows(config: np.ndarray, rows, points: np.ndarray) -> np.ndarray:
    out = np.asarray(config, float).copy()
    out[[int(i) - 1 for i in rows]] = np.asarray(points, float)
    return out


def _block(v: np.ndarray, rows) -> np.ndarray:
    v = np.asarray(v, float).reshape(-1, 3)
    return v[[int(i) - 1 for i in rows]].ravel()


def manual_atlas_difference(atlas22: dict, manual: dict, mean: np.ndarray, rows=TARGETS) -> np.ndarray:
    """**a**ᵐᵃⁿ: cada atlas con sus filas ``rows`` sustituidas por ``manual[stage]`` y proyectado sobre ``mean``."""
    t = {st: aa.project_to_tangent(replace_rows(atlas22[st], rows, manual[st]), mean) for st in STAGES}
    return t["E18.5"] - t["E15.5"]


def q_value(a_man: np.ndarray, a: np.ndarray, rows=TARGETS) -> float:
    """⟨aᵐᵃⁿ₁₇₋₂₂, a₁₇₋₂₂⟩ / |a₁₇₋₂₂|²."""
    am, ar = _block(a_man, rows), _block(a, rows)
    return float(am @ ar) / float(ar @ ar)


def r_manual(d: np.ndarray, a_man: np.ndarray) -> float:
    return float(np.linalg.norm(d - a_man)) / float(np.linalg.norm(d))


def verdict_mtd1(lo: float, hi: float) -> str:
    """§5: reproducida si el IC está entero en [0,75; 1,25]; no reproducida si el límite superior ≤ 0,50."""
    if not (math.isfinite(lo) and math.isfinite(hi)):
        return "no evaluable"
    if lo >= Q_LOW and hi <= Q_HIGH:
        return "reproducida"
    if hi <= Q_NOT:
        return "no reproducida"
    return "no concluyente"


def _resample_mean(reps: np.ndarray, rng) -> np.ndarray:
    """Media de cada landmark tras remuestrear con reemplazo sus repeticiones válidas."""
    out = np.empty(reps.shape[1:], float)
    for j in range(reps.shape[1]):
        valid = reps[~np.isnan(reps[:, j]).any(axis=1), j]
        out[j] = valid[rng.integers(0, len(valid), len(valid))].mean(axis=0)
    return out


def bootstrap_q(atlas22: dict, reps: dict, mean: np.ndarray, a: np.ndarray, d: np.ndarray, *,
                rows=TARGETS, n_boot: int = N_BOOT, seed: int = SEED_MTD) -> dict:
    """§4.3–4.4: q y rᵐᵃⁿ con las medias manuales, y su IC 95 % remuestreando repeticiones (solo error de
    anotación)."""
    for st in STAGES:
        n = repeat_stats(reps[st])["n_valid"]
        if np.any(n < MIN_REPEATS):
            return {"q": math.nan, "r_manual": math.nan, "q_ci": [math.nan, math.nan],
                    "r_ci": [math.nan, math.nan], "verdict_mtd1": "no evaluable",
                    "reason": f"{st}: menos de {MIN_REPEATS} repeticiones válidas en algún landmark"}
    manual = {st: repeat_stats(reps[st])["mean"] for st in STAGES}
    a_man = manual_atlas_difference(atlas22, manual, mean, rows)
    q, r = q_value(a_man, a, rows), r_manual(d, a_man)
    rng = np.random.default_rng(seed)
    qs, rs = np.empty(n_boot), np.empty(n_boot)
    for b in range(n_boot):
        m = {st: _resample_mean(np.asarray(reps[st], float), rng) for st in STAGES}
        ab = manual_atlas_difference(atlas22, m, mean, rows)
        qs[b], rs[b] = q_value(ab, a, rows), r_manual(d, ab)
    q_ci = [float(np.percentile(qs, 2.5)), float(np.percentile(qs, 97.5))]
    r_ci = [float(np.percentile(rs, 2.5)), float(np.percentile(rs, 97.5))]
    return {"q": q, "r_manual": r, "q_ci": q_ci, "r_ci": r_ci, "n_boot": n_boot, "seed": seed,
            "a_manual": a_man.tolist(), "verdict_mtd1": verdict_mtd1(*q_ci),
            "verdict_mtd2": aa.verdict_mtb1(*r_ci)}


# ---------------------------------------------------------------- puertas posteriores
def gate_precision(atlas22: dict, reps: dict, mean: np.ndarray, a: np.ndarray, rows=TARGETS) -> dict:
    """G0-ε: en cada atlas y landmark objetivo, el error de repetición proyectado al espacio tangente
    (cada repetición sustituye las filas y se proyecta) ≤ 0,5 · |aᵢ| de MusMorph."""
    a_i = np.linalg.norm(np.asarray(a, float).reshape(-1, 3)[[int(i) - 1 for i in rows]], axis=1)
    out, ok = {}, True
    for st in STAGES:
        r = np.asarray(reps[st], float)
        fill = repeat_stats(r)["mean"]
        ts = []
        for k in range(len(r)):
            rk = np.where(np.isnan(r[k]), np.nan, r[k])
            valid = ~np.isnan(rk).any(axis=1)
            pts = np.where(valid[:, None], rk, fill)
            t = aa.project_to_tangent(replace_rows(atlas22[st], rows, pts), mean).reshape(-1, 3)
            tk = t[[int(i) - 1 for i in rows]]
            tk[~valid] = np.nan
            ts.append(tk)
        ts = np.array(ts)
        with np.errstate(invalid="ignore"):
            eps_t = np.sqrt(np.nanmean(((ts - np.nanmean(ts, axis=0)) ** 2).sum(axis=2), axis=0))
        passed = eps_t <= EPS_FACTOR * a_i
        ok = ok and bool(np.all(passed))
        out[st] = {"eps_tangent": eps_t.tolist(), "limit": (EPS_FACTOR * a_i).tolist(),
                   "passed_per_landmark": {label(i): bool(p) for i, p in zip(rows, passed)}}
    return {"gate": "G0-ε", "landmarks": [int(i) for i in rows], "items": out, "passed": bool(ok)}


def gate_references(musmorph: dict, reps: dict, refs) -> dict:
    """G0-r: en cada atlas, mediana de δᵢ / εᵢ en las referencias ≤ 3 (δ: media manual − MusMorph, en mm)."""
    out, ok = {}, True
    for st in STAGES:
        s = repeat_stats(reps[st])
        m = np.asarray(musmorph[st], float)[[int(i) - 1 for i in refs]]
        delta = np.linalg.norm(s["mean"] - m, axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = delta / s["eps_mm"]
        med = float(np.median(ratio)) if np.all(np.isfinite(ratio)) else math.inf
        passed = med <= REF_RATIO_MAX
        ok = ok and passed
        out[st] = {"delta_mm": delta.tolist(), "eps_mm": s["eps_mm"].tolist(), "ratio": ratio.tolist(),
                   "median_ratio": med, "passed": bool(passed)}
    return {"gate": "G0-r", "references": [int(i) for i in refs], "items": out, "passed": bool(ok)}


def discrepancy_table(musmorph: dict, reps: dict, rows) -> dict:
    """MT-D3: δᵢ, εᵢ y δᵢ / εᵢ por atlas y landmark."""
    out = {}
    for st in STAGES:
        s = repeat_stats(reps[st])
        m = np.asarray(musmorph[st], float)[[int(i) - 1 for i in rows]]
        delta = np.linalg.norm(s["mean"] - m, axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = delta / s["eps_mm"]
        out[st] = {label(i): {"delta_mm": float(dl), "eps_mm": float(e), "ratio": float(r), "n": int(n)}
                   for i, dl, e, r, n in zip(rows, delta, s["eps_mm"], ratio, s["n_valid"])}
    return out


# ---------------------------------------------------------------- parte B (descriptiva)
def kabsch(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """Rotación (sin reflexión) que mejor lleva ``src`` centrado a ``dst`` centrado: x_rot = x @ R."""
    s = np.asarray(src, float) - np.asarray(src, float).mean(axis=0)
    t = np.asarray(dst, float) - np.asarray(dst, float).mean(axis=0)
    u, _, vt = np.linalg.svd(s.T @ t)
    dfix = np.diag([1.0, 1.0, np.sign(np.linalg.det(u @ vt))])
    return u @ dfix @ vt


def specimen_offsets(spec_manual: dict, spec_musmorph: dict, atlas_musmorph: np.ndarray,
                     atlas_offset: np.ndarray, rows=TARGETS) -> dict:
    """§4.5 para un estadio. Cada vector manual − MusMorph de un espécimen se gira al marco del atlas con la rotación
    de Kabsch entre sus 22 landmarks de MusMorph y los del atlas (solo landmarks; sin registro de imágenes). Se
    promedian por estadio y se mide el ángulo con el vector manual − MusMorph del atlas (6 × 3 aplanado)."""
    vecs, per = [], {}
    for sid, man in spec_manual.items():
        mus = np.asarray(spec_musmorph[sid], float)
        R = kabsch(mus[:aa.N_HOMOLOGOUS], np.asarray(atlas_musmorph, float)[:aa.N_HOMOLOGOUS])
        off = (np.asarray(man, float) - mus[[int(i) - 1 for i in rows]]) @ R
        per[sid] = {"delta_mm": np.linalg.norm(off, axis=1).tolist()}
        if not np.isnan(off).any():
            vecs.append(off.ravel())
    if not vecs:
        return {"n": 0, "per_specimen": per}
    mean = np.mean(vecs, axis=0)
    ref = np.asarray(atlas_offset, float).ravel()
    return {"n": len(vecs), "mean_offset_mm": mean.reshape(-1, 3).tolist(),
            "angle_with_atlas_offset_deg": lm.angle_deg(mean, ref), "per_specimen": per}
