"""Verificación de la cadena de registro (``scripts/verify_registration_chain.py``). Sin datos reales.

Qué falla si ``apply`` deja de componer de izquierda a derecha (la nota VERIFICACION_REGISTRO compara los dos órdenes
de la composición afín/B-spline con esta función), si ``err_mm`` deja de medir la distancia euclídea por punto, o si
``_mi`` (la información mutua que usa ``geometry``) deja de preferir la alineación correcta.
"""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

sitk = pytest.importorskip("SimpleITK")

_spec = importlib.util.spec_from_file_location(
    "verify_registration_chain", Path(__file__).resolve().parents[1] / "scripts" / "verify_registration_chain.py")
vrc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vrc)


def test_apply_composes_left_to_right():
    shift = sitk.TranslationTransform(3, (1.0, 0.0, 0.0))
    scale = sitk.ScaleTransform(3, (2.0, 2.0, 2.0))
    p = np.array([[1.0, 1.0, 1.0]])
    assert np.allclose(vrc.apply([shift, scale], p), [[4.0, 2.0, 2.0]])   # escala(traslación(p))
    assert np.allclose(vrc.apply([scale, shift], p), [[3.0, 2.0, 2.0]])   # traslación(escala(p))


def test_err_mm_is_the_per_point_euclidean_distance():
    a = np.zeros((4, 3))
    b = np.array([[3.0, 4.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, 2.0], [0.0, 0.0, 3.0]])
    e = vrc.err_mm(a, b)
    assert e["median_mm"] == pytest.approx(2.5)
    assert e["p90_mm"] == pytest.approx(np.percentile([5.0, 1.0, 2.0, 3.0], 90))


def test_bspline_displacement_is_zero_for_an_untouched_bspline():
    img = sitk.Image([10, 10, 10], sitk.sitkFloat32)
    bs = sitk.BSplineTransformInitializer(img, [2, 2, 2], order=3)
    d = vrc.bspline_displacement(bs, np.array([[2.0, 3.0, 4.0], [5.0, 5.0, 5.0]]))
    assert d == (0.0, 0.0)


def test_mutual_information_is_better_at_the_true_alignment():
    rng = np.random.default_rng(0)
    arr = np.zeros((24, 24, 24), np.float32)
    arr[6:18, 8:16, 5:19] = 1.0
    arr += rng.normal(0, 0.05, arr.shape).astype(np.float32)
    img = sitk.GetImageFromArray(arr)
    aligned = vrc._mi(img, img, sitk.AffineTransform(3))
    off = sitk.AffineTransform(3)
    off.SetTranslation((4.0, 0.0, 0.0))
    assert aligned < vrc._mi(img, img, off)   # Mattes MI de ITK: más negativo es mejor
