"""H11: transferencia del certificado congelado a ecografía 3D real de embrión de ratón.

Aplica ``docs/PREREGISTRO_H11.md`` tal como está escrito (y las aclaraciones de su sección
«Desviaciones», fechadas antes de abrir ningún dato).

* ``run_cases``: recorre un manifiesto (embrión, estructura, imagen, etiqueta, valor de etiqueta) y
  aplica ``realdata.compare_case`` con los modelos congelados, sin reajustar nada.
* ``evaluate_h11``: veredictos H11a–H11e con intervalos por remuestreo de **embriones**.

La referencia de una imagen real es un contorno humano: lo que se mide es acuerdo, no error exacto.
Solo investigación y educación; sin uso clínico.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from .realdata import compare_case, load_volume

SEGMENTERS = ("global", "otsu", "smoothed_otsu")
ROI_MARGIN = 0.25          # solo para el ventrículo: favorece al método y se declara siempre
BOOT_SEED = 20261126
N_BOOT = 2000
MIN_GREEN = 30
MIN_EMBRYOS_GREEN = 15
TOLERANCE_PRIMARY = 0.10
IN_DOMAIN_MAX = 0.50
MANIFEST_COLUMNS = ("embryo_id", "structure", "image", "label", "label_value")


def run_cases(manifest: pd.DataFrame, root=".", profile: str = "realistic", frozen: dict | None = None,
              segmenters=SEGMENTERS) -> pd.DataFrame:
    """Una fila por (caso del manifiesto × segmentador). Las rutas son relativas a ``root``.

    ``structure`` = ``body`` (se mide con el umbral de toda la imagen) o ``ventricle`` (el umbral se
    calcula en una caja alrededor de la referencia, declarada en ``roi_margin``).
    """
    missing = [c for c in MANIFEST_COLUMNS if c not in manifest.columns]
    if missing:
        raise ValueError(f"al manifiesto le faltan las columnas {missing}")
    root = Path(root)
    rows = []
    for _, case in manifest.iterrows():
        image, spacing, _ = load_volume(root / case["image"])
        label, label_spacing, _ = load_volume(root / case["label"])
        if label.shape != image.shape:
            raise ValueError(f"{case['embryo_id']}: imagen {image.shape} y etiqueta {label.shape} no coinciden")
        if not np.allclose(spacing, label_spacing, rtol=1e-4):
            raise ValueError(f"{case['embryo_id']}: la imagen y la etiqueta no comparten tamaño de vóxel")
        ref = label == case["label_value"]
        if not ref.any():
            raise ValueError(f"{case['embryo_id']}: el valor de etiqueta {case['label_value']} no aparece")
        margin = ROI_MARGIN if case["structure"] == "ventricle" else None
        for seg in segmenters:
            out = compare_case(image, spacing, ref, seg, profile, frozen, roi_margin=margin)
            rows.append({"embryo_id": case["embryo_id"], "structure": case["structure"], **out})
    return pd.DataFrame(rows)


# --- Veredictos --------------------------------------------------------------------------------

def _embryo_bootstrap(df: pd.DataFrame, bad: pd.Series, n_boot: int, seed: int) -> list[float]:
    """Intervalo percentil 95 % de la fracción de casos malos, remuestreando embriones."""
    g = pd.DataFrame({"embryo_id": df["embryo_id"].to_numpy(), "bad": bad.to_numpy(float)})
    per = g.groupby("embryo_id")["bad"].agg(["sum", "count"])
    s, c = per["sum"].to_numpy(float), per["count"].to_numpy(float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(per), size=(n_boot, len(per)))
    ratio = s[idx].sum(axis=1) / c[idx].sum(axis=1)
    lo, hi = np.percentile(ratio, [2.5, 97.5])
    return [float(lo), float(hi)]


def _fraction_bad(rows: pd.DataFrame, bad: pd.Series, n_boot: int, seed: int) -> dict:
    n = int(len(rows))
    emb = int(rows["embryo_id"].nunique())
    out = {"n_green": n, "n_embryos_green": emb}
    if n < MIN_GREEN or emb < MIN_EMBRYOS_GREEN:
        return {**out, "estimate": None, "ci": None, "verdict": "no evaluable"}
    est = float(bad.mean())
    ci = _embryo_bootstrap(rows, bad, n_boot, seed)
    return {**out, "estimate": est, "ci": ci}


def evaluate_h11(df: pd.DataFrame, n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> dict:
    """Veredictos de H11 sobre la tabla de ``run_cases``. No reajusta nada."""
    body = df[df["structure"] == "body"]
    res: dict = {"n_cases": int(len(df)), "n_embryos": int(df["embryo_id"].nunique())}

    # H11a: la guardia rechaza lo que no se parece (cuerpo, por segmentador)
    fr = {s: float(body.loc[body["segmenter"] == s, "in_domain_volume"].astype(bool).mean())
          for s in SEGMENTERS if (body["segmenter"] == s).any()}
    passed = sum(v <= IN_DOMAIN_MAX for v in fr.values())
    res["h11a"] = {"in_domain_fraction": fr, "passed": passed,
                   "verdict": "no evaluable" if not fr else
                   ("apoyada" if passed == len(SEGMENTERS) else
                    ("parcial" if passed == len(SEGMENTERS) - 1 else "no apoyada"))}

    # H11b (primaria): verde con guardia, fracción con |error| > 10 %
    green = body[body["light_volume"] == "verde"]
    b = _fraction_bad(green, ~green["ok10"].astype(bool), n_boot, seed)
    if b["estimate"] is not None:
        b["verdict"] = ("apoyada" if b["estimate"] <= TOLERANCE_PRIMARY else
                        ("no apoyada" if b["ci"][0] > TOLERANCE_PRIMARY else "no concluyente"))
    res["h11b"] = b

    # H11c: sin guardia, el semáforo de v0.3 falla (supera 10 %)
    free = body[body["light_volume_without_guard"] == "verde"]
    c = _fraction_bad(free, ~free["ok10"].astype(bool), n_boot, seed)
    if c["estimate"] is not None:
        c["verdict"] = "apoyada" if c["estimate"] > TOLERANCE_PRIMARY else "no apoyada"
    res["h11c"] = c

    # H11d: acuerdo (descriptivo, sin veredicto)
    rows = []
    for (seg, st), g in df.groupby(["segmenter", "structure"]):
        ae = g["rel_error_volume"].abs()
        rows.append({"segmenter": seg, "structure": st, "n": int(len(g)),
                     "dice_median": float(g["dice"].median()), "dice_min": float(g["dice"].min()),
                     "dice_max": float(g["dice"].max()),
                     "abs_error_median": float(ae.median()), "abs_error_min": float(ae.min()),
                     "abs_error_max": float(ae.max()),
                     "ok10": float(g["ok10"].astype(bool).mean()), "ok5": float(g["ok5"].astype(bool).mean())})
    res["h11d"] = {"rows": rows}

    # H11e: topología del cuerpo con luz verde de topología
    tg = body[body["light_topology"] == "verde"]
    e = _fraction_bad(tg, ~tg["topology_ok"].astype(bool), n_boot, seed)
    if e["estimate"] is not None:
        e["verdict"] = "apoyada" if e["estimate"] <= TOLERANCE_PRIMARY else "no apoyada"
    first = body.drop_duplicates("embryo_id")
    simple = first["betti_reference"].map(lambda b: tuple(int(x) for x in b) == (1, 0, 0))
    e["reference_not_simple"] = float((~simple).mean()) if len(first) else math.nan
    res["h11e"] = e
    return res
