# Preregistro — P3: ¿cuánto de la variación de una estructura embrionaria es técnica y cuánto es del espécimen? (MusMorph IMPC E15.5; **aprobado por el autor; piloto descargado, desviaciones D1 y D2**)

> **Estado:** aprobado por el autor el 14 nov 2026 (Fase 2). Falta, idealmente, la revisión de un asesor antes de descargar datos. El análisis de §5 está en `src/geovida/p3.py`, probado solo con fantomas.
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
| Segmentador A | Segmentaciones de MusMorph: atlas propagado por registro no lineal al espacio inicializado (rígido) de cada espécimen | Propagación [HV, script `Processing/Label_Propagation.py`]; existencia de los 1344 E15.5 en FaceBase [HV]; remuestreadas con interpolación trilineal: ver la desviación D1 (§11) |
| Segmentador B | MEMOS (UNETR, 50 estructuras del atlas KOMP2), ejecutado sobre el mismo volumen | Licencia BSD-2-Clause [HV]; se ejecuta sin 3D Slicer, en CPU, a la escala de su entrenamiento: ver la desviación D2 (§11) |
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

- Revisión de un asesor (decisión 9 de la auditoría). El autor aprobó el diseño el 14 nov 2026.
- Cuenta de FaceBase creada por el autor (el asistente no crea cuentas).
- Lista exacta de las 48 etiquetas de MusMorph E15.5 y su correspondencia con KOMP2.
- ~~Saber si MEMOS puede ejecutarse en el equipo del autor (3D Slicer; CPU o GPU).~~ Sí, en CPU y sin 3D Slicer, unos 17 minutos por espécimen con 4 núcleos (desviación D2).
- ~~Implementar y probar con fantomas, antes de descargar, el análisis de §5.~~ Hecho: `src/geovida/p3.py` y `tests/test_p3.py` (14 pruebas en verde en la CI).

## 11. Desviaciones

### D1 (15 nov 2026) — Las segmentaciones de MusMorph están interpoladas

Registrada **antes de calcular τ, `p` o cualquier medida de las hipótesis**. Solo se miró el formato de las 20 segmentaciones del piloto (`results/p3/diagnostico_segs.json`, fuera de git).

- **Hallazgo [HV].** Los `<ID>_Segs.mnc` son MINC2 en coma flotante, no mapas de etiquetas: en el piloto, entre el 28 % y el 32 % de los vóxeles con valor > 0 tienen un valor no entero. Es una mezcla de números de etiqueta en los bordes. Ejemplo: entre la etiqueta 10 y la 40, un vóxel puede valer 25, que es otra etiqueta.
- **Causa [HV].** `Processing/Label_Propagation.py` de MusMorph remuestrea el atlas de etiquetas con `mincresample -like … -transform …` sin `-nearest_neighbour` ni `-labels`, así que usa la interpolación trilineal por defecto.
- **Etiquetas válidas [HV].** Las etiquetas 1 a 48, más la 102 y la 103, tienen vóxeles exactos en los 20 especímenes (la 102, al menos 1072, y la 103, al menos 490). Los demás enteros > 48 aparecen en 1 o 2 vóxeles: son coincidencias de la interpolación y se descartan. Son 50 etiquetas, como en KOMP2. [HIP] La 102 y la 103 de MusMorph corresponden a la 49 y la 50 de KOMP2 (ventrículos izquierdo y derecho) [PV, se comprueba al cruzar con MEMOS].
- **Rejilla [HV, 2 especímenes].** La imagen y la segmentación comparten la misma rejilla (723 × 567 × 486 vóxeles, 0,027 mm, ejes alineados), así que la correspondencia vóxel a vóxel es directa.
- **Regla principal, fijada ahora (`geovida.p3_data.recover_labels`, `rule="nearest"`):**
  - Un vóxel con valor entero de una etiqueta válida conserva esa etiqueta, y 0 es fondo.
  - Un vóxel mezclado toma, entre el fondo y las etiquetas exactas de su vecindario de 26, la de valor más cercano. Con dos candidatos equivale a asignarlo a la que pesa ≥ 0,5 en la mezcla, el mismo umbral que §5.1.
  - Si no tiene ningún vecino exacto, se busca a 2 vóxeles.
  - Se cuentan los vóxeles con tres o más candidatos (asignación aproximada) y los que quedan sin candidato. En el piloto, de los vóxeles mezclados, el 68 % tiene un solo candidato a 1 vóxel, el 26 % dos, el 0,7 % tres o más y el 4,7 % ninguno (pasan a la búsqueda a 2 vóxeles).
- **Por qué esta regla [HV, sonda sintética en `tests/test_p3_data.py`].** En esferas giradas y remuestreadas, coincide con el remuestreo por vecino más cercano en el 95–96 % de los vóxeles. Solo con los enteros exactos la coincidencia es del 74–77 %, y con el redondeo simple del 57–61 %, que además crea etiquetas inexistentes. En una placa de 2 vóxeles, `nearest` conserva el 98 % del volumen y `exact` pierde alrededor del 54 %.
- **Sensibilidad (fijada ahora).** Todo §5 se repite con `rule="exact"` (los vóxeles mezclados pasan a fondo). Se informan ambas. Si el orden de las estructuras por τ discrepa (ρ de Spearman < 0,7), H-P3a y H-P3b solo se interpretan cuando las dos reglas dan el mismo veredicto.
- **Qué no cambia.** Ni la pregunta, ni las hipótesis, ni los criterios, ni el muestreo, ni las semillas. El segmentador A pasa a ser «atlas propagado + recuperación `nearest`».
- **Límite declarado.** La regla reconstruye una aproximación del remuestreo por vecino más cercano que MusMorph no hizo; no recupera la segmentación «verdadera». Los vóxeles con tres o más candidatos se asignan de forma aproximada.

### D2 (15 nov 2026) — MEMOS se ejecuta sin 3D Slicer, a la escala con la que se entrenó

Registrada **antes de calcular τ, `p` o cualquier medida de las hipótesis**, y antes de comparar MEMOS con el atlas en ningún espécimen.

- **Hallazgo [HV, Rolfe et al. 2023, doi:10.1242/bio.059698, Métodos].** MEMOS se entrenó con la versión de baja resolución de los escáneres de IMPC, de unos 250 × 250 × 400 vóxeles. El script de inferencia de SlicerMEMOS no remuestrea: pone el espaciado a 1 y aplica la red a la rejilla de entrada.
- **Escala [HV].** En el volumen de ejemplo de SlicerMEMOS (`IMPC_sample_data.nrrd`), el cuerpo, umbralizado con Otsu, ocupa 1,49 millones de vóxeles. En `IMPC_E15.5_0040` de MusMorph ocupa 10,4 millones. La razón de volumen es 7,0, es decir, un factor lineal de 1,91. Los ejes coinciden en orden (S, A, R ↔ eje 0, 1, 2 del arreglo). Por tanto, MusMorph tiene unas dos veces la resolución con la que se entrenó MEMOS.
- **Regla fijada ahora (`scripts/p3_memos.py`):**
  - La imagen nativa se reduce por promedio de bloques de 2, a ≈ 0,054 mm.
  - La intensidad se reescala como en SlicerMEMOS: mínimo y máximo a 0–255, y después `ScaleIntensityRange(-175, 250, 0, 1)`.
  - La red es la misma: UNETR, 51 salidas, 128³, con los pesos publicados. Se aplica con ventana deslizante de 128³, solapamiento 0,8 y promedio constante.
  - Solo se procesa la caja del cuerpo (Otsu, más 16 vóxeles de margen) y se acumula por franjas, para caber en 4 GB de RAM. Las pruebas comprueban que el resultado es idéntico al cálculo directo.
  - Los logits medios se amplían a la rejilla nativa (0,027 mm) con interpolación trilineal, y **después** se toma el argmax. Así se obtiene una máscara nativa sin bordes en escalera. Si se ampliaran las etiquetas por vecino más cercano, la variación técnica de las estructuras finas se inflaría, a favor de H-P3a.
- **Sin 3D Slicer.** El cálculo es el mismo que hace el módulo (configuración e hiperparámetros publicados en SlicerMEMOS, BSD-2-Clause), con código propio, MONAI 1.6 y PyTorch en CPU. Los pesos tienen licencia no declarada: se usan localmente y no se redistribuyen.
- **Comprobación 3.3 [EI].** Ni el artículo, ni el repositorio de MEMOS, ni los metadatos de MusMorph identifican los 91 escáneres de entrenamiento. MusMorph renumera los especímenes sin conservar el identificador del portal IMPC. Por tanto, según §3.3, no se excluye a nadie y se declara la limitación: el acuerdo atlas–MEMOS puede estar sobreestimado en los especímenes que coincidan.
- **Qué no cambia.** Ni la pregunta, ni las hipótesis, ni los criterios, ni el muestreo. El segmentador B pasa a ser «MEMOS a ×2, logits ampliados de forma trilineal a la rejilla nativa».
- **Límite declarado.** La máscara nativa de MEMOS se infiere a la mitad de resolución: su detalle fino es interpolado, no observado. Con el factor ×2 de §5.1, ambos segmentadores parten de máscaras nativas, pero la de MEMOS tiene menos información independiente a ×1. El exploratorio «MEMOS ejecutado otra vez sobre la imagen degradada ×2» pasa a ser a ×4 sobre la nativa.
