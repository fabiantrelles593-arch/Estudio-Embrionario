"""FI-1 de extremo a extremo con marcas SINTÉTICAS (scripts/fi1_foto_impresion.py).

Qué haría fallar cada prueba: si sin registro de G0-ética se pudiera medir, el código no protegería la condición ética
del preregistro; si una foto marcada no diera las distancias impresas, la cadena marcas → mm estaría rota; si una
foto de papel doblado pasara las puertas, G0-homografía no serviría; si el plan no repitiera cada foto en 3 sesiones,
no sería el preregistrado. Sin imágenes humanas.
"""
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pytest

from geovida import print_measure as pm

_spec = importlib.util.spec_from_file_location(
    "fi1", Path(__file__).resolve().parents[1] / "scripts" / "fi1_foto_impresion.py")
fi1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fi1)

W, H = 120.0, 90.0


def _marks(rng, pairs_mm, bend=0.0, noise=0.3):
    src = np.array([[0, 0], [W, 0], [W, H], [0, H]], float)
    dst = src * 15 + np.array([200, 150]) + rng.uniform(-0.2, 0.2, (4, 2)) * 15 * W
    Hph = pm.homography(src, dst)
    j = lambda x: pm.warp_points(Hph, np.asarray(x, float)) + rng.normal(0, noise, (len(x), 2))  # noqa: E731
    mids = np.array([[W / 2, bend], [W, H / 2], [W / 2, H], [0, H / 2]], float)
    return {"aspect_mm": [W, H], "corners": j(src).tolist(), "midpoints": j(mids).tolist(),
            "ticks": j([[W - 5, 5 + 10 * k] for k in range(8)]).tolist(),
            "pairs": {n: j(pq).tolist() for n, pq in pairs_mm.items()}}


def _setup(tmp_path, rng, ethics=True, bend=0.0):
    base = tmp_path / "eco"
    (base / "marcas").mkdir(parents=True)
    if ethics:
        (base / "g0_etica.json").write_text(json.dumps(
            {"consentimiento_codigo": "CI-001", "aval_etico": "SINTETICO", "anonimizacion_revisada": True}))
    printed = {}
    for pr in ("IMP01", "IMP02"):
        pairs = {}
        for k in range(4):
            p = rng.uniform([15, 15], [70, 60])
            a = rng.uniform(0, 2 * math.pi)
            q = p + rng.uniform(10, 30) * np.array([math.cos(a), math.sin(a)])
            pairs[f"P{k + 1}"] = [p.tolist(), q.tolist()]
        printed[pr] = {n: round(float(np.linalg.norm(np.subtract(*map(np.array, pq)))), 2)
                       for n, pq in pairs.items()}
        for ph in ("F1", "F2", "F3"):
            for r in (1, 2, 3):
                m = _marks(rng, pairs, bend=bend)
                m.update({"print": pr, "photo": ph})
                (base / "marcas" / f"{pr}-{ph}_r{r}.json").write_text(json.dumps(m))
    (base / "valores_impresos.json").write_text(json.dumps(printed))
    return base


def test_without_ethics_record_nothing_is_measured(tmp_path):
    base = _setup(tmp_path, np.random.default_rng(1), ethics=False)
    res = fi1.run_gates(base)
    assert not res["passed"] and "fotos" not in res["gates"]
    assert set(res["gates"]["G0-ética"]["missing"]) == set(pm.ETHICS_FIELDS)
    (base / "g0_etica.json").write_text(json.dumps({"consentimiento_codigo": "CI-001"}))
    assert not fi1.ethics(base)["passed"]


def test_end_to_end_synthetic_is_supported(tmp_path):
    base = _setup(tmp_path, np.random.default_rng(2))
    g = fi1.run_gates(base)
    assert g["passed"] and g["n_marks"] == 18
    res = fi1.run_analysis(base)
    assert res["n_measurements"] == 72 and res["n_prints"] == 2 and res["n_photos"] == 6
    assert res["median_abs_error"] < 0.02 and res["verdict"]["FI-1a"] == "apoyada"
    assert res["fi1c"]["median_abs_error_uncorrected"] > res["median_abs_error"]


def test_bent_paper_fails_homography_gate(tmp_path):
    base = _setup(tmp_path, np.random.default_rng(3), bend=4.0)
    g = fi1.run_gates(base)
    assert not g["passed"]
    assert all(not v["G0-homografia"] for v in g["gates"]["fotos"].values())


def test_plan_repeats_each_photo_once_per_session():
    p1 = fi1.plan(["IMP01-F1", "IMP01-F2", "IMP02-F1"])
    assert p1 == fi1.plan(["IMP01-F1", "IMP01-F2", "IMP02-F1"])
    assert len(p1) == 9
    for s in (1, 2, 3):
        assert sorted(x["photo"] for x in p1 if x["session"] == s) == ["IMP01-F1", "IMP01-F2", "IMP02-F1"]
    assert {x["file"] for x in p1} == {f"marcas/{ph}_r{r}.json" for ph in ("IMP01-F1", "IMP01-F2", "IMP02-F1")
                                       for r in (1, 2, 3)}


def test_gate_ethics_requires_all_fields():
    assert pm.gate_ethics(None)["passed"] is False
    full = {"consentimiento_codigo": "CI-001", "aval_etico": "X", "anonimizacion_revisada": True}
    assert pm.gate_ethics(full)["passed"]
    assert not pm.gate_ethics({**full, "anonimizacion_revisada": False})["passed"]
    with pytest.raises(KeyError):
        pm.measure_photo({})
