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


# --- v0.2: segmentador de extension con limpieza de motas -------------------
from geovida.segment import EXTENSION_SEGMENTERS


def test_extension_segmenters_do_not_touch_the_preregistered_set():
    assert set(SEGMENTERS) == {"global", "otsu", "smoothed_otsu"}
    assert set(EXTENSION_SEGMENTERS) == {"otsu_clean"}


def _two_level(shape=(24, 24, 24)):
    img = np.zeros(shape, dtype=np.float32)
    img[4:20, 4:20, 4:20] = 1.0
    return img


def test_clean_removes_an_isolated_speck_that_plain_otsu_keeps():
    img = _two_level()
    img[1, 1, 1] = 1.0
    assert segment("otsu", img, (1, 1, 1))[1, 1, 1]
    assert not segment("otsu_clean", img, (1, 1, 1))[1, 1, 1]


def test_clean_fills_a_tiny_hole_that_plain_otsu_keeps():
    img = _two_level()
    img[10:12, 10, 10] = 0.0  # hueco de 2 voxeles
    assert not segment("otsu", img, (1, 1, 1))[10, 10, 10]
    assert segment("otsu_clean", img, (1, 1, 1))[10, 10, 10]


def test_clean_keeps_a_real_cavity():
    img = _two_level()
    img[9:15, 9:15, 9:15] = 0.0  # cavidad de 6^3 voxeles
    assert not segment("otsu_clean", img, (1, 1, 1))[12, 12, 12]
    assert betti_numbers(segment("otsu_clean", img, (1, 1, 1)), 26).as_tuple() == (1, 0, 1)


def test_clean_keeps_the_main_object_unchanged():
    img = _two_level()
    assert (segment("otsu_clean", img, (1, 1, 1)) == segment("otsu", img, (1, 1, 1))).all()


# --- v0.2: limites conocidos y visibilidad de la limpieza (ERRATA E11) -------
from geovida.experiment import Condition, run_condition
from geovida.segment import clean_report


def test_clean_erases_a_real_cavity_below_the_size_floor():
    # Piloto (12 reps, ideal, shell_tight, t/h = 4): otsu acierta la topologia
    # 12/12 y otsu_clean 0/12, porque la cavidad real mide ~2 voxeles de
    # diametro (< 8 voxeles de volumen) y la limpieza la rellena.
    rows = run_condition(Condition("shell_tight", 4.0, 1.0, "ideal", 0),
                         segmenters=("otsu", "otsu_clean"))
    by = {r["segmenter"]: r for r in rows}
    assert by["otsu"]["topology_ok"] is True
    assert by["otsu_clean"]["topology_ok"] is False


def test_clean_report_counts_what_was_removed_and_filled():
    img = _two_level()
    img[1, 1, 1] = 1.0           # una mota aislada
    img[10:12, 10, 10] = 0.0     # un hueco de 2 voxeles
    rep = clean_report(img, (1, 1, 1))
    assert rep == {"removed_components": 1, "filled_cavities": 1}


def test_clean_report_is_zero_when_nothing_is_cleaned():
    img = _two_level()
    img[9:15, 9:15, 9:15] = 0.0  # cavidad real de 6^3
    assert clean_report(img, (1, 1, 1)) == {"removed_components": 0, "filled_cavities": 0}
