"""Pruebas del manifiesto de H11 (Qiu et al. 2021) con fichas fabricadas: no abre ningún dato real."""
import importlib.util
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "h11_manifest", Path(__file__).resolve().parents[1] / "scripts" / "h11_manifest_qiu2021.py")
hm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hm)


@pytest.mark.parametrize("name, eid", [
    ("20171122_En1_E12_Ext_E11a_reg", "20171122_E12_E11"),
    ("20161121_En1_E2a_reg-filt", "20161121_E2"),
    ("20170313_EN1_E10_E1a_reg_filt", "20170313_E10_E1"),
    ("20170706_En1_E13_E10a-Mut_reg", "20170706_E13_E10"),
    ("20180302_En1_E14.5_Ext_E12b_Mut", "20180302_E14p5_E12"),
    ("20170331_En1_E14p_E4b", "20170331_E14p_E4"),
    ("20171211_En1_E13_E2aMut_ext", "20171211_E13_E2"),
    ("20161128_En1_E14_E3R-filt", "20161128_E14_E3"),
])
def test_embryo_id(name, eid):
    assert hm.embryo_id(name) == eid


def test_a_and_b_scans_share_embryo():
    assert hm.embryo_id("20170206_En1_E12_E2a_Head") == hm.embryo_id("20170206_En1_E12_E2b")


def _row(path, shape=(4, 5, 6), spacing=(0.05, 0.05, 0.05), labels=None):
    r = {"path": path, "shape": list(shape), "spacing_mm": list(spacing)}
    if labels is not None:
        r["labels"] = labels
    return r


def test_build_pairs_excludes_and_deduplicates():
    rows = [_row("a\\20170101_En1_E12_E1a.nii"), _row("a\\20170101_En1_E12_E1a_BODY_labels.nii", labels=["0", "1"]),
            _row("a\\20170101_En1_E12_E1a_BV_labels.nii", labels=["0", "1"]),
            _row("a\\20170101_En1_E12_E2a.nii"),
            _row("a\\20170101_En1_E12_E2a_BODY_labels.nii", spacing=(1, 1, 1), labels=["0", "1"]),
            _row("a\\20170101_En1_E12_E2a_prebv.nii", spacing=(1, 1, 1), labels=["0", "1"]),
            _row("b\\20170101_En1_E12_E1a.nii")]
    man, exc = hm.build(rows)
    assert list(zip(man["structure"], man["embryo_id"])) == [("body", "20170101_E12_E1"), ("ventricle", "20170101_E12_E1")]
    reasons = sorted(exc["reason"].str.split(" ").str[0])
    assert reasons == ["duplicado", "sin", "vóxel"]
    relaxed, _ = hm.build(rows, relaxed_spacing=True)
    assert (relaxed["structure"] == "body").sum() == 2
