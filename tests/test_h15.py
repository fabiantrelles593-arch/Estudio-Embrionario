import numpy as np
import pandas as pd

from geovida import biometry as bio
from geovida import h13, h15


def test_chain_cases_are_deterministic_and_paired():
    a, b = h15.chain_cases(5, 4, 123), h15.chain_cases(5, 4, 123)
    assert a == b
    assert len(a) == 2 * (5 + 4)
    assert all("chain" in c for c in a)
    base = h13.confirmation_cases(5, 4, 123)
    assert [{k: v for k, v in c.items() if k != "chain"} for c in a] == base


def test_chain_parameters_differ_between_cases():
    cs = h15.chain_cases(6, 0, 77)
    assert len({c["chain"]["noise_seed"] for c in cs}) == len(cs)


def test_seeds_are_distinct_from_earlier_sets():
    assert len({h15.H15_CONF_SEED, h15.H15_PILOT_SEED, 20261211, 20261212, 20261213, 20261214, 20261215}) == 7


def _fake(variant, kind, n, wrong_every, seg="smoothed_otsu"):
    rows = []
    for i in range(n):
        green = True
        rows.append({"idx": i, "kind": kind, "segmenter": seg, "region": "in", "truth_mm": 30.0,
                     "measured_mm": 30.0 + (0.5 if variant == "chain" else 0.0), "in_domain": True,
                     "light": "verde" if green else "amarillo", "p": 0.95,
                     "correct": not (wrong_every and i % wrong_every == 0), "sd_mm": 0.3,
                     "variant": variant, "chain_compression_a": 3.0 + i})
    return pd.DataFrame(rows)


def test_evaluate_h15_reports_all_hypotheses_and_paired_shift():
    df = pd.concat([_fake("clean", "body", 120, 0), _fake("chain", "body", 120, 0),
                    _fake("clean", "slot", 120, 0), _fake("chain", "slot", 120, 0)], ignore_index=True)
    v = h15.evaluate_h15(df, n_boot=50, seed=1)
    assert set(v) == {"h15a", "h15b", "h15c", "h15d", "h15e"}
    assert v["h15a"]["verdict"] == "apoyada" and v["h15b"]["verdict"] == "apoyada"
    sh = v["h15d"]["shift"]["body|smoothed_otsu"]
    assert abs(sh["median_pct"] - 100 * 0.5 / 30.0) < 1e-9
    assert v["h15d"]["retention"]["body"]["ratio"] == 1.0


def test_false_green_rule_detects_a_failing_chain_variant():
    df = pd.concat([_fake("clean", "body", 120, 0), _fake("chain", "body", 120, 3),
                    _fake("clean", "slot", 120, 0), _fake("chain", "slot", 120, 0)], ignore_index=True)
    v = h15.evaluate_h15(df, n_boot=100, seed=1)
    assert v["h15a"]["verdict"] == "no apoyada"           # 1/3 de verdes equivocados
    assert v["h15d"]["clean_reference"]["body"]["verdict"] == "apoyada"


def test_compression_terciles_table_has_three_levels():
    df = _fake("chain", "body", 90, 5)
    t = h15.compression_terciles(df)
    assert set(t["compression"]) == {"baja", "media", "alta"}
