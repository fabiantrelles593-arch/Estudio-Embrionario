"""Atlas de estadios de Carnegie (tabla verificada en UNSW Embryology, basada en Streeter).

Qué haría fallar cada prueba:
* si se alterara un número de la tabla (edad, longitud), las comprobaciones de valores citados fallarían;
* si los rangos no fueran monótonos, la búsqueda por edad o longitud devolvería estadios imposibles;
* si la edad gestacional clínica no fuera la embrionaria + 14 días, la conversión sería incorrecta.
"""
import pytest

from geovida import atlas


def test_table_has_23_stages_in_order_with_consistent_ranges():
    st = atlas.CARNEGIE
    assert [s.number for s in st] == list(range(1, 24))
    for s in st:
        assert s.age_days_lo <= s.age_days_hi
        assert s.length_mm_lo <= s.length_mm_hi
    assert all(a.age_days_lo <= b.age_days_lo for a, b in zip(st, st[1:]))
    assert all(a.length_mm_lo <= b.length_mm_lo for a, b in zip(st, st[1:]))


@pytest.mark.parametrize("number,days,length", [
    (1, (1, 1), (0.1, 0.15)),
    (6, (13, 15), (0.2, 0.2)),
    (9, (19, 21), (1.5, 2.5)),
    (11, (23, 26), (2.5, 4.5)),
    (12, (26, 30), (3.0, 5.0)),
    (17, (42, 44), (11.0, 14.0)),
    (23, (56, 60), (27.0, 31.0)),
])
def test_cited_values_match_the_source_table(number, days, length):
    s = atlas.CARNEGIE[number - 1]
    assert (s.age_days_lo, s.age_days_hi) == days
    assert (s.length_mm_lo, s.length_mm_hi) == length


def test_clinical_gestational_age_is_embryonic_age_plus_14_days():
    s = atlas.CARNEGIE[9]      # estadio 10: 22-23 días
    assert atlas.clinical_ga_days(s) == (22 + 14, 23 + 14)
    assert atlas.embryonic_to_clinical_days(30) == 44


def test_stages_for_age_returns_every_overlapping_stage():
    assert [s.number for s in atlas.stages_for_age(21)] == [9]
    assert [s.number for s in atlas.stages_for_age(26)] == [11, 12]      # 23-26 y 26-30
    assert atlas.stages_for_age(200) == []                             # fuera de la tabla


def test_stages_for_length_uses_inclusive_ranges():
    nums = [s.number for s in atlas.stages_for_length(4.0)]
    assert 11 in nums and 12 in nums and 13 in nums
    assert atlas.stages_for_length(1000.0) == []


def test_source_and_basis_are_stated_on_the_module():
    assert "post ovulación" in atlas.AGE_BASIS
    assert "Streeter" in atlas.SOURCE and "UNSW" in atlas.SOURCE


def test_voxels_across_is_arithmetic_and_rejects_nonpositive_voxel():
    assert atlas.voxels_across(3.0, 0.5) == pytest.approx(6.0)
    with pytest.raises(ValueError):
        atlas.voxels_across(3.0, 0.0)
