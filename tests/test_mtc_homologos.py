"""MT-C (PREREGISTRO_HOMOLOGOS.md): subconjunto de landmarks, contribución por landmark, concentración y orden.

Qué haría fallar cada prueba: si el subconjunto no tomara las primeras filas, MT-C no mediría los landmarks
anatómicos; si las cᵢ no sumaran 1 o no detectaran una diferencia construida en pocos landmarks, MT-C2 no mediría
concentración; si la comprobación de orden no fallara al permutar filas, G0-o no protegería contra un orden
equivocado; y si MT-B cambiara sus valores por defecto, dejaría de ser reproducible. Sin datos reales.
"""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from geovida import atlas_anchor as aa

_spec = importlib.util.spec_from_file_location(
    "mtc_homologos", Path(__file__).resolve().parents[1] / "scripts" / "mtc_homologos.py")
mtc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mtc)

K = 40


def _rot(rng):
    q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    return q if np.linalg.det(q) > 0 else -q


def _specimens(rng, base, n, noise=0.02):
    return np.stack([rng.uniform(0.5, 2.0) * (base + noise * rng.normal(size=base.shape)) @ _rot(rng)
                     + rng.normal(size=3) for _ in range(n)])


def _atlases(rng, shift=0.25, only=None):
    a15 = rng.normal(size=(K, 3))
    delta = shift * rng.normal(size=(K, 3))
    if only is not None:
        mask = np.zeros(K, bool)
        mask[list(only)] = True
        delta[~mask] = 0.0
    return a15, a15 + delta


def test_subset_rows_takes_first_rows():
    x = np.arange(2 * 30 * 3, dtype=float).reshape(2, 30, 3)
    assert np.array_equal(aa.subset_rows(x, 22), x[:, :22])
    assert np.array_equal(aa.subset_rows(x[0], 25), x[0, :25])
    with pytest.raises(ValueError):
        aa.subset_rows(x, 31)


def test_contributions_sum_to_one_and_detect_concentration():
    rng = np.random.default_rng(0)
    a15, a18 = _atlases(rng, shift=0.3, only=[1, 4, 7])          # la diferencia vive en 3 de 22 landmarks
    a15, a18 = a15[:22], a18[:22]
    pub15, pub18 = _specimens(rng, a15, 40), _specimens(rng, a18, 60)
    s = aa.shape_space(pub15, pub18)
    t15a, t18a = aa.project_to_tangent(a15, s["mean"]), aa.project_to_tangent(a18, s["mean"])
    dec = aa.decompose(s["t15"], s["t18"], t15a, t18a)
    c = aa.landmark_contributions(dec["a"], dec["d"], s["t15"], s["t18"])
    assert abs(sum(c["c"]) - 1) < 1e-12
    assert len(c["c"]) == 22 and c["uniform_share"] == pytest.approx(5 / 22)
    assert c["verdict"] == "apoyada" and c["top_share"] > 0.5
    assert {2, 5, 8} <= set(c["top_landmarks"])               # índices desde 1


def test_spread_diffuse_difference_is_not_concentrated():
    rng = np.random.default_rng(1)
    a15 = rng.normal(size=(22, 3))
    a18 = a15 + 0.05 * np.ones((22, 3)) * rng.choice([-1, 1], size=(22, 3))   # todos los landmarks por igual
    pub15, pub18 = _specimens(rng, a15, 40), _specimens(rng, a18, 60)
    s = aa.shape_space(pub15, pub18)
    t15a, t18a = aa.project_to_tangent(a15, s["mean"]), aa.project_to_tangent(a18, s["mean"])
    dec = aa.decompose(s["t15"], s["t18"], t15a, t18a)
    assert aa.landmark_contributions(dec["a"], dec["d"], s["t15"], s["t18"])["verdict"] == "no apoyada"


def test_verdict_mtc2_edges():
    assert aa.verdict_mtc2(0.50) == "apoyada"
    assert aa.verdict_mtc2(0.4999) == "no apoyada"
    assert aa.verdict_mtc2(float("nan")) == "no evaluable"


def test_gate_order_detects_permutation_and_degenerate_triangles():
    rng = np.random.default_rng(2)
    atlas = {s: rng.normal(size=(K, 3)) for s in aa.STAGES}
    same = {s: atlas[s] + 1e-6 for s in aa.STAGES}
    g = aa.gate_order(atlas, same)
    assert g["passed"] and g["passed_a"] and g["passed_b"]
    perm = {s: atlas[s][np.r_[1, 0, 2:K]] for s in aa.STAGES}      # dos filas cambiadas
    assert not aa.gate_order(atlas, perm)["passed"]
    flat = {s: atlas[s].copy() for s in aa.STAGES}
    flat["E15.5"][20] = flat["E15.5"][19]                          # cara (20, 19, 21) degenerada
    g2 = aa.gate_order(flat, None)
    assert not g2["passed"] and g2["compared_with_github"] is False


def test_patch_triangles_are_the_21_published_faces():
    assert len(aa.PATCH_TRIANGLES) == 21
    assert {i for t in aa.PATCH_TRIANGLES for i in t} == set(range(3, 23))


def test_mtb_defaults_unchanged():
    assert aa.SEED == 20261124 and aa.N_BOOT == 2000
    mean = np.eye(3)[[0, 1, 2, 0]] / 2.0
    atlas = {s: mean * 3 for s in aa.STAGES}
    assert aa.gate_tangent(atlas, mean)["limit"] == aa.RHO_MAX_REF


def test_script_gates_and_analysis_on_synthetic_inputs():
    rng = np.random.default_rng(3)
    a15, a18 = _atlases(rng)
    pub15, pub18 = _specimens(rng, a15, 12), _specimens(rng, a18, 16)
    atlas = {"E15.5": a15, "E18.5": a18}
    g = mtc.run_gates(pub15, pub18, atlas, {s: atlas[s].copy() for s in aa.STAGES})
    assert g["gates"]["G0-o"]["passed"] and g["gates"]["G0-p22"]["passed"]
    assert g["n_landmarks"] == 22
    res = mtc._analysis_n(pub15, pub18, atlas, 22, n_boot=30)
    assert res["n_landmarks"] == 22 and len(res["contributions"]["c"]) == 22
    assert res["seed"] == aa.SEED_MTC
