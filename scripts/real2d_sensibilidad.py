"""Sensibilidad (descriptiva) de la medida de una imagen 2D real. NO cambia el resultado primario de ``geovida real2d``.

Muestra cuánto se mueve la longitud nativa cuando cambian, uno a uno, la escala (mediana vs mínimos cuadrados), el segmentador
(`smoothed_otsu` vs `otsu`) y la ROI (desplazada ±``--shift`` px). No elige nada: sirve para dar un orden de magnitud de la
incertidumbre de procedimiento. La imagen no entra al repositorio: se pasa por línea de órdenes y solo se imprime un JSON con números.

    python scripts/real2d_sensibilidad.py FOTO.png --roi X0 Y0 X1 Y1 --ticks a,b,c,... --tick-mm 10 [--shift 6] [--out resultado.json]
"""
import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np

from geovida import biometry as bio
from geovida import real2d

FROZEN = Path(__file__).resolve().parents[1] / "results" / "summary" / "h14_frozen.json"


def lsq_scale(ticks, spacing_mm):
    """Escala por mínimos cuadrados con marcas consecutivas (índice 0, 1, 2, …); devuelve (mm/px, error típico de la pendiente en px)."""
    t = np.asarray(sorted(ticks), float)
    i = np.arange(len(t))
    A = np.vstack([i, np.ones_like(i)]).T
    (slope, _), res, *_ = np.linalg.lstsq(A, t, rcond=None)
    resid = t - A @ np.array([slope, t.mean() - slope * i.mean()])
    se = float(np.sqrt(resid @ resid / max(len(t) - 2, 1) / ((i - i.mean()) ** 2).sum()))
    return spacing_mm / slope, se


def native(gray, roi, scale, models, segmenter):
    r = real2d.measure_roi(gray, roi, scale, models=models, segmenter=segmenter, blur_mm_grid=(0.5,))
    return {"length_mm": r["native"]["length_mm"], "length_px": r["native"]["n_px"],
            "touches_roi_border": r["qc"]["touches_roi_border"], "n_components": r["qc"]["n_components_ge_5pct_of_largest"]}


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("image")
    a.add_argument("--roi", type=int, nargs=4, required=True)
    a.add_argument("--ticks", required=True)
    a.add_argument("--tick-mm", type=float, required=True)
    a.add_argument("--shift", type=int, default=6)
    a.add_argument("--dark-object", action="store_true")
    a.add_argument("--out", default=None)
    args = a.parse_args(argv)
    models = bio.models_from_json(FROZEN.read_text())
    img = real2d.load_gray(args.image)
    ticks = [float(v) for v in args.ticks.split(",")]
    s_med = real2d.scale_from_ticks(ticks, args.tick_mm)
    mm_lsq, se = lsq_scale(ticks, args.tick_mm)
    s_lsq = real2d.Scale(mm_lsq, "marcas (mínimos cuadrados)", 0.0)
    roi = tuple(args.roi)
    out = {"scale_median_mm_per_px": s_med.mm_per_px, "scale_lsq_mm_per_px": mm_lsq,
           "scale_lsq_relative_se": se / (args.tick_mm / mm_lsq), "segmenter": {}, "roi_shift": []}
    for seg in ("smoothed_otsu", "otsu"):
        out["segmenter"][seg] = native(img.gray, roi, s_med, models, seg)
    out["with_lsq_scale"] = native(img.gray, roi, s_lsq, models, "smoothed_otsu")
    x0, y0, x1, y1 = roi
    H, W = img.gray.shape
    for dx0, dy0, dx1, dy1 in itertools.product((-args.shift, args.shift), repeat=4):
        r = (x0 + dx0, y0 + dy0, x1 + dx1, y1 + dy1)
        if not (0 <= r[0] < r[2] <= W and 0 <= r[1] < r[3] <= H):
            continue
        n = native(img.gray, r, s_med, models, "smoothed_otsu")
        out["roi_shift"].append({"roi": list(r), **n})
    ok = [v["length_mm"] for v in out["roi_shift"] if not v["touches_roi_border"]]
    out["roi_shift_summary"] = {"n_variants": len(out["roi_shift"]), "n_not_touching_border": len(ok),
                                "min_mm": min(ok) if ok else None, "max_mm": max(ok) if ok else None,
                                "median_mm": float(np.median(ok)) if ok else None}
    txt = json.dumps(out, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(txt)
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
