"""FI-1 (docs/prenatal/PREREGISTRO_FOTO_IMPRESION.md): error de medir sobre fotos de impresiones de ecografía.

    python scripts/fi1_foto_impresion.py plan       # orden aleatorio de las sesiones de marcado (semilla 20261127)
    python scripts/fi1_foto_impresion.py gates      # G0-ética, G0-escala y G0-homografía
    python scripts/fi1_foto_impresion.py analyze    # FI-1a, FI-1b y FI-1c (solo si las puertas pasaron)

Todo lo que contiene datos de la persona está en ``data/private/ecografia/`` (ignorado por git) y nunca se sube:

* ``g0_etica.json``: {"consentimiento_codigo": "CI-001", "aval_etico": "...", "anonimizacion_revisada": true}; sin
  nombres. Sin este registro completo el script no mide nada.
* ``anon/<foto>.png``: fotos anonimizadas con ``scripts/anonimizar_imagen.py`` (código ``<impresion>-<foto>``).
* ``marcas/<foto>_r<k>.json``: lo que marca la persona de D2 en la repetición k (formato en
  ``geovida.print_measure.measure_photo``), más ``print`` y ``photo``. No contiene los valores impresos.
* ``valores_impresos.json``: {impresión: {pareja: mm}}, copiado de la impresión por otra persona o en otro momento,
  para que quien marca no los vea.

Resultados agregados (sin imágenes ni datos personales) en ``results/prenatal/fi1/``. Ningún resultado clínico.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from geovida import print_measure as pm
from geovida.provenance import git_state

BASE = Path("data/private/ecografia")
OUT = Path("results/prenatal/fi1")
N_REPEATS = 3


def _read(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _write(res: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    res["provenance"] = git_state()
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "provenance"}, ensure_ascii=False, default=float)[:3000])


def ethics(base: Path = BASE) -> dict:
    f = base / "g0_etica.json"
    return pm.gate_ethics(_read(f) if f.exists() else None)


def plan(photos: list[str], seed: int = pm.SEED_FI1) -> list[dict]:
    """§3.4: cada foto se marca 3 veces, en 3 sesiones; en cada sesión, las fotos en orden aleatorio."""
    rng = np.random.default_rng(seed)
    out = []
    for r in range(1, N_REPEATS + 1):
        for i in rng.permutation(len(photos)):
            out.append({"session": r, "photo": photos[i], "file": f"marcas/{photos[i]}_r{r}.json"})
    return out


def load_marks(base: Path = BASE) -> list[dict]:
    rows = []
    for f in sorted((base / "marcas").glob("*_r*.json")):
        ann = _read(f)
        rows.append({"file": f.name, "print": ann["print"], "photo": ann["photo"],
                     "repeat": int(f.stem.rsplit("_r", 1)[1]), "m": pm.measure_photo(ann)})
    return rows


def run_gates(base: Path = BASE) -> dict:
    g_e = ethics(base)
    if not g_e["passed"]:
        return {"gates": {"G0-ética": g_e}, "passed": False}
    marks = load_marks(base)
    per = {r["file"]: pm.gate_photo(r["m"]) for r in marks}
    ok = bool(per) and all(v["passed"] for v in per.values())
    return {"gates": {"G0-ética": g_e, "fotos": per}, "n_marks": len(marks), "passed": ok}


def build_rows(marks: list[dict], printed: dict, key: str) -> list[dict]:
    rows = []
    for r in marks:
        for pair, d in r["m"]["pairs"].items():
            rows.append({"print": r["print"], "photo": f'{r["print"]}/{r["photo"]}', "pair": pair,
                         "repeat": r["repeat"], "measured_mm": d[key], "printed_mm": float(printed[r["print"]][pair])})
    return rows


def run_analysis(base: Path = BASE) -> dict:
    marks = load_marks(base)
    printed = _read(base / "valores_impresos.json")
    main = pm.analyze(build_rows(marks, printed, "corrected_mm"))
    raw = pm.analyze(build_rows(marks, printed, "uncorrected_mm"))
    by_len = sorted(((float(printed[r["print"]][p]), abs(d["corrected_mm"] / float(printed[r["print"]][p]) - 1))
                     for r in marks for p, d in r["m"]["pairs"].items()))
    return {"analysis": "FI-1", **main,
            "fi1c": {"median_abs_error_uncorrected": raw["median_abs_error"],
                     "median_abs_error_uncorrected_ci": raw["median_abs_error_ci"],
                     "error_by_length": [{"printed_mm": a, "abs_rel_error": b} for a, b in by_len]},
            "verdict": {"FI-1a": main["verdict_fi1a"], "FI-1b": main["verdict_fi1b"]}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["plan", "gates", "analyze"])
    a = ap.parse_args(argv)
    g_e = ethics()
    if not g_e["passed"]:
        print(f"G0-ética no superada (faltan: {', '.join(g_e['missing'])}). No se planifica, mide ni analiza nada.")
        return 1
    if a.cmd == "plan":
        photos = sorted(p.stem for p in (BASE / "anon").glob("*.png"))
        if not photos:
            raise SystemExit(f"no hay fotos anonimizadas en {BASE / 'anon'}")
        _write({"seed": pm.SEED_FI1, "sessions": plan(photos)}, OUT / "plan.json")
        return 0
    if a.cmd == "gates":
        res = run_gates()
        _write(res, OUT / "gates.json")
        return 0 if res["passed"] else 1
    p = OUT / "gates.json"
    if not p.exists() or not _read(p).get("passed"):
        raise SystemExit("las puertas no están superadas; el preregistro no permite seguir")
    _write(run_analysis(), OUT / "analisis.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
