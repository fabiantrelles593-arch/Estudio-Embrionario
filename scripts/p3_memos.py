"""P3 — Segmentador B: MEMOS (Rolfe et al. 2023, doi:10.1242/bio.059698) sin 3D Slicer.

Código propio (MIT). Reproduce la configuración publicada de MEMOS (SlicerMEMOS, BSD-2-Clause):
UNETR de MONAI (in=1, out=51, img 128³, feature 16, hidden 768, mlp 3072, 12 cabezas,
proyección «perceptron», norma de instancia, bloque residual), intensidad reescalada a 0–255 y
después a [0, 1] con a_min=-175 y a_max=250, ventana deslizante de 128³ con solapamiento 0,8,
promedio constante y argmax de los logits. Los pesos (`best_metric_model_largePatch_noise.pth`)
se descargan del enlace del README de SlicerMEMOS; su licencia no está declarada, así que
**no se redistribuyen** y quedan en `data/external/memos/` (fuera de git).

Desviación D2 del preregistro de P3 (§11):
- MEMOS se entrenó con la versión de baja resolución de IMPC (~250×250×400 vóxeles). Los
  volúmenes de MusMorph tienen el doble de resolución, así que la entrada se reduce por promedio
  de bloques de 2 (`--factor 2`).
- Los logits promediados se amplían de forma trilineal a la rejilla nativa antes del argmax, para
  no fabricar bordes en escalera que inflarían la variación técnica de las estructuras finas.
- Solo se procesa la caja del cuerpo (umbral de Otsu + 16 vóxeles de margen) y la ventana
  deslizante se acumula por franjas, para caber en ~4 GB de RAM.

Desviación D3: las segmentaciones de MusMorph están trasladadas respecto a su imagen. `compare`
informa el acuerdo sin trasladar y tras la mejor traslación entera (`best_translation`).

Uso:
  python scripts/p3_memos.py run --model data/external/memos/model/best_metric_model_largePatch_noise.pth \
      --data data/external/musmorph/impc_e15_5 --ids results/p3/seleccion.json --out results/p3/memos
  python scripts/p3_memos.py compare --data ... --out results/p3/memos

Solo investigación; no es una herramienta clínica.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

ROI = 128
OVERLAP = 0.8
N_CLASSES = 51
A_MIN, A_MAX = -175.0, 250.0


# ---------------------------------------------------------------- utilidades sin torch
def window_starts(size: int, roi: int = ROI, overlap: float = OVERLAP) -> list[int]:
    """Inicios de ventana en un eje, con la misma regla que MONAI `dense_patch_slices`."""
    if size <= roi:
        return [0]
    interval = max(int(roi * (1 - overlap)), 1)
    n = math.ceil((size - roi) / interval) + 1
    return sorted({min(i * interval, size - roi) for i in range(n)})


def block_mean(arr: np.ndarray, f: int) -> np.ndarray:
    """Promedio de bloques f×f×f (recorta el resto)."""
    if f == 1:
        return arr.astype(np.float32, copy=False)
    s = [d // f * f for d in arr.shape]
    a = arr[: s[0], : s[1], : s[2]]
    return a.reshape(s[0] // f, f, s[1] // f, f, s[2] // f, f).mean(axis=(1, 3, 5), dtype=np.float32)


def memos_intensity(arr: np.ndarray, lo: float, hi: float) -> np.ndarray:
    """Reescala [lo, hi] → [0, 255] (como SlicerMEMOS) y después ScaleIntensityRange(-175, 250, 0, 1, clip)."""
    v = (arr.astype(np.float32) - lo) * (255.0 / max(hi - lo, 1e-12))
    return np.clip((v - A_MIN) / (A_MAX - A_MIN), 0.0, 1.0).astype(np.float32)


def otsu(x: np.ndarray, bins: int = 256) -> float:
    h, e = np.histogram(x, bins=bins)
    c = (e[:-1] + e[1:]) / 2
    w = np.cumsum(h)
    m = np.cumsum(h * c)
    wf = w[-1] - w
    var = (m[-1] * w / w[-1] - m) ** 2 / np.maximum(w * wf, 1)
    return float(c[np.argmax(var)])


def body_box(vol: np.ndarray, margin: int = 16, min_size: int = ROI) -> tuple[slice, ...]:
    """Caja del mayor componente sobre el umbral de Otsu, con margen y tamaño mínimo `min_size`."""
    from scipy import ndimage

    m = ndimage.binary_opening(vol > otsu(vol[::2, ::2, ::2].ravel()), iterations=2)
    lab, n = ndimage.label(m)
    if n == 0:
        return tuple(slice(0, d) for d in vol.shape)
    sz = np.bincount(lab.ravel())
    sz[0] = 0
    m = lab == sz.argmax()
    box = []
    for ax, dim in enumerate(vol.shape):
        idx = np.where(m.any(axis=tuple(j for j in range(3) if j != ax)))[0]
        a, b = max(int(idx[0]) - margin, 0), min(int(idx[-1]) + 1 + margin, dim)
        while b - a < min(min_size, dim):
            a, b = max(a - 1, 0), min(b + 1, dim)
        box.append(slice(a, b))
    return tuple(box)


def sliding_mean_logits(vol: np.ndarray, predictor, n_classes: int, out: np.ndarray,
                        roi: int = ROI, overlap: float = OVERLAP, log=None) -> int:
    """Media constante de los logits de la ventana deslizante, acumulada por franjas del eje 0.

    `predictor(patch[roi,roi,roi]) -> logits[n_classes,roi,roi,roi]` (mismo orden de ejes que `vol`).
    `out` (n_classes, *vol.shape) recibe la media; puede ser un memmap en disco. Equivale a la
    media de MONAI `sliding_window_inference(mode="constant")` sin guardar el volumen entero en RAM.
    Devuelve el número de ventanas evaluadas.
    """
    if any(d < roi for d in vol.shape):
        raise ValueError(f"volumen {vol.shape} menor que la ventana {roi}")
    s0, s1, s2 = (window_starts(d, roi, overlap) for d in vol.shape)
    _, n1, n2 = vol.shape
    acc = np.zeros((n_classes, roi, n1, n2), np.float32)
    cnt = np.zeros((roi, n1, n2), np.float32)
    base = s0[0]  # fila global de acc[ :, 0]
    n_win, t0 = 0, time.time()
    total = len(s0) * len(s1) * len(s2)
    for t, z in enumerate(s0):
        shift = z - base  # desplazar la franja para que empiece en z
        if shift:
            done = slice(base, z)
            out[:, done] = (acc[:, :shift] / np.maximum(cnt[:shift], 1e-6)).astype(out.dtype)
            acc[:, :-shift] = acc[:, shift:]
            acc[:, -shift:] = 0
            cnt[:-shift] = cnt[shift:]
            cnt[-shift:] = 0
            base = z
        for y in s1:
            for x in s2:
                acc[:, :, y:y + roi, x:x + roi] += predictor(vol[z:z + roi, y:y + roi, x:x + roi])
                cnt[:, y:y + roi, x:x + roi] += 1
                n_win += 1
                if log and n_win % 10 == 0:
                    el = time.time() - t0
                    log(f"  ventana {n_win}/{total} · {el / n_win:.1f} s/ventana")
    out[:, base:base + roi] = (acc / np.maximum(cnt, 1e-6)).astype(out.dtype)
    return n_win

def upsample_argmax(logits: np.ndarray, factor: int, slab: int = 4) -> np.ndarray:
    """Amplía logits (C, Z, Y, X) por `factor` (trilineal, align_corners=False) y aplica argmax.

    Se hace por franjas del eje 0 con una fila de contexto a cada lado, de modo que el resultado
    es idéntico al de interpolar el volumen entero.
    """
    if factor == 1:
        return np.asarray(logits).argmax(axis=0).astype(np.uint8)
    import torch
    import torch.nn.functional as F

    c, z, y, x = logits.shape
    out = np.empty((z * factor, y * factor, x * factor), np.uint8)
    for a in range(0, z, slab):
        b = min(a + slab, z)
        lo, hi = max(a - 1, 0), min(b + 1, z)
        t = torch.from_numpy(np.asarray(logits[:, lo:hi], dtype=np.float32))[None]
        # con align_corners=False, la fila de salida 2·lo + o' cae en la misma coordenada de
        # entrada que en el volumen completo; la fila de contexto evita el sujetado en el corte
        up = F.interpolate(t, scale_factor=factor, mode="trilinear", align_corners=False)
        off = (a - lo) * factor
        out[a * factor:b * factor] = up[0, :, off:off + (b - a) * factor].argmax(0).numpy().astype(np.uint8)
    return out


# ---------------------------------------------------------------- MEMOS
def build_memos(model_path: str | Path, threads: int = 4):
    import torch
    from monai.networks.nets import UNETR

    torch.set_num_threads(threads)
    net = UNETR(in_channels=1, out_channels=N_CLASSES, img_size=(ROI, ROI, ROI), feature_size=16,
                hidden_size=768, mlp_dim=3072, num_heads=12, proj_type="perceptron",
                norm_name="instance", res_block=True, dropout_rate=0.0)
    sd = torch.load(str(model_path), map_location="cpu", weights_only=True)
    missing, unexpected = net.load_state_dict(sd, strict=False)
    bad = [k for k in missing if "cross_attn" not in k]
    if bad or unexpected:
        raise RuntimeError(f"pesos incompatibles: faltan {bad[:5]}, sobran {unexpected[:5]}")
    net.eval()

    def predictor(patch: np.ndarray) -> np.ndarray:
        # nuestros arreglos están en orden (k, j, i); MONAI ve (i, j, k) en RAS
        t = torch.from_numpy(np.ascontiguousarray(patch.transpose(2, 1, 0)))[None, None]
        with torch.inference_mode():
            o = net(t)[0].numpy()
        return o.transpose(0, 3, 2, 1)

    return predictor


def segment_volume(img: np.ndarray, predictor, factor: int, workdir: Path, log=print) -> tuple[np.ndarray, tuple[slice, ...], dict]:
    """Etiquetas MEMOS (uint8, 0 = fondo, 1–50 = KOMP2) en la caja del cuerpo de la rejilla nativa."""
    lo, hi = float(img.min()), float(img.max())
    ds = memos_intensity(block_mean(img, factor), lo, hi)
    box = body_box(ds)
    vol = np.ascontiguousarray(ds[box])
    del ds
    mm = np.lib.format.open_memmap(workdir / "logits.npy", mode="w+", dtype=np.float16,
                                   shape=(N_CLASSES, *vol.shape))
    t0 = time.time()
    n = sliding_mean_logits(vol, predictor, N_CLASSES, mm, log=log)
    t_inf = time.time() - t0
    mm.flush()
    lab = upsample_argmax(mm, factor)
    del mm
    (workdir / "logits.npy").unlink(missing_ok=True)
    full_box = tuple(slice(s.start * factor, s.start * factor + lab.shape[i]) for i, s in enumerate(box))
    info = {"factor": factor, "box_native": [[s.start, s.stop] for s in full_box],
            "grid_input": list(vol.shape), "windows": n, "seconds_inference": round(t_inf, 1),
            "intensity_minmax": [lo, hi]}
    return lab, full_box, info


def dice_table(memos: np.ndarray, atlas: np.ndarray) -> dict:
    """Para cada etiqueta del atlas: etiqueta MEMOS de mayor solapamiento y Dice con ella."""
    a = atlas.ravel().astype(np.int64)
    m = memos.ravel().astype(np.int64)
    keep = (a > 0) | (m > 0)
    a, m = a[keep], m[keep]
    la, ia = np.unique(a, return_inverse=True)
    lm, im = np.unique(m, return_inverse=True)
    conf = np.zeros((len(la), len(lm)), np.int64)
    np.add.at(conf, (ia, im), 1)
    na, nm = conf.sum(1), conf.sum(0)
    res = {}
    for i, l in enumerate(la):
        if l == 0:
            continue
        cand = [(j, conf[i, j]) for j in range(len(lm)) if lm[j] != 0]
        j, inter = max(cand, key=lambda t: t[1]) if cand else (None, 0)
        if j is None:
            res[int(l)] = {"memos": None, "dice": 0.0}
            continue
        res[int(l)] = {"memos": int(lm[j]), "dice": round(2 * inter / (na[i] + nm[j]), 4),
                       "vox_atlas": int(na[i]), "vox_memos": int(nm[j])}
    return res


def best_translation(fixed: np.ndarray, moving: np.ndarray, coarse: int = 2, refine: int = 2) -> tuple[tuple[int, int, int], float]:
    """Traslación entera t que maximiza el Dice entre `fixed` y `moving` desplazada t (desviación D3).

    Correlación cruzada por FFT a 1/`coarse` y refinamiento exhaustivo ±`refine` vóxeles en la
    rejilla original. Devuelve (t, Dice). Sin rotaciones.
    """
    f = np.asarray(fixed, bool)
    g = np.asarray(moving, bool)
    a = block_mean(g.astype(np.float32), coarse)
    b = block_mean(f.astype(np.float32), coarse)
    cc = np.fft.irfftn(np.fft.rfftn(b) * np.conj(np.fft.rfftn(a)), s=a.shape, axes=(0, 1, 2))
    sh = np.array(np.unravel_index(int(cc.argmax()), cc.shape))
    sh = np.where(sh > np.array(a.shape) // 2, sh - np.array(a.shape), sh) * coarse
    del a, b, cc
    nf, ng = int(f.sum()), int(g.sum())
    best = (-1.0, (0, 0, 0))
    r = range(-refine, refine + 1)
    for dz in r:
        for dy in r:
            for dx in r:
                t = (int(sh[0] + dz), int(sh[1] + dy), int(sh[2] + dx))
                d = 2 * int((np.roll(g, t, (0, 1, 2)) & f).sum()) / max(nf + ng, 1)
                if d > best[0]:
                    best = (d, t)
    return best[1], best[0]


# ---------------------------------------------------------------- CLI
def _ids(path: str, which: str) -> list[str]:
    sel = json.loads(Path(path).read_text(encoding="utf-8"))
    return list(sel[which])


def cmd_run(a):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from geovida.minc import load_minc

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    predictor = build_memos(a.model, a.threads)
    ids = a.id or _ids(a.ids, a.which)
    log_path = out / "memos_run.json"
    runs = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else {}
    for k, sid in enumerate(ids, 1):
        dest = out / f"{sid}_memos.npz"
        if dest.exists() and not a.force:
            print(f"[{k}/{len(ids)}] {sid}: ya existe")
            continue
        print(f"[{k}/{len(ids)}] {sid}")
        t0 = time.time()
        try:
            img, spacing, meta = load_minc(Path(a.data) / f"{sid}.mnc")
            shape = img.shape
            with tempfile.TemporaryDirectory(dir=out) as wd:
                lab, box, info = segment_volume(img, predictor, a.factor, Path(wd))
            del img
            np.savez_compressed(dest, labels=lab, box=np.array([[s.start, s.stop] for s in box]),
                                shape=np.array(shape), factor=a.factor)
            info.update(ok=True, seconds_total=round(time.time() - t0, 1),
                        labels_present=sorted(int(v) for v in np.unique(lab) if v))
        except Exception as exc:  # se registra el fallo: cuenta para la comprobación 3.4
            info = {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                    "seconds_total": round(time.time() - t0, 1)}
        runs[sid] = info
        log_path.write_text(json.dumps(runs, indent=1), encoding="utf-8")
        print(f"   {'ok' if info['ok'] else 'FALLO'} · {info['seconds_total']} s")
    ok = sum(1 for v in runs.values() if v.get("ok"))
    print(f"MEMOS ejecutado en {ok}/{len(runs)}")


def cmd_compare(a):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from geovida.p3_data import MUSMORPH_LABELS, load_labels

    out = Path(a.out)
    res = {}
    pad = a.pad
    for f in sorted(out.glob("*_memos.npz")):
        sid = f.name[: -len("_memos.npz")]
        z = np.load(f)
        lab, box = z["labels"], z["box"]
        atlas, abox, *_ = load_labels(Path(a.data) / f"{sid}_Segs.mnc", MUSMORPH_LABELS, "nearest")
        ab = np.array([[s.start, s.stop] for s in abox])
        # lienzo común: unión de las dos cajas con margen `pad` (np.roll no recicla etiquetas)
        lo = np.minimum(box[:, 0], ab[:, 0]) - pad
        hi = np.maximum(box[:, 1], ab[:, 1]) + pad
        shape = tuple(int(v) for v in hi - lo)
        M = np.zeros(shape, np.uint8)
        M[tuple(slice(box[i][0] - lo[i], box[i][1] - lo[i]) for i in range(3))] = lab
        A = np.zeros(shape, np.int16)
        A[tuple(slice(ab[i][0] - lo[i], ab[i][1] - lo[i]) for i in range(3))] = atlas
        del lab, atlas
        t, d_union = best_translation(M > 0, A > 0)
        if max(abs(v) for v in t) >= pad:
            raise RuntimeError(f"{sid}: traslación {t} ≥ margen {pad}; aumente --pad")
        nu = int((A > 0).sum() + (M > 0).sum())
        d_raw = 2 * int(((A > 0) & (M > 0)).sum()) / nu
        raw = dice_table(M, A)
        A = np.roll(A, t, (0, 1, 2))
        shifted = dice_table(M, A)
        res[sid] = {"translation_vox": list(t), "translation_mm": [round(v * 0.027, 3) for v in t],
                    "dice_union_raw": round(d_raw, 4), "dice_union_shifted": round(d_union, 4),
                    "raw": raw, "shifted": shifted}
        med = [float(np.median([v["dice"] for k, v in tab.items() if k <= 48])) for tab in (raw, shifted)]
        print(f"{sid}: traslación {t} · Dice unión {d_raw:.3f} → {d_union:.3f} · "
              f"mediano 1–48 {med[0]:.3f} → {med[1]:.3f}")
        (out / "memos_vs_atlas.json").write_text(json.dumps(res, indent=1), encoding="utf-8")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--model", required=True)
    r.add_argument("--data", required=True)
    r.add_argument("--ids", default="results/p3/seleccion.json")
    r.add_argument("--which", default="pilot")
    r.add_argument("--id", action="append")
    r.add_argument("--out", default="results/p3/memos")
    r.add_argument("--factor", type=int, default=2)
    r.add_argument("--threads", type=int, default=4)
    r.add_argument("--force", action="store_true")
    r.set_defaults(fn=cmd_run)
    c = sub.add_parser("compare")
    c.add_argument("--data", required=True)
    c.add_argument("--out", default="results/p3/memos")
    c.add_argument("--pad", type=int, default=40)
    c.set_defaults(fn=cmd_compare)
    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
