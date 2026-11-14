"""EXPLORATORIO, resultado negativo: estimador del desenfoque por perfil de borde (docs/REAL2D_METODO.md).

No se usa en el programa. Se conserva para que el resultado se pueda reproducir: python scripts/explore_blur_estimator.py
"""
import numpy as np, warnings
from scipy import ndimage as ndi
from scipy.optimize import curve_fit
from scipy.special import erf
from geovida import biometry as bio
from geovida.twod import render2d, segment2d

def esf_fwhm(img, mask, D=10.0, step=0.5):
    m = bio.largest_component(mask)
    din = ndi.distance_transform_edt(m); dout = ndi.distance_transform_edt(~m)
    sd = np.where(m, din - 0.5, -(dout - 0.5))
    sel = np.abs(sd) <= D
    d = sd[sel]; v = img[sel]
    edges = np.arange(-D, D + step, step); k = np.digitize(d, edges)
    xs, ys = [], []
    for i in range(1, len(edges)):
        s = k == i
        if s.sum() >= 5: xs.append(d[s].mean()); ys.append(v[s].mean())
    xs, ys = np.array(xs), np.array(ys)
    f = lambda x, a, b, sg, c: a + b * erf((x - c) / (np.sqrt(2) * sg))
    p0 = [ys.mean(), (ys.max() - ys.min()) / 2, 1.5, 0.0]
    try:
        p, _ = curve_fit(f, xs, ys, p0=p0, bounds=([-np.inf, -np.inf, 0.2, -3], [np.inf, np.inf, 12, 3]))
    except Exception:
        return np.nan
    return 2.3548 * p[2]

warnings.filterwarnings("ignore")
rows = []
for kind_n in (80, 130, 210):
    for f in (1.0, 2.0, 3.5, 5.0):
        est = []
        for seed in range(12):
            L = 20.0; h = L / kind_n
            ph = bio.make_body(L)
            img = render2d(ph, bio.spec_for(h, f), np.random.default_rng([7, kind_n, int(f*10), seed])).image
            mask = segment2d("smoothed_otsu", img, h)
            est.append(esf_fwhm(img, mask))
        est = np.array(est)
        print(f"n={kind_n:4d} f_true={f:3.1f}  est median={np.nanmedian(est):5.2f}  p10={np.nanpercentile(est,10):5.2f} p90={np.nanpercentile(est,90):5.2f}  ratio={np.nanmedian(est)/f:4.2f}")
