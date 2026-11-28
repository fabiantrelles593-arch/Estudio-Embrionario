"""Manifiesto de datos externos (ADR-005).

Los datos de terceros (p. ej. MusMorph en FaceBase) no se versionan: las condiciones de FaceBase
piden no redistribuir los archivos originales. En el repositorio solo queda este manifiesto, que
permite comprobar más tarde que se analizan exactamente los mismos archivos.

Cada fila guarda la ruta relativa (con «/»), el tamaño en bytes, el SHA-256, la fuente, el registro
(p. ej. el RID de FaceBase), la licencia y la fecha de descarga (AAAA-MM-DD). No se admite una
licencia vacía: un archivo sin licencia conocida no entra en el análisis. Nunca se guardan rutas
absolutas, que podrían revelar el nombre de usuario o la estructura del equipo.

Uso
---
  python -m geovida.manifest build CARPETA --source FaceBase --record 3-JZA6 \\
      --license "CC BY 4.0" --downloaded 2026-11-20 --out data/manifests/musmorph_e155.csv
  python -m geovida.manifest verify data/manifests/musmorph_e155.csv CARPETA
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import sys
from pathlib import Path, PurePosixPath

FIELDS = ("file", "bytes", "sha256", "source", "record", "license", "downloaded")
DEFAULT_SUFFIXES = (".mnc", ".mnc.gz", ".nii", ".nii.gz", ".tag", ".csv", ".xfm")


def sha256_file(path, chunk: int = 1 << 20) -> str:
    """SHA-256 de un archivo, leído por bloques."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _files(root: Path, suffixes) -> list[Path]:
    suf = tuple(s.lower() for s in suffixes)
    return sorted(p for p in root.rglob("*") if p.is_file() and p.name.lower().endswith(suf))


def build_manifest(root, *, source: str, record: str, license: str, downloaded: str,
                   suffixes=DEFAULT_SUFFIXES) -> list[dict]:
    """Una fila por archivo de datos bajo ``root``, con ruta relativa y SHA-256."""
    if not license or not license.strip():
        raise ValueError("falta la licencia: no se registran datos con licencia desconocida")
    dt.date.fromisoformat(downloaded)  # ValueError si la fecha no es AAAA-MM-DD
    root = Path(root)
    if not root.is_dir():
        raise ValueError(f"{root}: no es una carpeta")
    rows = [{"file": p.relative_to(root).as_posix(), "bytes": p.stat().st_size,
             "sha256": sha256_file(p), "source": source, "record": record,
             "license": license.strip(), "downloaded": downloaded}
            for p in _files(root, suffixes)]
    if not rows:
        raise ValueError(f"{root}: no hay archivos con las extensiones {list(suffixes)}")
    return rows


def write_manifest(rows, path) -> Path:
    """Guarda el manifiesto como CSV (UTF-8, fin de línea \\n)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return path


def read_manifest(path) -> list[dict]:
    """Lee y valida un manifiesto: cabecera exacta y rutas relativas sin «..»."""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError(f"{path}: cabecera {reader.fieldnames}, se esperaba {list(FIELDS)}")
        rows = list(reader)
    for row in rows:
        rel = PurePosixPath(row["file"])
        if rel.is_absolute() or ".." in rel.parts or "\\" in row["file"]:
            raise ValueError(f"{path}: ruta no permitida {row['file']!r}")
        row["bytes"] = int(row["bytes"])
    return rows


def verify_manifest(manifest, root, suffixes=DEFAULT_SUFFIXES) -> list[dict]:
    """Estado de cada archivo: ``ok``, ``missing`` (no está), ``changed`` (tamaño o SHA-256
    distintos) o ``extra`` (está en la carpeta pero no en el manifiesto)."""
    root = Path(root)
    rows = read_manifest(manifest)
    out = []
    for row in rows:
        p = root / row["file"]
        if not p.is_file():
            status = "missing"
        elif p.stat().st_size != row["bytes"] or sha256_file(p) != row["sha256"]:
            status = "changed"
        else:
            status = "ok"
        out.append({"file": row["file"], "status": status})
    listed = {row["file"] for row in rows}
    for p in _files(root, suffixes):
        rel = p.relative_to(root).as_posix()
        if rel not in listed:
            out.append({"file": rel, "status": "extra"})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m geovida.manifest", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="crear el manifiesto de una carpeta de datos externos")
    b.add_argument("root")
    b.add_argument("--source", required=True, help="p. ej. FaceBase")
    b.add_argument("--record", required=True, help="identificador del registro, p. ej. el RID de FaceBase")
    b.add_argument("--license", required=True, help="licencia comprobada en la fuente")
    b.add_argument("--downloaded", required=True, help="fecha de descarga, AAAA-MM-DD")
    b.add_argument("--out", required=True)
    v = sub.add_parser("verify", help="comprobar una carpeta contra un manifiesto")
    v.add_argument("manifest")
    v.add_argument("root")
    args = ap.parse_args(argv)
    if args.cmd == "build":
        rows = build_manifest(args.root, source=args.source, record=args.record,
                              license=args.license, downloaded=args.downloaded)
        write_manifest(rows, args.out)
        print(f"{len(rows)} archivos en {args.out}")
        return 0
    res = verify_manifest(args.manifest, args.root)
    bad = [r for r in res if r["status"] != "ok"]
    for r in bad:
        print(f"{r['status']}: {r['file']}")
    print(f"{len(res) - len(bad)} correctos, {len(bad)} con diferencias")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
