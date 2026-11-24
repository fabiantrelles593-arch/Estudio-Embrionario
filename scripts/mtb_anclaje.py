"""MT-B (docs/morpho_trace/PREREGISTRO_ANCLAJE_ATLAS.md): ¿la separación entre estadios es la diferencia entre atlas?

    python scripts/mtb_anclaje.py gates     # G0-d‴, G0-p y G0-t
    python scripts/mtb_anclaje.py analyze   # MT-B1–MT-B3 y sensibilidad (solo si las tres puertas pasaron)

Sin registro ni descargas: landmarks de los dos atlas y las 597 configuraciones publicadas del confirmatorio de v2.
Resultados en ``results/morpho_trace/mtb/`` (fuera de git). Solo datos animales publicados (MusMorph/IMPC,
CC BY 4.0); nada humano ni clínico.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atlas_effect_gates as gates  # noqa: E402

from geovida import atlas_anchor as aa  # noqa: E402
from geovida import landmarks as lm  # noqa: E402
from geovida.provenance import git_state  # noqa: E402

OUT = Path("results/morpho_trace/mtb")


def _read(p: Path) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _write(res: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    res["provenance"] = git_state()
    out.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "provenance"}, default=float, ensure_ascii=False))


def load_inputs(sel_v2: Path, lmdir: Path, atlas_dir: Path):
    pub = gates._load(_read(sel_v2), "confirm", lmdir)
    atlas = {st: np.asarray(lm.read_tag(atlas_dir / gates.ATLAS_TAG[st]), float) for st in aa.STAGES}
    return np.asarray(pub["E15.5"], float), np.asarray(pub["E18.5"], float), atlas


def run_gates(pub15, pub18, atlas) -> dict:
    s = aa.shape_space(pub15, pub18)
    g_d = aa.gate_d(float(np.linalg.norm(s["t18"].mean(axis=0) - s["t15"].mean(axis=0))))
    k = aa.N_PROJ_CHECK   # las 5 primeras de la lista confirm (E15.5 primero)
    g_p = aa.gate_projection(pub15[:k], s["t15"][:k], s["mean"])
    g_t = aa.gate_tangent(atlas, s["mean"])
    return {"gates": {"G0-d‴": g_d, "G0-p": g_p, "G0-t": g_t}, "rho_max_597": s["rho_max"],
            "gpa_converged": s["converged"], "passed": bool(g_d["passed"] and g_p["passed"] and g_t["passed"])}


def run_analysis(pub15, pub18, atlas) -> dict:
    s = aa.shape_space(pub15, pub18)
    a15, a18 = (aa.project_to_tangent(atlas[st], s["mean"]) for st in aa.STAGES)
    main = aa.anchor_decomposition(s["t15"], s["t18"], a15, a18)
    sens = {"in_gpa": aa.sensitivity_in_gpa(pub15, pub18, atlas),
            "regpa": aa.sensitivity_regpa(pub15, pub18, atlas),
            "halves_e18": aa.sensitivity_halves(s["t15"], s["t18"], a15, a18)}
    return {"analysis": "MT-B", **main, "sensitivity": sens,
            "verdict": {"MT-B1": main["mtb1"]["verdict"], "MT-B2": main["mtb2"]["verdict"]}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["gates", "analyze"])
    ap.add_argument("--sel-v2", default="results/morpho_trace/v2/seleccion_v2.json", help="confirmatorio de 597 (d)")
    ap.add_argument("--landmarks", default="data/external/musmorph/landmarks_confirm")
    ap.add_argument("--atlas", default="data/external/musmorph/atlas")
    a = ap.parse_args(argv)
    pub15, pub18, atlas = load_inputs(Path(a.sel_v2), Path(a.landmarks), Path(a.atlas))
    if a.cmd == "gates":
        res = run_gates(pub15, pub18, atlas)
        _write(res, OUT / "gates.json")
        return 0 if res["passed"] else 1
    p = OUT / "gates.json"
    if not p.exists() or not _read(p).get("passed"):
        raise SystemExit(f"las puertas no están superadas ({p}); el preregistro no permite seguir")
    _write(run_analysis(pub15, pub18, atlas), OUT / "analisis.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
