"""H18 (``docs/PREREGISTRO_H18.md``): reparto por embrión, segmentador con limpieza, certificado y candado.

Solo volúmenes sintéticos y tablas fabricadas; ninguna imagen real. Qué haría fallar cada prueba:
* si un embrión pudiera quedar a los dos lados del reparto, la prueba vería algo del entrenamiento;
* si ``smooth_lcc`` no quitara las islas del moteado, el volumen saldría inflado como en H11;
* si la puerta F usara el propio embrión para ajustar su predicción, una relación inventada pasaría;
* si ``check_frozen`` aceptara otro archivo, se podría reajustar después de ver la prueba.
"""
import json

import numpy as np
import pandas as pd
import pytest

from geovida import h18


def _speckle_ball(n=64, radius=18.0, seed=0, islands=True):
    rng = np.random.default_rng(seed)
    zz, yy, xx = np.mgrid[:n, :n, :n]
    c = (n - 1) / 2
    inside = ((zz - c) ** 2 + (yy - c) ** 2 + (xx - c) ** 2) <= radius ** 2
    img = np.where(inside, 1.0, 0.25) * rng.rayleigh(1.0, inside.shape)   # moteado multiplicativo
    if islands:                                                              # ecos brillantes fuera
        for _ in range(40):
            p = rng.integers(2, n - 4, 3)
            img[p[0]:p[0] + 3, p[1]:p[1] + 3, p[2]:p[2] + 3] = 3.0
    return img.astype(np.float32), inside


def test_split_keeps_each_embryo_on_one_side():
    m = pd.DataFrame({"embryo_id": ["A", "A", "B", "C", "D"],
                      "image": ["nii_train/E11/a.nii", "nii_test/E11/a2.nii", "nii_train/E12/b.nii",
                                "nii_test/E12/c.nii", "nii_hard/x.nii".replace("nii_hard", "nii_train")]})
    df, rep = h18.split_cases(m)
    assert df.loc[df.embryo_id == "A", "split"].eq("train").all()
    assert rep["embryos_in_both"] == ["A"] and rep["test_cases_moved_to_train"] == 1
    assert set(df.loc[df.split == "test", "embryo_id"]) == {"C"}
    assert not set(df.loc[df.split == "test", "embryo_id"]) & set(df.loc[df.split == "train", "embryo_id"])
    with pytest.raises(ValueError):
        h18.split_cases(pd.DataFrame({"embryo_id": ["X"], "image": ["otra/x.nii"]}))


def test_smooth_lcc_removes_speckle_islands_that_inflate_otsu():
    img, inside = _speckle_ball()
    sp = (0.05, 0.05, 0.05)
    plain = h18.smooth_lcc(img, sp, sigma=2.0, thr=1.0, close=0)
    from geovida.segment import segment
    raw = segment("smoothed_otsu", img, sp)
    err_plain = abs(plain.sum() - inside.sum()) / inside.sum()
    err_raw = abs(raw.sum() - inside.sum()) / inside.sum()
    assert err_plain < 0.10 < err_raw or err_plain < err_raw / 2
    from scipy import ndimage as ndi
    assert ndi.label(plain, structure=np.ones((3, 3, 3)))[1] == 1


def test_grid_rows_and_select_config_with_tie_breaks():
    img, inside = _speckle_ball(seed=1)
    rows = h18.grid_rows(img, (0.05,) * 3, inside, grid=h18.GRID[:4])
    assert len(rows) == 4 and all({"rel_error_volume", "dice"} <= set(r) for r in rows)
    t = pd.DataFrame([
        {"sigma": 1.0, "thr": 1.0, "close": 0, "rel_error_volume": 0.05, "dice": 0.8},
        {"sigma": 2.0, "thr": 1.0, "close": 0, "rel_error_volume": 0.05, "dice": 0.8},
        {"sigma": 4.0, "thr": 1.0, "close": 0, "rel_error_volume": 0.50, "dice": 0.9}])
    best = h18.select_config(t)
    assert (best["sigma"], best["thr"], best["close"]) == (1.0, 1.0, 0) and best["train_ok10"] == 1.0
    assert h18.config_key(best) == "s1_t1_c0"
    assert len(h18.GRID) == 18


def _table(n_embryos=60, per=2, seed=0, informative=True):
    """Filas con observables; si ``informative``, el error depende de d_over_hgeo."""
    rng = np.random.default_rng(seed)
    rows = []
    for e in range(n_embryos):
        for _ in range(per):
            d = float(np.exp(rng.uniform(0.0, 3.0)))
            if informative:
                err = rng.normal(0, 0.3 if d < 5 else 0.02)
            else:
                err = rng.normal(0, 0.3)
            rows.append({"embryo_id": f"E{e}", "d_over_hgeo": d, "snr_hat": float(rng.uniform(5, 9)),
                         "edge_width": float(rng.uniform(1.0, 2.0)), "rel_error_volume": err, "dice": 0.9})
    return pd.DataFrame(rows)


def test_feasibility_gate_passes_only_when_the_observables_predict_the_error():
    good = h18.feasibility_gate(_table(), n_boot=200)
    assert good["passed"] and good["n_green"] >= h18.MIN_GREEN
    bad = h18.feasibility_gate(_table(informative=False), n_boot=200)
    assert not bad["passed"] and bad["verdict"] in {"no evaluable", "no apoyada", "no concluyente"}


def test_out_of_fold_never_uses_the_row_embryo():
    df = _table(n_embryos=20)
    folds = h18.embryo_folds(df["embryo_id"])
    assert set(folds.values()) == set(range(h18.N_FOLDS))
    assert h18.embryo_folds(df["embryo_id"]) == folds          # semilla fija
    oof = h18.out_of_fold(df)
    assert list(oof.index) == list(df.index) and {"p_ok10", "light", "in_domain"} <= set(oof.columns)


def test_guard_caps_green_outside_the_training_envelope():
    df = _table()
    cert = h18.fit_certificate(df)
    far = df.head(5).assign(d_over_hgeo=20.0, snr_hat=50.0)      # fuera de la envolvente de snr
    lit = h18.lights(far, cert)
    assert not lit["in_domain"].any() and (lit["light"] != "verde").all()
    assert (lit["light_without_guard"] == "verde").any()


def test_green_failure_rules():
    base = _table(n_embryos=30, per=1)
    g = base.assign(light="verde", rel_error_volume=0.01)
    assert h18.green_failure(g, n_boot=200)["verdict"] == "apoyada"
    g2 = base.assign(light="verde", rel_error_volume=0.5)
    out = h18.green_failure(g2, n_boot=200)
    assert out["verdict"] == "no apoyada" and out["ci"][0] > 0.10
    few = base.head(10).assign(light="verde")
    assert h18.green_failure(few, n_boot=200)["verdict"] == "no evaluable"


def test_frozen_lock_refuses_any_other_file(tmp_path):
    cert = h18.fit_certificate(_table())
    p = tmp_path / "h18_frozen.json"
    sha = h18.freeze(p, {"sigma": 2.0, "thr": 1.0, "close": 0}, cert, {"train_manifest_sha256": "x"})
    assert h18.check_frozen(p, sha)["config"]["sigma"] == 2.0
    with pytest.raises(PermissionError):
        h18.check_frozen(p, "0" * 64)
    with pytest.raises(PermissionError):
        h18.check_frozen(p, "")
    data = json.loads(p.read_text(encoding="utf-8"))
    data["model"]["intercept"] += 1
    p.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(PermissionError):
        h18.check_frozen(p, sha)


def test_runner_reads_only_the_requested_side(tmp_path):
    """``develop`` y ``observe`` piden ``train``: ningún caso de prueba puede colarse."""
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(
        "run_h18", Path(__file__).resolve().parents[1] / "scripts" / "run_h18.py")
    run = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run)
    m = pd.DataFrame({"embryo_id": ["A", "A", "B", "C"], "structure": ["body", "body", "body", "ventricle"],
                      "image": ["nii_train/a.nii", "nii_test/a2.nii", "nii_test/b.nii", "nii_train/c.nii"],
                      "label": ["l"] * 4, "label_value": [1] * 4})
    p = tmp_path / "m.csv"
    m.to_csv(p, index=False)
    train, _ = run._cases(str(p), "train")
    test, _ = run._cases(str(p), "test")
    assert list(train["image"]) == ["nii_train/a.nii", "nii_test/a2.nii"]      # A entero en train
    assert list(test["image"]) == ["nii_test/b.nii"]                            # sin ventrículo
    assert not set(train["embryo_id"]) & set(test["embryo_id"])


def test_evaluate_test_reports_every_hypothesis():
    train, test = _table(seed=0), _table(n_embryos=30, seed=5)
    cert = h18.fit_certificate(train)
    res = h18.evaluate_test(test, cert, n_boot=200)
    assert {"h18a", "h18b", "h18c", "h18d"} <= set(res)
    assert res["n_embryos"] == 30 and 0 <= res["h18a"]["green_fraction"] <= 1
