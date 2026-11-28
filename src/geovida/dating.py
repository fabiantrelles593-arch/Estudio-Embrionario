"""Datación por longitud cráneo-rabadilla (CRL) con presupuesto de incertidumbre de medida.

Solo investigación y educación; no es una herramienta clínica. Combina dos fuentes de incertidumbre:
la dispersión **biológica** de la fórmula publicada y el error de **medida** de la longitud, que
viene del presupuesto de incertidumbre del proyecto (ver ``geovida.biometry``).

Fórmulas (verificadas en fuentes abiertas el 2026-11-11):
* INTERGROWTH-21st (Papageorghiou et al. 2014; ecuaciones en el texto de acceso abierto):
  ``GA[días] = 40.9041 + 3.21585·√CRL + 0.348956·CRL`` y ``SD(GA) = 2.39102 + 0.0193474·CRL``,
  CRL de 15 a 95 mm, 4265 mujeres. La fuente da percentiles como media ± Z·SD.
* Robinson (1973/1975), tal como la cita arXiv 1110.6631: ``GA[días] = 8.052·√CRL + 23.73``
  (esa fuente no da desviación).
"""
from __future__ import annotations

import math

INTERGROWTH_RANGE_MM = (15.0, 95.0)
GREEN, RED = 0.90, 0.50
DEFAULT_TOLERANCE_DAYS = 1.0


def _check(crl_mm: float) -> float:
    crl_mm = float(crl_mm)
    if not (crl_mm > 0) or math.isnan(crl_mm):
        raise ValueError("la longitud cráneo-rabadilla debe ser un número > 0 (mm)")
    return crl_mm


def in_formula_range(crl_mm: float) -> bool:
    lo, hi = INTERGROWTH_RANGE_MM
    return lo <= crl_mm <= hi


def ga_days_intergrowth(crl_mm: float) -> float:
    c = _check(crl_mm)
    return 40.9041 + 3.21585 * math.sqrt(c) + 0.348956 * c


def sd_ga_days_intergrowth(crl_mm: float) -> float:
    c = _check(crl_mm)
    return 2.39102 + 0.0193474 * c


def ga_days_robinson(crl_mm: float) -> float:
    return 8.052 * math.sqrt(_check(crl_mm)) + 23.73


def dga_dcrl(crl_mm: float) -> float:
    """Derivada de la edad (días) respecto de la longitud (mm) en la fórmula de INTERGROWTH-21st."""
    c = _check(crl_mm)
    return 3.21585 / (2.0 * math.sqrt(c)) + 0.348956


def weeks_days(days: float) -> tuple[int, int]:
    total = int(round(days))
    return total // 7, total % 7


def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def prob_within(bias: float, sd: float, tol: float) -> float:
    """P(|e| ≤ tol) para e ~ N(bias, sd²)."""
    if sd <= 0:
        return 1.0 if abs(bias) <= tol else 0.0
    return _phi((tol - bias) / sd) - _phi((-tol - bias) / sd)


def _light(p: float) -> str:
    return "verde" if p >= GREEN else ("rojo" if p < RED else "amarillo")


def certify_dating(crl_mm: float, bias_mm: float, sd_mm: float,
                   tolerance_days: float = DEFAULT_TOLERANCE_DAYS) -> dict:
    """Certificado de datación.

    ``bias_mm`` y ``sd_mm`` son el sesgo y la desviación del error de medida de la longitud (del
    presupuesto de incertidumbre). ``p_within_tolerance`` es la probabilidad de que el error de edad
    **causado por la medida** no pase de ``tolerance_days``. Fuera del rango de la fórmula (15–95 mm)
    nunca hay luz verde.
    """
    ga = ga_days_intergrowth(crl_mm)
    slope = dga_dcrl(crl_mm)
    sd_form = sd_ga_days_intergrowth(crl_mm)
    b_days = slope * bias_mm
    s_days = abs(slope) * sd_mm
    p = prob_within(b_days, s_days, tolerance_days)
    in_range = in_formula_range(crl_mm)
    light = _light(p)
    if not in_range and light == "verde":
        light = "amarillo"
    share = s_days**2 / (s_days**2 + sd_form**2)
    return {
        "crl_mm": float(crl_mm), "ga_days": ga, "ga_weeks_days": weeks_days(ga),
        "sd_formula_days": sd_form, "sd_measurement_days": s_days, "bias_measurement_days": b_days,
        "sd_total_days": math.sqrt(sd_form**2 + s_days**2), "measurement_share": share,
        "tolerance_days": tolerance_days, "p_within_tolerance": p, "in_range": in_range, "light": light,
    }


def certify_side(measured: float, bias: float, sd: float, threshold: float) -> dict:
    """Certificado de decisión: ¿está el valor verdadero del mismo lado del umbral que el medido?

    El valor verdadero se modela como N(medido − bias, sd²) (a priori plano). ``bias`` es el sesgo del
    método (medido − verdadero). Verde si la probabilidad de que el lado medido sea el verdadero es ≥ 0.90.
    Rojo si es ≤ 0.50: con 0.50 el lado medido no es más fiable que una moneda al aire, así que aquí el
    empate cuenta como rojo (en la datación, ``p < 0.50``, el empate no existe como caso práctico).
    """
    mean = measured - bias
    side = "arriba" if measured >= threshold else "debajo"
    if sd <= 0:
        above = mean >= threshold
        p = 1.0 if above == (side == "arriba") else 0.0
    else:
        p_above = 1.0 - _phi((threshold - mean) / sd)
        p = p_above if side == "arriba" else 1.0 - p_above
    light = "verde" if p >= GREEN else ("rojo" if p <= RED else "amarillo")
    return {"measured": float(measured), "threshold": float(threshold), "side": side,
            "posterior_mean": mean, "posterior_sd": float(sd), "p_same_side": p, "light": light}
