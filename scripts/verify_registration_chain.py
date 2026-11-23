"""Verificación de la cadena de registro de MT-A (ingeniería, sin veredicto científico).

Tras el fallo de G1 en MT-A v2 (`docs/morpho_trace/RESULTADOS_ATLAS_v2.md` §5), comprueba:

``synthetic``  Deformación conocida sobre un atlas real: el atlas ×4 es la imagen fija y la móvil es el mismo atlas
               deformado por una afín conocida T. Si la cadena es correcta, los landmarks transferidos coinciden con
               T(landmarks). Se mide con el registro solo afín y con el completo, y con los dos órdenes posibles de la
               composición afín/B-spline.
``specimens``  Variantes del registro sobre especímenes de MT-A v2, comparando con sus landmarks publicados: solo
               afín, el del preregistro (malla 8, LBFGS-B con muestreo aleatorio), y dos variantes (muestreo
               regular, y malla 4 con muestreo regular).
``geometry``   Comprueba que imagen y landmarks comparten el espacio físico (rejilla, centroides) y mide qué hace la
               inicialización por momentos con la información mutua y con el error de los landmarks.

Uso: python scripts/verify_registration_chain.py synthetic|specimens|geometry [--names ...]
         --out results/morpho_trace/v2/verificacion
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import atlas_effect_gates as g  # noqa: E402
from geovida import atlas_effect as ae  # noqa: E402
from geovida import landmarks as lm  # noqa: E402

ATLAS = Path("data/external/musmorph/atlas")
IMAGES = Path("data/external/musmorph/qc_images")
LANDMARKS = Path("data/external/musmorph/landmarks_confirm")
CACHE = Path("results/morpho_trace/cache")


def register_parts(fixed, moving, *, mesh=8, sampling="random", seed=ae.SEED, bspline_iterations=100):
    """Igual que ``ae.register`` pero devuelve la afín y la B-spline por separado; ``sampling`` = random|regular."""
    sitk = ae._sitk()
    f, m = sitk.Cast(fixed, sitk.sitkFloat32), sitk.Cast(moving, sitk.sitkFloat32)
    init = sitk.CenteredTransformInitializer(f, m, sitk.AffineTransform(3),
                                             sitk.CenteredTransformInitializerFilter.MOMENTS)

    def method(levels, sigmas, strategy):
        r = sitk.ImageRegistrationMethod()
        r.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
        r.SetMetricSamplingStrategy(strategy)
        r.SetMetricSamplingPercentage(0.10, seed)
        r.SetInterpolator(sitk.sitkLinear)
        r.SetShrinkFactorsPerLevel(levels)
        r.SetSmoothingSigmasPerLevel(sigmas)
        r.SmoothingSigmasAreSpecifiedInPhysicalUnitsOff()
        return r

    r1 = method([4, 2, 1], [2, 1, 0], sitk.ImageRegistrationMethod.RANDOM)  # la afín, como en el preregistro
    r1.SetOptimizerAsRegularStepGradientDescent(learningRate=1.0, minStep=1e-4, numberOfIterations=200)
    r1.SetOptimizerScalesFromPhysicalShift()
    r1.SetInitialTransform(init, inPlace=False)
    affine_tx = r1.Execute(f, m)
    out = {"affine": affine_tx, "affine_metric": float(r1.GetMetricValue())}
    if mesh is None:
        return out
    strategy = sitk.ImageRegistrationMethod.RANDOM if sampling == "random" else sitk.ImageRegistrationMethod.REGULAR
    bs = sitk.BSplineTransformInitializer(f, [mesh] * 3, order=3)
    r2 = method([2, 1], [1, 0], strategy)
    r2.SetOptimizerAsLBFGSB(gradientConvergenceTolerance=1e-5, numberOfIterations=bspline_iterations)
    r2.SetMovingInitialTransform(affine_tx)
    r2.SetInitialTransform(bs, inPlace=True)
    r2.Execute(f, m)
    out.update({"bspline": bs, "bspline_metric": float(r2.GetMetricValue()),
                "bspline_stop": r2.GetOptimizerStopConditionDescription()})
    return out


def apply(tx_list, pts):
    """Composición explícita: aplica la lista de izquierda a derecha."""
    p = np.asarray(pts, float)
    for tx in tx_list:
        p = ae.transfer_points(tx, p)
    return p


def bspline_displacement(bs, pts):
    d = ae.transfer_points(bs, pts) - np.asarray(pts, float)
    return float(np.median(np.linalg.norm(d, axis=1))), float(np.max(np.linalg.norm(d, axis=1)))


def err_mm(a, b):
    e = np.linalg.norm(np.asarray(a) - np.asarray(b), axis=1)
    return {"median_mm": float(np.median(e)), "p90_mm": float(np.percentile(e, 90))}


def synthetic(out: Path) -> dict:
    sitk = ae._sitk()
    st = "E15.5"
    a = g.load_x4(ATLAS / g.ATLAS_IMAGES[st], CACHE)
    fixed = ae.to_sitk(a["downsampled"], a["affine_ds"])
    tags = lm.read_tag(ATLAS / g.ATLAS_TAG[st])
    centre = np.asarray(fixed.TransformContinuousIndexToPhysicalPoint([(s - 1) / 2 for s in fixed.GetSize()]))
    true = sitk.AffineTransform(3)
    true.SetCenter(tuple(centre))
    rot = sitk.VersorTransform((0.0, 0.0, 1.0), np.deg2rad(4.0)).GetMatrix()
    true.SetMatrix(tuple((np.reshape(rot, (3, 3)) * 1.03).ravel()))
    true.SetTranslation((0.6, -0.4, 0.3))
    # móvil(T(x)) = fija(x): Resample da salida(y) = imagen(transform(y)), con transform = T⁻¹
    moving = sitk.Resample(fixed, fixed, true.GetInverse(), sitk.sitkLinear, 0.0)
    target = ae.transfer_points(true, tags)
    res = {"stage": st, "true_transform": "rotación 4° (eje z), escala 1,03, traslación (0,6, −0,4, 0,3) mm",
           "true_shift_median_mm": err_mm(target, tags)["median_mm"]}
    t0 = time.time()
    p = register_parts(fixed, moving, mesh=None)
    res["affine_only"] = err_mm(ae.transfer_points(p["affine"], tags), target)
    p = register_parts(fixed, moving, mesh=8)
    res["full_affine_of_bspline"] = err_mm(apply([p["bspline"], p["affine"]], tags), target)  # afín(B-spline(p))
    res["full_bspline_of_affine"] = err_mm(apply([p["affine"], p["bspline"]], tags), target)  # B-spline(afín(p))
    res["pipeline_composite"] = err_mm(ae.transfer_points(sitk.CompositeTransform([p["affine"], p["bspline"]]), tags),
                                       target)
    res["bspline_displacement_median_max_mm"] = bspline_displacement(p["bspline"], tags)
    res["seconds"] = round(time.time() - t0, 1)
    return res


def specimens(out: Path, names: list[str]) -> dict:
    res = {}
    for name in names:
        st = g.stage_of(name)
        a = g.load_x4(ATLAS / g.ATLAS_IMAGES[st], CACHE)
        s = g.load_x4(IMAGES / f"{name}.mnc", CACHE)
        fixed, moving = ae.to_sitk(a["downsampled"], a["affine_ds"]), ae.to_sitk(s["downsampled"], s["affine_ds"])
        tags = lm.read_tag(ATLAS / g.ATLAS_TAG[st])
        pub = lm.read_tag(LANDMARKS / f"{name}_Head_Landmarks.tag")

        def score(pts):
            return {"rho": float(lm.procrustes_distances(pts, pub)["rho"]), **err_mm(pts, pub)}

        r = {"stage": st, "identity": score(tags)}
        t0 = time.time()
        p = register_parts(fixed, moving, mesh=None)
        r["affine_only"] = score(ae.transfer_points(p["affine"], tags))
        for label, mesh, sampling in (("preregistered_mesh8_random", 8, "random"),
                                      ("mesh8_regular", 8, "regular"), ("mesh4_regular", 4, "regular")):
            p = register_parts(fixed, moving, mesh=mesh, sampling=sampling)
            r[label] = {**score(apply([p["bspline"], p["affine"]], tags)),
                        "other_order": score(apply([p["affine"], p["bspline"]], tags)),
                        "bspline_displacement_median_max_mm": bspline_displacement(p["bspline"], tags),
                        "bspline_stop": p["bspline_stop"][:60]}
            print(name, label, r[label]["rho"], flush=True)
        r["seconds"] = round(time.time() - t0, 1)
        res[name] = r
    return res


def _foreground(img):
    """Centroide y percentiles 5/95 (mm) de los vóxeles por encima de mediana + ½(p99 − mediana)."""
    sitk = ae._sitk()
    arr = sitk.GetArrayFromImage(img)
    thr = np.percentile(arr, 50) + 0.5 * (np.percentile(arr, 99) - np.percentile(arr, 50))
    idx = np.argwhere(arr > thr)[:, ::-1]
    idx = idx[:: max(1, len(idx) // 20000)]
    phys = np.array([img.TransformContinuousIndexToPhysicalPoint(tuple(float(c) for c in p)) for p in idx])
    return {"centroid_mm": phys.mean(0).round(2).tolist(),
            "p5_mm": np.percentile(phys, 5, 0).round(2).tolist(), "p95_mm": np.percentile(phys, 95, 0).round(2).tolist()}


def _mi(fixed, moving, tx) -> float:
    sitk = ae._sitk()
    r = sitk.ImageRegistrationMethod()
    r.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    r.SetMetricSamplingStrategy(sitk.ImageRegistrationMethod.REGULAR)
    r.SetMetricSamplingPercentage(0.20, 1)
    r.SetInterpolator(sitk.sitkLinear)
    r.SetInitialTransform(tx)
    return float(r.MetricEvaluate(sitk.Cast(fixed, sitk.sitkFloat32), sitk.Cast(moving, sitk.sitkFloat32)))


def geometry(out: Path, names: list[str]) -> dict:
    """¿Comparten imagen y landmarks el espacio físico? ¿Qué hace la inicialización por momentos?"""
    sitk = ae._sitk()
    res = {}
    for name in names:
        st = g.stage_of(name)
        a = g.load_x4(ATLAS / g.ATLAS_IMAGES[st], CACHE)
        s = g.load_x4(IMAGES / f"{name}.mnc", CACHE)
        fixed, moving = ae.to_sitk(a["downsampled"], a["affine_ds"]), ae.to_sitk(s["downsampled"], s["affine_ds"])
        tags = lm.read_tag(ATLAS / g.ATLAS_TAG[st])
        pub = lm.read_tag(LANDMARKS / f"{name}_Head_Landmarks.tag")
        init = sitk.CenteredTransformInitializer(fixed, moving, sitk.AffineTransform(3),
                                                 sitk.CenteredTransformInitializerFilter.MOMENTS)
        res[name] = {
            "same_grid": bool(fixed.GetSize() == moving.GetSize()
                              and np.allclose(fixed.GetOrigin(), moving.GetOrigin())
                              and np.allclose(fixed.GetSpacing(), moving.GetSpacing())
                              and np.allclose(fixed.GetDirection(), moving.GetDirection())),
            "spacing_mm": [round(x, 4) for x in fixed.GetSpacing()],
            "atlas_foreground": _foreground(fixed), "specimen_foreground": _foreground(moving),
            "atlas_tags_centroid_mm": np.mean(tags, 0).round(2).tolist(),
            "published_centroid_mm": np.mean(pub, 0).round(2).tolist(),
            "moments_init_translation_mm": [round(x, 3) for x in init.GetTranslation()],
            "mi_identity": _mi(fixed, moving, sitk.AffineTransform(3)), "mi_moments_init": _mi(fixed, moving, init),
            "identity": err_mm(tags, pub), "moments_init": err_mm(ae.transfer_points(init, tags), pub),
        }
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("synthetic", "specimens", "geometry"))
    ap.add_argument("--names", nargs="*", default=[])
    ap.add_argument("--out", default="results/morpho_trace/v2/verificacion")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res = synthetic(out) if a.cmd == "synthetic" else (specimens if a.cmd == "specimens" else geometry)(out, a.names)
    (out / f"{a.cmd}.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
