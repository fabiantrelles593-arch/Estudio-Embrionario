# Preregistro — QC-LM: ¿están bien colocados los landmarks publicados de MusMorph, y cambia **d** si se quitan los que no? (v1.0, 19 nov 2026)

> Siguiente paso fijado por `docs/morpho_trace/RESULTADOS_ATLAS_v1_1.md` §6. Se sube a la rama **antes** de
> descargar las imágenes y antes de medir nada en ellas. Etiquetas: [HV] verificado · [EI] evidencia indirecta ·
> [HIP] hipótesis · [PROP] propuesta. Solo datos animales publicados (MusMorph/IMPC, FaceBase 3-JZA6, CC BY 4.0,
> Devine et al. 2022). Nada humano ni clínico.

## 1. Pregunta y por qué importa

En el piloto de MT-A, 6 de 20 especímenes E15.5 y 0 de 20 E18.5 tenían más del 5 % de sus landmarks publicados a
más de 0,23 mm del tejido [HV, `RESULTADOS_ATLAS_v1_1.md` §2]. ONTO-MAP usó esos landmarks publicados tal cual para
estimar **d**, la separación de forma entre E15.5 y E18.5 [HV, `docs/onto_map/RESULTADOS_P4.md`].

**QC-LM pregunta, en especímenes nuevos del confirmatorio de ONTO-MAP:** (1) ¿es más frecuente en E15.5 que en E18.5
que los landmarks publicados estén lejos del tejido?, y (2) ¿cambia la longitud de **d** al quitar los especímenes que
no cumplen?

## 2. Datos y muestra (fijos)

* **Población:** los 717 especímenes del confirmatorio de ONTO-MAP (259 E15.5 y 458 E18.5,
  `results/onto_map/seleccion.json`), con landmarks publicados ya descargados (`data/external/musmorph/landmarks_confirm`).
  Los 717 tienen imagen en FaceBase 3-JZA6 (comprobado en el catálogo el 19 nov) [HV]. Son disjuntos del piloto de
  MT-A, así que **ningún** espécimen de la muestra se ha visto antes.
* **Muestra:** aleatoria simple sin reemplazo, **60 por estadio**, semilla **20261119**, sobre la lista ordenada de
  nombres (`scripts/landmark_qc.py select`). Ya extraída (sin mirar ninguna imagen): `results/landmark_qc/muestra.json`,
  SHA-256 de `json.dumps(sample, sort_keys=True)`: `8c97e0b9980f20ca7c3f09ca983416c90049d2ccc3eb66bf38f2758caef49784`.
* **Tamaño:** con 60 por estadio, si las tasas fueran las del piloto (30 % y 0 %), el IC 95 % de la diferencia tendría
  una semianchura de unos 12 puntos; basta para distinguirla de cero [EI, aproximación binomial].
* **Descarga:** 102 imágenes, **6,14 GB** (42 de E15.5, 3,90 GB; 60 de E18.5, 2,24 GB). Las otras 18 de E15.5 ya están
  en disco (descarga de P3) y se copian solo si su MD5 coincide con el catálogo. MD5 de cada archivo comprobado;
  manifiesto SHA-256 en `data/manifests/`; nada en git.

## 3. Medida (la misma que MT-A v1.1)

Para cada espécimen, la **distancia al tejido** de cada uno de sus 540 landmarks publicados: 0 si su vóxel está por
encima del umbral de Otsu de toda la imagen; si no, la distancia al vóxel más cercano por encima, a resolución
completa, buscando hasta 0,5 mm (`geovida.atlas_effect.distance_to_tissue`). Un espécimen **cumple** si ≥ 95 % de sus
landmarks quedan a ≤ **0,23 mm** (error publicado de los landmarks automáticos de MusMorph). Se registra también la
mediana, el p90 y cuántos quedan a más de 0,5 mm.

## 4. Puertas (si una falla, no hay veredicto)

| Puerta | Qué se comprueba | Criterio |
|---|---|---|
| **G1** Medidas completas | Especímenes descargados con MD5 correcto y medidos sin error | ≥ 57 de 60 por estadio |
| **G2** Geometría | Cada imagen medida tiene la misma rejilla (forma y afín) que el atlas de su estadio, como las 40 de MT-A | Todas |

## 5. Hipótesis y criterios (fijos)

**QC1 (primaria) — Más landmarks desplazados en E15.5.** Δ = (fracción de E15.5 que no cumple) − (fracción de E18.5 que
no cumple), IC 95 % por remuestreo de especímenes dentro de cada estadio (2000 réplicas, semilla 20261119).
*Apoyada* si el límite inferior es > 0. *Refutada* si el límite superior es < 0,05. *No concluyente* en otro caso.

**QC2 (secundaria) — Quitar los que no cumplen cambia d.** r = (|d|_cumplen − |d|_todos) / |d|_todos, donde |d| se calcula con
los 120 especímenes de la muestra (GPA único, coordenadas tangentes, media E18.5 − media E15.5, como en ONTO-MAP y
G0-d) con todos ellos o solo con los que cumplen. IC 95 % por el mismo remuestreo, recalculando ambos |d| en cada
réplica. *Apoyada* si el IC excluye 0 y |r| ≥ 0,05. *Refutada* si el IC queda dentro de (−0,05, 0,05). *No
concluyente* en otro caso. **Evaluable** solo si hay ≥ 3 especímenes E15.5 que no cumplen y ≥ 30 que cumplen en cada
estadio; si no, «no evaluable».

**QC3 (descriptiva).** Distribución por estadio de la fracción de landmarks a ≤ 0,23 mm, la mediana y el p90; |d| con
todos y con los que cumplen.

Un valor no calculable es «no evaluable», nunca «refutada».

## 6. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| Pasan G1 y G2 | 85 % |
| QC1 apoyada | 65 % |
| QC1 refutada | 10 % |
| QC2 evaluable | 70 % |
| QC2 apoyada, dado que es evaluable | 35 % |
| QC2 refutada, dado que es evaluable | 30 % |

## 7. Qué significará cada resultado (antes de verlo)

| Resultado | Conclusión | Siguiente paso |
|---|---|---|
| QC1 apoyada, QC2 apoyada | Los landmarks publicados de E15.5 tienen errores de colocación frecuentes y cambian **d**: la separación de ONTO-MAP mezcla biología con error | Repetir el análisis de ONTO-MAP solo con especímenes que cumplan; un MT-A nuevo con muestra filtrada |
| QC1 apoyada, QC2 refutada | Hay errores, pero no mueven **d** a esta escala | **d** de ONTO-MAP se mantiene frente a este error; el factor atlas sigue sin medir |
| QC1 refutada | Lo del piloto no se repite: no hay más errores en E15.5 | El problema de MT-A fue de la muestra piloto |
| No concluyente | Hace falta más muestra | Ampliar con el mismo protocolo |

## 8. Qué no se puede concluir

* «Lejos del tejido» no es lo mismo que «mal colocado»: un landmark puede estar bien colocado en una zona de poco
  contraste. El umbral de 0,23 mm viene de cráneos adultos [EI].
* Una muestra de 60 por estadio estima tasas, no identifica todos los especímenes problemáticos de MusMorph.
* QC2 mide el cambio de **d** en la muestra, no en los 717; no corrige el resultado publicado de ONTO-MAP.
* Nada sobre el efecto del atlas (MT-A), sobre otras especies, humanos ni uso clínico.

## 9. Ejecución

1. Código `scripts/landmark_qc.py` y pruebas `tests/test_landmark_qc.py` (muestra reproducible, puertas, QC1 y QC2
   con casos sintéticos de error conocido), subidos con este preregistro.
2. Descarga, **con permiso explícito** (nombre, fuente y tamaño indicados en §2).
3. `measure` (reanudable; menos de un minuto por espécimen) y `analyze`.
4. Resultados en `docs/morpho_trace/RESULTADOS_QC_LANDMARKS.md`, transcribiendo los veredictos sin reinterpretar.

## 10. Desviaciones

(Ninguna al subir este preregistro.)
