# Resultados — MT-A v1.0: efecto del atlas sobre la forma (19 nov 2026)

> Preregistro: `docs/morpho_trace/PREREGISTRO_ATLAS.md` (v1.0, 18 nov, y notas de ejecución de §11).
> Código: `scripts/atlas_effect_gates.py`, `src/geovida/atlas_effect.py`, `src/geovida/minc.py`.
> Datos: FaceBase 6-2EPY y 3-JZA6 (MusMorph/IMPC, CC BY 4.0, Devine et al. 2022), manifiestos en
> `data/manifests/musmorph_atlas.csv` y `data/manifests/musmorph_mta_images.csv`. Resultados brutos fuera de git
> (`results/morpho_trace/`). Solo datos animales; nada clínico.
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta.

## 1. Veredicto

**MT-A1, MT-A2 y MT-A3: no evaluables.** Fallaron dos puertas previas (G0-a y G0-b), y §4 dice que si una puerta
falla no hay veredicto [HV]. No se hizo ningún registro: se detuvieron antes de empezar, porque su resultado ya no
podía dar un veredicto con este protocolo.

Esto **no** dice nada sobre cuánto de **d** se debe al atlas: la pregunta sigue abierta.

## 2. Puertas

| Puerta | Criterio (§4) | Resultado | Estado |
|---|---|---|---|
| G0-d · reproducción de d | longitud en [0,150, 0,164] | 0,156707 | **Superada** [HV] |
| G0-c · correspondencia entre atlas | ρ dado < mínimo de 200 barajados | 0,160 frente a ≥ 1,454 | **Superada** [HV] |
| G0-b · landmarks del atlas sobre Otsu | ≥ 95 % por atlas | E15.5: 96,3 % · E18.5: **58,0 %** | **Fallida** [HV] |
| G0-a · landmarks publicados sobre Otsu | ≥ 95 % por espécimen | `IMPC_E15.5_1212`: **14,4 %** · `IMPC_E18.5_1287`: **58,0 %** · `IMPC_E15.5_0437`: **43,3 %** | **Fallida** [HV] |
| G1, G2 | — | no se llegó a medir | — |

Medido a resolución completa con lectura por losas, con el mismo resultado que cargar la imagen entera
(`tests/test_atlas_stream.py`); umbral de Otsu sobre toda la imagen, 540 landmarks por imagen.

## 3. Por qué fallaron (diagnóstico hecho después de ver el resultado; no cambia el veredicto)

Se miró, en los volúmenes ×4, dónde caen los landmarks respecto a la imagen y al tejido sobre el umbral:

| Imagen | Landmarks dentro del volumen | Distancia al tejido sobre Otsu: mediana · p90 | Tejido sobre Otsu (% del volumen) |
|---|---|---|---|
| Atlas E15.5 | 100 % | 0 · 0,108 mm | 10 % |
| Atlas E18.5 | 100 % | 0 · 0,216 mm | 8 % |
| `IMPC_E15.5_1212` | 100 % | 0,108 · 0,219 mm | 10 % |
| `IMPC_E18.5_1287` | 100 % | 0 · 0,216 mm | 7 % |
| `IMPC_E15.5_0437` | 100 % | 0,108 · 0,153 mm | 6 % |

* **La geometría está bien** [HV]. Todos los landmarks caen dentro de su imagen y en el mismo espacio que los del
  atlas: los publicados de los tres especímenes quedan a una mediana de 0,25 a 0,92 mm de los del atlas de su
  estadio, con ρ de Procrustes de 0,03 a 0,07. No hay un error de convención de coordenadas.
* **Los puntos que «fallan» están en el borde del tejido** [HV]. Su distancia al tejido sobre el umbral es como
  mucho de un vóxel ×4 (0,108 mm en E15.5, 0,216 mm en E18.5) para el 90 % de los puntos.
* **La puerta estaba mal planteada** [EI]. Los landmarks de cabeza de MusMorph marcan sobre todo superficies y
  bordes; un punto en un borde cae dentro o fuera del umbral casi al azar, así que exigir el 95 % por encima de
  Otsu no podía cumplirse aunque la geometría fuera perfecta. Además, en estas imágenes Otsu deja por encima solo
  el 6–10 % del volumen, es decir, el tejido más denso y no toda la cabeza. El atlas E15.5 la pasó (96 %) quizá
  porque es una media de muchos especímenes, con bordes más suaves [HIP].

## 4. Predicciones frente a resultado

| Predicción (§7) | Probabilidad dada | Resultado |
|---|---|---|
| Pasan las puertas G0 | 75 % | **No** (fallan G0-a y G0-b) |
| Pasa G1 | 50 % | No medido |
| MT-A1 apoyada / refutada | 40 % / 25 % | No evaluable |
| MT-A2 < 45° | 60 % | No evaluable |

La confianza en las puertas fue excesiva: se diseñaron sin mirar cómo están colocados los landmarks.

## 5. Qué se aprendió

* La lectura por losas permite trabajar con las imágenes de MusMorph en un equipo de 3,9 GB sin esperar a que
  terminen otras mediciones, con el mismo resultado que cargarlas enteras [HV].
* Las imágenes de MusMorph se distribuyen ya remuestreadas al espacio de su atlas, y el atlas y las imágenes de
  E18.5 tienen vóxel de 54 µm [HV]. Las dos cosas cambian el diseño de cualquier registro posterior.
* Una puerta de geometría para landmarks de superficie debe medir **distancia al borde**, no pertenencia al tejido.

## 6. Siguiente paso propuesto (no ejecutado)

**MT-A v1.1 [PROP]**, como preregistro nuevo, sin tocar este veredicto:

* Sustituir G0-a/G0-b por una puerta de distancia: cada landmark a menos de *X* mm de un borde del tejido. *X*
  se fijaría por una razón independiente de estos datos (por ejemplo, el error de colocación publicado por
  MusMorph), **no** con las distancias de §3, que ya se han visto.
* Comprobarla en especímenes distintos de los tres de G0-a.
* Mantener sin cambios todo lo demás: G0-c y G0-d ya superadas, registro, estimando f y criterios de §5.

Como §3 ya mostró estas distancias, cualquier umbral nuevo se elige sabiéndolas; el preregistro nuevo debe
declararlo. La puerta no toca el estimando f, así que el riesgo de sesgo sobre el veredicto es bajo, pero no nulo.

## 7. Qué no se puede concluir

* Nada sobre el efecto del atlas: MT-A no llegó a medirlo.
* Que la geometría esté bien en 3 especímenes y 2 atlas no garantiza que lo esté en los 40.
* El diagnóstico de §3 es posterior al resultado y descriptivo; no sustituye a una puerta preregistrada.
