"""Análisis confirmatorio de H12 según docs/PREREGISTRO_H12.md (no cambia criterios).

Usa ``results/summary/h12_frozen.json`` (calibración congelada) y el congelado empaquetado de v0.4;
no reajusta nada. Para H12b(ii) hace falta el barrido de v0.4 ``results/raw/h9_test.csv.gz``
(se regenera con ``python scripts/run_h9.py --set test``; semilla en h9_test_manifest.json).
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from geovida import h9, h12
from geovida.certificate import load_frozen

RAW = Path("results/raw")
OUT = Path("results/summary")


def clean(o):
    """JSON estándar: NaN -> null, tipos de numpy -> Python."""
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not math.isfinite(float(o)) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def load(name):
    return pd.read_csv(RAW / f"h12_{name}.csv.gz")


def main():
    frozen_us = json.loads((OUT / "h12_frozen.json").read_text())
    frozen_v04 = load_frozen()
    test, unseen, shift = load("test"), load("unseen"), load("shift")
    old_path = RAW / "h9_test.csv.gz"
    old = pd.read_csv(old_path) if old_path.exists() else pd.DataFrame(
        columns=["profile", "segmenter", "snr_hat", "edge_width"])

    res_c = h12.evaluate_confirmation(test, frozen_us)
    res_u = h12.evaluate_unseen(unseen, frozen_us)
    res_s = h12.evaluate_shift(shift, frozen_us, "us_compound")
    res_a = h12.evaluate_baseline(test, frozen_v04)
    res_b = h12.evaluate_modality(old, test, frozen_us, frozen_v04)
    res_h = h12.evaluate_benefit(test, frozen_us, frozen_v04)
    silent = h9.silent_failures(test, frozen_us)

    for name, rows in (("strata_test", res_c["strata"]), ("strata_unseen", res_u["strata"]),
                       ("strata_shift", res_s["strata"]), ("baseline_v04_on_us", res_a["strata"]),
                       ("modality_checks", res_b["checks"]), ("benefit", res_h["strata"])):
        pd.DataFrame(rows).round(4).to_csv(OUT / f"h12_{name}.csv", index=False)
    pd.DataFrame(res_u["by_shape"]).round(4).to_csv(OUT / "h12_unseen_by_shape_exploratory.csv",
                                                     index=False)
    silent.round(4).to_csv(OUT / "h12_silent_by_level_exploratory.csv", index=False)
    verdicts = {
        "selected": frozen_us["selected"], "features": frozen_us["features"],
        "h12a": res_a["h12a"], "in_domain_v04_guard_by_segmenter": res_a["in_domain_by_segmenter"],
        "h12b": res_b["h12b"],
        "h12c": res_c["h12c"], "h12d": res_c["h12d"], "retained_min": res_c["retained_min"],
        "h12e": res_u["h12e"], "h12f": res_s["h12f"], "h12g": res_s["h12g"],
        "h12h": res_h["h12h"],
        "silent_failure_overall": {
            "n_failures": int(silent["n_failures"].sum()),
            "green": float(np.average(silent["green"], weights=silent["n_failures"]))
            if len(silent) and silent["n_failures"].sum() else None,
            "red": float(np.average(silent["red"], weights=silent["n_failures"]))
            if len(silent) and silent["n_failures"].sum() else None},
        "h9_test_available": bool(old_path.exists())}
    (OUT / "h12_verdicts.json").write_text(json.dumps(clean(verdicts), indent=2))
    print(json.dumps(clean(verdicts), indent=2))


if __name__ == "__main__":
    main()
