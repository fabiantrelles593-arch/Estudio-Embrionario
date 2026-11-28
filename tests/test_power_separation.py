"""El veredicto vectorizado de ``scripts/power_separation.py`` coincide con ``geovida.h24.separation``."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from geovida import h24

_spec = importlib.util.spec_from_file_location(
    "power_separation", Path(__file__).resolve().parents[1] / "scripts" / "power_separation.py")
ps = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ps)


def _frame(green, bad):
    return pd.DataFrame({"embryo_id": [f"e{i}" for i in range(len(green))],
                         "light": np.where(green, "verde", "amarilla"),
                         "e_b": np.where(bad, 1.0, 0.1)})


@pytest.mark.parametrize("n,pg,pn,seed", [(40, 0.05, 0.05, 1), (80, 0.05, 0.4, 2), (60, 0.0, 0.0, 3),
                                          (120, 0.05, 0.27, 4)])
def test_verdict_matches_h24(n, pg, pn, seed):
    rng = np.random.default_rng(seed)
    green = rng.random(n) < 0.5
    bad = np.where(green, rng.random(n) < pg, rng.random(n) < pn)
    ref = h24.separation(_frame(green, bad))["verdict"]
    assert ps.verdict(green, bad, np.random.default_rng(seed)) == ref


def test_not_evaluable_with_few_greens():
    green = np.array([True] * 4 + [False] * 30)
    assert ps.verdict(green, np.zeros(34, bool), np.random.default_rng(0)) == "no evaluable"


def test_simulate_probabilities_sum_to_one():
    r = ps.simulate(40, 0.05, 0.05, 20, np.random.default_rng(0))
    assert abs(sum(r.values()) - 1) < 1e-9
