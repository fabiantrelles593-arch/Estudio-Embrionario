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


def test_d_is_computed_without_any_qc_specimen():
    s, passed = _qc()
    res = mta.draw(s, passed)
    confirm = {"E15.5": s["E15.5"] + ["IMPC_E15.5_9001"], "E18.5": s["E18.5"] + ["IMPC_E18.5_9002"]}
    rest = mta.confirm_without(confirm, res["excluded_from_d"])
    assert rest == {"E15.5": ["IMPC_E15.5_9001"], "E18.5": ["IMPC_E18.5_9002"]}
    assert not (set(rest["E15.5"]) | set(rest["E18.5"])) & set(res["sample"]["E15.5"] + res["sample"]["E18.5"])
