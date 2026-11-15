"""Piloto de P3 (docs/PREREGISTRO_P3.md): elegir los especímenes y pasar las comprobaciones previas.

  python scripts/p3_pilot.py select --metadata MusMorph_Metadata_Mar2024.csv --out results/p3/seleccion.json
  python scripts/p3_pilot.py check --ids results/p3/seleccion.json --data data/external/musmorph \\
      --out results/p3/precheck_piloto.json

``select`` aplica el muestreo fijado (semilla 20261114) y lista los archivos que hay que descargar de FaceBase
(registro 3-JZA6). ``check`` lee solo las segmentaciones descargadas y aplica las comprobaciones 3.1 y 3.2;
devuelve 0 si ambas pasan y 1 si alguna falla (el estudio se detiene). Ninguna de las dos mira resultados.
Los volúmenes nunca se guardan en el repositorio (``data/external/`` está en ``.gitignore``).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from geovida import p3, p3_data


def _write_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=float), encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select", help="elegir piloto y confirmatorio y listar los archivos a descargar")
    s.add_argument("--metadata", required=True, help="CSV de metadatos de MusMorph")
    s.add_argument("--out", required=True)
    s.add_argument("--n-confirm", type=int, default=60, help="60, o 120 si lo exige la regla de ampliación")
    c = sub.add_parser("check", help="comprobaciones previas 3.1 y 3.2 sobre la descarga")
    c.add_argument("--ids", required=True, help="JSON producido por select")
    c.add_argument("--data", required=True, help="carpeta con los .mnc descargados")
    c.add_argument("--which", choices=("pilot", "confirm"), default="pilot")
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
    res = p3_data.precheck(args.data, sel[args.which])
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
    return 0 if res["check_3_1_passed"] and res["check_3_2_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
