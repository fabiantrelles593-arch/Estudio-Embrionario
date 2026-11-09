"""Barridos del semáforo H6: fase de calibración (--phase cal) y de confirmación (--phase test)."""
import argparse
import datetime as dt
import json
import platform
import time
from importlib.metadata import version
from pathlib import Path

from geovida.experiment import H6_CAL_SEED, H6_SEED, h6_design, run_sweep
from geovida.provenance import git_state

SEGMENTERS = ("global", "otsu", "smoothed_otsu")  # los tres preregistrados
PHASES = {"cal": (H6_CAL_SEED, "results/raw/h6cal_sweep.csv.gz", "results/summary/h6cal_run_manifest.json", 30),
          "test": (H6_SEED, "results/raw/h6_sweep.csv.gz", "results/summary/h6_run_manifest.json", 40)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=PHASES, required=True)
    ap.add_argument("--reps", type=int, default=None)
    ap.add_argument("--jobs", type=int, default=2)
    a = ap.parse_args()
    seed, out, manifest_path, reps_default = PHASES[a.phase]
    reps = a.reps or reps_default
    design = h6_design(reps)
    t0 = time.time()
    df = run_sweep(design, n_jobs=a.jobs, base_seed=seed, segmenters=SEGMENTERS)
    elapsed = time.time() - t0
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, compression="gzip")
    state = git_state()
    manifest = {"phase": a.phase, "started_utc": dt.datetime.fromtimestamp(t0, dt.timezone.utc).isoformat(),
                "elapsed_s": round(elapsed, 1), "git_commit": state["commit"], "code_dirty": state["dirty_code"],
                "reps": reps, "conditions": len(design), "rows": len(df), "base_seed": seed,
                "segmenters": list(SEGMENTERS), "python": platform.python_version(),
                "packages": {p: version(p) for p in ("numpy", "scipy", "scikit-image", "pandas", "statsmodels")}}
    Path(manifest_path).write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
