"""MT-A (docs/morpho_trace/PREREGISTRO_ATLAS.md §4): puertas previas, una por subcomando.

  python scripts/atlas_effect_gates.py g0d --ids results/onto_map/seleccion.json \\
      --data data/external/musmorph/landmarks_confirm --out results/morpho_trace/g0d.json

  python scripts/atlas_effect_gates.py download --out data/external/musmorph/atlas
  python scripts/atlas_effect_gates.py g0c --data data/external/musmorph/atlas --out results/morpho_trace/g0c.json

``g0d``: reproduce la longitud de **d** con las 717 configuraciones publicadas del confirmatorio de ONTO-MAP
(GPA único, coordenadas tangentes, media E18.5 − media E15.5), con el mismo cargador que ONTO-MAP. Criterio:
longitud en [0,150, 0,164] (publicada: 0,157). No usa datos nuevos.

``download``: baja del catálogo público de FaceBase (registro 6-2EPY, CC BY 4.0) los dos atlas y sus landmarks.
Antes de bajar nada exige que el tamaño y el MD5 del catálogo sean los fijados en el preregistro (§3); después
comprueba el MD5 de cada archivo bajado.

``g0c``: ¿el punto *i* es el mismo en los dos atlas? ``geovida.landmarks.correspondence_check`` con 200 órdenes
barajados; pasa si los dos atlas tienen 540 puntos y ρ con el orden dado es menor que el mínimo barajado.

Las demás puertas (G0-a, G0-b, G1, G2) se añaden cuando la memoria permita leer las imágenes. Los resultados
quedan fuera de git (``results/``), como los datos.
"""
from __future__ import annotations

import argparse
import hashlib
import json
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


def fetch_atlas(out: Path, expected: dict = ATLAS_FILES, opener=urllib.request.urlopen, tries: int = 3) -> list[dict]:
    """Baja los archivos preregistrados si el catálogo coincide con el preregistro; una fila por archivo."""
    filt = ";".join("filename=" + urllib.parse.quote(n, safe="") for n in expected)
    query = f"{FACEBASE}/ermrest/catalog/1/attribute/isa:file/dataset={ATLAS_RECORD}/{filt}/filename,url,byte_count,md5"
    with opener(query, timeout=60) as resp:
        rows = json.load(resp)
    problems = check_catalog(rows, expected)
    if problems:
        raise RuntimeError("el catálogo no coincide con el preregistro; no se baja nada:\n  " + "\n  ".join(problems))
    out.mkdir(parents=True, exist_ok=True)
    log = []
    for r in rows:
        if r["filename"] not in expected:
            continue
        dest = out / r["filename"]
        ok = dest.exists() and dest.stat().st_size == int(r["byte_count"]) and _md5(dest) == r["md5"]
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
        log.append({"filename": r["filename"], "bytes": int(r["byte_count"]), "md5": r["md5"], "md5_ok": ok})
        print(f"  {r['filename']}: {'md5 correcto' if ok else 'FALLO'}", flush=True)
    return log


def g0c(a, b, n_perm: int = 200, seed: int = ae.SEED) -> dict:
    """Puerta G0-c: correspondencia punto a punto de los landmarks de los dos atlas."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    same = a.shape == b.shape == (N_POINTS, 3)
    r = lm.correspondence_check(a, b, n_perm=n_perm, seed=seed) if a.shape == b.shape else {"corresponds": False}
    return {"n_points": [len(a), len(b)], "expected_points": N_POINTS, "n_perm": n_perm, "seed": seed, **r,
            "passed": bool(same and r["corresponds"])}


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
    c = sub.add_parser("g0c")
    c.add_argument("--data", required=True)
    c.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "download":
        log = fetch_atlas(Path(a.out))
        return 0 if len(log) == len(ATLAS_FILES) and all(r["md5_ok"] for r in log) else 1
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
