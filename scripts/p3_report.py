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


VERDICT_TEXT = {"apoyada": "apoyada", "contraria": "contraria", "no_concluyente": "no concluyente",
                "no_apoyada": "no apoyada", "no_evaluable": "no evaluable",
                "no_interpretable_D1": "no interpretable (regla de D1)"}


def _ci(pair, nd=3) -> str:
    lo, hi = pair
    return f"{_f(lo, nd)} a {_f(hi, nd)}"


def _order(o: dict | None) -> str:
    if not o:
        return "—"
    return f"ρ = {_f(o['rho'], 2)} en {o['n_structures']} estructuras → {'coinciden' if o['agree'] else '**discrepan**'} (umbral 0,7)"


def section7(verdict_a: str, verdict_b: str) -> tuple[str, str]:
    """Fila de la tabla §7 del preregistro (conclusión, siguiente paso) para los veredictos tras D1."""
    if verdict_a == "apoyada" and verdict_b == "apoyada":
        return ("La resolución y la segmentación pesan más en las estructuras finas, y el certificado lo anticipa "
                "mejor que el tamaño", "Repetir en un segundo estadio o conjunto (validación externa) antes de "
                "cualquier afirmación general")
    if verdict_a == "apoyada" and verdict_b == "no_apoyada":
        return ("El fenómeno existe, pero el certificado no añade nada al tamaño", "Reformular MORPHO-TRACE: la "
                "descomposición de varianza es la contribución; el certificado actual no lo es")
    if verdict_a in ("contraria", "no_concluyente"):
        return ("La fracción técnica no depende del tamaño o grosor como se esperaba",
                "Informar el resultado negativo; revisar los supuestos de H1 y H3 sintéticas")
    return ("Combinación no prevista en §7 (algún veredicto no evaluable o no interpretable por D1): no se extrae "
            "conclusión", "Informar tal cual; no se reinterpreta")


def render_confirm(summary: dict, agreement: pd.DataFrame | None = None) -> str:
    """Informe confirmatorio a partir de ``confirmatorio.json`` (``p3_analyze.py confirm``) y su
    ``.agreement_summary.csv``. Los veredictos son los del código preregistrado; aquí solo se transcriben."""
    p, e, v = summary["primary"], summary["exact_D1"], summary["verdicts_after_D1"]
    out = ["# P3 — Informe confirmatorio (generado por `scripts/p3_report.py`)", "",
           f"- Especímenes analizados: **{p['n_specimens']}**; ausentes: "
           f"{', '.join(summary['missing']) if summary['missing'] else 'ninguno'}.",
           f"- Unidades por grupo: {', '.join(f'{k}: {n}' for k, n in sorted(p['n_units'].items()))}; "
           f"bootstrap {p['n_boot']} réplicas, semilla {p['seed']}.", "",
           "## Veredictos preregistrados (regla `nearest`, valor log-volumen)", "",
           "| Hipótesis | Estadístico | IC 95 % | Veredicto | Con regla `exact` (D1) | Veredicto tras D1 |",
           "|---|---|---|---|---|---|",
           f"| H-P3a | Δ = {_f(p['delta'], 3)} | {_ci(p['delta_ci'])} | {VERDICT_TEXT[p['verdict_a']]} | "
           f"Δ = {_f(e['delta'], 3)} → {VERDICT_TEXT[e['verdict_a']]} | **{VERDICT_TEXT[v['verdict_a']]}** |",
           f"| H-P3b | ρ = {_f(p['rho'], 3)}; ρ parcial = {_f(p['rho_partial'], 3)} | {_ci(p['rho_partial_ci'])} (ρ parcial) | "
           f"{VERDICT_TEXT[p['verdict_b']]} | ρ = {_f(e['rho'], 3)} → {VERDICT_TEXT[e['verdict_b']]} | "
           f"**{VERDICT_TEXT[v['verdict_b']]}** |", "",
           "## Consecuencia según la tabla §7 del preregistro", "",
           "- Conclusión: {}.".format(section7(v["verdict_a"], v["verdict_b"])[0]),
           "- Siguiente paso: {}.".format(section7(v["verdict_a"], v["verdict_b"])[1]), "",
           "## Concordancia de órdenes", "",
           f"- τ con `nearest` frente a `exact` (D1): {_order(summary['order_tau_vs_exact_D1'])}.",
           f"- τ por varianzas frente a modelo mixto: {_order(summary['order_tau_vs_mixed'])}; "
           f"modelos mixtos convergidos: {summary['mixed_converged']}.", ""]
    nr = summary.get("non_rigid_D5", [])
    out += ["## H-P3c — acuerdo atlas frente a MEMOS (descriptivo, no es validación)", "",
            f"- Marcados como no rígidos (D5): {len(nr)}" + (f" ({', '.join(f'`{s}`' for s in nr)})." if nr else "."), ""]
    if agreement is not None and len(agreement):
        out += ["| Forma | Estructuras | Dice (mediana de medianas) | HD95 mm | ASSD mm | Dif. relativa de volumen |",
                "|---|---|---|---|---|---|"]
        label = {"a": "(a) sin trasladar", "b": "(b) con traslación (principal)", "b_rigid": "(b) sin no rígidos (D5)"}
        for form, g in agreement.groupby("form", sort=False):
            out.append(f"| {label.get(form, form)} | {len(g)} | {_f(g['dice'].median())} | {_f(g['hd95'].median())} | "
                       f"{_f(g['assd'].median())} | {_f(g['vol_diff_rel'].median())} |")
        out.append("")
    x4 = summary.get("exploratory_x4")
    out += ["## Exploratorios (no confirmatorios)", "",
            f"- Por sexo: {'calculado (`.sex.csv`)' if summary.get('exploratory_sex') else 'no calculado'}.",
            "- MEMOS a ×4: " + (f"{x4['n_specimens']} especímenes; orden de τ frente a ×4: {_order(x4['order_tau_vs_x4'])}."
                                 if x4 and x4.get("order_tau_vs_x4") else "no calculado."),
            f"- Tiempo: principal {_f(summary['seconds_main'], 0)} s; pasada `exact` {_f(summary['seconds_exact'], 0)} s.", ""]
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--confirm", help="confirmatorio.json: genera el informe confirmatorio en lugar del del piloto")
    ap.add_argument("--memos")
    ap.add_argument("--selection", default="results/p3/seleccion.json")
    ap.add_argument("--groups")
    ap.add_argument("--analysis")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.confirm:
        path = Path(a.confirm)
        agr_path = path.with_suffix(".agreement_summary.csv")
        text = render_confirm(json.loads(path.read_text(encoding="utf-8")),
                              pd.read_csv(agr_path) if agr_path.exists() else None)
        Path(a.out).write_text(text + "\n", encoding="utf-8")
        print(text)
        return 0
    if not a.memos:
        ap.error("--memos es obligatorio para el informe del piloto")
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
