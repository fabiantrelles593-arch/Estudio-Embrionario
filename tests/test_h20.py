"""H20: señales de fiabilidad de la red y regla fija.

Qué haría fallar cada prueba: si los volteos no fueran los 8 (o la identidad no fuera la primera), ``s_flip`` no
mediría lo declarado y la identidad no sería la medida de H19; si la regla diera verde fuera del dominio o con una
señal no calculable, el certificado aprobaría lo que no puede juzgar; si la guardia de la calibración se ajustara con
el propio embrión, la puerta C sería optimista; si la puerta C cambiara respecto a H19, H19 y H20 no serían comparables.
"""
import math

import numpy as np
import pandas as pd
import pytest

from geovida import h19, h20


def test_flips_are_the_eight_with_identity_first():
    assert len(h20.FLIPS) == 8 and h20.FLIPS[0] == () and len(set(h20.FLIPS)) == 8
    seen = []

    def fake_segment(c, f, im):
        seen.append(im.copy())
        return im > 0.5, im

    image = np.zeros((6, 7, 8), np.float32)
    image[1:3, 1:3, 3:7] = 1                              # asimétrico en los tres ejes: cada volteo da otra imagen
    vols = h20.flip_volumes(None, None, image, segment=fake_segment)
    assert vols == [float((image > 0.5).sum())] * 8       # el volumen no cambia al voltear
    assert np.array_equal(seen[0], image)
    assert len({s.tobytes() for s in seen}) == 8


def test_signals():
    s = h20.signals([100, 104, 98, 100, 101, 99, 100, 100], 110)
    assert s["s_flip"] == pytest.approx(0.06) and s["s_stage"] == pytest.approx(0.10) and s["v_identity"] == 100
    e = h20.signals([0] * 8, 10)
    assert math.isnan(e["s_flip"]) and math.isnan(e["s_stage"])


def test_rule_thresholds_guard_and_missing():
    assert h20.rule(0.05, 0.10, True) == "verde"                    # en el umbral: verde
    assert h20.rule(0.0501, 0.0, True) == "amarillo"
    assert h20.rule(0.0, 0.1001, True) == "amarillo"
    assert h20.rule(0.01, 0.01, False) == "amarillo"                # fuera del dominio nunca verde
    assert h20.rule(0.21, 0.0, True) == "rojo" and h20.rule(0.0, 0.31, False) == "rojo"
    assert h20.rule(0.20, 0.30, True) == "amarillo"
    assert h20.rule(math.nan, 0.0, True) == "amarillo" and h20.rule(0.0, math.nan, True) == "amarillo"
    assert (h20.GREEN_FLIP, h20.GREEN_STAGE, h20.RED_FLIP, h20.RED_STAGE) == (0.05, 0.10, 0.20, 0.30)


def _cal(n=27, seed=0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({"image": [f"i{k}" for k in range(n)], "embryo_id": [f"e{k // 2}" for k in range(n)],
                         "rel_error_volume": rng.normal(0, 0.05, n), "s_flip": rng.uniform(0, 0.08, n),
                         "s_stage": rng.uniform(0, 0.15, n), "d_over_hgeo": rng.uniform(8, 12, n),
                         "snr_hat": rng.uniform(0.4, 2, n), "edge_width": rng.uniform(0.5, 1.7, n)})


def test_out_of_fold_guard_excludes_own_embryo():
    cal = _cal()
    cal.loc[0, ["s_flip", "s_stage", "snr_hat"]] = [0.0, 0.0, 50.0]       # fuera de lo que ven los demás pliegues
    cal.loc[1, "snr_hat"] = 1.0                                            # su pareja de embrión, dentro
    lit = h20.out_of_fold(cal)
    assert list(lit.index) == list(cal.index)
    assert not lit.loc[0, "in_domain"] and lit.loc[0, "light"] == "amarillo"
    assert lit.loc[0, "light_without_guard"] == "verde"


def test_gate_c_is_h19s_gate():
    assert (h19.MIN_GREEN_CAL, h19.MAX_FAIL_CAL) == (10, 0.10)
    lit = pd.DataFrame({"light": ["verde"] * 16 + ["amarillo"] * 11,
                        "rel_error_volume": [0.5, 0.11] + [0.0] * 25})
    g = h20.gate_c(lit)
    assert g["n_green"] == 16 and g["fail"] == pytest.approx(0.125) and not g["passed"]   # el caso de H19
    lit.loc[1, "rel_error_volume"] = 0.0
    assert h20.gate_c(lit)["passed"]                                                       # 1 de 16 = 6,25 %
    assert not h20.gate_c(lit.assign(light="amarillo"))["passed"]                          # sin verdes no pasa


def test_g0_is_feasibility_only():
    ok = {"s_flip": 0.3, "s_stage": 0.5, "identity_matches_h19": True, "seconds": 100}   # señales altas: no importa
    assert h20.g0([ok] * 5)["passed"]
    assert not h20.g0([ok, {**ok, "identity_matches_h19": False}])["passed"]
    assert not h20.g0([ok, {**ok, "seconds": 301}])["passed"]
    assert not h20.g0([ok, {**ok, "s_flip": math.nan}])["passed"]
    assert not h20.g0([])["passed"]


def test_evaluate_test_separation():
    lit = pd.DataFrame({"embryo_id": [f"e{k}" for k in range(30)], "light": ["verde"] * 20 + ["amarillo"] * 10,
                        "light_without_guard": ["verde"] * 22 + ["amarillo"] * 8,
                        "rel_error_volume": [0.0] * 19 + [0.2] + [0.3] * 5 + [0.0] * 5,
                        "dice": 0.9, "in_domain": True})
    out = h20.evaluate_test(lit, n_boot=200)
    assert out["h20b"]["n_green"] == 20 and out["h20b"]["estimate"] == pytest.approx(0.05)
    assert out["h20b"]["verdict"] == "apoyada"
    d = out["h20d"]
    assert d["fail_green"] == pytest.approx(0.05) and d["fail_not_green"] == pytest.approx(0.5)
    assert d["difference"] == pytest.approx(0.45) and d["difference_ci"][0] > 0
    assert d["green_without_guard"] == 22


def test_runs_with_real_two_stage_pipeline():
    """Cableado con la U-Net de H19 sin entrenar (no mide exactitud): 8 volúmenes y la etapa 1 sobre arrays volteados."""
    torch = pytest.importorskip("torch")
    torch.manual_seed(0)
    coarse, fine = h19.UNet3D(1), h19.UNet3D(2)
    with torch.no_grad():                                    # sesgo de salida alto: la etapa 1 marca todo, hay caja
        coarse.out.bias.fill_(5.0)
    image = np.random.default_rng(0).random((40, 36, 32)).astype(np.float32)
    vols = h20.flip_volumes(coarse, fine, image)
    vc = h20.coarse_volume(coarse, image)
    assert len(vols) == 8 and all(v >= 0 for v in vols) and vc > 0
    mask, _ = h19.segment_full(coarse, fine, image)
    assert vols[0] == float(mask.sum())                      # la identidad es la medida de H19


def test_largest_component():
    m = np.zeros((10, 10, 10), bool)
    m[1:4, 1:4, 1:4] = True
    m[7, 7, 7] = True
    assert h20.largest_component(m).sum() == 27
