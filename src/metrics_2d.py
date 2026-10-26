from __future__ import annotations
from dataclasses import dataclass, asdict
import math
from numbers import Real
import numpy as np
from skimage import measure

@dataclass
class Metrics2D:
    pixel_area: float
    area: float
    perimeter: float
    major_axis: float
    minor_axis: float
    aspect_ratio: float
    circularity: float
    solidity: float
    extent: float
    eccentricity: float
    orientation_rad: float
    beta0: int
    beta1: int
    euler_characteristic: int
    primary_component_pixel_area: float
    component_policy: str


def measure_mask(mask: np.ndarray, pixel_size: float = 1.0) -> Metrics2D:
    """Mide una máscara 2D.

    `area` y `perimeter` suman todas las componentes; descriptores de ejes,
    solidity, extent y eccentricity describen la componente de mayor área.
    `pixel_size` es la longitud de un píxel en las unidades elegidas. Su valor
    predeterminado es 1.0, lo que conserva las medidas en unidades de píxel.
    """
    if not isinstance(pixel_size, Real) or isinstance(pixel_size, bool) or not math.isfinite(float(pixel_size)) or pixel_size <= 0:
        raise ValueError('pixel_size debe ser un número finito y positivo.')
    binary = np.asarray(mask, dtype=bool)
    if binary.ndim != 2 or binary.size == 0 or not binary.any():
        raise ValueError('La máscara debe ser 2D, no vacía y contener al menos un píxel del objeto.')

    labels = measure.label(binary, connectivity=2)
    regions = measure.regionprops(labels)
    beta0 = len(regions)
    chi = int(measure.euler_number(binary, connectivity=2))
    beta1 = int(beta0 - chi)
    if beta1 < 0:
        raise ValueError('La topología estimada es inconsistente; revisar máscara y conectividad.')

    primary = max(regions, key=lambda region: region.area)
    pixel_area = float(binary.sum())
    area = pixel_area * float(pixel_size) ** 2
    perimeter = float(sum(region.perimeter for region in regions)) * float(pixel_size)
    major = float(primary.axis_major_length) * float(pixel_size)
    minor = float(primary.axis_minor_length) * float(pixel_size)
    aspect = major / minor if minor else math.nan
    circularity = 4 * math.pi * area / (perimeter ** 2) if perimeter else math.nan
    return Metrics2D(
        pixel_area=pixel_area, area=area, perimeter=perimeter,
        major_axis=major, minor_axis=minor, aspect_ratio=aspect,
        circularity=circularity, solidity=float(primary.solidity),
        extent=float(primary.extent), eccentricity=float(primary.eccentricity),
        orientation_rad=float(primary.orientation), beta0=beta0, beta1=beta1,
        euler_characteristic=chi, primary_component_pixel_area=float(primary.area),
        component_policy='total_area_perimeter; shape_descriptors_largest_component',
    )


def metrics_to_dict(metrics: Metrics2D):
    return asdict(metrics)
