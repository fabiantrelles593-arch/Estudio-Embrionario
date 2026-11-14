"""Trayectoria de referencia: dónde cae el tamaño de referencia poblacional en semanas posteriores, con la incertidumbre propagada.

Solo investigación y educación. **No predice el crecimiento ni el aspecto de ningún feto.** Con una sola medida no se
puede saber cómo crecerá ese feto en particular; lo que sí se puede mostrar es la franja de la referencia poblacional
publicada, condicionada (con dos supuestos extremos) al tamaño medido, y cuánto la ensanchan el error de medida y la
incertidumbre de la edad.

Ecuaciones (INTERGROWTH-21st; Papageorghiou et al. 2014, texto de acceso abierto, leídas el 2026-11-12; 4 265 mujeres):
``CRL media[mm] = −50.6562 + 0.815118·GA + 0.00535302·GA²`` y ``SD(CRL) = −2.21626 + 0.0984894·GA``, con GA en días,
válidas de 58 a 105 días. Fuera de ese rango este módulo **se niega a calcular**. La edad dada la CRL es la de
``geovida.dating``. La fuente no publica serie temporal por individuo: **la correlación entre el tamaño de una visita
y el de la siguiente no la conozco**; por eso se muestran dos escenarios extremos y nada intermedio.

Escenarios (supuestos, no validados; H17 pide datos seriados para ponerlos a prueba):

* ``persistence``: el feto conserva su puntuación z respecto de la referencia (tamaño futuro = media + z·SD de la edad futura).
* ``regression``: la puntuación z se pierde por completo (el tamaño futuro es una extracción nueva de la referencia).
"""
from __future__ import annotations

import math

import numpy as np

from . import dating

GA_RANGE_DAYS = (58.0, 105.0)
DEFAULT_HORIZONS_DAYS = (7, 14, 21, 28)
DEFAULT_SEED = 20261218
DEFAULT_COVERAGE = 0.90

SOURCE = ("INTERGROWTH-21st, Papageorghiou et al. 2014 (UOG): CRL media = −50.6562 + 0.815118·GA + 0.00535302·GA², "
          "SD = −2.21626 + 0.0984894·GA (GA en días, 58–105); edad dada la CRL: ver geovida.dating")
ASSUMPTIONS = (
    "Las ecuaciones son poblacionales; no describen a ningún individuo ni a ninguna población distinta de la del estudio.",
    "La persistencia de la puntuación z entre visitas no se conoce: se muestran los dos escenarios extremos, sin validar.",
    "La incertidumbre de la medida es la que el usuario declara (`crl_rel_sd`); este módulo no la mide.",
    "Cuando la edad se estima con esta misma CRL, el tamaño no puede decir si el feto es grande o pequeño para su edad.",
    "No hay predicción del aspecto, de rasgos ni de salud: el tamaño de referencia no los determina.",
)


def _check_ga(ga_days: float) -> float:
    ga = float(ga_days)
    lo, hi = GA_RANGE_DAYS
    if math.isnan(ga) or not (lo <= ga <= hi):
        raise ValueError(f"la edad {ga_days} d está fuera del rango publicado de la ecuación ({lo:g}–{hi:g} días)")
    return ga


def crl_mean_mm(ga_days: float) -> float:
    ga = _check_ga(ga_days)
    return -50.6562 + 0.815118 * ga + 0.00535302 * ga * ga


def crl_sd_mm(ga_days: float) -> float:
    ga = _check_ga(ga_days)
    return -2.21626 + 0.0984894 * ga


def _mean_sd_arrays(ga: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Las mismas ecuaciones sobre un arreglo; las muestras individuales se recortan al rango publicado."""
    g = np.clip(ga, *GA_RANGE_DAYS)
    return -50.6562 + 0.815118 * g + 0.00535302 * g * g, -2.21626 + 0.0984894 * g


def _q(x: np.ndarray, coverage: float) -> dict:
    a = (1.0 - coverage) / 2.0
    lo, med, hi = np.quantile(x, [a, 0.5, 1.0 - a])
    return {"lo": float(lo), "median": float(med), "hi": float(hi)}


def projection(crl_mm: float, *, crl_rel_sd: float = 0.0, crl_rel_bias: float = 0.0, ga_known_days: float | None = None,
               horizons_days=DEFAULT_HORIZONS_DAYS, n_draws: int = 20000, seed: int = DEFAULT_SEED,
               coverage: float = DEFAULT_COVERAGE) -> dict:
    """Franja de referencia a ``horizons_days`` días de la medida.

    ``crl_rel_sd`` y ``crl_rel_bias``: error relativo declarado de la CRL medida (CRL medida = verdadera·(1+sesgo+SD·ξ)).
    ``ga_known_days``: edad por otra vía (p. ej. fecha de la última regla confirmada); sin ella, se estima con esta CRL.
    """
    crl_mm = float(crl_mm)
    if not (crl_mm > 0) or math.isnan(crl_mm):
        raise ValueError("la longitud debe ser un número > 0 (mm)")
    if crl_rel_sd < 0 or not (0 <= coverage < 1) or n_draws < 100:
        raise ValueError("parámetros fuera de rango")
    rng = np.random.default_rng(seed)
    meas = crl_mm / (1.0 + crl_rel_bias + crl_rel_sd * rng.standard_normal(n_draws))   # CRL verdadera, una por muestra

    if ga_known_days is None:
        if not dating.in_formula_range(crl_mm):
            raise ValueError(f"la CRL {crl_mm:g} mm está fuera del rango de la fórmula de edad "
                             f"({dating.INTERGROWTH_RANGE_MM[0]:g}–{dating.INTERGROWTH_RANGE_MM[1]:g} mm); "
                             "da la edad con ga_known_days")
        centre = np.array([dating.ga_days_intergrowth(c) for c in meas])
        sd_ga = np.array([dating.sd_ga_days_intergrowth(c) for c in meas])
        ga_true = centre + sd_ga * rng.standard_normal(n_draws)
        source = "estimada con esta misma CRL"
    else:
        ga_true = np.full(n_draws, _check_ga(ga_known_days))
        source = "dada por otra vía"
    mean0, sd0 = _mean_sd_arrays(ga_true)
    z0 = (meas - mean0) / sd0
    eps = rng.standard_normal(n_draws)                    # componente nueva si se pierde la puntuación z

    ga_med = float(np.median(ga_true))
    ga_now = {"source": source, "median_days": ga_med, "weeks_days": list(dating.weeks_days(ga_med)),
              **{k + "_days": v for k, v in _q(ga_true, coverage).items() if k != "median"}}
    rows = []
    lo_ga, hi_ga = GA_RANGE_DAYS
    for h in horizons_days:
        h = float(h)
        ga_central = ga_med + h
        in_range = lo_ga <= ga_central <= hi_ga
        row = {"days_ahead": int(h) if h == int(h) else h, "ga_days": ga_central,
               "ga_weeks_days": list(dating.weeks_days(ga_central)), "in_source_range": bool(in_range),
               "population_mean_mm": None, "population_sd_mm": None, "persistence": None, "regression": None, "envelope": None}
        if in_range:
            m, s = _mean_sd_arrays(ga_true + h)
            pers = _q(m + z0 * s, coverage)
            regr = _q(m + eps * s, coverage)
            row.update({"population_mean_mm": float(crl_mean_mm(ga_central)), "population_sd_mm": float(crl_sd_mm(ga_central)),
                        "persistence": pers, "regression": regr,
                        "envelope": {"lo": min(pers["lo"], regr["lo"]), "hi": max(pers["hi"], regr["hi"])}})
        rows.append(row)
    return {"crl_mm_measured": crl_mm, "crl_rel_sd": float(crl_rel_sd), "crl_rel_bias": float(crl_rel_bias),
            "coverage": float(coverage), "n_draws": int(n_draws), "seed": int(seed), "ga_now": ga_now, "rows": rows,
            "source": SOURCE, "assumptions": list(ASSUMPTIONS)}


def report_markdown(p: dict) -> str:
    ga = p["ga_now"]
    w, d = ga["weeks_days"]
    cov = int(round(100 * p["coverage"]))
    L = ["# Trayectoria de referencia — informe (solo investigación y educación)", "",
         "> Esto **no predice** el crecimiento ni el **aspecto** de ningún feto. Muestra la franja de la referencia poblacional "
         "publicada y cuánto la ensanchan el error de medida y la incertidumbre de la edad. Sin uso clínico.", "",
         f"* CRL medida: {p['crl_mm_measured']:.1f} mm; error relativo declarado: SD {100*p['crl_rel_sd']:.1f} %, sesgo {100*p['crl_rel_bias']:.1f} %.",
         f"* Edad ahora ({ga['source']}): {ga['median_days']:.1f} d ({w}+{d}); intervalo {cov} %: {ga['lo_days']:.1f}–{ga['hi_days']:.1f} d.", "",
         f"## Tamaño de referencia en semanas posteriores (intervalo {cov} %)", "",
         "| Días después | Edad | Media poblacional (mm) | Escenario «persistencia» (mm) | Escenario «regresión» (mm) | Envolvente (mm) |",
         "| --- | --- | --- | --- | --- | --- |"]
    for r in p["rows"]:
        w2, d2 = r["ga_weeks_days"]
        if not r["in_source_range"]:
            L.append(f"| {r['days_ahead']} | {w2}+{d2} | fuera del rango de la fuente (58–105 d): no se calcula | — | — | — |")
            continue
        f = lambda q: f"{q['lo']:.1f}–{q['hi']:.1f}"
        L.append(f"| {r['days_ahead']} | {w2}+{d2} | {r['population_mean_mm']:.1f} | {f(r['persistence'])} | {f(r['regression'])} | "
                 f"{r['envelope']['lo']:.1f}–{r['envelope']['hi']:.1f} |")
    L += ["", "## Cómo leerlo", "",
          "* **Persistencia**: el feto conserva su puntuación z respecto de la referencia. **Regresión**: la pierde por completo. "
          "La realidad no es ninguno de los dos extremos y la correlación entre visitas **no se conoce** (sin validar; H17 pide datos seriados).",
          "* Si la edad se estimó con esta misma CRL, el tamaño no dice si el feto es grande o pequeño para su edad: por construcción cae en la mediana.",
          "* El tamaño de referencia no determina rasgos, aspecto ni salud.", "", "## Fuente y supuestos", "", f"* {p['source']}"]
    L += [f"* {a}" for a in p["assumptions"]]
    return "\n".join(L) + "\n"
