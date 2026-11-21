"""Pruebas del generador de informe del piloto de P3 con resultados sintéticos."""
import importlib.util
import math
from pathlib import Path

import pandas as pd

_spec = importlib.util.spec_from_file_location(
    "p3_report", Path(__file__).resolve().parents[1] / "scripts" / "p3_report.py")
rep = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rep)


def test_precheck_34_threshold_and_missing_specimens():
    ids = [f"s{i}" for i in range(20)]
    run = {s: {"ok": True} for s in ids[:18]}
    run["s18"] = {"ok": False}
    pre = rep.precheck_34(run, ids)
    assert pre["n_ok"] == 18 and pre["passed"] and pre["failed"] == ["s18", "s19"]
    run.pop("s0")
    assert not rep.precheck_34(run, ids)["passed"]


def test_compare_rows_ignore_structures_absent_from_atlas():
    cmp = {"s1": {"translation_vox": [1, 0, 0], "dice_union_raw": 0.5, "dice_union_shifted": 0.9,
                  "raw": {"1": {"dice": 0.2, "vox_atlas": 10}, "2": {"dice": 0.4, "vox_atlas": 10},
                          "3": {"dice": 0.0, "vox_atlas": 0}, "102": {"dice": 0.0, "vox_atlas": 50}},
                  "shifted": {"1": {"dice": 0.8, "vox_atlas": 10}, "2": {"dice": 0.6, "vox_atlas": 10}}}}
    row = rep.compare_rows(cmp).iloc[0]
    assert math.isclose(row["dice_median_raw"], 0.3) and math.isclose(row["dice_median_shifted"], 0.7)


def test_non_rigid_specimens_are_flagged_and_excluded_in_sensitivity():
    def spec(d):
        return {"translation_vox": [0, 0, 0], "dice_union_raw": d, "dice_union_shifted": d,
                "raw": {"1": {"dice": d, "vox_atlas": 10}}, "shifted": {"1": {"dice": d, "vox_atlas": 10}}}
    cmp = {"a": spec(0.8), "b": spec(0.7), "c": spec(0.2)}
    rows = rep.compare_rows(cmp, {"a": {"spread_vox": 1}, "b": {"spread_vox": 4}, "c": {"spread_vox": 21}})
    assert list(rows["non_rigid"]) == [False, False, True]  # el umbral es > 4
    text = rep.render({"n": 3, "n_ok": 3, "failed": [], "passed": True}, rows, None, None)
    assert "21 (no rígido)" in text
    assert "sin los 1 marcados como no rígidos: **0,75** (n = 2)" in text
    assert not rep.compare_rows(cmp)["non_rigid"].any()


def test_render_includes_decision_and_marks_pilot_as_not_a_result():
    pre = {"n": 20, "n_ok": 19, "failed": ["s3"], "passed": True}
    analysis = {"n_specimens": 19, "n_boot": 2000, "delta": 0.1, "delta_ci": [0.0, 0.2], "rho": -0.4,
                "rho_partial": -0.3, "rho_partial_ci": [-0.6, 0.1], "delta_ci_half_width": 0.1,
                "projected_half_width_60": 0.056, "n_confirm_decision": 60,
                "seconds_measure": 100.0, "seconds_evaluate": 5.0}
    groups = pd.DataFrame({"unit": ["1", "2"], "group": ["delgada", "compacta"]})
    text = rep.render(pre, pd.DataFrame(), groups, analysis)
    assert "19 de 20" in text and "no es resultado de P3" in text
    assert "confirmatorio según la regla de D4: 60" in text and "0,056" in text


def _res(delta, va, rho, vb):
    return {"n_specimens": 60, "n_boot": 2000, "seed": 20261115, "n_units": {"compacta": 20, "delgada": 12},
            "delta": delta, "delta_ci": [delta - 0.05, delta + 0.05], "verdict_a": va,
            "rho": rho, "rho_partial": rho, "rho_partial_ci": [rho - 0.1, rho + 0.1], "verdict_b": vb}


def test_render_confirm_transcribes_verdicts_and_d1():
    summary = {"which": "confirm", "specimens": ["s"] * 60, "missing": [], "non_rigid_D5": ["s7"],
               "primary": _res(0.1, "apoyada", -0.6, "apoyada"),
               "exact_D1": _res(0.02, "no_concluyente", -0.55, "apoyada"),
               "order_tau_vs_exact_D1": {"rho": 0.5, "n_structures": 40, "agree": False},
               "verdicts_after_D1": {"verdict_a": "no_interpretable_D1", "verdict_b": "apoyada"},
               "order_tau_vs_mixed": {"rho": 0.9, "n_structures": 40, "agree": True}, "mixed_converged": 38,
               "exploratory_sex": True, "exploratory_x4": None, "seconds_main": 10.0, "seconds_exact": 5.0}
    agr = pd.DataFrame({"form": ["a", "a", "b", "b"], "structure": [1, 2, 1, 2], "dice": [0.5, 0.7, 0.8, 0.9],
                        "hd95": [1, 2, 1, 1], "assd": [0.1, 0.2, 0.1, 0.1], "vol_diff_rel": [0.1, 0.1, 0.0, 0.0],
                        "n_specimens": [60] * 4})
    text = rep.render_confirm(summary, agr)
    assert "**no interpretable (regla de D1)**" in text and "**discrepan**" in text
    assert "| H-P3a | Δ = 0,100 | 0,050 a 0,150 | apoyada |" in text
    assert "(a) sin trasladar | 2 | 0,60" in text and "(b) con traslación (principal) | 2 | 0,85" in text
    assert "no rígidos (D5): 1 (`s7`)" in text and "MEMOS a ×4: no calculado" in text
    assert "Combinación no prevista en §7" in text
    # como lo deja `confirm --reuse-main`: sin tiempo de la pasada principal y ×4 vacío
    text2 = rep.render_confirm({**summary, "seconds_main": float("nan"),
                                "exploratory_x4": {"n_specimens": 0, "status": "sin segmentaciones ×4: no calculado"}},
                               agr)
    assert "MEMOS a ×4: no calculado" in text2 and "principal — s" in text2


def test_section7_rows():
    assert rep.section7("apoyada", "apoyada")[1].startswith("Repetir en un segundo estadio")
    assert rep.section7("apoyada", "no_apoyada")[0].startswith("El fenómeno existe")
    assert rep.section7("no_concluyente", "apoyada")[0] == rep.section7("contraria", "no_apoyada")[0]
    assert rep.section7("apoyada", "no_evaluable")[0].startswith("Combinación no prevista")
    assert rep.section7("no_interpretable_D1", "apoyada")[0].startswith("Combinación no prevista")
