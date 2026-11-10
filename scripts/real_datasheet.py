"""Ficha de un conjunto de volúmenes NIfTI (carpeta, .zip o un archivo), sin comparar con nada.

Uso:  python scripts/real_datasheet.py RUTA [--out results/summary/real_datasheet.json]

Solo lee cabeceras y resúmenes: forma, tamaño del vóxel, intensidades, etiquetas. No calcula
ningún acuerdo con una referencia (eso va después, con criterios ya fijados en git). El resultado
es un JSON pequeño: no contiene imágenes.
"""
import argparse
import json
from pathlib import Path

from geovida import realdata


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--out", default="results/summary/real_datasheet.json")
    a = ap.parse_args()
    rows = realdata.scan(a.source)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(rows, indent=1, default=float), encoding="utf-8")
    for r in rows:
        if "error" in r:
            print(f"{r['path']}: ERROR {r['error']}")
            continue
        kind = "etiquetas " + ",".join(r["labels"]) if r["label_like"] else \
            f"intensidad p1={r['p1']:.3g} p50={r['p50']:.3g} p99={r['p99']:.3g}"
        print(f"{r['path']}: forma {tuple(r['shape'])}, vóxel {tuple(round(s, 4) for s in r['spacing_mm'])} mm, {kind}")
    print(f"\n{len(rows)} archivos; ficha guardada en {a.out}")


if __name__ == "__main__":
    main()
