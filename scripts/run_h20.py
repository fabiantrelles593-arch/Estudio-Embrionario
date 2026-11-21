"""H20: señales de fiabilidad de la red de H19 y regla fija, en este orden (docs/h20/PREREGISTRO_H20.md §4).

    python scripts/run_h20.py g0                    # factibilidad en 5 casos de ajuste (la red ya los vio)
    python scripts/run_h20.py calibrate             # señales en los 27 de calibración; puerta C; congela si pasa
    python scripts/run_h20.py test --sha <SHA-256 del congelado anotado en el preregistro>

Usa las redes de H19 tal cual (``results/h19/coarse.pt`` y ``fine.pt``; se comprueba su SHA-256 contra
``results/h19/calibrate.json``). Nada lee un volumen de prueba salvo ``test``, que se niega a correr sin el SHA-256
anotado. Resultados en ``results/h20`` (fuera de git).
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

from geovida import h18, h19, h20
from geovida.provenance import git_state

H19 = Path("results/h19")
OUT = Path("results/h20")
_spec = importlib.util.spec_from_file_location("run_h18", Path(__file__).with_name("run_h18.py"))
run_h18 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_h18)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _nets():
    """Las redes de H19, solo si son las que H19 calibró."""
    expected = json.loads((H19 / "calibrate.json").read_text(encoding="utf-8"))["nets_sha256"]
    for n, s in expected.items():
        if _sha(H19 / f"{n}.pt") != s:
            raise PermissionError(f"la red {n} no es la que calibró H19")
    return h19.load(H19 / "coarse.pt"), h19.load(H19 / "fine.pt", in_ch=2), expected


def _roles(manifest):
    train, _ = run_h18._cases(manifest, "train")
    return h19.fit_calibration_split(train)


def _signal_row(coarse, fine, image, ref, case) -> dict:
    t0 = time.time()
    vols = h20.flip_volumes(coarse, fine, image)
    s = h20.signals(vols, h20.coarse_volume(coarse, image))
    vr = float(ref.sum())
    return {"image": case["image"], "embryo_id": case["embryo_id"], "volumes": vols, **s,
            "rel_error_identity": (s["v_identity"] - vr) / vr, "seconds": round(time.time() - t0, 1)}


def _signals(a, cases, path, coarse, fine):
    done = {r["image"] for r in run_h18._done(path)}
    for _, c in cases[~cases["image"].isin(done)].iterrows():
        image, _, ref = run_h18._load(a.root, c)
        run_h18._append(path, [_signal_row(coarse, fine, image, ref, c)])
        print(f"  {c['image']}", flush=True)
    rows = pd.DataFrame(run_h18._done(path))
    return rows[rows["image"].isin(cases["image"])]


def cmd_g0(a):
    coarse, fine, _ = _nets()
    fit = _roles(a.manifest)
    fit = fit[fit.role == "fit"].reset_index(drop=True)
    pick = fit.iloc[np.sort(np.random.default_rng(h20.SEED_G0).choice(len(fit), h20.N_G0, replace=False))]
    rows = []
    for _, c in pick.iterrows():
        image, _, ref = run_h18._load(a.root, c)
        r = _signal_row(coarse, fine, image, ref, c)
        mask, _ = h19.segment_full(coarse, fine, image)              # la medida de H19, tal cual
        r["identity_matches_h19"] = bool(float(mask.sum()) == r["v_identity"])
        rows.append(r)
        print(f"  {c['image']}: {r['seconds']} s", flush=True)
    out = h20.g0(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "g0.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({"passed": out["passed"], "seconds": [r["seconds"] for r in rows]}))


def cmd_calibrate(a):
    coarse, fine, nets = _nets()
    df = _roles(a.manifest)
    sig = _signals(a, df[df.role == "cal"], OUT / "cal_signals.jsonl", coarse, fine)
    h19rows = pd.DataFrame(run_h18._done(H19 / "cal_rows.jsonl"))
    cal = h19rows.merge(sig.drop(columns=["embryo_id"]), on="image", validate="one_to_one")
    same = np.allclose(cal["rel_error_identity"], cal["rel_error_volume"], rtol=0, atol=1e-12)
    if not same or len(cal) != len(h19rows):
        raise RuntimeError("la pasada identidad no reproduce la medida de H19: se para y se busca la causa")
    lit = h20.out_of_fold(cal)
    g = h20.gate_c(lit)
    result = {"gate_c": g, "n_cal": int(len(cal)), "nets_sha256": nets, "provenance": git_state()}
    if g["passed"]:
        payload = {"study": "H20", "nets_sha256": nets, "thresholds": h20.THRESHOLDS,
                   "envelope": h18.fit_envelope(cal), "gate_c": g}
        path = OUT / "h20_frozen.json"
        path.write_bytes((json.dumps(payload, indent=1, sort_keys=True, default=float) + "\n").encode("utf-8"))
        result["frozen_sha256"] = h18.sha256_file(path)
        print(f"puerta C superada; congelado SHA-256 {result['frozen_sha256']}. Anotarlo en el preregistro ANTES de `test`.")
    else:
        print("puerta C NO superada: la prueba no se abre.")
    lit.drop(columns=["volumes"]).to_csv(OUT / "cal_lights.csv", index=False)
    (OUT / "calibrate.json").write_text(json.dumps(result, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({"gate_c": g}, default=float))


def cmd_test(a):
    frozen = h18.check_frozen(OUT / "h20_frozen.json", a.sha)
    coarse, fine, nets = _nets()
    if nets != frozen["nets_sha256"] or frozen["thresholds"] != json.loads(json.dumps(h20.THRESHOLDS)):
        raise PermissionError("las redes o los umbrales no son los congelados")
    test, _ = run_h18._cases(a.manifest, "test")
    path = OUT / "test_rows.jsonl"
    done = {r["image"] for r in run_h18._done(path)}
    for _, c in test[~test["image"].isin(done)].iterrows():
        image, sp, ref = run_h18._load(a.root, c)
        mask, prob = h19.segment_full(coarse, fine, image)
        v, vr = float(mask.sum()), float(ref.sum())
        r = _signal_row(coarse, fine, image, ref, c)
        run_h18._append(path, [{**r, "rel_error_volume": (v - vr) / vr,
                                "dice": 2 * float(np.logical_and(mask, ref).sum()) / (v + vr),
                                "identity_matches_h19": bool(v == r["v_identity"]), **h18.observables(image, sp, mask)}])
        print(f"  {c['image']}", flush=True)
    rows = pd.DataFrame(run_h18._done(path))
    rows = rows[rows["image"].isin(test["image"])]
    if not rows["identity_matches_h19"].all():
        raise RuntimeError("la pasada identidad no reproduce la medida de H19 en algún caso de prueba")
    lit = h20.lights(rows, frozen["envelope"])
    out = {**h20.evaluate_test(lit), "frozen_sha256": a.sha, "provenance": git_state()}
    lit.drop(columns=["volumes"]).to_csv(OUT / "test_cases.csv", index=False)
    (OUT / "test_verdicts.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("h20a", "h20b", "h20c", "h20d")}, default=float))


def main(argv=None):
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["g0", "calibrate", "test"])
    ap.add_argument("--manifest", default="results/h11/manifiesto_qiu2021.csv")
    ap.add_argument("--root", default="data/external/ieee_qiu2021/nii")
    ap.add_argument("--sha", default="")
    a = ap.parse_args(argv)
    {"g0": cmd_g0, "calibrate": cmd_calibrate, "test": cmd_test}[a.cmd](a)


if __name__ == "__main__":
    main()
