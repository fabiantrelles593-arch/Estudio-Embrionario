"""MT-A v2 (docs/morpho_trace/PREREGISTRO_ATLAS_v2.md): muestra y especímenes excluidos del cálculo de d.

    python scripts/mta_v2.py sample      # 20 + 20 por semilla entre los de QC-LM que cumplen; no lee imágenes

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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["sample"])
    ap.add_argument("--qc", default="results/landmark_qc/muestra.json")
    ap.add_argument("--measures", default="results/landmark_qc/medidas")
    ap.add_argument("--out", default="results/morpho_trace/muestra_v2.json")
    a = ap.parse_args(argv)
    qc = json.loads(Path(a.qc).read_text(encoding="utf-8"))["sample"]
    passed = {p.stem: json.loads(p.read_text(encoding="utf-8"))["passed"] for p in Path(a.measures).glob("*.json")}
    res = draw(qc, passed)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    print({k: v for k, v in res.items() if k not in ("sample", "excluded_from_d")})


if __name__ == "__main__":
    main()
