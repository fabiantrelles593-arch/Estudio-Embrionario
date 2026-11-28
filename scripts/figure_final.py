"""Figuras y datos de la presentación final, calculados con el propio software (sin copiar números a mano).

    python scripts/figure_final.py --out docs/exposicion/img

Muestra real: el **primer caso** del manifiesto de H11 (`results/h11/manifiesto_qiu2021.csv`): ecografía 3D de
alta frecuencia de un embrión de ratón E11 con sus referencias de cuerpo y ventrículos dibujadas por personas
(Qiu et al. 2021, IEEE DataPort, CC BY). Se elige por esa regla, no por cómo salga.

Produce:
* ``pipeline_real.png`` y ``final_data.json["pipeline"]``: imagen original → referencia → segmentaciones de
  geovida (umbral global, Otsu, Otsu suavizado) en el mismo corte; medidas 2D del corte y 3D del volumen.
* ``final_data.json["h11_case"]``: las filas de ese caso en la caché de H11 (salida real del software; un caso,
  no un veredicto).
* ``mesh_body.json`` y ``mesh_ventricle.json``: mallas por marching cubes de las **referencias** reales.
* ``resolution_real.png`` y ``final_data.json["resolution"]``: la misma referencia remuestreada ×1…×4.
* ``euler_examples.png`` y ``final_data.json["euler"]``: ejemplos **sintéticos** de Betti y χ (ilustración).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ACCENT, ACCENT2, ACCENT3, MUTED, FG, BG = "#3fd0c9", "#f2a541", "#b69cff", "#8b98a5", "#e6edf3", "#0b1016"


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG, "text.color": FG,
                         "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
                         "axes.edgecolor": "#24303c", "font.size": 10})
    return plt


def _window(a, lo=1.0, hi=99.5):
    a = a.astype(np.float32)
    p0, p1 = np.percentile(a, [lo, hi])
    return np.clip((a - p0) / max(p1 - p0, 1e-6), 0, 1)


def _metrics_2d(mask: np.ndarray, sp: float) -> dict:
    """Medidas del corte: área y perímetro de geovida (``twod``) y descriptores de forma de scikit-image."""
    from skimage.measure import label, regionprops
    from geovida.twod import measure_mask_2d
    base = measure_mask_2d(mask, sp)
    lab = label(mask, connectivity=2)
    big = max(regionprops(lab), key=lambda r: r.area)
    perim = base["perim_crofton"]
    out = {"area_mm2": base["area"], "perimeter_mm": perim, "b0": base["b0"], "b1": base["b1"],
           "circularity": 4 * np.pi * base["area"] / perim ** 2 if perim > 0 else None,
           "solidity": float(big.solidity), "eccentricity": float(big.eccentricity),
           "aspect_ratio": float(big.axis_major_length / big.axis_minor_length) if big.axis_minor_length > 0 else None,
           "length_mm": float(big.axis_major_length * sp), "width_mm": float(big.axis_minor_length * sp),
           "hu": [float(h) for h in big.moments_hu[:3]]}
    return out


def _metrics_3d(mask: np.ndarray, sp) -> dict:
    from geovida import reference as ref
    from geovida.measure import measure_mask
    from geovida.topology import betti_numbers
    m = measure_mask(mask, sp)
    b26, b6 = betti_numbers(mask, 26), betti_numbers(mask, 6)
    return {"volume_mm3": m["volume"], "area_sdf_mm2": m["area_sdf"], "area_crofton_mm2": ref.crofton_area(mask, sp),
            "betti26": list(b26.as_tuple()), "chi26": b26.chi, "betti6": list(b6.as_tuple()), "chi6": b6.chi,
            "voxels": int(mask.sum())}


def _crop(mask, margin=4):
    idx = np.argwhere(mask)
    lo = np.maximum(idx.min(0) - margin, 0)
    hi = np.minimum(idx.max(0) + margin + 1, mask.shape)
    return tuple(slice(a, b) for a, b in zip(lo, hi))


def _mesh(mask: np.ndarray, sp, step: int, center_mm: np.ndarray, sigma: float = 0.8) -> dict:
    """Malla en mm, en el sistema de coordenadas común definido por ``center_mm`` (centroide del cuerpo),
    para que el cuerpo y los ventrículos conserven su posición relativa real."""
    from scipy import ndimage as ndi
    from skimage.measure import marching_cubes
    sl = _crop(mask, 3)
    m = ndi.gaussian_filter(mask[sl].astype(np.float32), sigma)
    v, f, _, _ = marching_cubes(m, 0.5, spacing=tuple(sp), step_size=step)
    v = v + np.array([s.start for s in sl]) * np.asarray(sp) - center_mm
    return {"vertices": np.round(v, 4).ravel().tolist(), "faces": f.astype(int).ravel().tolist(),
            "n_vertices": int(len(v)), "n_faces": int(len(f)), "step": step, "smoothing_sigma_vox": sigma}


def _downsample(mask: np.ndarray, f: int) -> np.ndarray:
    if f == 1:
        return mask
    s = [d - d % f for d in mask.shape]
    m = mask[:s[0], :s[1], :s[2]].astype(np.float32)
    m = m.reshape(s[0] // f, f, s[1] // f, f, s[2] // f, f).mean(axis=(1, 3, 5))
    return m > 0.5


def pipeline(root: Path, manifest: Path, out: Path, data: dict):
    import nibabel as nib
    import pandas as pd
    from geovida.segment import segment
    plt = _plt()
    man = pd.read_csv(manifest)
    first = man.iloc[0]
    body_row = man[(man.image == first.image) & (man.structure == "body")].iloc[0]
    ven_row = man[(man.image == first.image) & (man.structure == "ventricle")].iloc[0]
    img_nii = nib.load(str(root / first.image))
    sp = tuple(float(z) for z in img_nii.header.get_zooms()[:3])
    image = np.asarray(img_nii.dataobj, dtype=np.float32)
    body = np.asarray(nib.load(str(root / body_row.label)).dataobj) == int(body_row.label_value)
    ven = np.asarray(nib.load(str(root / ven_row.label)).dataobj) == int(ven_row.label_value)
    k = int(np.argmax(body.sum(axis=(0, 1))))
    segs = {name: segment(name, image, sp) for name in ("global", "otsu", "smoothed_otsu")}
    fig, axs = plt.subplots(1, 5, figsize=(15, 3.6))
    show = lambda a: np.asarray(a[:, :, k]).T
    panels = [("1 · Imagen original", None, None), ("2 · Referencia (personas)", body, ACCENT),
              ("3 · Umbral global", segs["global"], ACCENT2), ("4 · Otsu", segs["otsu"], ACCENT2),
              ("5 · Otsu suavizado", segs["smoothed_otsu"], ACCENT2)]
    for ax, (title, m, col) in zip(axs, panels):
        ax.imshow(_window(show(image)), cmap="gray", origin="lower", interpolation="lanczos")
        if m is not None:
            ax.contour(show(m), levels=[0.5], colors=[col], linewidths=1.1, origin="lower")
        if title.startswith("2"):
            ax.contour(show(ven), levels=[0.5], colors=[ACCENT3], linewidths=1.0, origin="lower")
        ax.set_title(title, color=FG, fontsize=10, loc="left")
        ax.set_axis_off()
    fig.text(0.01, 0.02, f"Embrión de ratón E11 ({Path(first.image).name}), corte z = {k}, vóxel {sp[0] * 1000:.0f} µm. "
             "Turquesa: cuerpo (referencia); violeta: ventrículos (referencia); naranja: segmentación de geovida. "
             "Qiu et al. 2021, CC BY.", color=MUTED, fontsize=8)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(out / "pipeline_real.png", dpi=100)
    plt.close(fig)
    data["pipeline"] = {"image": Path(first.image).name, "embryo_id": first.embryo_id, "slice_z": k,
                        "spacing_mm": sp, "shape": list(image.shape),
                        "slice_2d_reference_body": _metrics_2d(show(body), sp[0]),
                        "volume_3d_reference_body": _metrics_3d(body, sp),
                        "volume_3d_reference_ventricle": _metrics_3d(ven, sp),
                        "volume_3d_segmented": {n: _metrics_3d(m, sp) for n, m in segs.items()}}
    center = np.argwhere(body).mean(axis=0) * np.asarray(sp)
    (out / "mesh_body.json").write_text(json.dumps(_mesh(body, sp, step=3, center_mm=center)), encoding="utf-8")
    (out / "mesh_ventricle.json").write_text(json.dumps(_mesh(ven, sp, step=2, center_mm=center)), encoding="utf-8")
    return body, sp


def h11_case(cache: Path, image_name: str, data: dict):
    keep = ("structure", "segmenter", "volume_mm3_measured", "volume_mm3_reference", "rel_error_volume", "dice",
            "betti_measured", "betti_reference", "p_volume", "light_volume", "light_volume_without_guard",
            "in_domain_volume", "light_topology", "d_over_hgeo")
    rows = [json.loads(l) for l in cache.read_text(encoding="utf-8").splitlines()[1:]]
    data["h11_case"] = [{k: r[k] for k in keep} for r in rows if Path(r["image"]).name == image_name]


def resolution(body: np.ndarray, sp, out: Path, data: dict):
    plt = _plt()
    sl = _crop(body, 6)
    m0 = body[sl]
    rows = []
    for f in (1, 2, 3, 4):
        m = _downsample(m0, f)
        r = _metrics_3d(m, tuple(s * f for s in sp))
        r["factor"] = f
        r["voxel_um"] = sp[0] * f * 1000
        rows.append(r)
    data["resolution"] = rows
    v0, a0 = rows[0]["volume_mm3"], rows[0]["area_crofton_mm2"]
    fig, ax = plt.subplots(1, 1, figsize=(6.4, 3.4))
    x = [r["voxel_um"] for r in rows]
    ax.plot(x, [100 * (r["volume_mm3"] / v0 - 1) for r in rows], "o-", color=ACCENT, label="Volumen")
    ax.plot(x, [100 * (r["area_crofton_mm2"] / a0 - 1) for r in rows], "s-", color=ACCENT2, label="Área (Crofton)")
    for r in rows:
        ax.annotate(f"β = {tuple(r['betti26'])}", (r["voxel_um"], 100 * (r["area_crofton_mm2"] / a0 - 1)),
                    textcoords="offset points", xytext=(4, -14), color=MUTED, fontsize=8)
    ax.axhline(0, color="#24303c")
    ax.set_xlabel("Tamaño de vóxel (µm)")
    ax.set_ylabel("Cambio frente a 50 µm (%)")
    ax.legend(frameon=False, labelcolor=FG)
    ax.set_title("La misma referencia real, medida a otra resolución", color=FG, loc="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(out / "resolution_real.png", dpi=110)
    plt.close(fig)


def euler(out: Path, data: dict):
    from geovida.topology import betti_numbers
    from geovida.twod import betti_2d
    from skimage.measure import marching_cubes
    plt = _plt()
    n = 48
    yy, xx = np.mgrid[:n, :n] - (n - 1) / 2
    r2 = xx ** 2 + yy ** 2
    ex2 = {"Región sin agujeros": r2 <= 18 ** 2,
           "Dos componentes": ((xx + 11) ** 2 + yy ** 2 <= 8 ** 2) | ((xx - 11) ** 2 + yy ** 2 <= 8 ** 2),
           "Un ciclo (anillo)": (r2 <= 18 ** 2) & (r2 >= 9 ** 2)}
    m3 = 36
    zz, y3, x3 = np.mgrid[:m3, :m3, :m3] - (m3 - 1) / 2
    R = np.sqrt(x3 ** 2 + y3 ** 2 + zz ** 2)
    torus = (np.sqrt(x3 ** 2 + y3 ** 2) - 10) ** 2 + zz ** 2 <= 4.5 ** 2
    ex3 = {"Túnel (toro)": torus, "Cavidad cerrada (cáscara)": (R <= 15) & (R >= 9)}
    fig = plt.figure(figsize=(15, 4.0))
    res = []
    for i, (name, m) in enumerate(ex2.items()):
        ax = fig.add_subplot(1, 5, i + 1)
        ax.imshow(m, cmap="Blues_r" if False else "gray", interpolation="nearest")
        b = betti_2d(m, 8)
        chi = b.b0 - b.b1
        ax.set_title(f"{name}\nβ0={b.b0}  β1={b.b1}  χ={chi}", color=FG, fontsize=9.5, loc="left")
        ax.set_axis_off()
        res.append({"name": name, "dim": 2, "betti": [b.b0, b.b1], "chi": chi})
    for j, (name, m) in enumerate(ex3.items()):
        ax = fig.add_subplot(1, 5, 4 + j, projection="3d")
        mm = m.copy()
        if "cáscara" in name:
            mm[:, :, : m3 // 2] = False  # se corta por la mitad solo para VER la cavidad; Betti se mide entera
        v, f, _, _ = marching_cubes(mm.astype(np.float32), 0.5)
        ax.plot_trisurf(v[:, 0], v[:, 1], f, v[:, 2], color=ACCENT, alpha=0.85, linewidth=0)
        ax.view_init(elev=38, azim=30)
        ax.set_axis_off()
        ax.set_facecolor(BG)
        b = betti_numbers(m, 26)
        ax.set_title(f"{name}\nβ=({b.b0},{b.b1},{b.b2})  χ={b.chi}", color=FG, fontsize=9.5, loc="left")
        res.append({"name": name, "dim": 3, "betti": list(b.as_tuple()), "chi": b.chi})
    fig.text(0.01, 0.02, "Ilustración sintética (no son embriones). Valores calculados por geovida: twod.betti_2d "
             "(conectividad 8/4) y topology.betti_numbers (26/6). La cáscara se dibuja cortada; se midió cerrada.",
             color=MUTED, fontsize=8)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.80, bottom=0.08, wspace=0.08)
    fig.savefig(out / "euler_examples.png", dpi=100)
    plt.close(fig)
    data["euler"] = res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="docs/exposicion/img")
    ap.add_argument("--root", default="data/external/ieee_qiu2021/nii")
    ap.add_argument("--manifest", default="results/h11/manifiesto_qiu2021.csv")
    ap.add_argument("--cache", default="results/h11/cache_v04.jsonl")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    data = {}
    body, sp = pipeline(Path(a.root), Path(a.manifest), out, data)
    h11_case(Path(a.cache), data["pipeline"]["image"], data)
    resolution(body, sp, out, data)
    euler(out, data)
    (out / "final_data.json").write_text(json.dumps(data, indent=1, ensure_ascii=False, default=float) + "\n",
                                         encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in data.items()}, ensure_ascii=False, default=float)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
