"""FI-1 (docs/prenatal/PREREGISTRO_FOTO_IMPRESION.md): medir sobre la foto de una impresión de ecografía.

Qué hace
--------
* ``homography``: transformación proyectiva (DLT normalizada) que lleva las 4 esquinas del recuadro, marcadas a mano en
  la foto, a un rectángulo. ``warp_points`` la aplica a cualquier punto marcado.
* ``scale_mm_per_unit`` y ``scale_cv``: calibración con las marcas de 1 cm de la escala impresa (G0-escala).
* ``edge_bend_deg``: G0-homografía con puntos medios de los bordes del recuadro (véase la nota del §10 del preregistro).
* ``distance_mm``, ``relative_errors`` y ``analyze``: estimandos de §3.5 y remuestreo por conglomerados (impresión →
  foto), con los veredictos de FI-1a y FI-1b.

Qué NO hace
-----------
No lee imágenes ni coloca puntos: los puntos los marca una persona (D2) y llegan como coordenadas. No interpreta
anatomía ni da ningún resultado clínico. Las pruebas usan impresiones sintéticas; que pasen no valida ninguna foto real.
"""
from __future__ import annotations

import math

import numpy as np

SEED_FI1 = 20261127
N_BOOT = 2000
TICK_MM = 10.0
SUPPORT_MAX, REFUTE_MIN = 0.05, 0.10      # FI-1a: |e| mediano
BIAS_BAND = 0.05                          # FI-1b
SCALE_CV_MAX = 0.05                       # G0-escala
BEND_MAX_DEG = 2.0                        # G0-homografía


# ---------------------------------------------------------------- geometría proyectiva
def _normalize(p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    c = p.mean(axis=0)
    s = math.sqrt(2) / np.mean(np.linalg.norm(p - c, axis=1))
    T = np.array([[s, 0, -s * c[0]], [0, s, -s * c[1]], [0, 0, 1.0]])
    return (np.c_[p, np.ones(len(p))] @ T.T)[:, :2], T


def homography(src, dst) -> np.ndarray:
    """H (3 × 3) con dst ≈ H·src, por DLT normalizada. Hacen falta ≥ 4 puntos, sin 3 alineados."""
    src, dst = np.asarray(src, float), np.asarray(dst, float)
    if src.shape != dst.shape or src.ndim != 2 or src.shape[1] != 2 or len(src) < 4:
        raise ValueError("src y dst deben ser (n, 2) con n ≥ 4")
    s, Ts = _normalize(src)
    d, Td = _normalize(dst)
    rows = []
    for (x, y), (u, v) in zip(s, d):
        rows.append([-x, -y, -1, 0, 0, 0, u * x, u * y, u])
        rows.append([0, 0, 0, -x, -y, -1, v * x, v * y, v])
    _, sv, vt = np.linalg.svd(np.asarray(rows))
    if sv[-2] < 1e-10:
        raise ValueError("puntos degenerados (¿tres alineados?)")
    Hn = vt[-1].reshape(3, 3)
    H = np.linalg.inv(Td) @ Hn @ Ts
    return H / H[2, 2]


def warp_points(H: np.ndarray, pts) -> np.ndarray:
    p = np.c_[np.asarray(pts, float), np.ones(len(pts))] @ np.asarray(H, float).T
    return p[:, :2] / p[:, 2:3]


def rectify(corners_photo, aspect: float, width: float = 1000.0) -> np.ndarray:
    """H que lleva las esquinas (sup-izq, sup-der, inf-der, inf-izq) a un rectángulo de razón ancho/alto ``aspect``.

    ``aspect`` tiene que ser la razón **real** del recuadro impreso, medida con una regla sobre el papel. Estimarla a
    partir de la propia foto deja una deformación anisótropa que la escala vertical no corrige (en las pruebas
    sintéticas, un error mediano de varios por ciento)."""
    c = np.asarray(corners_photo, float)
    if c.shape != (4, 2):
        raise ValueError("hacen falta 4 esquinas (sup-izq, sup-der, inf-der, inf-izq)")
    if not (aspect > 0 and math.isfinite(aspect)):
        raise ValueError("aspect debe ser la razón ancho/alto (> 0) medida sobre la impresión")
    dst = np.array([[0, 0], [width, 0], [width, width / aspect], [0, width / aspect]], float)
    return homography(c, dst)


def photo_aspect_estimate(corners_photo) -> float:
    """Razón ancho/alto aparente en la foto (solo para mostrar el sesgo que evita ``rectify``; no usar para medir)."""
    c = np.asarray(corners_photo, float)
    w = 0.5 * (np.linalg.norm(c[1] - c[0]) + np.linalg.norm(c[2] - c[3]))
    h = 0.5 * (np.linalg.norm(c[3] - c[0]) + np.linalg.norm(c[2] - c[1]))
    return float(w / h)


# ---------------------------------------------------------------- puertas
def scale_mm_per_unit(ticks) -> float:
    """mm por unidad a partir de marcas consecutivas de 1 cm (ya corregidas), en orden a lo largo de la escala."""
    t = np.asarray(ticks, float)
    if len(t) < 3:
        raise ValueError("hacen falta ≥ 3 marcas de escala")
    gaps = np.linalg.norm(np.diff(t, axis=0), axis=1)
    return TICK_MM / float(gaps.mean())


def scale_cv(ticks) -> float:
    gaps = np.linalg.norm(np.diff(np.asarray(ticks, float), axis=0), axis=1)
    return float(gaps.std(ddof=1) / gaps.mean()) if len(gaps) > 1 else math.inf


def edge_bend_deg(corners, midpoints) -> float:
    """Máxima desviación de 180° del ángulo esquina–punto medio–esquina en los 4 bordes (ya corregidos).

    Con exactamente 4 puntos la homografía deja un rectángulo perfecto por construcción; los puntos medios, marcados
    aparte y no usados para ajustar H, son los que pueden mostrar curvatura del papel o distorsión de la lente."""
    c, m = np.asarray(corners, float), np.asarray(midpoints, float)
    worst = 0.0
    for k in range(4):
        a, b, p = c[k], c[(k + 1) % 4], m[k]
        u, v = a - p, b - p
        cosang = float(u @ v) / (np.linalg.norm(u) * np.linalg.norm(v))
        worst = max(worst, 180.0 - math.degrees(math.acos(max(-1.0, min(1.0, cosang)))))
    return worst


# ---------------------------------------------------------------- medida y análisis
def distance_mm(p, q, mm_per_unit: float) -> float:
    return float(np.linalg.norm(np.asarray(p, float) - np.asarray(q, float))) * mm_per_unit


def measure_photo(ann: dict) -> dict:
    """Una foto marcada a mano → distancias de cada pareja de calibres, con y sin corrección de perspectiva.

    ``ann``: ``aspect_mm`` [ancho, alto] medidos con regla (D-1); ``corners`` (4, sup-izq en sentido horario);
    ``midpoints`` (4, en el mismo orden de bordes: superior, derecho, inferior, izquierdo; D-2); ``ticks`` (≥ 3
    marcas consecutivas de 1 cm); ``pairs`` {nombre: [[x, y], [x, y]]}. Coordenadas en píxeles de la foto."""
    w, h = (float(v) for v in ann["aspect_mm"])
    R = rectify(ann["corners"], w / h)
    corners_r = warp_points(R, ann["corners"])
    mids_r = warp_points(R, ann["midpoints"])
    ticks_r = warp_points(R, ann["ticks"])
    k = scale_mm_per_unit(ticks_r)
    k_raw = scale_mm_per_unit(ann["ticks"])
    out = {}
    for name, (p, q) in sorted(ann["pairs"].items()):
        pr, qr = warp_points(R, [p, q])
        out[name] = {"corrected_mm": distance_mm(pr, qr, k), "uncorrected_mm": distance_mm(p, q, k_raw)}
    return {"scale_cv": scale_cv(ticks_r), "edge_bend_deg": edge_bend_deg(corners_r, mids_r), "pairs": out}


def gate_photo(m: dict) -> dict:
    """G0-escala y G0-homografía (enmendada, D-2) para una foto medida."""
    ok_s, ok_h = m["scale_cv"] <= SCALE_CV_MAX, m["edge_bend_deg"] <= BEND_MAX_DEG
    return {"scale_cv": m["scale_cv"], "edge_bend_deg": m["edge_bend_deg"], "G0-escala": bool(ok_s),
            "G0-homografia": bool(ok_h), "passed": bool(ok_s and ok_h)}


ETHICS_FIELDS = ("consentimiento_codigo", "aval_etico", "anonimizacion_revisada")


def gate_ethics(record: dict | None) -> dict:
    """G0-ética: registro con el código interno del consentimiento firmado (sin nombres), el aval (comité o
    institución) y la confirmación de que una persona revisó la anonimización. Sin registro completo, no pasa."""
    rec = record or {}
    missing = [f for f in ETHICS_FIELDS if not rec.get(f)]
    return {"gate": "G0-ética", "missing": missing, "passed": not missing}


def relative_errors(measured, printed) -> np.ndarray:
    m, p = np.asarray(measured, float), np.asarray(printed, float)
    if np.any(p <= 0):
        raise ValueError("los valores impresos deben ser > 0")
    return (m - p) / p


def verdict_fi1a(lo: float, hi: float) -> str:
    if not (math.isfinite(lo) and math.isfinite(hi)):
        return "no evaluable"
    if hi <= SUPPORT_MAX:
        return "apoyada"
    if lo >= REFUTE_MIN:
        return "refutada"
    return "no concluyente"


def verdict_fi1b(lo: float, hi: float) -> str:
    if not (math.isfinite(lo) and math.isfinite(hi)):
        return "no evaluable"
    return "apoyada" if (lo <= 0.0 <= hi and lo >= -BIAS_BAND and hi <= BIAS_BAND) else "no apoyada"


def _stats(e: np.ndarray) -> tuple[float, float]:
    return float(np.median(np.abs(e))), float(np.mean(e))


def analyze(rows: list[dict], *, n_boot: int = N_BOOT, seed: int = SEED_FI1) -> dict:
    """``rows``: una por medida, con ``print``, ``photo``, ``pair``, ``repeat``, ``measured_mm`` y ``printed_mm``.

    Remuestreo por conglomerados: impresiones con reemplazo y, dentro de cada una, fotos con reemplazo; cada foto
    aporta todas sus medidas."""
    if not rows:
        raise ValueError("sin medidas")
    e = relative_errors([r["measured_mm"] for r in rows], [r["printed_mm"] for r in rows])
    med, bias = _stats(e)
    prints: dict = {}
    for i, r in enumerate(rows):
        prints.setdefault(r["print"], {}).setdefault(r["photo"], []).append(i)
    keys = sorted(prints)
    rng = np.random.default_rng(seed)
    meds, biases = np.empty(n_boot), np.empty(n_boot)
    for b in range(n_boot):
        idx = []
        for k in rng.choice(len(keys), len(keys), replace=True):
            photos = prints[keys[k]]
            pk = sorted(photos)
            for j in rng.choice(len(pk), len(pk), replace=True):
                idx.extend(photos[pk[j]])
        meds[b], biases[b] = _stats(e[idx])
    med_ci = [float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))]
    bias_ci = [float(np.percentile(biases, 2.5)), float(np.percentile(biases, 97.5))]
    # componentes descriptivos: entre fotos de la misma impresión y pareja, y entre repeticiones de la misma foto
    cell: dict = {}
    for i, r in enumerate(rows):
        cell.setdefault((r["print"], r["pair"], r["photo"]), []).append(e[i])
    within = [np.std(v, ddof=1) for v in cell.values() if len(v) > 1]
    by_pair: dict = {}
    for (pr, pa, _ph), v in cell.items():
        by_pair.setdefault((pr, pa), []).append(float(np.mean(v)))
    between = [np.std(v, ddof=1) for v in by_pair.values() if len(v) > 1]
    return {"n_measurements": len(rows), "n_prints": len(keys),
            "n_photos": int(sum(len(v) for v in prints.values())),
            "median_abs_error": med, "median_abs_error_ci": med_ci,
            "mean_signed_error": bias, "mean_signed_error_ci": bias_ci,
            "sd_between_photos": float(np.mean(between)) if between else math.nan,
            "sd_between_repeats": float(np.mean(within)) if within else math.nan,
            "verdict_fi1a": verdict_fi1a(*med_ci), "verdict_fi1b": verdict_fi1b(*bias_ci),
            "n_boot": n_boot, "seed": seed}
