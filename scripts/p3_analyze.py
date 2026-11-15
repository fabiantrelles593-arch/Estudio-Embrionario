"""P3 (docs/PREREGISTRO_P3.md §5): grupos sobre el atlas de consenso y análisis del piloto.

  python scripts/p3_analyze.py groups --atlas data/external/musmorph/atlas/IMPC_E15.5_Body_Atlas_Segs.mnc \\
      --out results/p3/grupos.csv
  python scripts/p3_analyze.py pilot --data data/external/musmorph/impc_e15_5 --memos results/p3/memos \\
      --groups results/p3/grupos.csv --out results/p3/analisis_piloto.json

``groups`` fija los grupos «pequeño o delgado» y «grande o compacto» (§5.6) con la profundidad media
interior relativa al vóxel sobre el atlas de consenso, sin mirar especímenes. ``pilot`` construye las 6
condiciones (resolución ×1, ×2, ×4 por segmentador A = atlas propagado y B = MEMOS) de los especímenes del
piloto que tengan las dos segmentaciones, y calcula τ, H-P3a y H-P3b **solo para tiempos y anchura de
intervalos** (el piloto no entra en el confirmatorio). Aplica la regla de ampliación de §4 con la proyección
fijada en la desviación D4: semianchura a 60 = semianchura del piloto × √(n_piloto / 60).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from geovida import p3, p3_data  # noqa: E402

EXPANSION_HALF_WIDTH = 0.10
N_CONFIRM, N_CONFIRM_EXPANDED = 60, 120


def projected_half_width(lo: float, hi: float, n_pilot: int, n_target: int = N_CONFIRM) -> float:
    """Semianchura del IC proyectada a ``n_target`` especímenes, escalando por √(n_piloto / n_target)."""
    if not (math.isfinite(lo) and math.isfinite(hi)) or n_pilot < 2:
        return math.nan
    return (hi - lo) / 2 * math.sqrt(n_pilot / n_target)


def expansion_decision(lo: float, hi: float, n_pilot: int) -> int:
    """60, o 120 si la semianchura proyectada a 60 supera 0,10 (o no se puede proyectar)."""
    hw = projected_half_width(lo, hi, n_pilot)
    return N_CONFIRM_EXPANDED if not math.isfinite(hw) or hw > EXPANSION_HALF_WIDTH else N_CONFIRM


def _specimen_maps(sid: str, data: Path, memos: Path):
    """Mapas del atlas (recuperación nearest, D1) y de MEMOS en una misma caja nativa, con el vóxel."""
    atlas, abox, spacing, _, _ = p3_data.load_labels(data / f"{sid}_Segs.mnc", p3_data.MUSMORPH_LABELS, "nearest")
    z = np.load(memos / f"{sid}_memos.npz")
    lab, box = z["labels"], z["box"]
    ab = np.array([[s.start, s.stop] for s in abox])
    lo = np.minimum(box[:, 0], ab[:, 0])
    hi = np.maximum(box[:, 1], ab[:, 1])
    shape = tuple(int(v) for v in hi - lo)
    a = np.zeros(shape, np.int16)
    a[tuple(slice(ab[i][0] - lo[i], ab[i][1] - lo[i]) for i in range(3))] = atlas
    m = np.zeros(shape, np.uint8)
    m[tuple(slice(box[i][0] - lo[i], box[i][1] - lo[i]) for i in range(3))] = lab
    return {"A": a, "B": m}, spacing


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("groups")
    g.add_argument("--atlas", required=True)
    g.add_argument("--out", required=True)
    p = sub.add_parser("pilot")
    p.add_argument("--data", required=True)
    p.add_argument("--memos", required=True)
    p.add_argument("--groups", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--n-boot", type=int, default=p3.N_BOOT)
    a = ap.parse_args(argv)

    if a.cmd == "groups":
        atlas, _, spacing, _, _ = p3_data.load_labels(a.atlas, p3_data.P3_STRUCTURES, "exact")
        out = p3.groups_from_atlas(atlas, spacing, p3_data.P3_STRUCTURES, p3_data.p3_units())
        out["names"] = [" + ".join(p3_data.KOMP2_NAMES[int(s)] for s in u.split("+")) for u in out["unit"]]
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        out.sort_values("d_over_hgeo").to_csv(a.out, index=False)
        print(out.groupby("group").size().to_string())
        return 0

    memos = Path(a.memos)
    ids = sorted(f.name[: -len("_memos.npz")] for f in memos.glob("*_memos.npz"))
    t0 = time.time()

    def items():
        for sid in ids:
            maps, spacing = _specimen_maps(sid, Path(a.data), memos)
            print(f"  {sid}", flush=True)
            yield sid, maps, spacing

    df = p3.condition_table(items(), p3_data.P3_STRUCTURES, cert_segmenter="A")
    t_measure = time.time() - t0
    df.to_csv(Path(a.out).with_suffix(".conditions.csv"), index=False)
    groups = pd.read_csv(a.groups, dtype={"unit": str})
    t1 = time.time()
    res = p3.evaluate(df, groups, p3_data.p3_units(), n_boot=a.n_boot)
    t_eval = time.time() - t1
    lo, hi = res["delta_ci"]
    summary = {k: v for k, v in res.items() if k != "units"}
    summary.update(specimens=ids, seconds_measure=round(t_measure, 1), seconds_evaluate=round(t_eval, 1),
                   delta_ci_half_width=(hi - lo) / 2 if math.isfinite(lo) else math.nan,
                   projected_half_width_60=projected_half_width(lo, hi, len(ids)),
                   n_confirm_decision=expansion_decision(lo, hi, len(ids)))
    res["units"].to_csv(Path(a.out).with_suffix(".units.csv"), index=False)
    Path(a.out).write_text(json.dumps(summary, indent=1, ensure_ascii=False, default=float), encoding="utf-8")
    print(json.dumps(summary, indent=1, ensure_ascii=False, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
