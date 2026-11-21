"""H21 (docs/PREREGISTRO_H21.md): Crofton frente a ``area_sdf`` en máscaras segmentadas de formas nuevas.

  python scripts/run_h21.py run --out results/h21/sweep.csv.gz
  python scripts/run_h21.py analyze --sweep results/h21/sweep.csv.gz --out results/h21/verdicts.json

``run`` mide una sola vez el diseño congelado de ``geovida.h21`` (semilla propia) y guarda un manifiesto con la
huella del código. ``analyze`` resume por celda y aplica ``geovida.h21.verdicts`` sin ningún parámetro libre.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
import sys
import time
from importlib.metadata import version
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from geovida import h21  # noqa: E402
from geovida.experiment import run_sweep  # noqa: E402
from geovida.provenance import git_state  # noqa: E402


def cmd_run(a) -> int:
    out = Path(a.out)
    if out.exists() and not a.force:
        raise SystemExit(f"{out} ya existe: H21 se mide una sola vez (usa --force solo para pruebas)")
    design = h21.design(a.reps)
    t0 = time.time()
    df = run_sweep(design, n_jobs=a.jobs, base_seed=h21.SEED, segmenters=h21.SEGMENTERS, extra=h21.crofton_extra)
    elapsed = time.time() - t0
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, compression="gzip")
    manifest = {
        "started_utc": dt.datetime.fromtimestamp(t0, dt.timezone.utc).isoformat(),
        "elapsed_s": round(elapsed, 1), "reps": a.reps, "conditions": len(design), "rows": len(df),
        "base_seed": h21.SEED, "segmenters": list(h21.SEGMENTERS), "profiles": list(h21.PROFILES),
        "shapes": list(h21.SHAPES), "python": platform.python_version(),
        "packages": {p: version(p) for p in ("numpy", "scipy", "scikit-image", "pandas")},
        "provenance": git_state(Path(__file__).resolve().parents[1]),
    }
    out.with_name(out.name.replace(".csv.gz", "") + "_manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "provenance"}, indent=1))
    return 0


def cmd_analyze(a) -> int:
    df = pd.read_csv(a.sweep)
    cells = h21.cell_table(df)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cells.to_csv(out.with_suffix(".cells.csv"), index=False)
    h21.descriptive(df).to_csv(out.with_suffix(".descriptive.csv"), index=False)
    res = {"verdicts": h21.verdicts(cells), "summary": h21.summary_numbers(cells), "rows": len(df),
           "cells": len(cells)}
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False, default=float), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False, default=float))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--out", default="results/h21/sweep.csv.gz")
    r.add_argument("--reps", type=int, default=h21.REPS)
    r.add_argument("--jobs", type=int, default=1)
    r.add_argument("--force", action="store_true")
    z = sub.add_parser("analyze")
    z.add_argument("--sweep", default="results/h21/sweep.csv.gz")
    z.add_argument("--out", default="results/h21/verdicts.json")
    a = ap.parse_args(argv)
    return cmd_run(a) if a.cmd == "run" else cmd_analyze(a)


if __name__ == "__main__":
    raise SystemExit(main())
