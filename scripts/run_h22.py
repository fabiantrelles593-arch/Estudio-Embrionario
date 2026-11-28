"""H22 (docs/h22/PREREGISTRO_H22.md): estado «inservible» de la guardia, en imágenes sintéticas.

  python scripts/run_h22.py run --out results/h22/sweep.csv.gz
  python scripts/run_h22.py analyze --sweep results/h22/sweep.csv.gz --out results/h22/verdicts.json

``run`` mide una sola vez el diseño congelado de ``geovida.h22`` (semilla propia) y guarda un manifiesto con la
huella del código. ``analyze`` aplica la guardia congelada de v0.4 (``geovida/frozen/h9_frozen.json``) con el
perfil declarado ``realistic`` y ``geovida.h22.verdicts``, sin ningún parámetro libre.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import platform
import sys
import time
from importlib import resources
from importlib.metadata import version
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from geovida import h22  # noqa: E402
from geovida.certificate import load_frozen  # noqa: E402
from geovida.experiment import run_sweep  # noqa: E402
from geovida.provenance import git_state  # noqa: E402


def _frozen_sha() -> str:
    data = resources.files("geovida").joinpath("frozen/h9_frozen.json").read_bytes()
    return hashlib.sha256(data).hexdigest()


def cmd_run(a) -> int:
    out = Path(a.out)
    if out.exists() and not a.force:
        raise SystemExit(f"{out} ya existe: H22 se mide una sola vez (usa --force solo para pruebas)")
    design = h22.design(a.reps)
    t0 = time.time()
    df = run_sweep(design, n_jobs=a.jobs, base_seed=h22.SEED, segmenters=h22.SEGMENTERS, extra=h22.guard_extra)
    elapsed = time.time() - t0
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, compression="gzip")
    manifest = {
        "started_utc": dt.datetime.fromtimestamp(t0, dt.timezone.utc).isoformat(),
        "elapsed_s": round(elapsed, 1), "reps": a.reps, "conditions": len(design), "rows": len(df),
        "base_seed": h22.SEED, "segmenters": list(h22.SEGMENTERS), "profiles": list(h22.PROFILES),
        "shapes": list(h22.SHAPES), "frozen_sha256": _frozen_sha(), "python": platform.python_version(),
        "packages": {p: version(p) for p in ("numpy", "scipy", "scikit-image", "pandas")},
        "provenance": git_state(Path(__file__).resolve().parents[1]),
    }
    out.with_name(out.name.replace(".csv.gz", "") + "_manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "provenance"}, indent=1))
    return 0


def cmd_analyze(a) -> int:
    df = pd.read_csv(a.sweep)
    frozen = load_frozen()
    c = h22.classify(df, frozen)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    h22.by_stratum(c).to_csv(out.with_suffix(".strata.csv"), index=False)
    h22.crosstab(c).to_csv(out.with_suffix(".crosstab.csv"), index=False)
    res = {"verdicts": h22.verdicts(c), "sensitivity": h22.sensitivity(df, frozen), "rows": len(df),
           "frozen_sha256": _frozen_sha()}
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False, default=float), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False, default=float))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--out", default="results/h22/sweep.csv.gz")
    r.add_argument("--reps", type=int, default=h22.REPS)
    r.add_argument("--jobs", type=int, default=1)
    r.add_argument("--force", action="store_true")
    z = sub.add_parser("analyze")
    z.add_argument("--sweep", default="results/h22/sweep.csv.gz")
    z.add_argument("--out", default="results/h22/verdicts.json")
    a = ap.parse_args(argv)
    return cmd_run(a) if a.cmd == "run" else cmd_analyze(a)


if __name__ == "__main__":
    raise SystemExit(main())
