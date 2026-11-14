"""Linealización de un mapa de color con la barra de la propia captura (solo investigación y educación).

Una ecografía impresa con un tinte (naranja, sepia) no es una escala de grises: el color es una función conocida de la intensidad, y
la barra de color de la captura la muestra. Aquí se prueba, con un mapa de color **inventado** y una degradación tipo foto, que
(1) la intensidad se recupera con la barra, (2) la barra recupera mejor que la luminancia cuando el mapa no es lineal en luminancia,
(3) los colores que no pertenecen al mapa (texto, calibradores) se señalan en vez de recibir una intensidad inventada.
Nada de esto usa ninguna imagen real.
"""
import numpy as np
import pytest
from scipy import ndimage as ndi

from geovida import colorbar


def _cm(p):
    """Mapa de color sintético: del rojo oscuro al durazno, no lineal en luminancia. p en [0, 1]."""
    p = np.asarray(p, float)
    r = np.clip(1.8 * p, 0, 1) ** 0.9
    g = 0.85 * p ** 1.7
    b = 0.7 * p ** 2.4
    return np.stack([r, g, b], axis=-1)


def _phantom(rng, size=(60, 80), noise=0.0):
    p = np.full(size, 0.18)
    yy, xx = np.mgrid[:size[0], :size[1]]
    p[((yy - 30) / 14) ** 2 + ((xx - 40) / 22) ** 2 <= 1] = 0.82
    p = ndi.gaussian_filter(p, 1.2)
    return np.clip(p + noise * rng.standard_normal(size), 0, 1)


def _bar(h=60, w=7, top_high=True, rng=None, noise=0.0):
    p = np.linspace(1.0, 0.0, h) if top_high else np.linspace(0.0, 1.0, h)
    bar = np.repeat(_cm(p)[:, None, :], w, axis=1)
    if rng is not None and noise:
        bar = np.clip(bar + noise * rng.standard_normal(bar.shape), 0, 1)
    return bar


def _canvas(img_rgb, bar, gap=4):
    """Imagen a la derecha y barra a la izquierda, en un solo cuadro; devuelve (cuadro, caja de la barra)."""
    h = max(img_rgb.shape[0], bar.shape[0]) + 4
    cv = np.zeros((h, bar.shape[1] + gap + img_rgb.shape[1] + 4, 3))
    cv[2:2 + bar.shape[0], 2:2 + bar.shape[1]] = bar
    cv[2:2 + img_rgb.shape[0], 2 + bar.shape[1] + gap:2 + bar.shape[1] + gap + img_rgb.shape[1]] = img_rgb
    box = (2, 2, 2 + bar.shape[1], 2 + bar.shape[0])
    return cv, box


def test_the_lut_runs_from_dark_to_bright_and_is_monotone_for_a_clean_bar():
    lut = colorbar.lut_from_bar(_bar(), (0, 0, 7, 60))
    lum = lut.colors @ np.array([0.299, 0.587, 0.114])
    assert lum[0] < lum[-1] and lut.lum_monotone_fraction > 0.99 and not lut.warnings


def test_recovers_the_intensity_of_a_colorized_phantom():
    rng = np.random.default_rng(1)
    p = _phantom(rng)
    cv, box = _canvas(_cm(p), _bar())
    lin = colorbar.linearize(cv, colorbar.lut_from_bar(cv, box))
    inside = lin["linear"][2:62, 13:93]                      # la zona de la imagen (a la derecha de la barra)
    assert np.median(np.abs(inside - p)) < 0.02
    assert np.percentile(np.abs(inside - p), 95) < 0.06


def test_survives_a_photo_like_degradation_of_the_image_but_not_of_the_bar():
    rng = np.random.default_rng(2)
    p = _phantom(rng)
    img = _cm(p)
    img = ndi.gaussian_filter(img, sigma=(1.0, 1.0, 0.0)) * 0.93 + 0.012       # desenfoque, ganancia y pedestal
    img = np.clip(img + 0.02 * rng.standard_normal(img.shape), 0, 1)
    cv, box = _canvas(img, _bar(rng=rng, noise=0.015))
    lin = colorbar.linearize(cv, colorbar.lut_from_bar(cv, box))
    err = np.abs(lin["linear"][2:62, 13:93] - p)
    assert np.median(err) < 0.05


def test_the_bar_beats_plain_luminance_when_the_colormap_is_not_linear_in_luminance():
    rng = np.random.default_rng(3)
    p = _phantom(rng)
    cv, box = _canvas(_cm(p), _bar())
    lin = colorbar.linearize(cv, colorbar.lut_from_bar(cv, box))["linear"][2:62, 13:93]
    lum = cv @ np.array([0.299, 0.587, 0.114])
    lum_all = _cm(np.linspace(0, 1, 256)) @ np.array([0.299, 0.587, 0.114])
    lum = ((lum - lum_all.min()) / (lum_all.max() - lum_all.min()))[2:62, 13:93]
    assert np.median(np.abs(lin - p)) < 0.5 * np.median(np.abs(lum - p))


def test_a_flipped_bar_gives_the_same_linearization():
    rng = np.random.default_rng(4)
    cv1, b1 = _canvas(_cm(_phantom(rng)), _bar(top_high=True))
    cv2, b2 = _canvas(_cm(_phantom(np.random.default_rng(4))), _bar(top_high=False))
    l1 = colorbar.linearize(cv1, colorbar.lut_from_bar(cv1, b1))["linear"][2:62, 13:93]      # solo la imagen: la barra
    l2 = colorbar.linearize(cv2, colorbar.lut_from_bar(cv2, b2))["linear"][2:62, 13:93]      # misma está invertida
    assert np.max(np.abs(l1 - l2)) < 0.02


def test_colors_that_are_not_in_the_colormap_are_flagged_not_given_an_intensity():
    rng = np.random.default_rng(5)
    img = _cm(_phantom(rng))
    img[5:15, 5:15] = (0.0, 1.0, 0.0)                         # un recuadro verde (texto, calibrador)
    cv, box = _canvas(img, _bar())
    lin = colorbar.linearize(cv, colorbar.lut_from_bar(cv, box))
    patch = lin["off_lut"][2 + 5:2 + 15, 13 + 5:13 + 15]
    assert patch.all()
    assert lin["off_lut"][2 + 25:2 + 35, 13 + 30:13 + 50].mean() < 0.02          # el interior del objeto, no
    assert 0.0 < lin["off_lut_fraction"] < 0.1


def test_a_bar_whose_luminance_is_not_a_ramp_raises_a_warning():
    h = 60
    p = np.concatenate([np.linspace(0, 1, h // 2), np.linspace(1, 0, h // 2)])      # sube y baja
    bar = np.repeat(_cm(p)[:, None, :], 7, axis=1)
    lut = colorbar.lut_from_bar(bar, (0, 0, 7, h))
    assert lut.lum_monotone_fraction < 0.9
    assert any("monótona" in w for w in lut.warnings)


def test_accepts_8_bit_images():
    rng = np.random.default_rng(6)
    cv, box = _canvas(_cm(_phantom(rng)), _bar())
    u8 = np.round(cv * 255).astype(np.uint8)
    a = colorbar.linearize(u8, colorbar.lut_from_bar(u8, box))["linear"]
    b = colorbar.linearize(cv, colorbar.lut_from_bar(cv, box))["linear"]
    assert np.max(np.abs(a - b)) < 0.02


def test_bad_boxes_and_bad_images_raise():
    cv = np.zeros((40, 40, 3))
    with pytest.raises(ValueError):
        colorbar.lut_from_bar(cv, (0, 0, 7, 100))             # fuera de la imagen
    with pytest.raises(ValueError):
        colorbar.lut_from_bar(cv, (0, 0, 7, 5))               # muy corta para ser una barra
    with pytest.raises(ValueError):
        colorbar.lut_from_bar(cv, (0, 0, 2, 30))              # muy angosta
    with pytest.raises(ValueError):
        colorbar.lut_from_bar(np.zeros((40, 40)), (0, 0, 7, 30))      # no es RGB
    with pytest.raises(ValueError):
        colorbar.lut_from_bar(cv, (5, 5, 3, 30))              # caja invertida


def test_output_is_in_unit_range_and_has_the_image_shape():
    rng = np.random.default_rng(7)
    cv, box = _canvas(_cm(_phantom(rng)), _bar())
    lin = colorbar.linearize(cv, colorbar.lut_from_bar(cv, box))
    assert lin["linear"].shape == cv.shape[:2] and lin["off_lut"].shape == cv.shape[:2]
    assert lin["linear"].min() >= 0.0 and lin["linear"].max() <= 1.0
