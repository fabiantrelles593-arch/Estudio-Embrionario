"""Pruebas de geovida.onto_map con poblaciones sintéticas de alometría conocida."""
import numpy as np
import pandas as pd
import pytest
from scipy.spatial.transform import Rotation

from geovida import onto_map as om

K = 40
RNG = np.random.default_rng(11)
MEAN = RNG.normal(size=(K, 3))


def _unit(v):
    v = v - v.mean(axis=0)
    return v / np.linalg.norm(v)


D = _unit(RNG.normal(size=(K, 3)))
OTHER = _unit(RNG.normal(size=(K, 3)))
OTHER = _unit(OTHER - np.sum(OTHER * D) * D)  # ortogonal a D


def _population(n, stage_shift, allo_dir, seed):
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        log_cs = rng.normal(0, 0.1)
        shape = MEAN + 0.6 * stage_shift * D + 1.5 * log_cs * allo_dir + rng.normal(scale=0.01, size=(K, 3))
        r = Rotation.random(random_state=seed * 1000 + i).as_matrix()
        out.append(np.exp(3 + stage_shift + log_cs) * shape @ r.T + rng.normal(size=3))
    return np.stack(out)


def test_aligned_allometry_supported():
    cfg = {"E15.5": _population(60, 0, D, 1), "E18.5": _population(60, 1, D, 2)}
    res = om.analyze(cfg, n_boot=200)
    for k in ("a15_d", "a18_d", "a15_a18"):
        assert res["angles"][k]["verdict"] == "apoyada", (k, res["angles"][k])
    assert res["rho_max"] < 0.3


def test_orthogonal_allometry_contrary():
    cfg = {"E15.5": _population(60, 0, OTHER, 3), "E18.5": _population(60, 1, OTHER, 4)}
    res = om.analyze(cfg, n_boot=200)
    assert res["angles"]["a15_d"]["verdict"] == "contraria"
    assert res["angles"]["a18_d"]["verdict"] == "contraria"
    assert res["angles"]["a15_a18"]["verdict"] == "apoyada"


def test_verdict_rule():
    assert om.verdict(10, 44) == "apoyada"
    assert om.verdict(61, 90) == "contraria"
    assert om.verdict(30, 70) == "no concluyente"


def test_prechecks_detect_point_count():
    a = _population(5, 0, D, 5)
    res = om.prechecks({"E15.5": a, "E18.5": a})
    assert res["check4_points"] is False and res["pass"] is False


def test_prechecks_pass_with_540(monkeypatch):
    monkeypatch.setattr(om, "N_POINTS", K)
    res = om.prechecks({"E15.5": _population(8, 0, D, 6), "E18.5": _population(8, 1, D, 7)})
    assert res["pass"], res
    assert res["correspondence_fraction"] == 1.0


def test_select_disjoint_balanced():
    rows = []
    for st in om.STAGES:
        for sex in ("F", "M"):
            for i in range(15):
                rows.append({"Biosample": f"X_{st}_{sex}_{i}", "Dataset": "IMPC", "Zygosity": "Wildtype",
                             "Genotype": "C57BL/6N", "Sex": sex, "Stage": st})
    rows.append({"Biosample": "Y", "Dataset": "IMPC", "Zygosity": "Wildtype", "Genotype": "C57BL/6N",
                 "Sex": "NA", "Stage": "E15.5"})
    meta = pd.DataFrame(rows)
    avail = [om.landmark_name(b) for b in meta["Biosample"] if not b.endswith("_14")]
    sel = om.select(meta, avail, n_pilot_per_stage=10)
    for st in om.STAGES:
        p, c = set(sel["pilot"][st]), set(sel["confirm"][st])
        assert len(p) == 10 and not p & c
        assert len(p) + len(c) == sel["n_eligible"][st] == 28
        assert sum("_F_" in x for x in p) == 5
    assert sel == om.select(meta, avail, n_pilot_per_stage=10)  # reproducible
    with pytest.raises(ValueError):
        om.select(meta, avail, n_pilot_per_stage=9)
