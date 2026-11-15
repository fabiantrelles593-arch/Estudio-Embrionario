"""Pruebas de scripts/p3_memos.py (segmentador B de P3) sin pesos de MEMOS.

La acumulación por franjas y la ampliación por franjas se comparan con el cálculo directo sobre el
volumen entero. Las pruebas que necesitan torch o MONAI se saltan si no están instalados.
"""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("p3_memos", ROOT / "scripts" / "p3_memos.py")
pm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pm)


def test_window_starts_rule():
    assert pm.window_starts(300) == [0, 25, 50, 75, 100, 125, 150, 172]
    assert pm.window_starts(128) == [0]
    assert pm.window_starts(129) == [0, 1]


def test_window_starts_match_monai():
    monai_utils = pytest.importorskip("monai.data.utils")
    for size in (128, 131, 190, 271, 300):
        sl = monai_utils.dense_patch_slices((size,), (128,), (25,))
        assert sorted({s[0].start for s in sl}) == pm.window_starts(size)


def _predictor(roi):
    g = np.indices((roi, roi, roi)).astype(np.float32)

    def f(p):  # depende del contenido y de la posición dentro de la ventana
        return np.stack([p, p ** 2, g[0] * p, g[1] - g[2]])
    return f


def test_sliding_mean_matches_direct():
    rng = np.random.default_rng(0)
    roi, ov = 8, 0.5
    vol = rng.random((23, 13, 9)).astype(np.float32)
    pred = _predictor(roi)
    out = np.zeros((4, *vol.shape), np.float32)
    n = pm.sliding_mean_logits(vol, pred, 4, out, roi=roi, overlap=ov)
    acc = np.zeros_like(out)
    cnt = np.zeros(vol.shape, np.float32)
    k = 0
    for z in pm.window_starts(23, roi, ov):
        for y in pm.window_starts(13, roi, ov):
            for x in pm.window_starts(9, roi, ov):
                acc[:, z:z + roi, y:y + roi, x:x + roi] += pred(vol[z:z + roi, y:y + roi, x:x + roi])
                cnt[z:z + roi, y:y + roi, x:x + roi] += 1
                k += 1
    assert n == k
    assert cnt.min() >= 1
    np.testing.assert_allclose(out, acc / cnt, rtol=1e-5, atol=1e-5)


def test_sliding_rejects_small_volume():
    with pytest.raises(ValueError):
        pm.sliding_mean_logits(np.zeros((5, 9, 9), np.float32), _predictor(8), 4,
                               np.zeros((4, 5, 9, 9), np.float32), roi=8)


def test_upsample_slabs_equal_whole():
    torch = pytest.importorskip("torch")
    import torch.nn.functional as F

    rng = np.random.default_rng(1)
    lg = rng.normal(size=(5, 11, 6, 7)).astype(np.float32)
    whole = F.interpolate(torch.from_numpy(lg)[None], scale_factor=2, mode="trilinear",
                          align_corners=False)[0].argmax(0).numpy()
    for slab in (1, 3, 4, 11):
        np.testing.assert_array_equal(pm.upsample_argmax(lg, 2, slab=slab), whole)
    np.testing.assert_array_equal(pm.upsample_argmax(lg, 1), lg.argmax(0))


def test_block_mean_and_intensity():
    a = np.arange(5 * 4 * 4, dtype=np.float32).reshape(5, 4, 4)
    b = pm.block_mean(a, 2)
    assert b.shape == (2, 2, 2)
    assert b[0, 0, 0] == pytest.approx(a[:2, :2, :2].mean())
    v = pm.memos_intensity(np.array([0.0, 1.0]), 0.0, 1.0)
    assert v[0] == pytest.approx(175 / 425)
    assert v[1] == pytest.approx(1.0)


def test_body_box_minimum_and_margin():
    vol = np.zeros((60, 50, 40), np.float32)
    vol[20:30, 20:28, 15:20] = 1.0
    box = pm.body_box(vol, margin=3, min_size=16)
    assert box[0] == slice(17, 33)
    assert all(s.stop - s.start >= 16 for s in box)
    assert all(s.start <= lo and s.stop >= hi for s, (lo, hi) in zip(box, [(20, 30), (20, 28), (15, 20)]))


def test_best_translation_recovers_shift():
    from scipy import ndimage

    rng = np.random.default_rng(3)
    f = ndimage.gaussian_filter(rng.random((48, 44, 40)), 3) > 0.5
    f[:6], f[-6:], f[:, :6], f[:, -6:], f[:, :, :6], f[:, :, -6:] = (False,) * 6
    for t in [(5, -3, 2), (0, 0, 0), (-4, 1, -5)]:
        g = np.roll(f, tuple(-v for v in t), (0, 1, 2))  # g desplazada t vuelve a f
        found, d = pm.best_translation(f, g)
        assert found == t
        assert d == pytest.approx(1.0)


def _labeled_body(shape=(72, 28, 28)):
    """Cuerpo alargado en el eje 0 con etiquetas distintas en bloques pequeños (estructura interna)."""
    rng = np.random.default_rng(5)
    lab = np.zeros(shape, np.uint8)
    blocks = rng.integers(1, 40, size=(shape[0] // 4, 4, 4))
    lab[8:-8, 8:-8, 8:-8] = np.kron(blocks, np.ones((4, 3, 3), np.uint8))[: shape[0] - 16, :12, :12]
    return lab


def test_local_translations_rigid_shift_has_no_spread():
    atlas = _labeled_body()
    t = (2, -3, 1)
    memos = np.roll(atlas, t, (0, 1, 2))  # el atlas desplazado t coincide con MEMOS
    r = pm.local_translations(atlas, memos, center=(0, 0, 0), rad=6)
    assert r["axis"] == 0
    assert [p["translation_vox"] for p in r["parts"]] == [list(t)] * 3
    assert r["spread_vox"] == 0
    assert all(p["agreement"] == pytest.approx(1.0) for p in r["parts"])


def test_local_translations_detect_non_rigid_misfit():
    atlas = _labeled_body()
    memos = np.zeros_like(atlas)
    edges = np.linspace(8, 64, 4).astype(int)
    for k, dy in enumerate((-4, 0, 4)):  # cada tercio desplazado distinto: no hay traslación única
        part = np.zeros_like(atlas)
        part[edges[k]:edges[k + 1]] = atlas[edges[k]:edges[k + 1]]
        memos = np.maximum(memos, np.roll(part, (0, dy, 0), (0, 1, 2)))
    r = pm.local_translations(atlas, memos, center=(0, 0, 0), rad=8)
    assert [p["translation_vox"][1] for p in r["parts"]] == [-4, 0, 4]
    assert r["spread_vox"] == 8
    assert pm.label_agreement(atlas, memos, (0, 0, 0)) < 0.9


def test_dice_table_best_match():
    atlas = np.zeros((10, 10, 10), np.int16)
    memos = np.zeros_like(atlas, dtype=np.uint8)
    atlas[:5] = 102
    memos[:4] = 49
    memos[4:6] = 7
    t = pm.dice_table(memos, atlas)
    assert t[102]["memos"] == 49
    assert t[102]["dice"] == pytest.approx(2 * 400 / (500 + 400), abs=1e-4)
