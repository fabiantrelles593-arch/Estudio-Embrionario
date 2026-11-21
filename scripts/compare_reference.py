"""Comparación externa del motor 3D frente a estimadores de referencia independientes (tarea P1).

    python scripts/compare_reference.py --out results/summary/reference_comparison

Criterios fijados ANTES de ejecutar (16–17 nov 2026):

* C1 (comprobación de errores, binaria): χ de ``topology.betti_numbers`` = χ de ``reference.euler_cubical``
  en **todas** las máscaras, con conectividad 6 y 26. Una sola discrepancia es un error que hay que explicar.
* C2 (descriptivo): error relativo de área frente a la verdad analítica de ``area_sdf`` (principal de geovida),
  ``area_mc``, ``area_faces`` y ``crofton`` (referencia), en fantomas con área conocida, a t/h = 4, 6, 8, 12 y 16
  y 3 rotaciones al azar (semilla 20261117). Expectativa [HIP]: a t/h ≥ 8, ``area_sdf`` y ``crofton`` quedan a
  ≤ 5 % de la verdad en las formas convexas. No hay criterio de superioridad.
* C3 (descriptivo, datos reales): en máscaras reales de Qiu et al. 2021 (cuerpo y ventrículos, volúmenes pequeños
  para no competir por memoria), diferencia relativa ``area_sdf`` frente a ``crofton`` y acuerdo de χ.
  Con datos reales no hay verdad: es acuerdo entre dos estimadores, no exactitud.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from geovida import reference as ref
from geovida.measure import measure_mask
from geovida.phantoms import make_phantom
from geovida.topology import betti_numbers

SEED = 20261117
SHAPES = ("ball", "ellipsoid", "capsule", "cylinder", "oblate", "shell", "torus", "dumbbell")
T_OVER_H = (4, 6, 8, 12, 16)
CONVEX = {"ball", "ellipsoid", "capsule", "cylinder", "oblate"}


def _rotation(rng: np.random.Generator) -> np.ndarray:
    q, r = np.linalg.qr(rng.normal(size=(3, 3)))
    q *= np.sign(np.diag(r))
    if np.linalg.det(q) < 0:
        q[:, 0] *= -1
    return q


def _row(mask, sp) -> dict:
    meas = measure_mask(mask, sp)
    out = {"volume": meas["volume"], "area_sdf": meas["area_sdf"], "area_mc": meas["area_mc"],
           "area_faces": meas["area_faces"], "crofton": ref.crofton_area(mask, sp)}
    for c in (6, 26):
        out[f"chi_geovida_{c}"] = betti_numbers(mask, c).chi
        out[f"chi_ref_{c}"] = ref.euler_cubical(mask, c)
    return out


def phantoms(n_rot: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    rows = []
    for shape in SHAPES:
        for toh in T_OVER_H:
            for k in range(n_rot):
                ph = make_phantom(shape, 1.0)
                h = ph.truth.t_min / toh
                mask, sp = ref.voxelize(ph, h, rotation=_rotation(rng))
                r = _row(mask, sp)
                r.update(shape=shape, t_over_h=toh, rot=k, true_area=ph.truth.surface_area,
                         true_volume=ph.truth.volume, true_chi=ph.truth.chi)
                rows.append(r)
                print(f"{shape} t/h={toh} rot={k}", flush=True)
    return pd.DataFrame(rows)


def real_masks(root: Path, manifest: Path, max_bytes: int, max_cases: int) -> pd.DataFrame:
    import nibabel as nib
    man = pd.read_csv(manifest)
    rows = []
    for _, r in man.iterrows():
        p = root / r["label"]
        if not p.exists() or p.stat().st_size > max_bytes:
            continue
        img = nib.load(str(p))
        lab = np.asarray(img.dataobj) == int(r["label_value"])
        if not lab.any():
            continue
        idx = np.argwhere(lab)
        lo, hi = idx.min(0), idx.max(0) + 1
        lab = lab[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
        sp = tuple(float(z) for z in img.header.get_zooms()[:3])
        row = _row(lab, sp)
        row.update(structure=r["structure"], embryo_id=r["embryo_id"], label=Path(r["label"]).name,
                   n_voxels=int(lab.sum()))
        rows.append(row)
        print(f"real {row['label']}", flush=True)
        if len(rows) >= max_cases:
            break
    return pd.DataFrame(rows)


def summarize(ph: pd.DataFrame, real: pd.DataFrame) -> dict:
    out = {"seed": SEED}
    chi_ok = lambda d: int(((d.chi_geovida_6 == d.chi_ref_6) & (d.chi_geovida_26 == d.chi_ref_26)).sum())
    out["C1"] = {"masks": int(len(ph) + len(real)), "agree": chi_ok(ph) + (chi_ok(real) if len(real) else 0)}
    out["C1"]["passed"] = out["C1"]["agree"] == out["C1"]["masks"]
    est = ("area_sdf", "area_mc", "area_faces", "crofton")
    for e in est:
        ph[f"err_{e}"] = ph[e] / ph.true_area - 1
    ph["err_volume"] = ph.volume / ph.true_volume - 1
    tab = ph.groupby(["shape", "t_over_h"])[[f"err_{e}" for e in est] + ["err_volume"]].median()
    out["C2_median_rel_error"] = {f"{s}|{t}": {k: float(v) for k, v in row.items()} for (s, t), row in tab.iterrows()}
    big = ph[(ph.t_over_h >= 8) & ph["shape"].isin(CONVEX)]
    out["C2_expectation"] = {e: float(big[f"err_{e}"].abs().max()) for e in ("area_sdf", "crofton")}
    out["C2_expectation"]["holds"] = all(v <= 0.05 for v in out["C2_expectation"].values())
    out["C2_by_toh"] = {str(t): {e: float(g[f"err_{e}"].abs().median()) for e in est}
                        for t, g in ph.groupby("t_over_h")}
    if len(real):
        real["diff_sdf_vs_crofton"] = real.area_sdf / real.crofton - 1
        out["C3"] = {s: {"n": int(len(g)), "median": float(g.diff_sdf_vs_crofton.median()),
                         "min": float(g.diff_sdf_vs_crofton.min()), "max": float(g.diff_sdf_vs_crofton.max())}
                     for s, g in real.groupby("structure")}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="results/summary/reference_comparison")
    ap.add_argument("--root", default="data/external/ieee_qiu2021/nii")
    ap.add_argument("--manifest", default="results/h11/manifiesto_qiu2021.csv")
    ap.add_argument("--max-bytes", type=int, default=20_000_000)
    ap.add_argument("--max-cases", type=int, default=20)
    a = ap.parse_args(argv)
    ph = phantoms()
    real = real_masks(Path(a.root), Path(a.manifest), a.max_bytes, a.max_cases) if Path(a.manifest).exists() else pd.DataFrame()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    ph.to_csv(f"{out}_phantoms.csv", index=False)
    if len(real):
        real.to_csv(f"{out}_real.csv", index=False)
    s = summarize(ph, real)
    Path(f"{out}.json").write_text(json.dumps(s, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: s[k] for k in s if k in ("C1", "C2_expectation", "C2_by_toh", "C3")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
