"""H11: manifiesto del conjunto de Qiu et al. 2021 (IEEE DataPort, DOI 10.21227/drmd-xq36) a partir de la ficha.

    python scripts/h11_manifest_qiu2021.py results/summary/real_datasheet_qiu2021.json \\
        --out results/h11/manifiesto_qiu2021.csv [--relaxed-spacing]

Solo usa la ficha (formas, vóxel, etiquetas); no abre imágenes ni mide nada. Reglas (desviación del
16 nov 2026 en docs/PREREGISTRO_H11.md):

* Imagen = ``X.nii``; cuerpo = ``X_BODY_labels.nii``; ventrículo = ``X_BV_labels.nii``; valor de etiqueta 1.
  Los ``*_prebv.nii`` no se emparejan (nombre ambiguo).
* Un par se excluye si la etiqueta no tiene la misma forma y el mismo vóxel que la imagen (aclaración 5).
  Con ``--relaxed-spacing`` (solo sensibilidad declarada) se admite la etiqueta con la misma forma aunque su
  cabecera declare otro vóxel; la medida usa siempre el vóxel de la imagen.
* Embrión = fecha + estadio + número de embrión (``20171212_E11_E2``): las letras ``a``/``b``, ``R`` y los
  sufijos ``Mut``/``Ext``/``reg``/``filt`` no separan embriones. Agrupar de más solo ensancha los intervalos.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import PurePath

import pandas as pd

ETOKEN = re.compile(r"^E(\d+(?:\.5|p5|p)?)")  # E12, E12p5, E14.5, E14p, E2a, E3R-filt, E10a-Mut, E2aMut


def embryo_id(name: str) -> str:
    """Fecha + estadio + número de embrión: ``20171122_En1_E12_Ext_E11a_reg`` → ``20171122_E12_E11``.

    Los tokens que empiezan por E y un dígito son el estadio (el primero, si hay dos) y el embrión (el
    último). Sin estadio (``20161121_En1_E2a_reg-filt``) queda ``20161121_E2``. Letras (a/b/c/d/R), ``Mut``,
    ``Ex``/``Ext``, ``reg`` y ``filt`` no separan embriones.
    """
    tok = name.split("_")
    es = [t for t in tok[1:] if ETOKEN.match(t)]
    if not es:
        raise ValueError(f"no se reconoce el embrión en {name}")
    num = re.match(r"^E(\d+)", es[-1]).group(1)
    stage = ETOKEN.match(es[0]).group(1).replace(".5", "p5") if len(es) > 1 else ""
    return "_".join(p for p in (tok[0], f"E{stage}" if stage else "", f"E{num}") if p)


def build(rows: list[dict], relaxed_spacing: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    by = {PurePath(r["path"].replace("\\", "/")).as_posix(): r for r in rows if "error" not in r}
    out, excluded, seen = [], [], {}
    for path, img in sorted(by.items()):
        if path.endswith("_labels.nii") or path.endswith("_prebv.nii"):
            continue
        stem = path[:-4]
        name = PurePath(stem).name
        if name in seen:  # el mismo volumen en dos carpetas: se usa una vez
            excluded.append({"image": path, "structure": "ambas", "reason": f"duplicado de {seen[name]}"})
            continue
        seen[name] = path
        eid = embryo_id(name)
        for structure, suffix in (("body", "_BODY_labels.nii"), ("ventricle", "_BV_labels.nii")):
            lab = by.get(stem + suffix)
            if lab is None:
                excluded.append({"image": path, "structure": structure, "reason": "sin archivo de etiqueta"})
                continue
            if lab["shape"] != img["shape"]:
                excluded.append({"image": path, "structure": structure, "reason": "forma distinta"})
                continue
            if lab["spacing_mm"] != img["spacing_mm"] and not relaxed_spacing:
                excluded.append({"image": path, "structure": structure,
                                 "reason": f"vóxel distinto ({lab['spacing_mm']} frente a {img['spacing_mm']})"})
                continue
            if "1" not in lab.get("labels", []):
                excluded.append({"image": path, "structure": structure, "reason": "sin valor 1"})
                continue
            out.append({"embryo_id": eid, "structure": structure, "image": path, "label": stem + suffix,
                        "label_value": 1})
    return pd.DataFrame(out), pd.DataFrame(excluded)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("datasheet")
    ap.add_argument("--out", required=True)
    ap.add_argument("--relaxed-spacing", action="store_true")
    a = ap.parse_args(argv)
    rows = json.loads(open(a.datasheet, encoding="utf-8").read())
    man, exc = build(rows, a.relaxed_spacing)
    man.to_csv(a.out, index=False)
    exc.to_csv(a.out.replace(".csv", "_excluidos.csv"), index=False)
    print(man.groupby("structure").agg(casos=("image", "size"), embriones=("embryo_id", "nunique")))
    print(f"excluidos: {len(exc)}")
    if len(exc):
        print(exc.groupby(["structure", "reason"]).size())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
