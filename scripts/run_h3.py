"""Ejecuta el barrido confirmatorio H3 (formas nuevas, semilla nueva)."""
import argparse
import datetime as dt
import json
import platform
import time
from importlib.metadata import version
from pathlib import Path

from geovida.experiment import H3_SEED, h3_design, run_sweep
from geovida.provenance import git_state

SEGMENTERS = ("global", "otsu", "smoothed_otsu", "otsu_clean")  # el último es extensión


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--out", default="results/raw/h3_sweep.csv.gz")
    ap.add_argument("--manifest", default="results/summary/h3_run_manifest.json")
    a = ap.parse_args()

    design = h3_design(a.reps)
    t0 = time.time()
    df = run_sweep(design, n_jobs=a.jobs, base_seed=H3_SEED, segmenters=SEGMENTERS)
    elapsed = time.time() - t0

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out, index=False, compression="gzip")
    state = git_state()
    manifest = {
        "started_utc": dt.datetime.fromtimestamp(t0, dt.timezone.utc).isoformat(),
        "elapsed_s": round(elapsed, 1),
        "git_commit": state["commit"], "code_dirty": state["dirty_code"],
        "reps": a.reps, "conditions": len(design), "rows": len(df),
        "base_seed": H3_SEED, "segmenters": list(SEGMENTERS),
        "python": platform.python_version(),
        "packages": {p: version(p) for p in
                     ("numpy", "scipy", "scikit-image", "pandas", "statsmodels")},
    }
    Path(a.manifest).write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
