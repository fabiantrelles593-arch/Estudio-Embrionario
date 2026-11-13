"""H16: ¿puede el certificado enterarse, solo con la imagen, de que pasó por una cadena? (solo simulación)

Aquí se prueba el *cableado* del experimento con casos pequeños y tablas construidas a mano: que los casos sean reproducibles y
etiqueten su familia, que la ejecución mida la misma imagen con y sin cadena, que los índices salgan de la imagen (no de la verdad), que el
certificado ajustado no haga nada cuando el ajuste es cero y se niegue fuera del soporte, y que las reglas de veredicto hagan lo escrito.
Los resultados del experimento mismo no están en estas pruebas.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from geovida import biometry as bio
from geovida import chainguard as cg
from geovida import h16

FROZEN = Path(__file__).resolve().parents[1] / "results" / "summary" / "h14_frozen.json"


@pytest.fixture(scope="module")
def models():
    return bio.models_from_json(FROZEN.read_text())


# --------------------------------------------------------------------------- casos

def test_cases_are_reproducible_in_box_only_and_tag_their_family():
    a1, a2 = h16.cases(5, 123, "A"), h16.cases(5, 123, "A")
    assert [c["chain"] for c in a1] == [c["chain"] for c in a2]
    assert len(a1) == 10 and {c["region"] for c in a1} == {"in"}
    assert {c["family"] for c in a1} == {"A"} and all("compression_a" in c["chain"] for c in a1)
    b = h16.cases(5, 123, "B")
    assert {c["family"] for c in b} == {"B"} and all(c["chain"]["family"] == "B" for c in b)
    assert [c["size_mm"] for c in a1] == [c["size_mm"] for c in b]            # mismo diseño de casos, otra familia de cadena


def test_unknown_family_is_rejected():
    with pytest.raises(ValueError):
        h16.cases(2, 1, "C")


# --------------------------------------------------------------------------- ejecución

def test_run_measures_the_same_case_clean_and_through_the_chain(models):
    df = h16.run(h16.cases(3, 7, "A"), models, n_jobs=1)
    assert len(df) == 12 and set(df["variant"]) == {"clean", "chain"}
    need = {"idx", "kind", "family", "variant", "truth_mm", "h_mm", "measured_mm", "ln_cv", "skew", "light", "correct",
            "resid_px", "sd_clean_px", "in_domain"}
    assert need <= set(df.columns)
    for (_, _), g in df.groupby(["idx", "kind"]):
        c, k = g[g["variant"] == "chain"].iloc[0], g[g["variant"] == "clean"].iloc[0]
        assert c["truth_mm"] == k["truth_mm"] and c["h_mm"] == k["h_mm"]
        assert c["ln_cv"] < k["ln_cv"]                               # la compresión aplana el grano que ve el índice


def test_family_b_changes_the_table_but_not_the_clean_rows(models):
    a = h16.run(h16.cases(3, 11, "A"), models, 1)
    b = h16.run(h16.cases(3, 11, "B"), models, 1)
    ca, cb = a[a["variant"] == "clean"].reset_index(drop=True), b[b["variant"] == "clean"].reset_index(drop=True)
    assert np.allclose(ca["measured_mm"], cb["measured_mm"]) and np.allclose(ca["ln_cv"], cb["ln_cv"])
    xa, xb = a[a["variant"] == "chain"], b[b["variant"] == "chain"]
    assert not np.allclose(xa["ln_cv"], xb["ln_cv"])


# --------------------------------------------------------------------------- entrenamiento y certificado ajustado

def test_training_table_labels_regimes_and_drops_rows_without_a_residual(models):
    df = h16.run(h16.cases(4, 13, "A"), models, 1)
    t = h16.training_table(df)
    assert set(t["regime"]) <= {"clean", "chain"} and t["resid_px"].notna().all()
    assert (t[t["regime"] == "clean"].index.isin(df[df["variant"] == "clean"].index)).all()
    assert {"kind", "regime", "ln_cv", "skew", "resid_px", "sd_clean_px"} <= set(t.columns)


def _frame(n=400, shift=0.0):
    """Tabla a mano: dos regímenes bien separados; sirve para fit/apply/evaluación sin renderizar."""
    rng = np.random.default_rng(5)
    rows = []
    for v, lo, hi, sk in (("clean", 1.1, 1.4, (2.0, 2.6)), ("chain", -1.8, -0.5, (0.4, 1.2))):
        for i in range(n):
            rows.append({"idx": i, "kind": "body", "family": "A", "variant": v, "regime": v, "region": "in", "truth_mm": 40.0, "h_mm": 0.3,
                         "measured_mm": 40.0 + rng.normal(shift if v == "chain" else 0.0, 0.5), "fwhm_px": 2.5,
                         "ln_cv": rng.uniform(lo, hi), "skew": rng.uniform(*sk), "segmenter": "smoothed_otsu",
                         "sd_clean_px": 1.0, "resid_px": rng.normal(shift if v == "chain" else 0.0, 1.0)})
    return pd.DataFrame(rows)


def test_apply_chain_aware_is_the_same_as_the_baseline_when_the_adjustment_is_zero(models):
    df = h16.run(h16.cases(6, 17, "A"), models, 1)
    clean = df[df["variant"] == "clean"]
    zero = cg.ChainModel("body", (cg.Regime("clean", {"ln_cv": (-9.0, 9.0), "skew": (-9.0, 9.0)}, (), (0.0,), (0.0,), (100,)),))
    zero_slot = cg.ChainModel("slot", (cg.Regime("clean", {"ln_cv": (-9.0, 9.0), "skew": (-9.0, 9.0)}, (), (0.0,), (0.0,), (100,)),))
    out = h16.apply_chain_aware(clean, models, {"body": zero, "slot": zero_slot})
    both = out[out["in_domain"].astype(bool)]
    assert len(both) > 0 and (both["light_cg"] == both["light"]).all()
    assert np.allclose(both["p_cg"].to_numpy(float), both["p"].to_numpy(float))


def test_apply_chain_aware_refuses_green_outside_the_support(models):
    df = h16.run(h16.cases(6, 19, "A"), models, 1)
    nowhere = cg.ChainModel("body", (cg.Regime("chain", {"ln_cv": (50.0, 51.0), "skew": (50.0, 51.0)}, (), (0.0,), (0.0,), (100,)),))
    nowhere_s = cg.ChainModel("slot", nowhere.regimes)
    out = h16.apply_chain_aware(df, models, {"body": nowhere, "slot": nowhere_s})
    assert (out["light_cg"] != "verde").all() and (~out["in_domain_cg"].astype(bool)).all()


def test_fit_returns_one_model_per_kind_and_json_round_trips(models):
    t = _frame()
    t2 = t.copy()
    t2["kind"] = "slot"
    fitted = h16.fit(pd.concat([t, t2], ignore_index=True))
    assert set(fitted) == {"body", "slot"}
    again = h16.chain_models_from_json(h16.chain_models_to_json(fitted, {"nota": "prueba"}))
    probe = {"ln_cv": -1.0, "skew": 0.8}
    assert again["body"].adjustment(probe) == fitted["body"].adjustment(probe)


# --------------------------------------------------------------------------- reglas de veredicto

def _paired(n, green_base_clean, green_cg_chain):
    """Casos emparejados: ``n`` con verdes correctos en la limpia (base) y los ``green_cg_chain`` primeros con verde correcto en la cadena."""
    rows = []
    for i in range(n):
        for v in ("clean", "chain"):
            g = (i < green_base_clean) if v == "clean" else (i < green_cg_chain)
            rows.append({"idx": i, "kind": "body", "variant": v, "region": "in", "segmenter": "smoothed_otsu",
                         "light": "verde" if (v == "clean" and g) else "amarillo",
                         "light_cg": "verde" if (v == "chain" and g) else "amarillo", "correct": True})
    return pd.DataFrame(rows)


def test_retention_verdict_follows_the_written_thresholds():
    ok = h16.retention_verdict(_paired(400, 300, 240), "body", n_boot=300, seed=1)
    assert ok["ratio"] == pytest.approx(0.8) and ok["verdict"] == "apoyada"
    bad = h16.retention_verdict(_paired(400, 300, 60), "body", n_boot=300, seed=1)
    assert bad["ratio"] == pytest.approx(0.2) and bad["verdict"] == "no apoyada"
    mid = h16.retention_verdict(_paired(400, 300, 150), "body", n_boot=300, seed=1)
    assert mid["verdict"] == "no concluyente" and mid["ci"][0] < 0.5 <= mid["ci"][1] + 0.1


def test_retention_verdict_is_not_evaluable_with_few_reference_greens():
    r = h16.retention_verdict(_paired(100, 10, 5), "body", n_boot=100, seed=1)
    assert r["verdict"] == "no evaluable"


def test_evaluate_h16_returns_every_hypothesis_and_the_descriptive_block(models):
    a = h16.run(h16.cases(6, 23, "A"), models, 1)
    b = h16.run(h16.cases(6, 29, "B"), models, 1)
    train = h16.training_table(pd.concat([a, b]))
    cm = {"body": cg.fit_chain_model(_frame(), "body"), "slot": cg.fit_chain_model(_frame().assign(kind="slot"), "slot")}
    a2, b2 = h16.apply_chain_aware(a, models, cm), h16.apply_chain_aware(b, models, cm)
    out = h16.evaluate_h16(a2, b2, n_boot=50, seed=3)
    assert {"h16a", "h16b", "h16c", "h16d", "h16e", "h16f", "descriptive"} <= set(out)
    assert {"baseline_false_green", "out_of_support", "greens"} <= set(out["descriptive"])
    assert len(train) > 0


def _eval_frame(n=300):
    """Tabla a mano para las reglas: el semáforo base da verde siempre; la guardia lo quita justo donde la cadena hizo errar."""
    rows = []
    for kind, off in ((bio.BODY, 0), (bio.SLOT, n)):
        for i in range(n):
            wrong = i % 2 == 0
            for v in ("clean", "chain"):
                bad = wrong and v == "chain"
                rows.append({"idx": i + off, "kind": kind, "variant": v, "region": "in", "segmenter": "smoothed_otsu",
                             "light": "verde", "light_cg": "amarillo" if bad else "verde", "in_domain": True,
                             "in_domain_cg": True, "p": 0.9, "p_cg": 0.9, "correct": not bad})
    return pd.DataFrame(rows)


def test_evaluate_h16_scores_the_guarded_certificate_and_reports_the_baseline_apart():
    df = _eval_frame()
    out = h16.evaluate_h16(df, df, n_boot=200, seed=1)
    assert out["h16a"]["false_green"] == 0.0 and out["h16a"]["verdict"] == "apoyada"
    base = out["descriptive"]["baseline_false_green"]["A|body"]
    assert base["false_green"] == pytest.approx(0.5) and base["verdict"] == "no apoyada"
    assert out["h16d"]["A"]["ratio"] == pytest.approx(0.5)
    assert out["h16e"]["verdict"] == "apoyada"
    assert out["h16f"]["body"]["ratio"] == pytest.approx(1.0) and out["h16f"]["verdict"] == "apoyada"
    assert out["descriptive"]["greens"]["A|body"] == {"base_on_chain": 300, "guard_on_chain": 150, "base_on_clean": 300}


def test_clean_cost_fails_when_the_guard_removes_more_than_a_tenth_of_the_clean_greens():
    df = _eval_frame()
    df.loc[(df["variant"] == "clean") & (df["idx"] % 5 < 2), "light_cg"] = "amarillo"      # quita el 40 % de los verdes limpios
    out = h16.evaluate_h16(df, df, n_boot=100, seed=1)
    assert out["h16f"]["body"]["ratio"] == pytest.approx(0.6) and out["h16f"]["verdict"] == "no apoyada"


def test_training_table_marks_clean_images_as_the_clean_regime():
    df = _eval_frame(6).assign(in_domain=True, ln_cv=1.0, skew=1.0, resid_px=0.1, sd_clean_px=0.5, family="A")
    t = h16.training_table(df)
    assert (t["regime"].to_numpy() == np.where(df["variant"] == "clean", "clean", "chain")).all()


def test_training_table_leaves_out_cases_outside_the_calibrated_box():
    df = _eval_frame(6).assign(in_domain=True, ln_cv=1.0, skew=1.0, resid_px=0.1, sd_clean_px=0.5, family="A")
    df.loc[df["idx"] == 0, "region"] = "n_high"
    t = h16.training_table(df)
    assert 0 not in set(t["idx"]) and len(t) == len(df) - 2        # las dos filas (limpia y con cadena) del caso 0
