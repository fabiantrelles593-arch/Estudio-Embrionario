"""H26: separación con S-1, evaluación de cuerpo y ventrículo, y G0-datos (todo sintético)."""
import numpy as np
import pandas as pd

from geovida import h20, h24, h26


def _lit(n_green, n_other, fail_green, fail_other, kind="body", seed=0):
    rng = np.random.default_rng(seed)
    n = n_green + n_other
    green = np.array([True] * n_green + [False] * n_other)
    bad = np.zeros(n, bool)
    bad[rng.choice(n_green, fail_green, replace=False)] = True
    bad[n_green + rng.choice(n_other, fail_other, replace=False)] = True
    df = pd.DataFrame({"embryo_id": [f"e{i}" for i in range(n)],
                       "light": np.where(green, "verde", np.where(np.arange(n) % 2, "amarillo", "rojo")),
                       "light_without_guard": np.where(green, "verde", "amarillo"),
                       "in_domain": True, "dice": 0.9, "snr_hat": 5.0})
    if kind == "body":
        df["rel_error_volume"] = np.where(bad, 0.2, 0.01)
    else:
        df["e_b"] = np.where(bad, 1.0, 0.1)
    return df, bad


def test_s1_needs_ten_failures():
    df, bad = _lit(20, 20, 1, 8)
    r = h26.separation_s1(df, bad)
    assert r["verdict"] == "no evaluable" and "menos de 10 fallos (S-1)" in r["reasons"]


def test_s1_needs_a_failure_in_each_group():
    df, bad = _lit(30, 30, 0, 12)
    r = h26.separation_s1(df, bad)
    assert r["verdict"] == "no evaluable" and "algún grupo sin fallos (S-1)" in r["reasons"]


def test_s1_blocks_the_degenerate_no_separa():
    """El caso del defecto de §4 de la nota: sin fallos entre no verdes, la regla antigua podía decir «no separa»."""
    df, bad = _lit(20, 20, 2, 0)
    assert h26.separation_s1(df, bad)["verdict"] == "no evaluable"


def test_s1_separates_with_enough_failures():
    df, bad = _lit(60, 60, 2, 25)
    r = h26.separation_s1(df, bad)
    assert r["verdict"] == "separa" and r["ci"][0] > 0


def test_s1_matches_h24_rule_when_evaluable():
    df, bad = _lit(40, 40, 4, 10, kind="ventricle", seed=3)
    assert h26.separation_s1(df, bad)["verdict"] == h24.separation(df)["verdict"]


def test_evaluate_body_and_ventricle_keys():
    df, _ = _lit(25, 25, 1, 10)
    rb = h26.evaluate_body(df)
    assert {"r1a", "r1b", "r1c", "r1d", "r1e", "r1g"} <= set(rb)
    assert rb["r1g"]["fail_all"] == 11 / 50
    dv, _ = _lit(25, 25, 1, 10, kind="ventricle")
    rv = h26.evaluate_ventricle(dv)
    assert {"v1a", "v1b", "v1c", "v1d", "v1e", "v1g"} <= set(rv)


def test_body_failure_is_h20b_definition():
    df = pd.DataFrame({"rel_error_volume": [0.10, -0.1000001, 0.05]})
    assert h26.body_bad(df).tolist() == [False, True, False]


def _manifest(images, embryos, structure="body"):
    return pd.DataFrame({"image": images, "label": [i + ".lab" for i in images], "label_value": 1,
                         "embryo_id": embryos, "structure": structure})


def test_g0_datos_passes_and_counts():
    m = _manifest(["a", "b", "c"], ["n1", "n2", "n2"])
    r = h26.g0_datos(m, {"a": "1", "b": "2", "c": "3"}, {"p": "9"}, {"p1"}, "terms", [])
    assert r["passed"] and r["counts"]["body"] == {"volumes": 3, "embryos": 2}


def test_g0_datos_excludes_public_overlap():
    m = _manifest(["a", "b", "c"], ["n1", "p1", "n3"])
    r = h26.g0_datos(m, {"a": "9", "b": "2", "c": "3"}, {"p": "9"}, {"p1"}, "terms", [])
    assert r["excluded_same_file"] == ["a"] and r["excluded_same_embryo"] == ["p1"] and r["n_kept"] == 1


def test_g0_datos_fails_without_terms_or_files():
    m = _manifest(["a"], ["n1"])
    assert not h26.g0_datos(m, {"a": "1"}, {}, set(), None, [])["passed"]
    assert not h26.g0_datos(m, {"a": "1"}, {}, set(), "t", ["a.lab"])["passed"]
    assert not h26.g0_datos(m.drop(columns=["structure"]), {"a": "1"}, {}, set(), "t", [])["passed"]


def test_frozen_hashes_are_the_preregistered_ones():
    assert h26.FROZEN["body"]["sha256"].startswith("66d7ffcf")
    assert h26.FROZEN["ventricle"]["sha256"].startswith("91ba4f3d")
    assert h20.THRESHOLDS["green_flip"] == 0.05 and h24.THRESHOLDS["tol_voxels"] == 0.5
