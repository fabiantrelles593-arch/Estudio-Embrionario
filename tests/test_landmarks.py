"""Pruebas de geovida.landmarks con configuraciones sintéticas de forma conocida."""
import math

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from geovida import landmarks as lm

RNG = np.random.default_rng(7)
BASE = RNG.normal(size=(30, 3))


def _similar(x, seed):
    r = Rotation.random(random_state=seed).as_matrix()
    return 2.5 * x @ r.T + np.array([10.0, -3.0, 4.0])


def test_read_tag(tmp_path):
    p = tmp_path / "a.tag"
    p.write_text('MNI Tag Point File\nVolumes = 1;\n% comentario\n\nPoints =\n'
                 ' 1.5 2 3 0.12 1 1 "Marker"\n 4 5 6.25 0.12 1 1 "Marker"\n'
                 ' 7 8 9 0.12 1 1 "Marker";\n', encoding="utf-8")
    np.testing.assert_allclose(lm.read_tag(p), [[1.5, 2, 3], [4, 5, 6.25], [7, 8, 9]])
    bad = tmp_path / "b.tag"
    bad.write_text("otra cosa", encoding="utf-8")
    with pytest.raises(ValueError):
        lm.read_tag(bad)
    two = tmp_path / "c.tag"
    two.write_text("MNI Tag Point File\nVolumes = 2;\nPoints =\n 1 2 3 4 5 6;\n", encoding="utf-8")
    with pytest.raises(ValueError):
        lm.read_tag(two)


def test_centroid_size_units_and_scale():
    sq = np.array([[0, 0], [2, 0], [2, 2], [0, 2]], float)
    assert lm.centroid_size(sq) == pytest.approx(math.sqrt(8))
    assert lm.centroid_size(3 * sq + 5) == pytest.approx(3 * math.sqrt(8))


def test_distances_invariant_to_similarity():
    d = lm.procrustes_distances(BASE, _similar(BASE, 1))
    assert d["rho"] == pytest.approx(0, abs=1e-6)
    assert d["partial"] == pytest.approx(0, abs=1e-6)


def test_reflection_is_not_a_similarity():
    mirror = BASE * np.array([1, 1, -1])
    assert lm.procrustes_distances(BASE, mirror)["rho"] > 0.1


def test_distance_relations():
    other = BASE + RNG.normal(scale=0.3, size=BASE.shape)
    d = lm.procrustes_distances(BASE, other)
    t = math.cos(d["rho"])
    assert d["partial"] == pytest.approx(math.sqrt(2 * (1 - t)))
    assert d["full"] == pytest.approx(math.sin(d["rho"]))
    assert d["full"] <= d["partial"] <= d["rho"] + 1e-12


def test_full_distance_matches_scipy_reference():
    from scipy.spatial import procrustes

    for seed in range(5):
        other = _similar(BASE + np.random.default_rng(seed).normal(scale=0.2, size=BASE.shape), seed)
        _, _, disparity = procrustes(BASE, other)  # SciPy: 1 − (Σσ)², sin excluir reflexiones
        assert lm.procrustes_distances(BASE, other)["full"] ** 2 == pytest.approx(disparity, rel=1e-9)


def test_gpa_recovers_mean_shape():
    noisy = [_similar(BASE + RNG.normal(scale=0.02, size=BASE.shape), s) for s in range(25)]
    out = lm.gpa(noisy)
    assert out["converged"]
    assert lm.procrustes_distances(out["mean"], BASE)["rho"] < 0.01
    np.testing.assert_allclose(out["centroid_size"], 2.5 * lm.centroid_size(BASE), rtol=0.02)
    np.testing.assert_allclose([np.linalg.norm(a) for a in out["aligned"]], 1.0)
    np.testing.assert_allclose(out["aligned"].mean(axis=1), 0.0, atol=1e-12)


def test_tangent_coordinates_orthogonal_to_mean():
    noisy = [_similar(BASE + RNG.normal(scale=0.05, size=BASE.shape), s) for s in range(10)]
    out = lm.gpa(noisy)
    tan, rho_max = lm.tangent_coordinates(out["aligned"], out["mean"])
    assert tan.shape == (10, BASE.size)
    np.testing.assert_allclose(tan @ out["mean"].ravel(), 0.0, atol=1e-12)
    assert 0 < rho_max < 0.2


def test_allometry_recovers_direction():
    direction = RNG.normal(size=BASE.size)
    log_cs = np.linspace(0, 1, 40)
    shape = np.outer(log_cs, direction) + RNG.normal(scale=0.01, size=(40, BASE.size))
    v = lm.allometry_vector(shape, log_cs)
    assert lm.angle_deg(v, direction) < 2.0
    with pytest.raises(ValueError):
        lm.allometry_vector(shape, np.ones(40))


def test_angles_and_null():
    assert lm.angle_deg([1, 0], [0, 1]) == pytest.approx(90)
    assert lm.angle_deg([1, 0], [-1, 0]) == pytest.approx(180)
    # en dimensión alta dos rectas al azar son casi ortogonales
    assert lm.random_angle_quantile(500, 0.01) > 80
    assert lm.random_angle_quantile(2, 0.5) == pytest.approx(45, abs=1.5)


def test_correspondence_check():
    other = _similar(BASE + RNG.normal(scale=0.05, size=BASE.shape), 3)
    res = lm.correspondence_check(BASE, other)
    assert res["corresponds"]
    shuffled = other[RNG.permutation(len(other))]
    assert not lm.correspondence_check(BASE, shuffled)["corresponds"]
