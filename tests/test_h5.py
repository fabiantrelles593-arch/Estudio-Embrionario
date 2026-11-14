import numpy as np
import pandas as pd

from geovida.h5 import evaluate_h5

LEVELS = (2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 20.0)
SEGS = ("global", "otsu", "smoothed_otsu", "smoothed_otsu_s2")


def _frame(area_err=0.01, topo_raw=0.1, topo_good=1.0, hc_raw=0.08, hc_comp=0.02, n=6):
    rows = []
    for shape in ("disk", "ellipse", "annulus"):
        for lvl in LEVELS:
            for prof in ("ideal", "us_compound", "us_raw"):
                for seg in SEGS:
                    for rep in range(n):
                        if prof == "us_raw":
                            ok = rep < topo_raw * n if seg == "otsu" else rep < topo_good * n
                            hc = hc_raw
                        elif prof == "us_compound":
                            ok = rep < topo_good * n if seg == "smoothed_otsu_s2" else rep < 0.1 * n
                            hc = hc_comp
                        else:
                            ok, hc = True, 0.0
                        rows.append({"shape": shape, "t_over_h": lvl, "profile": prof,
                                     "segmenter": seg, "rep": rep, "err_area": area_err,
                                     "err_hc": hc, "topology_ok": bool(ok)})
    return pd.DataFrame(rows)


def test_all_criteria_supported_on_favourable_data():
    res = evaluate_h5(_frame())
    for k in ("h5a", "h5b", "h5c", "h5d", "h5e"):
        assert res[k]["verdict"] == "apoyada", (k, res[k])


def test_h5a_fails_with_large_area_error():
    assert evaluate_h5(_frame(area_err=0.08))["h5a"]["verdict"] == "no apoyada"


def test_h5b_fails_if_raw_speckle_topology_is_actually_fine():
    assert evaluate_h5(_frame(topo_raw=1.0))["h5b"]["verdict"] == "no apoyada"


def test_h5c_fails_if_no_segmenter_reaches_95_percent():
    assert evaluate_h5(_frame(topo_good=0.5))["h5c"]["verdict"] == "no apoyada"


def test_h5d_and_h5e_follow_the_hc_errors():
    res = evaluate_h5(_frame(hc_comp=0.06))
    assert res["h5d"]["verdict"] == "no apoyada"
    res = evaluate_h5(_frame(hc_raw=0.01, hc_comp=0.02))
    assert res["h5e"]["verdict"] == "no apoyada"


def test_missing_data_is_not_evaluable_not_failed():
    df = _frame()
    df = df[df["profile"] != "us_raw"]
    res = evaluate_h5(df)
    assert res["h5b"]["verdict"] == "no evaluable" and res["h5e"]["verdict"] == "no evaluable"
