"""H15 — robustez a pantalla/impresión/foto (solo simulación).

  python scripts/run_h15.py --set pilot   # piloto pequeño (semilla 20261217): comprueba que la cadena funciona
  python scripts/run_h15.py --set conf    # confirmación (semilla 20261216), código limpio
Usa los modelos congelados de H14 (results/summary/h14_frozen.json); no recalibra nada.
"""
import argparse
import datetime as dt
import hashlib
import json
import platform
import sys
import time
import warnings
from importlib.metadata import version
from pathlib import Path

from geovida import biometry as bio
from geovida import h15
from geovida.provenance import git_state

RAW, SUMMARY = Path("results/raw"), Path("results/summary")
H14_FROZEN = SUMMARY / "h14_frozen.json"
PKGS = ("numpy", "scipy", "scikit-image", "pandas", "opencv-python-headless")


def _pkg(p):
    try:
        return version(p)
    except Exception:
        return None


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", required=True, choices=("pilot", "conf"))
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--allow-dirty", action="store_true")
    a = ap.parse_args()
    state, t0 = git_state(), time.time()
    if a.set == "conf" and state["dirty_code"] and not a.allow_dirty:
        sys.exit("el código tiene cambios sin commitear: haz commit antes de confirmar (o --allow-dirty)")
    models = bio.models_from_json(H14_FROZEN.read_text())
    seed, n_in, n_out = ((h15.H15_PILOT_SEED, 150, 0) if a.set == "pilot" else (h15.H15_CONF_SEED, 1500, 400))
    cases = h15.chain_cases(n_in, n_out, seed)
    df = h15.run(cases, models, a.jobs)
    RAW.mkdir(parents=True, exist_ok=True)
    SUMMARY.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW / f"h15_{a.set}.csv.gz", index=False, compression="gzip")
    m = {"set": a.set, "started_utc": dt.datetime.fromtimestamp(t0, dt.timezone.utc).isoformat(),
         "elapsed_s": round(time.time() - t0, 1), "git_commit": state["commit"], "code_dirty": state["dirty_code"],
         "python": platform.python_version(), "packages": {p: _pkg(p) for p in PKGS}, "rows": len(df),
         "base_seed": seed, "n_in": n_in, "n_out": n_out, "h14_frozen_sha256": _sha(H14_FROZEN)}
    (SUMMARY / f"h15_{a.set}_manifest.json").write_text(json.dumps(m, indent=2))
    print(f"H15 {a.set}: {len(df)} filas en {m['elapsed_s']} s")


if __name__ == "__main__":
    main()
