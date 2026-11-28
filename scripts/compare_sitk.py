"""Comparación del motor 3D con una herramienta externa establecida: SimpleITK (ITK), tarea P1.

    pip install "geovida[reference]"      # SimpleITK >= 2.3 (Apache 2.0)
    python scripts/compare_sitk.py --out results/summary/sitk_comparison

Mismas máscaras que ``scripts/compare_reference.py`` (fantomas con verdad analítica, semilla 20261117, y
máscaras reales pequeñas de Qiu et al. 2021). De SimpleITK se usan ``LabelShapeStatisticsImageFilter``
(``PhysicalSize`` = volumen, ``Perimeter`` = área de la frontera en 3D) y ``ConnectedComponentImageFilter``
(conectividad 6 por defecto, 26 con ``FullyConnected``).

Criterios fijados ANTES de ejecutar (17 nov 2026):

* S1 (comprobación de errores): volumen de geovida = ``PhysicalSize`` de ITK (diferencia relativa < 1e-9) en
  todas las máscaras.
* S2 (comprobación de errores): b0 de geovida = número de componentes de ITK, con conectividad 6 y 26, en todas
  las máscaras.
* S3 (descriptivo): error relativo del ``Perimeter`` de ITK frente a la verdad analítica, junto a ``area_sdf`` y
  Crofton (``reference.crofton_area``). Expectativa [HIP]: como ITK también estima el área por intersecciones
  (familia de Crofton), su mediana por t/h queda a ≤ 1 punto porcentual de la de ``reference.crofton_area``;
  si no, la reimplementación propia tiene un problema que hay que explicar.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

from geovida import reference as ref
from geovida.measure import measure_mask
from geovida.topology import betti_numbers

_spec = importlib.util.spec_from_file_location("compare_reference", Path(__file__).with_name("compare_reference.py"))
cr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cr)


def sitk_measures(mask: np.ndarray, spacing) -> dict:
    import SimpleITK as sitk
    img = sitk.GetImageFromArray(np.asarray(mask, dtype=np.uint8))
    img.SetSpacing(tuple(float(s) for s in spacing[::-1]))  # numpy (z, y, x) -> ITK (x, y, z)
    f = sitk.LabelShapeStatisticsImageFilter()
    f.ComputePerimeterOn()
    f.Execute(img)
    out = {"itk_volume": f.GetPhysicalSize(1) if f.HasLabel(1) else 0.0,
           "itk_area": f.GetPerimeter(1) if f.HasLabel(1) else 0.0}
    for full, conn in ((False, 6), (True, 26)):
        cc = sitk.ConnectedComponentImageFilter()
        cc.SetFullyConnected(full)
        cc.Execute(img)
        out[f"itk_b0_{conn}"] = int(cc.GetObjectCount())
    return out


def row(mask, sp) -> dict:
    meas = measure_mask(mask, sp)
    r = {"volume": meas["volume"], "area_sdf": meas["area_sdf"], "crofton": ref.crofton_area(mask, sp)}
    for c in (6, 26):
        r[f"b0_{c}"] = betti_numbers(mask, c).b0
    r.update(sitk_measures(mask, sp))
    return r


def phantoms(n_rot: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(cr.SEED)
    rows = []
    for shape in cr.SHAPES:
        for toh in cr.T_OVER_H:
            for k in range(n_rot):
                ph = cr.make_phantom(shape, 1.0)
                mask, sp = ref.voxelize(ph, ph.truth.t_min / toh, rotation=cr._rotation(rng))
                r = row(mask, sp)
                r.update(shape=shape, t_over_h=toh, rot=k, true_area=ph.truth.surface_area)
                rows.append(r)
                print(f"{shape} t/h={toh} rot={k}", flush=True)
    return pd.DataFrame(rows)


def real(root: Path, manifest: Path, max_bytes: int, max_cases: int) -> pd.DataFrame:
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
        x = row(lab, sp)
        x.update(structure=r["structure"], label=Path(r["label"]).name)
        rows.append(x)
        print(f"real {x['label']}", flush=True)
        if len(rows) >= max_cases:
            break
    return pd.DataFrame(rows)


def summarize(ph: pd.DataFrame, rl: pd.DataFrame) -> dict:
    both = pd.concat([ph, rl], ignore_index=True)
    vol_ok = (np.abs(both.itk_volume / both.volume - 1) < 1e-9)
    b0_ok = (both.itk_b0_6 == both.b0_6) & (both.itk_b0_26 == both.b0_26)
    out = {"seed": cr.SEED, "S1": {"masks": int(len(both)), "agree": int(vol_ok.sum())},
           "S2": {"masks": int(len(both)), "agree": int(b0_ok.sum())}}
    out["S1"]["passed"] = out["S1"]["agree"] == out["S1"]["masks"]
    out["S2"]["passed"] = out["S2"]["agree"] == out["S2"]["masks"]
    for e in ("itk_area", "area_sdf", "crofton"):
        ph[f"err_{e}"] = ph[e] / ph.true_area - 1
    by = {}
    for t, g in ph.groupby("t_over_h"):
        by[str(t)] = {e: float(g[f"err_{e}"].abs().median()) for e in ("itk_area", "area_sdf", "crofton")}
    out["S3_median_abs_rel_error_by_toh"] = by
    gap = max(abs(v["itk_area"] - v["crofton"]) for v in by.values())
    out["S3_expectation"] = {"max_gap_itk_vs_crofton_pp": 100 * gap, "holds": gap <= 0.01}
    if len(rl):
        rl["itk_vs_crofton"] = rl.itk_area / rl.crofton - 1
        rl["sdf_vs_itk"] = rl.area_sdf / rl.itk_area - 1
        out["S3_real"] = {k: {"median": float(rl[k].median()), "min": float(rl[k].min()), "max": float(rl[k].max())}
                          for k in ("itk_vs_crofton", "sdf_vs_itk")}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="results/summary/sitk_comparison")
    ap.add_argument("--root", default="data/external/ieee_qiu2021/nii")
    ap.add_argument("--manifest", default="results/h11/manifiesto_qiu2021.csv")
    ap.add_argument("--max-bytes", type=int, default=20_000_000)
    ap.add_argument("--max-cases", type=int, default=20)
    a = ap.parse_args(argv)
    import SimpleITK as sitk
    ph = phantoms()
    rl = real(Path(a.root), Path(a.manifest), a.max_bytes, a.max_cases) if Path(a.manifest).exists() else pd.DataFrame()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    ph.to_csv(f"{out}_phantoms.csv", index=False)
    if len(rl):
        rl.to_csv(f"{out}_real.csv", index=False)
    s = summarize(ph, rl)
    s["simpleitk_version"] = sitk.Version_VersionString()
    Path(f"{out}.json").write_text(json.dumps(s, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(s, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
