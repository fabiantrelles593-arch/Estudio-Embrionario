import numpy as np
import pytest
from skimage import io
from src.image_io import load_mask


def test_load_grayscale_png(tmp_path):
    path = tmp_path / 'mask.png'
    io.imsave(path, np.array([[0, 0], [255, 255]], dtype=np.uint8))
    result = load_mask(path)
    assert result.dtype == bool
    assert result.tolist() == [[False, False], [True, True]]


def test_load_rgb_png(tmp_path):
    image = np.zeros((3, 3, 3), dtype=np.uint8)
    image[1:, 1:, :] = 255
    path = tmp_path / 'rgb.png'
    io.imsave(path, image)
    result = load_mask(path)
    assert result.shape == (3, 3)
    assert result[2, 2]


def test_bad_threshold_rejected(tmp_path):
    path = tmp_path / 'mask.png'
    io.imsave(path, np.zeros((2, 2), dtype=np.uint8), check_contrast=False)
    with pytest.raises(ValueError):
        load_mask(path, threshold=1.2)


def test_nonexistent_path_rejected(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_mask(tmp_path / 'absent.png')


def test_float_image_outside_unit_interval_rejected(tmp_path):
    path = tmp_path / 'float.tiff'
    io.imsave(path, np.array([[0.0, 2.0]], dtype=np.float32), check_contrast=False)
    with pytest.raises(ValueError):
        load_mask(path)
