"""H19: segmentador aprendido de dos etapas para ecografía 3D de embrión de ratón, con certificado.

Aplica ``docs/PREREGISTRO_H19.md``. H18 mostró que ningún segmentador de umbral, ni con limpieza, acierta en estos
datos (1 de 136 casos de entrenamiento a ≤ 10 %). La literatura del propio conjunto usa redes 3D en dos etapas
(una segmentación gruesa y un refinamiento en una caja alrededor, con la probabilidad gruesa como entrada:
«auto-context»; Xu et al. 2020, doi:10.1109/isbi45749.2020.9098387; Qiu et al. 2021,
doi:10.1109/TUFFC.2021.3068156). Aquí se **reimplementa la idea desde la publicación**, con código propio y una
red pequeña que cabe en una CPU de 4 núcleos; no se copia código ni pesos de nadie.

* ``fit_calibration_split``: los embriones de entrenamiento de H18 se reparten, con semilla fija, en ajuste (la red)
  y calibración (el certificado). La prueba de H18 sigue sin abrir.
* ``UNet3D``, ``train``, ``predict``: red 3D pequeña; etapa 1 a ¼ de resolución sobre todo el volumen, etapa 2 a ½ de
  resolución en la caja de la etapa 1, con la probabilidad gruesa como segundo canal.
* ``segment_full``: máscara a resolución completa; ``uncertain_band``: fracción del borde con probabilidad dudosa
  (observable propio de la red para el certificado).

La referencia es un contorno humano: se mide acuerdo. Solo investigación con datos animales; sin uso clínico.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import ndimage as ndi

SEED = 20261121
CAL_FRACTION = 0.20
COARSE = 4                      # etapa 1: ¼ de resolución
FINE = 2                        # etapa 2: ½ de resolución
ROI_MARGIN = 6                  # vóxeles de la etapa 2 alrededor de la caja gruesa
MULTIPLE = 8                    # tres reducciones de la U-Net
EPOCHS = {"coarse": 150, "fine": 100}
CHANNELS = 8
LR = 1e-3
THREADS = 2
UNCERTAIN = (0.2, 0.8)


# --- reparto -----------------------------------------------------------------------------------------
def fit_calibration_split(train: pd.DataFrame, fraction: float = CAL_FRACTION, seed: int = SEED) -> pd.DataFrame:
    """Columna ``role`` (``fit`` / ``cal``) por embrión: nunca un embrión a los dos lados."""
    emb = sorted(train["embryo_id"].unique())
    order = np.random.default_rng(seed).permutation(len(emb))
    n_cal = max(1, int(round(fraction * len(emb))))
    cal = {emb[i] for i in order[:n_cal]}
    return train.assign(role=np.where(train["embryo_id"].isin(cal), "cal", "fit"))


# --- remuestreo --------------------------------------------------------------------------------------
def downsample(image: np.ndarray, factor: int) -> np.ndarray:
    """Media por bloques ``factor``³ (recorta el sobrante del borde)."""
    s = [n // factor * factor for n in image.shape]
    a = np.asarray(image, np.float32)[: s[0], : s[1], : s[2]]
    return a.reshape(s[0] // factor, factor, s[1] // factor, factor, s[2] // factor, factor).mean(axis=(1, 3, 5))


def normalize(image: np.ndarray) -> np.ndarray:
    """Percentiles 1–99 → [0, 1]: la intensidad absoluta de la ecografía cambia entre adquisiciones."""
    lo, hi = np.percentile(image, [1, 99])
    return np.clip((image - lo) / max(hi - lo, 1e-6), 0, 1).astype(np.float32)


def pad_to(a: np.ndarray, multiple: int = MULTIPLE) -> tuple[np.ndarray, tuple]:
    pads = tuple((0, (-n) % multiple) for n in a.shape)
    return np.pad(a, pads, mode="edge"), pads


def upsample_prob(prob: np.ndarray, factor: int, shape) -> np.ndarray:
    """Probabilidad a otra rejilla por interpolación lineal, centrando los bloques (orden 1)."""
    zoom = [factor] * 3
    up = ndi.zoom(prob.astype(np.float32), zoom, order=1, mode="nearest", grid_mode=True)
    out = np.zeros(shape, np.float32)
    s = tuple(slice(0, min(a, b)) for a, b in zip(shape, up.shape))
    out[s] = up[s]
    return out


def bbox(mask: np.ndarray, margin: int):
    idx = np.nonzero(mask)
    if not idx[0].size:
        return None
    return tuple(slice(max(0, int(i.min()) - margin), min(n, int(i.max()) + 1 + margin))
                 for i, n in zip(idx, mask.shape))


# --- red ---------------------------------------------------------------------------------------------
def _torch():
    import torch
    torch.set_num_threads(THREADS)
    return torch


def UNet3D(in_ch: int = 1, c: int = CHANNELS):
    torch = _torch()
    nn = torch.nn

    def block(i, o):
        return nn.Sequential(nn.Conv3d(i, o, 3, padding=1), nn.InstanceNorm3d(o), nn.LeakyReLU(0.1),
                             nn.Conv3d(o, o, 3, padding=1), nn.InstanceNorm3d(o), nn.LeakyReLU(0.1))

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.e1, self.e2, self.e3 = block(in_ch, c), block(c, 2 * c), block(2 * c, 4 * c)
            self.b = block(4 * c, 8 * c)
            self.u3, self.d3 = nn.ConvTranspose3d(8 * c, 4 * c, 2, 2), block(8 * c, 4 * c)
            self.u2, self.d2 = nn.ConvTranspose3d(4 * c, 2 * c, 2, 2), block(4 * c, 2 * c)
            self.u1, self.d1 = nn.ConvTranspose3d(2 * c, c, 2, 2), block(2 * c, c)
            self.out = nn.Conv3d(c, 1, 1)
            self.pool = nn.MaxPool3d(2)

        def forward(self, x):
            e1 = self.e1(x)
            e2 = self.e2(self.pool(e1))
            e3 = self.e3(self.pool(e2))
            b = self.b(self.pool(e3))
            d3 = self.d3(torch.cat([self.u3(b), e3], 1))
            d2 = self.d2(torch.cat([self.u2(d3), e2], 1))
            return self.out(self.d1(torch.cat([self.u1(d2), e1], 1)))

    return Net()


def _loss(logits, target):
    torch = _torch()
    bce = torch.nn.functional.binary_cross_entropy_with_logits(logits, target)
    p = torch.sigmoid(logits)
    dice = 1 - (2 * (p * target).sum() + 1) / (p.sum() + target.sum() + 1)
    return bce + dice


def train(samples: list[tuple[np.ndarray, np.ndarray]], epochs: int, seed: int = SEED, in_ch: int = 1,
          log=None):
    """Entrena con pares (entrada [C, Z, Y, X], objetivo [Z, Y, X]) ya múltiplos de 8. Volteos al azar por eje."""
    torch = _torch()
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    net = UNet3D(in_ch)
    opt = torch.optim.Adam(net.parameters(), LR)
    for ep in range(epochs):
        total = 0.0
        for k in rng.permutation(len(samples)):
            x, y = samples[k]
            for ax in range(3):
                if rng.random() < 0.5:
                    x, y = np.flip(x, ax + 1), np.flip(y, ax)
            xt = torch.from_numpy(np.ascontiguousarray(x))[None]
            yt = torch.from_numpy(np.ascontiguousarray(y, dtype=np.float32))[None, None]
            opt.zero_grad()
            loss = _loss(net(xt), yt)
            loss.backward()
            opt.step()
            total += float(loss.detach())
        if log:
            log(ep, total / max(len(samples), 1))
    return net


def predict(net, x: np.ndarray) -> np.ndarray:
    torch = _torch()
    net.eval()
    with torch.no_grad():
        return torch.sigmoid(net(torch.from_numpy(np.ascontiguousarray(x))[None]))[0, 0].numpy()


def save(net, path):
    torch = _torch()
    torch.save(net.state_dict(), str(path))


def load(path, in_ch: int = 1):
    torch = _torch()
    net = UNet3D(in_ch)
    net.load_state_dict(torch.load(str(path), weights_only=True))
    return net


# --- muestras de cada etapa -------------------------------------------------------------------------
def coarse_sample(image: np.ndarray, ref: np.ndarray | None = None):
    x, _ = pad_to(normalize(downsample(image, COARSE)))
    y = None if ref is None else pad_to((downsample(ref.astype(np.float32), COARSE) >= 0.5).astype(np.float32))[0]
    return x[None], y


def fine_sample(image: np.ndarray, coarse_prob_full: np.ndarray, ref: np.ndarray | None = None):
    """Caja de la etapa 1 (umbral 0,5) a ½ resolución, con la probabilidad gruesa como segundo canal."""
    img2 = normalize(downsample(image, FINE))
    p2 = downsample(coarse_prob_full, FINE)
    box = bbox(p2 >= 0.5, ROI_MARGIN)
    if box is None:
        return None
    xi, _ = pad_to(img2[box])
    xp, _ = pad_to(p2[box])
    y = None
    if ref is not None:
        y = pad_to((downsample(ref.astype(np.float32), FINE)[box] >= 0.5).astype(np.float32))[0]
    return np.stack([xi, xp]), y, box


def segment_full(coarse_net, fine_net, image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Máscara y probabilidad a resolución completa (la probabilidad fina dentro de la caja; 0 fuera)."""
    xc, _ = coarse_sample(image)
    pc = predict(coarse_net, xc)
    pc_full = upsample_prob(pc, COARSE, image.shape)
    fs = fine_sample(image, pc_full)
    prob = np.zeros(image.shape, np.float32)
    if fs is None:
        return prob >= 0.5, prob
    xf, _, box = fs
    pf = predict(fine_net, xf)
    size2 = tuple(s.stop - s.start for s in box)
    pf = pf[: size2[0], : size2[1], : size2[2]]
    full_box = tuple(slice(s.start * FINE, s.stop * FINE) for s in box)
    target = tuple(slice(b.start, min(b.stop, n)) for b, n in zip(full_box, image.shape))
    up = upsample_prob(pf, FINE, tuple(t.stop - t.start for t in target))
    prob[target] = up
    mask = prob >= 0.5
    lab, n = ndi.label(mask, structure=np.ones((3, 3, 3), bool))
    if n > 1:                                       # el cuerpo es una pieza: fuera las islas
        sizes = np.bincount(lab.ravel())
        sizes[0] = 0
        mask = lab == int(sizes.argmax())
    return mask, prob


FEATURES = ("ln_d_over_hgeo", "ln_snr_hat", "ln_edge_width", "uncertain_band")


def feature_matrix(df: pd.DataFrame) -> np.ndarray:
    cols = [np.log(df[f.removeprefix("ln_")].to_numpy(float)) if f.startswith("ln_") else df[f].to_numpy(float)
            for f in FEATURES]
    return np.column_stack(cols)


def fit_certificate(df: pd.DataFrame) -> dict:
    """Como ``h18.fit_certificate`` pero con el observable propio de la red (``uncertain_band``)."""
    from .analysis import fit_logit_multi
    from .h18 import RIDGE, TOLERANCE, fit_envelope

    X = feature_matrix(df)
    good = np.isfinite(X).all(axis=1)
    y = (df["rel_error_volume"].abs() <= TOLERANCE).to_numpy(float)
    model = fit_logit_multi(X[good], y[good], ridge=RIDGE, features=FEATURES)
    return {"model": model, "envelope": fit_envelope(df[good]), "n_train": int(good.sum())}


def lights(df: pd.DataFrame, cert: dict) -> pd.DataFrame:
    from .analysis import predict_logit_multi
    from .budget import traffic_light
    from .h18 import inside

    X = feature_matrix(df)
    good = np.isfinite(X).all(axis=1)
    p = np.zeros(len(df))
    if good.any():
        p[good] = predict_logit_multi(cert["model"], X[good])
    dom = inside(df, cert["envelope"]) & good
    free = np.array([traffic_light(float(v)) for v in p])
    return df.assign(p_ok10=p, in_domain=dom, light_without_guard=free,
                     light=np.where((free == "verde") & ~dom, "amarillo", free))


def out_of_fold(df: pd.DataFrame, n_folds: int = 5, seed: int = SEED) -> pd.DataFrame:
    from .h18 import embryo_folds

    fold = df["embryo_id"].map(embryo_folds(df["embryo_id"], n_folds, seed))
    parts = [lights(df[fold == k], fit_certificate(df[fold != k])) for k in range(n_folds) if (fold == k).any()]
    return pd.concat(parts).loc[df.index]


MIN_OK10_CAL = 0.50            # puerta S: el segmentador acierta en al menos la mitad de la calibración
MIN_GREEN_CAL = 10             # puerta C: al menos 10 verdes fuera de pliegue en la calibración ...
MAX_FAIL_CAL = 0.10            # ... y como mucho el 10 % de ellas fallan


def gates(cal: pd.DataFrame) -> dict:
    """Puertas S (segmentador) y C (certificado) sobre los casos de calibración, que la red no vio."""
    ok10 = float((cal["rel_error_volume"].abs() <= 0.10).mean()) if len(cal) else math.nan
    s = {"ok10": ok10, "passed": bool(ok10 >= MIN_OK10_CAL)}
    if not s["passed"]:
        return {"S": s, "C": {"passed": False, "reason": "no se evalúa sin la puerta S"}, "passed": False}
    oof = out_of_fold(cal)
    g = oof[oof["light"] == "verde"]
    fail = float((g["rel_error_volume"].abs() > 0.10).mean()) if len(g) else math.nan
    c = {"n_green": int(len(g)), "fail": fail,
         "passed": bool(len(g) >= MIN_GREEN_CAL and math.isfinite(fail) and fail <= MAX_FAIL_CAL)}
    return {"S": s, "C": c, "passed": bool(s["passed"] and c["passed"])}


def uncertain_band(prob: np.ndarray, mask: np.ndarray) -> float:
    """Fracción de los vóxeles del borde de la máscara (±1 vóxel) con probabilidad entre 0,2 y 0,8."""
    if not mask.any():
        return math.nan
    edge = ndi.binary_dilation(mask) & ~ndi.binary_erosion(mask)
    p = prob[edge]
    return float(((p > UNCERTAIN[0]) & (p < UNCERTAIN[1])).mean())
