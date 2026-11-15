"""Pruebas del análisis de P3 (docs/PREREGISTRO_P3.md) con fantomas y tablas sintéticas.

No hay ningún dato de MusMorph: cada prueba fija de antemano qué resultado debe dar el análisis en un caso
construido a propósito (verdad conocida).
"""
import math

import numpy as np
import pandas as pd
import pytest
from scipy import ndimage as ndi

from geovida import p3


def _ball(shape, center, r):
    g = np.indices(shape).astype(float)
    d2 = sum((g[i] - center[i]) ** 2 for i in range(3))
    return d2 <= r ** 2


# --------------------------------------------------------------------------- degradación

def test_degrade_identity_power_of_two_and_volume():
    m = _ball((47, 48, 49), (23, 24, 24), 12.0)
    assert np.array_equal(p3.degrade_mask(m, 1), m)
    for k in (2, 4):
        d = p3.degrade_mask(m, k)
        assert d.dtype == bool
        assert d.shape == tuple(math.ceil(s / k) for s in m.shape)
        assert d.sum() * k ** 3 == pytest.approx(m.sum(), rel=0.05)
    with pytest.raises(ValueError):
        p3.degrade_mask(m, 3)


def test_aligned_crop_gives_the_same_degraded_volume_as_the_full_volume():
    m = _ball((64, 64, 64), (37, 21, 45), 7.3)
    box = p3._aligned_box(m)
    for k in (2, 4):
        assert p3.degrade_mask(m[box], k).sum() == p3.degrade_mask(m, k).sum()


# --------------------------------------------------------------------------- τ

def _table(values):
    """values[i][c] -> tabla con un solo segmentador y una condición por factor."""
    rows = []
    for i, conds in enumerate(values):
        for c, v in enumerate(conds):
            rows.append({"specimen": f"s{i}", "structure": 1, "segmenter": "A", "factor": 2 ** c,
                         "log_volume": v, "volume": math.exp(v) if math.isfinite(v) else 0.0,
                         "p_cert": math.nan})
    return pd.DataFrame(rows)


def test_tau_is_zero_without_technical_variation_and_one_without_biological_variation():
    no_tech = p3.technical_fraction(_table([[v, v, v] for v in (1.0, 1.5, 2.0, 2.2)]))
    assert no_tech.loc[0, "tau"] == pytest.approx(0.0)
    no_bio = p3.technical_fraction(_table([[1.0, 1.2, 1.5]] * 4))
    assert no_bio.loc[0, "tau"] == pytest.approx(1.0)


def test_specimen_with_missing_condition_is_dropped_and_counted():
    t = p3.technical_fraction(_table([[1.0, 1.1, 1.2], [2.0, 2.1, math.nan], [1.5, 1.4, 1.6]]))
    assert t.loc[0, "n_specimens"] == 2 and t.loc[0, "n_dropped"] == 1
    assert 0.0 <= t.loc[0, "tau"] <= 1.0


# --------------------------------------------------------------------------- fantoma completo

SHAPE = (56, 40, 40)


def _specimen(rng):
    """Etiqueta 1: bola compacta (radio con variación biológica). Etiqueta 2: placa delgada de 5 vóxeles."""
    lab = np.zeros(SHAPE, np.uint8)
    lab[_ball(SHAPE, (18, 20, 20), 13.0 + rng.normal(0, 0.8))] = 1
    hy = min(19, int(round(13 + rng.normal(0, 1.5))))
    lab[42:47, 20 - hy:20 + hy, 7:33] = 2
    return lab


def _dilated(lab):
    out = np.zeros_like(lab)
    for s in (1, 2):
        out[ndi.binary_dilation(lab == s) & (out == 0)] = s
    return out


@pytest.fixture(scope="module")
def phantom_table():
    rng = np.random.default_rng(7)
    items = []
    for i in range(6):
        a = _specimen(rng)
        items.append((f"e{i}", {"A": a, "B": _dilated(a)}, (0.027, 0.027, 0.027)))
    return p3.condition_table(items, labels=[1, 2]), items[0][1]["A"]


def test_thin_plate_has_higher_technical_fraction_than_compact_ball(phantom_table):
    df, _ = phantom_table
    assert len(df) == 6 * 2 * 2 * 3
    t = p3.technical_fraction(df).set_index("structure")
    assert (t["n_dropped"] == 0).all()
    assert t.loc[2, "tau"] > t.loc[1, "tau"]
    assert 0.0 < t.loc[1, "tau"] < 1.0


def test_certificate_only_on_native_resolution_of_the_first_segmenter(phantom_table):
    df, _ = phantom_table
    has_p = df[np.isfinite(df["p_cert"])]
    assert set(has_p["segmenter"]) == {"A"} and set(has_p["factor"]) == {1}
    assert has_p["p_cert"].between(0, 1).all()


def test_groups_from_atlas_put_the_plate_in_the_thin_group(phantom_table):
    _, atlas = phantom_table
    g = p3.groups_from_atlas(atlas, (0.027,) * 3, [1, 2]).set_index("unit")
    assert g.loc["2", "group"] == p3.GROUP_THIN and g.loc["1", "group"] == p3.GROUP_COMPACT
    assert g.loc["2", "d_over_hgeo"] < g.loc["1", "d_over_hgeo"]


def test_units_merge_left_and_right_labels(phantom_table):
    _, atlas = phantom_table
    g = p3.groups_from_atlas(atlas, (0.027,) * 3, [1, 2], units={1: "par", 2: "par"})
    assert list(g["unit"]) == ["par"]


def test_label_variation_detects_atlas_space(phantom_table):
    df, _ = phantom_table
    assert p3.label_variation(df, "A")["passed"]
    same = df.copy()
    same["volume"] = same.groupby(["structure", "segmenter", "factor"])["volume"].transform("first")
    assert not p3.label_variation(same, "A")["passed"]


# --------------------------------------------------------------------------- veredictos

def _synthetic(n_spec=20, n_units=16, seed=3, thin_noise=0.30, compact_noise=0.05):
    rng = np.random.default_rng(seed)
    rows, groups = [], []
    for u in range(n_units):
        thin = u < n_units // 2
        bio = rng.normal(0, 0.2, n_spec)
        for i in range(n_spec):
            for seg in ("A", "B"):
                for k in (1, 2, 4):
                    v = 3.0 + bio[i] + rng.normal(0, thin_noise if thin else compact_noise)
                    p = (0.2 if thin else 0.9) + rng.normal(0, 0.02) if (seg == "A" and k == 1) else math.nan
                    rows.append({"specimen": f"s{i}", "structure": u, "segmenter": seg, "factor": k,
                                 "log_volume": v, "volume": math.exp(v), "p_cert": p})
        groups.append({"unit": str(u), "group": p3.GROUP_THIN if thin else p3.GROUP_COMPACT,
                       "log_volume": rng.normal(0, 1)})
    return pd.DataFrame(rows), pd.DataFrame(groups)


def test_hp3a_supported_when_thin_structures_are_technically_noisier():
    df, groups = _synthetic()
    out = p3.evaluate(df, groups, n_boot=200, seed=1)
    assert out["verdict_a"] == "apoyada"
    assert out["delta"] > 0 and out["delta_ci"][0] > 0
    assert out["n_units"] == {p3.GROUP_THIN: 8, p3.GROUP_COMPACT: 8}
    assert out["verdict_b"] in ("apoyada", "no_apoyada")
    assert out["rho"] < 0


def test_hp3a_not_evaluable_with_too_few_units():
    df, groups = _synthetic(n_units=6)
    assert p3.evaluate(df, groups, n_boot=50, seed=1)["verdict_a"] == "no_evaluable"


def test_bootstrap_is_reproducible_with_the_same_seed():
    df, groups = _synthetic(n_spec=10)
    a = p3.evaluate(df, groups, n_boot=100, seed=5)
    b = p3.evaluate(df, groups, n_boot=100, seed=5)
    assert a["delta_ci"] == b["delta_ci"] and a["rho_partial_ci"] == b["rho_partial_ci"]


def test_partial_spearman_known_cases():
    rng = np.random.default_rng(0)
    x = rng.normal(size=50)
    z = rng.normal(size=50)
    assert p3.partial_spearman(x, x, z) == pytest.approx(1.0)
    assert p3.spearman(x, -x) == pytest.approx(-1.0)
    assert math.isnan(p3.spearman([1, 1, 1], [1, 2, 3]))


# --------------------------------------------------------------------------- muestreo

def _meta():
    rows = []
    for sex in ("F", "M"):
        for i in range(30):
            rows.append({"Biosample": f"IMPC_E15.5_{sex}{i:03d}", "Stage": "E15.5", "Dataset": "IMPC",
                         "Zygosity": "Wildtype", "Sex": sex})
    rows += [{"Biosample": "IMPC_E15.5_X", "Stage": "E15.5", "Dataset": "IMPC", "Zygosity": "Wildtype", "Sex": "NA"},
             {"Biosample": "IMPC_E15.5_MUT", "Stage": "E15.5", "Dataset": "IMPC", "Zygosity": "Homozygous", "Sex": "F"},
             {"Biosample": "IMPC_E18.5_W", "Stage": "E18.5", "Dataset": "IMPC", "Zygosity": "Wildtype", "Sex": "M"}]
    return pd.DataFrame(rows)


def test_select_specimens_is_balanced_disjoint_deterministic_and_prefix_stable():
    meta = _meta()
    a = p3.select_specimens(meta, n_pilot=4, n_confirm=6)
    b = p3.select_specimens(meta, n_pilot=4, n_confirm=6)
    big = p3.select_specimens(meta, n_pilot=4, n_confirm=10)
    assert a == b and a["n_eligible"] == 60
    assert not set(a["pilot"]) & set(a["confirm"])
    assert sum("_F" in s for s in a["confirm"]) == 3
    assert a["pilot"] == big["pilot"]
    assert set(a["confirm"]) <= set(big["confirm"])
    assert not {"IMPC_E15.5_X", "IMPC_E15.5_MUT", "IMPC_E18.5_W"} & set(big["pilot"] + big["confirm"])
    excl = p3.select_specimens(meta, n_pilot=4, n_confirm=6, exclude=a["pilot"][:1])
    assert a["pilot"][0] not in excl["pilot"] + excl["confirm"]
    with pytest.raises(ValueError):
        p3.select_specimens(meta, n_pilot=40, n_confirm=40)
