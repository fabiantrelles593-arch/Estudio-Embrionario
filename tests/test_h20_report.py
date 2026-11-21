"""Pruebas del generador de tablas de H20 con resultados sintéticos (la forma de lo que escribe run_h20.py)."""
import importlib.util
from pathlib import Path

import pandas as pd

_spec = importlib.util.spec_from_file_location(
    "h20_report", Path(__file__).resolve().parents[1] / "scripts" / "h20_report.py")
rep = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rep)


def _g0(passed=True):
    items = [{"image": f"c{i}", "s_flip": 0.01 * i, "s_stage": 0.02, "identity_matches_h19": True, "seconds": 120.0}
             for i in range(5)]
    if not passed:
        items[2]["identity_matches_h19"] = False
    return {"n": 5, "passed": passed, "items": items}


def _lit():
    return pd.DataFrame({"image": list("abcdef"), "embryo_id": list("aabbcc"),
                         "rel_error_volume": [0.02, -0.15, 0.05, 0.30, -0.01, 0.12],
                         "light": ["verde", "verde", "amarillo", "rojo", "verde", "amarillo"],
                         "light_without_guard": ["verde", "verde", "verde", "rojo", "verde", "amarillo"],
                         "in_domain": [True, True, False, True, True, True]})


def _cal(passed):
    return {"gate_c": {"n_green": 12, "fail": 0.0833 if passed else 0.25, "passed": passed}, "n_cal": 27,
            **({"frozen_sha256": "ab" * 32} if passed else {})}


def _test(verdict="apoyada", ok10=0.80):
    return {"n_cases": 44, "n_embryos": 20,
            "h20b": {"n_green": 25, "n_embryos_green": 16, "estimate": 0.04, "ci": [0.0, 0.12], "verdict": verdict},
            "h20a": {"green_fraction": 25 / 44, "lights": {"verde": 25, "amarillo": 15, "rojo": 4}},
            "h20c": {"dice_median": 0.91, "abs_error_median": 0.05, "ok10": ok10, "ok5": 0.5},
            "h20d": {"fail_green": 0.04, "fail_not_green": 0.4, "difference": 0.36, "difference_ci": [0.1, 0.6],
                     "in_domain": 0.9, "green_without_guard": 28, "green_without_guard_bad": 2}}


def test_light_table_counts_failures_per_light():
    t = rep.light_table(_lit())
    assert list(t["light"]) == ["verde", "amarillo", "rojo"]
    assert list(t["n"]) == [3, 2, 1] and list(t["bad"]) == [1, 1, 1]
    assert list(rep.light_table(_lit(), "light_without_guard")["n"]) == [4, 1, 1]


def test_section8_follows_where_the_study_stopped():
    assert rep.section8(False, None, None) == rep.SECTION8["g0"]
    assert rep.section8(True, False, None) == rep.SECTION8["c"]
    assert rep.section8(True, True, "apoyada") == rep.SECTION8["apoyada"]
    assert rep.section8(True, True, "no apoyada") == rep.SECTION8["no apoyada"]
    assert rep.section8(True, True, "no evaluable") == rep.section8(True, True, "no concluyente") == rep.SECTION8["otro"]


def test_g0_failure_stops_the_report_and_ignores_later_files():
    text = rep.render(_g0(False), _cal(True), _lit(), _test())
    assert "G0: **no superada**" in text and "| **no** |" in text
    assert "Puerta C" not in text and "## Prueba" not in text
    assert "Las señales no se pueden calcular" in text
    assert "| Pasa la puerta C | 40 % | no aplica |" in text


def test_gate_c_failure_closes_the_test():
    text = rep.render(_g0(), _cal(False), _lit())
    assert "**no superada**" in text and "**La prueba no se abre.**" in text and "## Prueba" not in text
    assert "| verde | 3 | 1 | 4 | 1 |" in text and "Dentro del dominio: 5 de 6." in text
    assert "| Pasa G0 | 90 % | sí |" in text and "| Pasa la puerta C | 40 % | no |" in text
    assert "| H20b evaluable, dado que se abre la prueba | 45 % | no aplica |" in text
    # un fichero de prueba presente no se informa si la puerta C no se superó
    assert "## Prueba" not in rep.render(_g0(), _cal(False), _lit(), _test())


def test_full_run_transcribes_verdicts_and_predictions():
    text = rep.render(_g0(), _cal(True), _lit(), _test())
    assert "`" + "ab" * 32 + "`" in text
    assert "| H20b (primaria): fallos entre verdes | 4,0 % | 0,0 % a 12,0 % | **apoyada** |" in text
    assert "luces: verde 25, amarillo 15, rojo 4." in text
    assert "una luz verde dada solo por la estabilidad" in text
    assert "| H20b apoyada, dado que es evaluable | 60 % | sí |" in text
    assert "(H20c) | 60 % | sí |" in text


def test_not_evaluable_marks_the_conditional_prediction_as_not_applicable():
    t = _test("no evaluable", ok10=0.70)
    t["h20b"].update(estimate=None, ci=None)
    text = rep.render(_g0(), _cal(True), _lit(), t)
    assert "| — | — | **no evaluable** |" in text
    assert "| H20b evaluable, dado que se abre la prueba | 45 % | no |" in text
    assert "| H20b apoyada, dado que es evaluable | 60 % | no aplica |" in text
    assert "(H20c) | 60 % | no |" in text and "Pocas verdes o pocos embriones" in text


def test_main_requires_g0_and_reads_partial_directories(tmp_path, capsys):
    import json
    import pytest
    with pytest.raises(SystemExit):
        rep.main(["--dir", str(tmp_path)])
    (tmp_path / "g0.json").write_text(json.dumps(_g0()), encoding="utf-8")
    assert rep.main(["--dir", str(tmp_path), "--out", str(tmp_path / "informe.md")]) == 0
    assert "G0: **superada**" in (tmp_path / "informe.md").read_text(encoding="utf-8")
