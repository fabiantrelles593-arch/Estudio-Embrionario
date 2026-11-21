"""H16 — ¿puede el certificado enterarse, solo con la imagen, de que pasó por una cadena? (solo simulación)

  python scripts/run_h16.py --set pilot    # piloto declarado (semilla 20261220): no confirma nada
  python scripts/run_h16.py --set train    # conjunto de ajuste de la guardia (semilla 20261221), familia A; escribe el modelo congelado
  python scripts/run_h16.py --set conf_a   # confirmación, familia A nueva (semilla 20261222), código limpio y modelo ya congelado
  python scripts/run_h16.py --set conf_b   # confirmación, familia B nunca vista (semilla 20261223), código limpio y modelo ya congelado
Línea base: los modelos congelados de H14 (results/summary/h14_frozen.json); no se recalibran.
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

import pandas as pd

from geovida import biometry as bio
from geovida import h16
from geovida.provenance import git_state

RAW, SUMMARY = Path("results/raw"), Path("results/summary")
H14_FROZEN = SUMMARY / "h14_frozen.json"
H16_FROZEN = SUMMARY / "h16_chain_frozen.json"
PKGS = ("numpy", "scipy", "scikit-image", "pandas", "opencv-python-headless")
N_PILOT, N_TRAIN, N_CONF = 400, 1500, 1500


def _pkg(p):
    try:
        return version(p)
    except Exception:
        return None


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(name, state, t0, rows, seed, n_in, extra=None):
    m = {"set": name, "started_utc": dt.datetime.fromtimestamp(t0, dt.timezone.utc).isoformat(),
         "elapsed_s": round(time.time() - t0, 1), "git_commit": state["commit"], "code_dirty": state["dirty_code"],
         "python": platform.python_version(), "packages": {p: _pkg(p) for p in PKGS}, "rows": rows, "base_seed": seed,
         "n_in_per_kind": n_in, "h14_frozen_sha256": _sha(H14_FROZEN), **(extra or {})}
    (SUMMARY / f"h16_{name}_manifest.json").write_text(json.dumps(m, indent=2))
    return m


def main():
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", required=True, choices=("pilot", "train", "conf_a", "conf_b"))
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--allow-dirty", action="store_true")
    a = ap.parse_args()
    state, t0 = git_state(), time.time()
    RAW.mkdir(parents=True, exist_ok=True)
    SUMMARY.mkdir(parents=True, exist_ok=True)
    models = bio.models_from_json(H14_FROZEN.read_text())

    if a.set == "pilot":
        # Piloto: ajusta con las filas de índice par de la familia A y evalúa con las impares (A) y con la familia B completa.
        seed = h16.H16_PILOT_SEED
        da = h16.run(h16.cases(N_PILOT, seed, "A"), models, a.jobs)
        db = h16.run(h16.cases(N_PILOT, seed, "B"), models, a.jobs)
        t = h16.training_table(da[da["idx"] % 2 == 0])
        par, rec = h16.fit(t), h16.fit_recal(t)

        def both(d):
            return h16.apply_recal(h16.apply_chain_aware(d, models, par), models, rec)

        ta, tb = both(da[da["idx"] % 2 == 1]), both(db)
        pd.concat([ta, tb]).to_csv(RAW / "h16_pilot.csv.gz", index=False, compression="gzip")
        v = {g: h16.evaluate_h16(ta, tb, guard=g) for g in h16.GUARDS}
        (SUMMARY / "h16_pilot_verdicts.json").write_text(json.dumps(v, indent=2, default=float))
        _manifest("pilot", state, t0, len(ta) + len(tb), seed, N_PILOT, {"nota": "exploratorio; no confirma nada"})
        print(json.dumps(v, indent=2, default=float))
        return

    if a.set != "train" and state["dirty_code"] and not a.allow_dirty:
        sys.exit("el código tiene cambios sin commitear: haz commit antes de confirmar (o --allow-dirty)")
    if a.set == "train":
        seed = h16.H16_TRAIN_SEED
        df = h16.run(h16.cases(N_TRAIN, seed, "A"), models, a.jobs)
        df.to_csv(RAW / "h16_train.csv.gz", index=False, compression="gzip")
        t = h16.training_table(df)
        meta = {"train_seed": seed, "n_in_per_kind": N_TRAIN, "family": "A", "rows_used": len(t),
                "h14_frozen_sha256": _sha(H14_FROZEN), "git_commit": state["commit"]}
        H16_FROZEN.write_text(h16.freeze_to_json(h16.fit(t), h16.fit_recal(t), meta))
        m = _manifest("train", state, t0, len(df), seed, N_TRAIN, {"h16_frozen_sha256": _sha(H16_FROZEN)})
        print(f"H16 train: {len(df)} filas ({len(t)} usadas) en {m['elapsed_s']} s; congelado: {H16_FROZEN}")
        return

    if not H16_FROZEN.exists():
        sys.exit("falta el modelo congelado de la guardia: corre --set train y haz commit antes de confirmar")
    par, rec = h16.freeze_from_json(H16_FROZEN.read_text())
    fam, seed = ("A", h16.H16_CONF_A_SEED) if a.set == "conf_a" else ("B", h16.H16_CONF_B_SEED)
    df = h16.apply_recal(h16.apply_chain_aware(h16.run(h16.cases(N_CONF, seed, fam), models, a.jobs), models, par), models, rec)
    df.to_csv(RAW / f"h16_{a.set}.csv.gz", index=False, compression="gzip")
    m = _manifest(a.set, state, t0, len(df), seed, N_CONF, {"family": fam, "h16_frozen_sha256": _sha(H16_FROZEN)})
    print(f"H16 {a.set}: {len(df)} filas en {m['elapsed_s']} s")


if __name__ == "__main__":
    sys.exit(main())
