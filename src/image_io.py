"""Carga de imágenes y conversión controlada a máscaras binarias 2D."""
from pathlib import Path
import numpy as np
from skimage import color, io, util


def load_mask(path: str | Path, threshold: float = 0.5) -> np.ndarray:
    """Lee imagen 2D o RGB/RGBA y devuelve una máscara booleana 2D.

    Los píxeles con intensidad en escala de grises estrictamente mayor que
    `threshold` se marcan como objeto. El umbral se define en [0, 1]. La
    conversión RGB usa luminancia y omite el canal alfa. Esta segmentación
    automática simple no constituye una segmentación anatómica validada.
    """
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float, np.number)) or not np.isfinite(threshold):
        raise ValueError('threshold debe ser un número finito en [0, 1].')
    if threshold < 0 or threshold > 1:
        raise ValueError('threshold debe ser un número finito en [0, 1].')

    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f'No se encontró el archivo: {file_path}')
    image = np.asarray(io.imread(file_path))
    if image.size == 0:
        raise ValueError('La imagen está vacía.')
    if np.issubdtype(image.dtype, np.floating):
        if not np.isfinite(image).all() or image.min() < 0 or image.max() > 1:
            raise ValueError('Las imágenes de punto flotante deben tener intensidades finitas en [0, 1].')
    if image.ndim == 2:
        gray = util.img_as_float(image)
    elif image.ndim == 3 and image.shape[-1] in (3, 4):
        rgb = util.img_as_float(image[..., :3])
        gray = color.rgb2gray(rgb)
    else:
        raise ValueError('Formato no compatible: se esperaba una imagen 2D o RGB/RGBA.')
    if not np.isfinite(gray).all():
        raise ValueError('La imagen contiene intensidades no finitas.')
    return gray > float(threshold)
