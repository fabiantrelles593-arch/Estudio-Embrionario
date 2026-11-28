"""MT-D (PREREGISTRO_ANOTACION_MANUAL.md): lectura de Slicer, coordenadas, q, puertas y plan de sesiones.

Qué haría fallar cada prueba: si la convención LPS no se invirtiera, todos los puntos manuales caerían reflejados y
G0-r fallaría por un error nuestro; si el recorte o el NIfTI movieran el mundo, el anotador marcaría en otro sitio; si
q no valiera 1 con los puntos de MusMorph ni ≈ 0 sin diferencia entre atlas, MT-D1 no mediría lo que dice; si las
puertas no fallaran con anotaciones imprecisas o desplazadas, no protegerían nada; si el plan cambiara con la
semilla fija o repitiera un atlas en la misma sesión, el diseño no sería el preregistrado. Sin datos reales.
"""
import json

import numpy as np
import pytest

from geovida import atlas_anchor as aa
from geovida import manual_landmarks as ml

K = 22


def _rot(rng):
    q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    return q if np.linalg.det(q) > 0 else -q


def _world(rng, n15=30, n18=30, only=ml.TARGETS, shift=0.3):
    """Atlas de 22 landmarks que difieren solo en ``only`` y especímenes alrededor de cada uno."""
    a15 = rng.normal(size=(K, 3)) * 2.0
    delta = np.zeros((K, 3))
    delta[[i - 1 for i in only]] = shift * rng.normal(size=(len(only), 3))
    a18 = a15 + delta
    def spec(base, n):
        return np.stack([(base + 0.02 * rng.normal(size=base.shape)) @ _rot(rng) + rng.normal(size=3)
                         for _ in range(n)])
    p15, p18 = spec(a15, n15), spec(a18, n18)
    s = aa.shape_space(p15, p18)
    t15, t18 = (aa.project_to_tangent(x, s["mean"]) for x in (a15, a18))
    dec = aa.decompose(s["t15"], s["t18"], t15, t18)
    return {"E15.5": a15, "E18.5": a18}, s["mean"], dec["a"], dec["d"]


def _reps(rng, at, rows=ml.TARGETS, sd=0.005, n=5, offset=None):
    out = {}
    for st in aa.STAGES:
        base = at[st][[i - 1 for i in rows]]
        if offset is not None and st in offset:
            base = base + offset[st]
        out[st] = base[None] + sd * rng.normal(size=(n, len(rows), 3))
    return out


def test_markups_lps_and_ras_give_same_world(tmp_path):
    pts = {17: np.array([1.0, -2.0, 3.0]), 18: np.array([-4.5, 0.25, 7.0])}
    for cs in ("LPS", "RAS"):
        f = tmp_path / f"{cs}.mrk.json"
        ml.write_markups(f, pts, cs)
        got = ml.read_markups(f)
        for k, v in pts.items():
            np.testing.assert_allclose(got[k], v)
    doc = json.loads((tmp_path / "LPS.mrk.json").read_text())
    np.testing.assert_allclose(doc["markups"][0]["controlPoints"][0]["position"], [-1.0, 2.0, 3.0])


def test_markups_skip_undefined_and_reject_duplicates(tmp_path):
    doc = {"markups": [{"coordinateSystem": "RAS", "controlPoints": [
        {"label": "L17", "position": [0, 0, 0], "positionStatus": "defined"},
        {"label": "L18", "position": [0, 0, 0], "positionStatus": "missing"}]}]}
    f = tmp_path / "a.mrk.json"
    f.write_text(json.dumps(doc))
    assert set(ml.read_markups(f)) == {17}
    doc["markups"][0]["controlPoints"][1].update({"label": "17", "positionStatus": "defined"})
    f.write_text(json.dumps(doc))
    with pytest.raises(ValueError, match="repetida"):
        ml.read_markups(f)
    doc["markups"][0]["coordinateSystem"] = "XYZ"
    f.write_text(json.dumps(doc))
    with pytest.raises(ValueError, match="desconocido"):
        ml.read_markups(f)


def test_template_has_labels_and_reads_as_empty(tmp_path):
    f = tmp_path / "plantilla.mrk.json"
    ml.write_template(f, [17, 18, 10])
    doc = json.loads(f.read_text())
    cps = doc["markups"][0]["controlPoints"]
    assert [c["label"] for c in cps] == ["L17", "L18", "L10"]
    assert all(c["positionStatus"] == "undefined" for c in cps)
    assert ml.read_markups(f) == {}
    cps[0].update({"position": [1.0, 2.0, 3.0], "positionStatus": "defined"})
    f.write_text(json.dumps(doc))
    got = ml.read_markups(f)
    assert set(got) == {17} and np.allclose(got[17], [-1.0, -2.0, 3.0])


def test_crop_and_nifti_keep_world(tmp_path):
    nib = pytest.importorskip("nibabel")
    rng = np.random.default_rng(1)
    aff = np.eye(4)
    aff[:3, :3] = _rot(rng) * 0.05
    aff[:3, 3] = [3.0, -1.0, 2.0]
    arr = rng.normal(size=(40, 50, 60)).astype(np.float32)
    idx = np.array([[12, 30, 41]])
    world = idx @ aff[:3, :3].T + aff[:3, 3]
    sl = ml.box_slices(arr.shape, aff, world[0] - 0.4, world[0] + 0.4)
    sub, a2 = arr[sl], ml.shifted_affine(aff, sl)
    ml.save_nifti(sub, a2, tmp_path / "v.nii.gz")
    img = nib.load(str(tmp_path / "v.nii.gz"))
    j = np.rint(ml.world_to_index(world, img.affine)).astype(int)[0]
    assert np.asarray(img.dataobj)[tuple(j)] == pytest.approx(arr[tuple(idx[0])])
    np.testing.assert_allclose(img.affine, a2, atol=1e-5)


def test_phantom_truth_and_gate():
    rng = np.random.default_rng(2)
    a3 = _rot(rng) * 0.027
    vol, aff, truth = ml.phantom(a3, shape=(40, 40, 40))
    for k, c in truth.items():
        j = np.rint(ml.world_to_index(c[None], aff)).astype(int)[0]
        assert vol[tuple(j)] == 1000.0
    ok = ml.gate_phantom(truth, {k: v + 0.01 for k, v in truth.items()}, 0.027)
    assert ok["passed"]
    bad = ml.gate_phantom(truth, {k: v * np.array([-1, -1, 1]) for k, v in truth.items()}, 0.027)
    assert not bad["passed"]
    assert not ml.gate_phantom(truth, {1: truth[1]}, 0.027)["passed"]


def test_gate_space_detects_outside_and_dark():
    aff = np.eye(4)
    vol = np.zeros((10, 10, 10))
    vol[2:8, 2:8, 2:8] = 5.0
    def box_at(i, r):
        sl = [slice(max(0, int(i[k]) - r), min(10, int(i[k]) + r + 1)) for k in range(3)]
        return vol[tuple(sl)], np.asarray(i) - np.array([s.start for s in sl])
    pts = np.array([[4.0, 4, 4], [1.0, 4, 4], [1.0, 1, 4], [0.0, 0, 0], [20.0, 1, 1]])
    g = ml.gate_space(pts, vol.shape, aff, box_at, 1.0)
    assert g["n_inside"] == 4 and g["n_above_otsu"] == 1 and g["n_within_tolerance"] == 2
    assert g["below_otsu_landmarks"] == [2, 3, 4] and g["failed_landmarks"] == [3, 4, 5]
    assert g["distance_vox"][1] == pytest.approx(1.0) and g["distance_vox"][4] is None
    assert not g["passed"]
    assert ml.gate_space(pts[:2], vol.shape, aff, box_at, 1.0)["passed"]
    assert not ml.gate_space(pts[:2], vol.shape, aff, box_at, 1.0, tol_vox=0.0)["passed"]


def test_q_is_one_with_musmorph_points_and_near_zero_without_difference():
    rng = np.random.default_rng(3)
    at, mean, a, d = _world(rng)
    rows = [i - 1 for i in ml.TARGETS]
    same = {st: at[st][rows] for st in aa.STAGES}
    a_man = ml.manual_atlas_difference(at, same, mean)
    assert ml.q_value(a_man, a) == pytest.approx(1.0, abs=1e-9)
    flat = {st: at["E15.5"][rows] for st in aa.STAGES}
    q0 = ml.q_value(ml.manual_atlas_difference(at, flat, mean), a)
    assert abs(q0) < 0.1


def test_bootstrap_verdicts():
    rng = np.random.default_rng(4)
    at, mean, a, d = _world(rng)
    good = ml.bootstrap_q(at, _reps(rng, at), mean, a, d, n_boot=200)
    assert good["verdict_mtd1"] == "reproducida"
    rows = [i - 1 for i in ml.TARGETS]
    off = {"E18.5": at["E15.5"][rows] - at["E18.5"][rows]}
    bad = ml.bootstrap_q(at, _reps(rng, at, offset=off), mean, a, d, n_boot=200)
    assert bad["verdict_mtd1"] == "no reproducida"
    missing = _reps(rng, at)
    missing["E15.5"][:3, 0] = np.nan
    assert ml.bootstrap_q(at, missing, mean, a, d, n_boot=10)["verdict_mtd1"] == "no evaluable"
    assert ml.verdict_mtd1(0.6, 1.1) == "no concluyente"


def test_gates_precision_and_references():
    rng = np.random.default_rng(5)
    at, mean, a, d = _world(rng)
    assert ml.gate_precision(at, _reps(rng, at, sd=0.001), mean, a)["passed"]
    assert not ml.gate_precision(at, _reps(rng, at, sd=0.5), mean, a)["passed"]
    refs = (10, 15, 9, 8)
    assert ml.gate_references(at, _reps(rng, at, rows=refs, sd=0.05), refs)["passed"]
    shifted = _reps(rng, at, rows=refs, sd=0.05, offset={"E18.5": np.array([1.0, 0, 0])})
    g = ml.gate_references(at, shifted, refs)
    assert g["items"]["E15.5"]["passed"] and not g["passed"]


def test_references_rule_and_session_plan():
    ratio = [1.8, 1.8, 2.6, 3.2, 3.2, 3.2, 1.14, 0.993, 0.986, 0.50, 2.2, 2.1, 2.3, 2.2, 0.76, 1.16] + [6.0] * 6
    r = ml.choose_references(ratio)
    assert r["references"] == [10, 15, 9, 8] and r["spares"] == [7, 16, 1]
    ids = {st: [f"IMPC_{st}_{i:04d}" for i in range(20)] for st in aa.STAGES}
    p1, p2 = ml.plan_sessions(ids), ml.plan_sessions(ids)
    assert p1 == p2
    t = p1["tasks"]
    assert len(t) == 10 + 16 + 4 and len({x["task"] for x in t}) == len(t)
    for s in range(1, 6):
        atl = [x["stage"] for x in t if x["session"] == s and x["kind"] == "atlas"]
        assert sorted(atl) == sorted(aa.STAGES)
    for st in aa.STAGES:
        assert len(p1["specimens"][st]) == 8 and set(p1["specimen_repeats"][st]) <= set(p1["specimens"][st])
    for x in t:
        if x["kind"] == "specimen" and x["repeat"] == 2:
            first = [y for y in t if y["id"] == x["id"] and y["repeat"] == 1][0]
            assert first["session"] != x["session"] and first["volume"] == x["volume"]


def test_kabsch_brings_specimen_offsets_to_atlas_frame():
    rng = np.random.default_rng(6)
    atlas = rng.normal(size=(K, 3))
    R = _rot(rng)
    rows = [i - 1 for i in ml.TARGETS]
    off = 0.1 * rng.normal(size=(6, 3))
    spec = {"s1": atlas @ R.T + 5.0}
    man = {"s1": (atlas[rows] + off) @ R.T + 5.0}
    res = ml.specimen_offsets(man, spec, atlas, off)
    np.testing.assert_allclose(res["mean_offset_mm"], off, atol=1e-9)
    assert res["angle_with_atlas_offset_deg"] == pytest.approx(0.0, abs=1e-5)


def test_constants_match_preregistration():
    assert ml.SEED_MTD == 20261126 and ml.N_BOOT == 2000 and ml.TARGETS == (17, 18, 19, 20, 21, 22)
    assert (ml.Q_LOW, ml.Q_HIGH, ml.Q_NOT) == (0.75, 1.25, 0.50)
    assert ml.EPS_FACTOR == 0.5 and ml.REF_RATIO_MAX == 3.0 and ml.N_REPEATS_ATLAS == 5
    assert ml.N_SPECIMENS_PER_STAGE == 8 and ml.N_SPECIMEN_REPEATS == 2
    assert ml.G0E_TOL_VOX == 1.0
