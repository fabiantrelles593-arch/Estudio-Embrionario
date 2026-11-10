"""Ejecuta el barrido de H8 (docs/PREREGISTRO_H8.md): series de crecimiento con semáforo."""
import argparse
import datetime as dt
import json
import platform
import time
from importlib.metadata import version
from pathlib import Path

from geovida.growth import H8_PILOT_SEED, H8_SEED, design_h8, run_h8
from geovida.provenance import git_state


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--pilot", action="store_true", help="usa la semilla de piloto y otro archivo")
    a = ap.parse_args()
    seed = H8_PILOT_SEED if a.pilot else H8_SEED
    tag = "h8pilot" if a.pilot else "h8"
    design = design_h8(a.reps)
    t0 = time.time()
    df = run_h8(design, n_jobs=a.jobs, base_seed=seed)
    elapsed = time.time() - t0
    out = Path(f"results/raw/{tag}_sweep.csv.gz")
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, compression="gzip")
    state = git_state()
    manifest = {
        "started_utc": dt.datetime.fromtimestamp(t0, dt.timezone.utc).isoformat(),
        "elapsed_s": round(elapsed, 1), "git_commit": state["commit"],
        "code_dirty": state["dirty_code"], "reps": a.reps, "series": len(design),
        "rows": len(df), "base_seed": seed, "python": platform.python_version(),
        "frozen_models": "results/summary/h6_frozen_models.json (copiados en budget.FROZEN_H6)",
        "packages": {p: version(p) for p in ("numpy", "scipy", "scikit-image", "pandas")},
    }
    Path(f"results/summary/{tag}_run_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
