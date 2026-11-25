"""FI-1s con hojas y fotos SINTÉTICAS (docs/prenatal/PREREGISTRO_FOTO_IMPRESION_SINTETICA.md).

Qué haría fallar cada prueba: si las hojas no fueran deterministas o los pares se salieran de 10–60 mm, se cruzaran o
pisaran la escala, el material no sería el preregistrado; si el PDF no midiera A4 a escala 1:1, la referencia en mm no
valdría; si los «+» no estuvieran dibujados donde dice el diseño, la referencia no sería la distancia diseñada; si una
foto simulada de la hoja no diera las distancias diseñadas con la cadena de FI-1, generador y medida no encajarían; si
G0-impresión aceptara una hoja escalada, no detectaría «ajustar a página». Sin datos de personas.
"""
import importlib.util
import json
import math
import re
from pathlib import Path

import numpy as np
import pytest

from geovida import fi1s
from geovida import print_measure as pm

_root = Path(__file__).resolve().parents[1] / "scripts"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _root / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hojas, script = _load("fi1s_hojas"), _load("fi1s")


def test_design_is_deterministic_and_valid():
    d1, d2 = fi1s.design_all(), fi1s.design_all()
    assert d1 == d2 and len(d1["sheets"]) == 6
    x0, y0, w, h = fi1s.FRAME
    scale_x = fi1s.ticks()[0, 0]
    for s in d1["sheets"].values():
        pairs = s["pairs"]
        assert sorted(pairs) == ["P1", "P2", "P3", "P4"]
        pts = []
        for d in pairs.values():
            assert 10 <= d["mm"] <= 60
            assert math.isclose(d["mm"], float(np.linalg.norm(np.subtract(d["q"], d["p"]))))
            for x, y in (d["p"], d["q"]):
                assert x0 < x < scale_x - fi1s.MIN_SEP + 1e-9 and y0 < y < y0 + h
                pts.append((x, y))
        dist = [math.dist(a, b) for i, a in enumerate(pts) for b in pts[i + 1:]]
        assert min(dist) >= fi1s.MIN_SEP
        segs = [(np.array(d["p"]), np.array(d["q"])) for d in pairs.values()]
        assert not any(fi1s._segments_cross(*segs[i], *segs[j]) for i in range(4) for j in range(i + 1, 4))


def test_pdf_is_a4_with_six_pages(tmp_path):
    d = hojas.generate(tmp_path)
    raw = (tmp_path / "hojas_fi1s.pdf").read_bytes()
    boxes = re.findall(rb"/MediaBox \[\s*0 0 ([\d.]+) ([\d.]+)\s*\]", raw)
    assert len(boxes) == 6
    for w, h in boxes:                                       # 1 pt = 25,4 / 72 mm
        assert math.isclose(float(w) * 25.4 / 72, 210, abs_tol=0.01)
        assert math.isclose(float(h) * 25.4 / 72, 297, abs_tol=0.01)
    stored = json.loads((tmp_path / "valores_disenados.json").read_text(encoding="utf-8"))
    assert stored["sheets"] == d["sheets"]


def test_crosses_are_drawn_where_designed():
    import matplotlib.pyplot as plt
    rng = np.random.default_rng(0)
    code, sheet = next(iter(fi1s.design_all()["sheets"].items()))
    fig = fi1s.render_sheet(code, sheet, rng)
    px = 10                                                   # píxeles por mm
    fig.set_dpi(25.4 * px)
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())[..., :3].mean(axis=2)
    plt.close(fig)
    for d in sheet["pairs"].values():
        for x, y in (d["p"], d["q"]):
            c = img[int(round(y * px)) - 1:int(round(y * px)) + 2, int(round(x * px)) - 1:int(round(x * px)) + 2]
            assert c.max() > 200                              # el centro del «+» es blanco sobre el moteado
            off = img[int(round((y + 1.0) * px)), int(round((x + 1.0) * px))]
            assert off < 200                                  # a 1 mm en diagonal ya es moteado


def _photo(rng, sheet, tilt=0.15, noise=0.4):
    """Foto simulada: homografía aleatoria de la hoja en mm a píxeles, con ruido de marcado."""
    src = fi1s.frame_corners()
    dst = (src - src.mean(0)) * 12 + 1500 + rng.uniform(-tilt, tilt, (4, 2)) * 12 * 160
    H = pm.homography(src, dst)

    def j(x):
        return (pm.warp_points(H, np.asarray(x, float)) + rng.normal(0, noise, (len(x), 2))).tolist()
    return {"aspect_mm": list(fi1s.FRAME[2:]), "corners": j(src), "midpoints": j(fi1s.frame_midpoints()),
            "ticks": j(fi1s.ticks()), "pairs": {k: j([d["p"], d["q"]]) for k, d in sheet["pairs"].items()}}


def _setup(tmp_path, ruler_scale=1.0):
    base = tmp_path / "fi1s"
    design = hojas.generate(base)
    (base / "marcas").mkdir()
    w, h = fi1s.FRAME[2:]
    (base / "regla.json").write_text(json.dumps({c: [w * ruler_scale, h * ruler_scale] for c in design["sheets"]}))
    rng = np.random.default_rng(5)
    for code, sheet in design["sheets"].items():
        for f in fi1s.N_PHOTOS:
            for r in (1, 2, 3):
                m = _photo(rng, sheet)
                m["aspect_mm"] = [w * ruler_scale, h * ruler_scale]
                m.update({"print": code, "photo": f})
                (base / "marcas" / f"{code}-{f}_r{r}.json").write_text(json.dumps(m))
    return base


def test_end_to_end_synthetic_photos_recover_design(tmp_path):
    base = _setup(tmp_path)
    g = script.run_gates(base)
    assert g["passed"] and g["n_marks"] == 54 and g["n_failed"] == 0
    res = script.run_analysis(base, g)
    assert res["n_measurements"] == 216 and res["n_prints"] == 6 and res["n_photos"] == 18
    assert res["median_abs_error"] < 0.02 and res["verdict"]["FI-1sa"] == "apoyada"
    assert res["fi1sc"]["median_abs_error_uncorrected"] > res["median_abs_error"]
    assert set(res["fi1sc"]["median_abs_error_by_photo_type"]) == {"F1", "F2", "F3"}


def test_gate_print_rejects_scaled_sheet(tmp_path):
    base = _setup(tmp_path, ruler_scale=0.97)                 # «ajustar a página»: 3 % más pequeña
    g = script.run_gates(base)
    assert not g["passed"] and "fotos" not in g["gates"]
    assert not fi1s.gate_print({})["passed"]


def test_plan_three_sessions_of_eighteen():
    p = fi1s.plan(script.photos())
    assert len(p) == 54 and p == fi1s.plan(script.photos())
    for s in (1, 2, 3):
        assert sorted(x["photo"] for x in p if x["session"] == s) == sorted(script.photos())


def test_analyze_refuses_without_gates(tmp_path, monkeypatch):
    monkeypatch.setattr(script, "OUT", tmp_path / "out")
    with pytest.raises(SystemExit):
        script.main(["analyze"])
