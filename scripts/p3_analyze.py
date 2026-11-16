"""P3 (docs/PREREGISTRO_P3.md §5): grupos sobre el atlas de consenso y análisis del piloto.

  python scripts/p3_analyze.py groups --atlas data/external/musmorph/atlas/IMPC_E15.5_Body_Atlas_Segs.mnc \\
      --out results/p3/grupos.csv
  python scripts/p3_analyze.py pilot --data data/external/musmorph/impc_e15_5 --memos results/p3/memos \\
      --groups results/p3/grupos.csv --out results/p3/analisis_piloto.json

``groups`` fija los grupos «pequeño o delgado» y «grande o compacto» (§5.6) con la profundidad media
interior relativa al vóxel sobre el atlas de consenso, sin mirar especímenes. ``pilot`` construye las 6
condiciones (resolución ×1, ×2, ×4 por segmentador A = atlas propagado y B = MEMOS) de los especímenes del
piloto que tengan las dos segmentaciones, y calcula τ, H-P3a y H-P3b **solo para tiempos y anchura de
intervalos** (el piloto no entra en el confirmatorio). Aplica la regla de ampliación de §4 con la proyección
fijada en la desviación D4: semianchura a 60 = semianchura del piloto × √(n_piloto / 60).

``confirm`` es el análisis confirmatorio de §5–§6: H-P3a y H-P3b con la regla ``nearest`` (principal), la
sensibilidad ``exact`` de D1 con su regla de interpretación, τ de área y b0, el modelo mixto de §5.4, el acuerdo
entre segmentadores de §5.8 (forma a, forma b de D3 y sensibilidad de D5) y los τ exploratorios.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from geovida import p3, p3_data  # noqa: E402

EXPANSION_HALF_WIDTH = 0.10
N_CONFIRM, N_CONFIRM_EXPANDED = 60, 120


def projected_half_width(lo: float, hi: float, n_pilot: int, n_target: int = N_CONFIRM) -> float:
    """Semianchura del IC proyectada a ``n_target`` especímenes, escalando por √(n_piloto / n_target)."""
    if not (math.isfinite(lo) and math.isfinite(hi)) or n_pilot < 2:
        return math.nan
    return (hi - lo) / 2 * math.sqrt(n_pilot / n_target)


def expansion_decision(lo: float, hi: float, n_pilot: int) -> int:
    """60, o 120 si la semianchura proyectada a 60 supera 0,10 (o no se puede proyectar)."""
    hw = projected_half_width(lo, hi, n_pilot)
    return N_CONFIRM_EXPANDED if not math.isfinite(hw) or hw > EXPANSION_HALF_WIDTH else N_CONFIRM


def _specimen_maps(sid: str, data: Path, memos: Path, rule: str = "nearest", pad: int = 0,
                   memos_as_b: Path | None = None):
    """Mapas del atlas (recuperación ``rule``, D1) y de MEMOS en una misma caja nativa (más ``pad``), con el vóxel.

    Con ``memos_as_b``, B se toma de esa carpeta (p. ej. MEMOS sobre la imagen a ×4, exploratorio de D2).
    """
    atlas, abox, spacing, _, _ = p3_data.load_labels(data / f"{sid}_Segs.mnc", p3_data.MUSMORPH_LABELS, rule)
    z = np.load((memos_as_b or memos) / f"{sid}_memos.npz")
    lab, box = z["labels"], z["box"]
    ab = np.array([[s.start, s.stop] for s in abox])
    lo = np.minimum(box[:, 0], ab[:, 0]) - pad
    hi = np.maximum(box[:, 1], ab[:, 1]) + pad
    shape = tuple(int(v) for v in hi - lo)
    a = np.zeros(shape, np.int16)
    a[tuple(slice(ab[i][0] - lo[i], ab[i][1] - lo[i]) for i in range(3))] = atlas
    m = np.zeros(shape, np.uint8)
    m[tuple(slice(box[i][0] - lo[i], box[i][1] - lo[i]) for i in range(3))] = lab
    return {"A": a, "B": m}, spacing


AGREEMENT_PAD = 60  # margen del lienzo para trasladar el atlas sin reciclar bordes (D3)
SECONDARY_VALUES = ("area_sdf", "b0")


def summarize_agreement(rows: pd.DataFrame, non_rigid=()) -> pd.DataFrame:
    """Medianas por estructura de Dice, HD95, ASSD y diferencia relativa de volumen (§5.8).

    ``form`` a = sin trasladar; b = con la traslación de D3 (principal); b_rigid = b sin los especímenes marcados
    como no rígidos (sensibilidad de D5).
    """
    metrics = ["dice", "hd95", "assd", "vol_diff_rel"]
    non_rigid = set(map(str, non_rigid))
    parts = []
    for form, sub in (("a", rows[rows["form"] == "a"]), ("b", rows[rows["form"] == "b"]),
                      ("b_rigid", rows[(rows["form"] == "b") & ~rows["specimen"].astype(str).isin(non_rigid)])):
        if sub.empty:
            continue
        g = sub.groupby("structure")[metrics].median().reset_index()
        g["n_specimens"] = sub.groupby("structure")["specimen"].nunique().to_numpy()
        g.insert(0, "form", form)
        parts.append(g)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def exploratory_taus(df: pd.DataFrame, value: str = "log_volume") -> pd.DataFrame:
    """Exploratorio (§6): τ solo con el factor resolución (cada segmentador) y solo con el factor segmentador (×1)."""
    out = []
    for seg in sorted(df["segmenter"].unique()):
        t = p3.technical_fraction(df[df["segmenter"] == seg], value)
        out.append(t.assign(variant=f"resolution_only_{seg}"))
    t = p3.technical_fraction(df[df["factor"] == 1], value)
    out.append(t.assign(variant="segmenter_only_k1"))
    return pd.concat(out, ignore_index=True)


def sex_taus(df: pd.DataFrame, sex_of: dict, value: str = "log_volume") -> pd.DataFrame:
    """Exploratorio (§6): τ por separado en hembras y en machos (``sex_of``: espécimen → "F"/"M")."""
    out = []
    spec = df["specimen"].astype(str)
    for sex in ("F", "M"):
        sub = df[spec.map(sex_of).eq(sex)]
        if sub["specimen"].nunique() >= 2:
            out.append(p3.technical_fraction(sub, value).assign(variant=f"sex_{sex}"))
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def d1_verdicts(main: dict, exact: dict, order: dict) -> dict:
    """Regla de D1: si los órdenes por τ discrepan (ρ < 0,7), un veredicto solo se interpreta si coincide con ``exact``."""
    out = {}
    for key in ("verdict_a", "verdict_b"):
        same = main[key] == exact[key]
        out[key] = main[key] if order["agree"] or same else "no_interpretable_D1"
    return out


def cmd_confirm(a) -> int:
    sel = json.loads(Path(a.ids).read_text(encoding="utf-8"))
    memos, data = Path(a.memos), Path(a.data)
    ids = [s for s in sel[a.which] if (memos / f"{s}_memos.npz").exists() and (data / f"{s}_Segs.mnc").exists()]
    missing = [s for s in sel[a.which] if s not in ids]
    cmp = json.loads((memos / "memos_vs_atlas.json").read_text(encoding="utf-8"))
    rig_path = memos / "memos_rigidity.json"
    rig = json.loads(rig_path.read_text(encoding="utf-8")) if rig_path.exists() else {}
    non_rigid = sorted(s for s, r in rig.items() if s in ids and r["spread_vox"] > a.non_rigid_spread)
    groups = pd.read_csv(a.groups, dtype={"unit": str})
    units = p3_data.p3_units()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    agr: list[dict] = []
    t0 = time.time()

    def items(rule: str, with_agreement: bool):
        for sid in ids:
            maps, spacing = _specimen_maps(sid, data, memos, rule, pad=AGREEMENT_PAD)
            if with_agreement:
                for form, t in (("a", (0, 0, 0)), ("b", cmp[sid]["translation_vox"])):
                    agr.extend(dict(r, form=form) for r in
                               p3.agreement_rows(sid, maps["A"], maps["B"], spacing, p3_data.P3_STRUCTURES, t))
            print(f"  {rule} {sid}", flush=True)
            # la regla de D1 solo cambia A: en la pasada «exact», B se reutiliza de la tabla principal
            yield sid, (maps if with_agreement else {"A": maps["A"]}), spacing

    df = p3.condition_table(items("nearest", True), p3_data.P3_STRUCTURES, cert_segmenter="A")
    df.to_csv(out.with_suffix(".conditions.csv"), index=False)
    agr_df = pd.DataFrame(agr)
    agr_df.to_csv(out.with_suffix(".agreement.csv"), index=False)
    summarize_agreement(agr_df, non_rigid).to_csv(out.with_suffix(".agreement_summary.csv"), index=False)
    t_main = time.time() - t0

    res = p3.evaluate(df, groups, units, n_boot=a.n_boot)
    res["units"].to_csv(out.with_suffix(".units.csv"), index=False)
    taus = {v: p3.technical_fraction(df, v) for v in ("log_volume",) + SECONDARY_VALUES}
    pd.concat([t.assign(value=v) for v, t in taus.items()]).to_csv(out.with_suffix(".tau.csv"), index=False)
    mixed = p3.mixed_technical_fraction(df)
    mixed.to_csv(out.with_suffix(".mixed.csv"), index=False)
    order_mixed = p3.order_agreement(taus["log_volume"], mixed, "tau", "tau_mixed")
    exploratory_taus(df).to_csv(out.with_suffix(".exploratory.csv"), index=False)
    if a.metadata:
        meta = pd.read_csv(a.metadata)
        sex_of = dict(zip(meta["Biosample"].astype(str), meta["Sex"].astype(str)))
        sex_taus(df, sex_of).to_csv(out.with_suffix(".sex.csv"), index=False)
    x4 = None
    if a.memos_x4:
        mx4 = Path(a.memos_x4)
        ids4 = [s for s in ids if (mx4 / f"{s}_memos.npz").exists()]

        def items_x4():  # solo B cambia: A se reutiliza de la tabla principal
            for sid in ids4:
                maps, spacing = _specimen_maps(sid, data, memos, "nearest", memos_as_b=mx4)
                print(f"  x4 {sid}", flush=True)
                yield sid, {"B": maps["B"]}, spacing

        b4 = p3.condition_table(items_x4(), p3_data.P3_STRUCTURES, cert_segmenter="A")
        df4 = pd.concat([df[(df["segmenter"] == "A") & df["specimen"].isin(ids4)], b4], ignore_index=True)
        df4.to_csv(out.with_suffix(".conditions_x4.csv"), index=False)
        tau4 = p3.technical_fraction(df4)
        tau4.to_csv(out.with_suffix(".tau_x4.csv"), index=False)
        x4 = {"n_specimens": len(ids4), "order_tau_vs_x4": p3.order_agreement(taus["log_volume"], tau4)}

    t1 = time.time()
    a_exact = p3.condition_table(items("exact", False), p3_data.P3_STRUCTURES, cert_segmenter="A")
    df_exact = pd.concat([a_exact, df[df["segmenter"] == "B"]], ignore_index=True)
    df_exact.to_csv(out.with_suffix(".conditions_exact.csv"), index=False)
    res_exact = p3.evaluate(df_exact, groups, units, n_boot=a.n_boot)
    order_d1 = p3.order_agreement(taus["log_volume"], p3.technical_fraction(df_exact))
    t_exact = time.time() - t1

    def strip(r):
        return {k: v for k, v in r.items() if k != "units"}

    summary = {"which": a.which, "specimens": ids, "missing": missing, "non_rigid_D5": non_rigid,
               "primary": strip(res), "exact_D1": strip(res_exact), "order_tau_vs_exact_D1": order_d1,
               "verdicts_after_D1": d1_verdicts(res, res_exact, order_d1),
               "order_tau_vs_mixed": order_mixed, "mixed_converged": int(mixed["converged"].sum()),
               "exploratory_sex": bool(a.metadata), "exploratory_x4": x4,
               "seconds_main": round(t_main, 1), "seconds_exact": round(t_exact, 1)}
    out.write_text(json.dumps(summary, indent=1, ensure_ascii=False, default=float), encoding="utf-8")
    print(json.dumps(summary, indent=1, ensure_ascii=False, default=float))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("groups")
    g.add_argument("--atlas", required=True)
    g.add_argument("--out", required=True)
    p = sub.add_parser("pilot")
    p.add_argument("--data", required=True)
    p.add_argument("--memos", required=True)
    p.add_argument("--groups", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--n-boot", type=int, default=p3.N_BOOT)
    c = sub.add_parser("confirm")
    c.add_argument("--data", required=True)
    c.add_argument("--memos", required=True)
    c.add_argument("--groups", required=True)
    c.add_argument("--ids", default="results/p3/seleccion.json")
    c.add_argument("--which", default="confirm")
    c.add_argument("--out", required=True)
    c.add_argument("--n-boot", type=int, default=p3.N_BOOT)
    c.add_argument("--non-rigid-spread", type=int, default=4)
    c.add_argument("--metadata", help="CSV de MusMorph, para el exploratorio por sexo")
    c.add_argument("--memos-x4", help="carpeta de MEMOS sobre la imagen a ×4 (exploratorio de D2)")
    a = ap.parse_args(argv)
    if a.cmd == "confirm":
        return cmd_confirm(a)

    if a.cmd == "groups":
        atlas, _, spacing, _, _ = p3_data.load_labels(a.atlas, p3_data.P3_STRUCTURES, "exact")
        out = p3.groups_from_atlas(atlas, spacing, p3_data.P3_STRUCTURES, p3_data.p3_units())
        out["names"] = [" + ".join(p3_data.KOMP2_NAMES[int(s)] for s in u.split("+")) for u in out["unit"]]
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        out.sort_values("d_over_hgeo").to_csv(a.out, index=False)
        print(out.groupby("group").size().to_string())
        return 0

    memos = Path(a.memos)
    ids = sorted(f.name[: -len("_memos.npz")] for f in memos.glob("*_memos.npz"))
    t0 = time.time()

    def items():
        for sid in ids:
            maps, spacing = _specimen_maps(sid, Path(a.data), memos)
            print(f"  {sid}", flush=True)
            yield sid, maps, spacing

    df = p3.condition_table(items(), p3_data.P3_STRUCTURES, cert_segmenter="A")
    t_measure = time.time() - t0
    df.to_csv(Path(a.out).with_suffix(".conditions.csv"), index=False)
    groups = pd.read_csv(a.groups, dtype={"unit": str})
    t1 = time.time()
    res = p3.evaluate(df, groups, p3_data.p3_units(), n_boot=a.n_boot)
    t_eval = time.time() - t1
    lo, hi = res["delta_ci"]
    summary = {k: v for k, v in res.items() if k != "units"}
    summary.update(specimens=ids, seconds_measure=round(t_measure, 1), seconds_evaluate=round(t_eval, 1),
                   delta_ci_half_width=(hi - lo) / 2 if math.isfinite(lo) else math.nan,
                   projected_half_width_60=projected_half_width(lo, hi, len(ids)),
                   n_confirm_decision=expansion_decision(lo, hi, len(ids)))
    res["units"].to_csv(Path(a.out).with_suffix(".units.csv"), index=False)
    Path(a.out).write_text(json.dumps(summary, indent=1, ensure_ascii=False, default=float), encoding="utf-8")
    print(json.dumps(summary, indent=1, ensure_ascii=False, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
