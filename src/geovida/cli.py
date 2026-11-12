"""Línea de órdenes de geovida.

  geovida plan                      tabla de resolución mínima para luz verde de volumen
  geovida datasheet CARPETA_O_ZIP [--out ficha.json] [--hide-names]
                                    ficha descriptiva de volúmenes NIfTI (no compara con nada)
  geovida certify IMAGEN.npy --spacing 1 1 2 --segmenter otsu --profile realistic
                                    certificado de una imagen 3D (JSON)
  geovida certify VOLUMEN.nii.gz --segmenter smoothed_otsu --profile us_compound
                 --frozen h12_frozen.json --report informe.md
                                    NIfTI (el vóxel sale de la cabecera), calibración de ecografía
                                    simulada e informe con trazabilidad

  geovida real2d FOTO.jpg --roi X0 Y0 X1 Y1 --ruler X1 Y1 X2 Y2 --ruler-mm 10
                 [--printed-crl-mm 12.3] [--caliper X1 Y1 X2 Y2] [--human --authorization-note "..."]
                                    mide una longitud sobre una ecografía 2D real (informe sin nombres ni
                                    metadatos; el semáforo nunca sale verde sobre imagen real)

  geovida trajectory --crl 37.6 [--crl-rel-sd 0.02] [--ga-days 74] [--horizons 7 14 21 28] [--out DIR]
                                    franja de la referencia poblacional (INTERGROWTH-21st) en semanas posteriores, con la
                                    incertidumbre de medida y de edad propagada; NO predice crecimiento ni aspecto

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


def _datasheet(args) -> int:
    from .realdata import scan
    rows = scan(args.source)
    if args.hide_names:
        for i, r in enumerate(rows, start=1):
            r["name"], r["path"] = f"vol_{i:03d}", f"vol_{i:03d}"
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=1, default=float), encoding="utf-8")
    for r in rows:
        if "error" in r:
            print(f"{r['path']}: ERROR {r['error']}")
            continue
        kind = ("etiquetas " + ",".join(r["labels"])) if r["label_like"] else \
            f"intensidad p1={r['p1']:.3g} p50={r['p50']:.3g} p99={r['p99']:.3g}"
        print(f"{r['path']}: forma {tuple(r['shape'])}, "
              f"vóxel {tuple(round(s, 4) for s in r['spacing_mm'])} mm, {kind}")
    print(f"\n{len(rows)} archivos; ficha guardada en {args.out}")
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


def _real2d(args) -> int:
    from . import real2d as r2
    from .biometry import models_from_json

    if args.human and not (args.authorization_note or "").strip():
        print("error: una imagen humana exige --authorization-note (quién autoriza y con qué base; se "
              "guarda como declaración, no se verifica). Ver docs/DATOS_REALES_Y_ETICA.md.", file=sys.stderr)
        return 2
    if args.mm_per_px is not None:
        scale = r2.Scale(float(args.mm_per_px), "declarada", 0.0)
    elif args.ruler is not None and args.ruler_mm is not None:
        scale = r2.scale_from_ruler(tuple(args.ruler[:2]), tuple(args.ruler[2:]), args.ruler_mm)
    elif args.ticks is not None and args.tick_mm is not None:
        scale = r2.scale_from_ticks([float(v) for v in args.ticks.split(",")], args.tick_mm)
    else:
        print("error: da la escala con --mm-per-px, o --ruler X1 Y1 X2 Y2 --ruler-mm L, o --ticks a,b,c --tick-mm L",
              file=sys.stderr)
        return 2
    frozen = Path(args.frozen)
    if not frozen.exists():
        print(f"error: no existe la calibración {frozen}", file=sys.stderr)
        return 2
    models = models_from_json(frozen.read_text())
    img = r2.load_gray(args.image)
    res = r2.measure_roi(img.gray, tuple(args.roi), scale, models, bright=not args.dark_object,
                         blur_mm_grid=tuple(args.blur_mm) if args.blur_mm else r2.DEFAULT_BLUR_MM_GRID)
    printed = None
    if args.printed_crl_mm:
        ok = [r["measured_mm"] for r in res["rows"] if r.get("in_box") and r["measured_mm"]]
        mm = float(np.median(ok)) if ok else res["native"]["length_mm"]
        printed = r2.compare_printed(mm, args.printed_crl_mm)
    caliper = None
    if args.caliper:
        caliper = {"length_mm": r2.caliper_mm(tuple(args.caliper[:2]), tuple(args.caliper[2:]), scale)}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    kw = dict(sha256=img.sha256, image_shape=img.gray.shape, authorization_note=args.authorization_note,
              printed=printed, caliper=caliper, version=__version__)
    (out / "informe.md").write_text(r2.report_markdown(res, **kw), encoding="utf-8")
    (out / "informe.json").write_text(json.dumps(r2.report_dict(res, **kw), indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    r2.save_overlay(img.gray, res["roi"], res["native"]["mask"], out / "superposicion.png")
    print(f"medida nativa: {res['native']['length_mm']:.2f} mm; control: "
          f"{'objeto recortado por la ROI' if res['qc']['touches_roi_border'] else 'ok'}")
    for r in res["rows"]:
        m = "—" if r["measured_mm"] is None else f"{r['measured_mm']:.2f} mm"
        print(f"  desenfoque {r['blur_mm']:g} mm: {LIGHT_MARK.get(r['light'], r['light'])} {m}"
              f"{'  (' + r['reason'] + ')' if r.get('reason') else ''}")
    print(f"informe y superposición en {out}/ (guardar fuera del repositorio si la imagen es de una persona)")
    return 0


def _trajectory(args) -> int:
    from . import trajectory as tj
    try:
        p = tj.projection(args.crl, crl_rel_sd=args.crl_rel_sd, crl_rel_bias=args.crl_rel_bias, ga_known_days=args.ga_days,
                          horizons_days=tuple(args.horizons), n_draws=args.draws, seed=args.seed)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "trayectoria.json").write_text(json.dumps(p, indent=2, ensure_ascii=False))
    (out / "trayectoria.md").write_text(tj.report_markdown(p))
    ga = p["ga_now"]
    print(f"edad ahora ({ga['source']}): {ga['median_days']:.1f} d ({ga['weeks_days'][0]}+{ga['weeks_days'][1]})")
    for r in p["rows"]:
        if r["in_source_range"]:
            print(f"  +{r['days_ahead']} d: media poblacional {r['population_mean_mm']:.1f} mm; "
                  f"envolvente {r['envelope']['lo']:.1f}–{r['envelope']['hi']:.1f} mm")
        else:
            print(f"  +{r['days_ahead']} d: fuera del rango de la fuente; no se calcula")
    print(f"informe en {out}/ (no predice crecimiento ni aspecto; solo investigación y educación)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="geovida", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan", help="tabla de resolución mínima").set_defaults(fn=_plan)
    d = sub.add_parser("datasheet", help="ficha descriptiva de volúmenes NIfTI")
    d.add_argument("source", help="carpeta, .zip o un archivo .nii/.nii.gz")
    d.add_argument("--out", default="ficha_volumenes.json")
    d.add_argument("--hide-names", action="store_true",
                   help="sustituir los nombres de archivo por vol_001, vol_002… (privacidad)")
    d.set_defaults(fn=_datasheet)
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
    r = sub.add_parser("real2d", help="medir una longitud sobre una ecografía 2D real (investigación)")
    r.add_argument("image")
    r.add_argument("--roi", type=int, nargs=4, required=True, metavar=("X0", "Y0", "X1", "Y1"),
                   help="región de interés en píxeles de la imagen completa")
    r.add_argument("--mm-per-px", type=float, default=None, help="escala declarada")
    r.add_argument("--ruler", type=float, nargs=4, default=None, metavar=("X1", "Y1", "X2", "Y2"),
                   help="dos puntos de la regla impresa")
    r.add_argument("--ruler-mm", type=float, default=None, help="longitud real entre los dos puntos de la regla")
    r.add_argument("--ticks", default=None, help="posiciones en píxeles de marcas igualmente espaciadas, 'a,b,c,…'")
    r.add_argument("--tick-mm", type=float, default=None, help="espaciado real entre marcas")
    r.add_argument("--caliper", type=float, nargs=4, default=None, metavar=("X1", "Y1", "X2", "Y2"),
                   help="dos puntos marcados a mano para una segunda lectura")
    r.add_argument("--printed-crl-mm", type=float, default=None, help="medida impresa por el equipo u operador")
    r.add_argument("--dark-object", action="store_true", help="el objeto es más oscuro que el fondo")
    r.add_argument("--blur-mm", type=float, nargs="+", default=None, help="rejilla de desenfoque en mm")
    r.add_argument("--human", action="store_true", help="la imagen es de una persona")
    r.add_argument("--authorization-note", default=None,
                   help="quién autoriza y con qué base (obligatorio con --human; se guarda como declaración)")
    r.add_argument("--frozen", default="results/summary/h14_frozen.json", help="calibración congelada (JSON)")
    r.add_argument("--out", default="real2d_out")
    r.set_defaults(fn=_real2d)
    t = sub.add_parser("trajectory", help="franja de referencia poblacional en semanas posteriores (no es una predicción)")
    t.add_argument("--crl", type=float, required=True, help="longitud cráneo-rabadilla medida (mm)")
    t.add_argument("--crl-rel-sd", type=float, default=0.02, help="error relativo (SD) declarado de la medida; 0.02 = 2 %%")
    t.add_argument("--crl-rel-bias", type=float, default=0.0, help="sesgo relativo declarado de la medida")
    t.add_argument("--ga-days", type=float, default=None, help="edad en días por otra vía; sin ella se estima con la misma CRL")
    t.add_argument("--horizons", type=float, nargs="+", default=[7, 14, 21, 28], help="días después de la medida")
    t.add_argument("--draws", type=int, default=20000)
    t.add_argument("--seed", type=int, default=20261218)
    t.add_argument("--out", default="trayectoria_out")
    t.set_defaults(fn=_trajectory)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
