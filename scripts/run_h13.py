"""H13 — biometría fetal temprana simulada con certificado de incertidumbre (Programa B).

Solo investigación y educación. Imágenes sintéticas; no hay datos de personas.

  python scripts/run_h13.py --set pilot    # semilla de piloto, pocas réplicas; solo para ajustar el diseño
  python scripts/run_h13.py --set cal      # calibración (100 réplicas por celda) y congelado de modelos
  python scripts/run_h13.py --set conf     # confirmación con los modelos congelados (árbol de código limpio)
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
from geovida import h13
from geovida.provenance import git_state

RAW, SUMMARY = Path("results/raw"), Path("results/summary")
FROZEN = SUMMARY / "h13_frozen.json"
PKGS = ("numpy", "scipy", "scikit-image", "pandas")


def _manifest(name, state, t0, **extra):
    m = {"set": name, "started_utc": dt.datetime.fromtimestamp(t0, dt.timezone.utc).isoformat(),
         "elapsed_s": round(time.time() - t0, 1), "git_commit": state["commit"], "code_dirty": state["dirty_code"],
         "python": platform.python_version(), "packages": {p: version(p) for p in PKGS}, **extra}
    SUMMARY.mkdir(parents=True, exist_ok=True)
    (SUMMARY / f"h13_{name}_manifest.json").write_text(json.dumps(m, indent=2))
    return m


def main():
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", required=True, choices=("pilot", "cal", "conf"))
    ap.add_argument("--reps", type=int, default=None)
    ap.add_argument("--n-in", type=int, default=None)
    ap.add_argument("--n-out", type=int, default=None)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--allow-dirty", action="store_true")
    a = ap.parse_args()
    state = git_state()
    t0 = time.time()
    RAW.mkdir(parents=True, exist_ok=True)

    if a.set == "pilot":
        reps, n_in, n_out = a.reps or 10, a.n_in or 100, a.n_out or 40
        cal = h13.run_calibration(reps, h13.H13_PILOT_SEED, a.jobs)
        models = h13.fit_models(cal)
        cases = h13.confirmation_cases(n_in, n_out, h13.H13_PILOT_SEED)
        df = h13.run_confirmation(cases, models, a.jobs)
        cal.to_csv(RAW / "h13_pilot_cal.csv.gz", index=False, compression="gzip")
        df.to_csv(RAW / "h13_pilot_conf.csv.gz", index=False, compression="gzip")
        verdicts = h13.evaluate_h13(df, n_boot=500, seed=h13.BOOT_SEED)
        (SUMMARY / "h13_pilot_verdicts.json").write_text(json.dumps(verdicts, indent=2, default=float))
        _manifest("pilot", state, t0, reps=reps, n_in=n_in, n_out=n_out, base_seed=h13.H13_PILOT_SEED)
        print(json.dumps(verdicts, indent=2, default=float))
        return

    if a.set == "cal":
        reps = a.reps or 100
        cal = h13.run_calibration(reps, h13.H13_CAL_SEED, a.jobs)
        cal.to_csv(RAW / "h13_cal.csv.gz", index=False, compression="gzip")
        models = h13.fit_models(cal)
        meta = {"base_seed": h13.H13_CAL_SEED, "reps_per_cell": reps, "grid": h13.CAL_GRID,
                "looks": bio.LOOKS, "min_grain_px": bio.MIN_GRAIN_PX, "git_commit": state["commit"],
                "code_dirty": state["dirty_code"]}
        SUMMARY.mkdir(parents=True, exist_ok=True)
        FROZEN.write_text(bio.models_to_json(models, meta))
        sha = hashlib.sha256(FROZEN.read_bytes()).hexdigest()
        _manifest("cal", state, t0, reps=reps, rows=len(cal), base_seed=h13.H13_CAL_SEED, frozen_sha256=sha)
        print("modelos congelados en", FROZEN, "SHA-256", sha)
        return

    # confirmación: modelos congelados, código limpio
    if state["dirty_code"] and not a.allow_dirty:
        sys.exit("el código tiene cambios sin commitear: haz commit antes de confirmar (o --allow-dirty)")
    text = FROZEN.read_text()
    models = bio.models_from_json(text)
    n_in, n_out = a.n_in or 1500, a.n_out or 400
    cases = h13.confirmation_cases(n_in, n_out, h13.H13_CONF_SEED)
    df = h13.run_confirmation(cases, models, a.jobs)
    df.to_csv(RAW / "h13_conf.csv.gz", index=False, compression="gzip")
    _manifest("conf", state, t0, n_in=n_in, n_out=n_out, rows=len(df), base_seed=h13.H13_CONF_SEED,
              frozen_sha256=hashlib.sha256(text.encode()).hexdigest(), segmenters=list(bio.SEGMENTERS))
    print("confirmación lista:", len(df), "filas")


if __name__ == "__main__":
    main()
