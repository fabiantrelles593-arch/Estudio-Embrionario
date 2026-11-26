"""Pruebas de H24 (docs/h24/PREREGISTRO_H24.md): solo datos sintéticos."""
import math

import numpy as np
import pandas as pd
import pytest

from geovida import h20, h24


def _ball(r, n=48):
    z, y, x = np.mgrid[:n, :n, :n] - (n - 1) / 2
    return (x * x + y * y + z * z) <= r * r


def test_thresholds_keep_h20_proportions():
    tol = h24.TOL_VOXELS
    assert tol == 0.5
    for name in ("GREEN_FLIP", "GREEN_STAGE", "RED_FLIP", "RED_STAGE"):
        assert getattr(h24, name) / tol == pytest.approx(getattr(h20, name) / h20.TOLERANCE)


def test_area_of_ball_close_to_sphere():
    a = h24.area_voxels(_ball(15))
    assert a == pytest.approx(4 * math.pi * 15 ** 2, rel=0.05)
    assert h24.area_voxels(np.zeros((8, 8, 8), bool)) == 0.0


def test_one_voxel_shell_gives_about_one_voxel_error():
    ref, big = _ball(15), _ball(16)
    e = h24.boundary_error(big.sum(), ref.sum(), h24.area_voxels(ref))
    assert 0.9 < e < 1.15
    assert math.isnan(h24.boundary_error(10, 10, 0.0))


def test_signals_and_nan():
    s = h24.signals([100, 104, 98, 100, 101, 99, 100, 102], 110, 60.0)
    assert s["b_flip"] == pytest.approx(6 / 60)
    assert s["b_stage"] == pytest.approx(10 / 60)
    assert math.isnan(h24.signals([0] * 8, 5, 0.0)["b_flip"])
    assert math.isnan(h24.signals([10] * 8, 5, 0.0)["b_stage"])


def test_rule():
    assert h24.rule(0.25, 0.5) == "verde"
    assert h24.rule(0.25, 0.5, in_domain=False) == "amarillo"
    assert h24.rule(0.26, 0.1) == "amarillo"
    assert h24.rule(1.01, 0.1) == "rojo"
    assert h24.rule(0.1, 1.51) == "rojo"
    assert h24.rule(math.nan, 0.1) == "amarillo"


def _lit(n_green, fail_green, n_other, fail_other, per_embryo=1):
    rows = []
    for i in range(n_green + n_other):
        green = i < n_green
        fail = (i < fail_green) if green else (i - n_green < fail_other)
        rows.append({"embryo_id": f"e{i // per_embryo}", "light": "verde" if green else "amarillo",
                     "light_without_guard": "verde" if green else "amarillo", "in_domain": True,
                     "e_b": 0.9 if fail else 0.1, "rel_error_volume": 0.3 if fail else 0.02, "dice": 0.9})
    return pd.DataFrame(rows)


def test_bad_counts_nan_as_failure():
    df = pd.DataFrame({"e_b": [0.1, 0.5, 0.51, math.nan]})
    assert h24.bad(df).tolist() == [False, False, True, True]


def test_gates():
    lit = _lit(12, 1, 22, 10)
    assert h24.gate_s(lit)["passed"]
    assert h24.gate_c(lit)["passed"]
    assert not h24.gate_c(_lit(12, 2, 22, 10))["passed"]
    assert not h24.gate_c(_lit(9, 0, 25, 0))["passed"]


def test_green_failure_and_separation():
    lit = _lit(25, 1, 15, 8)
    gf = h24.green_failure(lit, n_boot=200)
    assert gf["verdict"] == "apoyada" and gf["estimate"] == pytest.approx(1 / 25)
    sep = h24.separation(lit, n_boot=200)
    assert sep["verdict"] == "separa"
    assert h24.green_failure(_lit(19, 0, 21, 0), n_boot=50)["verdict"] == "no evaluable"
    assert h24.separation(_lit(4, 0, 36, 5), n_boot=50)["verdict"] == "no evaluable"
    assert h24.separation(_lit(20, 0, 20, 0), n_boot=200)["verdict"] == "no separa"


def test_evaluate_test_keys():
    out = h24.evaluate_test(_lit(25, 1, 15, 8), n_boot=100)
    assert {"h24a", "h24b", "h24c", "h24d", "h24e", "h24g"} <= set(out)
    assert out["h24g"]["fail_all"] == pytest.approx(9 / 40)
