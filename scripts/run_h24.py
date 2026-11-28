"""H24: tolerancia en vóxeles de borde, en este orden fijo (docs/h24/PREREGISTRO_H24.md §6).

    python scripts/run_h24.py check            # huellas SHA-256 de las redes de H23 (§4)
    python scripts/run_h24.py g0               # 5 casos de ajuste (semilla 20261126)
    python scripts/run_h24.py calibrate        # 34 casos de calibración; puertas S′ y C′; congela si pasan
    python scripts/run_h24.py test --sha <SHA-256 del congelado anotado en el preregistro>
    python scripts/run_h24.py explore-body     # H24f, exploratoria: cuerpo, prueba de H20 ya abierta; tras `test`

No se entrena nada: las redes son las de H23 (``results/h23``), con la medida de la desviación D-1 (todas las piezas).
Nada lee un volumen de prueba de ventrículo salvo ``test``. Salidas en ``results/h24`` (fuera de git).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from geovida import h18, h19, h20, h23, h24
from geovida.provenance import git_state

OUT = Path("results/h24")
H23 = Path("results/h23")
H19 = Path("results/h19")
H20 = Path("results/h20")
_spec = importlib.util.spec_from_file_location("run_h18", Path(__file__).with_name("run_h18.py"))
run_h18 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_h18)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=1, default=float) + "\n", encoding="utf-8")


def _require(name):
    p = OUT / name
    if not p.exists() or not json.loads(p.read_text(encoding="utf-8")).get("passed"):
        raise SystemExit(f"{name} no superada o no existe: el preregistro no permite seguir")


def _check_nets() -> dict:
    found = {n: _sha(H23 / f"{n}.pt") for n in ("coarse", "fine")}
    if found != h24.NETS_SHA256:
        raise PermissionError(f"las redes de H23 no son las del preregistro: {found}")
    return found


def _nets():
    nets = _check_nets()
    return h19.load(H23 / "coarse.pt"), h19.load(H23 / "fine.pt", in_ch=2), nets


def roles(manifest) -> pd.DataFrame:
    train, _ = h23.cases(manifest, "train")
    return h19.fit_calibration_split(train)


def measure(coarse, fine, image, spacing, ref, case, segment=h23.segment_all, coarse_vol=h23.coarse_volume_all) -> dict:
    """Medida, error en vóxeles de borde y señales normalizadas sobre la misma imagen."""
    t0 = time.time()
    mask, _ = segment(coarse, fine, image)
    v, vr = float(mask.sum()), float(ref.sum())
    vols = h20.flip_volumes(coarse, fine, image, segment=segment)
    s = h24.signals(vols, coarse_vol(coarse, image), h24.area_voxels(mask))
    a_r = h24.area_voxels(ref)
    return {"image": case["image"], "embryo_id": case["embryo_id"], "volumes": vols, **s,
            "v_ref": vr, "area_ref": a_r, "e_b": h24.boundary_error(v, vr, a_r),
            "rel_error_volume": (v - vr) / vr, "dice": 2 * float(np.logical_and(mask, ref).sum()) / (v + vr),
            "identity_matches": bool(v == s["v_identity"]), "seconds": round(time.time() - t0, 1),
            **h18.observables(image, spacing, mask)}


def _measure_all(a, cases, path, coarse, fine, **kw):
    done = {r["image"] for r in run_h18._done(path)}
    for _, c in cases[~cases["image"].isin(done)].iterrows():
        image, sp, ref = run_h18._load(a.root, c)
        run_h18._append(path, [measure(coarse, fine, image, sp, ref, c, **kw)])
        print(f"  {c['image']}", flush=True)
    rows = pd.DataFrame(run_h18._done(path))
    return rows[rows["image"].isin(cases["image"])].reset_index(drop=True)


def cmd_check(a):
    nets = _check_nets()
    _write("check.json", {"passed": True, "nets_sha256": nets, "provenance": git_state()})
    print("redes de H23 verificadas")


def cmd_g0(a):
    _require("check.json")
    coarse, fine, nets = _nets()
    df = roles(a.manifest)
    fit = df[df.role == "fit"].reset_index(drop=True)
    pick = fit.iloc[np.sort(np.random.default_rng(h24.SEED_G0).choice(len(fit), h24.N_G0, replace=False))]
    rows = []
    for _, c in pick.iterrows():
        image, sp, ref = run_h18._load(a.root, c)
        r = measure(coarse, fine, image, sp, ref, c)
        rows.append(r)
        print(f"  {c['image']}: {r['seconds']} s", flush=True)
    out = h24.g0(rows)
    _write("g0.json", {**out, "nets_sha256": nets, "provenance": git_state()})
    print(json.dumps({"passed": out["passed"], "seconds": [r["seconds"] for r in rows]}))


def cmd_calibrate(a):
    _require("check.json")
    _require("g0.json")
    coarse, fine, nets = _nets()
    df = roles(a.manifest)
    cal = _measure_all(a, df[df.role == "cal"], OUT / "cal_rows.jsonl", coarse, fine)
    if not cal["identity_matches"].all():
        raise RuntimeError("la pasada identidad no reproduce segment_all: se para y se busca la causa")
    # Descriptivo: la medida coincide con la de H23 en los mismos casos (misma red, mismo código).
    prev = pd.DataFrame(run_h18._done(H23 / "cal_rows.jsonl")).set_index("image")["v_identity"]
    same_h23 = float((cal.set_index("image")["v_identity"] == prev.reindex(cal["image"])).mean())
    s = h24.gate_s(cal)
    lit = h24.out_of_fold(cal)
    c = h24.gate_c(lit)
    result = {"gate_s": s, "gate_c": c, "n_cal": int(len(cal)), "e_b_median_cal": float(cal["e_b"].median()),
              "identity_equals_h23_fraction": same_h23, "nets_sha256": nets, "provenance": git_state()}
    if s["passed"] and c["passed"]:
        payload = {"study": "H24", "nets_sha256": nets, "thresholds": h24.THRESHOLDS,
                   "envelope": h18.fit_envelope(cal), "gate_s": s, "gate_c": c}
        path = OUT / "h24_frozen.json"
        path.write_bytes((json.dumps(payload, indent=1, sort_keys=True, default=float) + "\n").encode("utf-8"))
        result["frozen_sha256"] = h18.sha256_file(path)
        print(f"puertas S′ y C′ superadas; congelado SHA-256 {result['frozen_sha256']}. Anotarlo ANTES de `test`.")
    else:
        print("puerta S′ o C′ NO superada: la prueba no se abre.")
    lit.drop(columns=["volumes"]).to_csv(OUT / "cal_lights.csv", index=False)
    _write("calibrate.json", result)
    print(json.dumps({"gate_s": s, "gate_c": c, "identity_equals_h23_fraction": same_h23}, default=float))


def cmd_test(a):
    frozen = h18.check_frozen(OUT / "h24_frozen.json", a.sha)
    coarse, fine, nets = _nets()
    if nets != frozen["nets_sha256"] or frozen["thresholds"] != json.loads(json.dumps(h24.THRESHOLDS)):
        raise PermissionError("las redes o los umbrales no son los congelados")
    test, _ = h23.cases(a.manifest, "test")
    rows = _measure_all(a, test, OUT / "test_rows.jsonl", coarse, fine)
    if not rows["identity_matches"].all():
        raise RuntimeError("la pasada identidad no reproduce segment_all en algún caso de prueba")
    lit = h24.lights(rows, frozen["envelope"])
    out = {**h24.evaluate_test(lit), "frozen_sha256": a.sha, "provenance": git_state()}
    lit.drop(columns=["volumes"]).to_csv(OUT / "test_cases.csv", index=False)
    _write("test_verdicts.json", out)
    print(json.dumps({k: out[k] for k in ("h24a", "h24b", "h24c", "h24d", "h24g")}, default=float))


def cmd_explore_body(a):
    """H24f: la regla de H24 en el cuerpo, con las redes de H19 y la medida de H20 tal cual (pieza mayor) y la
    envolvente congelada de H20. Esa prueba ya se abrió en H20: es descriptivo y no decide nada."""
    if not (OUT / "test_verdicts.json").exists():
        raise SystemExit("H24f se corre solo después de `test` (§7)")
    f20 = json.loads((H20 / "h20_frozen.json").read_text(encoding="utf-8"))
    nets = {n: _sha(H19 / f"{n}.pt") for n in ("coarse", "fine")}
    if nets != f20["nets_sha256"]:
        raise PermissionError("las redes de H19 no son las congeladas en H20")
    coarse, fine = h19.load(H19 / "coarse.pt"), h19.load(H19 / "fine.pt", in_ch=2)
    m = pd.read_csv(a.manifest)
    df, _ = h18.split_cases(m[m["structure"] == "body"])
    test = df[df["split"] == "test"].reset_index(drop=True)
    rows = _measure_all(a, test, OUT / "body_rows.jsonl", coarse, fine,
                        segment=h19.segment_full, coarse_vol=h20.coarse_volume)
    lit = h24.lights(rows, f20["envelope"])
    out = {"exploratory": True, **h24.evaluate_test(lit), "nets_sha256": nets, "provenance": git_state()}
    lit.drop(columns=["volumes"]).to_csv(OUT / "body_cases.csv", index=False)
    _write("explore_body.json", out)
    print(json.dumps({k: out[k] for k in ("h24a", "h24b", "h24c", "h24d", "h24g")}, default=float))


def main(argv=None):
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["check", "g0", "calibrate", "test", "explore-body"])
    ap.add_argument("--manifest", default="results/h11/manifiesto_qiu2021.csv")
    ap.add_argument("--root", default="data/external/ieee_qiu2021/nii")
    ap.add_argument("--sha", default="")
    a = ap.parse_args(argv)
    {"check": cmd_check, "g0": cmd_g0, "calibrate": cmd_calibrate, "test": cmd_test,
     "explore-body": cmd_explore_body}[a.cmd](a)


if __name__ == "__main__":
    main()
