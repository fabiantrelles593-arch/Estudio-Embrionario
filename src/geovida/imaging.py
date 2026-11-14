"""Simulación de adquisición: volumen parcial, anisotropía, PSF y ruido.

Pipeline (cada paso es una fuente de error medible por separado):

1. orientación aleatoria uniforme en SO(3) y desplazamiento subvoxel aleatorio;
2. fracción de ocupación por voxel (volumen parcial) mediante superes-
   muestreo ``n_sub``^3 del indicador analítico;
3. desenfoque gaussiano (PSF) con FWHM expresada en múltiplos de ``h_xy`` y
   aplicado en unidades físicas (por eso es más débil, en voxeles, en z);
4. ruido gaussiano aditivo con SNR = contraste / sigma (objeto = 1, fondo = 0).

Extensión v0.5 (H12), solo si se piden con parámetros nuevos (los perfiles antiguos no cambian ni
un bit ni consumen números aleatorios distintos):

* ``bg_level``: el fondo no es 0 sino ``bg_level`` (líquido amniótico débilmente ecogénico).
* ``atten``: atenuación a lo largo del eje z (dirección del haz): la imagen se multiplica por
  ``exp(-atten · z / z_max)``; ``atten`` es la pérdida total, en nepers, a lo largo del volumen.
* ``looks`` / ``grain_fwhm``: moteado completamente desarrollado, multiplicativo, de media 1 y
  contraste 1/sqrt(looks); ``grain_fwhm`` es el tamaño del grano en múltiplos de ``h_xy``
  (en unidades físicas, como la PSF). Es un modelo mínimo: no incluye compresión logarítmica,
  sombras acústicas ni reverberaciones.

El espaciado es (h_xy, h_xy, anisotropy * h_xy).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi
from scipy.spatial.transform import Rotation

from .phantoms import Phantom

_FWHM_TO_SIGMA = 1.0 / (2.0 * math.sqrt(2.0 * math.log(2.0)))

IMAGING_PROFILES: dict[str, dict] = {
    "ideal": {"psf_fwhm": 0.0, "snr": None},
    "realistic": {"psf_fwhm": 1.0, "snr": 10.0},
}
# v0.4: dominio desplazado (más desenfoque o más ruido que cualquier perfil usado
# para calibrar). No entran en H1-H8 ni en ninguna calibración: sirven para medir
# cuánto depende el certificado del simulador con el que se calibró.
SHIFTED_PROFILES: dict[str, dict] = {
    "blurry": {"psf_fwhm": 2.0, "snr": 10.0},
    "noisy": {"psf_fwhm": 1.0, "snr": 5.0},
    "mild_blur": {"psf_fwhm": 1.5, "snr": 10.0},
    "mild_noise": {"psf_fwhm": 1.0, "snr": 7.5},
}
# v0.5 (H12): ecografía 3D simulada. Los de calibración llevan moteado y atenuación moderados; los
# desplazados tienen más atenuación o un grano más grueso que cualquiera de ellos. Los valores son
# supuestos de diseño declarados en docs/PREREGISTRO_H12.md, no medidas de un ecógrafo real.
ULTRASOUND_PROFILES: dict[str, dict] = {
    "us_compound": {"psf_fwhm": 1.5, "snr": 20.0, "looks": 8, "grain_fwhm": 1.5,
                    "atten": 0.3, "bg_level": 0.15},
    "us_raw": {"psf_fwhm": 1.5, "snr": 20.0, "looks": 3, "grain_fwhm": 1.5,
               "atten": 0.3, "bg_level": 0.15},
}
ULTRASOUND_SHIFTED_PROFILES: dict[str, dict] = {
    "us_atten": {"psf_fwhm": 1.5, "snr": 20.0, "looks": 8, "grain_fwhm": 1.5,
                 "atten": 1.0, "bg_level": 0.15},
    "us_coarse": {"psf_fwhm": 2.5, "snr": 20.0, "looks": 8, "grain_fwhm": 3.0,
                  "atten": 0.3, "bg_level": 0.15},
}


@dataclass(frozen=True)
class ImagingSpec:
    h_xy: float
    anisotropy: float = 1.0
    psf_fwhm: float = 0.0          # en múltiplos de h_xy
    snr: float | None = None       # None = sin ruido
    n_sub: int = 3
    looks: int = 0                 # 0 = sin moteado; >0 = promedio de ``looks`` campos de moteado
    grain_fwhm: float = 0.0        # tamaño del grano de moteado, en múltiplos de h_xy
    atten: float = 0.0             # pérdida total (nepers) a lo largo de z
    bg_level: float = 0.0          # nivel del fondo (objeto = 1)

    def __post_init__(self):
        if not self.h_xy > 0:
            raise ValueError("h_xy debe ser > 0")
        if self.anisotropy < 1.0:
            raise ValueError("anisotropy = hz/hxy debe ser >= 1")
        if self.psf_fwhm < 0 or self.n_sub < 1:
            raise ValueError("psf_fwhm >= 0 y n_sub >= 1")
        if self.snr is not None and not self.snr > 0:
            raise ValueError("snr debe ser > 0 o None")
        if self.looks < 0:
            raise ValueError("looks debe ser >= 0")
        if self.looks > 0 and not self.grain_fwhm > 0:
            raise ValueError("con looks > 0 hace falta grain_fwhm > 0")
        if self.atten < 0:
            raise ValueError("atten debe ser >= 0")
        if not 0.0 <= self.bg_level < 1.0:
            raise ValueError("bg_level debe estar en [0, 1)")

    @property
    def spacing(self) -> tuple[float, float, float]:
        return (self.h_xy, self.h_xy, self.anisotropy * self.h_xy)

    @property
    def psf_sigma_phys(self) -> float:
        return self.psf_fwhm * self.h_xy * _FWHM_TO_SIGMA

    @property
    def grain_sigma_phys(self) -> float:
        return self.grain_fwhm * self.h_xy * _FWHM_TO_SIGMA


@dataclass
class Rendered:
    image: np.ndarray
    coverage: np.ndarray
    spacing: tuple[float, float, float]
    rotation: np.ndarray


def spec_for_t_over_h(t_over_h: float, anisotropy: float, profile: str,
                      t: float = 1.0) -> ImagingSpec:
    """Especificación con ``t / h_xy = t_over_h`` y el perfil de imagen dado."""
    profiles = {**IMAGING_PROFILES, **SHIFTED_PROFILES,
                **ULTRASOUND_PROFILES, **ULTRASOUND_SHIFTED_PROFILES}
    if profile not in profiles:
        raise ValueError(f"perfil desconocido: {profile!r}")
    return ImagingSpec(h_xy=t / t_over_h, anisotropy=anisotropy, **profiles[profile])


def speckle_field(shape: tuple[int, int, int], looks: int, sigma_vox,
                  rng: np.random.Generator) -> np.ndarray:
    """Campo de moteado multiplicativo 3D de media 1 y contraste ~1/sqrt(looks).

    Cada "look" es la intensidad |z|² de un campo gaussiano complejo suavizado con ``sigma_vox``
    (moteado completamente desarrollado: intensidad exponencial, contraste 1). Se promedian
    ``looks`` campos independientes.
    """
    acc = np.zeros(shape, dtype=np.float64)
    for _ in range(looks):
        re = ndi.gaussian_filter(rng.standard_normal(shape), sigma=sigma_vox)
        im = ndi.gaussian_filter(rng.standard_normal(shape), sigma=sigma_vox)
        inten = re * re + im * im
        acc += inten / inten.mean()
    return acc / looks


def render(phantom: Phantom, spec: ImagingSpec, rng: np.random.Generator) -> Rendered:
    sp = np.array(spec.spacing)
    rot = Rotation.random(random_state=rng).as_matrix()
    offset = rng.uniform(-0.5, 0.5, size=3) * sp

    # Semianchura de la caja envolvente rotada + margen para vecindad y PSF.
    half = np.abs(rot) @ np.array(phantom.half_extent)
    half = half + 2.0 * sp + 3.0 * spec.psf_sigma_phys
    n = 2 * np.ceil(half / sp).astype(int)

    axes = [(np.arange(k) - (k - 1) / 2.0) * h + o for k, h, o in zip(n, sp, offset)]
    base = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1)

    sub = (np.arange(spec.n_sub) + 0.5) / spec.n_sub - 0.5
    acc = np.zeros(tuple(n), dtype=np.float32)
    for dx in sub:
        for dy in sub:
            for dz in sub:
                pts = base + np.array([dx, dy, dz]) * sp
                acc += phantom.contains(pts @ rot)  # lab -> marco canónico
    coverage = acc / float(spec.n_sub**3)

    image = coverage.copy()
    if spec.psf_fwhm > 0:
        sigma_vox = spec.psf_sigma_phys / sp
        image = ndi.gaussian_filter(image, sigma=sigma_vox, mode="constant", cval=0.0)
    if spec.bg_level > 0:
        image = spec.bg_level + (1.0 - spec.bg_level) * image
    if spec.atten > 0:
        zfrac = np.arange(image.shape[2]) / max(image.shape[2] - 1, 1)
        image = image * np.exp(-spec.atten * zfrac).astype(np.float32)[None, None, :]
    if spec.looks > 0:
        image = image * speckle_field(image.shape, spec.looks, spec.grain_sigma_phys / sp, rng)
    if spec.snr is not None:
        image = image + rng.normal(0.0, 1.0 / spec.snr, size=image.shape).astype(np.float32)

    return Rendered(image=image.astype(np.float32), coverage=coverage,
                    spacing=spec.spacing, rotation=rot)
