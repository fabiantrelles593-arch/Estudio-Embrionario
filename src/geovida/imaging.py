"""Simulación de adquisición: volumen parcial, anisotropía, PSF y ruido.

Pipeline (cada paso es una fuente de error medible por separado):

1. orientación aleatoria uniforme en SO(3) y desplazamiento subvoxel aleatorio;
2. fracción de ocupación por voxel (volumen parcial) mediante superes-
   muestreo ``n_sub``^3 del indicador analítico;
3. desenfoque gaussiano (PSF) con FWHM expresada en múltiplos de ``h_xy`` y
   aplicado en unidades físicas (por eso es más débil, en voxeles, en z);
4. ruido gaussiano aditivo con SNR = contraste / sigma (objeto = 1, fondo = 0).

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


@dataclass(frozen=True)
class ImagingSpec:
    h_xy: float
    anisotropy: float = 1.0
    psf_fwhm: float = 0.0          # en múltiplos de h_xy
    snr: float | None = None       # None = sin ruido
    n_sub: int = 3

    def __post_init__(self):
        if not self.h_xy > 0:
            raise ValueError("h_xy debe ser > 0")
        if self.anisotropy < 1.0:
            raise ValueError("anisotropy = hz/hxy debe ser >= 1")
        if self.psf_fwhm < 0 or self.n_sub < 1:
            raise ValueError("psf_fwhm >= 0 y n_sub >= 1")
        if self.snr is not None and not self.snr > 0:
            raise ValueError("snr debe ser > 0 o None")

    @property
    def spacing(self) -> tuple[float, float, float]:
        return (self.h_xy, self.h_xy, self.anisotropy * self.h_xy)

    @property
    def psf_sigma_phys(self) -> float:
        return self.psf_fwhm * self.h_xy * _FWHM_TO_SIGMA


@dataclass
class Rendered:
    image: np.ndarray
    coverage: np.ndarray
    spacing: tuple[float, float, float]
    rotation: np.ndarray


def spec_for_t_over_h(t_over_h: float, anisotropy: float, profile: str,
                      t: float = 1.0) -> ImagingSpec:
    """Especificación con ``t / h_xy = t_over_h`` y el perfil de imagen dado."""
    profiles = {**IMAGING_PROFILES, **SHIFTED_PROFILES}
    if profile not in profiles:
        raise ValueError(f"perfil desconocido: {profile!r}")
    return ImagingSpec(h_xy=t / t_over_h, anisotropy=anisotropy, **profiles[profile])


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
    if spec.snr is not None:
        image = image + rng.normal(0.0, 1.0 / spec.snr, size=image.shape).astype(np.float32)

    return Rendered(image=image.astype(np.float32), coverage=coverage,
                    spacing=spec.spacing, rotation=rot)
