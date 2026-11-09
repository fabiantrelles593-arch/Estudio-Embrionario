import numpy as np
import pytest

from geovida.imaging import ImagingSpec, render, spec_for_t_over_h
from geovida.phantoms import make_phantom
from geovida.segment import SEGMENTERS, segment
from geovida.topology import betti_numbers


def test_registry_has_the_three_preregistered_segmenters():
    assert set(SEGMENTERS) == {"global", "otsu", "smoothed_otsu"}


@pytest.mark.parametrize("name", ["global", "otsu", "smoothed_otsu"])
def test_clean_ball_is_recovered_by_every_segmenter(name):
    ph = make_phantom("ball", t=1.0)
    out = render(ph, spec_for_t_over_h(10, 1.0, "ideal"), np.random.default_rng(0))
    mask = segment(name, out.image, out.spacing)
    vol = mask.sum() * np.prod(out.spacing)
    # Otsu sobre imagen suavizada sobrestima ~8 % un objeto de 10 voxeles de
    # diámetro (umbral < 0.5 por desbalance de clases): es una propiedad real
    # del método, no un error de código; el oráculo global sí es exacto (~1 %).
    tol = 0.01 if name == "global" else 0.10
    assert vol == pytest.approx(ph.truth.volume, rel=tol)
    assert mask.dtype == bool


def test_global_threshold_is_the_half_contrast_level():
    img = np.zeros((5, 5, 5), dtype=np.float32)
    img[2, 2, 2] = 0.5001
    img[1, 1, 1] = 0.4999
    m = segment("global", img, (1, 1, 1))
    assert m[2, 2, 2] and not m[1, 1, 1]


def test_smoothing_rescues_topology_at_low_snr():
    # A SNR = 2.5 el Otsu crudo se hunde en el ruido (umbral ~0.13): la máscara
    # es una maraña con cientos de túneles. Suavizar antes recupera la bola.
    ph = make_phantom("ball", t=1.0)
    spec = ImagingSpec(h_xy=0.1, snr=2.5)
    out = render(ph, spec, np.random.default_rng(5))
    raw = betti_numbers(segment("otsu", out.image, out.spacing), 26)
    smooth = betti_numbers(segment("smoothed_otsu", out.image, out.spacing), 26)
    assert raw.as_tuple() != (1, 0, 0)
    assert smooth.as_tuple() == (1, 0, 0)


def test_unknown_segmenter_is_rejected():
    with pytest.raises(ValueError):
        segment("magia", np.zeros((3, 3, 3), dtype=np.float32), (1, 1, 1))
