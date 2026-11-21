"""Comparación con SimpleITK en casos pequeños (se omite si SimpleITK no está instalado; la CI no lo exige)."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("SimpleITK")

_spec = importlib.util.spec_from_file_location("compare_sitk", Path(__file__).resolve().parents[1] / "scripts" / "compare_sitk.py")
cs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cs)


def test_volume_and_components_match_itk_with_anisotropic_spacing():
    m = np.zeros((6, 7, 8), bool)
    m[1:3, 1:3, 1:3] = True
    m[4, 5, 6] = True                 # segundo componente, aislado
    m[3, 3, 3] = True                 # toca al primero solo por un vértice
    r = cs.row(m, (2.0, 1.0, 0.5))
    assert abs(r["itk_volume"] - r["volume"]) < 1e-12
    assert (r["itk_b0_6"], r["b0_6"]) == (3, 3)
    assert (r["itk_b0_26"], r["b0_26"]) == (2, 2)


def test_itk_area_is_close_to_crofton_on_a_ball():
    from geovida import reference as ref
    from geovida.phantoms import make_phantom
    ph = make_phantom("ball", 30.0)
    mask, sp = ref.voxelize(ph, 1.0)
    r = cs.row(mask, sp)
    assert abs(r["itk_area"] / ph.truth.surface_area - 1) < 0.05
    assert abs(r["itk_area"] / r["crofton"] - 1) < 0.05
