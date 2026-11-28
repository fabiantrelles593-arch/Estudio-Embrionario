"""Utilidades de ``scripts/figure_atlas.py`` con arreglos sintéticos (ningún dato real)."""
import importlib.util
from pathlib import Path

import numpy as np

_spec = importlib.util.spec_from_file_location("figure_atlas", Path(__file__).resolve().parents[1] / "scripts" / "figure_atlas.py")
fa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fa)


def test_clean_labels_drops_interpolated_values_and_small_islands():
    raw = np.zeros((40, 40), np.float32)
    raw[5:25, 5:25] = 3.0
    raw[10, 10] = 2.5            # vóxel interpolado dentro de la etiqueta 3: se rellena con la moda
    raw[30:33, 30:33] = 7.0      # isla de 9 píxeles: se elimina (< 25)
    out = fa._clean_labels(raw)
    assert out[10, 10] == 3
    assert (out[30:33, 30:33] == 0).all()
    assert set(np.unique(out)) == {0, 3}


def test_bbox_crops_to_foreground_with_margin():
    img = np.zeros((100, 80), np.float32)
    img[40:60, 30:50] = 1.0
    cy, cx = fa._bbox(img, margin=5)
    assert (cy.start, cy.stop, cx.start, cx.stop) == (35, 64, 25, 54)


def test_window_is_bounded():
    w = fa._window(np.arange(100, dtype=np.float32))
    assert w.min() == 0.0 and w.max() == 1.0
