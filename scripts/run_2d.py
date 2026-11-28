"""Ejecuta la prueba de estrés 2D (docs/PREREGISTRO_2D.md)."""
import argparse
import datetime as dt
import json
import platform
import time
from importlib.metadata import version
from pathlib import Path

from geovida.provenance import git_state
from geovida.twod import BASE_SEED_2D, design_2d, run_sweep_2d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--out", default="results/raw/h5_sweep.csv.gz")
    ap.add_argument("--manifest", default="results/summary/h5_run_manifest.json")
    a = ap.parse_args()
    design = design_2d(a.reps)
    t0 = time.time()
    df = run_sweep_2d(design, n_jobs=a.jobs)
    elapsed = time.time() - t0
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out, index=False, compression="gzip")
    state = git_state()
    manifest = {
        "started_utc": dt.datetime.fromtimestamp(t0, dt.timezone.utc).isoformat(),
        "elapsed_s": round(elapsed, 1), "git_commit": state["commit"],
        "code_dirty": state["dirty_code"], "reps": a.reps, "conditions": len(design),
        "rows": len(df), "base_seed": BASE_SEED_2D, "python": platform.python_version(),
        "packages": {p: version(p) for p in ("numpy", "scipy", "scikit-image", "pandas")},
    }
    Path(a.manifest).write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
