# H21 — Resultados: Crofton frente a `area_sdf` en máscaras segmentadas de formas nuevas

> Aplica `docs/h21/PREREGISTRO_H21.md` (v1.0, aprobado el 21 nov 2026) sin desviaciones. Los veredictos son los del
> código preregistrado (`geovida.h21.verdicts`), transcritos sin cambios. Las cifras salen de
> `scripts/run_h21.py analyze` sobre `results/h21/` (fuera de git). Solo datos sintéticos con verdad analítica.
> Etiquetas: [HV] hecho verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta · [PV] pendiente.

## 1. Resumen

* **Decisión del §8: se mantiene `area_sdf`** como estimador principal de área [HV].
* **H21a (primaria): no concluyente.** A resolución fina, Crofton fue más exacto en 28 de 84 celdas evaluables
  (33 %; hacía falta ≥ 75 %).
* **H21b: no evaluable.** A resolución gruesa solo 64 de 144 celdas fueron evaluables (mínimo 72). En esas 64,
  Crofton quedó a ≤ 2 puntos de `area_sdf` en el 89 % (el umbral era 90 %), pero sin veredicto.
* **H21c (secundaria): no concluyente.** Con anisotropía 2, Crofton ganó en el 50 % de 121 celdas.
* **Lo que explica el resultado [HV]:** Crofton gana en las formas lisas y pierde en las de borde vivo. Con ruido
  fuerte y segmentadores sin suavizado, sobreestima el área un 60–90 %.

## 2. Ejecución

| Paso | Resultado |
|---|---|
| Candado (§10) | Los 8 archivos que producen la medida (`h21.py`, `phantoms.py`, `experiment.py`, `reference.py`, `imaging.py`, `segment.py`, `measure.py`, `run_h21.py`) coinciden blob a blob con la rama en `6448e40`, comprobado antes de `run` |
| Barrido | Medido una sola vez: 8000 imágenes, 24 000 filas, semilla 20262101; 1496 s en un proceso |
| Análisis | 480 celdas; ningún parámetro libre |

## 3. Veredictos

| Hipótesis | Celdas | Evaluables | Estimación | Criterio | Veredicto |
|---|---|---|---|---|---|
| H21a (primaria): Crofton más exacto, t/h 8–12, anisotropía 1 | 96 | 84 | 33,3 % de celdas con Crofton mejor | ≥ 75 % apoyada; ≤ 25 % contraria | **no concluyente** |
| H21b: Crofton no peor en más de 2 puntos, t/h 3–6 | 144 | 64 | 89,1 % no inferior | ≥ 72 evaluables; ≥ 90 % | **no evaluable** |
| H21c: como H21a con anisotropía 2, t/h 6–12 | 144 | 121 | 50,4 % | como H21a | **no concluyente** |

Mediana entre celdas evaluables de |error| [HV]:

| Resolución | `area_sdf` | Crofton | `area_mc` |
|---|---|---|---|
| Fina (t/h 8–12) | 3,2 % | 3,1 % | 7,9 % |
| Gruesa (t/h 3–6) | 7,4 % | 5,9 % | 24,7 % |

En el conjunto de celdas, los dos estimadores tienen un error típico parecido. Lo que cambia es **dónde** falla
cada uno.

## 4. Dónde gana y dónde pierde Crofton (resolución fina, celdas evaluables) [HV]

| Por forma | Crofton mejor | | Por perfil | Crofton mejor | | Por segmentador | Crofton mejor |
|---|---|---|---|---|---|---|---|
| alargado | 13 de 21 | | `ideal` | 9 de 24 | | `global` | 4 de 28 |
| herradura | 13 de 21 | | `realistic` | 12 de 24 | | `otsu` | 9 de 24 |
| cono | 2 de 21 | | `noisy` | 4 de 16 | | `smoothed_otsu` | 15 de 32 |
| media bola | 0 de 21 | | `us_compound` | 3 de 20 | | | |

* **Formas con borde vivo.** En la media bola y el cono, Crofton pierde casi siempre (2 de 42 celdas).
  * En la media bola infraestima más que `area_sdf`: medianas entre celdas de −2,2 % y −0,8 %.
  * En el cono los dos infraestiman lo mismo en mediana (−4,6 % y −4,7 %), pero Crofton queda por detrás en 19 de
    21 celdas.
  * Es coherente con el sesgo en caras planas visto antes de medir (§3 del preregistro), que la rotación al azar no
    elimina del todo [EI: no se separó el efecto de la orientación del de las aristas].
* **Ruido fuerte sin suavizado.** Mediana del error con signo a resolución fina [HV]:

  | Perfil · segmentador | `area_sdf` | Crofton |
  |---|---|---|
  | `noisy` · `global` | +3,0 % | +90,0 % |
  | `us_compound` · `global` | +32,7 % | +71,5 % |
  | `us_compound` · `otsu` | +17,3 % | +63,9 % |
  | `noisy` · `smoothed_otsu` | +1,1 % | −1,0 % |
  | `us_compound` · `smoothed_otsu` | +1,1 % | −0,6 % |

  Crofton cuenta cada transición objeto/fondo, así que los islotes y huecos de ruido suman área. `area_sdf` los
  atenúa con su suavizado. Se confirma la [HIP] del §1 del preregistro. Con `smoothed_otsu`, los dos quedan a ~1 %.
* **Imagen ideal.** En el simulador, `area_sdf` no muestra aquí el +3 % de las máscaras ideales de
  `docs/COMPARACION_REFERENCIA.md` (+1,0 % a t/h = 12; Crofton −1,2 %). Allí la máscara se obtenía por el centro del
  vóxel; aquí, umbralizando una imagen con volumen parcial. El sesgo de `area_sdf` depende de cómo se forma la
  máscara [HV en estos dos bancos].
* **Celdas no evaluables a resolución fina (12 de 96):** `otsu` sobre `noisy`, con error de volumen de +28 % a
  +1010 % (el umbral se va al ruido), y `global` sobre `us_compound` a t/h = 8 (−21 % a −24 %).

## 5. Predicciones escritas de antemano (§7)

| Predicción | Probabilidad | ¿Ocurrió? |
|---|---|---|
| H21a apoyada | 35 % | No |
| H21a contraria | 20 % | No |
| H21b apoyada | 45 % | No (no evaluable) |
| H21c con el mismo veredicto que H21a | 60 % | Sí (las dos no concluyentes) |
| En `ideal`, Crofton gana en ≥ 75 % de las celdas finas evaluables | 75 % | **No** (9 de 24, 38 %) |
| Decisión «cambiar a Crofton» | 25 % | No |

La predicción más segura falló. Esperaba que en imagen ideal se repitiera la ventaja de la comparación de referencia,
y no ocurrió: con estas formas y máscaras umbralizadas, `area_sdf` ya está cerca de la verdad.

## 6. Qué significa y qué no

* **Decisión (§8):** se mantiene `area_sdf`. Su sesgo a resolución fina sigue documentado, y aquí resulta menor
  (~1 %) en máscaras umbralizadas de imagen ideal.
* **Hallazgo útil [HV]:** con ruido o granulado y segmentadores sin suavizado, Crofton no sirve como estimador de área
  (+60–90 %). Ese es el caso realista que importa en ecografía.
* **No se puede concluir** (§9): nada sobre imágenes reales; nada fuera de estas 4 formas, 4 perfiles y 3
  segmentadores; los umbrales (20 %, 0,75, 0,25, 0,90 y 2 puntos) son juicios previos.
* **Límite del diseño:** el criterio de celda evaluable dejó fuera más de la mitad de las celdas gruesas, sobre todo con
  `noisy` y `us_compound`, y H21b no pudo decidir. Se informa tal cual; no se cambia ahora.

## 7. Siguiente paso [PROP, sin decidir]

* Ninguno sobre el estimador principal: la pregunta queda contestada para este banco.
* Si se quisiera insistir en Crofton, haría falta un preregistro nuevo con más direcciones (p. ej. 49) o con una
  máscara suavizada antes de contar transiciones. Hoy no hay motivo práctico, porque `area_sdf` no pierde.
