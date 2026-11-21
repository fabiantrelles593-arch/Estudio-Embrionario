"""Informe de H11/H12R con veredictos fabricados (ningún dato real)."""
import importlib.util
from pathlib import Path

import pandas as pd

_spec = importlib.util.spec_from_file_location("h11_report", Path(__file__).resolve().parents[1] / "scripts" / "h11_report.py")
rep = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rep)


def _v(in_domain_so, verdict_b="no evaluable", n_green=3):
    frac = {"global": 0.0, "otsu": 0.1, "smoothed_otsu": in_domain_so}
    fb = {"n_green": n_green, "n_embryos_green": 2, "estimate": None, "ci": None, "verdict": verdict_b}
    if verdict_b != "no evaluable":
        fb.update(estimate=0.05, ci=[0.01, 0.12])
    return {"n_cases": 1188, "n_embryos": 203,
            "h11a": {"in_domain_fraction": frac, "passed": 3, "verdict": "apoyada"},
            "h11b": fb, "h11c": dict(fb, verdict="no evaluable"), "h11e": dict(fb, verdict="no evaluable",
                                                                              reference_not_simple=0.25),
            "h11d": {"rows": [{"segmenter": "otsu", "structure": "body", "n": 180, "dice_median": 0.81,
                               "dice_min": 0.2, "dice_max": 0.95, "abs_error_median": 0.12, "abs_error_min": 0.0,
                               "abs_error_max": 0.9, "ok10": 0.4, "ok5": 0.2}]}}


def test_h12ra_compares_smoothed_otsu_only():
    assert rep.h12ra(_v(0.10), _v(0.30))["verdict"] == "apoyada"
    assert rep.h12ra(_v(0.30), _v(0.30))["verdict"] == "no apoyada"
    assert rep.h12ra(_v(float("nan")), _v(0.3))["verdict"] == "no evaluable"


def test_body_greens_counts_only_guarded_body_greens():
    cases = pd.DataFrame({"structure": ["body", "body", "ventricle", "body"],
                          "light_volume": ["verde", "amarillo", "verde", "verde"]})
    assert rep.body_greens(cases) == 2


def test_render_applies_h12r_section5_and_marks_not_clinical():
    text = rep.render({"v04": _v(0.1), "h12": _v(0.3, "apoyada", 40)}, {"v04": 3, "h12": 40})
    assert "Nada de esto es clínico" in text
    assert "→ H12 30,0 % → **apoyada**" in text
    assert "40 − 3 = **37**" in text
    assert "Replicar con un segundo conjunto" in text
    assert "| b — verdes con guardia" in text and "1,0 % a 12,0 %" in text
    assert "| otsu | body | 180 | 0,81 (0,20–0,95) | 12,0 % | 40,0 % | 20,0 % |" in text


def test_render_without_h12_has_no_h12r_section():
    text = rep.render({"v04": _v(0.1)}, {"v04": 3})
    assert "H12R — comparación" not in text and "H11 · calibración v0.4" in text
    assert rep.h12r_section5("no evaluable")[0].startswith("El simulador de ecografía")
