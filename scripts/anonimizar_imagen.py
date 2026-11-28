"""Anonimiza una imagen en local antes de cualquier análisis (docs/DATOS_REALES_Y_ETICA.md §3).

    python scripts/anonimizar_imagen.py preview  ORIGEN --boxes cajas.json --code CI-001-IMG01
    python scripts/anonimizar_imagen.py apply    ORIGEN --boxes cajas.json --code CI-001-IMG01

``cajas.json`` es una lista de cajas [x0, y0, x1, y1] en píxeles, o en fracciones (0–1) del ancho y el alto. ``preview``
escribe ``data/private/ecografia/revision/<code>_revision.png`` con las cajas en rojo, para que una persona compruebe que
tapan todo el texto que identifica (nombre, documento, fechas, médica, centro). ``apply`` escribe la copia limpia
``data/private/ecografia/anon/<code>.png`` y su registro, que no lleva el nombre del archivo original.

Úsese solo cuando existan el consentimiento firmado de la gestante y el aval ético. El script no detecta texto, no sube
nada y solo escribe en ``data/private/`` (ignorado por git).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from geovida import deidentify as di

BASE = di.PRIVATE_DIR / "ecografia"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["preview", "apply"])
    ap.add_argument("source", help="imagen original (no se copia ni se modifica)")
    ap.add_argument("--boxes", required=True, help="JSON con la lista de cajas [x0, y0, x1, y1]")
    ap.add_argument("--code", required=True, help="código interno, sin datos personales (p. ej., CI-001-IMG01)")
    a = ap.parse_args(argv)
    boxes = json.loads(Path(a.boxes).read_text(encoding="utf-8"))
    if a.cmd == "preview":
        out = BASE / "revision" / f"{a.code}_revision.png"
        di.preview(di.load_pixels(a.source), boxes, out)
        print(f"Revisa a mano {out}: las cajas rojas deben cubrir todo el texto que identifica.")
        return 0
    rec = di.anonymize(a.source, boxes, BASE / "anon", a.code)
    print(json.dumps({k: rec[k] for k in ("code", "shape", "sha256_output", "check")}, ensure_ascii=False))
    print("Revisa la copia limpia antes de usarla y anota la revisión en el registro (human_review).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
