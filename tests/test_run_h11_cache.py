"""La caché de ``scripts/run_h11.py`` da la misma tabla que ``h11.run_cases`` y reanuda sin repetir casos.

Volúmenes sintéticos (los mismos que ``tests/test_h11.py``); ninguna imagen real.
"""
import argparse
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

nib = pytest.importorskip("nibabel")

from geovida import h11  # noqa: E402

_spec = importlib.util.spec_from_file_location("run_h11", Path(__file__).resolve().parents[1] / "scripts" / "run_h11.py")
rh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rh)


def _ball(n=40, radius=12.0, seed=0):
    from scipy.ndimage import gaussian_filter
    zz, yy, xx = np.mgrid[:n, :n, :n]
    c = (n - 1) / 2
    inside = ((zz - c) ** 2 + (yy - c) ** 2 + (xx - c) ** 2) <= radius ** 2
    img = 0.1 + 0.8 * gaussian_filter(inside.astype(np.float32), 1.2)
    return (img + np.random.default_rng(seed).normal(0, 0.02, img.shape)).astype(np.float32), inside


def _save(path, arr):
    im = nib.Nifti1Image(arr, np.diag([0.05, 0.05, 0.05, 1.0]))
    im.header.set_xyzt_units("mm")
    nib.save(im, str(path))


@pytest.fixture()
def setup(tmp_path):
    rows = []
    for k in range(3):
        img, inside = _ball(radius=11.0 + k, seed=k)
        _save(tmp_path / f"e{k}.nii.gz", img)
        _save(tmp_path / f"e{k}_lab.nii.gz", inside.astype(np.uint8))
        for s in ("body", "ventricle"):
            rows.append({"embryo_id": f"E{k // 2}", "structure": s, "image": f"e{k}.nii.gz",
                         "label": f"e{k}_lab.nii.gz", "label_value": 1})
    args = argparse.Namespace(root=str(tmp_path), profile="realistic", frozen=None)
    return pd.DataFrame(rows), args, tmp_path


def test_cache_matches_run_cases_and_resumes(setup, monkeypatch):
    man, args, tmp = setup
    direct = h11.run_cases(man, root=args.root, profile=args.profile)
    cache = tmp / "cache.csv"
    rh._run_cached(man.iloc[:3], args, None, cache)          # se corta a medias
    cached = rh._run_cached(man, args, None, cache)           # y se reanuda
    pd.testing.assert_frame_equal(cached.reset_index(drop=True), direct.reset_index(drop=True), check_dtype=False)
    assert rh.h11.evaluate_h11(cached)["h11a"] == h11.evaluate_h11(direct)["h11a"]

    def boom(*_, **__):
        raise AssertionError("no debía recalcular")
    monkeypatch.setattr(rh.h11, "run_cases", boom)
    again = rh._run_cached(man.iloc[::-1], args, None, cache)  # orden del manifiesto, sin recalcular
    rev = man.iloc[::-1]
    assert list(again["structure"]) == [s for s in rev["structure"] for _ in h11.SEGMENTERS]
    assert list(again["embryo_id"]) == [e for e in rev["embryo_id"] for _ in h11.SEGMENTERS]


def test_cache_of_another_calibration_is_rejected(setup):
    man, args, tmp = setup
    cache = tmp / "cache.csv"
    rh._run_cached(man.iloc[:1], args, None, cache)
    other = argparse.Namespace(**{**vars(args), "profile": "us_raw"})
    with pytest.raises(SystemExit, match="otra calibración"):
        rh._run_cached(man, other, None, cache)
