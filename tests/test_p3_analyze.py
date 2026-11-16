"""Regla de ampliación de P3 (§4 del preregistro, proyección fijada en la desviación D4)."""
import importlib.util
import math
from pathlib import Path

import pytest

pytest.importorskip("nibabel")
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("p3_analyze", ROOT / "scripts" / "p3_analyze.py")
pa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pa)


def test_projection_scales_with_sqrt_n():
    assert pa.projected_half_width(0.0, 0.2, 20) == pytest.approx(0.1 * math.sqrt(20 / 60))
    assert pa.projected_half_width(0.0, 0.2, 60) == pytest.approx(0.1)
    assert math.isnan(pa.projected_half_width(math.nan, 0.2, 20))


def test_expansion_decision():
    assert pa.expansion_decision(0.0, 0.30, 20) == 60    # 0,15 → 0,087 a 60
    assert pa.expansion_decision(0.0, 0.40, 20) == 120   # 0,20 → 0,115 a 60
    assert pa.expansion_decision(math.nan, 0.4, 20) == 120


def test_summarize_agreement_forms_and_d5_sensitivity():
    import pandas as pd
    rows = pd.DataFrame([
        {"specimen": s, "structure": 1, "form": f, "dice": d, "hd95": 0.1, "assd": 0.05, "vol_diff_rel": 0.0}
        for s, f, d in (("x", "a", 0.2), ("y", "a", 0.6), ("x", "b", 0.4), ("y", "b", 0.8))])
    out = pa.summarize_agreement(rows, non_rigid={"x"}).set_index("form")
    assert out.loc["a", "dice"] == pytest.approx(0.4) and out.loc["b", "dice"] == pytest.approx(0.6)
    assert out.loc["b_rigid", "dice"] == pytest.approx(0.8) and out.loc["b_rigid", "n_specimens"] == 1


def test_d1_verdicts_rule():
    main = {"verdict_a": "apoyada", "verdict_b": "no_apoyada"}
    exact = {"verdict_a": "no_concluyente", "verdict_b": "no_apoyada"}
    assert pa.d1_verdicts(main, exact, {"agree": True}) == main
    assert pa.d1_verdicts(main, exact, {"agree": False}) == {"verdict_a": "no_interpretable_D1",
                                                             "verdict_b": "no_apoyada"}


def test_confirm_runs_end_to_end_on_synthetic_maps(tmp_path, monkeypatch):
    """Flujo completo de ``confirm`` con mapas sintéticos (sin MINC): produce el resumen y todas las tablas."""
    import json

    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(2)
    ids = [f"s{i}" for i in range(6)]
    memos, data = tmp_path / "memos", tmp_path / "data"
    memos.mkdir()
    data.mkdir()
    for s in ids:
        np.savez(memos / f"{s}_memos.npz", labels=np.zeros(1), box=np.zeros((3, 2)))
        (data / f"{s}_Segs.mnc").write_bytes(b"")
    (memos / "memos_vs_atlas.json").write_text(json.dumps({s: {"translation_vox": [1, 0, 0]} for s in ids}))
    (memos / "memos_rigidity.json").write_text(json.dumps({s: {"spread_vox": 9 if s == "s0" else 1} for s in ids}))
    sel = tmp_path / "sel.json"
    sel.write_text(json.dumps({"confirm": ids + ["falta"]}))
    pd.DataFrame({"unit": ["1", "2"], "group": ["delgada", "compacta"], "log_volume": [1.0, 2.0],
                  "d_over_hgeo": [1.0, 3.0]}).to_csv(tmp_path / "g.csv", index=False)

    def fake_maps(sid, data_dir, memos_dir, rule="nearest", pad=0, memos_as_b=None):
        a = np.zeros((40, 40, 40), np.int16)
        r = 9 + rng.normal(0, 1)
        g = np.indices(a.shape)
        a[((g - 20) ** 2).sum(0) <= r * r] = 2
        a[5:8, 5:30, 5:30] = 1
        b = np.roll(a, (1, 0, 0), (0, 1, 2)).astype(np.uint8)  # A trasladado (1, 0, 0) coincide con B
        if rule == "exact":
            a[5] = np.where(a[5] == 1, 0, a[5])
        return {"A": a, "B": b}, (0.027, 0.027, 0.027)

    monkeypatch.setattr(pa, "_specimen_maps", fake_maps)
    monkeypatch.setattr(pa.p3_data, "P3_STRUCTURES", (1, 2))
    x4 = tmp_path / "x4"
    x4.mkdir()
    for s in ids[:4]:
        np.savez(x4 / f"{s}_memos.npz", labels=np.zeros(1), box=np.zeros((3, 2)))
    meta = tmp_path / "meta.csv"
    pd.DataFrame({"Biosample": ids, "Sex": ["F", "M"] * 3}).to_csv(meta, index=False)
    out = tmp_path / "res" / "confirm.json"
    assert pa.main(["confirm", "--data", str(data), "--memos", str(memos), "--groups", str(tmp_path / "g.csv"),
                    "--ids", str(sel), "--out", str(out), "--n-boot", "20", "--metadata", str(meta),
                    "--memos-x4", str(x4)]) == 0
    s = json.loads(out.read_text(encoding="utf-8"))
    assert s["specimens"] == ids and s["missing"] == ["falta"] and s["non_rigid_D5"] == ["s0"]
    assert s["exploratory_sex"] and s["exploratory_x4"]["n_specimens"] == 4
    assert set(pd.read_csv(out.with_suffix(".sex.csv"))["variant"]) == {"sex_F", "sex_M"}
    assert s["primary"]["verdict_a"] == "no_evaluable"  # menos de 8 unidades por grupo
    for suffix in (".conditions.csv", ".agreement.csv", ".agreement_summary.csv", ".units.csv", ".tau.csv",
                   ".mixed.csv", ".exploratory.csv", ".conditions_exact.csv"):
        assert out.with_suffix(suffix).exists()
    agr = pd.read_csv(out.with_suffix(".agreement.csv"))
    b = agr[(agr["form"] == "b") & (agr["structure"] == 2)]
    assert b["dice"].min() == pytest.approx(1.0)  # la traslación de D3 alinea A con B
