"""H11 y H12R: informe Markdown a partir de los veredictos de ``scripts/run_h11.py`` (sin copiar números a mano).

    python scripts/h11_report.py --dir results/summary --out results/h11/informe_h11.md

Lee ``h11_<tag>_verdicts.json`` y ``h11_<tag>_cases.csv`` para las etiquetas que existan:
``v04`` (principal de H11), ``h12`` (principal de H12R, perfil ``us_raw``), ``h12c`` (``us_compound``, no se
puede elegir después) y las sensibilidades de vóxel ``v04_rs`` y ``h12_rs`` (desviación D1 de H11).

H12Ra y H12Rc comparan dos calibraciones y no los calcula ``run_h11.py``: se calculan aquí con las reglas de
``docs/PREREGISTRO_H12R.md`` §4. La conclusión de H12R sale de su tabla §5; no se reinterpreta.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

TAGS = {"v04": "H11 · calibración v0.4 (principal)", "h12": "H12R · calibración H12, `us_raw` (principal)",
        "h12c": "H12R · calibración H12, `us_compound`", "v04_rs": "H11 · sensibilidad de vóxel",
        "h12_rs": "H12R · sensibilidad de vóxel"}
H12R_PRIMARY_SEGMENTER = "smoothed_otsu"


def _f(x, nd=2) -> str:
    if x is None:
        return "—"
    try:
        x = float(x)
    except (TypeError, ValueError):
        return str(x)
    return "—" if not math.isfinite(x) else f"{x:.{nd}f}".replace(".", ",")


def _pct(x) -> str:
    return "—" if x is None else f"{_f(100 * float(x), 1)} %"


def _ci(ci) -> str:
    return "—" if not ci else f"{_pct(ci[0])} a {_pct(ci[1])}"


def body_greens(cases: pd.DataFrame) -> int:
    """Luces verdes de volumen (con guardia) en el cuerpo, sumando segmentadores (H12Rc)."""
    body = cases[cases["structure"] == "body"]
    return int((body["light_volume"] == "verde").sum())


def h12ra(v04: dict, h12: dict, seg: str = H12R_PRIMARY_SEGMENTER) -> dict:
    """§4 H12Ra: apoyada si en ``smoothed_otsu`` la fracción dentro del dominio es mayor con H12 que con v0.4."""
    a = v04["h11a"]["in_domain_fraction"].get(seg)
    b = h12["h11a"]["in_domain_fraction"].get(seg)
    if a is None or b is None or not (math.isfinite(a) and math.isfinite(b)):
        return {"v04": a, "h12": b, "verdict": "no evaluable"}
    return {"v04": a, "h12": b, "verdict": "apoyada" if b > a else "no apoyada"}


def h12r_section5(verdict_b: str) -> tuple[str, str]:
    """Fila de la tabla §5 de PREREGISTRO_H12R.md para el veredicto de H12Rb."""
    table = {
        "no evaluable": ("El simulador de ecografía de H12 no cubre aún la ecografía real de alta frecuencia. La "
                         "guardia hizo su trabajo: se negó", "Calibrar con los propios volúmenes reales, validando "
                         "por embrión; eso es otra hipótesis, con su preregistro"),
        "apoyada": ("Con este conjunto y este protocolo, las luces verdes de `smoothed_otsu` acertaron. No se "
                    "generaliza a otro equipo, especie ni estructura", "Replicar con un segundo conjunto antes de "
                    "afirmar nada más"),
        "no apoyada": ("La luz verde falló con datos reales. Se publica tal cual",
                       "Revisar qué rasgo de la ecografía real no estaba en el simulador"),
        "no concluyente": ("Faltan embriones para decidir", "Más embriones, mismo protocolo"),
    }
    return table.get(verdict_b, ("Veredicto no previsto en §5", "Informar tal cual"))


def _verdict_rows(tag: str, v: dict) -> list[str]:
    a, b, c, e = v["h11a"], v["h11b"], v["h11c"], v["h11e"]
    fr = ", ".join(f"{k} {_pct(x)}" for k, x in a["in_domain_fraction"].items())
    return [f"### {TAGS.get(tag, tag)}", "",
            f"- Filas: {v['n_cases']}; embriones: {v['n_embryos']}.", "",
            "| Hipótesis | Datos | Estimación | IC 95 % (por embrión) | Veredicto |", "|---|---|---|---|---|",
            f"| a — dentro del dominio (cuerpo) | {fr} | {a['passed']} de 3 segmentadores ≤ 50 % | — | **{a['verdict']}** |",
            f"| b — verdes con guardia y \\|error\\| > 10 % (primaria) | {b['n_green']} verdes, "
            f"{b['n_embryos_green']} embriones | {_pct(b['estimate'])} | {_ci(b['ci'])} | **{b['verdict']}** |",
            f"| c — verdes sin guardia y \\|error\\| > 10 % | {c['n_green']} verdes, {c['n_embryos_green']} embriones | "
            f"{_pct(c['estimate'])} | {_ci(c['ci'])} | **{c['verdict']}** |",
            f"| e — topología con verde | {e['n_green']} verdes, {e['n_embryos_green']} embriones | "
            f"{_pct(e['estimate'])} | {_ci(e['ci'])} | **{e['verdict']}** |", "",
            f"- Referencias de cuerpo con Betti distinto de (1, 0, 0): {_pct(e.get('reference_not_simple'))}.", ""]


def _agreement_rows(v: dict) -> list[str]:
    out = ["| Segmentador | Estructura | n | Dice mediano (mín–máx) | \\|error\\| mediano | ≤ 10 % | ≤ 5 % |",
           "|---|---|---|---|---|---|---|"]
    for r in v["h11d"]["rows"]:
        out.append(f"| {r['segmenter']} | {r['structure']} | {r['n']} | {_f(r['dice_median'])} "
                   f"({_f(r['dice_min'])}–{_f(r['dice_max'])}) | {_pct(r['abs_error_median'])} | {_pct(r['ok10'])} | "
                   f"{_pct(r['ok5'])} |")
    return out + [""]


def render(verdicts: dict[str, dict], greens: dict[str, int]) -> str:
    out = ["# H11 y H12R — Informe (generado por `scripts/h11_report.py`)", "",
           "Solo investigación con un conjunto animal (ecografía 3D de embrión de ratón, Qiu et al. 2021, CC BY). "
           "Una referencia dibujada por una persona no es la verdad: se mide acuerdo. Nada de esto es clínico.", ""]
    out += ["## Veredictos preregistrados", ""]
    for tag in TAGS:
        if tag in verdicts:
            out += _verdict_rows(tag, verdicts[tag])
    if "v04" in verdicts and "h12" in verdicts:
        ra = h12ra(verdicts["v04"], verdicts["h12"])
        rb = verdicts["h12"]["h11b"]["verdict"]
        concl, nxt = h12r_section5(rb)
        out += ["## H12R — comparación entre calibraciones (`us_raw`)", "",
                f"- **H12Ra** (`{H12R_PRIMARY_SEGMENTER}`, cuerpo dentro del dominio): v0.4 {_pct(ra['v04'])} → "
                f"H12 {_pct(ra['h12'])} → **{ra['verdict']}**.",
                f"- **H12Rb** (primaria): **{rb}** (tabla de arriba, calibración H12 `us_raw`).",
                f"- **H12Rc** (luces verdes de cuerpo, H12 menos v0.4): {greens.get('h12', 0)} − {greens.get('v04', 0)} "
                f"= **{greens.get('h12', 0) - greens.get('v04', 0)}** (sin criterio de éxito).", "",
                "### Consecuencia según la tabla §5 de PREREGISTRO_H12R.md", "",
                f"- Conclusión: {concl}.", f"- Siguiente paso: {nxt}.", ""]
    if "v04" in verdicts:
        out += ["## H11d — acuerdo con la referencia (descriptivo, calibración v0.4)", ""] + _agreement_rows(verdicts["v04"])
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default="results/summary")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    d = Path(a.dir)
    verdicts, greens = {}, {}
    for tag in TAGS:
        vp, cp = d / f"h11_{tag}_verdicts.json", d / f"h11_{tag}_cases.csv"
        if vp.exists():
            verdicts[tag] = json.loads(vp.read_text(encoding="utf-8"))
        if cp.exists():
            greens[tag] = body_greens(pd.read_csv(cp))
    text = render(verdicts, greens)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
