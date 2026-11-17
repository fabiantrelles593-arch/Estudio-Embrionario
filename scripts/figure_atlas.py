"""Figuras del atlas de especímenes reales para la exposición (sin copiar números a mano).

    python scripts/figure_atlas.py --out docs/exposicion/img

Lee corte a corte (sin cargar volúmenes enteros) los datos que ya están en ``data/external`` y que
tienen licencia CC BY verificada:

* MusMorph / IMPC E15.5, micro-CT y segmentación publicada (FaceBase 3-JZA6, CC BY 4.0).
* Qiu et al. 2021, ecografía 3D de alta frecuencia de embrión de ratón (IEEE DataPort, CC BY).
* Landmarks de cabeza de MusMorph (E15.5 y E18.5) para el mapa de ONTO-MAP.

No usa las salidas de MEMOS (sus pesos tienen licencia no declarada). Todo es animal; nada humano.
Las figuras son ilustrativas: no son resultados nuevos ni sustituyen los documentos de resultados.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

BG, FG, MUTED, ACCENT, ACCENT2 = "#0b1016", "#e6edf3", "#8b98a5", "#3fd0c9", "#f2a541"


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
                         "text.color": FG, "axes.labelcolor": MUTED, "xtick.color": MUTED,
                         "ytick.color": MUTED, "axes.edgecolor": "#24303c", "font.size": 10})
    return plt


def _window(a: np.ndarray, lo=1.0, hi=99.5) -> np.ndarray:
    a = a.astype(np.float32)
    p0, p1 = np.percentile(a, [lo, hi])
    return np.clip((a - p0) / max(p1 - p0, 1e-6), 0, 1)


# ---------------------------------------------------------------- MINC (MusMorph)
class MincSlices:
    """Cortes de un MINC2 (HDF5) con la escala real por corte (image-min / image-max)."""

    def __init__(self, path: Path):
        import h5py
        self.h = h5py.File(path, "r")
        g = self.h["minc-2.0/image/0"]
        self.d = g["image"]
        self.shape = self.d.shape
        self.real = self.d.dtype.kind in "iu"
        if self.real:
            info = np.iinfo(self.d.dtype)
            self.vmin, self.vmax = float(info.min), float(info.max)
            self.lo = np.asarray(g["image-min"][()], dtype=np.float64).reshape(-1)
            self.hi = np.asarray(g["image-max"][()], dtype=np.float64).reshape(-1)

    def _scale(self, raw: np.ndarray, zs) -> np.ndarray:
        if not self.real:
            return raw.astype(np.float32)
        lo = self.lo[zs] if self.lo.size > 1 else self.lo[0]
        hi = self.hi[zs] if self.hi.size > 1 else self.hi[0]
        f = (raw.astype(np.float64) - self.vmin) / (self.vmax - self.vmin)
        if np.ndim(lo):
            lo, hi = lo[:, None], hi[:, None]
        return (lo + f * (hi - lo)).astype(np.float32)

    def axial(self, z):
        return self._scale(self.d[z], z)

    def coronal(self, y):
        return self._scale(self.d[:, y, :], slice(None))

    def sagittal(self, x):
        return self._scale(self.d[:, :, x], slice(None))


def _boundaries(lab: np.ndarray) -> np.ndarray:
    from skimage.segmentation import find_boundaries
    return find_boundaries(lab, mode="inner")


def _clean_labels(raw: np.ndarray) -> np.ndarray:
    """Solo para mostrar: vóxeles con etiqueta exacta (los interpolados pasan a 0, regla «exact» de D1),
    huecos rellenados con un filtro de moda 3×3 y sin islas de menos de 25 píxeles."""
    from scipy import ndimage
    r = np.rint(raw)
    lab = np.where(np.abs(raw - r) < 0.02, r, 0).astype(np.int32)
    filled = ndimage.generic_filter(lab, lambda w: np.bincount(w.astype(np.int64)).argmax(), size=3)
    lab = np.where(lab > 0, lab, filled)
    out = np.zeros_like(lab)
    for v in np.unique(lab[lab > 0]):
        cc, n = ndimage.label(lab == v)
        if n:
            sizes = ndimage.sum(np.ones_like(cc), cc, range(1, n + 1))
            keep = np.isin(cc, 1 + np.flatnonzero(sizes >= 25))
            out[keep] = v
    return out


def _bbox(img: np.ndarray, margin=12):
    w = _window(img)
    ys, xs = np.nonzero(w > 0.18)
    if ys.size == 0:
        return slice(None), slice(None)
    return (slice(max(ys.min() - margin, 0), ys.max() + margin),
            slice(max(xs.min() - margin, 0), xs.max() + margin))


def _overlay(ax, img, lab, title):
    cy, cx = _bbox(img)
    img = img[cy, cx]
    ax.imshow(_window(img), cmap="gray", interpolation="lanczos")
    if lab is not None:
        lab = _clean_labels(lab[cy, cx])
        rgba = np.zeros(lab.shape + (4,), np.float32)
        cmap = __import__("matplotlib").colormaps["tab20"]
        for v in np.unique(lab[lab > 0]):
            m = lab == v
            c = cmap((int(v) * 7) % 20)
            rgba[m] = (*c[:3], 0.30)
            rgba[_boundaries(m)] = (*c[:3], 0.95)
        ax.imshow(rgba, interpolation="nearest")
    ax.set_title(title, color=FG, fontsize=11, loc="left")
    ax.set_axis_off()


def musmorph_hero(img_path: Path, seg_path: Path, out: Path):
    """Un solo corte sagital grande con la segmentación coloreada (portada)."""
    plt = _plt()
    im, sg = MincSlices(img_path), MincSlices(seg_path)
    nx = im.shape[2]
    fig, ax = plt.subplots(figsize=(5.2, 7.2))
    _overlay(ax, im.sagittal(nx // 2), sg.sagittal(nx // 2), "")
    fig.tight_layout(pad=0.2)
    fig.savefig(out, dpi=110)
    plt.close(fig)
    im.h.close(), sg.h.close()
    return {"file": out.name}


def musmorph_compare(items, out: Path):
    """Contorno de la unión de todas las etiquetas sobre la imagen: alineada frente a desplazada (D3)."""
    plt = _plt()
    fig, axs = plt.subplots(1, 2 * len(items), figsize=(13, 4.5),
                            gridspec_kw={"width_ratios": [0.55, 1] * len(items)})
    axs = np.asarray(axs).reshape(len(items), 2)
    rows = []
    for r, (img_path, seg_path, label, note) in enumerate(items):
        im, sg = MincSlices(img_path), MincSlices(seg_path)
        nz, ny, nx = im.shape
        for c, (name, a, b) in enumerate([("Coronal", im.coronal(ny // 2), sg.coronal(ny // 2)),
                                          ("Sagital", im.sagittal(nx // 2), sg.sagittal(nx // 2))]):
            cy, cx = _bbox(a)
            ax = axs[r, c]
            ax.imshow(_window(a[cy, cx]), cmap="gray", interpolation="lanczos")
            ax.contour(b[cy, cx] > 0.5, levels=[0.5], colors=[ACCENT if r == 0 else ACCENT2], linewidths=1.3)
            ax.set_title(f"{label} · {name}", color=FG, fontsize=11, loc="left")
            ax.set_axis_off()
        axs[r, 0].text(0, -0.02, note, transform=axs[r, 0].transAxes, color=MUTED, fontsize=9, va="top")
        rows.append({"specimen": label})
        im.h.close(), sg.h.close()
    fig.suptitle("Borde de la segmentación publicada (todas las estructuras) sobre su propia imagen",
                 x=0.01, ha="left", color=FG, fontsize=12)
    fig.text(0.01, 0.01, "MusMorph/IMPC, FaceBase 3-JZA6, CC BY 4.0 (Devine et al. 2022). Desfase medido en "
             "docs/p3/RESULTADOS_PILOTO.md (D3).", color=MUTED, fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(out, dpi=100)
    plt.close(fig)
    return {"file": out.name, "panels": rows}


def musmorph_specimen(img_path: Path, seg_path: Path, out: Path, label: str, note: str):
    plt = _plt()
    im, sg = MincSlices(img_path), MincSlices(seg_path)
    nz, ny, nx = im.shape
    step = float(im.h["minc-2.0/dimensions/xspace"].attrs["step"])
    views = [("Axial", im.axial(nz // 2), sg.axial(nz // 2)),
             ("Coronal", im.coronal(ny // 2), sg.coronal(ny // 2)),
             ("Sagital", im.sagittal(nx // 2), sg.sagittal(nx // 2))]
    fig, axs = plt.subplots(1, 3, figsize=(12, 4.6))
    for ax, (name, a, b) in zip(axs, views):
        _overlay(ax, a, b, name)
    fig.suptitle(f"{label} · micro-CT con la segmentación publicada superpuesta", x=0.01, ha="left",
                 color=FG, fontsize=12)
    fig.text(0.01, 0.015, f"{note}  Vóxel {step * 1000:.0f} µm · {nz}×{ny}×{nx} vóxeles. MusMorph/IMPC, "
             "FaceBase 3-JZA6, CC BY 4.0 (Devine et al. 2022).", color=MUTED, fontsize=8)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(out, dpi=100)
    plt.close(fig)
    im.h.close(), sg.h.close()
    return {"file": out.name, "specimen": label, "shape": [nz, ny, nx], "voxel_mm": step}


# ---------------------------------------------------------------- NIfTI (Qiu 2021)
def _best_slice(lab_proxy, axis=2, every=6):
    n = lab_proxy.shape[axis]
    best, area = n // 2, -1
    for k in range(0, n, every):
        sl = [slice(None)] * 3
        sl[axis] = k
        a = int((np.asarray(lab_proxy[tuple(sl)]) > 0).sum())
        if a > area:
            best, area = k, a
    return best


def qiu_series(root: Path, manifest: Path, out: Path):
    import nibabel as nib
    import pandas as pd
    plt = _plt()
    man = pd.read_csv(manifest)
    body = man[man["structure"] == "body"].copy()
    body["stage"] = body["image"].str.extract(r"/(E\d+(?:\.5)?)/")[0]
    picks = body.groupby("stage", sort=True).head(1)
    picks = picks.sort_values("stage", key=lambda s: s.str[1:].astype(float))
    fig, axs = plt.subplots(1, len(picks), figsize=(2.6 * len(picks), 3.4))
    axs = np.atleast_1d(axs)
    rows = []
    for ax, (_, r) in zip(axs, picks.iterrows()):
        img = nib.load(str(root / r["image"]))
        lb = nib.load(str(root / r["label"]))
        bv_path = root / r["label"].replace("_BODY_labels", "_BV_labels")
        k = _best_slice(lb.dataobj)
        a = np.asarray(img.dataobj[:, :, k]).T
        b = np.asarray(lb.dataobj[:, :, k]).T > 0
        ax.imshow(_window(a), cmap="gray", origin="lower", interpolation="lanczos")
        ax.contour(b, levels=[0.5], colors=[ACCENT], linewidths=1.2, origin="lower")
        if bv_path.exists():
            v = np.asarray(nib.load(str(bv_path)).dataobj[:, :, k]).T > 0
            if v.any():
                ax.contour(v, levels=[0.5], colors=[ACCENT2], linewidths=1.0, origin="lower")
        ax.set_title(r["stage"], color=FG, fontsize=11, loc="left")
        ax.set_axis_off()
        rows.append({"stage": r["stage"], "image": Path(r["image"]).name, "slice": int(k)})
    fig.suptitle("Ecografía 3D de alta frecuencia: un embrión distinto por estadio (transversal, no el mismo "
                 "embrión en el tiempo)", x=0.01, ha="left", color=FG, fontsize=11)
    fig.text(0.01, 0.02, "Contorno turquesa: cuerpo; naranja: ventrículos cerebrales (referencias dibujadas por "
             "personas). Qiu et al. 2021, IEEE DataPort, CC BY.", color=MUTED, fontsize=8)
    fig.tight_layout(rect=(0, 0.06, 1, 0.9))
    fig.savefig(out, dpi=100)
    plt.close(fig)
    return {"file": out.name, "panels": rows}


# ---------------------------------------------------------------- Landmarks (ONTO-MAP)
def ontomap_map(lm_dir: Path, out: Path):
    from geovida import landmarks as L
    plt = _plt()
    files = sorted(lm_dir.glob("IMPC_E1*_Head_Landmarks.tag"))
    configs, stage = [], []
    for f in files:
        x = L.read_tag(f)
        if x.shape[0] == 540:
            configs.append(x)
            stage.append("E15.5" if "E15.5" in f.name else "E18.5")
    g = L.gpa(configs)
    aligned, mean = g["aligned"], g["mean"]
    t, _ = L.tangent_coordinates(aligned, mean)
    t = t - t.mean(axis=0)
    u, s, vt = np.linalg.svd(t, full_matrices=False)
    pcs = u[:, :2] * s[:2]
    var = (s ** 2) / (s ** 2).sum()
    st = np.array(stage)
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1, 1.15]})
    for lab, col in (("E15.5", ACCENT), ("E18.5", ACCENT2)):
        m = st == lab
        axs[0].scatter(pcs[m, 0], pcs[m, 1], s=7, alpha=0.6, color=col, label=f"{lab} (n = {m.sum()})")
    axs[0].set_xlabel(f"CP1 de forma ({100 * var[0]:.0f} % de la varianza)")
    axs[0].set_ylabel(f"CP2 ({100 * var[1]:.0f} %)")
    axs[0].legend(frameon=False, labelcolor=FG)
    axs[0].set_title("Espacio de forma (Procrustes + CP)", color=FG, loc="left")
    m15 = aligned[st == "E15.5"].mean(axis=0)
    m18 = aligned[st == "E18.5"].mean(axis=0)
    # proyección sobre los dos ejes de mayor extensión de la forma media
    c = mean - mean.mean(axis=0)
    _, _, ax_v = np.linalg.svd(c, full_matrices=False)
    p15, p18 = m15 @ ax_v[:2].T, m18 @ ax_v[:2].T
    axs[1].scatter(p15[:, 0], p15[:, 1], s=6, color=ACCENT, label="Forma media E15.5")
    axs[1].scatter(p18[:, 0], p18[:, 1], s=6, color=ACCENT2, label="Forma media E18.5")
    k = np.linspace(0, len(p15) - 1, 45).astype(int)
    d = (p18 - p15)[k] * 1.5
    axs[1].quiver(p15[k, 0], p15[k, 1], d[:, 0], d[:, 1], angles="xy", scale_units="xy", scale=1,
                  color=FG, width=0.0025, alpha=0.8)
    axs[1].set_aspect("equal")
    axs[1].set_axis_off()
    axs[1].legend(frameon=False, labelcolor=FG, loc="lower right")
    axs[1].set_title("540 landmarks de cabeza: forma media (flechas ×1,5)", color=FG, loc="left")
    fig.text(0.01, 0.015, "Los estadios se separan, pero cada uno se registró a su propio atlas: la separación no se "
             "atribuye al desarrollo (ver RESULTADOS_P4). Landmarks MusMorph/IMPC, CC BY 4.0.",
             color=MUTED, fontsize=8)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(out, dpi=100)
    plt.close(fig)
    return {"file": out.name, "n": {"E15.5": int((st == "E15.5").sum()), "E18.5": int((st == "E18.5").sum())},
            "var_pc1": float(var[0]), "var_pc2": float(var[1])}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="docs/exposicion/img")
    ap.add_argument("--only", choices=["hero", "musmorph", "qiu", "ontomap"], action="append")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    mm = Path("data/external/musmorph/impc_e15_5")
    todo = set(a.only or ["hero", "musmorph", "qiu", "ontomap"])
    info_path = out / "atlas_info.json"
    info = json.loads(info_path.read_text(encoding="utf-8")) if info_path.exists() else {}
    if "hero" in todo:
        info["hero_0218"] = musmorph_hero(mm / "IMPC_E15.5_0218.mnc", mm / "IMPC_E15.5_0218_Segs.mnc",
                                          out / "hero_0218.png")
    if "musmorph" in todo:
        info["musmorph_0218"] = musmorph_specimen(
            mm / "IMPC_E15.5_0218.mnc", mm / "IMPC_E15.5_0218_Segs.mnc", out / "musmorph_0218.png",
            "IMPC E15.5 · espécimen 0218", "Segmentación alineada (desfase de 1 vóxel).")
        info["musmorph_0040"] = musmorph_compare([
            (mm / "IMPC_E15.5_0218.mnc", mm / "IMPC_E15.5_0218_Segs.mnc", "0218",
             "Alineada:\ntraslación de 1 vóxel (27 µm)"),
            (mm / "IMPC_E15.5_0040.mnc", mm / "IMPC_E15.5_0040_Segs.mnc", "0040",
             "Desplazada:\n(16, 6, −4) vóxeles ≈ 0,47 mm")], out / "musmorph_0040.png")
    if "qiu" in todo:
        info["qiu_series"] = qiu_series(Path("data/external/ieee_qiu2021/nii"),
                                        Path("results/h11/manifiesto_qiu2021.csv"), out / "qiu_series.png")
    if "ontomap" in todo:
        info["ontomap"] = ontomap_map(Path("data/external/musmorph/landmarks_confirm"), out / "ontomap_map.png")
    info_path.write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(info, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
