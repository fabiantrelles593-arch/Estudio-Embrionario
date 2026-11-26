"""H25: la luz de H24 con la guardia sin signo de contraste (docs/h25/PREREGISTRO_H25.md).

    python scripts/run_h25.py check                     # huellas SHA-256 de las redes de H23
    python scripts/run_h25.py g0                        # 5 casos de ajuste
    python scripts/run_h25.py calibrate                 # 34 casos de calibración; congela si pasan S′ y C′
    python scripts/run_h25.py test --sha <SHA-256 anotado en el §11 del preregistro>   # una sola vez

``calibrate`` nunca lee un caso de prueba. ``test`` se niega a correr si el congelado no tiene el SHA-256 dado o si las
redes o los umbrales no coinciden. Todo es reanudable: cada caso se guarda al terminarlo.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from geovida import h18, h20, h23, h24, h25
from geovida.provenance import git_state

OUT = Path("results/h25")
H24 = Path("results/h24")
_spec = importlib.util.spec_from_file_location("run_h24", Path(__file__).with_name("run_h24.py"))
run_h24 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_h24)
run_h18 = run_h24.run_h18


def _write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=1, default=float) + "\n", encoding="utf-8")


def _require(name):
    p = OUT / name
    if not p.exists() or not json.loads(p.read_text(encoding="utf-8")).get("passed"):
        raise SystemExit(f"{name} no superada o no existe: el preregistro no permite seguir")


def measure(coarse, fine, image, spacing, ref, case) -> dict:
    """La medida de H24 (señales, e_b) con los índices de la guardia nueva y de la antigua."""
    t0 = time.time()
    mask, _ = h23.segment_all(coarse, fine, image)
    v, vr = float(mask.sum()), float(ref.sum())
    vols = h20.flip_volumes(coarse, fine, image, segment=h23.segment_all)
    s = h24.signals(vols, h23.coarse_volume_all(coarse, image), h24.area_voxels(mask))
    a_r = h24.area_voxels(ref)
    return {"image": case["image"], "embryo_id": case["embryo_id"], "volumes": vols, **s,
            "v_ref": vr, "area_ref": a_r, "e_b": h24.boundary_error(v, vr, a_r),
            "rel_error_volume": (v - vr) / vr, "dice": 2 * float(np.logical_and(mask, ref).sum()) / (v + vr),
            "identity_matches": bool(v == s["v_identity"]), "seconds": round(time.time() - t0, 1),
            **h25.observables(image, spacing, mask)}


def _measure_all(a, cases, path, coarse, fine):
    done = {r["image"] for r in run_h18._done(path)}
    for _, c in cases[~cases["image"].isin(done)].iterrows():
        image, sp, ref = run_h18._load(a.root, c)
        run_h18._append(path, [measure(coarse, fine, image, sp, ref, c)])
        print(f"  {c['image']}", flush=True)
    rows = pd.DataFrame(run_h18._done(path))
    return rows[rows["image"].isin(cases["image"])].reset_index(drop=True)


def cmd_check(a):
    nets = run_h24._check_nets()
    _write("check.json", {"passed": True, "nets_sha256": nets, "provenance": git_state()})
    print("redes de H23 verificadas")


def cmd_g0(a):
    _require("check.json")
    coarse, fine, nets = run_h24._nets()
    df = run_h24.roles(a.manifest)
    fit = df[df.role == "fit"].reset_index(drop=True)
    rng = np.random.default_rng(h25.SEED_G0)
    pick = fit.iloc[np.sort(rng.choice(len(fit), h25.N_G0, replace=False))]
    rows = []
    for _, c in pick.iterrows():
        image, sp, ref = run_h18._load(a.root, c)
        r = measure(coarse, fine, image, sp, ref, c)
        rows.append(r)
        print(f"  {c['image']}: {r['seconds']} s; contraste {r['contrast']:.2f}", flush=True)
    extra = []
    if not any(h25.positive(r) for r in rows):
        # Ningún caso con C > 0: se siguen tomando casos de ajuste, en un orden fijo con la misma semilla, solo para
        # comprobar que la guardia nueva coincide con la antigua donde la antigua estaba definida.
        rest = [i for i in rng.permutation(len(fit)) if fit.iloc[i]["image"] not in set(pick["image"])]
        for i in rest:
            c = fit.iloc[i]
            image, sp, ref = run_h18._load(a.root, c)
            mask, _ = h23.segment_all(coarse, fine, image)
            r = {"image": c["image"], **h25.observables(image, sp, mask)}
            extra.append(r)
            print(f"  extra {c['image']}: contraste {r['contrast']:.2f}", flush=True)
            if h25.positive(r):
                break
    out = {**h25.g0(rows, extra), "extra": extra}
    _write("g0.json", {**out, "nets_sha256": nets, "provenance": git_state()})
    print(json.dumps({k: out[k] for k in ("passed", "guard_computable", "n_positive_contrast", "same_as_old")}))


def cmd_calibrate(a):
    _require("check.json")
    _require("g0.json")
    coarse, fine, nets = run_h24._nets()
    df = run_h24.roles(a.manifest)
    cal = _measure_all(a, df[df.role == "cal"], OUT / "cal_rows.jsonl", coarse, fine)
    if not cal["identity_matches"].all():
        raise RuntimeError("la pasada identidad no reproduce segment_all: se para y se busca la causa")
    prev = pd.DataFrame(run_h18._done(H24 / "cal_rows.jsonl")).set_index("image")
    same_h24 = float((cal.set_index("image")["v_identity"] == prev["v_identity"].reindex(cal["image"])).mean())
    s = h24.gate_s(cal)
    lit = h25.out_of_fold(cal)
    c = h24.gate_c(lit)
    result = {"gate_s": s, "gate_c": c, "n_cal": int(len(cal)),
              "guard_computable": int(np.isfinite(cal["snr_hat"]).sum()),
              "in_domain_out_of_fold": int(lit["in_domain"].sum()),
              "identity_equals_h24_fraction": same_h24, "nets_sha256": nets, "provenance": git_state()}
    if s["passed"] and c["passed"]:
        payload = {"study": "H25", "nets_sha256": nets, "thresholds": h25.THRESHOLDS,
                   "envelope": h18.fit_envelope(cal), "envelope_old_guard": h18.fit_envelope(h25.old_guard_view(cal)),
                   "gate_s": s, "gate_c": c}
        path = OUT / "h25_frozen.json"
        path.write_bytes((json.dumps(payload, indent=1, sort_keys=True, default=float) + "\n").encode("utf-8"))
        result["frozen_sha256"] = h18.sha256_file(path)
        print(f"puertas S′ y C′ superadas; congelado SHA-256 {result['frozen_sha256']}. Anotarlo ANTES de `test`.")
    else:
        print("puerta S′ o C′ NO superada: la prueba no se abre.")
    lit.drop(columns=["volumes"]).to_csv(OUT / "cal_lights.csv", index=False)
    _write("calibrate.json", result)
    print(json.dumps({k: result[k] for k in ("gate_s", "gate_c", "guard_computable", "in_domain_out_of_fold",
                                             "identity_equals_h24_fraction")}, default=float))


def cmd_test(a):
    frozen = h18.check_frozen(OUT / "h25_frozen.json", a.sha)
    coarse, fine, nets = run_h24._nets()
    if nets != frozen["nets_sha256"] or frozen["thresholds"] != json.loads(json.dumps(h25.THRESHOLDS)):
        raise PermissionError("las redes o los umbrales no son los congelados")
    test, _ = h23.cases(a.manifest, "test")
    rows = _measure_all(a, test, OUT / "test_rows.jsonl", coarse, fine)
    if not rows["identity_matches"].all():
        raise RuntimeError("la pasada identidad no reproduce segment_all en algún caso de prueba")
    lit = h24.lights(rows, frozen["envelope"])
    out = {**h25.evaluate_test(lit, frozen["envelope_old_guard"]), "frozen_sha256": a.sha, "provenance": git_state()}
    lit.drop(columns=["volumes"]).to_csv(OUT / "test_cases.csv", index=False)
    _write("test_verdicts.json", out)
    print(json.dumps({k: out[k] for k in ("h25a", "h25b", "h25c", "h25d", "h25e", "h25g", "h25h")}, default=float))


def main(argv=None):
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["check", "g0", "calibrate", "test"])
    ap.add_argument("--manifest", default="results/h11/manifiesto_qiu2021.csv")
    ap.add_argument("--root", default="data/external/ieee_qiu2021/nii")
    ap.add_argument("--sha", default="")
    a = ap.parse_args(argv)
    {"check": cmd_check, "g0": cmd_g0, "calibrate": cmd_calibrate, "test": cmd_test}[a.cmd](a)


if __name__ == "__main__":
    main()
