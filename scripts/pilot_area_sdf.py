"""EXPLORACION (descartable): ¿una superficie de distancia con signo reduce el sesgo de area?"""
import numpy as np, pandas as pd
from scipy import ndimage as ndi
from skimage.measure import marching_cubes, mesh_surface_area
from geovida.imaging import render, spec_for_t_over_h
from geovida.phantoms import make_phantom
from geovida.segment import segment
from geovida.measure import _area_mc, _area_faces

def area_sdf(mask, spacing, sigma_vox):
    sp = np.asarray(spacing, float)
    m = np.pad(mask, 3)
    d_in = ndi.distance_transform_edt(m, sampling=sp)
    d_out = ndi.distance_transform_edt(~m, sampling=sp)
    half = 0.5 * sp.min()
    sdf = np.where(m, d_in - half, -(d_out - half)).astype(np.float32)
    if sigma_vox > 0:
        sdf = ndi.gaussian_filter(sdf, sigma=sigma_vox * sp.min() / sp)
    try:
        v, f, _, _ = marching_cubes(sdf, level=0.0, spacing=tuple(sp))
    except (ValueError, RuntimeError):
        return 0.0
    return float(mesh_surface_area(v, f))

rows = []
for shape in ("ball", "ellipsoid", "shell", "tube"):
    for tov in (2, 3, 4, 6, 8, 12):
        for rep in range(8):
            rng = np.random.default_rng(np.random.SeedSequence([20261111, hash(shape) % 1000, tov, rep]))
            ph = make_phantom(shape, 1.0)
            spec = spec_for_t_over_h(float(tov), 1.0, "ideal", t=1.0)
            out = render(ph, spec, rng)
            mask = segment("global", out.image, out.spacing)
            S = ph.truth.surface_area
            r = dict(shape=shape, tov=tov, rep=rep,
                     mc=_area_mc(mask, out.spacing)/S - 1, faces=_area_faces(mask, out.spacing)/S - 1)
            for s in (0, 0.5, 1.0):
                r[f"sdf{s}"] = area_sdf(mask, out.spacing, s)/S - 1
            rows.append(r)
df = pd.DataFrame(rows)
print((df.groupby(["shape", "tov"]).median(numeric_only=True).drop(columns="rep")*100).round(1).to_string())
