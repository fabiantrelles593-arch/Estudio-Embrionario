"""MT-A v3 (PREREGISTRO_ATLAS_v3.md): muestra, caja de cabeza, inicialización, registro con máscara y puertas.

Qué haría fallar cada prueba: si la muestra repitiera especímenes de v2 o mezclara piloto y confirmatorio, el
procedimiento se elegiría y evaluaría con los mismos datos; si el recorte moviera la geometría del mundo, los landmarks
del atlas caerían en otro sitio; si T₀ no fuera la identidad en el registro propio, v3 repetiría el error de la
inicialización por momentos; si la máscara no excluyera lo de fuera de la cabeza, el registro volvería a seguir al
cuerpo; si la regla de S o G1′ no fuera la escrita, el veredicto no sería el preregistrado; y si ``register`` cambiara
sus valores por defecto, v2 dejaría de ser reproducible. Sin datos reales.
"""
import importlib.util
import inspect
from pathlib import Path

import numpy as np
import pytest

from geovida import atlas_effect as ae

_spec = importlib.util.spec_from_file_location("mta_v3", Path(__file__).resolve().parents[1] / "scripts" / "mta_v3.py")
mta = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mta)


# ---------------------------------------------------------------- muestra
def _qc():
    s = {"E15.5": [f"IMPC_E15.5_{i:04d}" for i in range(60)], "E18.5": [f"IMPC_E18.5_{i:04d}" for i in range(60)]}
    passed = {n: (i % 3 != 0) for st in s for i, n in enumerate(s[st])}            # 40 cumplen por estadio
    v2 = {st: [n for n in s[st] if passed[n]][:20] for st in s}                    # v2 usó 20 de ellos
    return s, passed, v2


def test_sample_is_new_disjoint_reproducible_and_from_passers():
    s, passed, v2 = _qc()
    a, b = mta.draw(s, passed, v2), mta.draw(s, passed, v2)
    assert a["pilot"] == b["pilot"] and a["confirm"] == b["confirm"] and a["sample_sha256"] == b["sample_sha256"]
    for st in mta.STAGES:
        p, c = a["pilot"][st], a["confirm"][st]
        assert len(p) == 2 and len(c) == 18 and not set(p) & set(c)
        assert all(passed[n] for n in p + c) and not set(p + c) & set(v2[st])
    assert mta.draw(s, passed, v2, seed=1)["confirm"] != a["confirm"]


def test_sample_fails_if_too_few_remain():
    s, passed, v2 = _qc()
    v2 = {st: [n for n in s[st] if passed[n]][:30] for st in s}                    # quedan 10 < 20
    with pytest.raises(ValueError):
        mta.draw(s, passed, v2)


def test_g0a4_needs_all_40():
    s, passed, v2 = _qc()
    smp = mta.draw(s, passed, v2)
    within = {n: 1.0 for n in passed}
    assert mta.g0a4(smp, passed, within)["passed"]
    bad = dict(passed, **{smp["confirm"]["E18.5"][0]: False})
    assert not mta.g0a4(smp, bad, within)["passed"]


# ---------------------------------------------------------------- caja de cabeza y geometría
def _affine(spacing=0.5, origin=(1.0, -2.0, 3.0)):
    a = np.eye(4)
    a[:3, :3] *= spacing
    a[:3, 3] = origin
    return a


def test_head_box_and_mask():
    pts = np.array([[0.0, 0.0, 0.0], [2.0, 1.0, 3.0]])
    lo, hi = ae.head_box(pts, 1.0)
    assert np.allclose(lo, [-1, -1, -1]) and np.allclose(hi, [3, 2, 4])
    m = ae.box_mask((10, 10, 10), np.eye(4), [2, 2, 2], [4, 4, 4])
    assert m.sum() == 27 and m[3, 3, 3] == 1 and m[1, 3, 3] == 0


def test_crop_keeps_world_geometry():
    rng = np.random.default_rng(0)
    arr = rng.random((20, 22, 24)).astype(np.float32)
    a = _affine()
    lo, hi = np.array([3.0, 0.0, 6.0]), np.array([6.0, 4.0, 9.0])
    sub, b = ae.crop_to_box(arr, a, lo, hi)
    w = np.array([4.5, 2.0, 7.0])                                                   # un centro de vóxel en la caja
    i_full = np.rint(ae.world_to_index(w[None], a)[0]).astype(int)
    i_sub = np.rint(ae.world_to_index(w[None], b)[0]).astype(int)
    assert sub[tuple(i_sub)] == arr[tuple(i_full)]
    assert sub.shape == (7, 9, 7)
    with pytest.raises(ValueError):
        ae.crop_to_box(arr, a, [100, 100, 100], [101, 101, 101])


def test_g0m_row():
    tags = np.array([[5.0, 5.0, 5.0], [8.0, 9.0, 7.0]])
    assert mta.g0m_row("E15.5", tags, (40, 40, 40), _affine(0.5, (0, 0, 0)))["passed"]     # imagen de 0 a 19,5 mm
    assert not mta.g0m_row("E15.5", tags, (20, 20, 20), _affine(0.5, (0, 0, 0)))["passed"]  # la caja se sale


# ---------------------------------------------------------------- inicialización
def test_landmark_affine_recovers_known_affine_and_identity():
    rng = np.random.default_rng(1)
    src = rng.normal(size=(50, 3))
    m = np.array([[1.1, 0.1, 0.0, 0.5], [0.0, 0.9, 0.2, -1.0], [0.05, 0.0, 1.0, 2.0], [0, 0, 0, 1]])
    dst = src @ m[:3, :3].T + m[:3, 3]
    assert np.allclose(ae.landmark_affine(src, dst), m)
    assert np.allclose(ae.landmark_affine(src, src), np.eye(4))
    with pytest.raises(ValueError):
        ae.landmark_affine(src[:3], dst[:3])


def test_initial_transform_is_identity_for_own_atlas_and_maps_atlas_landmarks_otherwise():
    pytest.importorskip("SimpleITK")
    rng = np.random.default_rng(2)
    t15 = rng.normal(size=(30, 3))
    t18 = t15 * 1.2 + np.array([0.3, -0.2, 1.0])
    own = mta.initial_transform(t15, t15, True)
    assert np.allclose(ae.transfer_points(own, t15), t15)
    cross = mta.initial_transform(t18, t15, False)                                  # fija = atlas 18; móvil en rejilla 15
    assert np.allclose(ae.transfer_points(cross, t18), t15, atol=1e-9)


# ---------------------------------------------------------------- registro con máscara
def _blob(shape, centre, r=3.0):
    g = np.indices(shape).astype(float)
    d2 = sum((g[i] - centre[i]) ** 2 for i in range(3))
    return np.exp(-d2 / (2 * r ** 2)).astype(np.float32)


def test_mask_makes_registration_follow_only_the_head():
    sitk = pytest.importorskip("SimpleITK")
    shape = (40, 40, 40)
    head_f, body_f = (12, 20, 20), (30, 20, 20)
    fixed = _blob(shape, head_f) + 2.0 * _blob(shape, body_f, 4.0)
    moving = _blob(shape, (14, 20, 20)) + 2.0 * _blob(shape, (26, 20, 20), 4.0)   # cabeza +2, cuerpo −4 en i
    f, m = ae.to_sitk(fixed, np.eye(4)), ae.to_sitk(moving, np.eye(4))
    mk = sitk.GetImageFromArray(ae.box_mask(shape, np.eye(4), [6, 14, 14], [18, 26, 26]))
    mk.CopyInformation(f)
    res = ae.register_head(f, m, fixed_mask=mk, initial=ae.affine_to_sitk(np.eye(4)), meshes=(None,),
                           sampling_percentage=0.5)
    tx, info = res[None]
    p = ae.transfer_points(tx, np.array([head_f], float))[0]
    assert abs(p[0] - 14) < 0.5 and info["mesh"] is None                          # sigue a la cabeza, no al cuerpo


def test_register_head_returns_one_transform_per_candidate():
    sitk = pytest.importorskip("SimpleITK")
    shape = (24, 24, 24)
    f = ae.to_sitk(_blob(shape, (12, 12, 12), 4.0), np.eye(4))
    m = ae.to_sitk(_blob(shape, (13, 12, 12), 4.0), np.eye(4))
    mk = sitk.GetImageFromArray(np.ones(shape, np.uint8))
    mk.CopyInformation(f)
    res = ae.register_head(f, m, fixed_mask=mk, initial=ae.affine_to_sitk(np.eye(4)), meshes=(None, 4),
                           bspline_iterations=5, sampling_percentage=0.5)
    assert set(res) == {None, 4} and res[4][1]["mesh"] == 4 and "bspline_metric" in res[4][1]


def test_register_defaults_for_v2_are_unchanged():
    sig = inspect.signature(ae.register).parameters
    assert sig["mesh"].default == 8 and sig["bspline_iterations"].default == 100 and sig["seed"].default == 20261118
    src = inspect.getsource(ae.register)
    assert "MOMENTS" in src and "r.RANDOM" in src and "0.10" in src and "SetMetricFixedMask" not in src


# ---------------------------------------------------------------- puertas
def test_select_candidate_rule():
    ident = [0.05, 0.05, 0.05, 0.05]
    r = mta.select_candidate({"C1": [0.04, 0.04, 0.04, 0.06], "C2": [0.0395, 0.04, 0.04, 0.06],
                              "C3": [0.03, 0.03, 0.03, 0.03]}, ident)
    assert r["chosen"] == "C3"
    r = mta.select_candidate({"C1": [0.04, 0.04, 0.04, 0.06], "C2": [0.0395, 0.0395, 0.0395, 0.06],
                              "C3": [0.06] * 4}, ident)
    assert r["chosen"] == "C1"                                                    # empate a < 0,001: el más simple
    r = mta.select_candidate({"C1": [0.04, 0.04, 0.06, 0.06], "C2": [0.06] * 4, "C3": [0.04, float("nan"), 0.04, 0.04]},
                             ident)
    assert not r["passed"] and r["chosen"] is None                                # 2 de 4 no basta; NaN no es apto


def test_g1_identity_needs_both_references():
    rng = np.random.default_rng(3)
    base = rng.normal(size=(20, 3))
    pub = np.array([base + rng.normal(scale=0.05, size=base.shape) for _ in range(6)])
    by = {"E15.5": pub[:3], "E18.5": pub[3:]}
    good = pub + rng.normal(scale=0.001, size=pub.shape)
    ident = np.array([base] * 6)
    assert ae.gate_g1_identity(good, ident, pub, by)["passed"]
    assert not ae.gate_g1_identity(ident, good, pub, by)["passed"]                # peor que la identidad


def test_g2_and_g0t():
    confirm = {"E15.5": [f"a{i}" for i in range(18)], "E18.5": [f"b{i}" for i in range(18)]}
    rows = [{"specimen": n, "own": o, "candidate": "C1", "ok": True} for st in confirm for n in confirm[st]
            for o in (True, False)]
    assert mta.g2(rows, confirm, "C1")["passed"]
    rows = [r for r in rows if not (r["specimen"] in confirm["E18.5"][:4] and not r["own"])]
    assert not mta.g2(rows, confirm, "C1")["passed"]                              # 14 de 18 válidos
    assert mta.g0t(3600)["passed"] and not mta.g0t(3601)["passed"]
