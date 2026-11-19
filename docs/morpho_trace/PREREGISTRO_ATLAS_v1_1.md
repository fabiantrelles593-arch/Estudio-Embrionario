# Preregistro — MT-A v1.1: efecto del atlas sobre la forma, con puerta de geometría corregida (19 nov 2026)

> Sustituye solo las puertas G0-a y G0-b de `docs/morpho_trace/PREREGISTRO_ATLAS.md` (v1.0), que se cerró como
> **no evaluable** (`docs/morpho_trace/RESULTADOS_ATLAS.md`). Ese veredicto no se toca. Todo lo que este documento
> no cambia sigue como en v1.0: pregunta, datos, muestra, registro, espacio de forma, estimandos, criterios de §5,
> sensibilidad y lo que no se puede concluir.
> Se sube a la rama **antes** de medir las puertas nuevas y antes de cualquier registro.
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta.
> Solo datos animales publicados (MusMorph/IMPC, FaceBase, CC BY 4.0). Nada humano ni clínico.

## 1. Qué cambia y por qué

En v1.0, G0-a y G0-b exigían que el 95 % de los landmarks cayera en vóxeles **por encima** del umbral de Otsu.
Los landmarks de cabeza de MusMorph marcan sobre todo superficies; un punto en el borde cae a un lado u otro del
umbral casi al azar. Las puertas fallaron (G0-a: 14 %, 58 % y 43 %; G0-b en el atlas E18.5: 58 %) con la geometría
correcta [HV, `RESULTADOS_ATLAS.md` §3]. v1.1 mide lo que la puerta quería comprobar: que cada landmark esté
**cerca del tejido**, no dentro.

## 2. Lo que ya se ha visto (declarado)

* En v1.0 se midió, sobre volúmenes ×4, la distancia de los landmarks al tejido sobre Otsu en los **dos atlas** y en
  **tres especímenes** (`IMPC_E15.5_1212`, `IMPC_E18.5_1287`, `IMPC_E15.5_0437`): p90 entre 0,153 y 0,219 mm.
* El umbral de distancia de §3 **no** se eligió a partir de esas cifras, pero se fija sabiéndolas: está cerca de
  ellas. Por eso G0-a′ se evalúa solo en los **37 especímenes no vistos**, y G0-b′ (los atlas, ya vistos) se informa
  con esa salvedad.
* Las puertas G0-c y G0-d ya están superadas (v1.0) y no se repiten.

## 3. Puertas nuevas (sustituyen a G0-a y G0-b)

**Distancia al tejido** de un landmark: 0 si su vóxel está por encima del umbral de Otsu de la imagen; si no, la
distancia euclídea en mm al centro del vóxel más cercano por encima del umbral. Se mide **a resolución completa**
(27 µm en E15.5, 54 µm en E18.5), leyendo solo un cubo de ±0,5 mm alrededor de cada landmark; más allá de 0,5 mm
se registra como «> 0,5 mm». El umbral de Otsu es el de toda la imagen, como en v1.0.

**Umbral de distancia: 0,23 mm.** Es el error medio (RMSE) de los landmarks automáticos de MusMorph frente a los
manuales que publican sus autores, comparable al error intraobservador manual (≤ 0,25 mm) [HV en la publicación:
Devine et al. 2022, *Sci Data* 9:230, §Technical Validation; DOI 10.1038/s41597-022-01338-x]. Se midió en cráneos
adultos, no en embriones [EI para este uso].

| Puerta | Qué se comprueba | Criterio |
|---|---|---|
| **G0-a′** Geometría de los especímenes | Para cada uno de los 37 especímenes del piloto no vistos, fracción de sus 540 landmarks publicados con distancia al tejido ≤ 0,23 mm | Un espécimen **pasa** con ≥ 95 %. La puerta pasa si pasan **≥ 35 de 37** |
| **G0-b′** Geometría de los atlas | Ídem con los 540 landmarks de cada atlas sobre su imagen | Pasan los dos atlas (≥ 95 % cada uno) |

**Especímenes que no pasan G0-a′.** El mismo criterio por espécimen se aplica a los 40 (también a los 3 ya vistos).
Un espécimen que no lo cumple **se excluye** del análisis y cuenta como no válido en G2. Así una imagen con
landmarks mal colocados no entra en f, y la exclusión queda fijada antes de registrar.

## 4. Sin cambios respecto a v1.0

Registro (×4, momentos → afín → B-spline 8³, semilla 20261118), transferencia de los landmarks del atlas, un GPA
común con las 717 configuraciones publicadas, **δ(s)**, **f = ⟨δ̄, d̂⟩ / |d|** con remuestreo (2000 réplicas),
criterios de MT-A1 (apoyada si el límite inferior ≥ 0,50; refutada si el superior ≤ 0,25), MT-A2 (< 45°), MT-A3,
G1 y G2 (≥ 16 de 20 especímenes válidos por estadio, con sus dos registros terminados), la sensibilidad de §6 y
§8–§9. Un fallo de cualquier puerta deja el estudio en «no evaluable».

Notas de v1.0 que siguen en vigor: lectura por losas (mismo resultado que cargar la imagen entera), vóxel de E18.5
de 54 µm, e imágenes ya remuestreadas al espacio de su atlas, lo que hace G1 más fácil de superar (§9).

## 5. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| Pasa G0-b′ | 70 % |
| Pasa G0-a′ (≥ 35 de 37) | 60 % |
| Pasa G1, dado que pasan las G0 | 80 % (más alta que en v1.0 por las imágenes ya alineadas a su atlas) |
| MT-A1 apoyada, dado que es evaluable | 40 % |
| MT-A1 refutada, dado que es evaluable | 25 % |
| MT-A2: ángulo < 45° | 60 % |

## 6. Ejecución

1. Código: `atlas_effect.distance_to_tissue` (cubo local a resolución completa) y subcomandos `g0a2` y `g0b2` de
   `scripts/atlas_effect_gates.py`, probados con fantomas de distancia conocida **antes** de medir.
2. G0-b′ y G0-a′. Si alguna falla: «no evaluable», documento de resultados y fin.
3. Si pasan: los 80 registros (reanudables), `analyze` con las exclusiones de §3, y la sensibilidad de §6 de v1.0.
4. Resultados en `docs/morpho_trace/RESULTADOS_ATLAS_v1_1.md`, transcribiendo los veredictos sin reinterpretar.

## 7. Desviaciones

(Ninguna al subir este preregistro.)

* **19 nov 2026 — G0-b′ superada, G0-a′ fallida (31 de 37); no evaluable.** Sin desviaciones. No se hizo ningún
  registro. Resultados en `docs/morpho_trace/RESULTADOS_ATLAS_v1_1.md`.
