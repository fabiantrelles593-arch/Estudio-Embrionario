# Resultados — MT-A v1.1: efecto del atlas sobre la forma, puerta de distancia al tejido (19 nov 2026)

> Preregistro: `docs/morpho_trace/PREREGISTRO_ATLAS_v1_1.md` (subido en `ff079c9`, antes de medir). Antecedente:
> `docs/morpho_trace/RESULTADOS_ATLAS.md` (v1.0, no evaluable). Código: `scripts/atlas_effect_gates.py` (`g0b2`,
> `g0a2`), `geovida.atlas_effect.distance_to_tissue`. Datos: MusMorph/IMPC en FaceBase (CC BY 4.0, Devine et al.
> 2022), manifiestos en `data/manifests/`. Resultados brutos fuera de git (`results/morpho_trace/g0a2.json`,
> `g0b2.json`). Solo datos animales; nada clínico.
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta.

## 1. Veredicto

**MT-A1, MT-A2 y MT-A3: no evaluables.** La puerta G0-a′ falló: 31 de los 37 especímenes no vistos cumplen el
criterio y se exigían 35 [HV]. Según §6 del preregistro, no se hizo ningún registro.

Tampoco habría sido evaluable siguiendo la regla de exclusión: sin los 6 especímenes que fallan, E15.5 se queda en
14 especímenes válidos y G2 exige 16 por estadio [HV]. Con esta muestra piloto, MT-A no se puede medir.

## 2. Puertas

| Puerta | Criterio | Resultado | Estado |
|---|---|---|---|
| G0-c, G0-d | (v1.0) | superadas en v1.0 | **Superadas** |
| G0-b′ · atlas | ≥ 95 % de landmarks a ≤ 0,23 mm del tejido, en los dos atlas | E15.5: 100 % · E18.5: 100 % (p90 0 y 0,044 mm) | **Superada** [HV] (atlas ya vistos en v1.0) |
| G0-a′ · especímenes | ≥ 35 de 37 no vistos con ≥ 95 % de landmarks a ≤ 0,23 mm | **31 de 37** | **Fallida** [HV] |

Por estadio, contando los 40:

| Estadio | Especímenes que cumplen | Fracción media de landmarks a ≤ 0,23 mm | p90 de la distancia (mediana entre especímenes) |
|---|---|---|---|
| E15.5 | **14 de 20** | 93,4 % | 0,149 mm |
| E18.5 | **20 de 20** | 99,9 % | 0,055 mm |

Los 6 que no cumplen son todos de E15.5 y ninguno de los 3 ya vistos: `IMPC_E15.5_0864` (58,0 %),
`IMPC_E15.5_0852` (65,7 %), `IMPC_E15.5_0434` (83,0 %), `IMPC_E15.5_0847` (85,4 %), `IMPC_E15.5_1185`
(93,3 %) e `IMPC_E15.5_0429` (94,8 %). En `IMPC_E15.5_0864`, 30 de sus 540 landmarks quedan a más de 0,5 mm de
cualquier tejido. Los 3 vistos cumplen (95,9 %, 98,9 % y 100 %).

## 3. Predicciones frente a resultado

| Predicción (§5) | Probabilidad dada | Resultado |
|---|---|---|
| Pasa G0-b′ | 70 % | **Sí** |
| Pasa G0-a′ | 60 % | **No** (31 de 37) |
| G1, MT-A1, MT-A2 | — | No medidos |

## 4. Qué muestra el resultado (descriptivo; no cambia el veredicto)

* **La geometría de E18.5 es buena; la de una parte de E15.5, no** [HV]. En 6 de los 20 especímenes E15.5 del
  piloto, más del 5 % de los landmarks publicados quedan a más de 0,23 mm del tejido (el error que MusMorph publica
  para sus landmarks automáticos), y en dos de ellos más de un tercio.
* **Encaja con lo que dicen los autores de MusMorph** [EI]. Avisan de errores locales de registro en embriones
  cuando la cabeza está orientada de forma distinta a la del atlas, y de que retiraron solo los archivos con errores
  claros (Devine et al. 2022, §Technical Validation). Estos 6 especímenes no se retiraron, pero tienen landmarks
  desplazados.
* **Consecuencia para ONTO-MAP** [HIP]. ONTO-MAP usó los landmarks publicados tal cual. Si una fracción parecida de
  los especímenes E15.5 de su muestra tiene landmarks desplazados, una parte de la separación **d** y de la
  dispersión dentro de E15.5 podría ser error de colocación y no biología. No está medido: es una hipótesis para un
  estudio futuro, no una conclusión.

## 5. Qué no se puede concluir

* Nada sobre el efecto del atlas: MT-A no llegó a medirlo en ninguna de sus dos versiones.
* El 30 % de especímenes E15.5 fuera de criterio es del piloto de 20; no es una tasa estimada para todo MusMorph.
* El umbral de 0,23 mm viene de cráneos adultos; en embriones podría ser demasiado estricto o demasiado laxo.

## 6. Siguiente paso propuesto (no ejecutado)

* **No se repite MT-A con otro umbral ni otra muestra elegida después de ver esto.** Cualquier versión nueva
  necesita un diseño distinto y un preregistro nuevo.
* **[PROP] Control de calidad de los landmarks publicados de MusMorph.** Medir la distancia al tejido de los
  landmarks de los especímenes usados en ONTO-MAP, con el mismo método y criterio, y comprobar si la separación **d**
  cambia al quitar los que no cumplen. El cálculo es rápido (los 40 de G0-a′ tardaron 25 min), pero necesita las
  imágenes: ONTO-MAP solo bajó landmarks, y sus 717 especímenes del confirmatorio suman decenas de GB (las de E15.5
  pesan unos 94 MB cada una). Habría que preregistrar una submuestra aleatoria y pedir permiso para la descarga.
* Después, un MT-A nuevo podría preregistrar de antemano una muestra de especímenes que cumplan el control de
  calidad, elegida por la misma semilla entre los que pasan.
