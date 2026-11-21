"""H21: formas nuevas con verdad analítica, diseño congelado y reglas de veredicto (sin datos medidos)."""
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import ndimage as ndi
from skimage.measure import marching_cubes, mesh_surface_area

from geovida import h21
from geovida.experiment import ALL_SHAPES, Condition, run_condition
from geovida.phantoms import EXTRA_NAMES, H21_NAMES, NEW_NAMES, PHANTOM_NAMES, make_phantom
from geovida.reference import crofton_area
from geovida.topology import betti_numbers

ROOT = Path(__file__).resolve().parents[1]


def _fine_grid(ph, voxels_per_t, seed=0):
    h = ph.t / voxels_per_t
    hx = np.array(ph.half_extent) + 2 * h
    shift = np.random.default_rng(seed).uniform(-0.5, 0.5, size=3) * h
    axes = [np.arange(-e, e + h, h) + s for e, s in zip(hx, shift)]
    pts = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1)
    return ph.contains(pts), h


def test_h21_shapes_are_appended_without_moving_earlier_seed_indices():
    assert H21_NAMES == ("prolate", "hemisphere", "cone", "horseshoe")
    assert ALL_SHAPES[:12] == PHANTOM_NAMES + EXTRA_NAMES + NEW_NAMES
    assert ALL_SHAPES[12:] == H21_NAMES
    assert not set(H21_NAMES) & set(PHANTOM_NAMES + EXTRA_NAMES + NEW_NAMES)


def test_closed_form_truths():
    t = 1.0
    p = make_phantom("prolate", t).truth
    a, c = 0.5, 1.5
    e = math.sqrt(1 - a * a / (c * c))
    assert p.volume == pytest.approx(4 / 3 * math.pi * a * a * c)
    assert p.surface_area == pytest.approx(2 * math.pi * a * a * (1 + c / (a * e) * math.asin(e)))
    hs = make_phantom("hemisphere", t).truth
    assert hs.volume == pytest.approx(2 / 3 * math.pi) and hs.surface_area == pytest.approx(3 * math.pi)
    co = make_phantom("cone", t).truth
    assert co.volume == pytest.approx(math.pi * 2 / 3) and co.surface_area == pytest.approx(
        math.pi * (1 + math.sqrt(5)))
    ho = make_phantom("horseshoe", t).truth
    assert ho.volume == pytest.approx(math.pi**2 * 2 * 0.25)
    assert ho.surface_area == pytest.approx(2 * math.pi**2 * 2 * 0.5 + 2 * math.pi * 0.25)
    for name in H21_NAMES:
        tr = make_phantom(name, t).truth
        assert tr.betti == (1, 0, 0) and tr.chi == 1 and tr.t_solid == pytest.approx(t)


@pytest.mark.parametrize("name", H21_NAMES)
def test_truth_scales_with_t(name):
    a, b = make_phantom(name, 1.0).truth, make_phantom(name, 2.0).truth
    assert b.volume == pytest.approx(8 * a.volume) and b.surface_area == pytest.approx(4 * a.surface_area)


@pytest.mark.parametrize("name", H21_NAMES)
def test_volume_matches_fine_raster(name):
    ph = make_phantom(name, 1.0)
    mask, h = _fine_grid(ph, 16)
    assert mask.sum() * h**3 == pytest.approx(ph.truth.volume, rel=0.01)


@pytest.mark.parametrize("name", H21_NAMES)
def test_area_matches_mesh_of_partial_volume_field(name):
    """Marching cubes sin suavizar sobre la cobertura (supermuestreo 2³) de una rasterización girada.

    No se usa la malla suavizada de ``test_phantoms_v04``: el suavizado de 1 vóxel redondea el borde de la
    media bola y el vértice del cono (−5 % y −8 % a 16 vóxeles por t). Tampoco Crofton: con caras planas
    alineadas con la rejilla infraestima un 2,7–3,1 % (sesgo de orientación de las 13 direcciones)."""
    from scipy.spatial.transform import Rotation
    ph = make_phantom(name, 1.0)
    rot = Rotation.random(random_state=1).as_matrix()
    h = 1 / 24
    e = ph.bounding_radius + 2 * h
    ax = np.arange(-e, e + h, h)
    pts = np.stack(np.meshgrid(ax, ax, ax, indexing="ij"), axis=-1)
    acc = np.zeros(pts.shape[:3], np.float32)
    for d in np.array(np.meshgrid((-.25, .25), (-.25, .25), (-.25, .25))).reshape(3, -1).T:
        acc += ph.contains((pts + d * h) @ rot)
    verts, faces, _, _ = marching_cubes(np.pad(acc / 8, 2), 0.5, spacing=(h, h, h))
    assert mesh_surface_area(verts, faces) == pytest.approx(ph.truth.surface_area, rel=0.015)


def test_crofton_orientation_bias_on_axis_aligned_flat_faces_is_documented():
    """Hallazgo previo a medir (docs/PREREGISTRO_H21.md §3): con la base alineada con la rejilla, Crofton
    infraestima la media bola más que girada. El barrido gira cada realización al azar."""
    from scipy.spatial.transform import Rotation
    ph = make_phantom("hemisphere", 1.0)
    h = 1 / 24
    e = ph.bounding_radius + 2 * h
    ax = np.arange(-e, e + h, h)
    pts = np.stack(np.meshgrid(ax, ax, ax, indexing="ij"), axis=-1)
    tr = ph.truth.surface_area
    aligned = crofton_area(ph.contains(pts), (h, h, h)) / tr - 1
    rotated = crofton_area(ph.contains(pts @ Rotation.random(random_state=1).as_matrix()), (h, h, h)) / tr - 1
    assert aligned < -0.02 and abs(rotated) < 0.015


@pytest.mark.parametrize("name", ("prolate",))
def test_area_of_smooth_shape_matches_independent_mesh(name):
    ph = make_phantom(name, 1.0)
    mask, h = _fine_grid(ph, 16)
    sm = ndi.gaussian_filter(np.pad(mask.astype(float), 2), 1.0)
    verts, faces, _, _ = marching_cubes(sm, level=0.5, spacing=(h, h, h))
    assert mesh_surface_area(verts, faces) == pytest.approx(ph.truth.surface_area, rel=0.04)


@pytest.mark.parametrize("name", H21_NAMES)
@pytest.mark.parametrize("conn", [6, 26])
def test_topology_matches_fine_raster(name, conn):
    mask, _ = _fine_grid(make_phantom(name, 1.0), 12)
    assert betti_numbers(mask, connectivity=conn).as_tuple() == (1, 0, 0)


@pytest.mark.parametrize("name", H21_NAMES)
def test_shape_fits_inside_declared_half_extent(name):
    mask, _ = _fine_grid(make_phantom(name, 1.0), 10)
    idx = np.argwhere(mask)
    assert idx.min() >= 1 and all(idx[:, k].max() <= mask.shape[k] - 2 for k in range(3))


def test_design_and_seed_are_frozen():
    d = h21.design()
    assert len(d) == 4 * 5 * 2 * 4 * 50 and {c.shape for c in d} == set(H21_NAMES)
    used = {20261109, 20261110, 20261111, 20261112, 20261113, 20261114, 20261115, 20261116, 20261117,
            20261120, 20261121, 20261122, 20261123, 20261124, 20261125, 20261126}
    assert h21.SEED not in used


def test_condition_adds_crofton_column_on_the_same_mask():
    rows = run_condition(Condition("prolate", 6.0, 1.0, "ideal", 0), h21.SEED, ("otsu",), h21.crofton_extra)
    assert rows[0]["area_crofton"] > 0
    assert rows[0]["area_crofton"] == pytest.approx(rows[0]["area_true"], rel=0.15)


def _cells(better: float, noninf: float = 1.0, evaluable: bool = True) -> pd.DataFrame:
    rows = []
    for shape in H21_NAMES:
        for th in h21.T_OVER_H:
            for an in h21.ANISOTROPY:
                for prof in h21.PROFILES:
                    for k, seg in enumerate(h21.SEGMENTERS):
                        i = len(rows)
                        rows.append({"shape": shape, "t_over_h": th, "anisotropy": an, "profile": prof,
                                     "segmenter": seg, "evaluable": evaluable,
                                     "crofton_better": (i % 100) < better * 100,
                                     "crofton_noninferior": (i % 100) < noninf * 100})
    return pd.DataFrame(rows)


def test_verdict_rules():
    v = h21.verdicts(_cells(0.9))
    assert v["H21a"]["cells"] == 96 and v["H21b"]["cells"] == 144 and v["H21c"]["cells"] == 144
    assert v["H21a"]["verdict"] == "apoyada" and v["H21b"]["verdict"] == "apoyada"
    assert v["decision"] == "cambiar_a_crofton"
    assert h21.verdicts(_cells(0.1))["H21a"]["verdict"] == "contraria"
    assert h21.verdicts(_cells(0.5))["decision"] == "mantener_area_sdf"
    mixed = h21.verdicts(_cells(0.9, noninf=0.5))
    assert mixed["H21b"]["verdict"] == "no_apoyada" and mixed["decision"] == "crofton_solo_a_resolucion_fina"
    none = h21.verdicts(_cells(0.9, evaluable=False))
    assert none["H21a"]["verdict"] == "no_evaluable" and none["decision"] == "mantener_area_sdf"


def test_cell_table_compares_absolute_medians():
    base = {"shape": "cone", "t_over_h": 8.0, "anisotropy": 1.0, "profile": "ideal", "segmenter": "otsu",
            "area_true": 10.0, "err_area_mc": 0.0}
    df = pd.DataFrame([dict(base, rep=i, err_volume=0.01, err_area_sdf=0.03, area_crofton=10.0 - 0.1 * i)
                       for i in range(3)])
    c = h21.cell_table(df).iloc[0]
    assert c["med_err_crofton"] == pytest.approx(-0.01) and bool(c["crofton_better"])
    assert bool(c["evaluable"]) and bool(c["crofton_noninferior"])


def test_runner_end_to_end_on_a_tiny_design(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("run_h21", ROOT / "scripts" / "run_h21.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod.h21, "design", lambda reps: [Condition("cone", 4.0, 1.0, "realistic", 0),
                                                         Condition("horseshoe", 8.0, 2.0, "noisy", 0)])
    out = tmp_path / "sweep.csv.gz"
    assert mod.main(["run", "--out", str(out), "--reps", "1"]) == 0
    with pytest.raises(SystemExit):
        mod.main(["run", "--out", str(out), "--reps", "1"])   # se mide una sola vez
    v = tmp_path / "verdicts.json"
    assert mod.main(["analyze", "--sweep", str(out), "--out", str(v)]) == 0
    res = json.loads(v.read_text(encoding="utf-8"))
    assert res["rows"] == 6 and res["verdicts"]["H21a"]["verdict"] == "no_evaluable"
    assert (tmp_path / "sweep_manifest.json").exists()
