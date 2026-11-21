"""H19: red de dos etapas y certificado con ecografía real, en este orden fijo (docs/PREREGISTRO_H19.md §4).

    python scripts/run_h19.py split                 # ajuste / calibración dentro del entrenamiento de H18
    python scripts/run_h19.py train-coarse          # etapa 1 con los casos de ajuste
    python scripts/run_h19.py train-fine            # etapa 2 con los casos de ajuste
    python scripts/run_h19.py calibrate             # mide los casos de calibración; puertas S y C; congela si pasan
    python scripts/run_h19.py test --sha <SHA-256 del congelado anotado en el preregistro>

Nada de esto lee un volumen de prueba salvo ``test``, que se niega a correr sin el SHA-256 anotado. Las redes y las
medidas quedan en ``results/h19`` (fuera de git).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from geovida import h18, h19
from geovida.provenance import git_state

OUT = Path("results/h19")
_spec = importlib.util.spec_from_file_location("run_h18", Path(__file__).with_name("run_h18.py"))
run_h18 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_h18)


def _roles(manifest):
    train, rep = run_h18._cases(manifest, "train")
    return h19.fit_calibration_split(train), rep


def _log(name):
    path = OUT / f"{name}.log"
    path.parent.mkdir(parents=True, exist_ok=True)

    def log(ep, loss):
        with path.open("a", encoding="utf-8") as f:
            f.write(f"{ep}\t{loss:.5f}\n")
        if ep % 10 == 0:
            print(f"  {name} época {ep}: pérdida {loss:.4f}", flush=True)
    return log


def cmd_split(a):
    df, rep = _roles(a.manifest)
    OUT.mkdir(parents=True, exist_ok=True)
    out = {"fit_cases": int((df.role == "fit").sum()), "cal_cases": int((df.role == "cal").sum()),
           "fit_embryos": int(df.loc[df.role == "fit", "embryo_id"].nunique()),
           "cal_embryos": int(df.loc[df.role == "cal", "embryo_id"].nunique()),
           "cal_images": sorted(df.loc[df.role == "cal", "image"]), "seed": h19.SEED, "h18_split": rep}
    (OUT / "reparto.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print({k: v for k, v in out.items() if k not in ("cal_images", "h18_split")})


def _fit_cases(a):
    df, _ = _roles(a.manifest)
    return df[df.role == "fit"]


def cmd_train_coarse(a):
    samples = []
    for _, c in _fit_cases(a).iterrows():
        image, _, ref = run_h18._load(a.root, c)
        samples.append(h19.coarse_sample(image, ref))
    net = h19.train(samples, h19.EPOCHS["coarse"], seed=h19.SEED, log=_log("coarse"))
    h19.save(net, OUT / "coarse.pt")
    print("etapa 1 guardada")


def cmd_train_fine(a):
    coarse = h19.load(OUT / "coarse.pt")
    samples = []
    for _, c in _fit_cases(a).iterrows():
        image, _, ref = run_h18._load(a.root, c)
        pc = h19.upsample_prob(h19.predict(coarse, h19.coarse_sample(image)[0]), h19.COARSE, image.shape)
        s = h19.fine_sample(image, pc, ref)
        if s is not None:
            samples.append((s[0], s[1]))
    net = h19.train(samples, h19.EPOCHS["fine"], seed=h19.SEED + 1, in_ch=2, log=_log("fine"))
    h19.save(net, OUT / "fine.pt")
    print(f"etapa 2 guardada ({len(samples)} cajas)")


def _measure(a, cases, path):
    coarse, fine = h19.load(OUT / "coarse.pt"), h19.load(OUT / "fine.pt", in_ch=2)
    done = {r["image"] for r in run_h18._done(path)}
    for _, c in cases[~cases["image"].isin(done)].iterrows():
        image, sp, ref = run_h18._load(a.root, c)
        mask, prob = h19.segment_full(coarse, fine, image)
        v, vr = float(mask.sum()), float(ref.sum())
        run_h18._append(path, [{"image": c["image"], "embryo_id": c["embryo_id"], "rel_error_volume": (v - vr) / vr,
                                "dice": 2 * float(np.logical_and(mask, ref).sum()) / (v + vr),
                                "uncertain_band": h19.uncertain_band(prob, mask), **h18.observables(image, sp, mask)}])
        print(f"  {c['image']}", flush=True)
    rows = pd.DataFrame(run_h18._done(path))
    return rows[rows["image"].isin(cases["image"])]


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cmd_calibrate(a):
    df, _ = _roles(a.manifest)
    cal = _measure(a, df[df.role == "cal"], OUT / "cal_rows.jsonl")
    g = h19.gates(cal)
    result = {"gates": g, "n_cal": int(len(cal)), "dice_median_cal": float(cal["dice"].median()),
              "nets_sha256": {n: _sha(OUT / f"{n}.pt") for n in ("coarse", "fine")}, "provenance": git_state()}
    if g["passed"]:
        cert = h19.fit_certificate(cal)
        sha = h18.freeze(OUT / "h19_frozen.json", {"nets_sha256": result["nets_sha256"]}, cert,
                         {"study_variant": "H19", "features": list(h19.FEATURES), "gates": g})
        result["frozen_sha256"] = sha
        print(f"puertas superadas; congelado SHA-256 {sha}. Anotarlo en el preregistro ANTES de `test`.")
    else:
        print("puertas NO superadas: la prueba no se abre.")
    (OUT / "calibrate.json").write_text(json.dumps(result, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({"gates": g, "dice_median_cal": result["dice_median_cal"]}, default=float))


def cmd_test(a):
    frozen = h18.check_frozen(OUT / "h19_frozen.json", a.sha)
    for n, s in frozen["config"]["nets_sha256"].items():
        if _sha(OUT / f"{n}.pt") != s:
            raise PermissionError(f"la red {n} no es la congelada")
    test, _ = run_h18._cases(a.manifest, "test")
    rows = _measure(a, test, OUT / "test_rows.jsonl")
    lit = h19.lights(rows, {"model": frozen["model"], "envelope": frozen["envelope"]})
    err = lit["rel_error_volume"].abs()
    free = lit[lit["light_without_guard"] == "verde"]
    out = {"n_cases": int(len(lit)), "n_embryos": int(lit["embryo_id"].nunique()),
           "h19b": h18.green_failure(lit),
           "h19a": {"green_fraction": float((lit["light"] == "verde").mean()), "lights": lit["light"].value_counts().to_dict()},
           "h19c": {"dice_median": float(lit["dice"].median()), "abs_error_median": float(err.median()),
                    "ok10": float((err <= 0.10).mean()), "ok5": float((err <= 0.05).mean())},
           "h19d": {"in_domain": float(lit["in_domain"].mean()), "green_without_guard": int(len(free)),
                    "green_without_guard_bad": int((free["rel_error_volume"].abs() > 0.10).sum())},
           "frozen_sha256": a.sha, "provenance": git_state()}
    lit.to_csv(OUT / "test_cases.csv", index=False)
    (OUT / "test_verdicts.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("h19a", "h19b", "h19c", "h19d")}, default=float))


def main(argv=None):
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["split", "train-coarse", "train-fine", "calibrate", "test"])
    ap.add_argument("--manifest", default="results/h11/manifiesto_qiu2021.csv")
    ap.add_argument("--root", default="data/external/ieee_qiu2021/nii")
    ap.add_argument("--sha", default="")
    a = ap.parse_args(argv)
    {"split": cmd_split, "train-coarse": cmd_train_coarse, "train-fine": cmd_train_fine,
     "calibrate": cmd_calibrate, "test": cmd_test}[a.cmd](a)


if __name__ == "__main__":
    main()
