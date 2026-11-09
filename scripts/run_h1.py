"""Ejecuta el barrido factorial de H1 y escribe resultados + manifiesto."""
import argparse
import datetime as dt
import json
import platform
import subprocess
import time
from importlib.metadata import version
from pathlib import Path

from geovida.experiment import BASE_SEED, full_design, run_sweep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--out", default="results/raw/h1_sweep.csv.gz")
    ap.add_argument("--manifest", default="results/summary/h1_run_manifest.json")
    a = ap.parse_args()

    design = full_design(a.reps)
    t0 = time.time()
    df = run_sweep(design, n_jobs=a.jobs)
    elapsed = time.time() - t0

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out, index=False, compression="gzip")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                            text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", "src", "docs"],
                                capture_output=True, text=True).stdout.strip())
    manifest = {
        "started_utc": dt.datetime.fromtimestamp(t0, dt.timezone.utc).isoformat(),
        "elapsed_s": round(elapsed, 1),
        "git_commit": commit, "working_tree_dirty_src_docs": dirty,
        "reps": a.reps, "conditions": len(design), "rows": len(df),
        "base_seed": BASE_SEED, "python": platform.python_version(),
        "packages": {p: version(p) for p in
                     ("numpy", "scipy", "scikit-image", "pandas", "statsmodels")},
    }
    Path(a.manifest).write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
