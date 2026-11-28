"""FI-1 (PREREGISTRO_FOTO_IMPRESION.md): medida sobre impresiones SINTÉTICAS con perspectiva conocida.

Qué haría fallar cada prueba: si la homografía no invirtiera una perspectiva conocida, cualquier distancia saldría
deformada; si la calibración con la escala no diera los mm correctos, todas las medidas tendrían un sesgo; si no
corregir la perspectiva no empeorara el error, FI-1c no mediría nada; si la curvatura de un borde no se detectara,
G0-homografía no protegería de una foto de papel doblado; si el análisis no reconociera un error construido de ≈ 1 %
(apoyada) o de ≈ 15 % (refutada), los veredictos no corresponderían al preregistro. Sin imágenes humanas.
"""
import math

import numpy as np
import pytest

from geovida import print_measure as pm

W, H = 120.0, 90.0          # recuadro de la impresión, en mm


def _random_h(rng, strength=0.25):
    """Perspectiva de una foto tomada en ángulo: lleva el recuadro en mm a píxeles de la foto."""
    src = np.array([[0, 0], [W, 0], [W, H], [0, H]], float)
    dst = src * 20 + np.array([300, 200]) + rng.uniform(-strength, strength, size=(4, 2)) * 20 * W
    return pm.homography(src, dst)


def _print(rng):
    ticks = np.array([[W - 5, 5 + 10 * k] for k in range(8)], float)          # escala de 1 cm en el borde
    pairs, values = [], []
    for _ in range(5):
        p = rng.uniform([10, 10], [W - 20, H - 10])
        ang = rng.uniform(0, 2 * math.pi)
        length = rng.uniform(8, 40)
        q = p + length * np.array([math.cos(ang), math.sin(ang)])
        q = np.clip(q, 5, [W - 10, H - 5])
        pairs.append((p, q))
        values.append(float(np.linalg.norm(q - p)))
    return ticks, pairs, values


def _measure(rng, Hph, ticks, pairs, noise_px=0.0, correct=True, aspect=W / H):
    corners_mm = np.array([[0, 0], [W, 0], [W, H], [0, H]], float)
    corners_ph = pm.warp_points(Hph, corners_mm)
    jitter = lambda x: x + rng.normal(0, noise_px, size=np.shape(x))   # noqa: E731
    c = jitter(corners_ph)
    if aspect is None:
        aspect = pm.photo_aspect_estimate(c)
    R = pm.rectify(c, aspect) if correct else np.eye(3)
    t = pm.warp_points(R, jitter(pm.warp_points(Hph, ticks)))
    k = pm.scale_mm_per_unit(t)
    out = []
    for p, q in pairs:
        pp, qq = pm.warp_points(R, jitter(pm.warp_points(Hph, np.array([p, q]))))
        out.append(pm.distance_mm(pp, qq, k))
    return out, t


def test_homography_recovers_known_points():
    rng = np.random.default_rng(1)
    Hph = _random_h(rng)
    pts = rng.uniform(0, 100, size=(10, 2))
    back = pm.warp_points(np.linalg.inv(Hph), pm.warp_points(Hph, pts))
    np.testing.assert_allclose(back, pts, atol=1e-8)
    est = pm.homography(pts, pm.warp_points(Hph, pts))
    np.testing.assert_allclose(est / est[2, 2], Hph / Hph[2, 2], rtol=1e-6, atol=1e-9)
    with pytest.raises(ValueError):
        pm.homography(pts[:3], pts[:3])


def test_rectified_distances_match_printed_values():
    rng = np.random.default_rng(2)
    Hph = _random_h(rng)
    ticks, pairs, values = _print(rng)
    meas, t = _measure(rng, Hph, ticks, pairs)
    np.testing.assert_allclose(meas, values, rtol=1e-6)
    assert pm.scale_cv(t) < 1e-6


def test_without_perspective_correction_error_is_larger():
    rng = np.random.default_rng(3)
    errs_c, errs_n = [], []
    for _ in range(10):
        Hph = _random_h(rng, strength=0.3)
        ticks, pairs, values = _print(rng)
        mc, _ = _measure(rng, Hph, ticks, pairs, noise_px=0.5, correct=True)
        mn, _ = _measure(rng, Hph, ticks, pairs, noise_px=0.5, correct=False)
        errs_c += list(np.abs(pm.relative_errors(mc, values)))
        errs_n += list(np.abs(pm.relative_errors(mn, values)))
    assert np.median(errs_c) < 0.01 and np.median(errs_n) > 2 * np.median(errs_c)


def test_aspect_from_the_photo_biases_distances():
    rng = np.random.default_rng(5)
    errs_ruler, errs_photo = [], []
    for _ in range(10):
        Hph = _random_h(rng, strength=0.3)
        ticks, pairs, values = _print(rng)
        mr, _ = _measure(rng, Hph, ticks, pairs, aspect=W / H)
        mp, _ = _measure(rng, Hph, ticks, pairs, aspect=None)
        errs_ruler += list(np.abs(pm.relative_errors(mr, values)))
        errs_photo += list(np.abs(pm.relative_errors(mp, values)))
    assert np.median(errs_ruler) < 1e-6 and np.median(errs_photo) > 0.01
    with pytest.raises(ValueError):
        pm.rectify(np.zeros((4, 2)) + np.arange(4)[:, None], aspect=0.0)


def test_scale_cv_and_edge_bend_detect_problems():
    ticks = np.array([[0, 10 * k] for k in range(6)], float)
    assert pm.scale_cv(ticks) == pytest.approx(0.0)
    bad = ticks.copy()
    bad[3, 1] += 3.0
    assert pm.scale_cv(bad) > pm.SCALE_CV_MAX
    corners = np.array([[0, 0], [100, 0], [100, 80], [0, 80]], float)
    mids = np.array([[50, 0], [100, 40], [50, 80], [0, 40]], float)
    assert pm.edge_bend_deg(corners, mids) == pytest.approx(0.0, abs=1e-9)
    bent = mids.copy()
    bent[0, 1] = 3.0                                    # borde superior curvado 3 unidades en 100
    assert pm.edge_bend_deg(corners, bent) > pm.BEND_MAX_DEG


def _rows(rng, rel_sd, bias=0.0, n_prints=3, n_photos=3, n_pairs=5, n_rep=3):
    rows = []
    for pr in range(n_prints):
        truth = rng.uniform(8, 40, n_pairs)
        for ph in range(n_photos):
            photo_shift = rng.normal(0, rel_sd / 2)
            for pa in range(n_pairs):
                for rep in range(n_rep):
                    m = truth[pa] * (1 + bias + photo_shift + rng.normal(0, rel_sd))
                    rows.append({"print": pr, "photo": ph, "pair": pa, "repeat": rep,
                                 "measured_mm": m, "printed_mm": truth[pa]})
    return rows


def test_analyze_verdicts():
    rng = np.random.default_rng(4)
    good = pm.analyze(_rows(rng, 0.01), n_boot=300)
    assert good["verdict_fi1a"] == "apoyada" and good["verdict_fi1b"] == "apoyada"
    assert good["n_measurements"] == 135 and good["n_prints"] == 3 and good["n_photos"] == 9
    bad = pm.analyze(_rows(rng, 0.02, bias=0.15), n_boot=300)
    assert bad["verdict_fi1a"] == "refutada" and bad["verdict_fi1b"] == "no apoyada"
    assert pm.verdict_fi1a(0.03, 0.08) == "no concluyente"
    with pytest.raises(ValueError):
        pm.relative_errors([1.0], [0.0])


def test_constants_match_preregistration():
    assert pm.SEED_FI1 == 20261127 and pm.N_BOOT == 2000 and pm.TICK_MM == 10.0
    assert (pm.SUPPORT_MAX, pm.REFUTE_MIN, pm.BIAS_BAND) == (0.05, 0.10, 0.05)
    assert pm.SCALE_CV_MAX == 0.05 and pm.BEND_MAX_DEG == 2.0
