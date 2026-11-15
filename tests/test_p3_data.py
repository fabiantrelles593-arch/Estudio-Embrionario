"""Pruebas de las comprobaciones previas de P3 con segmentaciones MINC sintéticas (sin datos de MusMorph)."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("nibabel")
from nibabel.externals.netcdf import netcdf_file  # noqa: E402

from geovida import p3_data  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DIMS = ("zspace", "yspace", "xspace")


def _write_labels(path, lab, step=0.027):
    """Segmentación MINC1 entera con escala identidad (valid_range = rango real)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    f = netcdf_file(str(path), "w")
    try:
        for d, n in zip(DIMS, lab.shape):
            f.createDimension(d, n)
        for d, cos in zip(DIMS, ((0, 0, 1), (0, 1, 0), (1, 0, 0))):
            v = f.createVariable(d, "i", ())
            v.data[()] = 0
            v.step = np.float64(step)
            v.start = np.float64(0.0)
            v.direction_cosines = np.asarray(cos, dtype=np.float64)
            v.spacing = b"regular__"
            v.units = b"mm"
        img = f.createVariable("image", "h", DIMS)
        img[:] = lab.astype(np.int16)
        img.signtype = b"signed__"
        top = float(max(int(lab.max()), 1))
        img.valid_range = np.asarray([0.0, top])
        for name, val in (("image-min", 0.0), ("image-max", top)):
            s = f.createVariable(name, "d", ())
            s.data[()] = val
    finally:
        f.close()


def _specimen(rng, same=False):
    lab = np.zeros((20, 24, 24), np.int16)
    a = 6 if same else int(rng.integers(4, 9))
    b = 5 if same else int(rng.integers(3, 7))
    lab[2:2 + a, 2:12, 2:12] = 1
    lab[12:12 + b, 4:20, 4:20] = 2
    return lab


def _download(tmp_path, ids, same=False, skip_seg=()):
    rng = np.random.default_rng(0)
    root = tmp_path / "bdbag" / "data"
    for k, i in enumerate(ids):
        sub = root / f"lote{k % 2}"
        (sub / f"{i}.mnc").parent.mkdir(parents=True, exist_ok=True)
        (sub / f"{i}.mnc").write_bytes(b"imagen no leida en las comprobaciones")
        if i not in skip_seg:
            _write_labels(sub / f"{i}_Segs.mnc", _specimen(rng, same))
    return tmp_path / "bdbag"


IDS = [f"IMPC_E15.5_{k:04d}" for k in range(6)]


def test_required_files_lists_image_and_segmentation():
    assert p3_data.required_files(["A", "B"]) == ["A.mnc", "A_Segs.mnc", "B.mnc", "B_Segs.mnc"]


def test_index_folder_finds_nested_files_and_rejects_duplicates(tmp_path):
    root = _download(tmp_path, IDS[:2])
    idx = p3_data.index_folder(root)
    assert set(idx) == {"IMPC_E15.5_0000.mnc", "IMPC_E15.5_0000_Segs.mnc",
                        "IMPC_E15.5_0001.mnc", "IMPC_E15.5_0001_Segs.mnc"}
    (root / "otra").mkdir()
    (root / "otra" / "IMPC_E15.5_0000.mnc").write_bytes(b"x")
    with pytest.raises(ValueError):
        p3_data.index_folder(root)


def test_precheck_passes_with_varying_specimen_space_segmentations(tmp_path):
    res = p3_data.precheck(_download(tmp_path, IDS), IDS)
    assert res["n_complete"] == 6 and res["check_3_1_passed"]
    assert res["check_3_2_passed"] and res["labels_present"] == [1, 2]
    assert res["spacings_mm"] == [[0.027, 0.027, 0.027]]
    vol = res["volumes"]
    assert len(vol) == 12 and (vol["volume"] > 0).all()


def test_precheck_stops_when_segmentations_are_identical_or_missing(tmp_path):
    same = p3_data.precheck(_download(tmp_path / "a", IDS, same=True), IDS)
    assert same["check_3_1_passed"] and not same["check_3_2_passed"]
    missing = p3_data.precheck(_download(tmp_path / "b", IDS, skip_seg=IDS[:2]), IDS)
    assert missing["existence_fraction"] == pytest.approx(4 / 6)
    assert not missing["check_3_1_passed"] and missing["missing"] == IDS[:2]


def _script():
    spec = importlib.util.spec_from_file_location("p3_pilot", ROOT / "scripts" / "p3_pilot.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_pilot_script_select_then_check(tmp_path, capsys):
    rows = [{"Biosample": f"IMPC_E15.5_{k:04d}", "Stage": "E15.5", "Dataset": "IMPC", "Zygosity": "Wildtype",
             "Sex": "F" if k % 2 else "M"} for k in range(200)]
    meta = tmp_path / "meta.csv"
    pd.DataFrame(rows).to_csv(meta, index=False)
    sel_path = tmp_path / "out" / "seleccion.json"
    script = _script()
    assert script.main(["select", "--metadata", str(meta), "--out", str(sel_path)]) == 0
    sel = json.loads(sel_path.read_text(encoding="utf-8"))
    assert len(sel["pilot"]) == 20 and len(sel["confirm"]) == 60 and len(sel["pilot_files"]) == 40
    root = _download(tmp_path, sel["pilot"])
    out = tmp_path / "out" / "precheck.json"
    assert script.main(["check", "--ids", str(sel_path), "--data", str(root), "--out", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["check_3_2_passed"]
    assert out.with_suffix(".volumes.csv").exists()
    assert "pasa" in capsys.readouterr().out
