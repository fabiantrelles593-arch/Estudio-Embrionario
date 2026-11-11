"""Línea de órdenes de geovida.

  geovida plan                      tabla de resolución mínima para luz verde de volumen
  geovida certify IMAGEN.npy --spacing 1 1 2 --segmenter otsu --profile realistic
                                    certificado de una imagen 3D (JSON)
  geovida certify VOLUMEN.nii.gz --segmenter smoothed_otsu --profile us_compound
                 --frozen h12_frozen.json --report informe.md
                                    NIfTI (el vóxel sale de la cabecera), calibración de ecografía
                                    simulada e informe con trazabilidad

Solo investigación y educación. No procesa ni debe procesar imágenes de personas sin las
condiciones de docs/DATOS_REALES_Y_ETICA.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import platform
import sys
from importlib import resources
from pathlib import Path

import numpy as np

from . import __version__
from .certificate import certify, load_frozen, planning_table
from .provenance import git_state

LIGHT_MARK = {"verde": "[VERDE]", "amarillo": "[AMARILLO]", "rojo": "[ROJO]"}


def _load(path: Path):
    """Imagen y, si el formato lo trae, el vóxel en mm (NIfTI); si no, ``None``."""
    name = path.name.lower()
    if name.endswith((".nii", ".nii.gz")):
        from .realdata import load_volume
        arr, spacing, _meta = load_volume(path)
        return arr, spacing
    if path.suffix == ".npy":
        return np.load(path, allow_pickle=False), None
    if path.suffix in (".tif", ".tiff"):
        from skimage import io
        return np.asarray(io.imread(path)), None
    raise SystemExit(f"formato no admitido: {path.suffix} (use .npy, .tif o .nii/.nii.gz)")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _calibration(frozen_path: str | None) -> tuple[dict, dict]:
    """Congelado y su procedencia. Sin ruta, el paquetado de v0.4."""
    if frozen_path is None:
        res = resources.files("geovida").joinpath("frozen/h9_frozen.json")
        digest = hashlib.sha256(res.read_bytes()).hexdigest()
        return load_frozen(), {"source": "paquete: geovida/frozen/h9_frozen.json", "sha256": digest}
    p = Path(frozen_path)
    frozen = json.loads(p.read_text(encoding="utf-8"))
    return frozen, {"source": f"archivo: {p.name}", "sha256": _sha256(p)}


NOTICE = ("Resultado de investigación y educación, sin uso clínico: este informe no es un informe "
          "médico ni un diagnóstico. Una luz verde es una probabilidad calibrada con imágenes "
          "simuladas, no una validación con datos reales.")


def _provenance(args, image_path: Path, calib: dict, frozen: dict) -> dict:
    state = git_state(Path(__file__).resolve().parents[2])
    return {
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "geovida_version": __version__,
        "git": state,
        "python": platform.python_version(), "numpy": np.__version__,
        "input": {"sha256": _sha256(image_path),
                  "file_name": image_path.name if args.include_filename else None,
                  "file_name_note": None if args.include_filename else
                  "omitido por privacidad (use --include-filename para incluirlo)"},
        "calibration": {**calib, "selected_features": frozen.get("selected"),
                        "content_sha256": frozen.get("content_sha256"),
                        "profiles": frozen.get("profiles")},
    }


def _report_markdown(rep: dict) -> str:
    c, pv = rep["certificate"], rep["provenance"]
    v, t = c["volume"], c["topology"]
    inp, cal = pv["input"], pv["calibration"]
    lines = [
        "# Informe de certificado geovida", "",
        f"> {rep['notice']}", "",
        "## Resultado", "",
        f"* **Volumen** {LIGHT_MARK[v['light']]}  p = {v['p']:.3f}  valor = {v['value']:.6g}"
        + (f"  ({v['reason']})" if v["reason"] else ""),
        f"* **Topología** {LIGHT_MARK[t['light']]}  p = {t['p']:.3f}  Betti = {tuple(t['betti'])}"
        + (f"  ({t['reason']})" if t["reason"] else ""),
        f"* Dentro del dominio de calibración: volumen {'sí' if v['in_domain'] else 'no'}, "
        f"topología {'sí' if t['in_domain'] else 'no'}", "",
        "## Parámetros declarados", "",
        f"* Segmentador: `{c['declared']['segmenter']}`; perfil de imagen: `{c['declared']['profile']}`",
        f"* Vóxel (mm): {', '.join(f'{x:.6g}' for x in c['spacing'])}; forma: {c['shape']}",
        f"* Umbrales: verde p >= {c['thresholds']['green']}, rojo p < {c['thresholds']['red']}", "",
        "## Procedencia", "",
        f"* geovida {pv['geovida_version']}; commit {pv['git']['commit']}"
        f" (código con cambios sin guardar: {pv['git']['dirty_code']})",
        f"* Python {pv['python']}, numpy {pv['numpy']}; generado {pv['generated_utc']}",
        f"* Imagen: SHA-256 `{inp['sha256']}`; "
        + (f"archivo `{inp['file_name']}`" if inp["file_name"] else inp["file_name_note"]),
        f"* Calibración: {cal['source']}; SHA-256 `{cal['sha256']}`; variables topológicas: "
        f"{cal['selected_features']}", "",
        "## Límites", "", *[f"* {s}" for s in c["limits"]], "",
    ]
    return "\n".join(lines)


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
    path = Path(args.image)
    image, header_spacing = _load(path)
    spacing = args.spacing if args.spacing is not None else header_spacing
    if spacing is None:
        raise SystemExit("falta --spacing HX HY HZ (solo un NIfTI trae el vóxel en su cabecera)")
    frozen, calib = _calibration(args.frozen)
    try:
        cert = certify(image, spacing, args.segmenter, args.profile, frozen)
    except KeyError as exc:
        raise SystemExit(f"{exc.args[0]}. Para el perfil {args.profile!r} indique --frozen "
                         "con la calibración correspondiente.") from None
    if args.json:
        Path(args.json).write_text(json.dumps(cert, indent=2, ensure_ascii=False))
    if args.report:
        rep = {"notice": NOTICE, "provenance": _provenance(args, path, calib, frozen),
               "certificate": cert}
        out = Path(args.report)
        out.write_text(_report_markdown(rep) if out.suffix.lower() == ".md"
                       else json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
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
    c.add_argument("--spacing", type=float, nargs=3, default=None, metavar=("HX", "HY", "HZ"),
                   help="vóxel en mm; obligatorio salvo en NIfTI (sale de la cabecera)")
    c.add_argument("--segmenter", required=True, choices=("global", "otsu", "smoothed_otsu"))
    c.add_argument("--profile", required=True,
                   help="perfil de imagen declarado: ideal, realistic (paquete) o los de la "
                        "calibración dada en --frozen (p. ej. us_compound, us_raw)")
    c.add_argument("--frozen", help="calibración congelada (JSON); sin ella, la de v0.4")
    c.add_argument("--json", help="guardar el certificado completo en este archivo")
    c.add_argument("--report", help="informe con trazabilidad (.md = Markdown; otro = JSON)")
    c.add_argument("--include-filename", action="store_true",
                   help="incluir el nombre del archivo en el informe (por defecto se omite)")
    c.set_defaults(fn=_certify)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
