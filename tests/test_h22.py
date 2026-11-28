"""H22: regla del estado «inservible», diseño congelado y reglas de veredicto (sin datos medidos)."""
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from geovida import h22
from geovida.certificate import certify, load_frozen
from geovida.experiment import Condition, run_condition

ROOT = Path(__file__).resolve().parents[1]
ENV = {"snr_hat": [8.0, 10.0], "edge_width": [0.5, 1.0]}


def test_design_and_seed_are_frozen():
    d = h22.design()
    assert len(d) == 4 * 5 * 1 * 9 * 30
    assert {c.profile for c in d} == set(h22.PROFILES) and h22.DECLARED in h22.PROFILES
    used = {20261109, 20261110, 20261111, 20261112, 20261113, 20261114, 20261115, 20261116, 20261117,
            20261120, 20261121, 20261122, 20261123, 20261124, 20261125, 20261126, 20261130, 20261131,
            20261132, 20261133, 20262101}
    assert h22.SEED not in used and h22.BOOT_SEED not in used


def test_log_excess():
    assert h22.log_excess({"snr_hat": 9.0, "edge_width": 0.7}, ENV) == 0.0
    assert h22.log_excess({"snr_hat": 9.0, "edge_width": 2.0}, ENV) == pytest.approx(math.log(2))
    assert h22.log_excess({"snr_hat": 2.0, "edge_width": 1.5}, ENV) == pytest.approx(math.log(4))
    assert h22.log_excess({"snr_hat": math.nan, "edge_width": 0.7}, ENV) == math.inf
    assert h22.log_excess({"snr_hat": 9.0, "edge_width": 0.0}, ENV) == math.inf


def _rows(**kw):
    base = {"shape": "cone", "t_over_h": 8.0, "anisotropy": 1.0, "profile": "noisy", "rep": 0,
            "segmenter": "otsu", "volume": 1.0, "err_volume": 0.0, "d_over_hgeo": 5.0,
            "snr_hat": 9.0, "edge_width": 0.8}
    return pd.DataFrame([{**base, **k} for k in kw.get("rows", [{}])])


def test_classify_reproduces_the_volume_light_of_the_certificate():
    frozen = load_frozen()
    env = frozen["envelopes"]["volume"]["otsu|realistic"]
    mid = {"snr_hat": float(np.mean(env["snr_hat"])), "edge_width": float(np.mean(env["edge_width"]))}
    df = _rows(rows=[
        {**mid},                                                     # dentro, profundo: verde
        {**mid, "snr_hat": env["snr_hat"][0] / 1.5},                 # fuera ×1,5: amarillo, no inservible
        {**mid, "snr_hat": env["snr_hat"][0] / 3},                   # fuera ×3: inservible
        {**mid, "edge_width": math.nan},                             # dominio no comprobable: inservible
        {**mid, "volume": 0.0, "snr_hat": math.nan},                 # máscara vacía: rojo, como certify
        {**mid, "d_over_hgeo": 0.5, "edge_width": env["edge_width"][1] * 3},   # rojo por p y además fuera
    ])
    c = h22.classify(df, frozen)
    assert list(c["light"]) == ["verde", "amarillo", "amarillo", "amarillo", "rojo", "rojo"]
    assert list(c["state"]) == ["verde", "amarillo", "inservible", "inservible", "rojo", "inservible"]
    assert list(c["in_domain"]) == [True, False, False, False, False, False]


def test_classify_matches_certify_on_one_image():
    """La luz que ``classify`` reconstruye desde las columnas del barrido es la de ``certify`` (semilla ajena)."""
    from geovida.imaging import render, spec_for_t_over_h
    from geovida.phantoms import make_phantom
    cond = Condition("prolate", 6.0, 1.0, "realistic", 0)
    rows = run_condition(cond, 1, ("otsu",), h22.guard_extra)
    c = h22.classify(pd.DataFrame(rows), load_frozen()).iloc[0]
    spec = spec_for_t_over_h(6.0, 1.0, "realistic", t=1.0)
    from geovida.experiment import _rng
    img = render(make_phantom("prolate", 1.0), spec, _rng(cond, 1))
    cert = certify(img.image, img.spacing, "otsu", "realistic")
    assert cert["volume"]["light"] == c["light"] and cert["volume"]["in_domain"] == bool(c["in_domain"])
    assert cert["volume"]["p"] == pytest.approx(c["p_volume"])


def _classified(n_img, flagged_ok, flagged_bad, gross_unflagged, ctrl_flag=0, n_ctrl=300):
    """Tabla clasificada artificial: una fila por imagen."""
    rows = []
    def add(profile, err, unusable, light="amarillo"):
        rows.append({"shape": "cone", "t_over_h": 8.0, "anisotropy": 1.0, "profile": profile, "rep": len(rows),
                     "segmenter": "otsu", "err_volume": err, "unusable": unusable, "light": light})
    for _ in range(flagged_ok):
        add("noisy", 0.05, True)
    for _ in range(flagged_bad):
        add("noisy", 0.9, True)
    for _ in range(gross_unflagged):
        add("noisy", 0.9, False)
    for i in range(n_ctrl):
        add("realistic", 0.02, i < ctrl_flag, "verde")
    for _ in range(n_img - len(rows)):
        add("blurry", 0.2, False)
    return pd.DataFrame(rows)


def test_verdict_rules():
    v = h22.verdicts(_classified(1000, 0, 200, 100))
    assert v["H22a"]["verdict"] == "apoyada" and v["H22a"]["upper95"] == 0.0
    assert v["H22b"]["fraction"] == pytest.approx(200 / 300) and v["H22b"]["verdict"] == "apoyada"
    assert v["H22c"]["verdict"] == "apoyada" and v["decision"] == "anadir_inservible"
    low = h22.verdicts(_classified(1000, 0, 200, 900))
    assert low["H22b"]["verdict"] == "contraria" and low["decision"] == "anadir_inservible_sensibilidad_baja"
    bad = h22.verdicts(_classified(1000, 40, 160, 100))
    assert bad["H22a"]["verdict"] == "contraria" and bad["decision"] == "no_anadir"
    ctrl = h22.verdicts(_classified(1000, 0, 200, 100, ctrl_flag=10))
    assert ctrl["H22c"]["verdict"] == "no_apoyada" and ctrl["decision"] == "no_anadir"
    few = h22.verdicts(_classified(1000, 0, 40, 50))
    assert few["H22a"]["verdict"] == "no_evaluable" and few["H22b"]["verdict"] == "no_evaluable"


def test_bootstrap_keeps_rows_of_one_image_together():
    img = np.array([0, 0, 0, 1, 1, 1])
    num = np.array([1, 1, 1, 0, 0, 0], float)
    den = np.ones(6)
    up = h22._boot_upper(num, den, img, n_boot=500)
    assert up == pytest.approx(1.0)     # con 2 imágenes, una réplica puede tomar solo la primera


def test_runner_end_to_end_on_a_tiny_design(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("run_h22", ROOT / "scripts" / "run_h22.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod.h22, "SEED", 1)       # nunca la semilla confirmatoria en las pruebas
    monkeypatch.setattr(mod.h22, "design", lambda reps: [Condition("cone", 4.0, 1.0, "realistic", 0),
                                                         Condition("horseshoe", 6.0, 1.0, "noisy", 0)])
    out = tmp_path / "sweep.csv.gz"
    assert mod.main(["run", "--out", str(out), "--reps", "1"]) == 0
    with pytest.raises(SystemExit):
        mod.main(["run", "--out", str(out), "--reps", "1"])   # se mide una sola vez
    v = tmp_path / "verdicts.json"
    assert mod.main(["analyze", "--sweep", str(out), "--out", str(v)]) == 0
    res = json.loads(v.read_text(encoding="utf-8"))
    assert res["rows"] == 6 and res["verdicts"]["H22a"]["verdict"] == "no_evaluable"
    assert json.loads((tmp_path / "sweep_manifest.json").read_text(encoding="utf-8"))["base_seed"] == 1
    assert (tmp_path / "verdicts.strata.csv").exists() and (tmp_path / "verdicts.crosstab.csv").exists()
