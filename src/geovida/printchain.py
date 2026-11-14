"""Cadena pantalla → impresión → foto → JPEG (H15). Solo simulación.

Una ecografía real que llega como foto de una impresión no es la imagen que el simulador calibró: el equipo comprime
el rango dinámico (logaritmo), hay un gradiente de ganancia con la profundidad, la cámara desenfoca y añade ruido, y el
JPEG introduce bloques. Esta cadena transforma una imagen simulada con parámetros muestreados de rangos **fijados de
antemano** (``RANGES``; ``docs/PREREGISTRO_H15.md``) para probar si el certificado resiste.

No pretende ser fiel a ningún equipo ni cámara: es una prueba de esfuerzo con efectos del tipo correcto.
La imagen se sube a ``upsample``× antes del ruido y el JPEG, y se vuelve a bajar con promedio de área, como haría
un remuestreo de foto grande a escala de trabajo (lo que hace ``geovida.real2d``).
"""
from __future__ import annotations

import cv2
import numpy as np
from scipy import ndimage as ndi

RANGES = {
    "compression_a": (3.0, 60.0),     # log-uniforme; y = log1p(a·x)/log1p(a)
    "gain_slope": (0.0, 0.25),        # magnitud; signo al azar; ganancia 1 + s·(−1…1) a lo largo de las filas
    "blur_sigma_px": (0.3, 1.0),      # px de la escala de trabajo
    "noise_sd": (0.01, 0.04),         # sobre el rango [0, 1], antes de bajar la escala
    "jpeg_quality": (50, 90),
}
UPSAMPLE = 3

# H16: familia B, de otro tipo y no un subconjunto de A. La curva de tono es una gamma que pasa por la luminancia de un
# mapa de color naranja INVENTADO (no es el de ningún equipo) y puede oscurecer (γ > 1), cosa que A nunca hace; además más
# desenfoque, más ruido, JPEG más duro y más gradiente de ganancia que A. Rangos fijados en ``docs/PREREGISTRO_H16.md``.
RANGES_B = {
    "gamma": (0.3, 2.5),              # log-uniforme (≈ 1/3.3 a 2.5: compresión y oscurecimiento de pantallas e impresoras); y = luminancia(mapa_naranja(x^γ)) normalizada
    "gain_slope": (0.0, 0.40),
    "blur_sigma_px": (0.8, 1.6),
    "noise_sd": (0.03, 0.08),
    "jpeg_quality": (25, 60),
}
_TONE_B_WHITE = 0.299 * 1.0 + 0.587 * 0.85 + 0.114 * 0.7


def tone_b(x: np.ndarray, gamma: float) -> np.ndarray:
    """Curva de tono de la familia B: gamma y luminancia de un mapa de color naranja inventado, normalizada a [0, 1]."""
    p = np.clip(np.asarray(x, dtype=float), 0.0, 1.0) ** float(gamma)
    r = np.clip(1.8 * p, 0.0, 1.0) ** 0.9
    g = 0.85 * p ** 1.7
    b = 0.7 * p ** 2.4
    return (0.299 * r + 0.587 * g + 0.114 * b) / _TONE_B_WHITE


def sample_chain(rng: np.random.Generator) -> dict:
    lo, hi = RANGES["compression_a"]
    sign = 1.0 if rng.random() < 0.5 else -1.0
    return {
        "compression_a": float(np.exp(rng.uniform(np.log(lo), np.log(hi)))),
        "gain_slope": float(sign * rng.uniform(*RANGES["gain_slope"])),
        "blur_sigma_px": float(rng.uniform(*RANGES["blur_sigma_px"])),
        "noise_sd": float(rng.uniform(*RANGES["noise_sd"])),
        "jpeg_quality": int(rng.integers(RANGES["jpeg_quality"][0], RANGES["jpeg_quality"][1] + 1)),
        "noise_seed": int(rng.integers(0, 2**31 - 1)),
        "upsample": UPSAMPLE,
    }


def sample_chain_b(rng: np.random.Generator) -> dict:
    """Cadena de la familia B (H16): otra familia, no un subconjunto de A."""
    lo, hi = RANGES_B["gamma"]
    sign = 1.0 if rng.random() < 0.5 else -1.0
    return {
        "family": "B",
        "gamma": float(np.exp(rng.uniform(np.log(lo), np.log(hi)))),
        "gain_slope": float(sign * rng.uniform(*RANGES_B["gain_slope"])),
        "blur_sigma_px": float(rng.uniform(*RANGES_B["blur_sigma_px"])),
        "noise_sd": float(rng.uniform(*RANGES_B["noise_sd"])),
        "jpeg_quality": int(rng.integers(RANGES_B["jpeg_quality"][0], RANGES_B["jpeg_quality"][1] + 1)),
        "noise_seed": int(rng.integers(0, 2**31 - 1)),
        "upsample": UPSAMPLE,
    }


def apply_chain(img: np.ndarray, chain: dict) -> np.ndarray:
    """Devuelve la imagen transformada, en [0, 1], con la misma forma que ``img``. Determinista dado ``chain``.

    ``chain["family"]`` = ``"B"`` usa la curva de tono de la familia B; sin esa clave (o ``"A"``), la compresión logarítmica de H15."""
    h, w = img.shape
    lo, hi = np.percentile(img, [1.0, 99.5])
    if not hi > lo:
        hi = lo + 1e-9
    x = np.clip((img - lo) / (hi - lo), 0.0, 1.0)
    if chain.get("family", "A") == "B":
        x = tone_b(x, float(chain["gamma"]))
    else:
        a = float(chain["compression_a"])
        x = np.log1p(a * x) / np.log1p(a)
    up = int(chain.get("upsample", 1))
    if up > 1:
        x = cv2.resize(x, dsize=None, fx=up, fy=up, interpolation=cv2.INTER_LINEAR)
    ramp = 1.0 + float(chain["gain_slope"]) * np.linspace(-1.0, 1.0, x.shape[0])[:, None]
    x = np.clip(x * ramp, 0.0, 1.0)
    sigma = float(chain["blur_sigma_px"]) * up
    if sigma > 0:
        x = ndi.gaussian_filter(x, sigma)
    x = x + float(chain["noise_sd"]) * np.random.default_rng(int(chain["noise_seed"])).standard_normal(x.shape)
    u8 = (np.clip(x, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
    ok, buf = cv2.imencode(".jpg", u8, [cv2.IMWRITE_JPEG_QUALITY, int(chain["jpeg_quality"])])
    if not ok:
        raise RuntimeError("no se pudo codificar el JPEG")
    x = cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE).astype(np.float64) / 255.0
    if up > 1:
        x = cv2.resize(x, dsize=(w, h), interpolation=cv2.INTER_AREA)
    return x
