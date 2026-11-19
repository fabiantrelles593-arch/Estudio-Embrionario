"""Puertas de MT-A (``scripts/atlas_effect_gates.py``). Configuraciones sintéticas; ningún dato real.

Qué falla si la puerta G0-d deja de aplicar el intervalo del preregistro (§4: longitud de d en [0,150, 0,164]).
"""
import importlib.util
from pathlib import Path

import numpy as np

_spec = importlib.util.spec_from_file_location(
    "atlas_effect_gates", Path(__file__).resolve().parents[1] / "scripts" / "atlas_effect_gates.py")
gates = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gates)


def _stage(base, shift, n, rng):
    return np.stack([base + shift + rng.normal(0, 0.002, base.shape) for _ in range(n)])


def test_g0d_uses_the_preregistered_range():
    assert gates.G0D_RANGE == (0.150, 0.164) and gates.PUBLISHED_D == 0.157


def test_g0d_passes_and_fails_by_the_length_of_d():
    rng = np.random.default_rng(0)
    base = rng.normal(0, 1, (40, 3))
    base -= base.mean(axis=0)
    base /= np.linalg.norm(base)                                   # preforma: d se mide en estas unidades
    direction = rng.normal(0, 1, base.shape)
    direction -= direction.mean(axis=0)
    direction -= (direction.ravel() @ base.ravel()) * base         # perpendicular a la forma media
    direction /= np.linalg.norm(direction)
    for length, expected in [(0.157, True), (0.10, False)]:
        cfg = {"E15.5": _stage(base, -length / 2 * direction, 30, rng),
               "E18.5": _stage(base, length / 2 * direction, 30, rng)}
        r = gates.g0d(cfg)
        assert r["passed"] is expected, r["d_length"]


def test_g0c_passes_for_corresponding_points_and_fails_when_shuffled():
    rng = np.random.default_rng(1)
    a = rng.normal(0, 1, (gates.N_POINTS, 3))
    b = 1.3 * a @ np.linalg.qr(rng.normal(size=(3, 3)))[0] + 5 + rng.normal(0, 0.05, a.shape)
    assert gates.g0c(a, b, n_perm=20)["passed"] is True
    assert gates.g0c(a, b[rng.permutation(len(b))], n_perm=20)["passed"] is False
    assert gates.g0c(a[:100], b[:100], n_perm=20)["passed"] is False      # 540 puntos exigidos


def test_catalog_must_match_the_preregistration():
    rows = [{"filename": n, "byte_count": s, "md5": m} for n, (s, m) in gates.ATLAS_FILES.items()]
    assert gates.check_catalog(rows) == []
    bad = [dict(r) for r in rows]
    bad[0]["md5"] = "0" * 32
    assert len(gates.check_catalog(bad)) == 1 and len(gates.check_catalog(rows[1:])) == 1


class _Resp:
    def __init__(self, data):
        import io
        self._b = io.BytesIO(data)

    def read(self, n=-1):
        return self._b.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_fetch_atlas_downloads_verifies_and_refuses_a_changed_catalog(tmp_path):
    import hashlib
    import json
    files = {"a.tag": b"MNI Tag Point File\n", "b.mnc": b"\x00" * 100}
    expected = {n: (len(d), hashlib.md5(d).hexdigest()) for n, d in files.items()}
    rows = [{"filename": n, "url": f"/hatrac/{n}", "byte_count": s, "md5": m} for n, (s, m) in expected.items()]
    calls = []

    def opener(url, timeout=None):
        calls.append(url)
        if "ermrest" in url:
            return _Resp(json.dumps(rows).encode())
        return _Resp(files[url.rsplit("/", 1)[1]])

    log = gates.fetch_atlas(tmp_path, expected, opener=opener)
    assert all(r["md5_ok"] for r in log) and (tmp_path / "b.mnc").read_bytes() == files["b.mnc"]
    n = len(calls)
    gates.fetch_atlas(tmp_path, expected, opener=opener)                   # ya están: solo consulta el catálogo
    assert len(calls) == n + 1
    changed = {**expected, "a.tag": (expected["a.tag"][0], "f" * 32)}
    import pytest
    with pytest.raises(RuntimeError):
        gates.fetch_atlas(tmp_path / "otra", changed, opener=opener)
    assert not (tmp_path / "otra").exists()


def test_fetch_reuses_verified_local_copies_and_reports_missing_files(tmp_path):
    import hashlib
    import json
    files = {"IMPC_E15.5_0001.mnc": b"\x01" * 50, "IMPC_E18.5_0002.mnc": b"\x02" * 70}
    rows = [{"filename": n, "url": f"/hatrac/{n}", "byte_count": len(d), "md5": hashlib.md5(d).hexdigest()}
            for n, d in files.items()]
    downloaded = []

    def opener(url, timeout=None):
        if "ermrest" in url:
            return _Resp(json.dumps(rows).encode())
        downloaded.append(url.rsplit("/", 1)[1])
        return _Resp(files[url.rsplit("/", 1)[1]])

    good, stale = tmp_path / "p3", tmp_path / "viejo"
    good.mkdir()
    stale.mkdir()
    (good / "IMPC_E15.5_0001.mnc").write_bytes(files["IMPC_E15.5_0001.mnc"])
    (stale / "IMPC_E18.5_0002.mnc").write_bytes(b"corrupto")              # MD5 distinto: no se reutiliza
    names = list(files) + ["IMPC_E18.5_9999.mnc"]
    log = {r["filename"]: r for r in gates.fetch(names, "3-JZA6", tmp_path / "out", reuse=[stale, good],
                                                 opener=opener)}
    assert log["IMPC_E15.5_0001.mnc"]["source"] == "copia local" and log["IMPC_E15.5_0001.mnc"]["md5_ok"]
    assert log["IMPC_E18.5_0002.mnc"]["source"] == "FaceBase" and log["IMPC_E18.5_0002.mnc"]["md5_ok"]
    assert downloaded == ["IMPC_E18.5_0002.mnc"]
    assert log["IMPC_E18.5_9999.mnc"]["md5_ok"] is False


def test_specimen_images_are_the_onto_map_pilot():
    sel = {"pilot": {"E15.5": ["IMPC_E15.5_0001"], "E18.5": ["IMPC_E18.5_0002", "IMPC_E18.5_0003"]},
           "confirm": {"E15.5": ["IMPC_E15.5_0999"], "E18.5": []}}
    assert gates.specimen_images(sel) == ["IMPC_E15.5_0001.mnc", "IMPC_E18.5_0002.mnc", "IMPC_E18.5_0003.mnc"]
