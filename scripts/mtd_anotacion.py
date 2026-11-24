"""MT-D (docs/morpho_trace/PREREGISTRO_ANOTACION_MANUAL.md): anotación manual independiente de los landmarks 17–22.

    python scripts/mtd_anotacion.py prepare      # referencias, muestra, códigos, volúmenes NIfTI y hoja de sesiones
    python scripts/mtd_anotacion.py gates-pre    # G0-e (espacio común) y G0-c (fantoma; necesita su anotación)
    python scripts/mtd_anotacion.py gates-post   # G0-ε y G0-r, con las anotaciones de los atlas
    python scripts/mtd_anotacion.py analyze      # MT-D1–MT-D3 (solo si las cuatro puertas pasaron)

Los puntos manuales los coloca una persona en 3D Slicer (D1); este script no genera ninguno. Volúmenes, hoja de
sesiones y anotaciones en ``data/manual/mtd/``; el manifiesto (qué código es cada imagen) y los resultados en
``results/morpho_trace/mtd/``; todo fuera de git. Solo datos animales publicados (MusMorph/IMPC, CC BY 4.0).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atlas_effect_gates as gates  # noqa: E402
from mtb_anclaje import load_inputs  # noqa: E402

from geovida import atlas_anchor as aa  # noqa: E402
from geovida import landmarks as lm  # noqa: E402
from geovida import manual_landmarks as ml  # noqa: E402
from geovida.provenance import git_state  # noqa: E402

OUT = Path("results/morpho_trace/mtd")
WORK = Path("data/manual/mtd")
CROP_MARGIN_MM = 2.0
OTSU_STRIDE = 4
PHANTOM = "P0000"


def _read(p: Path) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _write(res: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    res["provenance"] = git_state()
    out.write_text(json.dumps(res, indent=1, default=float, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k not in ("provenance", "tasks")}, default=float,
                     ensure_ascii=False)[:4000])


# ---------------------------------------------------------------- prepare
def specimen_ids(images: Path) -> dict[str, list[str]]:
    names = sorted(p.stem for p in images.glob("*.mnc") if "_Segs" not in p.name)
    return {st: [n for n in names if f"_{st}_" in n] for st in aa.STAGES}


def export_volume(src: Path, tags: np.ndarray, dst: Path) -> dict:
    from geovida import minc
    shape, affine, _ = minc.minc_header(src)
    lo, hi = tags.min(axis=0) - CROP_MARGIN_MM, tags.max(axis=0) + CROP_MARGIN_MM
    sl = ml.box_slices(shape, affine, lo, hi)
    arr = minc.minc_box_reader(src)(sl)
    ml.save_nifti(arr, ml.shifted_affine(affine, sl), dst)
    return {"shape": list(arr.shape), "crop": [[s.start, s.stop] for s in sl]}


def sheet(plan: dict, refs: list[int]) -> str:
    lines = ["# MT-D — hoja de sesiones para la persona que anota", "",
             "No abras `results/morpho_trace/mtd/` ni ningún resultado de MT-B o MT-C hasta terminar.", "",
             "* Definiciones de los landmarks: Tabla S2 de Devine et al. 2022 (numeración de MusMorph).",
             f"* Coloca en cada volumen, con estas etiquetas exactas: {', '.join(ml.label(i) for i in ml.TARGETS)} "
             f"y {', '.join(ml.label(i) for i in refs)}.",
             "* Un landmark que no puedas localizar: no lo coloques (no lo estimes).",
             "* Guarda los puntos como `annotations/<tarea>.mrk.json` (Markups de Slicer, sin cambiar la convención).",
             "* Sesiones separadas por al menos 24 h. En cada tarea empieza desde cero: no abras anotaciones previas.",
             "* Anota fecha, duración y comentarios de cada sesión en `annotations/registro.md`.", "",
             f"## Sesión 0 — prueba de coordenadas (G0-c)", "",
             f"Abre `volumes/{PHANTOM}.nii.gz`. Coloca un punto en el centro de cada esfera: `L1` en la pequeña, `L2` en "
             f"la mediana y `L3` en la grande. Guarda `annotations/{PHANTOM}.mrk.json`.", ""]
    for s in sorted({t["session"] for t in plan["tasks"]}):
        lines += [f"## Sesión {s}", "", "| Tarea | Volumen |", "|---|---|"]
        lines += [f"| {t['task']} | `volumes/{t['volume']}.nii.gz` |" for t in plan["tasks"] if t["session"] == s]
        lines.append("")
    return "\n".join(lines)


def run_prepare(a) -> dict:
    mtc = _read(Path(a.mtc))
    refs = ml.choose_references(mtc["contributions"]["ratio_to_spread"])
    plan = ml.plan_sessions(specimen_ids(Path(a.images)))
    atlas_dir, lmdir, images = Path(a.atlas), Path(a.landmarks), Path(a.images)
    vols = {}
    for t in plan["tasks"]:
        if t["volume"] in vols:
            continue
        if t["kind"] == "atlas":
            src = atlas_dir / gates.ATLAS_IMAGES[t["stage"]]
            tags = np.asarray(lm.read_tag(atlas_dir / gates.ATLAS_TAG[t["stage"]]), float)
        else:
            src = images / f"{t['id']}.mnc"
            tags = np.asarray(lm.read_tag(lmdir / f"{t['id']}_Head_Landmarks.tag"), float)
        vols[t["volume"]] = {"source": src.name, **export_volume(src, tags, WORK / "volumes" / f"{t['volume']}.nii.gz")}
    from geovida import minc
    _, aff15, _ = minc.minc_header(atlas_dir / gates.ATLAS_IMAGES["E15.5"])
    vol, aff, truth = ml.phantom(aff15[:3, :3])
    ml.save_nifti(vol, aff, WORK / "volumes" / f"{PHANTOM}.nii.gz")
    (WORK / "annotations").mkdir(parents=True, exist_ok=True)
    (WORK / "SESIONES.md").write_text(sheet(plan, refs["references"]) + "\n", encoding="utf-8")
    return {"step": "prepare", **refs, **plan, "volumes": vols,
            "phantom": {"code": PHANTOM, "truth_ras_mm": {k: v.tolist() for k, v in truth.items()},
                        "voxel_mm": float(np.max(np.linalg.norm(aff[:3, :3], axis=0)))}}


# ---------------------------------------------------------------- puertas
def otsu_of(path: Path) -> float:
    from skimage.filters import threshold_otsu

    from geovida import minc
    parts = [slab[::OTSU_STRIDE, ::OTSU_STRIDE, ::OTSU_STRIDE].ravel()
             for _, slab in minc.minc_slabs(path, 64 * OTSU_STRIDE)]
    return float(threshold_otsu(np.concatenate(parts)))


def run_gates_pre(a, manifest: dict) -> dict:
    from geovida import minc
    atlas_dir = Path(a.atlas)
    g_e = {}
    for st in aa.STAGES:
        img = atlas_dir / gates.ATLAS_IMAGES[st]
        shape, affine, _ = minc.minc_header(img)
        read = minc.minc_box_reader(img)
        pts = aa.subset_rows(np.asarray(lm.read_tag(atlas_dir / gates.ATLAS_TAG[st]), float), aa.N_HOMOLOGOUS)
        g_e[st] = ml.gate_space(pts, shape, affine,
                                lambda idx: np.array([read([slice(i, i + 1) for i in p])[0, 0, 0] for p in idx]),
                                otsu_of(img))
    e_ok = all(v["passed"] for v in g_e.values())
    ph = manifest["phantom"]
    f = WORK / "annotations" / f"{ph['code']}.mrk.json"
    if f.exists():
        truth = {int(k): np.asarray(v, float) for k, v in ph["truth_ras_mm"].items()}
        g_c = {"gate": "G0-c", **ml.gate_phantom(truth, ml.read_markups(f), ph["voxel_mm"])}
    else:
        g_c = {"gate": "G0-c", "status": "pendiente: falta la anotación del fantoma", "passed": False}
    return {"gates": {"G0-e": {"gate": "G0-e", "items": g_e, "passed": e_ok}, "G0-c": g_c},
            "passed": bool(e_ok and g_c["passed"])}


def load_annotations(manifest: dict, refs: list[int]) -> dict:
    rows = list(ml.TARGETS) + list(refs)
    atlas = {st: [] for st in aa.STAGES}
    spec: dict[str, list] = {}
    files = {}
    for t in manifest["tasks"]:
        f = WORK / "annotations" / f"{t['task']}.mrk.json"
        pts = ml.points_array(ml.read_markups(f), rows) if f.exists() else np.full((len(rows), 3), np.nan)
        files[t["task"]] = f.exists()
        if t["kind"] == "atlas":
            atlas[t["stage"]].append(pts)
        else:
            spec.setdefault(t["id"], []).append(pts)
    nt = len(ml.TARGETS)
    return {"targets": {st: np.array(v)[:, :nt] for st, v in atlas.items()},
            "refs": {st: np.array(v)[:, nt:] for st, v in atlas.items()},
            "specimens": {k: np.array(v)[:, :nt] for k, v in spec.items()}, "files_present": files}


def mtc_space(a):
    pub15, pub18, atlas = load_inputs(Path(a.sel_v2), Path(a.landmarks_confirm), Path(a.atlas))
    p15, p18 = aa.subset_rows(pub15, aa.N_HOMOLOGOUS), aa.subset_rows(pub18, aa.N_HOMOLOGOUS)
    at = {s: aa.subset_rows(atlas[s], aa.N_HOMOLOGOUS) for s in aa.STAGES}
    s = aa.shape_space(p15, p18)
    a15, a18 = (aa.project_to_tangent(at[st], s["mean"]) for st in aa.STAGES)
    dec = aa.decompose(s["t15"], s["t18"], a15, a18)
    return at, s["mean"], dec["a"], dec["d"]


def run_gates_post(a, manifest: dict) -> dict:
    ann = load_annotations(manifest, manifest["references"])
    at, mean, avec, _ = mtc_space(a)
    g_eps = ml.gate_precision(at, ann["targets"], mean, avec)
    g_r = ml.gate_references(at, ann["refs"], manifest["references"])
    return {"gates": {"G0-ε": g_eps, "G0-r": g_r}, "files_present": ann["files_present"],
            "passed": bool(g_eps["passed"] and g_r["passed"])}


# ---------------------------------------------------------------- análisis
def run_analysis(a, manifest: dict) -> dict:
    ann = load_annotations(manifest, manifest["references"])
    at, mean, avec, d = mtc_space(a)
    main = ml.bootstrap_q(at, ann["targets"], mean, avec, d)
    rows = list(ml.TARGETS) + list(manifest["references"])
    both = {st: np.concatenate([ann["targets"][st], ann["refs"][st]], axis=1) for st in aa.STAGES}
    table = ml.discrepancy_table(at, both, rows)
    part_b = {}
    lmdir = Path(a.landmarks)
    for st in aa.STAGES:
        man = ml.repeat_stats(ann["targets"][st])["mean"]
        atlas_off = man - at[st][[i - 1 for i in ml.TARGETS]]
        ids = manifest["specimens"][st]
        sm = {i: ml.repeat_stats(ann["specimens"][i])["mean"] for i in ids}
        mus = {i: np.asarray(lm.read_tag(lmdir / f"{i}_Head_Landmarks.tag"), float) for i in ids}
        part_b[st] = ml.specimen_offsets(sm, mus, at[st], atlas_off)
    return {"analysis": "MT-D", **main, "discrepancy": table, "part_b": part_b,
            "verdict": {"MT-D1": main["verdict_mtd1"], "MT-D2": main.get("verdict_mtd2", "no evaluable")}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["prepare", "gates-pre", "gates-post", "analyze"])
    ap.add_argument("--mtc", default="results/morpho_trace/mtc/analisis.json", help="resultados de MT-C (referencias)")
    ap.add_argument("--atlas", default="data/external/musmorph/atlas")
    ap.add_argument("--images", default="data/external/musmorph/mta_images")
    ap.add_argument("--landmarks", default="data/external/musmorph/landmarks", help=".tag de los 40 especímenes")
    ap.add_argument("--landmarks-confirm", default="data/external/musmorph/landmarks_confirm")
    ap.add_argument("--sel-v2", default="results/morpho_trace/v2/seleccion_v2.json", help="confirmatorio de 597 (d)")
    a = ap.parse_args(argv)
    if a.cmd == "prepare":
        _write(run_prepare(a), OUT / "manifest.json")
        return 0
    manifest = _read(OUT / "manifest.json")
    if a.cmd == "gates-pre":
        res = run_gates_pre(a, manifest)
        _write(res, OUT / "gates_pre.json")
        return 0 if res["passed"] else 1
    if a.cmd == "gates-post":
        pre = OUT / "gates_pre.json"
        if not pre.exists() or not _read(pre).get("passed"):
            raise SystemExit("G0-e y G0-c no están superadas; el preregistro no permite seguir")
        res = run_gates_post(a, manifest)
        _write(res, OUT / "gates_post.json")
        return 0 if res["passed"] else 1
    for p in (OUT / "gates_pre.json", OUT / "gates_post.json"):
        if not p.exists() or not _read(p).get("passed"):
            raise SystemExit(f"las puertas no están superadas ({p}); el preregistro no permite seguir")
    _write(run_analysis(a, manifest), OUT / "analisis.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
