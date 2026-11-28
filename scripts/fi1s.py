"""FI-1s (docs/prenatal/PREREGISTRO_FOTO_IMPRESION_SINTETICA.md): plan, puertas y análisis.

    python scripts/fi1s.py plan       # orden aleatorio de las 3 sesiones de marcado (18 fotos; semilla 20261125)
    python scripts/fi1s.py gates      # G0-impresión (regla.json), G0-escala y G0-homografía por foto
    python scripts/fi1s.py analyze    # FI-1sa, FI-1sb y FI-1sc con las fotos que pasan

Entradas en ``data/fi1s/`` (fuera de git):

* ``regla.json``: {"S01": [ancho_mm, alto_mm], ...}, el recuadro medido con regla antes de fotografiar.
* ``marcas/<hoja>-<foto>_r<k>.json``: lo que guarda ``tools/marcador.html`` (formato de
  ``geovida.print_measure.measure_photo``, más ``print`` y ``photo``).
* ``valores_disenados.json``: de ``scripts/fi1s_hojas.py``. Solo lo lee ``analyze``.

Resultados en ``results/prenatal/fi1s/``. Sin datos de personas ni ningún resultado clínico.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from geovida import fi1s
from geovida import print_measure as pm
from geovida.provenance import git_state

BASE = Path("data/fi1s")
OUT = Path("results/prenatal/fi1s")


def _read(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _write(res: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    res["provenance"] = git_state()
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k not in ("provenance", "fi1sc", "fotos")},
                     ensure_ascii=False, default=float)[:3000])


def photos() -> list[str]:
    return [f"S{s + 1:02d}-{f}" for s in range(fi1s.N_SHEETS) for f in fi1s.N_PHOTOS]


def load_marks(base: Path = BASE) -> list[dict]:
    rows = []
    for f in sorted((base / "marcas").glob("*_r*.json")):
        ann = _read(f)
        rows.append({"file": f.name, "print": ann["print"], "photo": ann["photo"],
                     "repeat": int(f.stem.rsplit("_r", 1)[1]), "aspect_mm": ann["aspect_mm"],
                     "m": pm.measure_photo(ann)})
    return rows


def run_gates(base: Path = BASE) -> dict:
    ruler_path = base / "regla.json"
    g_print = fi1s.gate_print(_read(ruler_path) if ruler_path.exists() else {})
    if not g_print["passed"]:
        return {"gates": {"G0-impresión": g_print}, "passed": False}
    ruler = _read(ruler_path)
    marks = load_marks(base)
    per = {}
    for r in marks:
        g = pm.gate_photo(r["m"])
        g["regla_coincide"] = bool([float(v) for v in r["aspect_mm"]] == [float(v) for v in ruler[r["print"]]])
        g["passed"] = g["passed"] and g["regla_coincide"]
        per[r["file"]] = g
    return {"gates": {"G0-impresión": g_print, "fotos": per}, "n_marks": len(marks),
            "n_failed": int(sum(not v["passed"] for v in per.values())), "passed": bool(per)}


def run_analysis(base: Path = BASE, gates: dict | None = None) -> dict:
    marks = load_marks(base)
    if gates is not None:
        ok = {f for f, v in gates["gates"]["fotos"].items() if v["passed"]}
        marks = [r for r in marks if r["file"] in ok]
    if not marks:
        raise SystemExit("ninguna foto marcada pasa las puertas")
    res = fi1s.analyze(marks, _read(base / "valores_disenados.json"))
    res["n_marks_used"] = len(marks)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["plan", "gates", "analyze"])
    a = ap.parse_args(argv)
    if a.cmd == "plan":
        _write({"seed": fi1s.SEED, "sessions": fi1s.plan(photos())}, OUT / "plan.json")
        return 0
    if a.cmd == "gates":
        res = run_gates()
        _write(res, OUT / "gates.json")
        return 0 if res["passed"] else 1
    p = OUT / "gates.json"
    if not p.exists() or not _read(p).get("passed"):
        raise SystemExit("G0-impresión no superada o puertas sin ejecutar: el preregistro no permite seguir")
    _write(run_analysis(gates=_read(p)), OUT / "analisis.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
