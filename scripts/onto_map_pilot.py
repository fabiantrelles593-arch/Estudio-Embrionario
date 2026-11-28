"""ONTO-MAP, piloto P4 (docs/onto_map/PROTOCOLO_ONTOMAP.md): elegir, descargar, comprobar y analizar.

  python scripts/onto_map_pilot.py select --metadata MusMorph_Metadata_Mar2024.csv --out results/onto_map/seleccion.json
  python scripts/onto_map_pilot.py download --ids results/onto_map/seleccion.json --which pilot \\
      --out data/external/musmorph/landmarks
  python scripts/onto_map_pilot.py check --ids results/onto_map/seleccion.json --which pilot \\
      --data data/external/musmorph/landmarks --out results/onto_map/precheck_piloto.json
  python scripts/onto_map_pilot.py analyze --ids ... --which confirm --data ... --out results/onto_map/analisis.json

``select`` consulta en el catálogo público de FaceBase (registro 3-JZA6) qué especímenes tienen
landmarks y aplica el muestreo fijado (semilla 20261116). ``download`` reutiliza la descarga con MD5
de ``scripts/p3_pilot.py``. ``check`` aplica las cuatro comprobaciones previas; ``analyze``, el
análisis de §5. Los archivos nunca se guardan en el repositorio (``data/external/``).
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p3_pilot import DATASET, FACEBASE, _write_json, download  # noqa: E402

from geovida import landmarks as lm  # noqa: E402
from geovida import onto_map as om  # noqa: E402


def catalog_landmarks(stage: str) -> list[str]:
    """Nombres de archivo ``IMPC_<estadio>_<n>_Head_Landmarks.tag`` del catálogo de FaceBase."""
    pat = urllib.parse.quote(f"IMPC_{stage}_[0-9]+_Head_Landmarks[.]tag$", safe="")
    url = f"{FACEBASE}/ermrest/catalog/1/attribute/isa:file/dataset={DATASET}/filename::regexp::{pat}/filename"
    with urllib.request.urlopen(url, timeout=120) as resp:
        return sorted(r["filename"] for r in json.load(resp))


def _load(sel: dict, which: str, data: Path) -> dict:
    return {st: np.stack([lm.read_tag(data / om.landmark_name(b)) for b in sel[which][st]])
            for st in om.STAGES}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select")
    s.add_argument("--metadata", required=True)
    s.add_argument("--out", required=True)
    for name in ("download", "check", "analyze"):
        p = sub.add_parser(name)
        p.add_argument("--ids", required=True)
        p.add_argument("--which", choices=("pilot", "confirm"), default="pilot")
        p.add_argument("--out", required=True)
        if name != "download":
            p.add_argument("--data", required=True)
        if name == "analyze":
            p.add_argument("--n-boot", type=int, default=2000)
    a = ap.parse_args(argv)

    if a.cmd == "select":
        avail = [f for st in om.STAGES for f in catalog_landmarks(st)]
        sel = om.select(pd.read_csv(a.metadata), avail)
        sel["n_catalog_landmarks"] = len(avail)
        _write_json(sel, Path(a.out))
        print(f"elegibles {sel['n_eligible']}; piloto {[len(v) for v in sel['pilot'].values()]}; "
              f"confirmatorio {[len(v) for v in sel['confirm'].values()]}")
        return 0
    sel = json.loads(Path(a.ids).read_text(encoding="utf-8"))
    if a.cmd == "download":
        names = [om.landmark_name(b) for st in om.STAGES for b in sel[a.which][st]]
        log = download(names, Path(a.out))
        n_ok = sum(r["md5_ok"] for r in log)
        print(f"{n_ok} de {len(log)} archivos con MD5 correcto")
        return 0 if n_ok == len(log) else 1
    cfg = _load(sel, a.which, Path(a.data))
    res = om.prechecks(cfg) if a.cmd == "check" else om.analyze(cfg, n_boot=a.n_boot)
    _write_json(res, Path(a.out))
    print(json.dumps(res, indent=1, ensure_ascii=False, default=float))
    return 0 if a.cmd == "analyze" or res["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
