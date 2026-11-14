"""Topología digital 3D con adyacencia explícita.

Los números de Betti de una imagen binaria NO son únicos: dependen del par de
adyacencias (primer plano, fondo). Aquí solo se admiten los dos pares que dan
una topología digital bien definida:

* conectividad 6  para el primer plano  -> 26 para el fondo
* conectividad 26 para el primer plano  -> 6  para el fondo

Relación usada: chi = b0 - b1 + b2, de modo que b1 = b0 + b2 - chi.
b0 y b2 se cuentan por etiquetado de componentes; chi lo calcula
``skimage.measure.euler_number`` (verificado con casos construidos a mano en
``tests/test_topology.py``).
"""
from __future__ import annotations

from typing import NamedTuple

import numpy as np
from scipy import ndimage as ndi
from skimage.measure import euler_number

_STRUCT = {
    6: ndi.generate_binary_structure(3, 1),
    26: ndi.generate_binary_structure(3, 3),
}
_COMPLEMENT = {6: 26, 26: 6}
_SKIMAGE_CONN = {6: 1, 26: 3}


class Betti(NamedTuple):
    b0: int
    b1: int
    b2: int
    chi: int

    def as_tuple(self) -> tuple[int, int, int]:
        return (self.b0, self.b1, self.b2)


def betti_numbers(mask: np.ndarray, connectivity: int = 26) -> Betti:
    """Números de Betti (b0, b1, b2) y característica de Euler de una máscara 3D.

    ``connectivity`` es la del primer plano (6 o 26); el fondo usa la
    complementaria. La máscara se rodea de fondo para que los objetos que
    tocan el borde queden cerrados.
    """
    if connectivity not in _STRUCT:
        raise ValueError("connectivity debe ser 6 o 26")
    mask = np.asarray(mask)
    if mask.ndim != 3:
        raise ValueError("se espera una máscara 3D")

    fg = np.pad(mask.astype(bool), 1, mode="constant", constant_values=False)
    if not fg.any():
        return Betti(0, 0, 0, 0)

    _, b0 = ndi.label(fg, structure=_STRUCT[connectivity])

    bg_labels, n_bg = ndi.label(~fg, structure=_STRUCT[_COMPLEMENT[connectivity]])
    # El fondo conectado con el borde de la imagen rellenada es el exterior;
    # el resto son cavidades. (El borde relleno es todo fondo y conexo.)
    b2 = n_bg - 1

    chi = int(euler_number(fg, connectivity=_SKIMAGE_CONN[connectivity]))
    b1 = int(b0 + b2 - chi)
    return Betti(int(b0), b1, int(b2), chi)
