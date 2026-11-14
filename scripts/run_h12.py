"""Barridos de ecografía 3D simulada (v0.5, H12).

  python scripts/run_h12.py --set pilot           # semilla de piloto, pocas réplicas
  python scripts/run_h12.py --set cal             # calibración (se congela después)
  python scripts/run_h12.py --set test            # confirmación, mismas formas
  python scripts/run_h12.py --set unseen          # mancuerna y copa
  python scripts/run_h12.py --set shift           # perfiles us_atten y us_coarse
"""
import argparse
import datetime as dt
import json
import platform
import time
import warnings
from importlib.metadata import version
from pathlib import Path

from geovida.certsweep import (
    H12_CAL_SEED, H12_PILOT_SEED, H12_SHIFT_SEED, H12_TEST_SEED, cert_extra, design_us_cal,
    design_us_shift, design_us_unseen,
)
from geovida.experiment import run_sweep
from geovida.provenance import git_state

SEGMENTERS = ("global", "otsu", "smoothed_otsu")
SETS = {  # nombre: (diseño, semilla, réplicas por defecto)
    "cal": (design_us_cal, H12_CAL_SEED, 10),
    "test": (design_us_cal, H12_TEST_SEED, 10),
    "unseen": (design_us_unseen, H12_TEST_SEED, 8),
    "shift": (design_us_shift, H12_SHIFT_SEED, 3),
    "pilot": (design_us_cal, H12_PILOT_SEED, 2),
    "pilot_unseen": (design_us_unseen, H12_PILOT_SEED, 2),
    "pilot_shift": (design_us_shift, H12_PILOT_SEED, 2),
}


def main():
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", required=True, choices=SETS)
    ap.add_argument("--reps", type=int, default=None)
    ap.add_argument("--jobs", type=int, default=2)
    a = ap.parse_args()
    design_fn, seed, reps_default = SETS[a.set]
    reps = a.reps or reps_default
    design = design_fn(reps)
    state = git_state()   # al empezar: es el código que se ejecuta
    t0 = time.time()
    df = run_sweep(design, n_jobs=a.jobs, base_seed=seed, segmenters=SEGMENTERS, extra=cert_extra)
    elapsed = time.time() - t0
    out = Path(f"results/raw/h12_{a.set}.csv.gz")
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, compression="gzip")
    manifest = {"set": a.set, "started_utc": dt.datetime.fromtimestamp(t0, dt.timezone.utc).isoformat(),
                "elapsed_s": round(elapsed, 1), "git_commit": state["commit"],
                "code_dirty": state["dirty_code"], "reps": reps, "conditions": len(design),
                "rows": len(df), "base_seed": seed, "segmenters": list(SEGMENTERS),
                "python": platform.python_version(),
                "packages": {p: version(p) for p in ("numpy", "scipy", "scikit-image", "pandas")}}
    Path(f"results/summary/h12_{a.set}_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
