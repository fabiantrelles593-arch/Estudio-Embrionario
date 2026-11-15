"""P3: tablas Markdown del piloto a partir de los archivos de resultados (sin copiar números a mano).

  python scripts/p3_report.py --memos results/p3/memos --groups results/p3/grupos.csv \\
      --analysis results/p3/analisis_piloto.json --out results/p3/informe_piloto.md

Lee ``memos_run.json`` (comprobación 3.4), ``memos_vs_atlas.json`` (H-P3c y desviación D3),
``memos_rigidity.json`` (desviación D5, si existe), ``grupos.csv`` y
el JSON de ``p3_analyze.py pilot``. Las cifras del piloto son solo para tiempos y anchura de intervalos: los
veredictos del piloto **no** son resultados de P3 (docs/PREREGISTRO_P3.md §4).
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

import pandas as pd

PRECHECK_34_MIN = 0.90  # §3.4: MEMOS debe segmentar al menos el 90 % del piloto


def precheck_34(run: dict, ids: list[str]) -> dict:
    """Cuenta los especímenes del piloto con ``ok`` en ``memos_run.json``; los ausentes cuentan como fallo."""
    ok = [s for s in ids if run.get(s, {}).get("ok") is True]
    failed = [s for s in ids if s not in ok]
    n = len(ids)
    return {"n": n, "n_ok": len(ok), "failed": failed,
            "passed": n > 0 and len(ok) >= math.ceil(PRECHECK_34_MIN * n)}


def _median_dice(table: dict) -> float:
    """Mediana del Dice en las estructuras de P3 (1–48) presentes en el atlas del espécimen."""
    vals = [v["dice"] for k, v in table.items()
            if 1 <= int(k) <= 48 and v.get("vox_atlas", 0) > 0 and math.isfinite(v.get("dice", math.nan))]
    return statistics.median(vals) if vals else math.nan


NON_RIGID_SPREAD_VOX = 4  # D5: dispersión > 4 vóxeles entre tercios = «desajuste no rígido»


def compare_rows(cmp: dict, rigidity: dict | None = None) -> pd.DataFrame:
    """Una fila por espécimen: traslación (D3), Dice de la unión y mediana del Dice por estructura, sin y con traslación.

    Con ``rigidity`` (``memos_rigidity.json``) añade la dispersión entre tercios y la marca de D5; sin dato, la
    dispersión queda vacía y el espécimen no se marca.
    """
    rigidity = rigidity or {}
    rows = []
    for sid, c in sorted(cmp.items()):
        spread = rigidity.get(sid, {}).get("spread_vox")
        rows.append({"specimen": sid, "translation_vox": tuple(c["translation_vox"]),
                     "dice_union_raw": c["dice_union_raw"], "dice_union_shifted": c["dice_union_shifted"],
                     "dice_median_raw": _median_dice(c["raw"]), "dice_median_shifted": _median_dice(c["shifted"]),
                     "spread_vox": math.nan if spread is None else int(spread),
                     "non_rigid": spread is not None and spread > NON_RIGID_SPREAD_VOX})
    return pd.DataFrame(rows)


def _f(x, nd=2) -> str:
    try:
        x = float(x)
    except (TypeError, ValueError):
        return str(x)
    return "—" if not math.isfinite(x) else f"{x:.{nd}f}".replace(".", ",")


def render(pre: dict, cmp: pd.DataFrame, groups: pd.DataFrame | None, analysis: dict | None) -> str:
    out = ["# P3 — Informe del piloto (generado por `scripts/p3_report.py`)", ""]
    out += ["## Comprobación 3.4 (MEMOS segmenta ≥ 90 % del piloto)", "",
            f"- Segmentados: **{pre['n_ok']} de {pre['n']}** → {'pasa' if pre['passed'] else '**no pasa**'}.",
            f"- Sin segmentación: {', '.join(pre['failed']) if pre['failed'] else 'ninguno'}.", ""]
    if len(cmp):
        out += ["## Comparación MEMOS frente a atlas propagado (H-P3c, desviación D3)", "",
                "| Espécimen | Traslación (vóxeles) | Dice unión sin → con | Dice mediano sin → con | Dispersión D5 |",
                "|---|---|---|---|---|"]
        for r in cmp.itertuples():
            spread = "—" if not math.isfinite(r.spread_vox) else f"{int(r.spread_vox)}{' (no rígido)' if r.non_rigid else ''}"
            out.append(f"| `{r.specimen}` | {r.translation_vox} | {_f(r.dice_union_raw)} → {_f(r.dice_union_shifted)} | "
                       f"{_f(r.dice_median_raw)} → {_f(r.dice_median_shifted)} | {spread} |")
        rigid = cmp[~cmp["non_rigid"]]
        out += ["", f"Mediana entre especímenes del Dice mediano con traslación: "
                    f"**{_f(cmp['dice_median_shifted'].median())}** (n = {len(cmp)}).",
                f"Sensibilidad D5, sin los {int(cmp['non_rigid'].sum())} marcados como no rígidos: "
                f"**{_f(rigid['dice_median_shifted'].median())}** (n = {len(rigid)}); "
                f"dispersión calculada en {int(cmp['spread_vox'].notna().sum())} de {len(cmp)}.", ""]
    if groups is not None and len(groups):
        counts = groups["group"].value_counts().to_dict()
        out += ["## Grupos sobre el atlas de consenso (D4)", "",
                f"- Unidades: {len(groups)} ({', '.join(f'{k}: {v}' for k, v in sorted(counts.items()))}).", ""]
    if analysis:
        lo, hi = analysis["delta_ci"]
        rlo, rhi = analysis["rho_partial_ci"]
        out += ["## Análisis del piloto (solo tiempos y anchura de intervalos; no es resultado de P3)", "",
                f"- Especímenes: {analysis['n_specimens']}; réplicas bootstrap: {analysis['n_boot']}.",
                f"- Δ (mediana τ delgadas − compactas): {_f(analysis['delta'], 3)} (IC 95 % {_f(lo, 3)} a {_f(hi, 3)}).",
                f"- ρ parcial: {_f(analysis['rho_partial'], 3)} (IC 95 % {_f(rlo, 3)} a {_f(rhi, 3)}); ρ: {_f(analysis['rho'], 3)}.",
                f"- Semianchura del IC de Δ: {_f(analysis['delta_ci_half_width'], 3)}; proyectada a 60: "
                f"{_f(analysis['projected_half_width_60'], 3)}.",
                f"- **Tamaño del confirmatorio según la regla de D4: {analysis['n_confirm_decision']}**.",
                f"- Tiempo: medida {_f(analysis['seconds_measure'], 0)} s; evaluación {_f(analysis['seconds_evaluate'], 0)} s.", ""]
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--memos", required=True)
    ap.add_argument("--selection", default="results/p3/seleccion.json")
    ap.add_argument("--groups")
    ap.add_argument("--analysis")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    memos = Path(a.memos)
    ids = json.loads(Path(a.selection).read_text(encoding="utf-8"))["pilot"]
    run = json.loads((memos / "memos_run.json").read_text(encoding="utf-8"))
    cmp_path = memos / "memos_vs_atlas.json"
    rig_path = memos / "memos_rigidity.json"
    rigidity = json.loads(rig_path.read_text(encoding="utf-8")) if rig_path.exists() else None
    cmp = (compare_rows(json.loads(cmp_path.read_text(encoding="utf-8")), rigidity)
           if cmp_path.exists() else pd.DataFrame())
    groups = pd.read_csv(a.groups, dtype={"unit": str}) if a.groups and Path(a.groups).exists() else None
    analysis = (json.loads(Path(a.analysis).read_text(encoding="utf-8"))
                if a.analysis and Path(a.analysis).exists() else None)
    text = render(precheck_34(run, ids), cmp, groups, analysis)
    Path(a.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
