"""MT-A v2 (docs/morpho_trace/PREREGISTRO_ATLAS_v2.md): muestra y especímenes excluidos del cálculo de d.

    python scripts/mta_v2.py sample      # 20 + 20 por semilla entre los de QC-LM que cumplen; no lee imágenes
    python scripts/mta_v2.py selection   # results/morpho_trace/v2/seleccion_v2.json (pilot = muestra; confirm = 597)
    python scripts/mta_v2.py g0a3        # G0-a″
    python scripts/mta_v2.py g0t         # G0-t: un registro atlas E18.5 → atlas E15.5, cronometrado
    python scripts/atlas_effect_gates.py g0d --ids results/morpho_trace/v2/seleccion_v2.json \\
        --data data/external/musmorph/landmarks_confirm --out results/morpho_trace/v2/g0d2.json        # G0-d′
    python scripts/atlas_effect_gates.py register --ids results/morpho_trace/v2/seleccion_v2.json \\
        --images data/external/musmorph/qc_images --regs results/morpho_trace/v2/registros
    python scripts/atlas_effect_gates.py analyze --protocol 2.0 --ids results/morpho_trace/v2/seleccion_v2.json \\
        --landmarks data/external/musmorph/landmarks_confirm --regs results/morpho_trace/v2/registros \\
        --gates-dir results/morpho_trace/v2 --out results/morpho_trace/v2/analisis.json

El registro, la transferencia y el análisis son los de MT-A v1.0 (`scripts/atlas_effect_gates.py`), con dos cambios
fijados en el preregistro: la muestra sale de este archivo y **d** se calcula con el confirmatorio de ONTO-MAP **sin**
los 120 especímenes de QC-LM, para que **d** y el efecto del atlas no compartan especímenes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

SEED = 20261122
N_PER_STAGE = 20
STAGES = ("E15.5", "E18.5")


def draw(qc_sample: dict, passed: dict[str, bool], seed: int = SEED, n: int = N_PER_STAGE) -> dict:
    """Muestra fija: para cada estadio, ``n`` nombres sin reemplazo, por semilla, entre los que cumplen (orden alfabético)."""
    rng = np.random.default_rng(seed)
    out = {"seed": seed, "sample": {}, "excluded_from_d": sorted(qc_sample["E15.5"] + qc_sample["E18.5"])}
    for st in STAGES:
        passers = sorted(name for name in qc_sample[st] if passed[name])
        if len(passers) < n:
            raise ValueError(f"{st}: solo {len(passers)} especímenes cumplen; hacen falta {n}")
        out["sample"][st] = sorted(rng.choice(passers, size=n, replace=False).tolist())
        out[f"n_passers_{st}"] = len(passers)
    out["sample_sha256"] = hashlib.sha256(json.dumps(out["sample"], sort_keys=True).encode()).hexdigest()
    return out


def confirm_without(confirm: dict, excluded) -> dict:
    """Confirmatorio de ONTO-MAP sin los especímenes excluidos (por estadio)."""
    ex = set(excluded)
    return {st: [n for n in names if n not in ex] for st, names in confirm.items()}


MAX_HOURS_80 = 72.0          # puerta G0-t: 80 registros en ≤ 72 h


def selection(v2: dict, onto_sel: dict) -> dict:
    """Selección con la forma de ``results/onto_map/seleccion.json`` para reutilizar ``atlas_effect_gates.py`` sin
    cambiarlo: ``pilot`` = muestra de v2; ``confirm`` = confirmatorio de ONTO-MAP sin los especímenes de QC-LM."""
    return {"pilot": v2["sample"], "confirm": confirm_without(onto_sel["confirm"], v2["excluded_from_d"]),
            "seed": v2["seed"], "protocol": "MT-A v2"}


def g0a3(sample: dict, passed: dict, within: dict) -> dict:
    """G0-a″: los 40 de la muestra cumplen la regla de QC-LM (se relee desde los archivos de medida)."""
    rows = [{"name": n, "within": within[n], "passed": bool(passed[n])} for st in STAGES for n in sample[st]]
    return {"gate": "G0-a″", "items": rows, "passed": bool(rows) and all(r["passed"] for r in rows)}


def g0t(seconds_one: float, n_registrations: int = 80, max_hours: float = MAX_HOURS_80) -> dict:
    """G0-t: con el tiempo de un registro de prueba, ¿caben los 80 en el límite?"""
    hours = seconds_one * n_registrations / 3600
    return {"gate": "G0-t", "seconds_one": round(seconds_one, 1), "hours_estimated": round(hours, 1),
            "max_hours": max_hours, "passed": bool(hours <= max_hours)}


def _timing_registration(atlas_dir: Path, cache: Path) -> float:
    """Registro atlas E18.5 → atlas E15.5 (sensibilidad 3 de v1.0): no usa ningún espécimen."""
    import importlib.util
    import sys
    import time

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from geovida import atlas_effect as ae
    spec = importlib.util.spec_from_file_location("gates", Path(__file__).with_name("atlas_effect_gates.py"))
    gates = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gates)
    a15 = gates.load_x4(atlas_dir / gates.ATLAS_IMAGES["E15.5"], cache)
    a18 = gates.load_x4(atlas_dir / gates.ATLAS_IMAGES["E18.5"], cache)
    t0 = time.time()
    ae.register(ae.to_sitk(a15["downsampled"], a15["affine_ds"]), ae.to_sitk(a18["downsampled"], a18["affine_ds"]))
    return time.time() - t0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["sample", "selection", "g0a3", "g0t"])
    ap.add_argument("--qc", default="results/landmark_qc/muestra.json")
    ap.add_argument("--measures", default="results/landmark_qc/medidas")
    ap.add_argument("--v2", default="results/morpho_trace/muestra_v2.json")
    ap.add_argument("--onto", default="results/onto_map/seleccion.json")
    ap.add_argument("--atlas", default="data/external/musmorph/atlas")
    ap.add_argument("--cache", default="results/morpho_trace/cache")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    v2dir = Path("results/morpho_trace/v2")
    if a.cmd == "sample":
        qc = json.loads(Path(a.qc).read_text(encoding="utf-8"))["sample"]
        passed = {p.stem: json.loads(p.read_text(encoding="utf-8"))["passed"] for p in Path(a.measures).glob("*.json")}
        res, out = draw(qc, passed), Path(a.out or a.v2)
    elif a.cmd == "selection":
        res = selection(json.loads(Path(a.v2).read_text(encoding="utf-8")),
                        json.loads(Path(a.onto).read_text(encoding="utf-8")))
        out = Path(a.out or v2dir / "seleccion_v2.json")
    elif a.cmd == "g0a3":
        meas = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in Path(a.measures).glob("*.json")}
        res = g0a3(json.loads(Path(a.v2).read_text(encoding="utf-8"))["sample"],
                   {k: v["passed"] for k, v in meas.items()}, {k: v["within"] for k, v in meas.items()})
        out = Path(a.out or v2dir / "g0a3.json")
    else:
        res, out = g0t(_timing_registration(Path(a.atlas), Path(a.cache))), Path(a.out or v2dir / "g0t.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")
    print({k: v for k, v in res.items() if k not in ("sample", "excluded_from_d", "items", "pilot", "confirm")})
    return 0 if res.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
