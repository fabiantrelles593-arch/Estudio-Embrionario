"""H26: replicación con el instrumento congelado (docs/h26/PREREGISTRO_H26_BORRADOR.md, base aprobada).

    python scripts/run_h26.py check                                  # huellas de los congelados y de las redes
    python scripts/run_h26.py replay-public                          # comprueba la evaluación con H20 y H25 ya medidos
    python scripts/run_h26.py g0-datos --new-manifest M --new-root R --terms T   # sin abrir ninguna imagen
    python scripts/run_h26.py g0       --new-manifest M --new-root R              # 5 volúmenes, sin leer referencias
    python scripts/run_h26.py test     --new-manifest M --new-root R              # una sola vez

El manifiesto nuevo tiene las columnas del público (``image``, ``label``, ``label_value``, ``embryo_id``,
``structure`` con ``body`` o la estructura de ventrículo de H23). ``test`` deja un candado en ``results/h26`` al
empezar y se niega a empezar otra vez; si se interrumpe, ``--resume`` sigue la misma corrida. Nada se ajusta.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from geovida import h18, h19, h20, h23, h24, h26
from geovida.provenance import git_state
from geovida.realdata import load_volume

OUT = Path("results/h26")


def _load_script(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


run_h20 = _load_script("run_h20")
run_h25 = _load_script("run_h25")
run_h24 = run_h25.run_h24
run_h18 = run_h25.run_h18


def _sha(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=1, default=float) + "\n", encoding="utf-8")


def _require(name):
    p = OUT / name
    if not p.exists() or not json.loads(p.read_text(encoding="utf-8")).get("passed"):
        raise SystemExit(f"{name} no superada o no existe: el preregistro no permite seguir")


def _frozen(kind):
    f = h26.FROZEN[kind]
    return h18.check_frozen(f["file"], f["sha256"])


def _new_cases(a, structure):
    m = pd.read_csv(a.new_manifest)
    excluded = set(json.loads((OUT / "g0_datos.json").read_text(encoding="utf-8"))["excluded_same_file"])
    g0d = json.loads((OUT / "g0_datos.json").read_text(encoding="utf-8"))
    m = m[~m["image"].isin(excluded) & ~m["embryo_id"].astype(str).isin(g0d["excluded_same_embryo"])]
    return m[m["structure"] == structure].reset_index(drop=True)


# --- Órdenes ------------------------------------------------------------------------------------------
def cmd_check(a):
    body, vent = _frozen("body"), _frozen("ventricle")
    _, _, nets_body = run_h20._nets()
    nets_vent = run_h24._check_nets()
    if nets_body != body["nets_sha256"] or nets_vent != vent["nets_sha256"]:
        raise PermissionError("las redes no son las de los congelados")
    if body["thresholds"] != json.loads(json.dumps(h20.THRESHOLDS)):
        raise PermissionError("los umbrales de cuerpo del código no son los congelados en H20")
    if vent["thresholds"] != json.loads(json.dumps(h24.THRESHOLDS)):
        raise PermissionError("los umbrales de ventrículo del código no son los congelados en H25")
    _write("check.json", {"passed": True, "frozen": h26.FROZEN, "nets_body": nets_body, "nets_ventricle": nets_vent,
                          "provenance": git_state()})
    print("congelados y redes verificados")


def cmd_replay_public(a):
    """Rehace la evaluación de H20 y H25 desde sus filas ya medidas (sin calcular ninguna red ni abrir nada nuevo)
    y comprueba que R1b y V1b dan exactamente H20b y H25b. Informa además qué diría S-1 en esos datos."""
    body_rows = pd.DataFrame(run_h18._done(Path("results/h20/test_rows.jsonl")))
    lit_b = h20.lights(body_rows, _frozen("body")["envelope"])
    rb = h26.evaluate_body(lit_b)
    h20v = json.loads(Path("results/h20/test_verdicts.json").read_text(encoding="utf-8"))
    vent_rows = pd.DataFrame(run_h18._done(Path("results/h25/test_rows.jsonl")))
    lit_v = h24.lights(vent_rows, _frozen("ventricle")["envelope"])
    rv = h26.evaluate_ventricle(lit_v)
    h25v = json.loads(Path("results/h25/test_verdicts.json").read_text(encoding="utf-8"))
    same_b = rb["r1b"] == json.loads(json.dumps(h20v["h20b"], default=float))
    same_v = rv["v1b"] == json.loads(json.dumps(h25v["h25b"], default=float))
    out = {"passed": bool(same_b and same_v), "r1b_equals_h20b": same_b, "v1b_equals_h25b": same_v,
           "r1d_with_s1_on_h20": rb["r1d"], "v1d_with_s1_on_h25": rv["v1d"], "provenance": git_state()}
    _write("replay_public.json", out)
    print(json.dumps({k: out[k] for k in ("passed", "r1b_equals_h20b", "v1b_equals_h25b")}))
    print("S-1 en H20:", rb["r1d"]["verdict"], rb["r1d"]["reasons"])
    print("S-1 en H25:", rv["v1d"]["verdict"], rv["v1d"]["reasons"])


def cmd_g0_datos(a):
    _require("check.json")
    m = pd.read_csv(a.new_manifest)
    root = Path(a.new_root)
    missing = []
    for col in ("image", "label"):
        if col in m:
            missing += [str(p) for p in m[col].unique() if not (root / p).exists()]
    new_sha = {p: _sha(root / p) for p in m["image"].unique() if (root / p).exists()} if "image" in m else {}
    pub = pd.read_csv(a.manifest)
    proot = Path(a.root)
    public_sha = {p: _sha(proot / p) for p in pub["image"].unique() if (proot / p).exists()}
    if len(public_sha) != pub["image"].nunique():
        raise SystemExit("faltan imágenes públicas: sin ellas no se puede comprobar el solapamiento")
    terms = _sha(a.terms) if a.terms and Path(a.terms).exists() else None
    out = h26.g0_datos(m, new_sha, public_sha, set(pub["embryo_id"].astype(str)), terms, sorted(set(missing)))
    out.update({"new_manifest_sha256": _sha(a.new_manifest), "provenance": git_state()})
    _write("g0_datos.json", out)
    print(json.dumps({k: out[k] for k in ("passed", "checks", "n_kept", "counts", "excluded_same_file",
                                          "excluded_same_embryo")}))


def cmd_g0(a):
    """Factibilidad en 5 volúmenes de cuerpo, **solo imagen**: no se lee ninguna referencia y nada se ajusta."""
    _require("check.json")
    _require("g0_datos.json")
    coarse, fine, _ = run_h20._nets()
    body = _new_cases(a, "body")
    pick = body.iloc[np.sort(np.random.default_rng(h26.SEED_G0).choice(len(body), min(h26.N_G0, len(body)),
                                                                       replace=False))]
    rows = []
    for _, c in pick.iterrows():
        image, _, _ = load_volume(Path(a.new_root) / c["image"])
        t0 = time.time()
        vols = h20.flip_volumes(coarse, fine, image)
        s = h20.signals(vols, h20.coarse_volume(coarse, image))
        rows.append({"image": c["image"], **s, "seconds": round(time.time() - t0, 1)})
        print(f"  {c['image']}: {rows[-1]['seconds']} s", flush=True)
    ok = [np.isfinite(r["s_flip"]) and np.isfinite(r["s_stage"]) and r["seconds"] <= h20.G0_MAX_SECONDS for r in rows]
    _write("g0.json", {"passed": bool(rows) and all(ok), "items": rows, "provenance": git_state()})
    print(json.dumps({"passed": bool(rows) and all(ok), "seconds": [r["seconds"] for r in rows]}))


def _measure_body(a, cases, coarse, fine):
    path = OUT / "test_rows_body.jsonl"
    done = {r["image"] for r in run_h18._done(path)}
    for _, c in cases[~cases["image"].isin(done)].iterrows():
        image, sp, ref = run_h18._load(a.new_root, c)
        mask, _ = h19.segment_full(coarse, fine, image)
        v, vr = float(mask.sum()), float(ref.sum())
        r = run_h20._signal_row(coarse, fine, image, ref, c)
        run_h18._append(path, [{**r, "rel_error_volume": (v - vr) / vr,
                                "dice": 2 * float(np.logical_and(mask, ref).sum()) / (v + vr),
                                "identity_matches_h19": bool(v == r["v_identity"]),
                                **h18.observables(image, sp, mask)}])
        print(f"  cuerpo {c['image']}", flush=True)
    rows = pd.DataFrame(run_h18._done(path))
    return rows[rows["image"].isin(cases["image"])].reset_index(drop=True)


def _measure_ventricle(a, cases, coarse, fine):
    path = OUT / "test_rows_ventricle.jsonl"
    done = {r["image"] for r in run_h18._done(path)}
    for _, c in cases[~cases["image"].isin(done)].iterrows():
        image, sp, ref = run_h18._load(a.new_root, c)
        run_h18._append(path, [run_h25.measure(coarse, fine, image, sp, ref, c)])
        print(f"  ventrículo {c['image']}", flush=True)
    rows = pd.DataFrame(run_h18._done(path))
    return rows[rows["image"].isin(cases["image"])].reset_index(drop=True)


def cmd_test(a):
    for n in ("check.json", "g0_datos.json", "g0.json"):
        _require(n)
    lock = OUT / "test_lock.json"
    if lock.exists() and not a.resume:
        raise SystemExit("la prueba de H26 ya se empezó: se abre una sola vez (usa --resume solo para continuarla)")
    if not lock.exists():
        _write("test_lock.json", {"started": datetime.now(timezone.utc).isoformat(),
                                  "new_manifest_sha256": _sha(a.new_manifest), "provenance": git_state()})
    body_frozen, vent_frozen = _frozen("body"), _frozen("ventricle")
    out = {"frozen": h26.FROZEN, "provenance": git_state()}

    coarse, fine, _ = run_h20._nets()
    rows = _measure_body(a, _new_cases(a, "body"), coarse, fine)
    if not rows["identity_matches_h19"].all():
        raise RuntimeError("la pasada identidad no reproduce la medida de H19 en algún volumen")
    lit = h20.lights(rows, body_frozen["envelope"])
    out["body"] = h26.evaluate_body(lit)
    lit.drop(columns=["volumes"]).to_csv(OUT / "test_cases_body.csv", index=False)

    vcases = _new_cases(a, h23.STRUCTURE)
    if len(vcases):
        vc, vf, _ = run_h24._nets()
        vrows = _measure_ventricle(a, vcases, vc, vf)
        vlit = h24.lights(vrows, vent_frozen["envelope"])
        out["ventricle"] = h26.evaluate_ventricle(vlit)
        vlit.drop(columns=["volumes"]).to_csv(OUT / "test_cases_ventricle.csv", index=False)
    _write("test_verdicts.json", out)
    print(json.dumps({"r1b": out["body"]["r1b"]["verdict"], "r1d": out["body"]["r1d"]["verdict"],
                      "v1b": out.get("ventricle", {}).get("v1b", {}).get("verdict"),
                      "v1d": out.get("ventricle", {}).get("v1d", {}).get("verdict")}))


def main(argv=None):
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["check", "replay-public", "g0-datos", "g0", "test"])
    ap.add_argument("--manifest", default="results/h11/manifiesto_qiu2021.csv", help="manifiesto público")
    ap.add_argument("--root", default="data/external/ieee_qiu2021/nii", help="carpeta de las imágenes públicas")
    ap.add_argument("--new-manifest", default="")
    ap.add_argument("--new-root", default="")
    ap.add_argument("--terms", default="", help="documento con las condiciones de uso por escrito")
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args(argv)
    {"check": cmd_check, "replay-public": cmd_replay_public, "g0-datos": cmd_g0_datos, "g0": cmd_g0,
     "test": cmd_test}[a.cmd](a)


if __name__ == "__main__":
    main()
