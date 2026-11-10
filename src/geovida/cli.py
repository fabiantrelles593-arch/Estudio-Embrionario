"""Línea de órdenes de geovida.

  geovida plan                      tabla de resolución mínima para luz verde de volumen
  geovida certify IMAGEN.npy --spacing 1 1 2 --segmenter otsu --profile realistic
                                    certificado de una imagen 3D (JSON)

Solo investigación y educación. No procesa ni debe procesar imágenes de personas sin las
condiciones de docs/DATOS_REALES_Y_ETICA.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from .certificate import certify, planning_table

LIGHT_MARK = {"verde": "[VERDE]", "amarillo": "[AMARILLO]", "rojo": "[ROJO]"}


def _load(path: Path) -> np.ndarray:
    if path.suffix == ".npy":
        return np.load(path, allow_pickle=False)
    if path.suffix in (".tif", ".tiff"):
        from skimage import io
        return np.asarray(io.imread(path))
    raise SystemExit(f"formato no admitido: {path.suffix} (use .npy o .tif)")


def _plan(_args) -> int:
    print("Vóxeles mínimos para luz verde de volumen (p >= 0.90). Guía de fantomas sintéticos.\n")
    print(f"{'segmentador':15s}{'perfil':11s}{'prof. media':>12s}{'bola (diám.)':>14s}"
          f"{'cilindro (diám.)':>18s}{'lámina (grosor)':>17s}")
    for r in planning_table():
        print(f"{r['segmenter']:15s}{r['profile']:11s}{r['min_depth_voxels']:12.2f}"
              f"{r['ball_diameter_voxels']:14.1f}{r['cylinder_diameter_voxels']:18.1f}"
              f"{r['slab_thickness_voxels']:17.1f}")
    return 0


def _certify(args) -> int:
    image = _load(Path(args.image))
    cert = certify(image, args.spacing, args.segmenter, args.profile)
    if args.json:
        Path(args.json).write_text(json.dumps(cert, indent=2, ensure_ascii=False))
    v, t = cert["volume"], cert["topology"]
    print(f"Volumen    {LIGHT_MARK[v['light']]:11s} p = {v['p']:.2f}   valor = {v['value']:.6g}"
          + (f"   ({v['reason']})" if v["reason"] else ""))
    print(f"Topología  {LIGHT_MARK[t['light']]:11s} p = {t['p']:.2f}   Betti = {tuple(t['betti'])}"
          + (f"   ({t['reason']})" if t["reason"] else ""))
    for side, site in t["critical_sites"].items():
        if site:
            where = "" if site["centroid_vox"] is None else \
                " en el vóxel " + ", ".join(f"{c:.0f}" for c in site["centroid_vox"])
            print(f"  punto frágil ({side}): {site['kind']} a {site['offset_vox']} vóxeles{where}")
    print("\n" + "\n".join("- " + s for s in cert["limits"]))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="geovida", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan", help="tabla de resolución mínima").set_defaults(fn=_plan)
    c = sub.add_parser("certify", help="certificado de una imagen 3D")
    c.add_argument("image")
    c.add_argument("--spacing", type=float, nargs=3, required=True, metavar=("HX", "HY", "HZ"))
    c.add_argument("--segmenter", required=True, choices=("global", "otsu", "smoothed_otsu"))
    c.add_argument("--profile", required=True, choices=("ideal", "realistic"))
    c.add_argument("--json", help="guardar el certificado completo en este archivo")
    c.set_defaults(fn=_certify)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
