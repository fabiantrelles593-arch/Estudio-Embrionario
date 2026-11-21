"""Rotulado: validación de manifiestos de anotación.

Solo investigación y educación. El manifiesto es el CSV que consume ``geovida.h11`` (columnas obligatorias
``embryo_id, structure, image, label, label_value``) más metadatos opcionales de especie, estadio,
procedencia y anotador. Este validador **no abre imágenes**: revisa que el manifiesto sea coherente y,
sobre todo, aplica una compuerta dura para datos humanos.

Compuerta humana: toda fila con ``species == "human"`` necesita ``consent_ref`` (referencia del consentimiento
informado) y ``ethics_ref`` (aprobación de un comité de ética) no vacíos. Sin ellos el manifiesto no es
válido, aunque las columnas falten del todo. El validador no puede comprobar que esas referencias sean reales:
solo impide que se omitan. La anonimización y la base legal siguen siendo responsabilidad de quien aporta los datos.
"""
from __future__ import annotations

import math

import pandas as pd

from . import atlas

REQUIRED = ("embryo_id", "structure", "image", "label", "label_value")
OPTIONAL = ("species", "stage_system", "stage", "age_days", "crl_mm", "annotator_id", "annotation_date",
            "consent_ref", "ethics_ref", "source")
SPECIES = ("mouse", "rat", "zebrafish", "chick", "human", "other")


def _blank(v) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    return str(v).strip() == ""


def _num(v):
    try:
        x = float(v)
        return None if math.isnan(x) else x
    except (TypeError, ValueError):
        return None


def validate_manifest(df: pd.DataFrame) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    missing = [c for c in REQUIRED if c not in df.columns]
    for c in missing:
        errors.append(f"falta la columna obligatoria {c!r}")
    cols = set(df.columns)

    if not missing:
        dup = df.duplicated(["embryo_id", "structure", "image"], keep=False)
        if dup.any():
            errors.append(f"{int(dup.sum())} fila(s) duplicada(s) en (embryo_id, structure, image)")

    if "species" not in cols:
        warnings.append("no hay columna de especie: se trata cada fila como 'other' (y no se aplica la compuerta humana)")
    if "annotator_id" not in cols or df["annotator_id"].map(_blank).any():
        warnings.append("hay filas sin anotador (annotator_id): sin él no se puede medir acuerdo entre anotadores")

    for i, row in df.iterrows():
        where = f"fila {i + 1}"
        species = None if "species" not in cols or _blank(row["species"]) else str(row["species"]).strip().lower()
        if species is not None and species not in SPECIES:
            errors.append(f"{where}: especie {species!r} desconocida; opciones: {SPECIES}")
        if species == "human":
            miss = [c for c in ("consent_ref", "ethics_ref") if c not in cols or _blank(row[c])]
            if miss:
                errors.append(f"{where}: dato humano sin {', '.join(miss)}: no se puede usar sin consentimiento "
                              "informado y aprobación de un comité de ética")
        system = None if "stage_system" not in cols or _blank(row["stage_system"]) else str(row["stage_system"]).strip().lower()
        if system != "carnegie":
            continue
        if species != "human":
            warnings.append(f"{where}: la escala Carnegie de este atlas es la humana; con otra especie declare "
                            "en stage_system la escala que use")
            continue
        stage = _num(row["stage"]) if "stage" in cols else None
        if stage is None or not (1 <= stage <= 23) or stage != int(stage):
            errors.append(f"{where}: estadio de Carnegie {row.get('stage')!r} inválido (debe ser un entero de 1 a 23)")
            continue
        st = atlas.CARNEGIE[int(stage) - 1]
        age = _num(row["age_days"]) if "age_days" in cols else None
        if age is not None and not (st.age_days_lo <= age <= st.age_days_hi):
            warnings.append(f"{where}: edad {age:g} d fuera del rango del estadio {st.number} "
                            f"({st.age_days_lo}–{st.age_days_hi} d post ovulación)")
        crl = _num(row["crl_mm"]) if "crl_mm" in cols else None
        if crl is not None and not (st.length_mm_lo <= crl <= st.length_mm_hi):
            warnings.append(f"{where}: CRL {crl:g} mm fuera del rango del estadio {st.number} "
                            f"({st.length_mm_lo:g}–{st.length_mm_hi:g} mm)")

    return {"ok": not errors, "errors": errors, "warnings": warnings, "n_rows": int(len(df))}
