import numpy as np
import pytest
from src.metrics_2d import measure_mask


def test_circle_mask_basic_topology():
    y, x = np.ogrid[:51, :51]
    mask = (x - 25) ** 2 + (y - 25) ** 2 <= 10 ** 2
    result = measure_mask(mask)
    assert result.pixel_area == int(mask.sum())
    assert result.beta0 == 1
    assert result.beta1 == 0
    assert result.euler_characteristic == 1
    assert result.primary_component_pixel_area == result.pixel_area


def test_pixel_size_scales_area_and_lengths():
    mask = np.zeros((12, 12), dtype=bool)
    mask[2:8, 2:8] = True
    one = measure_mask(mask, pixel_size=1.0)
    two = measure_mask(mask, pixel_size=2.0)
    assert two.area == pytest.approx(one.area * 4)
    assert two.perimeter == pytest.approx(one.perimeter * 2)


@pytest.mark.parametrize('pixel_size', [0, -1, float('nan'), float('inf'), True])
def test_invalid_pixel_size_rejected(pixel_size):
    with pytest.raises(ValueError):
        measure_mask(np.ones((3, 3), dtype=bool), pixel_size=pixel_size)


def test_empty_mask_rejected():
    with pytest.raises(ValueError):
        measure_mask(np.zeros((3, 3), dtype=bool))
