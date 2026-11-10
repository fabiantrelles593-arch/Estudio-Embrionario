"""Exporta series de crecimiento (4D) medidas con geovida a un JSON que lee el visor de Unity.

Cada etapa lleva los vóxeles de la superficie de la máscara, la luz del semáforo de volumen
(H6, solo máscara y vóxel) y la comparación con la verdad. Perfil «ideal», umbral 0.5.

  python scripts/export_unity.py            # escribe unity/Assets/StreamingAssets/geovida_series.json
"""
import json
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from geovida.budget import adequacy
from geovida.growth import TRUE_RATE, stage_sizes
from geovida.imaging import ImagingSpec, render
from geovida.phantoms import make_phantom
from geovida.segment import segment

SHAPES = ("ball", "torus", "capsule", "dumbbell", "shell")
SEED = 20261130          # solo para el visor; no interviene en ninguna hipótesis
OUT = Path("unity/Assets/StreamingAssets/geovida_series.json")


def surface_voxels(mask: np.ndarray) -> np.ndarray:
    """Índices (i, j, k) de los vóxeles de la máscara con algún vecino de cara vacío."""
    interior = ndi.binary_erosion(mask, structure=ndi.generate_binary_structure(3, 1),
                                  border_value=0)
    return np.argwhere(mask & ~interior)


def main():
    series = []
    for s_idx, shape in enumerate(SHAPES):
        stages = []
        for k, t in enumerate(stage_sizes()):
            ph = make_phantom(shape, t=float(t))
            rng = np.random.default_rng(np.random.SeedSequence([SEED, s_idx, k]))
            out = render(ph, ImagingSpec(h_xy=1.0), rng)
            mask = segment("global", out.image, out.spacing)
            rep = adequacy(mask, out.spacing, "global", "ideal")
            meas = rep["measurements"]
            betti = [int(meas.get(f"b{i}_26", 0)) for i in range(3)]
            stages.append({
                "stage": k, "tOverH": round(float(t), 3),
                "dims": [int(v) for v in mask.shape], "spacing": [float(v) for v in out.spacing],
                "volume": float(rep["volume"]), "volumeTrue": float(ph.truth.volume),
                "errVolume": float(rep["volume"] / ph.truth.volume - 1.0),
                "p": float(rep["p_volume_ok"]), "light": rep["light"],
                "betti": betti, "bettiTrue": [int(v) for v in ph.truth.betti],
                "voxels": surface_voxels(mask).astype(int).ravel().tolist(),
            })
        series.append({"shape": shape, "trueRate": TRUE_RATE, "stages": stages})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"note": "Datos sintéticos de geovida; sin uso clínico.",
                               "series": series}, separators=(",", ":")))
    n = sum(len(st["voxels"]) // 3 for s in series for st in s["stages"])
    print(f"{OUT}: {len(series)} formas x 8 etapas, {n} vóxeles de superficie, "
          f"{OUT.stat().st_size / 1e6:.2f} MB")
    for s in series:
        print(s["shape"], [st["light"][0] for st in s["stages"]],
              [round(100 * st["errVolume"]) for st in s["stages"]])


if __name__ == "__main__":
    main()
