"""H19 (``docs/PREREGISTRO_H19.md``): reparto ajuste/calibración, remuestreo, red de dos etapas y puertas.

Solo volúmenes sintéticos pequeños; ninguna imagen real. Qué haría fallar cada prueba:
* si un embrión quedara en ajuste y en calibración, el certificado se calibraría con casos que la red vio;
* si el remuestreo desplazara la rejilla, el volumen a resolución completa saldría sesgado;
* si la red no pudiera aprender ni una bola con moteado, no tendría sentido entrenarla con datos reales;
* si las puertas dejaran pasar un segmentador que falla, se abriría la prueba sin motivo.
"""
import numpy as np
import pandas as pd
import pytest

torch = pytest.importorskip("torch")

from geovida import h19  # noqa: E402


def _ball(shape=(64, 64, 64), radius=14, center=None, seed=0):
    rng = np.random.default_rng(seed)
    c = center or [n / 2 for n in shape]
    zz, yy, xx = np.mgrid[: shape[0], : shape[1], : shape[2]]
    inside = ((zz - c[0]) ** 2 + (yy - c[1]) ** 2 + (xx - c[2]) ** 2) <= radius ** 2
    img = np.where(inside, 1.0, 0.3) * rng.rayleigh(1.0, shape)
    return img.astype(np.float32), inside


def test_fit_calibration_split_is_by_embryo_and_reproducible():
    df = pd.DataFrame({"embryo_id": [f"E{i // 2}" for i in range(40)], "image": [f"i{i}" for i in range(40)]})
    a = h19.fit_calibration_split(df)
    b = h19.fit_calibration_split(df)
    assert a["role"].tolist() == b["role"].tolist()
    assert not set(a.loc[a.role == "cal", "embryo_id"]) & set(a.loc[a.role == "fit", "embryo_id"])
    assert a.loc[a.role == "cal", "embryo_id"].nunique() == 4          # 20 % de 20 embriones


def test_downsample_upsample_keeps_volume_and_position():
    _, inside = _ball(radius=16)
    small = h19.downsample(inside.astype(np.float32), 4)
    back = h19.upsample_prob(small, 4, inside.shape) >= 0.5
    assert abs(back.sum() - inside.sum()) / inside.sum() < 0.05
    com = lambda m: np.array(np.nonzero(m)).mean(axis=1)               # noqa: E731
    assert np.abs(com(back) - com(inside)).max() < 1.0


def test_pad_and_bbox():
    a, pads = h19.pad_to(np.zeros((9, 17, 8)))
    assert a.shape == (16, 24, 8) and pads[0] == (0, 7)
    m = np.zeros((20, 20, 20), bool)
    m[5:8, 6:9, 7:10] = True
    assert h19.bbox(m, 2) == (slice(3, 10), slice(4, 11), slice(5, 12))
    assert h19.bbox(np.zeros((4, 4, 4), bool), 1) is None


def test_two_stage_network_learns_a_speckled_ball(monkeypatch):
    monkeypatch.setattr(h19, "THREADS", 1)
    train = [_ball(radius=12 + k, center=[30 + k, 32, 34 - k], seed=k) for k in range(4)]
    cs = [h19.coarse_sample(img, ref) for img, ref in train]
    coarse = h19.train([(x, y) for x, y in cs], epochs=40, seed=1)
    fs = []
    for img, ref in train:
        pc = h19.upsample_prob(h19.predict(coarse, h19.coarse_sample(img)[0]), h19.COARSE, img.shape)
        s = h19.fine_sample(img, pc, ref)
        assert s is not None
        fs.append((s[0], s[1]))
    fine = h19.train(fs, epochs=40, seed=2, in_ch=2)
    img, ref = _ball(radius=13, center=[31, 31, 33], seed=9)                 # caso nuevo
    mask, prob = h19.segment_full(coarse, fine, img)
    dice = 2 * (mask & ref).sum() / (mask.sum() + ref.sum())
    assert dice > 0.80
    assert 0.0 <= h19.uncertain_band(prob, mask) <= 1.0


def test_save_and_load_give_the_same_prediction(tmp_path):
    net = h19.UNet3D()
    x = np.random.default_rng(0).random((1, 16, 16, 16), dtype=np.float32)
    h19.save(net, tmp_path / "n.pt")
    again = h19.load(tmp_path / "n.pt")
    assert np.allclose(h19.predict(net, x), h19.predict(again, x))


def _cal(n=40, good=True, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for e in range(n):
        u = float(rng.uniform(0, 0.6))
        err = rng.normal(0, 0.02) if (good and u < 0.3) else rng.normal(0, 0.4)
        rows.append({"embryo_id": f"E{e}", "d_over_hgeo": float(rng.uniform(5, 15)), "snr_hat": float(rng.uniform(5, 9)),
                     "edge_width": float(rng.uniform(1, 2)), "uncertain_band": u, "rel_error_volume": err})
    return pd.DataFrame(rows)


def test_gates_stop_a_segmenter_that_fails_and_pass_a_predictable_one():
    bad = h19.gates(_cal(good=False).assign(rel_error_volume=0.5))
    assert not bad["S"]["passed"] and not bad["passed"]
    ok = h19.gates(_cal(n=80, seed=3))
    assert ok["S"]["passed"]
    assert ok["C"]["n_green"] >= 0 and set(ok["C"]) >= {"n_green", "fail", "passed"}


def test_certificate_uses_the_network_uncertainty():
    df = _cal(n=80, seed=4)
    cert = h19.fit_certificate(df)
    assert cert["model"]["features"] == list(h19.FEATURES)
    lit = h19.lights(df, cert)
    lo = lit[lit.uncertain_band < 0.15]["p_ok10"].mean()
    hi = lit[lit.uncertain_band > 0.45]["p_ok10"].mean()
    assert lo > hi
