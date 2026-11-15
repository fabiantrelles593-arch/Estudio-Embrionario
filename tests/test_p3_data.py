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

# --- Recuperación de etiquetas interpoladas (desviación D1) -------------------------------------------
# Números de la sonda de 15-11-2026 (5 semillas): con 8 esferas de etiquetas no contiguas, giradas ±12° y
# remuestreadas con interpolación trilineal, la regla «nearest» coincide con el remuestreo por vecino más
# cercano en 95.4-96.2 % de los vóxeles, «exact» en 74.5-77.1 % y el redondeo simple en 57.4-61.4 % (y crea
# 32 etiquetas que no existen). Una placa de 2 vóxeles conserva con «nearest» el 98 % de su volumen (−1.4 a
# −1.9 %) y con «exact» pierde ~54 %.

from scipy import ndimage  # noqa: E402
from scipy.spatial.transform import Rotation  # noqa: E402


def _warp(lab, order, seed):
    rng = np.random.default_rng(seed)
    R = Rotation.from_euler("xyz", rng.uniform(-12, 12, 3), degrees=True).as_matrix()
    c = (np.array(lab.shape) - 1) / 2
    off = c - R @ c + rng.uniform(-0.5, 0.5, 3)
    return ndimage.affine_transform(lab.astype(np.float32), R, offset=off, order=order, mode="constant")


def _spheres(seed, n=48):
    rng = np.random.default_rng(seed)
    z, y, x = np.mgrid[:n, :n, :n]
    lab = np.zeros((n, n, n), np.int16)
    for L in range(1, 9):
        c = rng.uniform(10, n - 10, 3)
        lab[(z - c[0]) ** 2 + (y - c[1]) ** 2 + (x - c[2]) ** 2 < rng.uniform(3, 9) ** 2] = L * 5
    return lab


def test_recover_labels_keeps_exact_values_and_drops_unknown_integers():
    a = np.zeros((5, 5, 5), np.float32)
    a[1:4, 1:4, 1:4] = 7.0
    a[0, 0, 0] = 60.0  # entero que no es una etiqueta declarada: coincidencia de la interpolación
    lab, info = p3_data.recover_labels(a, allowed=[7], rule="exact")
    assert set(np.unique(lab)) == {0, 7} and info["n_labelled_exact"] == 27
    with pytest.raises(ValueError):
        p3_data.recover_labels(a, rule="redondeo")


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_nearest_rule_matches_nearest_neighbour_resampling(seed):
    lab = _spheres(seed)
    tri, nn = _warp(lab, 1, seed), np.rint(_warp(lab, 0, seed)).astype(int)
    allowed = sorted(set(np.unique(lab).tolist()) - {0})
    fg = (nn > 0) | (tri > 1e-3)
    near, info = p3_data.recover_labels(tri, allowed, "nearest")
    exact, _ = p3_data.recover_labels(tri, allowed, "exact")
    assert (near[fg] == nn[fg]).mean() > 0.94
    assert (exact[fg] == nn[fg]).mean() < 0.80
    assert set(np.unique(near).tolist()) <= set(allowed) | {0}
    assert len(set(np.unique(np.rint(tri)).astype(int).tolist()) - set(allowed) - {0}) > 10
    assert 0.3 < info["frac_mixed"] < 0.6


def test_thin_plate_keeps_its_volume_with_nearest_but_not_with_exact():
    lab = np.zeros((40, 40, 40), np.int16)
    lab[19:21, 8:32, 8:32] = 30
    lab[8:16, 8:16, 8:16] = 7
    for seed in range(3):
        tri, nn = _warp(lab, 1, seed), np.rint(_warp(lab, 0, seed)).astype(int)
        ref = (nn == 30).sum()
        near = (p3_data.recover_labels(tri, [7, 30], "nearest")[0] == 30).sum()
        exact = (p3_data.recover_labels(tri, [7, 30], "exact")[0] == 30).sum()
        assert abs(near / ref - 1) < 0.03
        assert exact / ref < 0.6


def test_mixed_voxels_without_exact_neighbour_look_two_voxels_away():
    a = np.zeros((9, 9, 9), np.float32)
    a[1:8, 1:8, 1:8] = 15.0
    a[3:6, 3:6, 3:6] = 14.6  # el centro no tiene ningún vecino exacto a 1 vóxel
    lab, info = p3_data.recover_labels(a, allowed=[15], rule="nearest")
    assert info["n_mixed_radius2"] == 1 and info["n_mixed_orphan"] == 0
    assert (lab[1:8, 1:8, 1:8] == 15).all()


def test_catalog_urls_batch_and_quote_file_names():
    urls = _script().catalog_urls([f"IMPC_E15.5_{k:04d}.mnc" for k in range(85)], chunk=40)
    assert len(urls) == 3 and urls[0].count("filename=") == 40 and urls[2].count("filename=") == 5
    assert all(u.startswith("https://www.facebase.org/ermrest/catalog/1/attribute/isa:file/dataset=3-JZA6/")
               and u.endswith("/filename,url,byte_count,md5") for u in urls)


def test_download_checks_md5_and_skips_files_already_correct(tmp_path, monkeypatch):
    import hashlib
    import io

    script = _script()
    good = b"segmentacion"
    md5 = hashlib.md5(good).hexdigest()
    (tmp_path / "A_Segs.mnc").write_bytes(good)  # ya descargado y correcto: no se vuelve a pedir
    rows = [{"filename": n, "url": f"/hatrac/{n}", "byte_count": len(good), "md5": md5}
            for n in ("A_Segs.mnc", "B_Segs.mnc")]
    calls = []

    def fake_urlopen(url, timeout=0):
        calls.append(url)
        return io.BytesIO(json.dumps(rows).encode() if "ermrest" in url else good)

    monkeypatch.setattr(script.urllib.request, "urlopen", fake_urlopen)
    log = script.download(["A_Segs.mnc", "B_Segs.mnc", "C_Segs.mnc"], tmp_path)
    assert [r["md5_ok"] for r in log] == [True, True, False]  # C no está en el catálogo
    assert sum("hatrac" in c for c in calls) == 1 and (tmp_path / "B_Segs.mnc").read_bytes() == good
    assert (tmp_path / "_descarga_md5.csv").exists()
