"""Rotulado: validación de manifiestos de anotación (el CSV que consume H11) con metadatos de estadio,
procedencia y una compuerta dura para datos humanos.

Las referencias de consentimiento y de comité de ética de estas pruebas son ficticias.

Qué haría fallar cada prueba:
* si la compuerta humana dejara pasar una fila sin consentimiento o sin comité de ética, el proyecto
  podría procesar imágenes de personas sin base legal;
* si no se detectara un estadio imposible o un duplicado, las anotaciones no serían comparables;
* si un aviso (sin anotador, CRL fuera del rango del estadio) pasara por error, quedaría oculto.
"""
import pandas as pd

from geovida import labeling


def _animal(**over):
    row = {"embryo_id": "e1", "structure": "body", "image": "e1.nii.gz", "label": "e1_body.nii.gz",
           "label_value": 1, "species": "mouse", "stage_system": "theiler", "stage": 14, "age_days": 9.0,
           "crl_mm": 2.0, "annotator_id": "a1", "annotation_date": "2026-11-11", "consent_ref": "",
           "ethics_ref": "", "source": "lab propio"}
    row.update(over)
    return row


def _human(**over):
    row = _animal(embryo_id="h1", species="human", image="h1.nii.gz", label="h1_body.nii.gz",
                  stage_system="carnegie", stage=12, age_days=28, crl_mm=4.0,
                  consent_ref="CI-FICTICIO-001", ethics_ref="CEI-FICTICIO-77", source="convenio ficticio")
    row.update(over)
    return row


def _df(*rows):
    return pd.DataFrame(list(rows))


def test_a_complete_animal_manifest_is_valid():
    r = labeling.validate_manifest(_df(_animal(), _animal(embryo_id="e2", image="e2.nii.gz")))
    assert r["ok"] and r["errors"] == [] and r["warnings"] == [] and r["n_rows"] == 2


def test_missing_required_columns_are_errors_and_named():
    df = _df(_animal()).drop(columns=["label_value", "structure"])
    r = labeling.validate_manifest(df)
    assert not r["ok"]
    text = " ".join(r["errors"])
    assert "label_value" in text and "structure" in text


def test_duplicate_embryo_structure_image_is_an_error():
    r = labeling.validate_manifest(_df(_animal(), _animal()))
    assert not r["ok"] and any("duplicad" in e for e in r["errors"])


def test_unknown_species_is_an_error_and_missing_species_is_a_warning():
    assert not labeling.validate_manifest(_df(_animal(species="dragon")))["ok"]
    r = labeling.validate_manifest(_df(_animal()).drop(columns=["species"]))
    assert r["ok"] and any("especie" in w for w in r["warnings"])


def test_human_rows_need_both_consent_and_ethics_references():
    assert labeling.validate_manifest(_df(_human()))["ok"]
    for bad in ({"consent_ref": "", "ethics_ref": ""},
                {"consent_ref": "CI-FICTICIO-001", "ethics_ref": ""},
                {"consent_ref": "", "ethics_ref": "CEI-FICTICIO-77"},
                {"consent_ref": "   ", "ethics_ref": "CEI-FICTICIO-77"}):
        r = labeling.validate_manifest(_df(_human(**bad)))
        assert not r["ok"] and any("humano" in e for e in r["errors"]), bad


def test_human_gate_applies_per_row_even_if_other_rows_are_animal():
    r = labeling.validate_manifest(_df(_animal(), _human(consent_ref="", ethics_ref="")))
    assert not r["ok"] and len([e for e in r["errors"] if "humano" in e]) == 1


def test_human_gate_cannot_be_skipped_by_leaving_out_the_columns():
    df = _df(_human()).drop(columns=["consent_ref", "ethics_ref"])
    r = labeling.validate_manifest(df)
    assert not r["ok"] and any("humano" in e for e in r["errors"])


def test_carnegie_stage_must_be_between_1_and_23_for_human_rows():
    assert not labeling.validate_manifest(_df(_human(stage=24)))["ok"]
    assert not labeling.validate_manifest(_df(_human(stage=0)))["ok"]
    assert labeling.validate_manifest(_df(_human(stage=23, age_days=58, crl_mm=29.0)))["ok"]


def test_age_or_length_outside_the_stage_range_is_a_warning_not_an_error():
    r = labeling.validate_manifest(_df(_human(stage=12, crl_mm=20.0)))      # estadio 12: 3–5 mm
    assert r["ok"] and any("crl" in w.lower() for w in r["warnings"])
    r2 = labeling.validate_manifest(_df(_human(stage=12, age_days=60)))     # estadio 12: 26–30 días
    assert r2["ok"] and any("edad" in w.lower() for w in r2["warnings"])


def test_stage_ranges_overlap_so_a_value_in_the_stated_stage_range_is_fine():
    # 26 días pertenece al estadio 11 (23–26) y al 12 (26–30): no debe avisar para ninguno
    assert labeling.validate_manifest(_df(_human(stage=11, age_days=26, crl_mm=3.0)))["warnings"] == []
    assert labeling.validate_manifest(_df(_human(stage=12, age_days=26, crl_mm=4.0)))["warnings"] == []


def test_carnegie_for_a_non_human_species_is_a_warning():
    r = labeling.validate_manifest(_df(_animal(stage_system="carnegie", stage=12)))
    assert r["ok"] and any("carnegie" in w.lower() and "human" in w.lower() for w in r["warnings"])


def test_missing_annotator_is_a_warning_because_agreement_cannot_be_measured():
    r = labeling.validate_manifest(_df(_animal(annotator_id="")))
    assert r["ok"] and any("anotador" in w for w in r["warnings"])


def test_other_stage_systems_are_not_range_checked():
    assert labeling.validate_manifest(_df(_animal(stage_system="theiler", stage=99)))["ok"]
