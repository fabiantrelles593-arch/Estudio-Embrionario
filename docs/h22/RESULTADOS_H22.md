# H22 — Resultados: ¿puede la guardia distinguir «fuera de dominio» de «inservible»?

> Aplica `docs/h22/PREREGISTRO_H22.md` (v1.0, aprobado el 21 nov 2026, commit `2c5983e`) sin desviaciones. Los
> veredictos son los del código preregistrado (`geovida.h22.verdicts`), transcritos sin cambios. Las cifras salen de
> `scripts/run_h22.py analyze` sobre `results/h22/` (fuera de git). Solo imágenes sintéticas con verdad analítica;
> ningún dato real ni clínico. Etiquetas: [HV] hecho verificado · [EI] evidencia indirecta · [HIP] hipótesis ·
> [PROP] propuesta · [PV] pendiente de validación.

## 1. Resumen

* **Decisión del §8: no se añade el estado «inservible».** La guardia sigue como en v0.4 [HV].
* **H22a (primaria): no concluyente.** El 6,0 % de las medidas marcadas eran aceptables (límite superior del IC 95 %:
  6,7 %; hacía falta ≤ 5 %).
* **H22b: no evaluable.** Solo 41 medidas con fallo grosero quedaron fuera del rojo (mínimo 100). Las 41 fueron
  marcadas.
* **H22c (control): no apoyada.** En el perfil de calibración se marcó el 5,2 % de las medidas (máximo 1 %).
* **Lo que explica el resultado [HV]:**
  * Las 93 medidas marcadas en el control eran todas fallos groseros (error ≥ 105 %), todas a t/h = 3. La regla
    no se equivocó ahí; el criterio de control suponía que en `realistic` no habría fallos groseros, y con estas
    formas a resolución gruesa sí los hay.
  * En este banco el certificado actual ya pone en rojo el 99,3 % de los fallos groseros (5609 de 5650). El problema
    que motivó H22 (fallos groseros en amarillo, como en H11) casi no aparece en sintético.

## 2. Ejecución

| Paso | Resultado |
|---|---|
| Aprobación | Cabecera del preregistro cambiada a «aprobado» en `2c5983e`, antes de medir |
| Candado (§10) | Los 11 archivos coinciden blob a blob con la rama (`h22.py` b30e41d, `h9_frozen.json` f7a91c3, `run_h22.py` 9feeec4, `domain.py` 8ca3239, `budget.py` 83ce907, `certificate.py` ab500dd, `experiment.py` da61676, `imaging.py` 2da60bf, `segment.py` 4b4ac39, `measure.py` 88853a9, `phantoms.py` b9c8b61), comprobado antes de `run` y de nuevo en la huella del manifiesto |
| Incidencia previa a `run` | Un script auxiliar de huellas añadió un salto de línea final a la copia local de `h9_frozen.json`. Se detectó al comparar con la rama, se restauró el archivo byte a byte (10 368 bytes) y se volvió a comprobar antes de medir. SHA-256 de la guardia usada: `7e5a7b2f…6a1c` |
| Barrido | Medido una sola vez: 5400 imágenes, 16 200 medidas, semilla 20262201; 672 s con 3 procesos |
| Análisis | `classify` y `verdicts` sin parámetros libres |

## 3. Veredictos

| Hipótesis | n | Estimación | Criterio | Veredicto |
|---|---|---|---|---|
| H22a (primaria): inservible casi nunca cae sobre una medida aceptable | 6745 marcadas | 6,0 % aceptables (408); IC 95 % sup. 6,7 % | sup. ≤ 5 % apoyada; > 10 % contraria | **no concluyente** |
| H22b: inservible encuentra los fallos groseros no rojos | 41 | 100 % (41 de 41) | ≥ 100 medidas; ≥ 50 % | **no evaluable** |
| H22c (control): en `realistic` casi no salta | 1800 | 5,2 % (93) | ≤ 1 % | **no apoyada** |
| Decisión (§8) | | | | **no añadir** |

Sensibilidad (solo descriptiva, no cambia nada):

| Factor | H22a | H22b | H22c |
|---|---|---|---|
| 1,5 | 8,5 % · no concluyente | 100 % · no evaluable | 11,6 % · no apoyada |
| 2 (preregistrado) | 6,0 % · no concluyente | 100 % · no evaluable | 5,2 % · no apoyada |
| 3 | 2,7 % · apoyada | 78 % · no evaluable | 3,6 % · no apoyada |

Con ningún factor se cumple el control.

## 4. Descriptivo [HV]

**Fracción marcada como inservible por perfil** (media de los tres segmentadores):

| Perfil | Inservible | Dentro de dominio |
|---|---|---|
| `noisy` | 92,9 % | 0 % |
| `us_coarse` | 71,8 % | 0 % |
| `us_atten` | 63,1 % | 2,6 % |
| `us_raw` | 46,2 % | 2,5 % |
| `us_compound` | 30,4 % | 2,9 % |
| `blurry` | 27,0 % | 0 % |
| `mild_noise` | 20,5 % | 0 % |
| `mild_blur` | 17,6 % | 19,9 % |
| `realistic` (control) | 5,2 % | 48,0 % |

* **El control.** Las 93 marcadas en `realistic` están todas a t/h = 3 y casi todas en `otsu` y `smoothed_otsu`
  sobre el alargado y el cono. 65 tenían los índices de dominio no medibles y 28 un `snr_hat` por debajo de la mitad
  de la envolvente. Su |error| de volumen fue de 105 % a 4280 % (mediana 2787 %). Ninguna era aceptable.
* **Dónde cae sobre medidas aceptables.** De las 408 aceptables marcadas, casi todas en `noisy` (8,9 % de sus
  marcadas), `us_raw` (13,2 %), `us_atten` (8,4 %) y `us_coarse` (4,1 %). En los perfiles de desenfoque y en el
  control, ninguna. Coincide con la [HIP] del §7 del preregistro: hay segmentadores que miden bien aunque el ruido o
  el moteado hundan `snr_hat`.
* **El certificado actual en este banco.** Ningún verde fue inaceptable (1010 verdes, todos con |error| ≤ 10 %). El
  rojo cubre 5609 de los 5650 fallos groseros. Los 41 restantes, en amarillo, fueron todos marcados por la regla.
* **Tabla cruzada (luz actual → estado nuevo, por banda de error):**

  | Luz actual | Estado nuevo | ≤ 10 % | 10–50 % | > 50 % |
  |---|---|---|---|---|
  | verde | verde | 1010 | 0 | 0 |
  | amarillo | amarillo | 2890 | 900 | 0 |
  | amarillo | inservible | 117 | 573 | 41 |
  | rojo | rojo | 862 | 2869 | 924 |
  | rojo | inservible | 291 | 1038 | 4685 |

* **`smoothed_otsu` con estas formas.** Queda en rojo en el 80 % de las medidas de todos los perfiles, también en
  `realistic`, con mediana de |error| de volumen del 19 %. Es una propiedad del semáforo de volumen calibrado en H6
  para las 10 formas de entonces, no de la regla nueva [HV en este banco].

## 5. Predicciones escritas de antemano (§7)

| Predicción | Probabilidad | ¿Ocurrió? |
|---|---|---|
| H22a apoyada | 55 % | No (no concluyente) |
| H22b apoyada | 40 % | No (no evaluable) |
| H22c apoyada | 85 % | **No** |
| Decisión «añadir inservible» | 25 % | No |
| Algún perfil de ecografía simulada con > 50 % inservibles | 60 % | Sí (`us_coarse` 72 %, `us_atten` 63 %) |

La predicción más segura falló, por un supuesto del diseño: que en el perfil de calibración no habría fallos
groseros. Con formas nuevas a t/h = 3, los hay.

## 6. Qué significa y qué no

* **Decisión (§8):** no se añade el estado «inservible». La guardia sigue con verde / amarillo / rojo.
* **Lectura honesta del control [HV]:** el 5,2 % que hundió H22c no son falsas alarmas: son fallos groseros que el
  semáforo de volumen dejó en amarillo o rojo y que la regla también marcó. El criterio del control estaba mal
  planteado para formas nuevas a resolución gruesa. No se cambia el veredicto: el criterio se fijó antes de medir.
* **El banco no reproduce el problema de H11 [HV]:** aquí el rojo ya captura el 99 % de los fallos groseros, y H22b no
  pudo evaluarse. Que la regla sirva o no donde importa (ecografía real, con `smoothed_otsu` en amarillo y errores de
  cientos por ciento) sigue sin contestar [PV].
* **No se puede concluir** (§9): nada sobre imágenes reales; nada fuera de estas 4 formas, 9 perfiles, 3
  segmentadores y la guardia de v0.4 con perfil declarado `realistic`; el factor 2 y los umbrales son juicios previos.
  La fracción total depende de la mezcla de perfiles elegida.

## 7. Siguiente paso [PROP, sin decidir]

* La tarea P2 queda contestada en sintético con un «no añadir». Reabrirla exigiría un preregistro nuevo, no un
  reajuste de este.
* Si se reabre, dos cambios de diseño que estos resultados sugieren, sin aplicarlos aquí:
  * un control que separe falsas alarmas (medida aceptable marcada) de alarmas correctas, en vez de contar todas las
    marcas del perfil de calibración;
  * un banco donde los fallos groseros queden de verdad fuera del rojo, por ejemplo con los perfiles de ecografía
    calibrados en H12, para que H22b sea evaluable.
* Usar los casos reales de H11 sería un estudio aparte, con su propio preregistro.
