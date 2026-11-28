"""Ejecuta el barrido de H2 (banco de pruebas 4D) y la demostración de acople H1->4D."""
import argparse
import datetime as dt
import itertools
import json
import platform
import subprocess
import time
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd

from geovida.analysis import add_predictors  # noqa: F401  (comprueba entorno)
from geovida.traj4d import FEATURES, K_STAGES, evaluate_cell, measurement_bias_function

BASE_SEED = 20261109
SIGMAS, NS, MS = (0.0, 0.1, 0.25, 0.5), (1, 3, 5, 10, 20), (0.0, 0.02, 0.05)


def cells():
    for fi, (feat, si, n, mi) in enumerate(itertools.product(
            FEATURES, range(len(SIGMAS)), NS, range(len(MS)))):
        sigma, m = SIGMAS[si], MS[mi]
        yield feat, sigma, n, m, "stage_mean", 1.0
        yield feat, sigma, n, m, "spline", 1.0
        for ratio in ((1.0,) if sigma == 0 else (0.5, 1.0, 2.0)):
            yield feat, sigma, n, m, "spline_corrected", ratio


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--boot", type=int, default=200)
    ap.add_argument("--h1raw", default="results/raw/h1_sweep.csv.gz")
    ap.add_argument("--outdir", default="results/summary")
    a = ap.parse_args()
    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    rows = []
    for i, (feat, sigma, n, m, est, ratio) in enumerate(cells()):
        seed = int(np.random.SeedSequence([BASE_SEED, i]).generate_state(1)[0])
        r = evaluate_cell(feat, n, sigma, m, est, sigma_assumed_ratio=ratio,
                          n_reps=a.reps, n_boot=a.boot, seed=seed)
        row = {"feature": feat, "sigma_s": sigma, "n": n, "meas": m, "estimator": est,
               "sigma_ratio": ratio, "max_abs_bias": r["max_abs_bias"],
               "int_abs_bias": r["int_abs_bias"], "irmse": r["irmse"],
               "bias2_share": r["bias2_share"], "mean_coverage": r["mean_coverage"]}
        for k in range(K_STAGES):
            row[f"bias_s{k}"], row[f"cov_s{k}"] = r["rel_bias"][k], r["coverage"][k]
        rows.append(row)
    cells_df = pd.DataFrame(rows)
    cells_df.to_csv(out / "h2_cells.csv", index=False)

    coupling = {}
    if Path(a.h1raw).exists():
        h1 = pd.read_csv(a.h1raw)
        k = np.arange(K_STAGES)
        t_over_h = 2.0 * np.exp(0.5 * k / 3.0)
        v_true = FEATURES["growth"](k.astype(float))
        for seg, prof in (("global", "ideal"), ("otsu", "realistic"), ("smoothed_otsu", "realistic")):
            fn = measurement_bias_function(h1, "ellipsoid", seg, prof, 1.0)
            bias = np.array([fn(t) for t in t_over_h])
            v_meas = v_true * (1 + bias)
            slope = float(np.polyfit(k, np.log(v_meas), 1)[0])
            coupling[f"{seg}/{prof}"] = {
                "t_over_h_by_stage": t_over_h.round(3).tolist(),
                "volume_bias_by_stage": bias.round(4).tolist(),
                "apparent_growth_rate": slope, "true_growth_rate": 0.5,
                "relative_distortion": slope / 0.5 - 1.0}
    (out / "h2_coupling.json").write_text(json.dumps(coupling, indent=2))

    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    manifest = {"started_utc": dt.datetime.fromtimestamp(t0, dt.timezone.utc).isoformat(),
                "elapsed_s": round(time.time() - t0, 1), "git_commit": commit,
                "cells": len(cells_df), "reps": a.reps, "boot": a.boot, "base_seed": BASE_SEED,
                "python": platform.python_version(),
                "packages": {p: version(p) for p in ("numpy", "scipy", "pandas")}}
    (out / "h2_run_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
