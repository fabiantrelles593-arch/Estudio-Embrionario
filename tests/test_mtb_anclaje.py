"""MT-B (PREREGISTRO_ANCLAJE_ATLAS.md): proyección de los atlas, descomposición d = a + e₁₈ − e₁₅, veredictos y puertas.

Qué haría fallar cada prueba: si la proyección no fuera la misma operación que el GPA, los atlas quedarían en un sitio
distinto del de los especímenes y r mediría esa diferencia; si la descomposición no cerrara, r no sería |e₁₈ − e₁₅|;
si especímenes alrededor de su atlas no dieran r ≈ 0, o desplazados no dieran r grande, el estimando no mediría lo
que dice; y si los umbrales o las puertas no fueran los escritos, el veredicto no sería el preregistrado. Sin datos
reales.
"""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from geovida import atlas_anchor as aa
from geovida import landmarks as lm

_spec = importlib.util.spec_from_file_location(
    "mtb_anclaje", Path(__file__).resolve().parents[1] / "scripts" / "mtb_anclaje.py")
mtb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mtb)

K = 20


def _rot(rng):
    q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    return q if np.linalg.det(q) > 0 else -q


def _atlases(rng, shift=0.25):
    a15 = rng.normal(size=(K, 3))
    a18 = a15 + shift * rng.normal(size=(K, 3))
    return a15, a18


def _specimens(rng, base, n, noise=0.02, offset=None):
    """Copias de ``base`` (+ ``offset``) con ruido, giradas, escaladas y trasladadas al azar."""
    out = []
    for _ in range(n):
        x = base + (0 if offset is None else offset) + noise * rng.normal(size=base.shape)
        out.append(rng.uniform(0.5, 2.0) * x @ _rot(rng) + rng.normal(size=3))
    return np.stack(out)


def _run(pub15, pub18, a15, a18, n_boot=200):
    s = aa.shape_space(pub15, pub18)
    t15a, t18a = aa.project_to_tangent(a15, s["mean"]), aa.project_to_tangent(a18, s["mean"])
    return s, aa.anchor_decomposition(s["t15"], s["t18"], t15a, t18a, n_boot=n_boot, seed=1)


# ---------------------------------------------------------------- proyección
def test_projection_reproduces_gpa_tangents():
    rng = np.random.default_rng(0)
    a15, a18 = _atlases(rng)
    pub15, pub18 = _specimens(rng, a15, 15), _specimens(rng, a18, 25)
    s = aa.shape_space(pub15, pub18)
    g = aa.gate_projection(pub15[:5], s["t15"][:5], s["mean"])
    assert g["passed"] and g["max_abs_diff"] < 1e-9
    assert np.max(np.abs(aa.project_to_tangent(pub18[3], s["mean"]) - s["t18"][3])) < 1e-9


def test_projection_ignores_similarity_transform():
    rng = np.random.default_rng(1)
    a15, _ = _atlases(rng)
    mean = lm.preshape(a15 + 0.05 * rng.normal(size=a15.shape))
    moved = 3.7 * a15 @ _rot(rng) + np.array([5.0, -2.0, 1.0])
    assert np.allclose(aa.project_to_tangent(a15, mean), aa.project_to_tangent(moved, mean), atol=1e-10)


# ---------------------------------------------------------------- descomposición
def test_decomposition_identity_closes():
    rng = np.random.default_rng(2)
    a15, a18 = _atlases(rng)
    _, res = _run(_specimens(rng, a15, 12), _specimens(rng, a18, 18), a15, a18, n_boot=20)
    assert res["identity_error"] < 1e-12
    p = res["point"]
    assert p["r"] >= abs(1 - p["f_a"]) - 1e-12        # |d − a| ≥ |proyección de d − a sobre d̂|


def test_specimens_around_their_atlas_give_small_r_and_support():
    rng = np.random.default_rng(3)
    a15, a18 = _atlases(rng)
    _, res = _run(_specimens(rng, a15, 40), _specimens(rng, a18, 60), a15, a18)
    assert res["point"]["r"] < 0.1
    assert abs(res["point"]["f_a"] - 1) < 0.1
    assert res["mtb1"]["verdict"] == "apoyada"
    assert res["mtb2"]["verdict"] == "apoyada"


def test_systematic_offset_gives_large_r_and_refutes():
    rng = np.random.default_rng(4)
    a15, a18 = _atlases(rng, shift=0.15)
    offset = 0.3 * rng.normal(size=(K, 3))              # los E18.5 se apartan de su atlas en una dirección fija
    _, res = _run(_specimens(rng, a15, 40), _specimens(rng, a18, 60, offset=offset), a15, a18)
    assert res["point"]["r"] > 0.5
    assert res["mtb1"]["verdict"] == "refutada"
    assert res["mtb2"]["verdict"] == "no apoyada"       # la media de E18.5 está lejos de su atlas


def test_bootstrap_is_reproducible_and_shifts_norm_upward():
    """r es una norma: con ruido, el remuestreo la infla y el IC percentil puede quedar por encima del punto
    (nota previa a la subida del preregistro). Lo que se exige es reproducibilidad y que el sesgo vaya hacia arriba."""
    rng = np.random.default_rng(5)
    a15, a18 = _atlases(rng)
    pub15, pub18 = _specimens(rng, a15, 20, noise=0.05), _specimens(rng, a18, 30, noise=0.05)
    _, r1 = _run(pub15, pub18, a15, a18)
    _, r2 = _run(pub15, pub18, a15, a18)
    assert r1["mtb1"]["ci"] == r2["mtb1"]["ci"]
    lo, hi = r1["mtb1"]["ci"]
    assert lo < hi and hi >= r1["point"]["r"]


# ---------------------------------------------------------------- veredictos
@pytest.mark.parametrize("lo,hi,expected", [
    (0.05, 0.25, "apoyada"), (0.05, 0.2501, "no concluyente"), (0.50, 0.9, "refutada"),
    (0.4999, 0.9, "no concluyente"), (0.2, 0.3, "no concluyente"), (float("nan"), 0.1, "no evaluable"),
])
def test_verdict_mtb1_thresholds(lo, hi, expected):
    assert aa.verdict_mtb1(lo, hi) == expected


def test_verdict_mtb2():
    med = {"E15.5": 0.03, "E18.5": 0.03}
    assert aa.verdict_mtb2({"E15.5": 0.01, "E18.5": 0.02}, med) == "apoyada"
    assert aa.verdict_mtb2({"E15.5": 0.01, "E18.5": 0.03}, med) == "no apoyada"
    assert aa.verdict_mtb2({"E15.5": float("nan"), "E18.5": 0.0}, med) == "no evaluable"


# ---------------------------------------------------------------- puertas y sensibilidad
def test_gate_d_and_tangent():
    assert aa.gate_d(aa.D_REF + 0.00009)["passed"]
    assert not aa.gate_d(aa.D_REF + 0.00011)["passed"]
    mean = lm.preshape(np.random.default_rng(6).normal(size=(K, 3)))
    near = {"E15.5": mean * 10, "E18.5": mean * 10 + 1e-3}
    assert aa.gate_tangent(near, mean)["passed"]
    far = {"E15.5": mean, "E18.5": np.random.default_rng(7).normal(size=(K, 3))}
    assert not aa.gate_tangent(far, mean)["passed"]


def test_split_halves_fixed_and_disjoint():
    h1, h2 = aa.split_halves(398)
    g1, g2 = aa.split_halves(398)
    assert len(h1) == len(h2) == 199
    assert not set(h1) & set(h2)
    assert np.array_equal(h1, g1) and np.array_equal(h2, g2)


def test_sensitivities_run_and_agree_on_clean_data():
    rng = np.random.default_rng(8)
    a15, a18 = _atlases(rng)
    pub15, pub18 = _specimens(rng, a15, 20), _specimens(rng, a18, 30)
    atlas = {"E15.5": a15, "E18.5": a18}
    s, res = _run(pub15, pub18, a15, a18, n_boot=50)
    sg = aa.sensitivity_in_gpa(pub15, pub18, atlas)
    assert abs(sg["r"] - res["point"]["r"]) < 0.05
    rg = aa.sensitivity_regpa(pub15, pub18, atlas, n_boot=10)
    assert rg["ci"][1] < 0.25
    t15a, t18a = aa.project_to_tangent(a15, s["mean"]), aa.project_to_tangent(a18, s["mean"])
    halves = aa.sensitivity_halves(s["t15"], s["t18"], t15a, t18a, n_boot=20)
    assert [h["n18"] for h in halves] == [15, 15]


def test_script_gates_and_analysis_on_synthetic_inputs():
    rng = np.random.default_rng(9)
    a15, a18 = _atlases(rng)
    pub15, pub18 = _specimens(rng, a15, 10), _specimens(rng, a18, 14)
    g = mtb.run_gates(pub15, pub18, {"E15.5": a15, "E18.5": a18})
    assert g["gates"]["G0-p"]["passed"] and g["gates"]["G0-t"]["passed"]
    assert not g["gates"]["G0-d‴"]["passed"]           # |d| sintética ≠ la de v2: la puerta no se fuerza
    assert not g["passed"]
