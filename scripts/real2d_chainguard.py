"""EXPLORATORIO (H16, §6 del preregistro): ¿cae una imagen 2D real dentro del soporte de la guardia de cadena? No certifica nada.

Calcula los dos índices de ``geovida.chainguard`` sobre la ROI de la imagen (y sobre la ROI ensanchada) y dice en qué cajas de régimen caen. La imagen
no entra al repositorio: se pasa por línea de órdenes y solo se imprime un JSON con números.

    python scripts/real2d_chainguard.py FOTO.png --roi X0 Y0 X1 Y1 [--pad 40] [--out resultado.json]
"""
import argparse
import json
import sys
from pathlib import Path

from geovida import chainguard as cg
from geovida import h16, real2d

FROZEN = Path(__file__).resolve().parents[1] / "results" / "summary" / "h16_chain_frozen.json"


def inside(models: dict, idx: dict) -> dict:
    out = {}
    for kind, m in models.items():
        out[kind] = {r.name: bool(r.contains(idx)) for r in m.regimes}
    return out


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("image")
    a.add_argument("--roi", type=int, nargs=4, required=True)
    a.add_argument("--pad", type=int, default=40)
    a.add_argument("--out", default=None)
    args = a.parse_args(argv)
    par, rec = h16.freeze_from_json(FROZEN.read_text())
    gray = real2d.load_gray(args.image).gray
    x0, y0, x1, y1 = args.roi
    h, w = gray.shape
    crops = {"roi": (x0, y0, x1, y1),
             "roi_ensanchada": (max(0, x0 - args.pad), max(0, y0 - args.pad), min(w, x1 + args.pad), min(h, y1 + args.pad))}
    out = {"crops_px": {k: list(v) for k, v in crops.items()}, "indices": {}, "dentro_del_soporte": {}}
    for name, (a0, b0, a1, b1) in crops.items():
        idx = cg.image_indices(gray[b0:b1, a0:a1])
        out["indices"][name] = idx
        out["dentro_del_soporte"][name] = {"diseno_2_recalibracion": inside(rec, idx), "diseno_1_parametrico": inside(par, idx)}
    out["cajas"] = {kind: {r.name: {c: list(b) for c, b in r.box.items()} for r in m.regimes} for kind, m in rec.items()}
    txt = json.dumps(out, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(txt)
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
