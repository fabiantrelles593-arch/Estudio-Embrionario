"""MT-A v2: la muestra sale solo de los que cumplen, es reproducible, y d se calcula sin ningún espécimen de QC-LM.

Qué haría fallar cada prueba: si entrara un espécimen que no cumple, MT-A volvería a medir landmarks desplazados; si la
muestra cambiara con la misma semilla, se podría elegir después; si d compartiera especímenes con la muestra, el
efecto del atlas y d no serían independientes (§2 de PREREGISTRO_ATLAS.md).
"""
import importlib.util
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("mta_v2", Path(__file__).resolve().parents[1] / "scripts" / "mta_v2.py")
mta = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mta)


def _qc(n=45):                                                    # 30 cumplen: la semilla sí elige
    s = {"E15.5": [f"IMPC_E15.5_{i:04d}" for i in range(n)], "E18.5": [f"IMPC_E18.5_{i:04d}" for i in range(n)]}
    passed = {name: (i % 3 != 0) for st in s for i, name in enumerate(s[st])}     # un tercio no cumple
    return s, passed


def test_sample_only_from_passers_and_reproducible():
    s, passed = _qc()
    a, b = mta.draw(s, passed), mta.draw(s, passed)
    assert a["sample"] == b["sample"] and a["sample_sha256"] == b["sample_sha256"]
    for st in mta.STAGES:
        assert len(a["sample"][st]) == mta.N_PER_STAGE and all(passed[n] for n in a["sample"][st])
    assert mta.draw(s, passed, seed=1)["sample"] != a["sample"]


def test_not_enough_passers_is_an_error():
    s, passed = _qc(n=12)                                           # 8 cumplen y hacen falta 20
    with pytest.raises(ValueError):
        mta.draw(s, passed)


def test_selection_has_the_shape_atlas_effect_gates_expects_and_is_disjoint():
    s, passed = _qc()
    v2 = mta.draw(s, passed)
    onto = {"pilot": {"E15.5": ["old1"], "E18.5": ["old2"]},
            "confirm": {"E15.5": s["E15.5"] + ["IMPC_E15.5_9001"], "E18.5": s["E18.5"] + ["IMPC_E18.5_9002"]}}
    sel = mta.selection(v2, onto)
    assert sel["pilot"] == v2["sample"]                                   # la muestra de v2, no el piloto viejo
    assert sel["confirm"] == {"E15.5": ["IMPC_E15.5_9001"], "E18.5": ["IMPC_E18.5_9002"]}
    pilot = set(sel["pilot"]["E15.5"] + sel["pilot"]["E18.5"])
    assert not pilot & set(sel["confirm"]["E15.5"] + sel["confirm"]["E18.5"])


def test_g0a3_and_g0t():
    sample = {"E15.5": ["a", "b"], "E18.5": ["c"]}
    ok = mta.g0a3(sample, {"a": True, "b": True, "c": True}, {"a": 0.99, "b": 0.97, "c": 1.0})
    assert ok["passed"] and len(ok["items"]) == 3
    assert not mta.g0a3(sample, {"a": True, "b": False, "c": True}, {"a": 1, "b": 0.9, "c": 1})["passed"]
    assert mta.g0t(3000)["passed"] and mta.g0t(3000)["hours_estimated"] == pytest.approx(66.7, abs=0.1)
    assert not mta.g0t(3300)["passed"]                                    # 80 × 3300 s = 73,3 h > 72 h


def test_gate_files_per_protocol(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "gates", Path(__file__).resolve().parents[1] / "scripts" / "atlas_effect_gates.py")
    gates = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gates)
    import json
    v2 = tmp_path / "v2"
    v2.mkdir()
    for stem in ("g0b2", "g0c"):                                          # ya superadas, en la carpeta superior
        (tmp_path / f"{stem}.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    for stem in ("g0a3", "g0d2"):
        (v2 / f"{stem}.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    g = gates.gate_files(v2, "2.0")
    assert set(g) == {"G0-a″", "G0-b′", "G0-c", "G0-d′", "G0-t"}
    assert all(g[k]["passed"] for k in ("G0-a″", "G0-b′", "G0-c", "G0-d′"))
    assert g["G0-t"] == {"passed": False, "missing": True}                 # falta: no superada
    assert set(gates.gate_files(tmp_path, "1.1")) == {"G0-a′", "G0-b′", "G0-c", "G0-d"}


def test_d_is_computed_without_any_qc_specimen():
    s, passed = _qc()
    res = mta.draw(s, passed)
    confirm = {"E15.5": s["E15.5"] + ["IMPC_E15.5_9001"], "E18.5": s["E18.5"] + ["IMPC_E18.5_9002"]}
    rest = mta.confirm_without(confirm, res["excluded_from_d"])
    assert rest == {"E15.5": ["IMPC_E15.5_9001"], "E18.5": ["IMPC_E18.5_9002"]}
    assert not (set(rest["E15.5"]) | set(rest["E18.5"])) & set(res["sample"]["E15.5"] + res["sample"]["E18.5"])
