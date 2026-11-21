"""El prototipo del navegador (prototype/calibre_geovida.html) calcula lo mismo que el código Python del proyecto.

La página no tiene servidor: toda la matemática está en un bloque JavaScript delimitado por ``/* CORE:BEGIN */`` y
``/* CORE:END */``. Estas pruebas extraen ese bloque, lo ejecutan con Node y lo comparan con ``geovida.dating``,
``geovida.trajectory`` y ``geovida.chainguard`` sobre las mismas entradas. También vigilan la privacidad por diseño:
la página no debe contener ninguna llamada de red ni almacenamiento persistente.

Qué falla si alguien cambia una fórmula en un solo lado. No prueba la interfaz (eso lo hace el script de capturas)."""
import json
import math
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from geovida import chainguard, dating, trajectory

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "prototype" / "calibre_geovida.html"
FROZEN = ROOT / "results" / "summary" / "h16_chain_frozen.json"

HARNESS = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const m = html.match(/\/\* CORE:BEGIN \*\/([\s\S]*?)\/\* CORE:END \*\//);
if (!m) { console.log(JSON.stringify([{__error: 'sin bloque CORE'}])); process.exit(0); }
const core = new Function(m[1] + '; return Core;')();
const calls = JSON.parse(fs.readFileSync(0, 'utf8'));
const out = calls.map(c => { try { return core[c.fn](...c.args); } catch (e) { return {__error: String(e.message || e)}; } });
console.log(JSON.stringify(out));
"""

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="hace falta Node para ejecutar el núcleo de la página")


@pytest.fixture(scope="module")
def harness(tmp_path_factory):
    d = tmp_path_factory.mktemp("harness")
    f = d / "harness.js"
    f.write_text(HARNESS, encoding="utf-8")
    return f


def run(harness, calls):
    assert PAGE.exists(), "falta prototype/calibre_geovida.html"
    p = subprocess.run(["node", str(harness), str(PAGE)], input=json.dumps(calls), capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)


def call(harness, fn, *args):
    return run(harness, [{"fn": fn, "args": list(args)}])[0]


# --- fórmulas de edad ---------------------------------------------------------------------------------------------

CRLS = [15.0, 15.5, 22.3, 37.57, 48.0, 62.9, 80.0, 94.9, 95.0]


def test_erf_matches_math_erf(harness):
    xs = [-6.0, -3.2, -2.5, -1.0, -0.1, 0.0, 0.3, 1.0, 2.49, 2.5, 2.51, 4.0, 6.0]
    got = run(harness, [{"fn": "erf", "args": [x]} for x in xs])
    for x, g in zip(xs, got):
        assert g == pytest.approx(math.erf(x), abs=1e-12), x


def test_age_formula_and_slope_match_dating(harness):
    for c in CRLS:
        a, s, d = run(harness, [{"fn": "gaDays", "args": [c]}, {"fn": "sdGaDays", "args": [c]}, {"fn": "dgaDcrl", "args": [c]}])
        assert a == pytest.approx(dating.ga_days_intergrowth(c), abs=1e-9)
        assert s == pytest.approx(dating.sd_ga_days_intergrowth(c), abs=1e-9)
        assert d == pytest.approx(dating.dga_dcrl(c), abs=1e-9)


def test_formula_range_is_the_published_one(harness):
    got = run(harness, [{"fn": "inFormulaRange", "args": [c]} for c in (14.99, 15.0, 95.0, 95.01)])
    assert got == [False, True, True, False]


def test_prob_within_matches_dating(harness):
    cases = [(0.0, 0.5, 1.0), (0.3, 0.7, 1.0), (-0.4, 1.4, 2.0), (0.0, 0.0, 1.0), (1.5, 0.0, 1.0), (0.2, 3.0, 0.5)]
    got = run(harness, [{"fn": "probWithin", "args": list(c)} for c in cases])
    for c, g in zip(cases, got):
        assert g == pytest.approx(dating.prob_within(*c), abs=1e-9), c


def test_certify_dating_matches_python_before_the_cap(harness):
    cases = [(37.57, 0.0, 0.4, 1.0), (22.0, 0.1, 1.2, 1.0), (60.0, 0.0, 0.05, 1.0), (88.0, 0.0, 6.0, 2.0), (10.0, 0.0, 0.01, 1.0), (120.0, 0.0, 0.01, 1.0)]
    got = run(harness, [{"fn": "certifyDating", "args": list(c)} for c in cases])
    for c, g in zip(cases, got):
        ref = dating.certify_dating(*c)
        assert g["gaDays"] == pytest.approx(ref["ga_days"], abs=1e-9)
        assert g["sdFormulaDays"] == pytest.approx(ref["sd_formula_days"], abs=1e-9)
        assert g["sdMeasurementDays"] == pytest.approx(ref["sd_measurement_days"], abs=1e-9)
        assert g["sdTotalDays"] == pytest.approx(ref["sd_total_days"], abs=1e-9)
        assert g["measurementShare"] == pytest.approx(ref["measurement_share"], abs=1e-9)
        assert g["pWithinTolerance"] == pytest.approx(ref["p_within_tolerance"], abs=1e-9)
        assert g["inRange"] == ref["in_range"]
        assert g["lightRaw"] == ref["light"], c


def _sd_mm_for_probability(crl, p_target, tol=1.0):
    """sd (mm) de la medida para que P(|error de edad| <= tol) valga p_target con sesgo 0."""
    lo, hi = 1e-6, 50.0
    for _ in range(200):
        mid = (lo + hi) / 2
        p = dating.prob_within(0.0, abs(dating.dga_dcrl(crl)) * mid, tol)
        lo, hi = (mid, hi) if p > p_target else (lo, mid)
    return (lo + hi) / 2


def test_semaphore_thresholds_sit_where_dating_puts_them(harness):
    """Casos pegados a los cortes 0.50 y 0.90 por los dos lados (atrapan un umbral movido)."""
    targets = [0.45, 0.49, 0.51, 0.58, 0.86, 0.89, 0.91, 0.95]
    cases = [(40.0, 0.0, _sd_mm_for_probability(40.0, t), 1.0) for t in targets]
    got = run(harness, [{"fn": "certifyDating", "args": list(c)} for c in cases])
    for t, c, g in zip(targets, cases, got):
        ref = dating.certify_dating(*c)
        assert g["pWithinTolerance"] == pytest.approx(t, abs=1e-6)
        assert g["lightRaw"] == ref["light"], t
    assert [g["lightRaw"] for g in got] == ["rojo", "rojo", "amarillo", "amarillo", "amarillo", "amarillo", "verde", "verde"]


def test_the_page_never_emits_a_green_light(harness):
    """Sobre una imagen sin validar el tope es amarillo, aunque la probabilidad pase de 0.90."""
    g = call(harness, "certifyDating", 60.0, 0.0, 0.05, 1.0)
    assert g["pWithinTolerance"] > 0.99 and g["lightRaw"] == "verde"
    assert g["light"] == "amarillo" and g["greenBlocked"] is True
    red = call(harness, "certifyDating", 60.0, 0.0, 6.0, 1.0)
    assert red["light"] == "rojo" and red["greenBlocked"] is False
    for c in (15.0, 40.0, 95.0):
        for sd in (0.0, 0.01, 0.2, 1.0, 5.0):
            r = call(harness, "certifyDating", c, 0.0, sd, 1.0)
            assert r["light"] in ("amarillo", "rojo")


def test_out_of_range_never_gets_an_age_certificate(harness):
    r = call(harness, "certifyDating", 10.0, 0.0, 0.01, 1.0)
    assert r["inRange"] is False and r["light"] != "verde" and r["refused"] is True
    ok = call(harness, "certifyDating", 40.0, 0.0, 0.4, 1.0)
    assert ok["refused"] is False


# --- presupuesto de incertidumbre del calibre ------------------------------------------------------------------

def _budget_ref(cal1, cal2, cal_mm, p1, p2, sigma):
    ref_px = math.dist(cal1, cal2)
    l_px = math.dist(p1, p2)
    s = cal_mm / ref_px
    rel_var = 2 * sigma**2 / l_px**2 + 2 * sigma**2 / ref_px**2
    return s, l_px * s, math.sqrt(rel_var)


def test_measure_budget_matches_independent_derivation(harness):
    cal1, cal2, cal_mm = [100.0, 400.0], [100.0, 700.0], 40.0
    p1, p2, sigma = [120.0, 210.0], [415.0, 150.0], 2.0
    got = call(harness, "measure", {"cal": [cal1, cal2], "calMm": cal_mm, "crl": [p1, p2], "sigmaPx": sigma, "biasRel": 0.0})
    s, length, rel = _budget_ref(cal1, cal2, cal_mm, p1, p2, sigma)
    assert got["mmPerPx"] == pytest.approx(s, rel=1e-12)
    assert got["lengthMm"] == pytest.approx(length, rel=1e-12)
    assert got["relSd"] == pytest.approx(rel, rel=1e-12)
    assert got["sdMm"] == pytest.approx(length * rel, rel=1e-12)
    assert got["issues"] == []


def test_measure_bias_is_relative_and_signed(harness):
    base = {"cal": [[0.0, 0.0], [0.0, 300.0]], "calMm": 30.0, "crl": [[10.0, 10.0], [310.0, 10.0]], "sigmaPx": 1.0}
    a = call(harness, "measure", {**base, "biasRel": 0.0})
    b = call(harness, "measure", {**base, "biasRel": 0.05})
    assert a["biasMm"] == 0.0
    assert b["biasMm"] == pytest.approx(0.05 * a["lengthMm"], rel=1e-12)
    assert b["lengthMm"] == pytest.approx(a["lengthMm"], rel=1e-12)   # el sesgo declarado no mueve la lectura, solo el certificado


def test_measure_refuses_degenerate_inputs(harness):
    same = [[5.0, 5.0], [5.0, 5.0]]
    ok = [[0.0, 0.0], [0.0, 100.0]]
    r1 = call(harness, "measure", {"cal": same, "calMm": 10.0, "crl": ok, "sigmaPx": 1.0, "biasRel": 0.0})
    assert r1["lengthMm"] is None and r1["issues"]
    r2 = call(harness, "measure", {"cal": ok, "calMm": 0.0, "crl": ok, "sigmaPx": 1.0, "biasRel": 0.0})
    assert r2["lengthMm"] is None and r2["issues"]
    r3 = call(harness, "measure", {"cal": ok, "calMm": 10.0, "crl": same, "sigmaPx": 1.0, "biasRel": 0.0})
    assert r3["lengthMm"] is None and r3["issues"]
    r4 = call(harness, "measure", {"cal": [None, [0.0, 1.0]], "calMm": 10.0, "crl": ok, "sigmaPx": 1.0, "biasRel": 0.0})
    assert r4["lengthMm"] is None and r4["issues"]


def test_measure_warns_when_the_object_has_few_pixels(harness):
    r = call(harness, "measure", {"cal": [[0.0, 0.0], [0.0, 200.0]], "calMm": 20.0, "crl": [[0.0, 0.0], [12.0, 0.0]], "sigmaPx": 2.0, "biasRel": 0.0})
    assert r["lengthMm"] == pytest.approx(1.2, rel=1e-9)
    assert any("píxeles" in w for w in r["warnings"])


# --- trayectoria de referencia ----------------------------------------------------------------------------------

def test_reference_equations_match_trajectory(harness):
    for ga in (58.0, 63.5, 75.0, 90.0, 105.0):
        m, s = run(harness, [{"fn": "crlMeanMm", "args": [ga]}, {"fn": "crlSdMm", "args": [ga]}])
        assert m == pytest.approx(trajectory.crl_mean_mm(ga), abs=1e-9)
        assert s == pytest.approx(trajectory.crl_sd_mm(ga), abs=1e-9)


def test_reference_equations_refuse_outside_the_published_range(harness):
    for ga in (57.9, 105.1):
        assert "__error" in call(harness, "crlMeanMm", ga)
        assert "__error" in call(harness, "crlSdMm", ga)


PROJ_CASES = [
    (37.57, dict(crlRelSd=0.0, crlRelBias=0.0)),
    (37.57, dict(crlRelSd=0.03, crlRelBias=0.0)),
    (24.0, dict(crlRelSd=0.05, crlRelBias=0.02)),
    (55.0, dict(crlRelSd=0.02, crlRelBias=0.0, gaKnownDays=80.0)),
]


def _py_projection(crl, kw):
    return trajectory.projection(crl, crl_rel_sd=kw.get("crlRelSd", 0.0), crl_rel_bias=kw.get("crlRelBias", 0.0),
                                 ga_known_days=kw.get("gaKnownDays"), n_draws=20000, seed=20261218)


def test_projection_matches_python_within_monte_carlo_error(harness):
    got = run(harness, [{"fn": "projection", "args": [c, {**kw, "nDraws": 20000, "seed": 20261218}]} for c, kw in PROJ_CASES])
    for (c, kw), g in zip(PROJ_CASES, got):
        ref = _py_projection(c, kw)
        assert g["gaNow"]["medianDays"] == pytest.approx(ref["ga_now"]["median_days"], abs=0.35)
        assert len(g["rows"]) == len(ref["rows"])
        for rg, rr in zip(g["rows"], ref["rows"]):
            assert rg["inSourceRange"] == rr["in_source_range"]
            if not rr["in_source_range"]:
                assert rg["envelope"] is None
                continue
            # la edad central sale de la mediana de la simulación: la media poblacional hereda su error de Monte Carlo
            assert rg["populationMeanMm"] == pytest.approx(trajectory.crl_mean_mm(rg["gaDays"]), abs=1e-9)
            assert rg["populationMeanMm"] == pytest.approx(rr["population_mean_mm"], abs=0.8)
            for key_js, key_py in (("persistence", "persistence"), ("regression", "regression"), ("envelope", "envelope")):
                for q in ("lo", "hi"):
                    assert rg[key_js][q] == pytest.approx(rr[key_py][q], abs=0.6), (c, kw, rg["daysAhead"], key_js, q)


def test_projection_is_deterministic_for_a_seed(harness):
    a, b = run(harness, [{"fn": "projection", "args": [40.0, {"crlRelSd": 0.03, "nDraws": 5000, "seed": 7}]}] * 2)
    assert a == b


def test_projection_refuses_crl_outside_the_age_formula_without_a_known_age(harness):
    r = call(harness, "projection", 10.0, {"crlRelSd": 0.02, "nDraws": 2000, "seed": 1})
    assert "__error" in r and "rango" in r["__error"]
    ok = call(harness, "projection", 10.0, {"crlRelSd": 0.02, "nDraws": 2000, "seed": 1, "gaKnownDays": 70.0})
    assert "__error" not in ok


def test_projection_marks_horizons_beyond_the_source_range(harness):
    r = call(harness, "projection", 80.0, {"crlRelSd": 0.0, "nDraws": 2000, "seed": 3})
    flags = {row["daysAhead"]: row["inSourceRange"] for row in r["rows"]}
    assert flags[7] is True and flags[28] is False
    assert all(row["envelope"] is None for row in r["rows"] if not row["inSourceRange"])


# --- huella de la imagen (guardia de cadena) --------------------------------------------------------------------

def _test_image(seed=11, h=96, w=128):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w]
    base = 90 + 50 * np.exp(-(((yy - h / 2) / 25) ** 2 + ((xx - w / 2) / 40) ** 2)) + 0.15 * xx
    speckle = rng.gamma(shape=4.0, scale=0.25, size=(h, w))
    img = np.clip(base * speckle, 0, 255)
    return np.round(img, 3)


def test_image_indices_match_chainguard(harness):
    for seed, (h, w) in ((11, (96, 128)), (12, (64, 64)), (13, (150, 90))):
        img = _test_image(seed, h, w)
        ref = chainguard.image_indices(img)
        got = call(harness, "imageIndices", img.ravel().tolist(), w, h)
        assert got["lnCv"] == pytest.approx(ref["ln_cv"], abs=1e-9)
        assert got["skew"] == pytest.approx(ref["skew"], abs=1e-9)


def test_image_indices_are_scale_free(harness):
    img = _test_image(14, 80, 100)
    a = call(harness, "imageIndices", img.ravel().tolist(), 100, 80)
    b = call(harness, "imageIndices", (img * 0.37).ravel().tolist(), 100, 80)
    assert a["lnCv"] == pytest.approx(b["lnCv"], abs=1e-9) and a["skew"] == pytest.approx(b["skew"], abs=1e-9)


def test_image_indices_match_on_extreme_dynamic_range(harness):
    """Fondo oscuro y 0.8 % de píxeles saturados: el percentil 99.5 y el mínimo de píxeles planos deciden el resultado."""
    rng = np.random.default_rng(3)
    a = np.clip(4 + rng.normal(0, 1, (80, 80)), 0.5, None)
    a.flat[rng.choice(a.size, int(0.008 * a.size), replace=False)] = 255
    a = np.round(a, 4)
    ref = chainguard.image_indices(a)
    assert math.isnan(ref["ln_cv"]) and not math.isnan(ref["skew"])      # pocas zonas planas: solo la asimetría
    got = call(harness, "imageIndices", a.ravel().tolist(), 80, 80)
    assert got["lnCv"] is None
    assert got["skew"] == pytest.approx(ref["skew"], abs=1e-9)


def test_image_indices_refuse_tiny_or_flat_images(harness):
    noisy_small = _test_image(5, 24, 40)                               # alto < 32: la guardia no mide nada
    ref_small = chainguard.image_indices(noisy_small)
    assert math.isnan(ref_small["ln_cv"]) and math.isnan(ref_small["skew"])
    got = call(harness, "imageIndices", noisy_small.ravel().tolist(), 40, 24)
    assert got["lnCv"] is None and got["skew"] is None
    tiny = np.ones((20, 20))
    got = call(harness, "imageIndices", tiny.ravel().tolist(), 20, 20)
    assert got["lnCv"] is None and got["skew"] is None
    flat = np.full((64, 64), 100.0)
    ref = chainguard.image_indices(flat)
    got = call(harness, "imageIndices", flat.ravel().tolist(), 64, 64)
    assert (got["lnCv"] is None) == math.isnan(ref["ln_cv"])
    assert (got["skew"] is None) == math.isnan(ref["skew"])


def test_embedded_support_boxes_equal_the_frozen_json(harness):
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    regimes = {r["name"]: r["box"] for r in frozen["recal"]["body"]["regimes"]}
    sup = call(harness, "supportBody")
    for name in ("chain", "clean"):
        assert sup[name]["lnCv"] == pytest.approx(regimes[name]["ln_cv"], abs=1e-12)
        assert sup[name]["skew"] == pytest.approx(regimes[name]["skew"], abs=1e-12)


def test_locate_regime_agrees_with_chainguard_boxes(harness):
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    model = chainguard.ChainModel.from_dict(frozen["parametric"]["body"])
    pts = [(-1.5, 0.8), (-0.97, 1.30), (0.5, 2.4), (-2.5, 0.5), (-1.5, 2.4), (0.5, 0.8), (2.0, 2.0), (-1.2, 3.5)]
    got = run(harness, [{"fn": "locateRegime", "args": [{"lnCv": a, "skew": b}]} for a, b in pts])
    for (a, b), g in zip(pts, got):
        loc = model.locate({"ln_cv": a, "skew": b})
        assert g == (None if loc is None else loc[0].name), (a, b)
    assert call(harness, "locateRegime", {"lnCv": None, "skew": 1.0}) is None


# --- privacidad por diseño --------------------------------------------------------------------------------------

FORBIDDEN = [r"\bfetch\s*\(", r"XMLHttpRequest", r"\bWebSocket\b", r"sendBeacon", r"localStorage", r"sessionStorage", r"indexedDB",
             r"document\.cookie", r"navigator\.clipboard\.read", r"<form[^>]+action=", r"\bEventSource\b", r"importScripts", r"new Worker"]
ALLOWED_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")


def test_page_has_no_network_calls_or_persistent_storage():
    html = PAGE.read_text(encoding="utf-8")
    for pat in FORBIDDEN:
        assert not re.search(pat, html), f"la página contiene {pat}"


def test_page_only_references_the_font_hosts():
    html = PAGE.read_text(encoding="utf-8")
    hosts = set(re.findall(r"https?://([A-Za-z0-9.\-]+)", html))
    assert hosts <= set(ALLOWED_HOSTS), f"hosts externos no permitidos: {hosts - set(ALLOWED_HOSTS)}"


def test_page_carries_the_research_only_notice():
    html = PAGE.read_text(encoding="utf-8")
    assert "Solo investigación y educación" in html
    assert "no es un dispositivo médico" in html.lower()
