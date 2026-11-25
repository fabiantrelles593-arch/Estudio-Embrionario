"""FI-1s (docs/prenatal/PREREGISTRO_FOTO_IMPRESION_SINTETICA.md): hojas sintéticas y análisis de FI-1 sin datos humanos.

* ``design_sheet``: geometría de una hoja A4 en mm (origen arriba a la izquierda, y hacia abajo). Tiene un recuadro
  oscuro con moteado, una escala vertical de 8 marcas de 1 cm y 4 pares de calibres «+» de 10–60 mm que no se cruzan.
* ``render_sheet``: dibuja una hoja a escala 1:1 con matplotlib (PDF para imprimir; PNG en las pruebas).
* ``plan``, ``gate_print``, ``build_rows`` y ``analyze``: el protocolo de §3–§5 con ``geovida.print_measure`` sin
  cambios.

Ninguna distancia se dibuja en la hoja. Los valores diseñados van a un archivo aparte que quien marca no abre.
Sin anatomía, sin datos de personas y sin uso clínico.
"""
from __future__ import annotations

import math

import numpy as np

from . import print_measure as pm

SEED = 20261125
N_SHEETS = 6
N_PAIRS = 4
N_PHOTOS = ("F1", "F2", "F3")
N_REPEATS = 3
PAGE_MM = (210.0, 297.0)
FRAME = (25.0, 45.0, 160.0, 120.0)          # x0, y0, ancho, alto (mm)
N_TICKS = 8
SCALE_X_FROM_RIGHT = 8.0                    # la línea de escala, a 8 mm del borde derecho del recuadro
TICK_Y0 = 15.0                              # primera marca, 15 mm por debajo del borde superior
LEN_RANGE = (10.0, 60.0)
CROSS_ARM = 1.6                             # mm, medio brazo de cada «+»
MIN_SEP = 7.0                               # separación mínima entre centros de «+» y con la escala
MARGIN = 9.0
PRINT_TOL = 0.02                            # G0-impresión


def frame_corners() -> np.ndarray:
    x0, y0, w, h = FRAME
    return np.array([[x0, y0], [x0 + w, y0], [x0 + w, y0 + h], [x0, y0 + h]], float)


def frame_midpoints() -> np.ndarray:
    c = frame_corners()
    return np.array([(c[k] + c[(k + 1) % 4]) / 2 for k in range(4)])      # superior, derecho, inferior, izquierdo


def ticks() -> np.ndarray:
    x0, y0, w, _ = FRAME
    x = x0 + w - SCALE_X_FROM_RIGHT
    return np.array([[x, y0 + TICK_Y0 + 10.0 * k] for k in range(N_TICKS)], float)


def _segments_cross(a, b, c, d) -> bool:
    def orient(p, q, r):
        return np.sign((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]))
    return orient(a, b, c) != orient(a, b, d) and orient(c, d, a) != orient(c, d, b)


def design_sheet(rng: np.random.Generator) -> dict:
    """4 pares dentro de la zona útil (sin la franja de la escala), que no se cruzan y con los «+» separados."""
    x0, y0, w, h = FRAME
    xmax = x0 + w - SCALE_X_FROM_RIGHT - MIN_SEP
    lo, hi = np.array([x0 + MARGIN, y0 + MARGIN]), np.array([xmax, y0 + h - MARGIN])
    pairs: dict = {}
    for _ in range(100000):
        if len(pairs) == N_PAIRS:
            break
        length = rng.uniform(*LEN_RANGE)
        ang = rng.uniform(0, math.pi)
        p = rng.uniform(lo, hi)
        q = p + length * np.array([math.cos(ang), math.sin(ang)])
        if np.any(q < lo) or np.any(q > hi):
            continue
        pts = [np.asarray(v) for pq in pairs.values() for v in pq]
        if any(min(np.linalg.norm(p - r), np.linalg.norm(q - r)) < MIN_SEP for r in pts):
            continue
        if any(_segments_cross(p, q, *pq) for pq in pairs.values()):
            continue
        pairs[f"P{len(pairs) + 1}"] = (p, q)
    if len(pairs) != N_PAIRS:
        raise RuntimeError("no se pudo colocar los pares")
    return {"pairs": {k: {"p": p.tolist(), "q": q.tolist(), "mm": float(np.linalg.norm(q - p))}
                      for k, (p, q) in pairs.items()}}


def design_all(seed: int = SEED, n: int = N_SHEETS) -> dict:
    rng = np.random.default_rng(seed)
    sheets = {f"S{k + 1:02d}": design_sheet(rng) for k in range(n)}
    return {"seed": seed, "frame_mm": list(FRAME[2:]), "frame_origin_mm": list(FRAME[:2]),
            "ticks_mm": ticks().tolist(), "sheets": sheets}


def speckle(rng: np.random.Generator, px_per_mm: float = 4.0) -> np.ndarray:
    """Moteado tipo ecografía (Rayleigh suavizado), en [0, 0.55]: sin ninguna estructura anatómica."""
    from scipy import ndimage as ndi
    w, h = FRAME[2:]
    a = rng.rayleigh(1.0, (int(h * px_per_mm), int(w * px_per_mm)))
    a = ndi.gaussian_filter(a, 1.2)
    return 0.55 * (a - a.min()) / (a.max() - a.min())


def render_sheet(code: str, sheet: dict, rng: np.random.Generator):
    """Figura de matplotlib a escala 1:1 (unidades de los ejes = mm del papel)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    W, H = PAGE_MM
    fig = plt.figure(figsize=(W / 25.4, H / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    x0, y0, w, h = FRAME
    ax.imshow(speckle(rng), cmap="gray", vmin=0, vmax=1, extent=(x0, x0 + w, y0 + h, y0), interpolation="nearest")
    lw = 0.25 / 25.4 * 72                                       # 0,25 mm en puntos
    t = ticks()
    ax.plot([t[0, 0], t[0, 0]], [t[0, 1] - 4, t[-1, 1] + 4], color="white", lw=lw)
    for x, y in t:
        ax.plot([x - 2.0, x + 2.0], [y, y], color="white", lw=lw)
    for name, d in sheet["pairs"].items():
        for end, (cx, cy) in (("a", d["p"]), ("b", d["q"])):
            ax.plot([cx - CROSS_ARM, cx + CROSS_ARM], [cy, cy], color="white", lw=lw)
            ax.plot([cx, cx], [cy - CROSS_ARM, cy + CROSS_ARM], color="white", lw=lw)
            ax.text(cx + 2.0, cy - 2.0, f"{name[1:]}{end}", color="white", fontsize=6, ha="left", va="bottom")
    ax.text(x0, y0 - 6, f"FI-1s · hoja {code}", fontsize=10, ha="left", va="bottom")
    ax.text(x0, y0 + h + 10, "Imprimir al 100 % (sin «ajustar a página»). Hoja sintética: sin anatomía ni datos de "
            "personas.", fontsize=7, ha="left", va="top")
    return fig


# ---------------------------------------------------------------- protocolo y análisis
def plan(photos: list[str], seed: int = SEED) -> list[dict]:
    """§3.4: cada foto se marca 3 veces, en 3 sesiones; en cada sesión, las fotos en orden aleatorio."""
    rng = np.random.default_rng(seed)
    out = []
    for r in range(1, N_REPEATS + 1):
        for i in rng.permutation(len(photos)):
            out.append({"session": r, "photo": photos[i], "file": f"marcas/{photos[i]}_r{r}.json"})
    return out


def gate_print(ruler: dict) -> dict:
    """G0-impresión: ancho y alto del recuadro medidos con regla, a ≤ 2 % de los del PDF, en cada hoja."""
    w0, h0 = FRAME[2:]
    per = {}
    for code, (w, h) in sorted(ruler.items()):
        dw, dh = abs(float(w) / w0 - 1), abs(float(h) / h0 - 1)
        per[code] = {"ancho_mm": float(w), "alto_mm": float(h), "dev_ancho": dw, "dev_alto": dh,
                     "passed": bool(dw <= PRINT_TOL and dh <= PRINT_TOL)}
    missing = [f"S{k + 1:02d}" for k in range(N_SHEETS) if f"S{k + 1:02d}" not in ruler]
    return {"hojas": per, "faltan": missing, "passed": not missing and all(v["passed"] for v in per.values())}


def build_rows(marks: list[dict], designed: dict, key: str = "corrected_mm") -> list[dict]:
    rows = []
    for r in marks:
        for pair, d in r["m"]["pairs"].items():
            rows.append({"print": r["print"], "photo": f'{r["print"]}/{r["photo"]}', "photo_type": r["photo"],
                         "pair": pair, "repeat": r["repeat"], "measured_mm": d[key],
                         "printed_mm": float(designed["sheets"][r["print"]]["pairs"][pair]["mm"])})
    return rows


def analyze(marks: list[dict], designed: dict, n_boot: int = pm.N_BOOT, seed: int = SEED) -> dict:
    main = pm.analyze(build_rows(marks, designed), n_boot=n_boot, seed=seed)
    raw = pm.analyze(build_rows(marks, designed, "uncorrected_mm"), n_boot=n_boot, seed=seed)
    rows = build_rows(marks, designed)
    e = pm.relative_errors([r["measured_mm"] for r in rows], [r["printed_mm"] for r in rows])
    by_type = {t: float(np.median(np.abs(e[[r["photo_type"] == t for r in rows]])))
               for t in N_PHOTOS if any(r["photo_type"] == t for r in rows)}
    by_len = sorted((r["printed_mm"], float(abs(x))) for r, x in zip(rows, e))
    return {"analysis": "FI-1s", **main,
            "verdict": {"FI-1sa": main["verdict_fi1a"], "FI-1sb": main["verdict_fi1b"]},
            "fi1sc": {"median_abs_error_uncorrected": raw["median_abs_error"],
                      "median_abs_error_uncorrected_ci": raw["median_abs_error_ci"],
                      "median_abs_error_by_photo_type": by_type,
                      "error_by_length": [{"designed_mm": a, "abs_rel_error": b} for a, b in by_len],
                      "sd_between_repeats": main["sd_between_repeats"]}}
