"""H23: red de dos etapas de H19 y señales de H20 en ventrículos, en este orden fijo (docs/h23/PREREGISTRO_H23.md §6).

    python scripts/run_h23.py g0               # G0-escala: solo etiquetas de los casos de ajuste, antes de entrenar
    python scripts/run_h23.py train-coarse     # etapa 1 con los 142 casos de ajuste
    python scripts/run_h23.py train-fine       # etapa 2 con los casos de ajuste
    python scripts/run_h23.py g0-signals       # G0-señales en 5 casos de ajuste
    python scripts/run_h23.py calibrate        # 34 casos de calibración; puertas S y C; congela si pasan
    python scripts/run_h23.py test --sha <SHA-256 del congelado anotado en el preregistro>

Nada lee un volumen de prueba salvo ``test``, que se niega a correr sin el SHA-256 anotado y sin que G0 y las redes
coincidan. Redes y medidas en ``results/h23`` (fuera de git).
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

from geovida import h18, h19, h20, h23
from geovida.provenance import git_state

OUT = Path("results/h23")
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


def roles(manifest) -> pd.DataFrame:
    train, _ = h23.cases(manifest, "train")
    return h19.fit_calibration_split(train)


def _fit(a):
    df = roles(a.manifest)
    return df[df.role == "fit"].reset_index(drop=True)


def _log(name):
    path = OUT / f"{name}.log"
    path.parent.mkdir(parents=True, exist_ok=True)

    def log(ep, loss):
        with path.open("a", encoding="utf-8") as f:
            f.write(f"{ep}\t{loss:.5f}\n")
        if ep % 10 == 0:
            print(f"  {name} época {ep}: pérdida {loss:.4f}", flush=True)
    return log


def cmd_g0(a):
    fit = _fit(a)
    counts, frac = [], []
    for _, c in fit.iterrows():
        _, _, ref = run_h18._load(a.root, c)
        counts.append(h23.coarse_voxels(ref))
        frac.append(h23.largest_fraction(ref))
    out = {**h23.g0_scale(counts), "coarse_voxels": counts,
           "largest_component_fraction_median": float(np.median(frac)),
           "largest_component_fraction_p10": float(np.percentile(frac, 10)),
           "manifest_sha256": _sha(a.manifest), "provenance": git_state()}
    _write("g0_scale.json", out)
    print(json.dumps({k: out[k] for k in ("n", "fraction_ok", "passed", "largest_component_fraction_median")}))


def cmd_train_coarse(a):
    _require("g0_scale.json")
    samples = []
    for _, c in _fit(a).iterrows():
        image, _, ref = run_h18._load(a.root, c)
        samples.append(h19.coarse_sample(image, ref))
    net = h19.train(samples, h19.EPOCHS["coarse"], seed=h19.SEED, log=_log("coarse"))
    h19.save(net, OUT / "coarse.pt")
    print("etapa 1 guardada")


def cmd_train_fine(a):
    _require("g0_scale.json")
    coarse = h19.load(OUT / "coarse.pt")
    samples = []
    for _, c in _fit(a).iterrows():
        image, _, ref = run_h18._load(a.root, c)
        pc = h19.upsample_prob(h19.predict(coarse, h19.coarse_sample(image)[0]), h19.COARSE, image.shape)
        s = h19.fine_sample(image, pc, ref)
        if s is not None:
            samples.append((s[0], s[1]))
    net = h19.train(samples, h19.EPOCHS["fine"], seed=h19.SEED + 1, in_ch=2, log=_log("fine"))
    h19.save(net, OUT / "fine.pt")
    print(f"etapa 2 guardada ({len(samples)} cajas de {len(_fit(a))})")


def _nets():
    return h19.load(OUT / "coarse.pt"), h19.load(OUT / "fine.pt", in_ch=2), \
        {n: _sha(OUT / f"{n}.pt") for n in ("coarse", "fine")}


def measure(coarse, fine, image, spacing, ref, case) -> dict:
    """Medida de ``h19.segment_full`` y señales de H20 sobre la misma imagen."""
    t0 = time.time()
    mask, prob = h19.segment_full(coarse, fine, image)
    v, vr = float(mask.sum()), float(ref.sum())
    vols = h20.flip_volumes(coarse, fine, image)
    s = h20.signals(vols, h20.coarse_volume(coarse, image))
    row = {"image": case["image"], "embryo_id": case["embryo_id"], "volumes": vols, **s,
           "rel_error_volume": (v - vr) / vr, "dice": 2 * float(np.logical_and(mask, ref).sum()) / (v + vr),
           "identity_matches": bool(v == s["v_identity"]), "seconds": round(time.time() - t0, 1),
           **h18.observables(image, spacing, mask)}          # NaN con máscara vacía: fuera de dominio, luz amarilla
    return row


def _measure_all(a, cases, path, coarse, fine):
    done = {r["image"] for r in run_h18._done(path)}
    for _, c in cases[~cases["image"].isin(done)].iterrows():
        image, sp, ref = run_h18._load(a.root, c)
        run_h18._append(path, [measure(coarse, fine, image, sp, ref, c)])
        print(f"  {c['image']}", flush=True)
    rows = pd.DataFrame(run_h18._done(path))
    return rows[rows["image"].isin(cases["image"])].reset_index(drop=True)


def cmd_g0_signals(a):
    _require("g0_scale.json")
    coarse, fine, nets = _nets()
    fit = _fit(a)
    pick = fit.iloc[np.sort(np.random.default_rng(h23.SEED_G0).choice(len(fit), h20.N_G0, replace=False))]
    rows = []
    for _, c in pick.iterrows():
        image, sp, ref = run_h18._load(a.root, c)
        r = measure(coarse, fine, image, sp, ref, c)
        rows.append({**r, "identity_matches_h19": r["identity_matches"]})
        print(f"  {c['image']}: {r['seconds']} s", flush=True)
    _write("g0_signals.json", {**h20.g0(rows), "nets_sha256": nets, "provenance": git_state()})
    print(json.dumps({"passed": h20.g0(rows)["passed"], "seconds": [r["seconds"] for r in rows]}))


def cmd_calibrate(a):
    _require("g0_scale.json")
    _require("g0_signals.json")
    coarse, fine, nets = _nets()
    df = roles(a.manifest)
    cal = _measure_all(a, df[df.role == "cal"], OUT / "cal_rows.jsonl", coarse, fine)
    if not cal["identity_matches"].all():
        raise RuntimeError("la pasada identidad no reproduce segment_full: se para y se busca la causa")
    s = h23.gate_s(cal)
    lit = h20.out_of_fold(cal)
    c = h20.gate_c(lit)
    result = {"gate_s": s, "gate_c": c, "n_cal": int(len(cal)), "dice_median_cal": float(cal["dice"].median()),
              "nets_sha256": nets, "provenance": git_state()}
    if s["passed"] and c["passed"]:
        payload = {"study": "H23", "nets_sha256": nets, "thresholds": h20.THRESHOLDS,
                   "envelope": h18.fit_envelope(cal), "gate_s": s, "gate_c": c}
        path = OUT / "h23_frozen.json"
        path.write_bytes((json.dumps(payload, indent=1, sort_keys=True, default=float) + "\n").encode("utf-8"))
        result["frozen_sha256"] = h18.sha256_file(path)
        print(f"puertas S y C superadas; congelado SHA-256 {result['frozen_sha256']}. Anotarlo ANTES de `test`.")
    else:
        print("puerta S o C NO superada: la prueba no se abre.")
    lit.drop(columns=["volumes"]).to_csv(OUT / "cal_lights.csv", index=False)
    _write("calibrate.json", result)
    print(json.dumps({"gate_s": s, "gate_c": c}, default=float))


def cmd_test(a):
    frozen = h18.check_frozen(OUT / "h23_frozen.json", a.sha)
    coarse, fine, nets = _nets()
    if nets != frozen["nets_sha256"] or frozen["thresholds"] != json.loads(json.dumps(h20.THRESHOLDS)):
        raise PermissionError("las redes o los umbrales no son los congelados")
    test, _ = h23.cases(a.manifest, "test")
    rows = _measure_all(a, test, OUT / "test_rows.jsonl", coarse, fine)
    if not rows["identity_matches"].all():
        raise RuntimeError("la pasada identidad no reproduce segment_full en algún caso de prueba")
    lit = h20.lights(rows, frozen["envelope"])
    out = {**h23.evaluate_test(lit), "frozen_sha256": a.sha, "provenance": git_state()}
    lit.drop(columns=["volumes"]).to_csv(OUT / "test_cases.csv", index=False)
    _write("test_verdicts.json", out)
    print(json.dumps({k: out[k] for k in ("h23a", "h23b", "h23c", "h23d")}, default=float))


def main(argv=None):
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["g0", "train-coarse", "train-fine", "g0-signals", "calibrate", "test"])
    ap.add_argument("--manifest", default="results/h11/manifiesto_qiu2021.csv")
    ap.add_argument("--root", default="data/external/ieee_qiu2021/nii")
    ap.add_argument("--sha", default="")
    a = ap.parse_args(argv)
    {"g0": cmd_g0, "train-coarse": cmd_train_coarse, "train-fine": cmd_train_fine, "g0-signals": cmd_g0_signals,
     "calibrate": cmd_calibrate, "test": cmd_test}[a.cmd](a)


if __name__ == "__main__":
    main()
