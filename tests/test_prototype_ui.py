"""La página del prototipo, abierta en un navegador de verdad (Chromium con Playwright), hace lo que dice.

Cubre el recorrido de una persona: el ejemplo sintético se abre ya medido, se carga una imagen propia, se marcan la escala y la
longitud con el ratón, se cambian los supuestos y la herramienta se niega o se pone en rojo cuando corresponde. También vigila
que la luz verde no se encienda nunca y que no haya desbordamiento horizontal en un teléfono.

Se omite si no hay Playwright o Chromium. No sustituye una revisión visual ni una prueba con usuarios."""
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
STANDALONE = ROOT / "prototype" / "calibre_geovida.standalone.html"

sync_api = pytest.importorskip("playwright.sync_api")
PIL_Image = pytest.importorskip("PIL.Image")


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as e:                              # pragma: no cover
            pytest.skip(f"no hay Chromium: {e}")
        yield b
        b.close()


def _open(browser, tmp_path, width=1280, height=900):
    ctx = browser.new_context(viewport={"width": width, "height": height})
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" and "ERR_FAILED" not in m.text else None)
    page.route("**/fonts.*/**", lambda r: r.abort())        # sin red: las tipografías caen a las del sistema
    page.goto(STANDALONE.as_uri())
    page.wait_for_timeout(500)
    return ctx, page, errors


def _lamps(page):
    return page.evaluate("[...document.querySelectorAll('.lamp')].map(l => ({text: l.textContent, on: l.classList.contains('on'), locked: l.classList.contains('locked')}))")


def _test_png(tmp_path):
    rng = np.random.default_rng(5)
    img = np.clip(rng.gamma(4, 12, (600, 800)), 0, 255)
    img[290:310, 200:500] = np.clip(img[290:310, 200:500] + 120, 0, 255)
    for k in range(16):
        img[100 + k * 20:102 + k * 20, 740:770] = 255
    f = tmp_path / "prueba.png"
    PIL_Image.fromarray(img.astype(np.uint8)).save(f)
    return f


def test_the_standalone_file_is_up_to_date_with_the_sources():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_prototype.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_example_opens_already_measured_and_never_shows_green(browser, tmp_path):
    ctx, page, errors = _open(browser, tmp_path)
    verdict = page.inner_text("#verdict")
    assert verdict.startswith("Amarillo")
    assert "no emite verde" in verdict
    lamps = _lamps(page)
    assert [l["text"] for l in lamps if l["on"]] == ["Amarillo"]
    green = next(l for l in lamps if l["text"].startswith("Verde"))
    assert green["locked"] and not green["on"]
    assert "ejemplo sintético" in page.inner_text("#stage-badge").lower()
    assert re.search(r"4[12]\.\d+ mm", page.inner_text("#crl-readout"))
    assert errors == []
    ctx.close()


def test_a_loaded_image_can_be_marked_and_measured(browser, tmp_path):
    ctx, page, errors = _open(browser, tmp_path)
    page.set_input_files("#file", str(_test_png(tmp_path)))
    page.wait_for_timeout(500)
    assert "faltan datos" in page.inner_text("#verdict")
    assert page.evaluate("document.getElementById('stage-badge').hidden") is True
    box = page.locator("#stage").bounding_box()
    k = min(box["width"] / 800, box["height"] / 600) * 0.97
    ox, oy = (box["width"] - 800 * k) / 2, (box["height"] - 600 * k) / 2
    at = lambda x, y: (box["x"] + ox + x * k, box["y"] + oy + y * k)
    page.fill("#cal-mm", "30")
    page.click("label[for=mode-scale]")
    for p in ((755, 101), (755, 401)):
        page.mouse.click(*at(*p))
    page.click("label[for=mode-crl]")
    for p in ((200, 300), (500, 300)):
        page.mouse.click(*at(*p))
    page.wait_for_timeout(400)
    m = re.search(r"([\d.]+) px → ([\d.]+) mm", page.inner_text("#crl-readout"))
    assert m and float(m.group(2)) == pytest.approx(30.0, abs=0.35)       # 300 px de objeto, 300 px = 30 mm de regla
    assert "Se parece a" in page.inner_text("#fingerprint")
    assert errors == []
    ctx.close()


def test_assumptions_drive_the_semaphore_and_the_refusal(browser, tmp_path):
    ctx, page, errors = _open(browser, tmp_path)
    page.fill("#sigma", "25")
    page.wait_for_timeout(300)
    assert page.inner_text("#verdict").startswith("Rojo")
    assert [l["text"] for l in _lamps(page) if l["on"]] == ["Rojo"]
    page.fill("#sigma", "2")
    page.fill("#cal-mm", "4")                                              # la regla "mide" menos: la CRL queda bajo 15 mm
    page.wait_for_timeout(300)
    assert page.inner_text("#verdict").startswith("Se niega a dar una edad")
    assert [l["text"] for l in _lamps(page) if l["on"]] == ["Se niega"]
    assert "sin edad" in page.inner_text("#metrics")
    assert errors == []
    ctx.close()


def test_envelope_notes_and_table_exist_and_refuse_outside_the_source_range(browser, tmp_path):
    ctx, page, errors = _open(browser, tmp_path)
    assert page.locator("#chart svg").count() == 1
    page.fill("#ga-known", "100")
    page.wait_for_timeout(400)
    table = page.evaluate("document.getElementById('env-table').textContent")
    assert "fuera del rango de la fuente" in table
    assert "no predice" in page.inner_text("#envelope").lower()
    assert errors == []
    ctx.close()


def test_phone_width_has_no_horizontal_overflow(browser, tmp_path):
    ctx, page, errors = _open(browser, tmp_path, 390, 844)
    assert page.evaluate("document.documentElement.scrollWidth") <= 390
    assert page.locator("#chart svg").count() == 1
    assert errors == []
    ctx.close()
