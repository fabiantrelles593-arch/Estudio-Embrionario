"""QC-LM (docs/morpho_trace/PREREGISTRO_QC_LANDMARKS.md): control de calidad de los landmarks publicados de MusMorph.

  python scripts/landmark_qc.py select --ids results/onto_map/seleccion.json --out results/landmark_qc/muestra.json
  python scripts/landmark_qc.py download --sample results/landmark_qc/muestra.json \\
      --out data/external/musmorph/qc_images --reuse data/external/musmorph/impc_e15_5_confirm ...
  python scripts/landmark_qc.py measure --sample results/landmark_qc/muestra.json --out results/landmark_qc/medidas
  python scripts/landmark_qc.py analyze --sample results/landmark_qc/muestra.json \\
      --measures results/landmark_qc/medidas --out results/landmark_qc/analisis.json

``select``: muestra aleatoria simple de 60 especímenes por estadio del confirmatorio de ONTO-MAP (semilla 20261119),
disjunta del piloto que usó MT-A. ``measure``: para cada espécimen, distancia de sus 540 landmarks publicados al
tejido sobre Otsu a resolución completa (mismo método y umbral de 0,23 mm que MT-A v1.1); un JSON por espécimen
(reanudable). ``analyze``: QC1 (prevalencia por estadio), QC2 (cambio de |d| al quitar los que no cumplen) y QC3
(descriptivos), con remuestreo por espécimen. Datos y resultados fuera de git.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atlas_effect_gates as gates  # noqa: E402

from geovida import atlas_effect as ae  # noqa: E402
from geovida import landmarks as lm  # noqa: E402
from geovida.provenance import git_state  # noqa: E402

SEED = 20261119
N_PER_STAGE = 60
N_BOOT = 2000
STAGES = ("E15.5", "E18.5")
MIN_MEASURED = 57             # G1: ≥ 57 de 60 por estadio
QC2_MIN_FAIL15, QC2_MIN_PASS = 3, 30
REL = 0.05                    # cambio relativo de |d| que se considera relevante (QC2)
QC1_REFUTE = 0.05             # diferencia de prevalencias por debajo de la cual se considera nula (QC1)


def select(sel: dict, n: int = N_PER_STAGE, seed: int = SEED) -> dict:
    """Muestra aleatoria simple sin reemplazo por estadio, sobre la lista ordenada del confirmatorio."""
    rng = np.random.default_rng(seed)
    out = {}
    for st in STAGES:
        pool = sorted(sel["confirm"][st])
        out[st] = [pool[i] for i in rng.choice(len(pool), size=n, replace=False)]
    return {"seed": seed, "n_per_stage": n, "source": "confirm de results/onto_map/seleccion.json", "sample": out}


def measure_one(name: str, image: Path, tag: Path) -> dict:
    """Distancia al tejido de los landmarks publicados de un espécimen (sin guardar volúmenes)."""
    from geovida import minc
    shape, affine, _ = minc.minc_header(image)
    otsu = ae.stream_volume(lambda: minc.minc_slabs(image, gates.FACTOR), shape, affine, factor=gates.FACTOR)["otsu"]
    pts = lm.read_tag(tag)
    d = ae.distance_to_tissue(minc.minc_box_reader(image), shape, affine, pts, otsu, gates.SEARCH_RADIUS_MM)
    within = float(np.mean(d <= gates.MAX_DIST_MM))
    return {"name": name, "stage": gates.stage_of(name), "otsu": otsu, "within": within,
            "passed": within >= gates.G0_MIN_INSIDE, "median_mm": float(np.median(d)),
            "p90_mm": float(np.percentile(d, 90)), "n_beyond_radius": int(np.sum(~np.isfinite(d))),
            "affine": affine.tolist()}


def _d_length(c15: np.ndarray, c18: np.ndarray) -> float:
    """|d| con el mismo procedimiento que ONTO-MAP y G0-d (GPA único, coordenadas tangentes)."""
    return float(ae.published_direction(c15, c18)["d_length"])


def analyze(rows: list[dict], configs: dict, atlas_affine: dict, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """``rows``: medidas por espécimen; ``configs``: {nombre: (540, 3)} landmarks publicados."""
    by = {st: [r for r in rows if r["stage"] == st] for st in STAGES}
    g1 = {st: len(v) for st, v in by.items()}
    grid = all(np.allclose(r["affine"], atlas_affine[r["stage"]], atol=1e-6) for r in rows)
    gates_ = {"G1": {"measured": g1, "required": MIN_MEASURED, "passed": all(n >= MIN_MEASURED for n in g1.values())},
              "G2": {"same_grid_as_atlas": grid, "passed": grid}}
    fail = {st: np.array([not r["passed"] for r in by[st]]) for st in STAGES}
    rng = np.random.default_rng(seed)

    # QC1: diferencia de prevalencias de «no cumple», E15.5 − E18.5
    p = {st: float(fail[st].mean()) if len(fail[st]) else float("nan") for st in STAGES}
    diff = p["E15.5"] - p["E18.5"]
    boot = [rng.choice(fail["E15.5"], len(fail["E15.5"])).mean() - rng.choice(fail["E18.5"], len(fail["E18.5"])).mean()
            for _ in range(n_boot)]
    lo, hi = (float(x) for x in np.percentile(boot, [2.5, 97.5]))
    qc1 = {"fail_rate": p, "n_fail": {st: int(fail[st].sum()) for st in STAGES}, "diff": diff, "ci": [lo, hi],
           "verdict": "apoyada" if lo > 0 else ("refutada" if hi < QC1_REFUTE else "no concluyente")}

    # QC2: cambio relativo de |d| al quitar los que no cumplen
    names = {st: [r["name"] for r in by[st]] for st in STAGES}
    ok = {st: ~fail[st] for st in STAGES}
    evaluable = int(fail["E15.5"].sum()) >= QC2_MIN_FAIL15 and all(int(ok[st].sum()) >= QC2_MIN_PASS for st in STAGES)
    qc2 = {"evaluable": evaluable}
    qc3 = {}
    if evaluable:
        c = {st: np.array([configs[b] for b in names[st]]) for st in STAGES}

        def rel(i15, i18):
            a = _d_length(c["E15.5"][i15], c["E18.5"][i18])
            k15, k18 = i15[ok["E15.5"][i15]], i18[ok["E18.5"][i18]]
            b = _d_length(c["E15.5"][k15], c["E18.5"][k18])
            return (b - a) / a, a, b

        n15, n18 = len(names["E15.5"]), len(names["E18.5"])
        r0, d_all, d_pass = rel(np.arange(n15), np.arange(n18))
        rb = [rel(rng.integers(0, n15, n15), rng.integers(0, n18, n18))[0] for _ in range(n_boot)]
        lo2, hi2 = (float(x) for x in np.percentile(rb, [2.5, 97.5]))
        if (lo2 > 0 or hi2 < 0) and abs(r0) >= REL:
            v2 = "apoyada"
        elif lo2 > -REL and hi2 < REL:
            v2 = "refutada"
        else:
            v2 = "no concluyente"
        qc2.update({"d_all": d_all, "d_pass": d_pass, "relative_change": r0, "ci": [lo2, hi2], "verdict": v2})
        qc3 = {"note": "descriptivo", "d_all": d_all, "d_pass": d_pass}
    else:
        qc2["verdict"] = "no evaluable"
    failed = [k for k, g in gates_.items() if not g["passed"]]
    if failed:
        qc1["verdict"] = qc2["verdict"] = "no evaluable"
    return {"gates": gates_, "failed_gates": failed, "qc1": qc1, "qc2": qc2, "qc3": qc3, "n_boot": n_boot, "seed": seed}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select")
    s.add_argument("--ids", required=True)
    s.add_argument("--out", required=True)
    for name in ("download", "measure", "analyze"):
        q = sub.add_parser(name)
        q.add_argument("--sample", required=True)
        q.add_argument("--images", default="data/external/musmorph/qc_images")
        q.add_argument("--landmarks", default="data/external/musmorph/landmarks_confirm")
        q.add_argument("--out", required=True)
        if name == "download":
            q.add_argument("--reuse", nargs="*", default=[])
        if name == "analyze":
            q.add_argument("--measures", default="results/landmark_qc/medidas")
            q.add_argument("--atlas", default="data/external/musmorph/atlas")
            q.add_argument("--n-boot", type=int, default=N_BOOT)
    a = ap.parse_args(argv)
    if a.cmd == "select":
        res = select(json.loads(Path(a.ids).read_text(encoding="utf-8")))
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
        print({st: len(v) for st, v in res["sample"].items()})
        return 0
    sample = json.loads(Path(a.sample).read_text(encoding="utf-8"))["sample"]
    names = sample["E15.5"] + sample["E18.5"]
    if a.cmd == "download":
        log = gates.fetch([f"{b}.mnc" for b in names], gates.IMAGES_RECORD, Path(a.out), reuse=a.reuse)
        bad = [r["filename"] for r in log if not r["md5_ok"]]
        print(f"{len(log) - len(bad)} de {len(names)} con MD5 correcto" + (f"; fallan {bad}" if bad else ""))
        return 0 if not bad else 1
    if a.cmd == "measure":
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        for b in names:
            dest = out / f"{b}.json"
            if dest.exists():
                continue
            try:
                row = measure_one(b, Path(a.images) / f"{b}.mnc", Path(a.landmarks) / f"{b}_Head_Landmarks.tag")
            except Exception as exc:  # cuenta como no medido en G1
                print(f"  {b}: ERROR {type(exc).__name__}: {exc}", flush=True)
                continue
            dest.write_text(json.dumps(row) + "\n", encoding="utf-8")
            print(f"  {b}: {row['within']:.1%}", flush=True)
        return 0
    from geovida import minc
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(a.measures).glob("*.json"))
            if p.stem in names]
    configs = {r["name"]: lm.read_tag(Path(a.landmarks) / f"{r['name']}_Head_Landmarks.tag") for r in rows}
    atlas_aff = {st: minc.minc_header(Path(a.atlas) / gates.ATLAS_IMAGES[st])[1] for st in STAGES}
    res = {"study": "QC-LM", **analyze(rows, configs, atlas_aff, n_boot=a.n_boot), "provenance": git_state()}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("failed_gates", "qc1", "qc2")}, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
