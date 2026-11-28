"""MT-C (docs/morpho_trace/PREREGISTRO_HOMOLOGOS.md): MT-B restringido a los 22 landmarks anatómicos homólogos.

    python scripts/mtc_homologos.py gates     # G0-o, G0-p₂₂ y G0-t₂₂
    python scripts/mtc_homologos.py analyze   # MT-C1–MT-C3 y sensibilidad (solo si las tres puertas pasaron)

Sin registro. Landmarks de los dos atlas (FaceBase; copia de GitHub solo para G0-o) y las 597 configuraciones
publicadas del confirmatorio de v2. Resultados en ``results/morpho_trace/mtc/`` (fuera de git). Solo datos animales
publicados (MusMorph/IMPC, CC BY 4.0); nada humano ni clínico.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atlas_effect_gates as gates  # noqa: E402
from mtb_anclaje import load_inputs  # noqa: E402

from geovida import atlas_anchor as aa  # noqa: E402
from geovida import landmarks as lm  # noqa: E402
from geovida.provenance import git_state  # noqa: E402

OUT = Path("results/morpho_trace/mtc")


def _read(p: Path) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _write(res: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    res["provenance"] = git_state()
    out.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "provenance"}, default=float, ensure_ascii=False))


def _sub(pub15, pub18, atlas, n):
    return aa.subset_rows(pub15, n), aa.subset_rows(pub18, n), {s: aa.subset_rows(atlas[s], n) for s in aa.STAGES}


def run_gates(pub15, pub18, atlas, github=None, n: int = aa.N_HOMOLOGOUS) -> dict:
    g_o = aa.gate_order(atlas, github, n)
    p15, p18, at = _sub(pub15, pub18, atlas, n)
    s = aa.shape_space(p15, p18)
    k = aa.N_PROJ_CHECK
    g_p = aa.gate_projection(p15[:k], s["t15"][:k], s["mean"])
    g_t = aa.gate_tangent(at, s["mean"], limit=s["rho_max"])
    d_len = float(np.linalg.norm(s["t18"].mean(axis=0) - s["t15"].mean(axis=0)))
    return {"gates": {"G0-o": g_o, "G0-p22": g_p, "G0-t22": g_t}, "n_landmarks": n, "d_length_22": d_len,
            "rho_max": s["rho_max"], "gpa_converged": s["converged"],
            "passed": bool(g_o["passed"] and g_p["passed"] and g_t["passed"])}


def _analysis_n(pub15, pub18, atlas, n: int, n_boot: int = aa.N_BOOT) -> dict:
    p15, p18, at = _sub(pub15, pub18, atlas, n)
    s = aa.shape_space(p15, p18)
    a15, a18 = (aa.project_to_tangent(at[st], s["mean"]) for st in aa.STAGES)
    main = aa.anchor_decomposition(s["t15"], s["t18"], a15, a18, n_boot=n_boot, seed=aa.SEED_MTC)
    dec = aa.decompose(s["t15"], s["t18"], a15, a18)
    contrib = aa.landmark_contributions(dec["a"], dec["d"], s["t15"], s["t18"])
    return {"n_landmarks": n, **main, "contributions": contrib}


def run_analysis(pub15, pub18, atlas) -> dict:
    main = _analysis_n(pub15, pub18, atlas, aa.N_HOMOLOGOUS)
    p15, p18, at = _sub(pub15, pub18, atlas, aa.N_HOMOLOGOUS)
    s25 = _analysis_n(pub15, pub18, atlas, aa.N_SPARSE_STAGE)
    sens = {"rows_1_25": {"r": s25["mtb1"]["r"], "ci": s25["mtb1"]["ci"], "verdict": s25["mtb1"]["verdict"],
                          "top_share": s25["contributions"]["top_share"],
                          "top_landmarks": s25["contributions"]["top_landmarks"]},
            "in_gpa": aa.sensitivity_in_gpa(p15, p18, at),
            "regpa": aa.sensitivity_regpa(p15, p18, at, seed=aa.SEED_MTC)}
    return {"analysis": "MT-C", **main, "sensitivity": sens,
            "verdict": {"MT-C1": main["mtb1"]["verdict"], "MT-C2": main["contributions"]["verdict"]}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["gates", "analyze"])
    ap.add_argument("--sel-v2", default="results/morpho_trace/v2/seleccion_v2.json", help="confirmatorio de 597 (d)")
    ap.add_argument("--landmarks", default="data/external/musmorph/landmarks_confirm")
    ap.add_argument("--atlas", default="data/external/musmorph/atlas")
    ap.add_argument("--atlas-github", default="data/external/musmorph/atlas_github",
                    help="copia de los .tag de atlas del repositorio MusMorph (solo para G0-o)")
    a = ap.parse_args(argv)
    pub15, pub18, atlas = load_inputs(Path(a.sel_v2), Path(a.landmarks), Path(a.atlas))
    if a.cmd == "gates":
        gh_dir = Path(a.atlas_github)
        gh = None
        if all((gh_dir / gates.ATLAS_TAG[s]).exists() for s in aa.STAGES):
            gh = {s: np.asarray(lm.read_tag(gh_dir / gates.ATLAS_TAG[s]), float) for s in aa.STAGES}
        res = run_gates(pub15, pub18, atlas, gh)
        _write(res, OUT / "gates.json")
        return 0 if res["passed"] else 1
    p = OUT / "gates.json"
    if not p.exists() or not _read(p).get("passed"):
        raise SystemExit(f"las puertas no están superadas ({p}); el preregistro no permite seguir")
    _write(run_analysis(pub15, pub18, atlas), OUT / "analisis.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
