"""Sensibilidad (descriptiva) de la medida de una imagen 2D real al mapa de color. NO cambia el resultado primario de ``geovida real2d``.

Convierte la ROI en color a intensidad con la barra de color de la propia captura (``geovida.colorbar``) en vez de la luminancia y vuelve a
medir con la misma escala, ROI, modelo congelado y segmentador. Informa la diferencia y si la linealización se puede leer
(reglas de confianza de ``docs/PREREGISTRO_REAL2D_PILOTO.md`` §8). La imagen no entra al repositorio: se pasa por línea de órdenes y
solo se imprime un JSON con números.

    python scripts/real2d_colorbar.py FOTO.png --roi X0 Y0 X1 Y1 --ticks a,b,c,... --tick-mm 10 --bar X0 Y0 X1 Y1 [--out resultado.json]
"""
import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

from geovida import biometry as bio
from geovida import colorbar, real2d

FROZEN = Path(__file__).resolve().parents[1] / "results" / "summary" / "h14_frozen.json"
RESIDUAL_MAX, OFF_LUT_MAX, MONOTONE_MIN = 0.06, 0.20, 0.9        # reglas de confianza fijadas en el preregistro §8
STEP_PX = 0.37                                                   # 1 px a 0.3704 mm/px, solo para la regla de lectura


def load_rgb(path) -> np.ndarray:
    with Image.open(Path(path)) as im:
        return np.asarray(ImageOps.exif_transpose(im).convert("RGB"), dtype=np.float64) / 255.0


def measure(gray, roi, scale, models):
    r = real2d.measure_roi(gray, roi, scale, models=models, segmenter="smoothed_otsu")
    ok = [x["measured_mm"] for x in r["rows"] if x.get("in_box") and x.get("measured_mm")]
    return {"native_mm": r["native"]["length_mm"], "native_px": r["native"]["n_px"],
            "rows_min_mm": min(ok) if ok else None, "rows_max_mm": max(ok) if ok else None,
            "touches_roi_border": r["qc"]["touches_roi_border"],
            "n_components": r["qc"]["n_components_ge_5pct_of_largest"],
            "contrast_to_noise": r["qc"]["contrast_to_noise"]}


def linear_gray(rgb, roi, bar, orientation="auto"):
    """Imagen del tamaño de ``rgb`` con la ROI linealizada (el resto en 0: solo se mide dentro de la ROI) y las cifras de confianza."""
    x0, y0, x1, y1 = roi
    lut = colorbar.lut_from_bar(rgb, bar, orientation=orientation)
    sub = colorbar.linearize(rgb[y0:y1, x0:x1], lut)
    g = np.zeros(rgb.shape[:2])
    g[y0:y1, x0:x1] = sub["linear"]
    return g, lut, sub


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("image")
    a.add_argument("--roi", type=int, nargs=4, required=True)
    a.add_argument("--ticks", required=True)
    a.add_argument("--tick-mm", type=float, required=True)
    a.add_argument("--bar", type=int, nargs=4, required=True, help="caja de la barra de color: x0 y0 x1 y1")
    a.add_argument("--out", default=None)
    args = a.parse_args(argv)
    models = bio.models_from_json(FROZEN.read_text())
    rgb = load_rgb(args.image)
    scale = real2d.scale_from_ticks([float(v) for v in args.ticks.split(",")], args.tick_mm)
    roi, bar = tuple(args.roi), tuple(args.bar)

    lum = real2d.load_gray(args.image).gray
    out = {"scale_mm_per_px": scale.mm_per_px, "luminance": measure(lum, roi, scale, models)}
    g, lut, sub = linear_gray(rgb, roi, bar)
    out["bar"] = {"box": list(bar), "n_rows": lut.n_rows, "lum_monotone_fraction": lut.lum_monotone_fraction,
                  "warnings": list(lut.warnings)}
    out["roi_vs_lut"] = {"residual_median": sub["residual_median"], "off_lut_fraction": sub["off_lut_fraction"],
                         "off_lut_threshold": sub["off_lut_threshold"]}
    out["linearized"] = measure(g, roi, scale, models)
    d = out["linearized"]["native_mm"] - out["luminance"]["native_mm"]
    trust = {"bar_is_monotone": bool(lut.lum_monotone_fraction >= MONOTONE_MIN and not lut.warnings),
             "residual_ok": bool(sub["residual_median"] <= RESIDUAL_MAX),
             "off_lut_ok": bool(sub["off_lut_fraction"] <= OFF_LUT_MAX)}
    trust["interpretable"] = all(trust.values())
    out["trust"] = trust
    out["delta"] = {"mm": d, "px": d / scale.mm_per_px,
                    "reading": ("no interpretable (no cumple las reglas de confianza)" if not trust["interpretable"] else
                                "no mueve la medida más de un píxel" if abs(d) <= STEP_PX else
                                "la mueve de forma apreciable (1 a 3 px)" if abs(d) <= 3 * STEP_PX else "la mueve mucho (más de 3 px)")}

    x0, y0, x1, y1 = bar
    var = []
    for t, b, l, r in itertools.product((-2, 0, 2), (-2, 0, 2), (-1, 0, 1), (-1, 0, 1)):
        box = (x0 + l, y0 + t, x1 + r, y1 + b)
        try:
            gv, lv, sv = linear_gray(rgb, roi, box)
            m = measure(gv, roi, scale, models)
        except ValueError:
            continue
        var.append({"box": list(box), "native_mm": m["native_mm"], "lum_monotone_fraction": lv.lum_monotone_fraction,
                    "residual_median": sv["residual_median"]})
    lens = [v["native_mm"] for v in var]
    out["bar_box_variants"] = {"n": len(var), "min_mm": min(lens), "max_mm": max(lens), "median_mm": float(np.median(lens))}
    out["orientation_explicit"] = {}
    for o in ("top_high", "bottom_high"):
        gv, lv, sv = linear_gray(rgb, roi, bar, orientation=o)
        out["orientation_explicit"][o] = {"native_mm": measure(gv, roi, scale, models)["native_mm"],
                                          "residual_median": sv["residual_median"]}
    txt = json.dumps(out, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(txt)
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
