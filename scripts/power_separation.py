"""Tamaño muestral para la pregunta de separación (H20d, H23d, H24d, H25d).

Simulación pura: no lee ningún dato. Para cada escenario (casos, fracción de verdes, tasa de fallo entre verdes y
entre no verdes) genera conjuntos con un caso por embrión y les aplica la regla de H25d: Δ = fallos entre no verdes −
fallos entre verdes; IC 95 % por bootstrap de percentiles (2000 réplicas, remuestreo por embrión); «separa» si el
límite inferior > 0, «no separa» si el superior ≤ 0,05, si no «no concluyente»; «no evaluable» con < 5 verdes o
< 5 no verdes.

Con un caso por embrión, remuestrear embriones es remuestrear casos, así que el bootstrap se vectoriza.
``tests/test_power_separation.py`` comprueba que el veredicto coincide con ``geovida.h24.separation``.

Uso: python scripts/power_separation.py --out results/power/separacion.csv
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

SEP_NO_MAX = 0.05
SEP_MIN_EACH = 5
N_BOOT = 2000
SEED = 20261127

SIZES = (40, 80, 120, 200, 300, 400)
GREEN_FRACTION = 0.5
# (nombre, fallo entre verdes, fallo entre no verdes)
SCENARIOS = (
    ("nulo_5_5", 0.05, 0.05),
    ("debil_5_15", 0.05, 0.15),
    ("calibracion_5_27", 0.05, 0.27),
    ("mas_fallos_10_30", 0.10, 0.30),
)


def verdict(green: np.ndarray, bad: np.ndarray, rng: np.random.Generator, n_boot: int = N_BOOT) -> str:
    """Veredicto de H25d con un caso por embrión (``green`` y ``bad`` booleanos, misma longitud)."""
    green, bad = np.asarray(green, bool), np.asarray(bad, bool)
    if green.sum() < SEP_MIN_EACH or (~green).sum() < SEP_MIN_EACH:
        return "no evaluable"
    n = len(green)
    idx = rng.integers(0, n, size=(n_boot, n))
    g, b = green[idx], bad[idx]
    ng, nn = g.sum(1), (~g).sum(1)
    ok = (ng > 0) & (nn > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        d = (b & ~g).sum(1) / nn - (b & g).sum(1) / ng
    d = d[ok]
    if d.size == 0:
        return "no evaluable"
    lo, hi = np.percentile(d, 2.5), np.percentile(d, 97.5)
    return "separa" if lo > 0 else ("no separa" if hi <= SEP_NO_MAX else "no concluyente")


def simulate(n: int, p_green_fail: float, p_other_fail: float, n_sim: int, rng: np.random.Generator,
             green_fraction: float = GREEN_FRACTION) -> dict:
    counts = {"separa": 0, "no separa": 0, "no concluyente": 0, "no evaluable": 0}
    for _ in range(n_sim):
        green = rng.random(n) < green_fraction
        bad = np.where(green, rng.random(n) < p_green_fail, rng.random(n) < p_other_fail)
        counts[verdict(green, bad, rng)] += 1
    return {k: v / n_sim for k, v in counts.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/power/separacion.csv")
    ap.add_argument("--n-sim", type=int, default=1000)
    args = ap.parse_args()
    rng = np.random.default_rng(SEED)
    rows = []
    for name, pg, pn in SCENARIOS:
        for n in SIZES:
            r = simulate(n, pg, pn, args.n_sim, rng)
            rows.append({"escenario": name, "fallo_verdes": pg, "fallo_no_verdes": pn, "casos": n,
                         **{k.replace(" ", "_"): round(v, 3) for k, v in r.items()}})
            print(rows[-1], flush=True)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
