"""La matriz de trazabilidad (docs/clinico/TRAZABILIDAD.md) solo cita archivos que existen.

Qué falla si alguien renombra un módulo, un script, una prueba o un resultado sin actualizar la
matriz. No comprueba que los resultados sean correctos."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "clinico" / "TRAZABILIDAD.md"
PATH_LIKE = re.compile(r"`((?:docs|src|scripts|tests|results)/[^`\s]+)`")


def _cited():
    return sorted(set(PATH_LIKE.findall(DOC.read_text(encoding="utf-8"))))


def test_matrix_cites_a_reasonable_number_of_files():
    assert len(_cited()) >= 40


def test_every_cited_file_exists():
    missing = [p for p in _cited() if not (ROOT / p).exists()]
    assert not missing, f"citados en TRAZABILIDAD.md pero inexistentes: {missing}"


def test_every_preregistration_and_results_document_is_in_the_matrix():
    cited = set(_cited())
    for doc in sorted((ROOT / "docs").glob("PREREGISTRO_*.md")) + \
            sorted((ROOT / "docs").glob("RESULTADOS*.md")):
        assert f"docs/{doc.name}" in cited, f"{doc.name} no está en la matriz de trazabilidad"
