"""MT-A (docs/morpho_trace/PREREGISTRO_ATLAS.md §4): puertas previas, una por subcomando.

  python scripts/atlas_effect_gates.py g0d --ids results/onto_map/seleccion.json \\
      --data data/external/musmorph/landmarks_confirm --out results/morpho_trace/g0d.json

  python scripts/atlas_effect_gates.py download --out data/external/musmorph/atlas
  python scripts/atlas_effect_gates.py g0c --data data/external/musmorph/atlas --out results/morpho_trace/g0c.json
  python scripts/atlas_effect_gates.py download-images --ids results/onto_map/seleccion.json \\
      --out data/external/musmorph/mta_images --reuse data/external/musmorph/impc_e15_5 ...

``g0d``: reproduce la longitud de **d** con las 717 configuraciones publicadas del confirmatorio de ONTO-MAP
(GPA único, coordenadas tangentes, media E18.5 − media E15.5), con el mismo cargador que ONTO-MAP. Criterio:
longitud en [0,150, 0,164] (publicada: 0,157). No usa datos nuevos.

``download``: baja del catálogo público de FaceBase (registro 6-2EPY, CC BY 4.0) los dos atlas y sus landmarks.
Antes de bajar nada exige que el tamaño y el MD5 del catálogo sean los fijados en el preregistro (§3); después
comprueba el MD5 de cada archivo bajado.

``download-images``: las imágenes de los 20 + 20 especímenes del piloto de ONTO-MAP (registro 3-JZA6), con el MD5
del catálogo. Las que ya se bajaron para P3 se copian de ``--reuse`` si su MD5 coincide, en vez de bajarlas otra vez.

``g0c``: ¿el punto *i* es el mismo en los dos atlas? ``geovida.landmarks.correspondence_check`` con 200 órdenes
barajados; pasa si los dos atlas tienen 540 puntos y ρ con el orden dado es menor que el mínimo barajado.

``g0a`` / ``g0b``: fracción de landmarks publicados (3 especímenes) o de atlas (los 2) que caen sobre el umbral de
Otsu de su imagen, a resolución completa; pasa con ≥ 95 % en cada imagen.

``register``: cada espécimen del piloto registrado a los dos atlas (§3), un JSON por registro (reanudable).
``analyze``: puertas G2 y G1 y estimandos de §5; el veredicto es «no evaluable» si falla cualquier puerta.

Las imágenes se leen por losas (``geovida.minc.minc_slabs``) y solo se guarda en memoria el volumen ×4
(caché ``.npz`` en ``results/morpho_trace/cache``). Los resultados quedan fuera de git (``results/``), como los
datos.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from onto_map_pilot import _load  # noqa: E402

from geovida import atlas_effect as ae  # noqa: E402
from geovida import landmarks as lm  # noqa: E402
from geovida.provenance import git_state  # noqa: E402

G0D_RANGE = (0.150, 0.164)
PUBLISHED_D = 0.157

FACEBASE = "https://www.facebase.org"
ATLAS_RECORD = "6-2EPY"
IMAGES_RECORD = "3-JZA6"
ATLAS_FILES = {  # nombre: (bytes, md5), fijados en el preregistro §3 antes de descargar
    "IMPC_E15.5_Body_Atlas.mnc": (76534006, "05245d18ee87ed25faec29b84bfb7adb"),
    "IMPC_E18.5_Body_Atlas.mnc": (48490766, "7db10ed92076cfb325a9d9ef83c7c18a"),
    "IMPC_E15.5_Head_Atlas_Landmarks.tag": (37693, "f7bb7275fb9a41d85968d5ff3771cf63"),
    "IMPC_E18.5_Head_Atlas_Landmarks.tag": (37675, "fc7a3de827bd73c13dd053ee47be9733"),
}
ATLAS_TAGS = ("IMPC_E15.5_Head_Atlas_Landmarks.tag", "IMPC_E18.5_Head_Atlas_Landmarks.tag")
N_POINTS = 540


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def check_catalog(rows: list[dict], expected: dict = ATLAS_FILES) -> list[str]:
    """Problemas entre las filas del catálogo y lo preregistrado (lista vacía si todo coincide)."""
    got = {r["filename"]: r for r in rows}
    problems = []
    for name, (size, md5) in expected.items():
        r = got.get(name)
        if r is None:
            problems.append(f"{name}: no está en el catálogo")
        elif int(r["byte_count"]) != size or r["md5"] != md5:
            problems.append(f"{name}: catálogo {r['byte_count']} B / {r['md5']}, preregistro {size} B / {md5}")
    return problems


def _matches(path: Path, row: dict) -> bool:
    return path.exists() and path.stat().st_size == int(row["byte_count"]) and _md5(path) == row["md5"]


def fetch(names: list[str], record: str, out: Path, expected: dict | None = None, reuse=(),
          opener=urllib.request.urlopen, tries: int = 3, chunk: int = 20) -> list[dict]:
    """Baja ``names`` del registro ``record`` de FaceBase y comprueba el MD5 del catálogo; una fila por nombre.

    Con ``expected`` ({nombre: (bytes, md5)}) exige antes que el catálogo coincida y, si no, no baja nada.
    Un archivo que ya está en ``out`` o en una carpeta de ``reuse`` con el tamaño y MD5 del catálogo no se
    vuelve a bajar (el de ``reuse`` se copia)."""
    rows = []
    for k in range(0, len(names), chunk):
        filt = ";".join("filename=" + urllib.parse.quote(n, safe="") for n in names[k:k + chunk])
        query = f"{FACEBASE}/ermrest/catalog/1/attribute/isa:file/dataset={record}/{filt}/filename,url,byte_count,md5"
        with opener(query, timeout=60) as resp:
            rows += json.load(resp)
    if expected is not None:
        problems = check_catalog(rows, expected)
        if problems:
            raise RuntimeError("el catálogo no coincide con el preregistro; no se baja nada:\n  " + "\n  ".join(problems))
    out.mkdir(parents=True, exist_ok=True)
    log = []
    for r in rows:
        if r["filename"] not in names:
            continue
        dest = out / r["filename"]
        ok, source = _matches(dest, r), "local"
        for folder in ([] if ok else reuse):
            if _matches(Path(folder) / r["filename"], r):
                shutil.copyfile(Path(folder) / r["filename"], dest)
                ok, source = _matches(dest, r), "copia local"
                break
        if not ok:
            source = "FaceBase"
        for _ in range(0 if ok else tries):
            tmp = dest.with_name(dest.name + ".part")
            with opener(FACEBASE + r["url"], timeout=300) as resp, open(tmp, "wb") as fh:
                for block in iter(lambda: resp.read(1 << 20), b""):
                    fh.write(block)
            ok = _md5(tmp) == r["md5"]
            if ok:
                tmp.replace(dest)
                break
            tmp.unlink()
        log.append({"filename": r["filename"], "bytes": int(r["byte_count"]), "md5": r["md5"], "md5_ok": ok,
                    "source": source})
        print(f"  {r['filename']}: {'md5 correcto' if ok else 'FALLO'} ({source})", flush=True)
    found = {r["filename"] for r in rows}
    log += [{"filename": n, "bytes": 0, "md5": "", "md5_ok": False, "source": "no está en el catálogo"}
            for n in names if n not in found]
    return log


def fetch_atlas(out: Path, expected: dict = ATLAS_FILES, opener=urllib.request.urlopen) -> list[dict]:
    """Los dos atlas y sus landmarks, solo si el catálogo coincide con el preregistro."""
    return fetch(list(expected), ATLAS_RECORD, out, expected=expected, opener=opener)


def specimen_images(sel: dict) -> list[str]:
    """Imágenes de los 20 + 20 especímenes del piloto de ONTO-MAP (preregistro §2)."""
    return [f"{b}.mnc" for stage in ("E15.5", "E18.5") for b in sel["pilot"][stage]]


def g0c(a, b, n_perm: int = 200, seed: int = ae.SEED) -> dict:
    """Puerta G0-c: correspondencia punto a punto de los landmarks de los dos atlas."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    same = a.shape == b.shape == (N_POINTS, 3)
    r = lm.correspondence_check(a, b, n_perm=n_perm, seed=seed) if a.shape == b.shape else {"corresponds": False}
    return {"n_points": [len(a), len(b)], "expected_points": N_POINTS, "n_perm": n_perm, "seed": seed, **r,
            "passed": bool(same and r["corresponds"])}


ATLAS_IMAGES = {"E15.5": "IMPC_E15.5_Body_Atlas.mnc", "E18.5": "IMPC_E18.5_Body_Atlas.mnc"}
ATLAS_TAG = {"E15.5": ATLAS_TAGS[0], "E18.5": ATLAS_TAGS[1]}
G0_MIN_INSIDE = 0.95
FACTOR = 4


def g0a_specimens(sel: dict) -> list[str]:
    """Los 3 especímenes de G0-a (§4 no fija cuáles): los primeros del piloto alternando estadios."""
    p = sel["pilot"]
    return [p["E15.5"][0], p["E18.5"][0], p["E15.5"][1]]


def stage_of(name: str) -> str:
    return "E15.5" if "_E15.5_" in name else "E18.5"


def load_x4(path: Path, cache: Path, points=None) -> dict:
    """Volumen ×4 (con caché .npz) y, con ``points``, la fracción de puntos sobre Otsu a resolución completa."""
    from geovida import minc
    cached = cache / (path.stem + f"_x{FACTOR}.npz")
    if points is None and cached.exists():
        z = np.load(cached)
        return {"downsampled": z["downsampled"], "affine_ds": z["affine_ds"], "affine": z["affine"]}
    shape, affine, _ = minc.minc_header(path)
    r = ae.stream_volume(lambda: minc.minc_slabs(path, FACTOR), shape, affine, factor=FACTOR, points=points)
    cache.mkdir(parents=True, exist_ok=True)
    np.savez(cached, downsampled=r["downsampled"], affine_ds=r["affine_ds"], affine=affine)
    r["affine"] = affine
    return r


def g0_inside(items: list[tuple[str, Path, np.ndarray]], cache: Path) -> dict:
    """Puertas G0-a/b: para cada (nombre, imagen, landmarks) la fracción de landmarks sobre el umbral de Otsu."""
    rows = []
    for name, img, pts in items:
        r = load_x4(img, cache, points=pts)
        rows.append({"name": name, "n_points": int(len(pts)), "otsu": r["otsu"], "inside": r["inside"],
                     "passed": r["inside"] >= G0_MIN_INSIDE})
    return {"criterion": f"≥ {G0_MIN_INSIDE:.0%} de los puntos sobre Otsu", "items": rows,
            "passed": bool(rows) and all(r["passed"] for r in rows)}


def register_all(names: list[str], images: Path, atlas_dir: Path, cache: Path, out: Path, *,
                 mesh: int = 8, affine_only: bool = False, log=print) -> list[dict]:
    """Registra cada espécimen a los dos atlas (fija = atlas) y transfiere sus 540 landmarks. Reanudable: un
    JSON por registro en ``out``; los que ya existen no se repiten."""
    import time
    out.mkdir(parents=True, exist_ok=True)
    atlas = {st: load_x4(atlas_dir / f, cache) for st, f in ATLAS_IMAGES.items()}
    tags = {st: lm.read_tag(atlas_dir / f) for st, f in ATLAS_TAG.items()}
    rows = []
    for name in names:
        spec = None
        for st in ("E15.5", "E18.5"):
            dest = out / f"{name}__atlas_{st}.json"
            if dest.exists():
                rows.append(json.loads(dest.read_text(encoding="utf-8")))
                continue
            if spec is None:
                spec = load_x4(images / f"{name}.mnc", cache)
            t0 = time.time()
            row = {"specimen": name, "stage": stage_of(name), "atlas": st, "own": st == stage_of(name),
                   "mesh": None if affine_only else mesh, "factor": FACTOR}
            try:
                fixed = ae.to_sitk(atlas[st]["downsampled"], atlas[st]["affine_ds"])
                moving = ae.to_sitk(spec["downsampled"], spec["affine_ds"])
                tx, info = ae.register(fixed, moving, mesh=mesh, affine_only=affine_only)
                pts = ae.transfer_points(tx, tags[st])
                metrics = [v for k, v in info.items() if k.endswith("_metric")]
                row.update({"info": info, "points": pts.tolist(),
                            "ok": bool(np.all(np.isfinite(pts)) and all(np.isfinite(metrics)))})
            except Exception as exc:  # G2 cuenta los registros que fallan; no se detiene la serie
                row.update({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
            row["seconds"] = round(time.time() - t0, 1)
            dest.write_text(json.dumps(row, default=float) + "\n", encoding="utf-8")
            log(f"  {name} → atlas {st}: {'ok' if row['ok'] else 'FALLO'} ({row['seconds']} s)")
            rows.append(row)
    return rows


def analyze(rows: list[dict], sel: dict, pub_pilot: dict, pub_confirm: dict, gates: dict,
            n_boot: int = ae.N_BOOT) -> dict:
    """G2, G1 y estimandos de §5. Un espécimen es válido si sus dos registros terminaron bien (δ necesita ambos)."""
    by = {}
    for r in rows:
        by.setdefault(r["specimen"], {})[r["atlas"]] = r
    valid = {st: [b for b in sel["pilot"][st] if all(by.get(b, {}).get(a, {}).get("ok") for a in ("E15.5", "E18.5"))]
             for st in ("E15.5", "E18.5")}
    g2 = {"valid": {st: len(v) for st, v in valid.items()}, "required": 16,
          "passed": all(len(v) >= 16 for v in valid.values())}
    res = {"gates": {**gates, "G2": g2}}
    names = valid["E15.5"] + valid["E18.5"]
    if len(names) < 2:
        res["verdict"] = "no evaluable"
        return res
    own = np.array([by[b][stage_of(b)]["points"] for b in names])
    published = np.array([pub_pilot[b] for b in names])
    res["gates"]["G1"] = ae.gate_g1(own, published, {st: [pub_pilot[b] for b in sel["pilot"][st]]
                                                     for st in ("E15.5", "E18.5")})
    l15 = np.array([by[b]["E15.5"]["points"] for b in names])
    l18 = np.array([by[b]["E18.5"]["points"] for b in names])
    res["mta"] = ae.atlas_effect(pub_confirm["E15.5"], pub_confirm["E18.5"], l15, l18,
                                 [stage_of(b) for b in names], n_boot=n_boot)
    failed = [k for k, g in res["gates"].items() if not g.get("passed")]
    res["failed_gates"] = failed
    res["verdict"] = "no evaluable" if failed else res["mta"]["mta1"]["verdict"]
    return res


def g0d(configs: dict) -> dict:
    """Puerta G0-d a partir de {'E15.5': (n, k, 3), 'E18.5': (n, k, 3)}."""
    r = ae.published_direction(configs["E15.5"], configs["E18.5"])
    lo, hi = G0D_RANGE
    r.update({"published": PUBLISHED_D, "range": list(G0D_RANGE), "passed": lo <= r["d_length"] <= hi})
    return r


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("g0d")
    p.add_argument("--ids", required=True)
    p.add_argument("--data", required=True)
    p.add_argument("--out", required=True)
    dl = sub.add_parser("download")
    dl.add_argument("--out", required=True, help="carpeta de destino (fuera de git: data/external/...)")
    di = sub.add_parser("download-images")
    di.add_argument("--ids", required=True, help="results/onto_map/seleccion.json")
    di.add_argument("--out", required=True, help="carpeta de destino (fuera de git: data/external/...)")
    di.add_argument("--reuse", nargs="*", default=[], help="carpetas con imágenes ya bajadas (se copian si el MD5 coincide)")
    c = sub.add_parser("g0c")
    c.add_argument("--data", required=True)
    c.add_argument("--out", required=True)
    for name in ("g0a", "g0b", "register", "analyze"):
        q = sub.add_parser(name)
        q.add_argument("--ids", required=True, help="results/onto_map/seleccion.json")
        q.add_argument("--atlas", default="data/external/musmorph/atlas")
        q.add_argument("--images", default="data/external/musmorph/mta_images")
        q.add_argument("--landmarks", default="data/external/musmorph/landmarks")
        q.add_argument("--cache", default="results/morpho_trace/cache")
        q.add_argument("--regs", default="results/morpho_trace/registros")
        q.add_argument("--out", required=name != "register")
        if name == "register":
            q.add_argument("--mesh", type=int, default=8)
            q.add_argument("--affine-only", action="store_true")
        if name == "analyze":
            q.add_argument("--confirm-landmarks", default="data/external/musmorph/landmarks_confirm")
            q.add_argument("--gates-dir", default="results/morpho_trace")
            q.add_argument("--n-boot", type=int, default=ae.N_BOOT)
    a = ap.parse_args(argv)
    if a.cmd in ("g0a", "g0b", "register", "analyze"):
        sel = json.loads(Path(a.ids).read_text(encoding="utf-8"))
        atlas_dir, images, cache = Path(a.atlas), Path(a.images), Path(a.cache)
        if a.cmd == "register":
            names = sel["pilot"]["E15.5"] + sel["pilot"]["E18.5"]
            rows = register_all(names, images, atlas_dir, cache, Path(a.regs), mesh=a.mesh, affine_only=a.affine_only)
            return 0 if len(rows) == 2 * len(names) else 1
        if a.cmd == "g0a":
            items = [(b, images / f"{b}.mnc", lm.read_tag(Path(a.landmarks) / f"{b}_Head_Landmarks.tag"))
                     for b in g0a_specimens(sel)]
            res = {"gate": "G0-a", **g0_inside(items, cache)}
        elif a.cmd == "g0b":
            items = [(f"atlas {st}", atlas_dir / ATLAS_IMAGES[st], lm.read_tag(atlas_dir / ATLAS_TAG[st]))
                     for st in ("E15.5", "E18.5")]
            res = {"gate": "G0-b", **g0_inside(items, cache)}
        else:
            gates = {}
            for g in ("g0a", "g0b", "g0c", "g0d"):
                p = Path(a.gates_dir) / f"{g}.json"
                gates[f"G0-{g[-1]}"] = (json.loads(p.read_text(encoding="utf-8")) if p.exists()
                                                         else {"passed": False, "missing": True})
            rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(a.regs).glob("*.json"))]
            names = sel["pilot"]["E15.5"] + sel["pilot"]["E18.5"]
            pub = {b: lm.read_tag(Path(a.landmarks) / f"{b}_Head_Landmarks.tag") for b in names}
            res = {"analysis": "MT-A", **analyze(rows, sel, pub, _load(sel, "confirm", Path(a.confirm_landmarks)),
                                                 {k: {"passed": v.get("passed", False)} for k, v in gates.items()},
                                                 n_boot=a.n_boot)}
            res["provenance"] = git_state()
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            Path(a.out).write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")
            print(json.dumps({k: res[k] for k in ("verdict", "gates")}, default=float))
            return 0
        res["provenance"] = git_state()
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in res.items() if k != "provenance"}, default=float))
        return 0 if res["passed"] else 1
    if a.cmd == "download":
        log = fetch_atlas(Path(a.out))
        return 0 if len(log) == len(ATLAS_FILES) and all(r["md5_ok"] for r in log) else 1
    if a.cmd == "download-images":
        names = specimen_images(json.loads(Path(a.ids).read_text(encoding="utf-8")))
        log = fetch(names, IMAGES_RECORD, Path(a.out), reuse=a.reuse)
        bad = [r["filename"] for r in log if not r["md5_ok"]]
        print(f"{len(log) - len(bad)} de {len(names)} con MD5 correcto; "
              f"bajadas {sum(r['source'] == 'FaceBase' and r['md5_ok'] for r in log)}" + (f"; fallan {bad}" if bad else ""))
        return 0 if not bad and len(log) == len(names) else 1
    if a.cmd == "g0c":
        pts = [lm.read_tag(Path(a.data) / n) for n in ATLAS_TAGS]
        res = {"gate": "G0-c", **g0c(*pts), "provenance": git_state()}
    else:
        sel = json.loads(Path(a.ids).read_text(encoding="utf-8"))
        res = {"gate": "G0-d", **g0d(_load(sel, "confirm", Path(a.data))), "provenance": git_state()}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "provenance"}, default=float))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
