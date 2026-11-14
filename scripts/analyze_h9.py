"""Análisis confirmatorio de H9/H10 según docs/PREREGISTRO_H9_H10.md (no cambia criterios).

Usa ``results/summary/h9_frozen.json`` y no reajusta nada.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from geovida import h9
from geovida.budget import GREEN, RED

RAW = Path("results/raw")
OUT = Path("results/summary")
FIG = Path("docs/figures")
LIGHT = {"verde": "#009E73", "amarillo": "#F0E442", "rojo": "#D55E00"}
SHIFT_ORDER = ("mild_noise", "noisy", "mild_blur", "blurry")
SHIFT_LABEL = {"mild_noise": "ruido ×1.3", "noisy": "ruido ×2", "mild_blur": "desenfoque ×1.5",
               "blurry": "desenfoque ×2"}


def load(name):
    return h9.add_features(pd.read_csv(RAW / f"h9_{name}.csv.gz"))


def main():
    frozen = json.loads((OUT / "h9_frozen.json").read_text())
    test, unseen, shift = load("test"), load("unseen"), load("shift")

    res_in = h9.evaluate_in_domain(test, frozen)
    res_un = h9.evaluate_unseen(unseen, frozen)
    res_sh = h9.evaluate_shift(shift, frozen)
    silent = h9.silent_failures(test, frozen)
    silent_shape = []
    pt = h9.p_topology(test.reset_index(drop=True), frozen)
    t = test.reset_index(drop=True).assign(p=pt)
    for shape, g in t[t["t_ok"] == 0].groupby("shape"):
        silent_shape.append({"shape": shape, "n_failures": int(len(g)),
                             "green": float((g["p"] >= GREEN).mean()),
                             "red": float((g["p"] < RED).mean())})
    silent_shape = pd.DataFrame(silent_shape)

    pd.DataFrame(res_in["strata"]).round(4).to_csv(OUT / "h9_strata_test.csv", index=False)
    pd.DataFrame(res_un["strata"]).round(4).to_csv(OUT / "h9_strata_unseen.csv", index=False)
    pd.DataFrame(res_un["by_shape"]).round(4).to_csv(OUT / "h9_unseen_by_shape_exploratory.csv",
                                                      index=False)
    sh = pd.DataFrame(res_sh["strata"])
    sh.round(4).to_csv(OUT / "h9_strata_shift.csv", index=False)
    silent.round(4).to_csv(OUT / "h9_silent_by_level_exploratory.csv", index=False)
    silent_shape.round(4).to_csv(OUT / "h9_silent_by_shape_exploratory.csv", index=False)
    verdicts = {"selected": frozen["selected"], "features": frozen["features"],
                **{k: v for k, v in res_in.items() if k != "strata"},
                "h9f": res_un["h9f"],
                **{k: v for k, v in res_sh.items() if k not in ("strata", "declared")},
                "silent_failure_overall": {
                    "n_failures": int(silent["n_failures"].sum()),
                    "green": float(np.average(silent["green"], weights=silent["n_failures"])),
                    "red": float(np.average(silent["red"], weights=silent["n_failures"]))}}
    (OUT / "h9_verdicts.json").write_text(json.dumps(verdicts, indent=2, default=float))

    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    strata = [r["stratum"] for r in res_in["strata"]]
    x = np.arange(len(strata))

    # Figura 1: verde falso en dominio, formas nuevas (modelo congelado frente a línea de base)
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    for ax, rows, title in ((axs[0], res_in["strata"], "mismas formas, semillas nuevas"),
                            (axs[1], res_un["strata"], "formas nunca vistas (mancuerna y copa)")):
        d = pd.DataFrame(rows).set_index("stratum").reindex(strata)
        ax.bar(x - 0.2, 100 * d["false_green_baseline"], 0.4, color="#999999",
               label="profundidad global (línea de base)")
        ax.bar(x + 0.2, 100 * d["false_green"], 0.4, color="#0072B2",
               label=f"semáforo topológico ({frozen['selected']})")
        ax.axhline(10, color="0.3", ls="--", lw=1)
        ax.set_xticks(x)
        ax.set_xticklabels([s.replace("|", "\n") for s in strata], fontsize=7)
        ax.set_title(title)
    axs[0].set_ylabel("luz verde falsa en topología (%)")
    handles, labels = axs[0].get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=8, frameon=False, ncol=2, loc="lower center",
               bbox_to_anchor=(0.5, -0.08))
    fig.suptitle("H9: ¿cuántas luces verdes de topología eran falsas? (línea: 10 %)", y=1.0)
    fig.tight_layout()
    fig.savefig(FIG / "h9_false_green.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Figura 2: dominio desplazado, volumen y topología, sin y con guardia
    fig, axs = plt.subplots(2, 3, figsize=(11.5, 6.2), sharey=True, sharex=True)
    xs = np.arange(len(SHIFT_ORDER))
    for j, seg in enumerate(("global", "otsu", "smoothed_otsu")):
        for i, (cols, title) in enumerate((
                (("false_green_volume", "false_green_volume_guard", "n_green_volume_guard"),
                 "volumen (semáforo de H6)"),
                (("false_green_topology", "false_green_topology_guard", "n_green_topology_guard"),
                 "topología (semáforo de H9)"))):
            ax = axs[i, j]
            d = sh[sh["stratum"].str.startswith(seg + "|")].copy()
            d["profile"] = d["stratum"].str.split("|").str[1]
            d = d.set_index("profile").reindex(SHIFT_ORDER)
            ax.bar(xs - 0.2, 100 * d[cols[0]].fillna(0), 0.4, color="#D55E00", label="sin guardia")
            ax.bar(xs + 0.2, 100 * d[cols[1]].fillna(0), 0.4, color="#0072B2", label="con guardia")
            tops = 100 * d[[cols[0], cols[1]]].fillna(0).max(axis=1)
            for k, n in enumerate(d[cols[2]].fillna(0).astype(int)):
                ax.text(xs[k], tops.iloc[k] + 2, f"n={n}", ha="center", va="bottom", fontsize=6.5,
                        color="0.2")
            ax.axhline(10, color="0.3", ls="--", lw=1)
            ax.set_title(f"{seg} · {title}", fontsize=8)
            ax.set_xticks(xs)
            ax.set_xticklabels([SHIFT_LABEL[p] for p in SHIFT_ORDER], fontsize=7, rotation=15)
    for ax in axs[:, 0]:
        ax.set_ylabel("luz verde falsa (%)")
    handles, labels = axs[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=8, frameon=False, ncol=2, loc="lower center",
               bbox_to_anchor=(0.5, -0.04))
    fig.suptitle("H9g/H10: imágenes con más ruido o más desenfoque que la calibración, declaradas "
                 "«realistic» (n = verdes que deja la guardia)", y=1.0)
    fig.tight_layout()
    fig.savefig(FIG / "h10_domain_shift.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Figura 3: fallo silencioso por resolución
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    bottom = np.zeros(len(silent))
    xl = np.arange(len(silent))
    for key, light in (("red", "rojo"), ("yellow", "amarillo"), ("green", "verde")):
        ax.bar(xl, 100 * silent[key], bottom=bottom, color=LIGHT[light], label=light,
               edgecolor="white", lw=.4)
        bottom += 100 * silent[key].to_numpy()
    ax.set_xticks(xl)
    ax.set_xticklabels([f"{v:g}\n(n={n})" for v, n in zip(silent["t_over_h"], silent["n_failures"])],
                       fontsize=8)
    ax.set_xlabel("t / h (vóxeles a través del rasgo más fino) y número de fallos")
    ax.set_ylabel("luz que recibieron (%)")
    ax.legend(fontsize=8, frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    ax.set_title("H9 (descriptivo): qué luz recibieron las topologías INCORRECTAS", y=1.12)
    fig.tight_layout()
    fig.savefig(FIG / "h9_silent_failures.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(json.dumps(verdicts, indent=2, default=float))
    cols = ["stratum", "p_ok", "auc", "auc_baseline", "ece", "logloss", "logloss_baseline",
            "logloss_no_scale", "n_green", "false_green", "fg_hi", "coverage",
            "false_green_baseline", "coverage_baseline", "retained_topology", "retained_volume"]
    print(pd.DataFrame(res_in["strata"])[cols].round(3).to_string(index=False))
    print(pd.DataFrame(res_un["strata"]).round(3).to_string(index=False))
    print(pd.DataFrame(res_un["by_shape"]).round(3).to_string(index=False))
    print(sh.round(3).to_string(index=False))
    print(silent.round(3).to_string(index=False))
    print(silent_shape.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
