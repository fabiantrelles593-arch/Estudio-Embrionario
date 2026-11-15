"""Regla de ampliación de P3 (§4 del preregistro, proyección fijada en la desviación D4)."""
import importlib.util
import math
from pathlib import Path

import pytest

pytest.importorskip("nibabel")
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("p3_analyze", ROOT / "scripts" / "p3_analyze.py")
pa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pa)


def test_projection_scales_with_sqrt_n():
    assert pa.projected_half_width(0.0, 0.2, 20) == pytest.approx(0.1 * math.sqrt(20 / 60))
    assert pa.projected_half_width(0.0, 0.2, 60) == pytest.approx(0.1)
    assert math.isnan(pa.projected_half_width(math.nan, 0.2, 20))


def test_expansion_decision():
    assert pa.expansion_decision(0.0, 0.30, 20) == 60    # 0,15 → 0,087 a 60
    assert pa.expansion_decision(0.0, 0.40, 20) == 120   # 0,20 → 0,115 a 60
    assert pa.expansion_decision(math.nan, 0.4, 20) == 120
