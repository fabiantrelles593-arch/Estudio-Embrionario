"""H14 — compuerta de «tasa de medidas utilizables» (solo simulación).

  python scripts/run_h14.py --set freeze   # deriva h14_frozen.json de la MISMA calibración de H13 (sin imágenes nuevas)
  python scripts/run_h14.py --set conf     # confirmación con semilla nueva: modelo con compuerta y sin ella, mismos casos
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

import numpy as np
import pandas as pd

from geovida import biometry as bio
from geovida import h13, h14
from geovida.provenance import git_state

RAW, SUMMARY = Path("results/raw"), Path("results/summary")
H13_FROZEN, H14_FROZEN = SUMMARY / "h13_frozen.json", SUMMARY / "h14_frozen.json"
H13_CAL = RAW / "h13_cal.csv.gz"
PKGS = ("numpy", "scipy", "scikit-image", "pandas")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(name, state, t0, **extra):
    m = {"set": name, "started_utc": dt.datetime.fromtimestamp(t0, dt.timezone.utc).isoformat(),
         "elapsed_s": round(time.time() - t0, 1), "git_commit": state["commit"], "code_dirty": state["dirty_code"],
         "python": platform.python_version(), "packages": {p: version(p) for p in PKGS}, **extra}
    (SUMMARY / f"h14_{name}_manifest.json").write_text(json.dumps(m, indent=2))


def main():
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", required=True, choices=("freeze", "conf"))
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--allow-dirty", action="store_true")
    a = ap.parse_args()
    state, t0 = git_state(), time.time()
    SUMMARY.mkdir(parents=True, exist_ok=True)

    if a.set == "freeze":
        cal = pd.read_csv(H13_CAL)
        models = h13.fit_models(cal, min_usable_rate=h14.H14_FREEZE_MIN_USABLE)
        old = bio.models_from_json(H13_FROZEN.read_text())
        for k, m in models.items():                      # el sesgo y la desviación NO cambian: solo se añade la compuerta
            assert np.allclose(m.bias_px, old[k].bias_px, atol=1e-12) and np.allclose(m.sd_px, old[k].sd_px, atol=1e-12), k
        meta = {"derived_from": "results/raw/h13_cal.csv.gz", "source_cal_sha256": _sha(H13_CAL),
                "h13_frozen_sha256": _sha(H13_FROZEN), "min_usable_rate": h14.H14_FREEZE_MIN_USABLE,
                "usable_definition": "|err_px| <= 0.5 * n", "git_commit": state["commit"]}
        H14_FROZEN.write_text(bio.models_to_json(models, meta))
        _manifest("freeze", state, t0, frozen_sha256=_sha(H14_FROZEN), **meta)
        print("congelado:", H14_FROZEN, _sha(H14_FROZEN))
        return

    if state["dirty_code"] and not a.allow_dirty:
        sys.exit("el código tiene cambios sin commitear: haz commit antes de confirmar (o --allow-dirty)")
    gated = bio.models_from_json(H14_FROZEN.read_text())
    ungated = bio.models_from_json(H13_FROZEN.read_text())
    cases = h13.confirmation_cases(1500, 400, h14.H14_CONF_SEED)
    parts = []
    for name, models in (("gated", gated), ("ungated", ungated)):
        d = h13.run_confirmation(cases, models, a.jobs)
        d["variant"] = name
        parts.append(d)
    df = pd.concat(parts, ignore_index=True)
    df.to_csv(RAW / "h14_conf.csv.gz", index=False, compression="gzip")
    _manifest("conf", state, t0, rows=len(df), base_seed=h14.H14_CONF_SEED, n_in=1500, n_out=400,
              h14_frozen_sha256=_sha(H14_FROZEN), h13_frozen_sha256=_sha(H13_FROZEN))
    print("confirmación H14 lista:", len(df), "filas")


if __name__ == "__main__":
    main()
