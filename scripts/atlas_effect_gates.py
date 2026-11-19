"""MT-A (docs/morpho_trace/PREREGISTRO_ATLAS.md §4): puertas previas, una por subcomando.

  python scripts/atlas_effect_gates.py g0d --ids results/onto_map/seleccion.json \\
      --data data/external/musmorph/landmarks_confirm --out results/morpho_trace/g0d.json

``g0d``: reproduce la longitud de **d** con las 717 configuraciones publicadas del confirmatorio de ONTO-MAP
(GPA único, coordenadas tangentes, media E18.5 − media E15.5), con el mismo cargador que ONTO-MAP. Criterio:
longitud en [0,150, 0,164] (publicada: 0,157). No usa datos nuevos.

Las demás puertas (G0-a, G0-b, G0-c, G1, G2) se añaden cuando estén los datos que necesitan. Los resultados
quedan fuera de git (``results/``), como los datos.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from onto_map_pilot import _load  # noqa: E402

from geovida import atlas_effect as ae  # noqa: E402
from geovida.provenance import git_state  # noqa: E402

G0D_RANGE = (0.150, 0.164)
PUBLISHED_D = 0.157


def g0d(configs: dict) -> dict:
    """Puerta G0-d a partir de {'E15.5': (n, k, 3), 'E18.5': (n, k, 3)}."""
    r = ae.published_direction(configs["E15.5"], configs["E18.5"])
    lo, hi = G0D_RANGE
    r.update({"published": PUBLISHED_D, "range": list(G0D_RANGE), "passed": lo <= r["d_length"] <= hi})
    return r


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("g0d")
    p.add_argument("--ids", required=True)
    p.add_argument("--data", required=True)
    p.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    sel = json.loads(Path(a.ids).read_text(encoding="utf-8"))
    res = {"gate": "G0-d", **g0d(_load(sel, "confirm", Path(a.data))), "provenance": git_state()}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "provenance"}, default=float))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
