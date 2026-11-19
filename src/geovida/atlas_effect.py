"""MT-A (MORPHO-TRACE): efecto del atlas sobre la forma, con los mismos especímenes registrados a dos atlas.

Implementa el protocolo fijado en ``docs/morpho_trace/PREREGISTRO_ATLAS.md`` (§3–§5). Tres partes:

1. **Geometría.** ``to_sitk`` pasa un volumen leído con ``geovida.minc.load_minc`` (arreglo en el orden del
   archivo y afín índice→mundo en mm) a una imagen de SimpleITK con la **misma** geometría del mundo: el origen,
   el espaciado y la dirección salen de la afín, con los ejes invertidos porque SimpleITK indexa (x, y, z)
   donde NumPy indexa (i, j, k). Así los landmarks ``.tag`` (en coordenadas del mundo de MINC) se usan sin
   convertir. ``downsample`` promedia bloques y actualiza la afín (centro del bloque).
2. **Registro y transferencia.** ``register``: momentos → afín (Mattes, 3 niveles) → B-spline (LBFGS-B), con
   los parámetros del preregistro. La transformada devuelta lleva puntos de la imagen **fija** (el atlas) a la
   **móvil** (el espécimen); ``transfer_points`` la aplica a los landmarks del atlas.
3. **Estadística** (solo NumPy). ``published_direction`` (puerta G0-d), ``atlas_effect`` (f, MT-A2, MT-A3 con
   remuestreo por espécimen), ``gate_g1``, ``fraction_inside`` (G0-a/b) y ``verdict_mta1``.

Las pruebas usan fantomas con deformación conocida (``tests/test_atlas_effect.py``): que el registro recupere
una transformada sintética no valida su comportamiento con embriones reales; eso lo mide la puerta G1.

Solo investigación con datos animales; no es una herramienta clínica.
"""
from __future__ import annotations

import math

import numpy as np

from geovida import landmarks as lm

SEED = 20261118
N_BOOT = 2000
SUPPORT, REFUTE = 0.50, 0.25


def _sitk():
    try:
        import SimpleITK as sitk
    except ImportError as exc:  # pragma: no cover
        raise ImportError("el registro de MT-A necesita SimpleITK: pip install 'geovida[reference]'") from exc
    return sitk


# ---------------------------------------------------------------- geometría
def to_sitk(arr: np.ndarray, affine) -> "object":
    """Imagen de SimpleITK con la geometría del mundo de ``affine`` (índice NumPy (i, j, k) → mm)."""
    sitk = _sitk()
    a = np.asarray(affine, dtype=float)
    cols = a[:3, :3][:, ::-1]                 # columna de cada eje ITK (x, y, z) = ejes NumPy (k, j, i)
    spacing = np.linalg.norm(cols, axis=0)
    if np.any(spacing <= 0):
        raise ValueError("afín degenerada")
    direction = cols / spacing
    if not np.allclose(direction.T @ direction, np.eye(3), atol=1e-5):
        raise ValueError("la afín no tiene cosenos directores ortogonales")
    img = sitk.GetImageFromArray(np.ascontiguousarray(arr, dtype=np.float32))
    img.SetSpacing(tuple(float(s) for s in spacing))
    img.SetDirection(tuple(float(x) for x in direction.ravel()))
    img.SetOrigin(tuple(float(x) for x in a[:3, 3]))
    return img


def downsample(arr: np.ndarray, affine, factor: int) -> tuple[np.ndarray, np.ndarray]:
    """Media de bloques ``factor``³ y afín del volumen resultante (el vóxel nuevo está en el centro del bloque)."""
    if factor < 1:
        raise ValueError("factor ≥ 1")
    a = np.asarray(affine, dtype=float).copy()
    if factor == 1:
        return np.asarray(arr, dtype=np.float32), a
    s = [d - d % factor for d in arr.shape]
    if min(s) == 0:
        raise ValueError("el volumen es menor que el bloque")
    x = np.asarray(arr, dtype=np.float32)[:s[0], :s[1], :s[2]]
    x = x.reshape(s[0] // factor, factor, s[1] // factor, factor, s[2] // factor, factor).mean(axis=(1, 3, 5))
    out = a.copy()
    out[:3, :3] = a[:3, :3] * factor
    out[:3, 3] = a[:3, :3] @ np.full(3, (factor - 1) / 2.0) + a[:3, 3]
    return x, out


def world_to_index(points: np.ndarray, affine) -> np.ndarray:
    """Coordenadas del mundo (n, 3) → índices continuos (i, j, k) del arreglo."""
    inv = np.linalg.inv(np.asarray(affine, dtype=float))
    p = np.c_[np.asarray(points, dtype=float), np.ones(len(points))]
    return (inv @ p.T).T[:, :3]


def fraction_inside(arr: np.ndarray, affine, points: np.ndarray, threshold: float | None = None) -> float:
    """Puertas G0-a/b: fracción de puntos que caen en vóxeles por encima del umbral de Otsu (o del dado)."""
    if threshold is None:
        from skimage.filters import threshold_otsu
        threshold = float(threshold_otsu(np.asarray(arr)))
    idx = np.rint(world_to_index(points, affine)).astype(int)
    shape = np.asarray(arr.shape)
    ok = np.all((idx >= 0) & (idx < shape), axis=1)
    vals = np.zeros(len(idx), bool)
    vals[ok] = np.asarray(arr)[tuple(idx[ok].T)] > threshold
    return float(vals.mean())


def stream_volume(slabs, shape, affine, *, factor: int = 4, points: np.ndarray | None = None,
                  nbins: int = 256) -> dict:
    """Lo que MT-A necesita de un volumen, leyéndolo por losas para no tenerlo entero en memoria.

    ``slabs()`` devuelve cada vez un iterable nuevo de ``(inicio, losa)`` a lo largo del primer eje, con losas
    de ``factor`` cortes alineadas en múltiplos de ``factor`` (``geovida.minc.minc_slabs(path, factor)``); se
    recorre dos veces. Devuelve:

    * ``downsampled`` y ``affine_ds``: idénticos a ``downsample(volumen, affine, factor)``;
    * ``otsu``: el umbral de ``skimage.filters.threshold_otsu`` sobre el volumen **completo** (mismo histograma
      de ``nbins`` contenedores entre el mínimo y el máximo);
    * con ``points``: la intensidad a resolución completa en el vóxel más cercano a cada punto (NaN fuera del
      volumen) y ``inside``, la fracción por encima de ``otsu`` (puertas G0-a/b, como ``fraction_inside``).
    """
    if factor < 1:
        raise ValueError("factor ≥ 1")
    shape = tuple(int(s) for s in shape)
    s = [d - d % factor for d in shape]
    if min(s) == 0:
        raise ValueError("el volumen es menor que el bloque")
    ds = np.empty((s[0] // factor, s[1] // factor, s[2] // factor), np.float32)
    if points is not None:
        idx = np.rint(world_to_index(points, affine)).astype(int)
        valid = np.all((idx >= 0) & (idx < np.asarray(shape)), axis=1)
        values = np.full(len(idx), np.nan)
    lo = hi = None
    for i0, slab in slabs():
        slab = np.asarray(slab, dtype=np.float32)
        if i0 % factor or (len(slab) % factor and i0 + len(slab) != shape[0]):
            raise ValueError("las losas deben empezar en múltiplos de factor y tener factor cortes")
        smin, smax = slab.min(), slab.max()
        lo = smin if lo is None else min(lo, smin)
        hi = smax if hi is None else max(hi, smax)
        if points is not None:
            sel = valid & (idx[:, 0] >= i0) & (idx[:, 0] < i0 + len(slab))
            values[sel] = slab[idx[sel, 0] - i0, idx[sel, 1], idx[sel, 2]]
        for b0 in range(0, len(slab) - factor + 1, factor):
            g = (i0 + b0) // factor
            if g < ds.shape[0]:
                x = slab[b0:b0 + factor, :s[1], :s[2]]
                ds[g] = x.reshape(1, factor, s[1] // factor, factor, s[2] // factor, factor).mean(axis=(1, 3, 5))[0]
    if lo is None:
        raise ValueError("volumen vacío")
    counts = np.zeros(nbins, np.int64)
    edges = None
    for _, slab in slabs():
        c, edges = np.histogram(np.asarray(slab, dtype=np.float32), bins=nbins, range=(lo, hi))
        counts += c
    from skimage.filters import threshold_otsu
    otsu = float(threshold_otsu(hist=(counts, (edges[:-1] + edges[1:]) / 2))) if hi > lo else float(lo)
    a = np.asarray(affine, dtype=float)
    out = a.copy()
    out[:3, :3] = a[:3, :3] * factor
    out[:3, 3] = a[:3, :3] @ np.full(3, (factor - 1) / 2.0) + a[:3, 3]
    res = {"downsampled": ds, "affine_ds": out, "otsu": otsu, "shape": shape, "factor": factor}
    if points is not None:
        res["point_values"] = values
        res["inside"] = float(np.mean(np.nan_to_num(values, nan=-np.inf) > otsu))
    return res


# ---------------------------------------------------------------- registro
def register(fixed, moving, *, mesh: int = 8, affine_only: bool = False, seed: int = SEED,
             affine_iterations: int = 200, bspline_iterations: int = 100) -> tuple["object", dict]:
    """Registro del preregistro (§3): momentos → afín → B-spline. Devuelve (transformada fija→móvil, info)."""
    sitk = _sitk()
    f = sitk.Cast(fixed, sitk.sitkFloat32)
    m = sitk.Cast(moving, sitk.sitkFloat32)
    init = sitk.CenteredTransformInitializer(f, m, sitk.AffineTransform(3),
                                             sitk.CenteredTransformInitializerFilter.MOMENTS)

    def _method(levels, sigmas):
        r = sitk.ImageRegistrationMethod()
        r.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
        r.SetMetricSamplingStrategy(r.RANDOM)
        r.SetMetricSamplingPercentage(0.10, seed)
        r.SetInterpolator(sitk.sitkLinear)
        r.SetShrinkFactorsPerLevel(levels)
        r.SetSmoothingSigmasPerLevel(sigmas)
        r.SmoothingSigmasAreSpecifiedInPhysicalUnitsOff()
        return r

    r1 = _method([4, 2, 1], [2, 1, 0])
    r1.SetOptimizerAsRegularStepGradientDescent(learningRate=1.0, minStep=1e-4,
                                                numberOfIterations=affine_iterations)
    r1.SetOptimizerScalesFromPhysicalShift()
    r1.SetInitialTransform(init, inPlace=False)
    affine_tx = r1.Execute(f, m)
    info = {"affine_metric": float(r1.GetMetricValue()), "affine_stop": r1.GetOptimizerStopConditionDescription(),
            "mesh": None if affine_only else mesh}
    if affine_only:
        return affine_tx, info
    bs = sitk.BSplineTransformInitializer(f, [mesh] * 3, order=3)
    r2 = _method([2, 1], [1, 0])
    r2.SetOptimizerAsLBFGSB(gradientConvergenceTolerance=1e-5, numberOfIterations=bspline_iterations)
    r2.SetMovingInitialTransform(affine_tx)
    r2.SetInitialTransform(bs, inPlace=True)
    r2.Execute(f, m)
    info.update({"bspline_metric": float(r2.GetMetricValue()),
                 "bspline_stop": r2.GetOptimizerStopConditionDescription()})
    # ITK: punto de la fija → afín(B-spline(p)). CompositeTransform aplica primero el último de la lista.
    return sitk.CompositeTransform([affine_tx, bs]), info


def transfer_points(transform, points: np.ndarray) -> np.ndarray:
    """Aplica la transformada (fija → móvil) a puntos del mundo (n, 3)."""
    return np.array([transform.TransformPoint(tuple(float(c) for c in p)) for p in np.asarray(points)])


# ---------------------------------------------------------------- estadística
def _tangent(configs: np.ndarray) -> tuple[np.ndarray, float]:
    g = lm.gpa(configs)
    return lm.tangent_coordinates(g["aligned"], g["mean"])


def published_direction(pub15: np.ndarray, pub18: np.ndarray) -> dict:
    """Puerta G0-d: d = media E18.5 − media E15.5 en el espacio tangente de un GPA de las publicadas."""
    t, rho = _tangent(np.concatenate([pub15, pub18]))
    d = t[len(pub15):].mean(axis=0) - t[:len(pub15)].mean(axis=0)
    return {"d_length": float(np.linalg.norm(d)), "rho_max": float(rho), "n15": len(pub15), "n18": len(pub18)}


def verdict_mta1(lo: float, hi: float) -> str:
    """§5: apoyada si el límite inferior de f ≥ 0,50; refutada si el superior ≤ 0,25; si no, no concluyente."""
    if not (math.isfinite(lo) and math.isfinite(hi)):
        return "no evaluable"
    if lo >= SUPPORT:
        return "apoyada"
    if hi <= REFUTE:
        return "refutada"
    return "no concluyente"


def _unsigned(u, v) -> float:
    return lm.angle_deg(u, v)


def atlas_effect(pub15: np.ndarray, pub18: np.ndarray, l15: np.ndarray, l18: np.ndarray, stage,
                 *, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """Estimandos de §5. ``l15``/``l18``: (n, k, 3) landmarks transferidos desde cada atlas al espécimen s;
    ``stage``: estadio de cada espécimen ('E15.5' o 'E18.5'). Un único GPA con publicadas y transferidas."""
    l15, l18 = np.asarray(l15, float), np.asarray(l18, float)
    stage = np.asarray(stage)
    n = len(l15)
    if l18.shape != l15.shape or len(stage) != n or n < 2:
        raise ValueError("l15, l18 y stage deben describir los mismos ≥ 2 especímenes")
    t, rho = _tangent(np.concatenate([pub15, pub18, l15, l18]))
    n15, n18 = len(pub15), len(pub18)
    tp15, tp18 = t[:n15], t[n15:n15 + n18]
    t15, t18 = t[n15 + n18:n15 + n18 + n], t[n15 + n18 + n:]
    d = tp18.mean(axis=0) - tp15.mean(axis=0)
    dl = float(np.linalg.norm(d))
    dh = d / dl
    delta = t18 - t15
    proj = delta @ dh

    def stats(idx):
        m = delta[idx].mean(axis=0)
        return float(m @ dh) / dl, float(np.linalg.norm(m)) / dl

    f, mag = stats(np.arange(n))
    g15, g18 = np.flatnonzero(stage == "E15.5"), np.flatnonzero(stage == "E18.5")
    rng = np.random.default_rng(seed)
    fb, ab = [], []
    for _ in range(n_boot):
        fb.append(stats(rng.integers(0, n, n))[0])
        if len(g15) >= 2 and len(g18) >= 2:
            a = delta[rng.choice(g15, len(g15))].mean(axis=0)
            b = delta[rng.choice(g18, len(g18))].mean(axis=0)
            ab.append(_unsigned(a, b))
    lo, hi = (float(x) for x in np.percentile(fb, [2.5, 97.5]))
    a2 = (_unsigned(delta[g15].mean(axis=0), delta[g18].mean(axis=0))
          if len(g15) >= 2 and len(g18) >= 2 else float("nan"))
    a2_ci = [float(x) for x in np.percentile(ab, [2.5, 97.5])] if ab else [float("nan")] * 2
    return {
        "n": n, "n_by_stage": {"E15.5": int(len(g15)), "E18.5": int(len(g18))}, "rho_max": float(rho),
        "d_length": dl,
        "mta1": {"f": f, "ci": [lo, hi], "verdict": verdict_mta1(lo, hi)},
        "mta2": {"angle_deg": a2, "ci": a2_ci,
                 "verdict": "no evaluable" if not math.isfinite(a2) else ("apoyada" if a2 < 45 else "no apoyada")},
        "mta3": {"magnitude_ratio": mag, "angle_to_d_deg": _unsigned(delta.mean(axis=0), d),
                 "sd_delta_along_d": float(proj.std(ddof=1)),
                 "sd_published_along_d": {"E15.5": float((tp15 @ dh).std(ddof=1)),
                                          "E18.5": float((tp18 @ dh).std(ddof=1))}},
        "n_boot": n_boot, "seed": seed,
    }


def gate_g1(own: np.ndarray, published: np.ndarray, published_by_stage: dict) -> dict:
    """G1: mediana de ρ(L_propio(s), publicados(s)) menor que la mediana de ρ entre especímenes distintos del
    mismo estadio (pares dentro de cada estadio, juntos)."""
    own, published = np.asarray(own, float), np.asarray(published, float)
    err = [lm.procrustes_distances(a, b)["rho"] for a, b in zip(own, published)]
    pairs = []
    for configs in published_by_stage.values():
        c = np.asarray(configs, float)
        pairs += [lm.procrustes_distances(c[i], c[j])["rho"] for i in range(len(c)) for j in range(i + 1, len(c))]
    if not err or not pairs:
        raise ValueError("faltan configuraciones para G1")
    me, mp = float(np.median(err)), float(np.median(pairs))
    return {"median_rho_transfer": me, "median_rho_between_specimens": mp, "passed": me < mp,
            "n_transfer": len(err), "n_pairs": len(pairs)}
