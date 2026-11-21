"""H18: segmentador y certificado con ecografía real, en este orden fijo (docs/PREREGISTRO_H18.md §4).

    python scripts/run_h18.py split    --manifest results/h11/manifiesto_qiu2021.csv
    python scripts/run_h18.py develop  --manifest ... --root data/external/ieee_qiu2021/nii   # solo entrenamiento
    python scripts/run_h18.py observe  --manifest ... --root ...                              # solo entrenamiento
    python scripts/run_h18.py freeze   --manifest ...                     # puerta F; congela si pasa
    python scripts/run_h18.py test     --manifest ... --root ... --sha <SHA-256 anotado en el preregistro>

``develop`` y ``observe`` nunca leen un volumen de prueba (lo comprueba ``_cases``). ``test`` se niega a
correr si el congelado no tiene el SHA-256 dado. Todo es reanudable: cada caso se guarda al terminarlo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from geovida import h18
from geovida.provenance import git_state
from geovida.realdata import load_volume

OUT = Path("results/h18")


def _sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _cases(manifest: str, split: str) -> tuple[pd.DataFrame, dict]:
    m = pd.read_csv(manifest)
    m = m[m["structure"] == "body"]
    df, rep = h18.split_cases(m)
    sel = df[df["split"] == split].reset_index(drop=True)
    assert set(sel["split"]) <= {split}
    return sel, rep


def _load(root, case):
    image, spacing, _ = load_volume(Path(root) / case["image"])
    label, lsp, _ = load_volume(Path(root) / case["label"])
    if label.shape != image.shape or not np.allclose(spacing, lsp, rtol=1e-4):
        raise ValueError(f"{case['embryo_id']}: imagen y etiqueta no coinciden")
    ref = label == case["label_value"]
    if not ref.any():
        raise ValueError(f"{case['embryo_id']}: etiqueta vacía")
    return image, spacing, ref


def _done(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def _append(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as f:
        for r in rows:
            f.write((json.dumps(r, ensure_ascii=False) + "\n").encode("utf-8"))


def cmd_split(a):
    _, rep = _cases(a.manifest, "train")
    rep["manifest_sha256"] = _sha(a.manifest)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reparto.json").write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(rep))


def cmd_develop(a):
    train, _ = _cases(a.manifest, "train")
    path = OUT / "grid_train.jsonl"
    have = {r["image"] for r in _done(path)}
    todo = train[~train["image"].isin(have)]
    for i, (_, c) in enumerate(todo.iterrows(), 1):
        image, sp, ref = _load(a.root, c)
        rows = h18.grid_rows(image, sp, ref)
        _append(path, [{"image": c["image"], "embryo_id": c["embryo_id"], **r} for r in rows])
        best = min(abs(r["rel_error_volume"]) for r in rows)
        print(f"[{i}/{len(todo)}] {c['image']} mejor |error| {best:.1%}", flush=True)


def _selected(manifest) -> dict:
    train, _ = _cases(manifest, "train")
    grid = pd.DataFrame(_done(OUT / "grid_train.jsonl"))
    missing = set(train["image"]) - set(grid["image"])
    if missing:
        raise SystemExit(f"faltan {len(missing)} casos de entrenamiento en grid_train.jsonl")
    return h18.select_config(grid[grid["image"].isin(train["image"])])


def cmd_observe(a):
    train, _ = _cases(a.manifest, "train")
    cfg = _selected(a.manifest)
    path = OUT / f"obs_train_{h18.config_key(cfg)}.jsonl"
    have = {r["image"] for r in _done(path)}
    todo = train[~train["image"].isin(have)]
    for i, (_, c) in enumerate(todo.iterrows(), 1):
        image, sp, ref = _load(a.root, c)
        mask = h18.smooth_lcc(image, sp, cfg["sigma"], cfg["thr"], cfg["close"])
        v, vr = float(mask.sum()), float(ref.sum())
        row = {"image": c["image"], "embryo_id": c["embryo_id"], "rel_error_volume": (v - vr) / vr,
               "dice": 2 * float(np.logical_and(mask, ref).sum()) / (v + vr), **h18.observables(image, sp, mask)}
        _append(path, [row])
        print(f"[{i}/{len(todo)}] {c['image']} |error| {abs(row['rel_error_volume']):.1%}", flush=True)


def cmd_freeze(a):
    train, rep = _cases(a.manifest, "train")
    cfg = _selected(a.manifest)
    obs = pd.DataFrame(_done(OUT / f"obs_train_{h18.config_key(cfg)}.jsonl"))
    obs = obs[obs["image"].isin(train["image"])]
    if len(obs) != len(train):
        raise SystemExit(f"observables de {len(obs)} de {len(train)} casos de entrenamiento")
    gate = h18.feasibility_gate(obs)
    result = {"config": cfg, "gate": gate, "split": rep, "manifest_sha256": _sha(a.manifest),
              "provenance": git_state()}
    if gate["passed"]:
        cert = h18.fit_certificate(obs)
        sha = h18.freeze(OUT / "h18_frozen.json", cfg, cert,
                         {"train_manifest_sha256": result["manifest_sha256"], "gate": gate})
        result["frozen_sha256"] = sha
        print(f"puerta F superada; congelado {OUT / 'h18_frozen.json'} SHA-256 {sha}")
        print("Anotar el SHA-256 en «Desviaciones» del preregistro y subirlo ANTES de correr `test`.")
    else:
        print("puerta F NO superada: la prueba no se abre; H18 es «no evaluable por diseño».")
    (OUT / "freeze.json").write_text(json.dumps(result, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({"config": cfg, "gate": gate}, default=float))


def cmd_test(a):
    frozen = h18.check_frozen(OUT / "h18_frozen.json", a.sha)
    cfg = frozen["config"]
    test, _ = _cases(a.manifest, "test")
    path = OUT / "test_rows.jsonl"
    have = {r["image"] for r in _done(path)}
    for i, (_, c) in enumerate(test[~test["image"].isin(have)].iterrows(), 1):
        image, sp, ref = _load(a.root, c)
        mask = h18.smooth_lcc(image, sp, cfg["sigma"], cfg["thr"], cfg["close"])
        v, vr = float(mask.sum()), float(ref.sum())
        _append(path, [{"image": c["image"], "embryo_id": c["embryo_id"], "rel_error_volume": (v - vr) / vr,
                        "dice": 2 * float(np.logical_and(mask, ref).sum()) / (v + vr),
                        **h18.observables(image, sp, mask)}])
        print(f"[{i}] {c['image']}", flush=True)
    rows = pd.DataFrame(_done(path))
    rows = rows[rows["image"].isin(test["image"])]
    res = h18.evaluate_test(rows, frozen)
    res["rows"].to_csv(OUT / "test_cases.csv", index=False)
    out = {k: v for k, v in res.items() if k != "rows"}
    out.update(frozen_sha256=a.sha, provenance=git_state())
    (OUT / "test_verdicts.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("h18a", "h18b", "h18c", "h18d")}, default=float))


def main(argv=None):
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["split", "develop", "observe", "freeze", "test"])
    ap.add_argument("--manifest", default="results/h11/manifiesto_qiu2021.csv")
    ap.add_argument("--root", default="data/external/ieee_qiu2021/nii")
    ap.add_argument("--sha", default="")
    a = ap.parse_args(argv)
    {"split": cmd_split, "develop": cmd_develop, "observe": cmd_observe, "freeze": cmd_freeze,
     "test": cmd_test}[a.cmd](a)


if __name__ == "__main__":
    main()
