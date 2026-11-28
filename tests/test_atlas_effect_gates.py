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


def _write_tag(path, pts):
    body = "\n".join(f" {x:.6f} {y:.6f} {z:.6f} \"\"" for x, y, z in pts)
    path.write_text(f"MNI Tag Point File\nVolumes = 1;\nPoints =\n{body};\n", encoding="utf-8")


def test_register_all_transfers_atlas_points_and_resumes(tmp_path):
    pytest = __import__("pytest")
    pytest.importorskip("SimpleITK")
    from scipy.ndimage import gaussian_filter, shift
    n = 40
    z, y, x = np.mgrid[:n, :n, :n].astype(float)
    c = (n - 1) / 2
    body = ((z - c) / 13) ** 2 + ((y - c) / 9) ** 2 + ((x - c) / 7) ** 2 <= 1
    knob = (z - c - 8) ** 2 + (y - c + 5) ** 2 + (x - c - 2) ** 2 <= 12
    atlas = gaussian_filter((body + 0.6 * knob).astype(np.float32), 1.0)
    move = np.array([2.0, -1.5, 1.0])                                # el espécimen = atlas desplazado (índice = mundo)
    spec = shift(atlas, move, order=1).astype(np.float32)
    cache, atlas_dir = tmp_path / "cache", tmp_path / "atlas"
    cache.mkdir()
    atlas_dir.mkdir()
    for st, f in gates.ATLAS_IMAGES.items():
        np.savez(cache / (Path(f).stem + "_x4.npz"), downsampled=atlas, affine_ds=np.eye(4), affine=np.eye(4))
    np.savez(cache / "IMPC_E15.5_0001_x4.npz", downsampled=spec, affine_ds=np.eye(4), affine=np.eye(4))
    pts = c + np.random.default_rng(0).uniform(-5, 5, (12, 3))
    for f in gates.ATLAS_TAG.values():
        _write_tag(atlas_dir / f, pts)
    out = tmp_path / "regs"
    rows = gates.register_all(["IMPC_E15.5_0001"], tmp_path, atlas_dir, cache, out, affine_only=True, log=lambda m: None)
    assert [r["own"] for r in rows] == [True, False] and all(r["ok"] for r in rows)
    err = np.linalg.norm(np.array(rows[0]["points"]) - (pts + move), axis=1)
    assert np.median(err) < 0.3, err                                   # el punto del atlas cae donde está en el espécimen
    again = gates.register_all(["IMPC_E15.5_0001"], tmp_path, atlas_dir, cache, out, affine_only=True,
                               log=lambda m: (_ for _ in ()).throw(AssertionError("no debía registrar")))
    assert [r["points"] for r in again] == [r["points"] for r in rows]


def _analysis_case(n_valid15=20, a=0.7, k=12):
    rng = np.random.default_rng(3)
    base = rng.normal(0, 1, (k, 3))
    dvec = rng.normal(0, 1, (k, 3)) * 0.08
    sel = {"pilot": {st: [f"IMPC_{st}_{i:04d}" for i in range(20)] for st in ("E15.5", "E18.5")}}
    conf = {"E15.5": np.stack([base - dvec / 2 + rng.normal(0, 0.01, base.shape) for _ in range(30)]),
            "E18.5": np.stack([base + dvec / 2 + rng.normal(0, 0.01, base.shape) for _ in range(30)])}
    pub, rows = {}, []
    for st in ("E15.5", "E18.5"):
        for i, b in enumerate(sel["pilot"][st]):
            shape = base + (dvec / 2 if st == "E18.5" else -dvec / 2) + rng.normal(0, 0.03, base.shape)
            pub[b] = shape
            l15 = shape + rng.normal(0, 0.005, base.shape) - (a * dvec / 2 if st == "E18.5" else 0)
            l18 = l15 + a * dvec
            ok = st == "E18.5" or i < n_valid15
            rows += [{"specimen": b, "atlas": "E15.5", "ok": ok, "points": l15.tolist()},
                     {"specimen": b, "atlas": "E18.5", "ok": True, "points": l18.tolist()}]
    return rows, sel, pub, conf


def test_analyze_gives_a_verdict_only_when_every_gate_passes():
    g0 = {g: {"passed": True} for g in ("G0-a", "G0-b", "G0-c", "G0-d")}
    rows, sel, pub, conf = _analysis_case()
    r = gates.analyze(rows, sel, pub, conf, g0, n_boot=200)
    assert r["gates"]["G2"]["passed"] and r["gates"]["G1"]["passed"] and r["failed_gates"] == []
    assert r["verdict"] == r["mta"]["mta1"]["verdict"] == "apoyada" and 0.5 < r["mta"]["mta1"]["f"] < 0.9
    rows, sel, pub, conf = _analysis_case(n_valid15=15)               # 15 de 20 válidos en E15.5: falla G2
    r = gates.analyze(rows, sel, pub, conf, g0, n_boot=200)
    assert r["gates"]["G2"]["valid"] == {"E15.5": 15, "E18.5": 20} and r["verdict"] == "no evaluable"
    rows, sel, pub, conf = _analysis_case()
    r = gates.analyze(rows, sel, pub, conf, {**g0, "G0-a": {"passed": False}}, n_boot=200)
    assert r["failed_gates"] == ["G0-a"] and r["verdict"] == "no evaluable"


def test_v1_1_constants_are_the_preregistered_ones():
    assert gates.MAX_DIST_MM == 0.23 and gates.SEARCH_RADIUS_MM == 0.5 and gates.G0A2_REQUIRED == 35


def test_g0a2_counts_only_unseen_specimens_and_lists_exclusions():
    seen = ["s0", "s1", "s2"]
    rows = [{"name": f"s{i}", "passed": i not in (0, 5, 6)} for i in range(40)]   # falla un visto y dos no vistos
    r = gates.g0a2(rows, seen)
    assert r["n_unseen"] == 37 and r["n_unseen_passed"] == 35 and r["passed"]
    assert r["excluded"] == ["s0", "s5", "s6"]
    rows[7]["passed"] = False
    assert not gates.g0a2(rows, seen)["passed"]                          # 34 de 37


def test_analyze_drops_excluded_specimens():
    g0 = {g: {"passed": True} for g in ("G0-a′", "G0-b′", "G0-c", "G0-d")}
    rows, sel, pub, conf = _analysis_case()
    r = gates.analyze(rows, sel, pub, conf, g0, n_boot=200, exclude=sel["pilot"]["E15.5"][:3])
    assert r["gates"]["G2"]["valid"] == {"E15.5": 17, "E18.5": 20} and r["mta"]["n"] == 37
    r = gates.analyze(rows, sel, pub, conf, g0, n_boot=200, exclude=sel["pilot"]["E15.5"][:5])
    assert r["verdict"] == "no evaluable" and "G2" in r["failed_gates"]


def test_specimen_images_are_the_onto_map_pilot():
    sel = {"pilot": {"E15.5": ["IMPC_E15.5_0001"], "E18.5": ["IMPC_E18.5_0002", "IMPC_E18.5_0003"]},
           "confirm": {"E15.5": ["IMPC_E15.5_0999"], "E18.5": []}}
    assert gates.specimen_images(sel) == ["IMPC_E15.5_0001.mnc", "IMPC_E18.5_0002.mnc", "IMPC_E18.5_0003.mnc"]
