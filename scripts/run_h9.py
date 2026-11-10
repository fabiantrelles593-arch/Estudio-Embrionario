"""Barridos del certificado vectorial (v0.4, H9/H10).

  python scripts/run_h9.py --set pilot           # semilla de piloto, pocas réplicas
  python scripts/run_h9.py --set cal             # calibración (se congela después)
  python scripts/run_h9.py --set test            # confirmación, mismas formas
  python scripts/run_h9.py --set unseen          # mancuerna y copa
  python scripts/run_h9.py --set shift           # perfiles de imagen nunca vistos
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
    H9_CAL_SEED, H9_PILOT_SEED, H9_SHIFT_SEED, H9_TEST_SEED, cert_extra, design_cal,
    design_shift, design_unseen,
)
from geovida.experiment import run_sweep
from geovida.provenance import git_state

SEGMENTERS = ("global", "otsu", "smoothed_otsu")
SETS = {  # nombre: (diseño, semilla, réplicas por defecto)
    "cal": (design_cal, H9_CAL_SEED, 15),
    "test": (design_cal, H9_TEST_SEED, 15),
    "unseen": (design_unseen, H9_TEST_SEED, 12),
    "shift": (design_shift, H9_SHIFT_SEED, 5),
    "pilot": (design_cal, H9_PILOT_SEED, 3),
    "pilot_unseen": (design_unseen, H9_PILOT_SEED, 3),
    "pilot_shift": (design_shift, H9_PILOT_SEED, 3),
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
    out = Path(f"results/raw/h9_{a.set}.csv.gz")
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, compression="gzip")
    manifest = {"set": a.set, "started_utc": dt.datetime.fromtimestamp(t0, dt.timezone.utc).isoformat(),
                "elapsed_s": round(elapsed, 1), "git_commit": state["commit"],
                "code_dirty": state["dirty_code"], "reps": reps, "conditions": len(design),
                "rows": len(df), "base_seed": seed, "segmenters": list(SEGMENTERS),
                "python": platform.python_version(),
                "packages": {p: version(p) for p in ("numpy", "scipy", "scikit-image", "pandas")}}
    Path(f"results/summary/h9_{a.set}_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
