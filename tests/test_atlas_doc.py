"""El documento del atlas (docs/ATLAS_ESTADIOS.md) no se separa del módulo ``geovida.atlas``.

Qué haría fallar cada prueba:
* si alguien cambia un número en el documento (o en el módulo) sin cambiar el otro, la tabla deja de coincidir;
* si desaparecen del documento la compuerta de datos humanos o el aviso de que los rasgos no están verificados,
  el documento prometería más de lo que el proyecto hace.
"""
import re
from pathlib import Path

from geovida import atlas

DOC = Path(__file__).resolve().parents[1] / "docs" / "ATLAS_ESTADIOS.md"
NUM = r"([\d.]+)(?:–([\d.]+))?"
ROW = re.compile(rf"^\| (\d+) \| {NUM} \| {NUM} \| {NUM} \|")


def _rows():
    out = {}
    for line in DOC.read_text(encoding="utf-8").splitlines():
        m = ROW.match(line)
        if m:
            out[int(m[1])] = m.groups()
    return out


def test_the_table_has_the_23_stages_and_matches_the_module():
    rows = _rows()
    assert sorted(rows) == list(range(1, 24))
    for s in atlas.CARNEGIE:
        g = rows[s.number]
        assert (float(g[1]), float(g[2] or g[1])) == (s.age_days_lo, s.age_days_hi)
        clo, chi = atlas.clinical_ga_days(s)
        assert (float(g[3]), float(g[4] or g[3])) == (clo, chi)
        assert (float(g[5]), float(g[6] or g[5])) == (s.length_mm_lo, s.length_mm_hi)


def test_the_document_states_its_limits_and_the_human_gate():
    text = DOC.read_text(encoding="utf-8")
    for must in ("no se comprobaron una por una", "consent_ref", "ethics_ref", "geovida.labeling",
                 "post ovulación", "Streeter"):
        assert must in text, must
