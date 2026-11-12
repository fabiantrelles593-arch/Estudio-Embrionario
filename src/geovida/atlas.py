"""Atlas de estadios de Carnegie del desarrollo embrionario humano.

Solo investigación y educación. Los números salen de una tabla pública y se citan tal cual; los rangos
de edad y de longitud **se solapan** porque el desarrollo varía entre embriones, así que buscar por una
edad o una longitud puede devolver más de un estadio.

Fuente abierta y verificada (2026-11-11): UNSW Embryology, «Carnegie stage table» (Dr. Mark Hill,
última modificación 21-12-2017), basada en la serie «Developmental Horizons in Human Embryos» de
George L. Streeter (Carnegie Institution of Washington, 1942–1957). La página da la edad como edad
embrionaria **post ovulación** y la edad gestacional clínica como esa edad más 2 semanas.
"""
from __future__ import annotations

from dataclasses import dataclass

SOURCE = ("UNSW Embryology, «Carnegie stage table» (Mark Hill, 21-12-2017), basada en Streeter, "
          "Developmental Horizons in Human Embryos, Carnegie Institution of Washington 1942-1957")
AGE_BASIS = "días de edad embrionaria post ovulación; la edad gestacional clínica es esa edad + 14 días"
CLINICAL_OFFSET_DAYS = 14


@dataclass(frozen=True)
class Stage:
    number: int
    age_days_lo: int
    age_days_hi: int
    length_mm_lo: float
    length_mm_hi: float
    features: str          # paráfrasis breve de los rasgos principales


CARNEGIE: tuple[Stage, ...] = (
    Stage(1, 1, 1, 0.1, 0.15, "cigoto con dos pronúcleos"),
    Stage(2, 2, 3, 0.1, 0.2, "mórula; se forma el blastocisto con masa interna y externa"),
    Stage(3, 4, 5, 0.1, 0.2, "se pierde la zona pelúcida; blastocisto libre"),
    Stage(4, 5, 6, 0.1, 0.2, "el blastocisto se adhiere a la pared uterina"),
    Stage(5, 7, 12, 0.1, 0.2, "implantación"),
    Stage(6, 13, 15, 0.2, 0.2, "mesodermo extraembrionario, línea primitiva; empieza la gastrulación"),
    Stage(7, 15, 17, 0.4, 0.4, "gastrulación; proceso notocordal"),
    Stage(8, 17, 19, 1.0, 1.5, "fosita primitiva; canal notocordal"),
    Stage(9, 19, 21, 1.5, 2.5, "somitas 1–3; pliegues neurales, primordio cardiaco, pliegue cefálico"),
    Stage(10, 22, 23, 2.0, 3.5, "somitas 4–12; fusión de los pliegues neurales"),
    Stage(11, 23, 26, 2.5, 4.5, "somitas 13–20; se cierra el neuroporo rostral"),
    Stage(12, 26, 30, 3.0, 5.0, "somitas 21–29; se cierra el neuroporo caudal"),
    Stage(13, 28, 32, 4.0, 6.0, "30 somitas; brotes de las piernas, placoda del cristalino, arcos faríngeos"),
    Stage(14, 31, 35, 5.0, 7.0, "fosita del cristalino; copa óptica"),
    Stage(15, 35, 38, 7.0, 9.0, "vesícula del cristalino; fosita nasal; placa de la mano"),
    Stage(16, 37, 42, 8.0, 11.0, "las fosas nasales se mueven ventralmente; montículos auriculares; placa del pie"),
    Stage(17, 42, 44, 11.0, 14.0, "radios de los dedos"),
    Stage(18, 44, 48, 13.0, 17.0, "comienza la osificación"),
    Stage(19, 48, 51, 16.0, 18.0, "el tronco se endereza"),
    Stage(20, 51, 53, 18.0, 22.0, "miembros superiores más largos, codos doblados"),
    Stage(21, 53, 54, 22.0, 24.0, "manos y pies girados hacia dentro"),
    Stage(22, 54, 56, 23.0, 28.0, "se forman los párpados y las orejas externas"),
    Stage(23, 56, 60, 27.0, 31.0, "cabeza redondeada; cuerpo y extremidades"),
)


def embryonic_to_clinical_days(embryonic_days: float) -> float:
    return embryonic_days + CLINICAL_OFFSET_DAYS


def clinical_ga_days(stage: Stage) -> tuple[int, int]:
    return (stage.age_days_lo + CLINICAL_OFFSET_DAYS, stage.age_days_hi + CLINICAL_OFFSET_DAYS)


def stages_for_age(embryonic_days: float) -> list[Stage]:
    """Todos los estadios cuyo rango de edad embrionaria contiene ``embryonic_days`` (extremos incluidos)."""
    return [s for s in CARNEGIE if s.age_days_lo <= embryonic_days <= s.age_days_hi]


def stages_for_length(length_mm: float) -> list[Stage]:
    """Todos los estadios cuyo rango de longitud contiene ``length_mm`` (extremos incluidos)."""
    return [s for s in CARNEGIE if s.length_mm_lo <= length_mm <= s.length_mm_hi]


def voxels_across(length_mm: float, voxel_mm: float) -> float:
    """Cuántos vóxeles caben a lo largo de una longitud (aritmética; no valida nada biológico)."""
    if not voxel_mm > 0:
        raise ValueError("el tamaño del vóxel debe ser > 0")
    return length_mm / voxel_mm
