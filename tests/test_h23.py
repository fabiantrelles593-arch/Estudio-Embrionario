"""H23 (docs/h23/PREREGISTRO_H23.md): puertas y criterio de separación, con datos SINTÉTICOS.

Qué haría fallar cada prueba: si el reparto mezclara cuerpo y ventrículo o dejara un embrión a dos lados, no sería el
preregistrado; si G0-escala contara mal los vóxeles a ¼, la puerta no diría si la etapa 1 tiene algo que localizar; si
la separación diera «separa» sin que el límite inferior pase de 0, H23d confirmaría lo que no se midió; si el script
entrenara sin G0 o abriera la prueba sin el SHA-256, el candado no existiría. Sin imágenes ni redes.
"""
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from geovida import h20, h23

_spec = importlib.util.spec_from_file_location(
    "run_h23", Path(__file__).resolve().parents[1] / "scripts" / "run_h23.py")
run_h23 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_h23)


def _manifest(tmp_path):
    rows = []
    for split, n in (("nii_train", 6), ("nii_test", 3)):
        for i in range(n):
            emb = f"{split}_E{i}"
            for st, lab in (("body", "BODY"), ("ventricle", "BV")):
                rows.append({"embryo_id": emb, "structure": st, "image": f"{split}/E11/{emb}.nii",
                             "label": f"{split}/E11/{emb}_{lab}_labels.nii", "label_value": 1})
    rows.append({"embryo_id": "nii_train_E0", "structure": "ventricle", "image": "nii_test/E11/dup.nii",
                 "label": "nii_test/E11/dup_BV_labels.nii", "label_value": 1})
    p = tmp_path / "m.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    return p


def test_cases_only_ventricle_and_embryo_disjoint(tmp_path):
    p = _manifest(tmp_path)
    tr, rep = h23.cases(p, "train")
    te, _ = h23.cases(p, "test")
    assert set(tr["structure"]) == set(te["structure"]) == {"ventricle"}
    assert not set(tr["embryo_id"]) & set(te["embryo_id"])
    assert len(tr) == 7 and len(te) == 3 and rep["test_cases_moved_to_train"] == 1


def test_coarse_voxels_and_g0_scale():
    ref = np.zeros((40, 40, 40), bool)
    ref[4:16, 4:16, 4:16] = True                     # 12³ a resolución completa → 3³ = 27 a ¼
    assert h23.coarse_voxels(ref) == 27
    small = np.zeros_like(ref)
    small[4:12, 4:12, 4:12] = True                   # 8³ → 2³ = 8
    assert h23.coarse_voxels(small) == 8
    assert h23.g0_scale([27] * 9 + [8])["passed"]            # 90 % justo
    assert not h23.g0_scale([27] * 8 + [8, 8])["passed"]     # 80 %
    assert not h23.g0_scale([])["passed"]


def test_largest_fraction():
    ref = np.zeros((20, 20, 20), bool)
    ref[1:5, 1:5, 1:5] = True                        # 64
    ref[10:12, 10:12, 10:16] = True                  # 24
    assert math.isclose(h23.largest_fraction(ref), 64 / 88)


def test_gate_s():
    cal = pd.DataFrame({"rel_error_volume": [0.05, -0.08, 0.3, -0.5]})
    assert h23.gate_s(cal)["passed"] and h23.gate_s(cal)["fraction_ok10"] == 0.5
    assert not h23.gate_s(cal.assign(rel_error_volume=[0.05, 0.3, 0.3, 0.3]))["passed"]


def _lit(n_green, n_other, fail_green, fail_other):
    rows = []
    for k in range(n_green):
        rows.append({"embryo_id": f"g{k}", "light": "verde", "rel_error_volume": 0.5 if k < fail_green else 0.01})
    for k in range(n_other):
        rows.append({"embryo_id": f"o{k}", "light": "amarillo", "rel_error_volume": 0.5 if k < fail_other else 0.01})
    return pd.DataFrame(rows)


def test_separation_verdicts():
    assert h23.separation(_lit(20, 20, 0, 15), n_boot=500)["verdict"] == "separa"
    assert h23.separation(_lit(20, 20, 0, 0), n_boot=500)["verdict"] == "no separa"
    assert h23.separation(_lit(4, 20, 0, 10), n_boot=500)["verdict"] == "no evaluable"
    r = h23.separation(_lit(10, 10, 1, 2), n_boot=500)
    assert r["verdict"] == "no concluyente" and r["ci"][0] <= 0 < r["ci"][1]


def test_evaluate_test_keys_and_rule_unchanged():
    lit = _lit(25, 15, 1, 10).assign(dice=0.8, in_domain=True)
    lit["light_without_guard"] = lit["light"]
    out = h23.evaluate_test(lit, n_boot=200)
    assert out["h23b"]["verdict"] == "apoyada" and out["h23d"]["verdict"] == "separa"
    assert set(out) >= {"h23a", "h23b", "h23c", "h23d", "h23e"}
    assert h20.THRESHOLDS["green_flip"] == 0.05 and h20.THRESHOLDS["red_stage"] == 0.30


def test_script_refuses_out_of_order(tmp_path, monkeypatch):
    monkeypatch.setattr(run_h23, "OUT", tmp_path / "h23")
    args = run_h23.argparse.Namespace(manifest=str(_manifest(tmp_path)), root=str(tmp_path), sha="")
    with pytest.raises(SystemExit):
        run_h23.cmd_train_coarse(args)                       # sin G0-escala
    (tmp_path / "h23").mkdir()
    (tmp_path / "h23" / "g0_scale.json").write_text(json.dumps({"passed": False}))
    with pytest.raises(SystemExit):
        run_h23.cmd_train_coarse(args)                       # G0-escala no superada
    with pytest.raises(Exception):
        run_h23.cmd_test(args)                               # sin congelado ni SHA-256


@pytest.mark.skipif(not Path("results/h11/manifiesto_qiu2021.csv").exists(), reason="manifiesto local, fuera de git")
def test_real_split_matches_preregistration():
    tr = run_h23.roles("results/h11/manifiesto_qiu2021.csv")
    te, _ = h23.cases("results/h11/manifiesto_qiu2021.csv", "test")
    assert (tr.role == "fit").sum() == 142 and (tr.role == "cal").sum() == 34 and len(te) == 40
