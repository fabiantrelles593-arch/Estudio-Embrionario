"""Diagnóstico exploratorio de G1 (MT-A v2). No cambia ningún veredicto.
rho por estadio: (a) transferido por el registro propio vs publicado; (b) landmarks del atlas sin
transformar (identidad; las imágenes ya están en la rejilla de su atlas) vs publicado; (c) pares
entre especímenes del mismo estadio."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, "scripts")
import atlas_effect_gates as g
from geovida import landmarks as lm

v2 = Path("results/morpho_trace/v2")
sel = json.loads((v2 / "seleccion_v2.json").read_text(encoding="utf-8"))
lmdir = Path("data/external/musmorph/landmarks_confirm")
atlas = Path("data/external/musmorph/atlas")
tags = {st: lm.read_tag(atlas / f) for st, f in g.ATLAS_TAG.items()}
out = {}
for st in ("E15.5", "E18.5"):
    names = sel["pilot"][st]
    pub = [lm.read_tag(lmdir / f"{b}_Head_Landmarks.tag") for b in names]
    own = [np.array(json.loads((v2 / "registros" / f"{b}__atlas_{st}.json").read_text(encoding="utf-8"))["points"])
           for b in names]
    rt = [lm.procrustes_distances(a, p)["rho"] for a, p in zip(own, pub)]
    ri = [lm.procrustes_distances(tags[st], p)["rho"] for p in pub]
    rp = [lm.procrustes_distances(pub[i], pub[j])["rho"] for i in range(len(pub)) for j in range(i + 1, len(pub))]
    # desplazamiento medio en mm (sin superponer) entre transferido y publicado, y entre atlas y publicado
    dt = [float(np.median(np.linalg.norm(a - p, axis=1))) for a, p in zip(own, pub)]
    di = [float(np.median(np.linalg.norm(tags[st] - p, axis=1))) for p in pub]
    q = lambda x: [float(np.percentile(x, k)) for k in (0, 50, 100)]
    out[st] = {"rho_transfer_min_med_max": q(rt), "rho_identity_min_med_max": q(ri),
               "rho_pairs_min_med_max": q(rp), "transfer_better_than_identity": int(sum(a < b for a, b in zip(rt, ri))),
               "n": len(names), "median_mm_transfer": float(np.median(dt)), "median_mm_identity": float(np.median(di))}
print(json.dumps(out, indent=1))
(v2 / "g1_diagnostico_exploratorio.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
