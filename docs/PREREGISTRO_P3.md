# Preregistro — P3: ¿cuánto de la variación de una estructura embrionaria es técnica y cuánto es del espécimen? (MusMorph IMPC E15.5; **BORRADOR, pendiente de aprobación y de datos**)

> **Estado:** borrador de Fase 2, 14 nov 2026. Requiere la aprobación del autor y, idealmente, la revisión de un asesor antes de descargar datos.
> Se escribe **antes de descargar ningún archivo de MusMorph**: no hay resultados. Solo investigación y educación; datos animales publicados, sin datos humanos.
> Base: ADR-005, `docs/estado_del_arte/FICHAS_REFERENTES.md` y `docs/estado_del_arte/MATRIZ_CAPACIDADES.md`.
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta · [PV] pendiente de validación.

## 1. Pregunta

En embriones de ratón silvestres de un mismo estadio (E15.5), una medida de una estructura segmentada (por ejemplo, su volumen) varía entre especímenes. Parte de esa variación es biológica; otra parte depende de decisiones técnicas: la resolución y el método de segmentación.

> Para cada estructura, ¿qué fracción de la variación del logaritmo del volumen se debe a la resolución (×1, ×2, ×4) y al segmentador (atlas propagado frente a MEMOS), y qué fracción se debe al espécimen? ¿Es mayor la fracción técnica en las estructuras pequeñas o delgadas que en las grandes y compactas? ¿Predice el certificado de geovida qué estructuras tienen una fracción técnica alta mejor que su simple tamaño?

La tercera pregunta es la prueba de MORPHO-TRACE con datos reales: si el certificado no supera al tamaño, no aporta (§9.6 del prompt rector).

## 2. Datos

| Elemento | Definición | Estado |
|---|---|---|
| Fuente | MusMorph, subconjunto IMPC E15.5, FaceBase 10.25550/3-HXMC | Licencia CC BY 4.0 [HV] |
| Población | Controles silvestres C57BL/6N, micro-TC con yodo, escáner Skyscan, cuerpo completo | 358 en los metadatos de MusMorph (mar 2024): 144 hembras, 165 machos, 49 sin sexo [HV] |
| Unidad experimental | **El espécimen** | — |
| Segmentador A | Segmentaciones de MusMorph: atlas propagado por registro no lineal al espacio inicializado (rígido) de cada espécimen | Propagación [HV, script `Processing/Label_Propagation.py`]; existencia por espécimen en E15.5 [PV] |
| Segmentador B | MEMOS (UNETR, 50 estructuras del atlas KOMP2), ejecutado sobre el mismo volumen | Licencia BSD-2-Clause [HV]; requiere 3D Slicer, ejecución local [PROP] |
| Estructuras | Etiquetas del atlas KOMP2 presentes en ambos segmentadores | KOMP2 tiene 50 etiquetas [HV, `KOMP2.ctbl`]; MusMorph declara 48 [HV]; cuáles faltan [PV] |
| Manifiesto | Todos los archivos descargados se registran con `python -m geovida.manifest build` antes de analizarlos | Implementado [HV] |

**Discrepancias registradas:** los metadatos listan 1344 especímenes E15.5 y el artículo 1426 [HV, ambos]; se usará la lista de los metadatos y se informará la diferencia.

## 3. Comprobaciones previas que pueden detener el estudio (sin mirar resultados)

1. **Existencia:** hay segmentación de MusMorph para al menos el 80 % de los especímenes elegidos. Si no, P3 no se evalúa con este diseño.
2. **Espacio:** las segmentaciones están en el espacio rígido del espécimen, no en el del atlas. Se comprueba con el lector MINC (afín y espaciado) y con que el volumen total de cada etiqueta **varíe** entre especímenes (coeficiente de variación > 0 en al menos el 90 % de las etiquetas). Si todas fueran idénticas, estarían en el espacio del atlas y la variación biológica no sería medible: se detiene.
3. **Fuga de datos:** MEMOS se entrenó con 91 escáneres silvestres de KOMP2 [HV]. Si se pueden identificar, se excluyen del muestreo. Si no, se declara como limitación: el acuerdo de MEMOS con el atlas puede estar sobreestimado en esos especímenes.
4. **MEMOS ejecutable:** corre sobre al menos el 90 % de los volúmenes del piloto. Si no, el factor «segmentador» se sustituye por un segundo segmentador por umbral de geovida, y esto se registra como desviación.

## 4. Muestreo (fijo)

- **Elegibles:** los silvestres con sexo conocido (309), menos los identificados en el paso 3.3.
- **Piloto:** 20 especímenes (10 hembras, 10 machos), elegidos al azar con la semilla **20261114**. Solo sirve para comprobar el flujo, los tiempos y la anchura de los intervalos. **No entra en el análisis confirmatorio.**
- **Confirmatorio:** 60 especímenes (30 + 30), disjuntos del piloto, con la misma semilla.
- **Regla de ampliación fijada de antemano:** si el piloto proyecta que con 60 especímenes la semianchura del IC 95 % de la diferencia de H-P3a superaría 0,10, el confirmatorio se amplía a 120 **antes** de descargar sus datos. No hay más ampliaciones.
- **Volumen de descarga estimado:** 80–140 volúmenes de 15–135 MB cada uno, entre 1,2 y 19 GB [EI, muestra de 25 archivos vista en FaceBase].

## 5. Diseño técnico (fijo)

Para cada espécimen *i*, estructura *s* y condición técnica *c* = (resolución *k* ∈ {1, 2, 4}) × (segmentador ∈ {A, B}), es decir, 6 condiciones:

1. **Resolución:** la máscara binaria nativa se degrada por factor *k* con el promedio de bloques de geovida (fracción de ocupación) y se umbraliza en 0,5; el vóxel pasa a *k* × 0,027 mm. Se aplica igual a ambos segmentadores. **Limitación declarada:** esto simula la pérdida de resolución de la delimitación, no una nueva adquisición ni una nueva segmentación.
2. **Medidas:** con `geovida.measure.measure_mask` sobre cada máscara:
   - primaria: logaritmo del volumen en mm³;
   - secundarias: área superficial (`area_sdf`) y número de componentes conexas b0 (conectividad 26).
3. **Fracción técnica de la estructura *s*:**
   τ_s = media_i Var_c(y_isc) / [ media_i Var_c(y_isc) + Var_i(media_c y_isc) ].
   Es decir, la varianza entre condiciones técnicas dentro de cada espécimen, frente a la varianza entre especímenes de su media. No requiere ajustar un modelo y no tiene problemas de convergencia.
4. **Sensibilidad:** modelo mixto `y ~ C(k) * C(segmentador) + (1 | espécimen)` con `statsmodels` (MixedLM), por estructura. Si discrepa de τ en el orden de las estructuras (ρ de Spearman < 0,7), se informan ambos.
5. **Intervalos:** remuestreo por espécimen, 2000 réplicas, semilla 20261115. En cada réplica se recalcula todo.
6. **Grupos de estructuras fijados antes de ver datos de especímenes:** sobre el atlas de consenso a resolución nativa se calcula, para cada estructura, la profundidad media interior en unidades del vóxel geométrico (`d_mean / h_geo`, el predictor de `geovida.budget`). Las estructuras por debajo de la mediana forman el grupo **pequeño o delgado**; las demás, el grupo **grande o compacto**. Los pares izquierda/derecha se promedian en una sola estructura para las pruebas entre estructuras, para no contar dos veces el mismo órgano.
7. **Certificado:** `geovida.budget.adequacy` sobre la máscara nativa del segmentador A de cada espécimen, con los modelos congelados de v0.4 (`segmenter="otsu"`, `profile="realistic"`). Se resume por estructura con la mediana de `p` entre especímenes. Esos modelos se calibraron con fantomas sintéticos: usarlos aquí es justamente la prueba de si transfieren. **No se recalibran.**
8. **Acuerdo entre segmentadores a resolución nativa:** Dice, HD95, ASSD y diferencia relativa de volumen (`geovida.agreement.compare_masks` y `geovida.measure.surface_distance_stats`; si alguna de estas métricas no estuviera implementada se añade con pruebas antes de descargar [PV]), elegidas siguiendo Metrics Reloaded para una segmentación semántica de estructuras de tamaño variable [PROP].

## 6. Hipótesis y criterios (fijos)

- **H-P3a — Primaria [HIP]. La fracción técnica es mayor en las estructuras pequeñas o delgadas.**
  Estadístico: Δ = mediana(τ, grupo pequeño) − mediana(τ, grupo grande).
  *Apoyada* si Δ > 0 y el límite inferior del IC 95 % > 0. *Contraria* si el límite superior < 0. *No concluyente* en el resto. *No evaluable* si quedan menos de 8 estructuras por grupo.
- **H-P3b — MORPHO-TRACE [HIP]. El certificado predice la fracción técnica mejor que el tamaño.**
  Entre estructuras, se calculan dos correlaciones de Spearman:
  - entre la mediana de `p` y τ (se espera negativa);
  - parcial, controlando el logaritmo del volumen del atlas.

  *Apoyada* si |ρ| ≥ 0,5 y el IC 95 % de la correlación parcial excluye 0 en la dirección esperada. *No apoyada* si la correlación parcial incluye 0: en ese caso el certificado no aporta nada sobre el tamaño, y MORPHO-TRACE se modifica o se descarta.
- **H-P3c — Descriptiva (sin criterio).** Acuerdo entre atlas y MEMOS por estructura (Dice, HD95, ASSD, error de volumen). Se informa, no se interpreta como validación anatómica: **ninguno de los dos segmentadores es una verdad anatómica** (el atlas es una propagación por registro y MEMOS se entrenó con esa misma propagación).
- **Exploratorio (sin criterio):** τ para área y b0; diferencias por sexo; τ calculado solo con el factor resolución o solo con el factor segmentador; MEMOS ejecutado otra vez sobre la imagen degradada ×2.

## 7. Qué se hace según el resultado (decidido de antemano)

| Resultado | Conclusión | Siguiente paso |
|---|---|---|
| H-P3a apoyada, H-P3b apoyada | La resolución y la segmentación pesan más en las estructuras finas, y el certificado lo anticipa mejor que el tamaño | Repetir en un segundo estadio o conjunto (validación externa) antes de cualquier afirmación general |
| H-P3a apoyada, H-P3b no apoyada | El fenómeno existe, pero el certificado no añade nada al tamaño | Reformular MORPHO-TRACE: la descomposición de varianza es la contribución; el certificado actual no lo es |
| H-P3a contraria o no concluyente | La fracción técnica no depende del tamaño o grosor como se esperaba | Informar el resultado negativo; revisar los supuestos de H1 y H3 sintéticas |
| Comprobaciones previas fallidas | El diseño no es aplicable a estos datos | Volver a la Fase 2 con otro conjunto (Matula 2021, CC0) |

## 8. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| Las comprobaciones previas se superan | 60 % |
| H-P3a apoyada | 70 % |
| H-P3b apoyada | 35 % |
| Dice atlas–MEMOS mediano ≥ 0,80 en las estructuras grandes | 75 % |

## 9. Qué no se puede concluir

- Nada sobre exactitud anatómica: no hay referencia manual por espécimen en este diseño.
- Nada sobre otros estadios, cepas, modalidades o especies. Y nada humano ni clínico.
- La degradación de resolución es simulada sobre máscaras: no equivale a reescanear.
- Con 60 especímenes, τ describe a esta muestra de silvestres C57BL/6N de un solo escáner; no a la población de embriones de ratón.

## 10. Pendiente antes de aprobar

- Aprobación del autor; revisión de un asesor (decisión 9 de la auditoría).
- Cuenta de FaceBase creada por el autor (el asistente no crea cuentas).
- Lista exacta de las 48 etiquetas de MusMorph E15.5 y su correspondencia con KOMP2.
- Saber si MEMOS puede ejecutarse en el equipo del autor (3D Slicer; CPU o GPU).
- Implementar y probar con fantomas, **antes de descargar**, el análisis de §5: degradación de máscaras, τ, remuestreo y grupos.

## 11. Desviaciones

(Ninguna: no hay datos.)
