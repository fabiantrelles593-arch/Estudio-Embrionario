"""Piloto de P3 (docs/PREREGISTRO_P3.md): elegir, descargar y pasar las comprobaciones previas.

  python scripts/p3_pilot.py select --metadata MusMorph_Metadata_Mar2024.csv --out results/p3/seleccion.json
  python scripts/p3_pilot.py download --ids results/p3/seleccion.json --out data/external/musmorph/impc_e15_5
  python scripts/p3_pilot.py check --ids results/p3/seleccion.json --data data/external/musmorph/impc_e15_5 \\
      --out results/p3/precheck_piloto.json

``select`` aplica el muestreo fijado (semilla 20261114) y lista los archivos que hay que descargar de FaceBase
(registro 3-JZA6). ``download`` los baja del catálogo público de FaceBase (sin autenticación) y comprueba el
MD5 de cada uno. ``check`` lee solo las segmentaciones descargadas, recupera las etiquetas (desviación D1) y
aplica las comprobaciones 3.1 y 3.2; devuelve 0 si ambas pasan y 1 si alguna falla (el estudio se detiene).
Ninguno de los tres mira resultados. Los volúmenes nunca se guardan en el repositorio (``data/external/`` está
en ``.gitignore``).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from geovida import p3, p3_data

FACEBASE = "https://www.facebase.org"
DATASET = "3-JZA6"


def _write_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=float), encoding="utf-8")


def catalog_urls(names: list[str], chunk: int = 40) -> list[str]:
    """Consultas ERMrest (nombre, url, bytes, md5) de los archivos pedidos, en lotes de ``chunk`` nombres."""
    out = []
    for k in range(0, len(names), chunk):
        filt = ";".join("filename=" + urllib.parse.quote(n, safe="") for n in names[k:k + chunk])
        out.append(f"{FACEBASE}/ermrest/catalog/1/attribute/isa:file/dataset={DATASET}/{filt}"
                   "/filename,url,byte_count,md5")
    return out


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download(names: list[str], out: Path, tries: int = 3) -> list[dict]:
    """Baja cada archivo (si no está ya con el MD5 correcto) y devuelve una fila por archivo."""
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for url in catalog_urls(names):
        with urllib.request.urlopen(url, timeout=60) as resp:
            rows += json.load(resp)
    log = []
    for r in rows:
        dest = out / r["filename"]
        ok = dest.exists() and dest.stat().st_size == int(r["byte_count"]) and _md5(dest) == r["md5"]
        for _ in range(tries if not ok else 0):
            tmp = dest.with_suffix(dest.suffix + ".part")
            with urllib.request.urlopen(FACEBASE + r["url"], timeout=120) as resp, open(tmp, "wb") as fh:
                for block in iter(lambda: resp.read(1 << 20), b""):
                    fh.write(block)
            ok = _md5(tmp) == r["md5"]
            if ok:
                tmp.replace(dest)
                break
            tmp.unlink()
        log.append({"filename": r["filename"], "bytes": int(r["byte_count"]), "md5": r["md5"], "md5_ok": ok})
        print(f"  {r['filename']}: {'md5 correcto' if ok else 'FALLO'}", flush=True)
    found = {r["filename"] for r in rows}
    log += [{"filename": n, "bytes": 0, "md5": "", "md5_ok": False} for n in names if n not in found]
    with open(out / "_descarga_md5.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["filename", "bytes", "md5", "md5_ok"])
        w.writeheader()
        w.writerows(log)
    return log


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select", help="elegir piloto y confirmatorio y listar los archivos a descargar")
    s.add_argument("--metadata", required=True, help="CSV de metadatos de MusMorph")
    s.add_argument("--out", required=True)
    s.add_argument("--n-confirm", type=int, default=60, help="60, o 120 si lo exige la regla de ampliación")
    d = sub.add_parser("download", help="bajar de FaceBase los archivos elegidos y comprobar su MD5")
    d.add_argument("--ids", required=True, help="JSON producido por select")
    d.add_argument("--which", choices=("pilot", "confirm"), default="pilot")
    d.add_argument("--out", required=True, help="carpeta de destino (fuera de git: data/external/...)")
    c = sub.add_parser("check", help="comprobaciones previas 3.1 y 3.2 sobre la descarga")
    c.add_argument("--ids", required=True, help="JSON producido por select")
    c.add_argument("--data", required=True, help="carpeta con los .mnc descargados")
    c.add_argument("--which", choices=("pilot", "confirm"), default="pilot")
    c.add_argument("--rule", choices=p3_data.RULES, default="nearest",
                   help="recuperación de etiquetas interpoladas (desviación D1): nearest (principal) o exact")
    c.add_argument("--any-label", action="store_true",
                   help="aceptar cualquier entero > 0 como etiqueta (por defecto, las 50 de MusMorph)")
    c.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    if args.cmd == "select":
        sel = p3.select_specimens(pd.read_csv(args.metadata), n_confirm=args.n_confirm)
        sel["pilot_files"] = p3_data.required_files(sel["pilot"])
        sel["confirm_files"] = p3_data.required_files(sel["confirm"])
        _write_json(sel, Path(args.out))
        print(f"{sel['n_eligible']} elegibles; piloto {len(sel['pilot'])}, confirmatorio {len(sel['confirm'])}")
        print("Archivos del piloto a descargar de FaceBase (3-JZA6):")
        for f in sel["pilot_files"]:
            print("  " + f)
        return 0

    sel = json.loads(Path(args.ids).read_text(encoding="utf-8"))
    if args.cmd == "download":
        log = download(sel[f"{args.which}_files"], Path(args.out))
        n_ok = sum(r["md5_ok"] for r in log)
        print(f"{n_ok} de {len(log)} archivos con MD5 correcto")
        return 0 if n_ok == len(log) else 1

    res = p3_data.precheck(args.data, sel[args.which], rule=args.rule,
                           allowed=None if args.any_label else p3_data.MUSMORPH_LABELS)
    vol = res.pop("volumes")
    out = Path(args.out)
    _write_json(res, out)
    vol.to_csv(out.with_suffix(".volumes.csv"), index=False)
    print(f"3.1 existencia: {res['n_complete']}/{res['n_requested']} -> "
          f"{'pasa' if res['check_3_1_passed'] else 'NO PASA'}")
    lv = res["label_variation"]
    print(f"3.2 espacio del espécimen: {lv['fraction_varying']:.0%} de {lv['n_structures']} etiquetas varían -> "
          f"{'pasa' if res['check_3_2_passed'] else 'NO PASA'}")
    print(f"vóxeles: {res['spacings_mm']}; etiquetas: {len(res['labels_present'])}")
    if res["frac_mixed_median"] is not None:
        print(f"vóxeles con valor interpolado (mediana): {res['frac_mixed_median']:.1%}; regla {res['label_recovery_rule']}")
    return 0 if res["check_3_1_passed"] and res["check_3_2_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
