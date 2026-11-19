"""Puertas de MT-A (``scripts/atlas_effect_gates.py``). Configuraciones sintéticas; ningún dato real.

Qué falla si la puerta G0-d deja de aplicar el intervalo del preregistro (§4: longitud de d en [0,150, 0,164]).
"""
import importlib.util
from pathlib import Path

import numpy as np

_spec = importlib.util.spec_from_file_location(
    "atlas_effect_gates", Path(__file__).resolve().parents[1] / "scripts" / "atlas_effect_gates.py")
gates = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gates)


def _stage(base, shift, n, rng):
    return np.stack([base + shift + rng.normal(0, 0.002, base.shape) for _ in range(n)])


def test_g0d_uses_the_preregistered_range():
    assert gates.G0D_RANGE == (0.150, 0.164) and gates.PUBLISHED_D == 0.157


def test_g0d_passes_and_fails_by_the_length_of_d():
    rng = np.random.default_rng(0)
    base = rng.normal(0, 1, (40, 3))
    base -= base.mean(axis=0)
    base /= np.linalg.norm(base)                                   # preforma: d se mide en estas unidades
    direction = rng.normal(0, 1, base.shape)
    direction -= direction.mean(axis=0)
    direction -= (direction.ravel() @ base.ravel()) * base         # perpendicular a la forma media
    direction /= np.linalg.norm(direction)
    for length, expected in [(0.157, True), (0.10, False)]:
        cfg = {"E15.5": _stage(base, -length / 2 * direction, 30, rng),
               "E18.5": _stage(base, length / 2 * direction, 30, rng)}
        r = gates.g0d(cfg)
        assert r["passed"] is expected, r["d_length"]
