"""MT-A (``geovida.atlas_effect``): geometría, registro con deformación conocida y estadística de §5.

Fantomas sintéticos; ninguna imagen real. Qué falla si:
* ``to_sitk`` no reproduce la afín índice→mundo de MINC (ejes invertidos, signos, espaciado);
* ``downsample`` desplaza el vóxel nuevo respecto del centro del bloque;
* el registro no recupera una transformada conocida o compone afín y B-spline en el orden equivocado;
* f, los veredictos o la puerta G1 no hacen lo que dice el preregistro.
"""
import math

import numpy as np
import pytest

from geovida import atlas_effect as ae

sitk = pytest.importorskip("SimpleITK")


# ---------------------------------------------------------------- geometría
def test_to_sitk_reproduces_the_minc_affine():
    # ejes permutados, uno invertido, espaciado anisótropo y origen arbitrario
    a = np.eye(4)
    a[:3, :3] = np.array([[0.0, 0.0, 0.7], [0.0, -0.6, 0.0], [0.5, 0.0, 0.0]])
    a[:3, 3] = [-3.0, 12.5, 7.25]
    arr = np.zeros((5, 6, 7), np.float32)
    img = ae.to_sitk(arr, a)
    assert img.GetSize() == (7, 6, 5)
    for ijk in [(0, 0, 0), (4, 5, 6), (2, 1, 3)]:
        world = a @ np.r_[ijk, 1.0]
        itk = img.TransformContinuousIndexToPhysicalPoint(tuple(float(x) for x in ijk[::-1]))
        assert np.allclose(itk, world[:3])


def test_to_sitk_rejects_non_orthogonal_directions():
    a = np.eye(4)
    a[0, 1] = 0.5
    with pytest.raises(ValueError):
        ae.to_sitk(np.zeros((3, 3, 3), np.float32), a)


def test_downsample_keeps_the_block_centre():
    rng = np.random.default_rng(0)
    arr = rng.random((9, 8, 10)).astype(np.float32)
    a = np.eye(4)
    a[:3, :3] = np.diag([0.5, -0.25, 2.0])
    a[:3, 3] = [1.0, 2.0, 3.0]
    x, a2 = ae.downsample(arr, a, 2)
    assert x.shape == (4, 4, 5)
    assert math.isclose(float(x[1, 2, 3]), float(arr[2:4, 4:6, 6:8].mean()), rel_tol=1e-6)
    block_centre = a @ np.r_[2.5, 4.5, 6.5, 1.0]
    assert np.allclose(a2 @ np.r_[1, 2, 3, 1.0], block_centre)


def test_fraction_inside_counts_points_over_the_threshold():
    arr = np.zeros((10, 10, 10), np.float32)
    arr[2:8, 2:8, 2:8] = 1.0
    pts = np.array([[5, 5, 5], [3, 4, 6], [0, 0, 0], [9, 9, 9]], float)   # afín identidad: mundo = índice
    assert ae.fraction_inside(arr, np.eye(4), pts) == 0.5
    assert ae.fraction_inside(arr, np.eye(4), np.array([[50.0, 0, 0]])) == 0.0


# ---------------------------------------------------------------- registro con deformación conocida
def _phantom(n=48):
    from scipy.ndimage import gaussian_filter
    z, y, x = np.mgrid[:n, :n, :n].astype(float)
    c = (n - 1) / 2
    body = ((z - c) / 15) ** 2 + ((y - c) / 11) ** 2 + ((x - c) / 8) ** 2 <= 1
    knob = (z - c - 10) ** 2 + (y - c + 6) ** 2 + (x - c - 3) ** 2 <= 16       # asimetrías para fijar la rotación
    tail = (z - c + 12) ** 2 + (y - c - 5) ** 2 + (x - c + 2) ** 2 <= 9
    img = gaussian_filter((body * 1.0 + knob * 0.6 + tail * 0.8).astype(np.float32), 1.0)
    return img


def _interior_points(n=48):
    c = (n - 1) / 2
    rng = np.random.default_rng(1)
    pts = c + rng.uniform(-6, 6, size=(40, 3))
    return pts                                             # afín identidad: mundo = índice (i, j, k)


def _truth_affine():
    t = sitk.AffineTransform(3)
    ang = math.radians(6)
    r = np.array([[math.cos(ang), -math.sin(ang), 0], [math.sin(ang), math.cos(ang), 0], [0, 0, 1]]) * 1.05
    t.SetMatrix(tuple(r.ravel()))
    t.SetCenter((23.5, 23.5, 23.5))
    t.SetTranslation((1.5, -1.0, 2.0))
    return t


def _residual(truth, found, pts):
    """M(x) = F(S(x)); el registro halla T con M(T(p)) ≈ F(p), así que S(T(p)) ≈ p."""
    q = ae.transfer_points(found, pts)
    back = ae.transfer_points(truth, q)
    return np.linalg.norm(back - pts, axis=1)


def test_affine_registration_recovers_a_known_transform():
    fixed = ae.to_sitk(_phantom(), np.eye(4))
    truth = _truth_affine()
    moving = sitk.Resample(fixed, truth)
    tx, info = ae.register(fixed, moving, affine_only=True)
    res = _residual(truth, tx, _interior_points())
    assert np.median(res) < 0.3 and res.max() < 0.8, (np.median(res), res.max(), info)


def test_bspline_registration_recovers_affine_plus_smooth_deformation():
    fixed = ae.to_sitk(_phantom(), np.eye(4))
    aff = _truth_affine()
    bs = sitk.BSplineTransformInitializer(fixed, [3, 3, 3], order=3)
    p = np.array(bs.GetParameters())
    p[:] = np.random.default_rng(2).normal(0, 3.0, p.size)       # parte no lineal ≈ 1,4 vóxeles (mediana)
    bs.SetParameters(tuple(p))
    truth = sitk.CompositeTransform([aff, bs])                    # S(x) = afín(B-spline(x))
    moving = sitk.Resample(fixed, truth)
    pts = _interior_points()
    nonlinear = np.linalg.norm(ae.transfer_points(truth, pts) - ae.transfer_points(aff, pts), axis=1)
    assert np.median(nonlinear) > 1.0                             # la prueba exige corregir algo apreciable
    tx_aff, _ = ae.register(fixed, moving, affine_only=True)
    tx, info = ae.register(fixed, moving, mesh=4)
    res_aff, res = _residual(truth, tx_aff, pts), _residual(truth, tx, pts)
    wrong = sitk.CompositeTransform([tx.GetNthTransform(1), tx.GetNthTransform(0)])
    res_wrong = _residual(truth, wrong, pts)
    assert np.median(res) < 0.35, (np.median(res), info)
    assert np.median(res) < 0.6 * np.median(res_aff)              # la parte no lineal corrige de verdad
    assert np.median(res) < np.median(res_wrong)                  # y el orden de composición importa


def test_composite_applies_the_last_transform_first():
    """``register`` devuelve CompositeTransform([afín, B-spline]) suponiendo que aplica primero el B-spline.
    Se comprueba con transformadas grandes, donde el orden cambia mucho el resultado."""
    a = sitk.Euler3DTransform((0, 0, 0), 0.0, 0.0, math.radians(40), (5.0, 0, 0))
    b = sitk.TranslationTransform(3, (0.0, 7.0, 0.0))
    p = (3.0, 1.0, 2.0)
    expected = a.TransformPoint(b.TransformPoint(p))
    other = b.TransformPoint(a.TransformPoint(p))
    got = sitk.CompositeTransform([a, b]).TransformPoint(p)
    assert np.allclose(got, expected) and not np.allclose(got, other, atol=0.5)


# ---------------------------------------------------------------- estadística de §5
def _configs(base, shift, n, rng, noise=0.003):
    return np.stack([base + shift + rng.normal(0, noise, base.shape) for _ in range(n)])


@pytest.mark.parametrize("a", [0.7, 0.05])
def test_atlas_effect_recovers_the_fraction_of_d(a):
    rng = np.random.default_rng(3)
    base = rng.normal(0, 1, (30, 3))
    d = rng.normal(0, 0.05, (30, 3))
    pub15, pub18 = _configs(base, 0, 60, rng), _configs(base, d, 60, rng)
    spec = [base + rng.normal(0, 0.01, base.shape) + (d if i % 2 else 0) for i in range(20)]
    l15 = np.stack([s + rng.normal(0, 0.002, base.shape) for s in spec])
    l18 = np.stack([s + a * d + rng.normal(0, 0.002, base.shape) for s in spec])
    stage = np.array(["E18.5" if i % 2 else "E15.5" for i in range(20)])
    r = ae.atlas_effect(pub15, pub18, l15, l18, stage, n_boot=300)
    assert abs(r["mta1"]["f"] - a) < 0.08, r["mta1"]
    assert r["mta1"]["verdict"] == ("apoyada" if a > 0.5 else "refutada")
    assert r["mta2"]["angle_deg"] < 45                              # mismo desplazamiento en los dos estadios
    assert r["mta3"]["angle_to_d_deg"] < 30


def test_verdict_thresholds_follow_the_preregistration():
    assert ae.verdict_mta1(0.50, 0.9) == "apoyada"
    assert ae.verdict_mta1(0.10, 0.25) == "refutada"
    assert ae.verdict_mta1(0.30, 0.70) == "no concluyente"
    assert ae.verdict_mta1(float("nan"), 0.3) == "no evaluable"


def test_gate_g1_passes_only_when_transfer_error_is_below_biological_spread():
    rng = np.random.default_rng(4)
    base = rng.normal(0, 1, (25, 3))
    pub = _configs(base, 0, 10, rng, noise=0.05)
    good = np.stack([p + rng.normal(0, 0.005, p.shape) for p in pub])
    bad = np.stack([p + rng.normal(0, 0.2, p.shape) for p in pub])
    groups = {"E15.5": pub[:5], "E18.5": pub[5:]}
    assert ae.gate_g1(good, pub, groups)["passed"]
    assert not ae.gate_g1(bad, pub, groups)["passed"]


def test_published_direction_length():
    rng = np.random.default_rng(5)
    base = rng.normal(0, 1, (30, 3))
    d = rng.normal(0, 0.05, (30, 3))
    r = ae.published_direction(_configs(base, 0, 40, rng), _configs(base, d, 40, rng))
    assert r["d_length"] > 0 and r["rho_max"] < 0.2
