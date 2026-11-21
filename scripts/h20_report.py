"""H20: tablas Markdown de resultados a partir de los archivos de ``run_h20.py`` (sin copiar números a mano).

  python scripts/h20_report.py --dir results/h20 --out results/h20/informe.md

Lee ``g0.json``, y si existen ``calibrate.json``, ``cal_lights.csv`` y ``test_verdicts.json``. Se detiene donde se
detuvo el estudio: sin G0 superada no hay calibración que informar; sin puerta C superada no hay prueba. Los
veredictos son los del código preregistrado; aquí solo se transcriben y se elige la fila de
``docs/h20/PREREGISTRO_H20.md`` §8 que corresponde.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

TOLERANCE = 0.10      # la de H18/H19 (|error| de volumen)
H20C_TARGET = 0.75    # §7: ≥ 75 % de los casos de prueba a ≤ 10 %
LIGHTS = ("verde", "amarillo", "rojo")

SECTION8 = {
    "g0": ("Las señales no se pueden calcular como se diseñaron en este equipo",
           "Documentar la causa; nuevo preregistro si hay arreglo"),
    "c": ("Ni la imagen (H19) ni la estabilidad de la red anticipan los fallos en la calibración",
          "Más datos de calibración o un segundo modelo independiente; la prueba sigue intacta"),
    "apoyada": ("En este conjunto, una luz verde dada solo por la estabilidad de la red acertó en embriones nuevos",
                "Replicar con otro conjunto o equipo; estudiar los amarillos"),
    "no apoyada": ("La red es estable también cuando se equivoca",
                   "Publicarlo; estudiar los verdes que fallan (errores consistentes)"),
    "otro": ("Pocas verdes o pocos embriones",
             "Más datos, mismo protocolo; **la prueba usada no decide dos veces**"),
    # no es una fila del §8: la puerta C se superó y la prueba todavía no se ha medido
    "pendiente": ("Prueba abierta, todavía sin medir: ningún veredicto",
                  "Correr `run_h20.py test --sha` con el SHA-256 anotado en el §10"),
}


def _f(x, nd=2) -> str:
    try:
        x = float(x)
    except (TypeError, ValueError):
        return str(x)
    return "—" if not math.isfinite(x) else f"{x:.{nd}f}".replace(".", ",")


def _pct(x) -> str:
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "—"
    return "—" if not math.isfinite(x) else f"{100 * x:.1f} %".replace(".", ",")


def _ci(pair, pct=True) -> str:
    if not pair:
        return "—"
    fmt = _pct if pct else _f
    return f"{fmt(pair[0])} a {fmt(pair[1])}"


def section8(g0_passed: bool, c_passed: bool | None, h20b_verdict: str | None) -> tuple[str, str]:
    """Fila de §8 (conclusión, siguiente paso) según hasta dónde llegó el estudio. Sin veredicto de H20b tras superar
    la puerta C, la prueba está pendiente (no es «pocas verdes»)."""
    if not g0_passed:
        return SECTION8["g0"]
    if not c_passed:
        return SECTION8["c"]
    if h20b_verdict is None:
        return SECTION8["pendiente"]
    return SECTION8.get(h20b_verdict, SECTION8["otro"])


def light_table(lit: pd.DataFrame, column: str = "light") -> pd.DataFrame:
    """Casos y casos con |error| > 10 % por luz, en el orden verde, amarillo, rojo."""
    bad = lit["rel_error_volume"].abs() > TOLERANCE
    rows = [{"light": c, "n": int((lit[column] == c).sum()), "bad": int((bad & (lit[column] == c)).sum())}
            for c in LIGHTS]
    return pd.DataFrame(rows)


def predictions(g0: dict, cal: dict | None, test: dict | None) -> list[tuple[str, str, str]]:
    """(predicción, probabilidad escrita en §7, ¿ocurrió?). «no aplica» si el estudio no llegó a ese punto."""
    def yn(b):
        return "sí" if b else "no"
    c = cal["gate_c"]["passed"] if cal else None
    b = test["h20b"] if test else None
    evaluable = b is not None and b["verdict"] != "no evaluable"
    return [
        ("Pasa G0", "90 %", yn(g0["passed"])),
        ("Pasa la puerta C", "40 %", yn(c) if c is not None else "no aplica"),
        ("H20b evaluable, dado que se abre la prueba", "45 %", yn(evaluable) if b is not None else "no aplica"),
        ("H20b apoyada, dado que es evaluable", "60 %", yn(b["verdict"] == "apoyada") if evaluable else "no aplica"),
        ("En la prueba, ≥ 75 % de los casos a ≤ 10 % (H20c)", "60 %",
         yn(test["h20c"]["ok10"] >= H20C_TARGET) if test else "no aplica"),
    ]


def render(g0: dict, cal: dict | None = None, lit: pd.DataFrame | None = None, test: dict | None = None) -> str:
    out = ["# H20 — Tablas de resultados (generado por `scripts/h20_report.py`)", ""]
    out += ["## G0 (factibilidad, casos de ajuste que la red ya vio)", "",
            "| Caso | s_flip | s_stage | Identidad = H19 | Segundos |", "|---|---|---|---|---|"]
    for r in g0["items"]:
        out.append(f"| `{r['image']}` | {_f(r['s_flip'], 3)} | {_f(r['s_stage'], 3)} | "
                   f"{'sí' if r['identity_matches_h19'] else '**no**'} | {_f(r['seconds'], 1)} |")
    out += ["", f"- G0: **{'superada' if g0['passed'] else 'no superada'}** ({g0['n']} casos; límite 300 s por caso). "
                "Los valores de las señales no cambian ningún umbral.", ""]
    c_passed = None
    if g0["passed"] and cal is not None:
        g = cal["gate_c"]
        c_passed = bool(g["passed"])
        out += [f"## Puerta C (calibración, {cal['n_cal']} casos, guardia fuera de pliegue)", "",
                f"- Verdes: **{g['n_green']}** (mínimo 10); con |error| > 10 %: **{_pct(g['fail'])}** (máximo 10 %) → "
                f"**{'superada' if c_passed else 'no superada'}**.", ""]
        if lit is not None:
            out += [r"| Luz | Casos (con guardia) | \|error\| > 10 % | Casos (sin guardia) | \|error\| > 10 % |",
                    "|---|---|---|---|---|"]
            w, wo = light_table(lit), light_table(lit, "light_without_guard")
            for (_, a), (_, b) in zip(w.iterrows(), wo.iterrows()):
                out.append(f"| {a['light']} | {a['n']} | {a['bad']} | {b['n']} | {b['bad']} |")
            out += ["", f"- Dentro del dominio: {int(lit['in_domain'].sum())} de {len(lit)}.", ""]
        if c_passed:
            out += [f"- Congelado: SHA-256 `{cal.get('frozen_sha256', '—')}` (debe figurar en el §10 del "
                    "preregistro antes de `test`).", ""]
        else:
            out += ["- **La prueba no se abre.**", ""]
    if c_passed and test is not None:
        b, a, c, d = test["h20b"], test["h20a"], test["h20c"], test["h20d"]
        out += [f"## Prueba ({test['n_cases']} casos, {test['n_embryos']} embriones)", "",
                "| Hipótesis | Estimación | IC 95 % | Veredicto |", "|---|---|---|---|",
                f"| H20b (primaria): fallos entre verdes | {_pct(b['estimate'])} | {_ci(b['ci'])} | **{b['verdict']}** |",
                "", f"- Verdes: {b['n_green']} en {b['n_embryos_green']} embriones (evaluable con ≥ 20 en ≥ 15).",
                f"- H20a cobertura: {_pct(a['green_fraction'])} verdes; luces: "
                + ", ".join(f"{k} {a['lights'].get(k, 0)}" for k in LIGHTS) + ".",
                f"- H20c acuerdo de la red: Dice mediano {_f(c['dice_median'], 3)}; |error| mediano "
                f"{_pct(c['abs_error_median'])}; a ≤ 10 %: {_pct(c['ok10'])}; a ≤ 5 %: {_pct(c['ok5'])}.",
                f"- H20d separación: fallos entre verdes {_pct(d['fail_green'])}, entre no verdes "
                f"{_pct(d['fail_not_green'])}; diferencia {_pct(d['difference'])} (IC {_ci(d['difference_ci'])}). "
                f"Dentro del dominio {_pct(d['in_domain'])}; verdes sin guardia {d['green_without_guard']}, de las que "
                f"fallan {d['green_without_guard_bad']}.", ""]
    concl, nxt = section8(g0["passed"], c_passed, test["h20b"]["verdict"] if (c_passed and test) else None)
    out += ["## Fila del §8 que corresponde", "", f"- **Conclusión:** {concl}.", f"- **Siguiente paso:** {nxt}.", ""]
    out += ["## Predicciones del §7", "", "| Predicción | Probabilidad escrita | ¿Ocurrió? |", "|---|---|---|"]
    out += [f"| {p} | {q} | {r} |" for p, q, r in predictions(g0, cal if g0["passed"] else None,
                                                            test if c_passed else None)]
    return "\n".join(out) + "\n"


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default="results/h20")
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    d = Path(a.dir)
    g0 = _load_json(d / "g0.json")
    if g0 is None:
        raise SystemExit(f"falta {d / 'g0.json'}: G0 no se ha corrido")
    lights_csv = d / "cal_lights.csv"
    text = render(g0, _load_json(d / "calibrate.json"),
                  pd.read_csv(lights_csv) if lights_csv.exists() else None, _load_json(d / "test_verdicts.json"))
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
