"""QC-LM (``scripts/landmark_qc.py``). Configuraciones sintéticas; ningún dato real.

Qué falla si cambia la muestra fijada por la semilla, si las puertas dejan pasar datos incompletos o mal alineados,
o si los veredictos de QC1/QC2 no siguen los criterios del preregistro.
"""
import importlib.util
from pathlib import Path

import numpy as np

_spec = importlib.util.spec_from_file_location(
    "landmark_qc", Path(__file__).resolve().parents[1] / "scripts" / "landmark_qc.py")
qc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qc)


def _sel():
    return {"pilot": {"E15.5": ["P15"], "E18.5": ["P18"]},
            "confirm": {"E15.5": [f"IMPC_E15.5_{i:04d}" for i in range(259)],
                        "E18.5": [f"IMPC_E18.5_{i:04d}" for i in range(458)]}}


def test_constants_are_the_preregistered_ones():
    assert (qc.SEED, qc.N_PER_STAGE, qc.N_BOOT, qc.MIN_MEASURED) == (20261119, 60, 2000, 57)
    assert (qc.QC2_MIN_FAIL15, qc.QC2_MIN_PASS, qc.REL, qc.QC1_REFUTE) == (3, 30, 0.05, 0.05)


def test_select_is_reproducible_and_does_not_depend_on_input_order():
    s = _sel()
    a = qc.select(s)
    shuffled = {**s, "confirm": {st: list(reversed(v)) for st, v in s["confirm"].items()}}
    assert a == qc.select(shuffled)
    for st in qc.STAGES:
        assert len(a["sample"][st]) == len(set(a["sample"][st])) == 60
        assert set(a["sample"][st]) <= set(s["confirm"][st])
    assert qc.select(s, seed=1) != a


def _case(n=60, n_fail15=12, shift=0.06, k=15, seed=0):
    """E15.5 con ``n_fail15`` especímenes que no cumplen y cuyos landmarks están desplazados hacia E18.5."""
    rng = np.random.default_rng(seed)
    base = rng.normal(0, 1, (k, 3))
    dvec = rng.normal(0, 1, (k, 3)) * 0.1
    rows, configs = [], {}
    for st in qc.STAGES:
        for i in range(n):
            name = f"IMPC_{st}_{i:04d}"
            bad = st == "E15.5" and i < n_fail15
            shape = base + (dvec / 2 if st == "E18.5" else -dvec / 2) + rng.normal(0, 0.01, base.shape)
            if bad:
                shape = shape + shift * dvec / np.linalg.norm(dvec) * 3
            configs[name] = shape
            rows.append({"name": name, "stage": st, "passed": not bad, "affine": np.eye(4).tolist()})
    return rows, configs, {st: np.eye(4) for st in qc.STAGES}


def test_displaced_failing_specimens_change_d_and_are_detected():
    rows, configs, aff = _case()
    r = qc.analyze(rows, configs, aff, n_boot=200)
    assert r["failed_gates"] == []
    assert r["qc1"]["n_fail"] == {"E15.5": 12, "E18.5": 0} and r["qc1"]["verdict"] == "apoyada"
    assert r["qc2"]["evaluable"] and r["qc2"]["relative_change"] > 0.05 and r["qc2"]["verdict"] == "apoyada"


def test_failing_specimens_without_displacement_leave_d_unchanged():
    rows, configs, aff = _case(shift=0.0)
    r = qc.analyze(rows, configs, aff, n_boot=200)
    assert r["qc2"]["verdict"] == "refutada" and abs(r["qc2"]["relative_change"]) < 0.05


def test_equal_prevalence_refutes_qc1_and_too_few_failures_make_qc2_not_evaluable():
    rows, configs, aff = _case(n_fail15=0)
    r = qc.analyze(rows, configs, aff, n_boot=200)
    assert r["qc1"]["diff"] == 0 and r["qc1"]["verdict"] == "refutada"
    assert r["qc2"] == {"evaluable": False, "verdict": "no evaluable"}


def test_gates_block_incomplete_or_misaligned_data():
    rows, configs, aff = _case()
    r = qc.analyze(rows[4:], configs, aff, n_boot=50)                   # 56 de 60 en E15.5
    assert r["failed_gates"] == ["G1"] and r["qc1"]["verdict"] == r["qc2"]["verdict"] == "no evaluable"
    rows[0]["affine"] = (np.eye(4) * 2).tolist()
    r = qc.analyze(rows, configs, aff, n_boot=50)
    assert "G2" in r["failed_gates"]
