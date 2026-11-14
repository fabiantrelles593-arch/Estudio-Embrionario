"""Fantomas geométricos con verdad analítica (volumen, área, Betti, grosores).

Cada fantoma se parametriza por ``t``: el menor grosor sólido (diámetro de la
bola, grosor de pared de la cáscara/tubo, diámetro del tubo del toro, eje
menor del elipsoide). El resto de dimensiones son proporciones fijas de ``t``
para que la comparación entre clases sea justa.

``t_void`` es el menor rasgo de *vacío* que debe resolverse para conservar la
topología (diámetro de la cavidad, del hueco del toro o de la luz del tubo).
``t_min = min(t_solid, t_void)``. Las clases ``*_tight`` existen para separar
las dos hipótesis de predictor (t_solid/h frente a t_min/h): en ellas el vacío
es más estrecho que el sólido.

Convención de la verdad topológica: números de Betti del sólido en R^3
(bola (1,0,0); cáscara (1,0,1); toro sólido y tubo hueco (1,1,0)).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.special import ellipeinc, ellipkinc

PHANTOM_NAMES = (
    "ball", "ellipsoid", "shell", "torus", "tube", "shell_tight", "torus_tight",
)
# v0.2: formas nuevas para la confirmación H3 (el conjunto preregistrado de H1
# no cambia). Todas son sólidos simples (Betti (1,0,0)) con proporciones fijas.
EXTRA_NAMES = ("capsule", "cylinder", "oblate")
# v0.4: formas no convexas reservadas como «nunca vistas» para el certificado.
# ``dumbbell``: dos bolas unidas por un cuello delgado (t = diámetro del cuello).
# ``cup``: semicáscara esférica abierta de pared t (rasgo laminar).
NEW_NAMES = ("dumbbell", "cup")


@dataclass(frozen=True)
class Truth:
    volume: float
    surface_area: float
    betti: tuple[int, int, int]
    chi: int
    t_solid: float
    t_void: float  # math.inf si el fantoma no tiene rasgos de vacío

    @property
    def t_min(self) -> float:
        return min(self.t_solid, self.t_void)


@dataclass(frozen=True)
class Phantom:
    name: str
    t: float
    truth: Truth
    half_extent: tuple[float, float, float]
    _inside: Callable[[np.ndarray], np.ndarray]

    def contains(self, pts: np.ndarray) -> np.ndarray:
        """Indicador del sólido en el marco canónico; ``pts`` tiene forma (..., 3)."""
        return self._inside(np.asarray(pts, dtype=float))

    @property
    def bounding_radius(self) -> float:
        return float(np.linalg.norm(self.half_extent))


def _ellipsoid_area(a: float, b: float, c: float) -> float:
    """Área de un elipsoide (forma de Legendre), con a >= b >= c."""
    a, b, c = sorted((a, b, c), reverse=True)
    if math.isclose(a, c):
        return 4 * math.pi * a * a
    phi = math.acos(c / a)
    m = (a * a * (b * b - c * c)) / (b * b * (a * a - c * c))
    s, co = math.sin(phi), math.cos(phi)
    return 2 * math.pi * c * c + (2 * math.pi * a * b / s) * (
        ellipeinc(phi, m) * s * s + ellipkinc(phi, m) * co * co
    )


def _ball(t: float) -> Phantom:
    r = t / 2
    truth = Truth(4 / 3 * math.pi * r**3, 4 * math.pi * r**2, (1, 0, 0), 1, t, math.inf)
    return Phantom("ball", t, truth, (r, r, r),
                   lambda p: (p**2).sum(-1) <= r * r)


def _ellipsoid(t: float) -> Phantom:
    c = t / 2
    b, a = 1.5 * c, 2.0 * c
    truth = Truth(4 / 3 * math.pi * a * b * c, _ellipsoid_area(a, b, c),
                  (1, 0, 0), 1, t, math.inf)
    return Phantom("ellipsoid", t, truth, (a, b, c),
                   lambda p: (p[..., 0] / a) ** 2 + (p[..., 1] / b) ** 2
                   + (p[..., 2] / c) ** 2 <= 1.0)


def _shell(t: float, void_ratio: float, name: str) -> Phantom:
    ri = void_ratio * t / 2
    ro = ri + t
    truth = Truth(4 / 3 * math.pi * (ro**3 - ri**3),
                  4 * math.pi * (ro**2 + ri**2), (1, 0, 1), 2, t, void_ratio * t)

    def inside(p):
        d2 = (p**2).sum(-1)
        return (d2 <= ro * ro) & (d2 >= ri * ri)

    return Phantom(name, t, truth, (ro, ro, ro), inside)


def _torus(t: float, void_ratio: float, name: str) -> Phantom:
    r = t / 2
    big_r = r + void_ratio * t / 2  # hueco = 2(R - r) = void_ratio * t
    truth = Truth(2 * math.pi**2 * big_r * r**2, 4 * math.pi**2 * big_r * r,
                  (1, 1, 0), 0, t, void_ratio * t)

    def inside(p):
        rho = np.hypot(p[..., 0], p[..., 1])
        return (rho - big_r) ** 2 + p[..., 2] ** 2 <= r * r

    return Phantom(name, t, truth, (big_r + r, big_r + r, r), inside)


def _tube(t: float, void_ratio: float = 2.0) -> Phantom:
    ri = void_ratio * t / 2
    ro = ri + t
    length = 5.0 * t
    truth = Truth(math.pi * (ro**2 - ri**2) * length,
                  2 * math.pi * (ro + ri) * length + 2 * math.pi * (ro**2 - ri**2),
                  (1, 1, 0), 0, t, void_ratio * t)

    def inside(p):
        rho2 = p[..., 0] ** 2 + p[..., 1] ** 2
        return (rho2 <= ro * ro) & (rho2 >= ri * ri) & (np.abs(p[..., 2]) <= length / 2)

    return Phantom("tube", t, truth, (ro, ro, length / 2), inside)


def _capsule(t: float) -> Phantom:
    r = t / 2
    lc = 3.0 * t  # tramo cilíndrico; longitud total 4 t
    truth = Truth(math.pi * r * r * lc + 4 / 3 * math.pi * r**3,
                  2 * math.pi * r * lc + 4 * math.pi * r * r, (1, 0, 0), 1, t, math.inf)

    def inside(p):
        z = p[..., 2]
        rho2 = p[..., 0] ** 2 + p[..., 1] ** 2
        body = (rho2 <= r * r) & (np.abs(z) <= lc / 2)
        cap = rho2 + (np.abs(z) - lc / 2) ** 2 <= r * r
        return body | cap

    return Phantom("capsule", t, truth, (r, r, lc / 2 + r), inside)


def _cylinder(t: float) -> Phantom:
    r = t / 2
    h = 3.0 * t
    truth = Truth(math.pi * r * r * h, 2 * math.pi * r * h + 2 * math.pi * r * r,
                  (1, 0, 0), 1, t, math.inf)

    def inside(p):
        return (p[..., 0] ** 2 + p[..., 1] ** 2 <= r * r) & (np.abs(p[..., 2]) <= h / 2)

    return Phantom("cylinder", t, truth, (r, r, h / 2), inside)


def _oblate(t: float) -> Phantom:
    c = t / 2
    a = 2.5 * t
    truth = Truth(4 / 3 * math.pi * a * a * c, _ellipsoid_area(a, a, c),
                  (1, 0, 0), 1, t, math.inf)
    return Phantom("oblate", t, truth, (a, a, c),
                   lambda p: (p[..., 0] ** 2 + p[..., 1] ** 2) / (a * a)
                   + (p[..., 2] / c) ** 2 <= 1.0)


def _dumbbell(t: float) -> Phantom:
    """Dos bolas de radio 2t unidas por un cuello cilíndrico de diámetro t.

    El tramo libre del cuello mide 1.5t. El cilindro llega hasta los centros de
    las bolas (su parte interior ya está contenida en ellas), así que el volumen
    es 2 V_bola + pi r^2 L_libre y el área es la de las dos esferas menos un
    casquete cada una, más la pared lateral del cuello libre.
    """
    r, big_r, l_out = t / 2, 2.0 * t, 1.5 * t
    root = math.sqrt(big_r**2 - r**2)
    d = root + l_out / 2                      # distancia del centro de cada bola al origen
    cap_height = big_r - root
    volume = 2 * 4 / 3 * math.pi * big_r**3 + math.pi * r * r * l_out
    area = (2 * (4 * math.pi * big_r**2 - 2 * math.pi * big_r * cap_height)
            + 2 * math.pi * r * l_out)
    truth = Truth(volume, area, (1, 0, 0), 1, t, math.inf)

    def inside(p):
        rho2 = p[..., 0] ** 2 + p[..., 1] ** 2
        z = p[..., 2]
        ball_up = rho2 + (z - d) ** 2 <= big_r**2
        ball_dn = rho2 + (z + d) ** 2 <= big_r**2
        neck = (rho2 <= r * r) & (np.abs(z) <= d)
        return ball_up | ball_dn | neck

    return Phantom("dumbbell", t, truth, (big_r, big_r, d + big_r), inside)


def _cup(t: float) -> Phantom:
    """Semicáscara esférica (z >= 0): radio interior 1.5t, exterior 2.5t, borde plano."""
    ri, ro = 1.5 * t, 2.5 * t
    truth = Truth(2 / 3 * math.pi * (ro**3 - ri**3),
                  2 * math.pi * (ro**2 + ri**2) + math.pi * (ro**2 - ri**2),
                  (1, 0, 0), 1, t, math.inf)

    def inside(p):
        d2 = (p**2).sum(-1)
        return (d2 <= ro * ro) & (d2 >= ri * ri) & (p[..., 2] >= 0.0)

    return Phantom("cup", t, truth, (ro, ro, ro), inside)


def make_phantom(name: str, t: float) -> Phantom:
    """Construye el fantoma ``name`` con menor grosor sólido ``t`` (>0)."""
    if not t > 0:
        raise ValueError("t debe ser > 0")
    if name == "ball":
        return _ball(t)
    if name == "ellipsoid":
        return _ellipsoid(t)
    if name == "shell":
        return _shell(t, 4.0, "shell")
    if name == "shell_tight":
        return _shell(t, 0.5, "shell_tight")
    if name == "torus":
        return _torus(t, 1.5, "torus")
    if name == "torus_tight":
        return _torus(t, 0.5, "torus_tight")
    if name == "tube":
        return _tube(t)
    if name == "capsule":
        return _capsule(t)
    if name == "cylinder":
        return _cylinder(t)
    if name == "oblate":
        return _oblate(t)
    if name == "dumbbell":
        return _dumbbell(t)
    if name == "cup":
        return _cup(t)
    raise ValueError(f"fantoma desconocido: {name!r}; "
                     f"opciones: {PHANTOM_NAMES + EXTRA_NAMES + NEW_NAMES}")
