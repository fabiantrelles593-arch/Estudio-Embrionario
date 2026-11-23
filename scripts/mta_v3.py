"""MT-A v3 (docs/morpho_trace/PREREGISTRO_ATLAS_v3.md): registro limitado a la cabeza, con puertas baratas primero.

    python scripts/mta_v3.py sample    # 2 + 2 de piloto y 18 + 18 confirmatorios entre los de QC-LM no usados en v2
    python scripts/mta_v3.py g0a4      # G0-a‴: los 40 cumplen la regla de QC-LM
    python scripts/mta_v3.py g0m       # G0-m: la caja de cada atlas contiene sus landmarks y cabe en la imagen
    python scripts/mta_v3.py pilot     # puerta S: 4 especímenes, registro propio, C1/C2/C3 (12 registros)
    python scripts/mta_v3.py g0t       # G0-t′: un registro atlas E18.5 → atlas E15.5 con el candidato elegido
    python scripts/mta_v3.py own       # G1′: los 36 confirmatorios, registro propio
    python scripts/mta_v3.py cross     # los 36 registros cruzados (solo si G1′ pasó)
    python scripts/mta_v3.py analyze   # G2 y MT-A1–MT-A3

Cada orden comprueba que las puertas anteriores pasaron y se niega a seguir si no. Los registros son reanudables
(un JSON por registro). Los resultados van a ``results/morpho_trace/v3/`` (fuera de git). Solo datos animales
publicados (MusMorph/IMPC, CC BY 4.0); nada humano ni clínico.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atlas_effect_gates as gates  # noqa: E402

from geovida import atlas_effect as ae  # noqa: E402
from geovida import landmarks as lm  # noqa: E402
from geovida.provenance import git_state  # noqa: E402

SEED = 20261123
STAGES = ("E15.5", "E18.5")
N_PILOT, N_CONFIRM = 2, 18
MASK_MM, CROP_MM = 1.0, 2.0
CANDIDATES = {"C1": None, "C2": 4, "C3": 8}          # malla de la B-spline; None = solo afín
SIMPLICITY = ("C1", "C2", "C3")
S_MIN_BETTER = 3                                     # de 4 especímenes del piloto
TIE = 0.001
N_CONFIRM_REGS = 72
MAX_HOURS = 72.0
G2_REQUIRED = 15                                     # de 18 por estadio
OUT = Path("results/morpho_trace/v3")


# ---------------------------------------------------------------- muestra y puertas sin registro
def draw(qc_sample: dict, passed: dict, v2_sample: dict, seed: int = SEED,
         n_pilot: int = N_PILOT, n_confirm: int = N_CONFIRM) -> dict:
    """Piloto y confirmatorio, por semilla, entre los de QC-LM que cumplen y no están en la muestra de v2."""
    rng = np.random.default_rng(seed)
    out = {"seed": seed, "pilot": {}, "confirm": {}}
    for st in STAGES:
        rem = sorted(n for n in qc_sample[st] if passed[n] and n not in set(v2_sample[st]))
        if len(rem) < n_pilot + n_confirm:
            raise ValueError(f"{st}: quedan {len(rem)}; hacen falta {n_pilot + n_confirm}")
        pilot = sorted(rng.choice(rem, size=n_pilot, replace=False).tolist())
        rest = [n for n in rem if n not in pilot]
        out["pilot"][st] = pilot
        out["confirm"][st] = sorted(rng.choice(rest, size=n_confirm, replace=False).tolist())
        out[f"n_remaining_{st}"] = len(rem)
    body = {"pilot": out["pilot"], "confirm": out["confirm"]}
    out["sample_sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    return out


def g0a4(sample: dict, passed: dict, within: dict) -> dict:
    """G0-a‴: los 40 (piloto + confirmatorio) cumplen la regla de QC-LM, releída desde los archivos de medida."""
    names = [n for part in ("pilot", "confirm") for st in STAGES for n in sample[part][st]]
    rows = [{"name": n, "within": within[n], "passed": bool(passed[n])} for n in names]
    return {"gate": "G0-a‴", "items": rows, "passed": len(rows) == 40 and all(r["passed"] for r in rows)}


def image_bounds(shape, affine) -> tuple[np.ndarray, np.ndarray]:
    """Extremos (en el mundo) de los centros de vóxel del volumen."""
    a = np.asarray(affine, dtype=float)
    corners = np.array([[i, j, k] for i in (0, shape[0] - 1) for j in (0, shape[1] - 1) for k in (0, shape[2] - 1)])
    w = corners @ a[:3, :3].T + a[:3, 3]
    return w.min(axis=0), w.max(axis=0)


def g0m_row(stage: str, tags: np.ndarray, shape, affine) -> dict:
    lo1, hi1 = ae.head_box(tags, MASK_MM)
    lo2, hi2 = ae.head_box(tags, CROP_MM)
    blo, bhi = image_bounds(shape, affine)
    contains = bool(np.all(tags >= lo1) and np.all(tags <= hi1))
    fits = bool(np.all(lo2 >= blo) and np.all(hi2 <= bhi))
    return {"atlas": stage, "mask_box_mm": (hi1 - lo1).tolist(), "crop_box_mm": (hi2 - lo2).tolist(),
            "contains_landmarks": contains, "crop_inside_image": fits, "passed": contains and fits}


# ---------------------------------------------------------------- registro de cabeza
def prepare(arr: np.ndarray, affine, tags: np.ndarray):
    """Imagen recortada a la caja de cabeza (2 mm) del atlas cuya rejilla comparte, como imagen de SimpleITK."""
    lo, hi = ae.head_box(tags, CROP_MM)
    sub, a = ae.crop_to_box(arr, affine, lo, hi)
    return ae.to_sitk(sub, a), sub, a


def initial_transform(tags_fixed: np.ndarray, tags_moving_grid: np.ndarray, same: bool):
    """T₀ (§3.2): identidad en el registro propio; afín entre los landmarks de los dos atlas en el cruzado."""
    m = np.eye(4) if same else ae.landmark_affine(tags_fixed, tags_moving_grid)
    return ae.affine_to_sitk(m)


def register_pair(atlas: dict, tags: dict, fixed_stage: str, moving_x4: dict, moving_stage: str,
                  meshes) -> dict:
    """Registra una imagen (en la rejilla del atlas ``moving_stage``) al atlas ``fixed_stage`` y transfiere los
    landmarks de ese atlas. Devuelve {malla: fila}."""
    sitk = ae._sitk()
    fixed, fsub, fa = prepare(atlas[fixed_stage]["downsampled"], atlas[fixed_stage]["affine_ds"], tags[fixed_stage])
    moving, _, _ = prepare(moving_x4["downsampled"], moving_x4["affine_ds"], tags[moving_stage])
    lo, hi = ae.head_box(tags[fixed_stage], MASK_MM)
    mask = sitk.GetImageFromArray(ae.box_mask(fsub.shape, fa, lo, hi))
    mask.CopyInformation(fixed)
    init = initial_transform(tags[fixed_stage], tags[moving_stage], fixed_stage == moving_stage)
    res = ae.register_head(fixed, moving, fixed_mask=mask, initial=init, meshes=meshes, seed=SEED)
    out = {}
    for mesh, (tx, info) in res.items():
        pts = ae.transfer_points(tx, tags[fixed_stage])
        metrics = [v for k, v in info.items() if k.endswith("_metric")]
        out[mesh] = {"info": info, "points": pts.tolist(),
                     "ok": bool(np.all(np.isfinite(pts)) and all(np.isfinite(metrics)))}
    return out


def _cand_of(mesh) -> str:
    return next(c for c, m in CANDIDATES.items() if m == mesh)


def run_registrations(names: list[str], candidates: list[str], own: bool, images: Path, atlas: dict, tags: dict,
                      cache: Path, out: Path, log=print) -> list[dict]:
    """Registro propio (``own``) o cruzado de cada espécimen con los candidatos dados. Reanudable."""
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in names:
        st = gates.stage_of(name)
        fst = st if own else next(s for s in STAGES if s != st)
        dest = {c: out / f"{name}__atlas_{fst}__{c}.json" for c in candidates}
        todo = [c for c in candidates if not dest[c].exists()]
        if todo:
            t0 = time.time()
            base = {"specimen": name, "stage": st, "atlas": fst, "own": own, "factor": gates.FACTOR}
            try:
                res = register_pair(atlas, tags, fst, gates.load_x4(images / f"{name}.mnc", cache), st,
                                    [CANDIDATES[c] for c in candidates])
                made = {_cand_of(mesh): row for mesh, row in res.items()}
            except Exception as exc:  # G2 cuenta los registros que fallan; no se detiene la serie
                made = {c: {"ok": False, "error": f"{type(exc).__name__}: {exc}"} for c in candidates}
            secs = round(time.time() - t0, 1)
            for c in todo:
                row = {**base, "candidate": c, **made[c], "seconds_pair": secs}
                dest[c].write_text(json.dumps(row, default=float) + "\n", encoding="utf-8")
                log(f"  {name} → atlas {fst} [{c}]: {'ok' if row['ok'] else 'FALLO'} ({secs} s)")
        rows += [json.loads(dest[c].read_text(encoding="utf-8")) for c in candidates]
    return rows


# ---------------------------------------------------------------- puertas con registro
def rho(a, b) -> float:
    return float(lm.procrustes_distances(np.asarray(a, float), np.asarray(b, float))["rho"])


def select_candidate(rho_by_cand: dict, rho_identity: list) -> dict:
    """Puerta S (§4): apto si mejora la identidad en ≥ 3 de 4 y su mediana es menor que la de la identidad; se elige
    el apto de menor mediana y, a menos de 0,001 de ella, el más simple. Sin aptos, no pasa."""
    ident = np.asarray(rho_identity, float)
    mi = float(np.median(ident))
    rows = {}
    for c in SIMPLICITY:
        if c not in rho_by_cand:
            continue
        r = np.asarray(rho_by_cand[c], float)
        ok = bool(len(r) == len(ident) and np.all(np.isfinite(r)))
        better = int(np.sum(r < ident)) if ok else 0
        med = float(np.median(r)) if ok else float("nan")
        rows[c] = {"rho": r.tolist(), "median": med, "n_better_than_identity": better,
                   "apt": ok and better >= S_MIN_BETTER and med < mi}
    apt = [c for c in SIMPLICITY if rows.get(c, {}).get("apt")]
    chosen = None
    if apt:
        best = min(rows[c]["median"] for c in apt)
        chosen = next(c for c in apt if rows[c]["median"] <= best + TIE)
    return {"gate": "S", "rho_identity": ident.tolist(), "median_identity": mi, "candidates": rows,
            "chosen": chosen, "passed": chosen is not None}


def g0t(seconds_one: float) -> dict:
    hours = seconds_one * N_CONFIRM_REGS / 3600
    return {"gate": "G0-t′", "seconds_one": round(seconds_one, 1), "hours_estimated": round(hours, 1),
            "max_hours": MAX_HOURS, "passed": bool(hours <= MAX_HOURS)}


def g2(rows: list[dict], confirm: dict, candidate: str) -> dict:
    """G2: un espécimen es válido si sus dos registros (propio y cruzado) con el candidato terminaron bien."""
    ok = {(r["specimen"], r["own"]) for r in rows if r.get("candidate") == candidate and r.get("ok")}
    valid = {st: [n for n in confirm[st] if (n, True) in ok and (n, False) in ok] for st in STAGES}
    return {"valid": {st: len(v) for st, v in valid.items()}, "required": G2_REQUIRED,
            "names": valid, "passed": all(len(v) >= G2_REQUIRED for v in valid.values())}


# ---------------------------------------------------------------- utilidades de la línea de órdenes
def _read(p: Path) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _write(res: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    res["provenance"] = git_state()
    out.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k not in ("items", "provenance", "pilot", "confirm", "names")},
                     default=float))


def _require(*stems: str) -> None:
    """Se niega a seguir si una puerta anterior falta o no pasó."""
    for s in stems:
        p = OUT / f"{s}.json"
        if not p.exists() or not _read(p).get("passed"):
            raise SystemExit(f"la puerta {s} no está superada ({p}); el preregistro no permite seguir")


def _atlas(atlas_dir: Path, cache: Path):
    atlas = {st: gates.load_x4(atlas_dir / gates.ATLAS_IMAGES[st], cache) for st in STAGES}
    tags = {st: np.asarray(lm.read_tag(atlas_dir / gates.ATLAS_TAG[st]), float) for st in STAGES}
    return atlas, tags


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["sample", "g0a4", "g0m", "pilot", "g0t", "own", "cross", "analyze"])
    ap.add_argument("--qc", default="results/landmark_qc/muestra.json")
    ap.add_argument("--measures", default="results/landmark_qc/medidas")
    ap.add_argument("--v2", default="results/morpho_trace/muestra_v2.json")
    ap.add_argument("--sel-v2", default="results/morpho_trace/v2/seleccion_v2.json", help="confirmatorio de 597 (d)")
    ap.add_argument("--atlas", default="data/external/musmorph/atlas")
    ap.add_argument("--images", default="data/external/musmorph/qc_images")
    ap.add_argument("--landmarks", default="data/external/musmorph/landmarks_confirm")
    ap.add_argument("--cache", default="results/morpho_trace/cache")
    a = ap.parse_args(argv)
    atlas_dir, images, cache, lmdir = Path(a.atlas), Path(a.images), Path(a.cache), Path(a.landmarks)

    def pub(name):
        return np.asarray(lm.read_tag(lmdir / f"{name}_Head_Landmarks.tag"), float)

    if a.cmd == "sample":
        if (OUT / "muestra_v3.json").exists():
            raise SystemExit("la muestra ya existe; no se vuelve a extraer")
        passed = {p.stem: _read(p)["passed"] for p in Path(a.measures).glob("*.json")}
        res = draw(_read(a.qc)["sample"], passed, _read(a.v2)["sample"])
        _write(res, OUT / "muestra_v3.json")
        return 0
    sample = _read(OUT / "muestra_v3.json")
    if a.cmd == "g0a4":
        meas = {p.stem: _read(p) for p in Path(a.measures).glob("*.json")}
        res = g0a4(sample, {k: v["passed"] for k, v in meas.items()}, {k: v["within"] for k, v in meas.items()})
        _write(res, OUT / "g0a4.json")
        return 0 if res["passed"] else 1
    if a.cmd == "g0m":
        from geovida import minc
        rows = []
        for st in STAGES:
            shape, affine, _ = minc.minc_header(atlas_dir / gates.ATLAS_IMAGES[st])
            rows.append(g0m_row(st, np.asarray(lm.read_tag(atlas_dir / gates.ATLAS_TAG[st]), float), shape, affine))
        res = {"gate": "G0-m", "items": rows, "passed": all(r["passed"] for r in rows)}
        _write(res, OUT / "g0m.json")
        return 0 if res["passed"] else 1
    atlas, tags = _atlas(atlas_dir, cache)
    if a.cmd == "pilot":
        _require("g0a4", "g0m")
        names = sample["pilot"]["E15.5"] + sample["pilot"]["E18.5"]
        rows = run_registrations(names, list(SIMPLICITY), True, images, atlas, tags, cache, OUT / "piloto")
        by = {(r["specimen"], r["candidate"]): r for r in rows}
        rc = {c: [rho(by[(n, c)]["points"], pub(n)) if by[(n, c)].get("ok") else float("nan") for n in names]
              for c in SIMPLICITY}
        ident = [rho(tags[gates.stage_of(n)], pub(n)) for n in names]
        res = {**select_candidate(rc, ident), "specimens": names}
        _write(res, OUT / "s.json")
        return 0 if res["passed"] else 1
    chosen = _read(OUT / "s.json").get("chosen") if (OUT / "s.json").exists() else None
    if a.cmd == "g0t":
        _require("g0a4", "g0m", "s")
        t0 = time.time()
        res_pair = register_pair(atlas, tags, "E15.5", atlas["E18.5"], "E18.5", [CANDIDATES[chosen]])
        secs = time.time() - t0
        row = next(iter(res_pair.values()))
        res = {**g0t(secs), "candidate": chosen, "sensitivity_1_points": row["points"], "ok": row["ok"]}
        _write(res, OUT / "g0t3.json")
        return 0 if res["passed"] else 1
    confirm = sample["confirm"]
    names = confirm["E15.5"] + confirm["E18.5"]
    if a.cmd == "own":
        _require("g0a4", "g0m", "s", "g0t3")
        rows = run_registrations(names, [chosen], True, images, atlas, tags, cache, OUT / "registros")
        okn = [r["specimen"] for r in rows if r.get("ok")]
        res = {"gate": "G1′", "candidate": chosen, "n_ok": len(okn),
               **ae.gate_g1_identity([next(r for r in rows if r["specimen"] == n)["points"] for n in okn],
                                     [tags[gates.stage_of(n)] for n in okn], [pub(n) for n in okn],
                                     {st: [pub(n) for n in confirm[st]] for st in STAGES})}
        _write(res, OUT / "g1.json")
        return 0 if res["passed"] else 1
    if a.cmd == "cross":
        _require("g0a4", "g0m", "s", "g0t3", "g1")
        run_registrations(names, [chosen], False, images, atlas, tags, cache, OUT / "registros")
        return 0
    # analyze
    _require("g0a4", "g0m", "s", "g0t3", "g1")
    rows = [_read(p) for p in sorted((OUT / "registros").glob("*.json"))]
    gate2 = g2(rows, confirm, chosen)
    res = {"analysis": "MT-A v3", "candidate": chosen, "gates": {"G2": gate2}}
    if gate2["passed"]:
        by = {(r["specimen"], r["atlas"]): r for r in rows if r.get("candidate") == chosen}
        valid = gate2["names"]["E15.5"] + gate2["names"]["E18.5"]
        pub_d = gates._load(_read(a.sel_v2), "confirm", lmdir)   # las 597 de v2: d no cambia
        res["mta"] = ae.atlas_effect(pub_d["E15.5"], pub_d["E18.5"],
                                     np.array([by[(n, "E15.5")]["points"] for n in valid]),
                                     np.array([by[(n, "E18.5")]["points"] for n in valid]),
                                     [gates.stage_of(n) for n in valid], seed=SEED)
        res["verdict"] = res["mta"]["mta1"]["verdict"]
    else:
        res["verdict"] = "no evaluable"
    _write(res, OUT / "analisis.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
