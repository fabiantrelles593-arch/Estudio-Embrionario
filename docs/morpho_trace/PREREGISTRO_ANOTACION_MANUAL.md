# Preregistro — MT-D: ¿una anotación manual independiente reproduce la diferencia entre atlas en los landmarks 17–22? (24 nov 2026)

> **Aprobado por el autor el 24 nov 2026, tal como estaba escrito el borrador** (decisiones del §0: las cuatro
> propuestas). Se sube a la rama con su código (`src/geovida/manual_landmarks.py`, `scripts/mtd_anotacion.py`) y sus
> pruebas (`tests/test_mtd_anotacion.py`) **antes** de que empiece la anotación. No se ha anotado nada.
>
> Antecedentes: MT-B (`RESULTADOS_ANCLAJE_ATLAS.md`) mostró que, a lo largo de **d**, la separación entre E15.5 y
> E18.5 es la diferencia entre las configuraciones de los dos atlas MusMorph. MT-C (`RESULTADOS_HOMOLOGOS.md`) mostró
> que esto se sostiene en los 22 landmarks anatómicos (r₂₂ = 0,206, IC 0,197–0,220) y que esa diferencia se concentra
> en los landmarks 17–22 (83 % de |a₂₂|²), donde es de 4 a 8 veces la dispersión entre especímenes [HV]. Como los
> landmarks de cada espécimen se obtienen registrando su imagen al atlas de su estadio, esos datos no separan biología de
> anotación.
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta · [PV] pendiente.
> Solo datos animales publicados (MusMorph/IMPC, FaceBase, CC BY 4.0, Devine et al. 2022, *Sci Data* 9:230,
> doi:10.1038/s41597-022-01338-x). Nada humano ni clínico.

## 0. Decisiones del autor (24 nov 2026: se aceptan las cuatro propuestas)

| # | Decisión | Propuesta | Alternativa |
|---|---|---|---|
| D1 | Quién anota | **Una persona con formación en anatomía craneofacial de ratón**, que el autor designa. Se registra solo su función y su formación, nunca su nombre. Claude no coloca, corrige ni sugiere ningún landmark | Dos anotadores, lo que permite medir el error entre observadores. Duplica el trabajo |
| D2 | Definiciones de los landmarks | **Descargar** el material suplementario de Devine et al. 2022 (`41597_2022_1338_MOESM1_ESM.pdf`, PMC/Nature, CC BY 4.0), fuera de git, con su SHA-256, para leer la Tabla S2. El tamaño se informa antes de guardarlo y la descarga se para si pasa de 20 MB | El autor o el anotador obtiene la Tabla S2 por su cuenta y pasa al repositorio solo los nombres y definiciones de los landmarks usados |
| D3 | Parte B (especímenes) | **Sí**: 8 especímenes por estadio | Solo la parte A (atlas). Es más corta, pero no dice si los especímenes heredan el sesgo |
| D4 | Herramienta | **3D Slicer** (libre, licencia de tipo BSD), con volúmenes NIfTI exportados por nuestro código y puntos guardados como `.mrk.json` | Otra herramienta que el anotador ya domine, si exporta coordenadas de mundo. Exige otra prueba de importación |

## 1. Pregunta y por qué importa

Si la diferencia entre los atlas en los landmarks 17–22 es biológica, un anotador independiente que coloque esos puntos
directamente sobre las dos imágenes de atlas debería reproducirla. Si se debe a cómo se anotó uno de los atlas, la
anotación manual se apartará de los puntos de MusMorph en ese atlas, mucho más que su propio error de repetición, y la
diferencia entre atlas se reducirá.

**Pregunta MT-D.** Colocados a mano por una persona que no ve los puntos de MusMorph, ¿reproducen los landmarks 17–22
la diferencia entre atlas que encontró MT-C?

## 2. Datos (todos ya en disco)

| Elemento | Origen | Estado |
|---|---|---|
| Imágenes de atlas | `data/external/musmorph/atlas/IMPC_E1{5,8}.5_Body_Atlas.mnc` (FaceBase) | [HV] en disco |
| Landmarks de MusMorph en los atlas | `.tag` de FaceBase ya usados en MT-B y MT-C | [HV] |
| Imágenes de especímenes (parte B) | `data/external/musmorph/mta_images/`: 20 E15.5 y 20 E18.5, cada una con su `.tag` de MusMorph en `landmarks/` | [HV] en disco; los 40 emparejados |
| Que las coordenadas de los `.tag` estén en el espacio de mundo de las imágenes `.mnc` | — | [PV]: puerta G0-e |
| Definiciones de los landmarks | Tabla S2 (D2) | [PV] |

**Lo que ya se ha visto (declarado):** todo MT-B y MT-C, incluidas la dirección y el tamaño de aᵢ en cada landmark. Nada
de eso se enseña al anotador.

## 3. Protocolo de anotación (fijo)

1. **Landmarks.** Los 17–22 (objetivo) y **4 de referencia**, elegidos por regla entre el 1 y el 16: los 4 con menor
   |aᵢ| / sᵢ en `results/morpho_trace/mtc/analisis.json`. Resultado de la regla, fijado antes de subir: **10, 15, 9
   y 8** (|aᵢ| / sᵢ = 0,50; 0,76; 0,99; 0,99); suplentes, en orden, **7, 16 y 1**. El anotador puede sustituir una
   referencia que no sepa localizar por la siguiente suplente, antes de empezar y por escrito. En total, 10 landmarks.
2. **Ciego.** El anotador no ve los puntos de MusMorph, ni los resultados de MT-B/MT-C, ni ninguna superposición.
   Trabaja con las definiciones de la Tabla S2. El estadio no se puede ocultar, porque el tamaño lo delata; se declara.
3. **Parte A — atlas.** Cada atlas se anota **5 veces**, en sesiones separadas por al menos 24 h, en un orden aleatorio
   (semilla **20261126**). Cada sesión empieza desde cero, sin ver las anteriores.
4. **Parte B — especímenes (si D3).** 8 especímenes por estadio, elegidos al azar de `mta_images` con la misma semilla.
   Cada uno se anota una vez, y 2 por estadio se repiten en otra sesión para medir el error. El orden se baraja entre
   estadios, y los archivos llevan un código, no el ID del IMPC.
5. **Registro.** Por sesión: fecha, duración, landmarks que no se pudieron colocar, y nota libre. Un landmark que no
   se pueda colocar queda como ausente; no se rellena.
6. **Coste estimado:** 100 colocaciones en la parte A y 200 en la parte B; unas 6–10 h de anotación [HIP].

## 4. Análisis (fijo)

Todo en coordenadas de mundo (mm) del atlas o espécimen correspondiente; sin registro entre imágenes.

1. **Posición manual** de cada landmark: media de las repeticiones, mᵢ. **Error de repetición** εᵢ: raíz de la media
   de |repetición − mᵢ|².
2. **Discrepancia con MusMorph** en cada atlas: δᵢ = |mᵢ − Mᵢ| en mm, y δᵢ / εᵢ.
3. **Diferencia entre atlas con puntos manuales.** En cada configuración de atlas de 22 filas se sustituyen las filas
   17–22 por las posiciones manuales (las filas 1–16 son las de MusMorph). Se proyecta sobre el espacio tangente de
   MT-C (mismo GPA de las 597 y misma media), con las funciones de `geovida.atlas_anchor` sin cambios, y se obtiene
   **a**ᵐᵃⁿ. Se calculan:
   * **q** = ⟨aᵐᵃⁿ₁₇₋₂₂, a₁₇₋₂₂⟩ / |a₁₇₋₂₂|²: la parte de la diferencia de MusMorph en los landmarks 17–22 que la
     anotación manual reproduce (1 = toda; 0 = nada).
   * rᵐᵃⁿ = |d₂₂ − aᵐᵃⁿ| / |d₂₂|, para comparar con el r₂₂ = 0,206 de MT-C.
4. **Incertidumbre:** solo error de anotación. En cada réplica, para cada atlas y landmark, se remuestrean con
   reemplazo sus 5 repeticiones y se recalcula la media. 2000 réplicas, semilla 20261126, percentil 95 %. **No incluye
   la variación entre anotadores** (§9).
5. **Parte B.** Para cada espécimen y landmark, el vector manual − MusMorph. Por estadio, la media de esos vectores
   en los landmarks 17–22 y su ángulo con el vector manual − MusMorph del atlas de ese estadio (descriptivo).

## 5. Hipótesis y criterios (fijos)

* **MT-D1 (primaria) — la anotación manual reproduce la diferencia entre atlas en 17–22.**
  *Reproducida* si el IC 95 % de q está entero en [0,75; 1,25]. *No reproducida* si el límite superior es ≤ 0,50.
  *No concluyente* en otro caso.
* **MT-D2 (secundaria) — con los puntos manuales sigue habiendo d ≈ a.** Criterio de MT-B1 sobre rᵐᵃⁿ: apoyada si el
  límite superior ≤ 0,25; refutada si el inferior ≥ 0,50.
* **MT-D3 (descriptiva).** δᵢ, εᵢ y δᵢ / εᵢ por landmark y atlas; en qué atlas se concentra la discrepancia; parte B
  (§4.5).

## 6. Puertas (en este orden; si una falla, el estudio se para y es no evaluable)

| Puerta | Qué se comprueba | Criterio |
|---|---|---|
| **G0-e** Espacio común (antes de anotar) | Los 22 puntos de MusMorph de cada atlas caen dentro de los límites de su `.mnc`, en vóxeles por encima del umbral de Otsu de la imagen | Los 22 en los dos atlas |
| **G0-c** Cadena de coordenadas (antes de anotar) | El anotador coloca 3 puntos en el centro de 3 esferas sintéticas de posición conocida, exportadas con la misma cadena NIfTI → Slicer → `.mrk.json` → importación | Error ≤ 1 vóxel en las 3 |
| **G0-ε** Precisión (después de la parte A) | En cada landmark objetivo, error de repetición proyectado al espacio tangente frente a la diferencia de MusMorph en ese landmark | εᵢ ≤ 0,5 · \|aᵢ\| en los 6 landmarks de los dos atlas |
| **G0-r** Referencias (después de la parte A) | Las 4 referencias manuales coinciden con MusMorph | Mediana de δ / ε en las referencias ≤ 3 en cada atlas |

G0-r comprueba que el marco de coordenadas y las definiciones coinciden. Si las referencias tampoco coinciden, una
discrepancia en 17–22 no se podría atribuir a esos landmarks.

## 7. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| Pasan las cuatro puertas | 60 % |
| MT-D1 reproducida | 40 % |
| MT-D1 no reproducida | 30 % |
| Si no se reproduce, la discrepancia se concentra en un solo atlas | 65 % |

La primera es baja porque G0-ε exige una precisión que depende del anotador y de lo visibles que sean estos puntos en
imágenes de embrión [HIP].

## 8. Qué significará cada resultado (antes de verlo)

| Resultado | Conclusión | Siguiente paso |
|---|---|---|
| Reproducida | Un anotador independiente encuentra la misma diferencia entre atlas en 17–22: es compatible con un cambio biológico en esa región entre E15.5 y E18.5 | Un segundo anotador para medir la variación entre observadores, antes de interpretarlo como biología |
| No reproducida | La diferencia entre atlas en 17–22 depende de cómo se colocaron esos puntos en los atlas de MusMorph: **d** a lo largo de **a** es, en buena parte, técnica | Repetir el análisis de ONTO-MAP excluyendo los landmarks 17–22 o con los puntos manuales (preregistro nuevo) |
| No concluyente | La anotación manual no acota q | Documentar; valorar más repeticiones o un segundo anotador |
| Falla G0-e o G0-c | Problema de espacio o de importación, no de anatomía | Corregir la cadena y repetir la puerta antes de anotar |
| Falla G0-ε o G0-r | La anotación no es lo bastante precisa, o las definiciones no coinciden | No se interpreta; se pide al autor decidir |

## 9. Qué no se puede concluir

* Con un solo anotador, nada sobre la variación entre observadores. El intervalo de q solo recoge el error de
  repetición de esa persona.
* Que la anotación manual sea "la verdad": es una segunda lectura independiente, no una referencia de oro.
* Nada sobre los landmarks 1–16, salvo las 4 referencias.
* Dos estadios, solo la cabeza, solo ratón; nada sobre humanos ni uso clínico.

## 10. Ejecución

1. Código antes de anotar:
   * `src/geovida/manual_landmarks.py`: lectura de `.mrk.json` con su convención de coordenadas (LPS/RAS), exportación
     a NIfTI conservando la matriz de mundo del `.mnc`, esferas sintéticas para G0-c, y las funciones de §4.
   * `scripts/mtd_anotacion.py` con las órdenes `prepare`, `gates-pre`, `gates-post` y `analyze`. `prepare` exporta los
     volúmenes, elige referencias y especímenes y escribe el manifiesto con el orden de las sesiones.
   * Pruebas con datos sintéticos: ida y vuelta de coordenadas, cambio de convención que se detecta, q = 1 cuando los
     puntos manuales son los de MusMorph, y q ≈ 0 cuando los dos atlas reciben los mismos puntos en 17–22 (con
     tolerancia declarada en la prueba, porque la rotación de Procrustes acopla los landmarks).
2. Si D2 se aprueba: descarga del PDF con su tamaño y SHA-256, fuera de git.
3. Subir el preregistro aprobado, el código y las pruebas con CI verde. Después, `prepare` y `gates-pre`.
4. Anotación por la persona de D1. Los archivos de puntos quedan fuera de git (`data/manual/mtd/`), con su SHA-256 en
   el informe.
5. `gates-post` y `analyze`. Resultados en `docs/morpho_trace/RESULTADOS_ANOTACION_MANUAL.md`; brutos fuera de git en
   `results/morpho_trace/mtd/`.

## 11. Desviaciones

(Ninguna al subir este preregistro.)

### Notas previas a la subida (no cambian ningún criterio)

* **24 nov 2026 — D2 detenida por tamaño.** El PDF suplementario
  (`static-content.springer.com/esm/art%3A10.1038%2Fs41597-022-01338-x/MediaObjects/41597_2022_1338_MOESM1_ESM.pdf`)
  declara 21 522 603 B (unos 21,5 MB) en la cabecera HTTP, por encima del límite de 20 MB aprobado en D2. **No se
  descargó.** Las definiciones de los landmarks quedan [PV]: o el autor amplía el límite, o se aplica la alternativa de
  D2 (el anotador obtiene la Tabla S2 por su cuenta). La anotación no puede empezar sin ellas.
* **Detalles de implementación** (fijados en el código antes de anotar):
  * Los volúmenes se recortan a la caja de los 540 puntos de MusMorph de cada imagen, ampliada 2 mm por lado, sin
    cambiar la geometría del mundo. La caja no señala dónde están los landmarks 17–22.
  * El umbral de Otsu de G0-e se calcula sobre una submuestra de la imagen entera (1 de cada 4 vóxeles por eje), y la
    intensidad de cada punto se lee en su vóxel más cercano a resolución completa.
  * Se considera que los `.tag` y la afín de nibabel comparten el mundo RAS, y que Slicer guarda en LPS o RAS según
    declare el archivo. G0-c y G0-r comprueban esa cadena de extremo a extremo.
  * En el fantoma de G0-c, las esferas se marcan como `L1` (pequeña), `L2` (mediana) y `L3` (grande).
  * Un landmark objetivo con menos de 3 repeticiones válidas en un atlas hace que MT-D1 y MT-D2 sean no evaluables.
  * En la parte B, cada espécimen se lleva al marco del atlas con la rotación de Kabsch entre sus 22 landmarks de
    MusMorph y los del atlas. Es un ajuste de landmarks, no un registro de imágenes.
  * Plan de sesiones: en cada una de las sesiones 1–5, una repetición de cada atlas. Los 16 especímenes se reparten
    entre las sesiones 1–4 (4 por sesión) y sus 4 repeticiones van a la sesión 5. El orden dentro de cada sesión es
    aleatorio (semilla 20261126).
* **Observación sobre G0-r (sin cambio).** El criterio usa δ / ε. Con un anotador muy preciso (ε muy pequeño),
  diferencias pequeñas en mm darían un cociente alto y G0-r podría fallar. Se deja como se aprobó. Si el autor quiere
  modificarlo, debe hacerlo antes de que empiece la anotación y quedará registrado como desviación.

### Notas de ejecución

* **24 nov 2026 — preregistro, código y pruebas en la rama** (preregistro en fa6692f; código en 2f8c269 y f9814af;
  pruebas en 781556b, con CI en verde en Python 3.12 y 3.13). Nadie ha anotado nada.
* **24 nov 2026 — `prepare`.** Referencias 10, 15, 9 y 8 (suplentes 7, 16 y 1), como se fijaron en §3.1.
  Especímenes de la parte B:
  * E15.5: 0020, 0429, 0434, 0480, 0845, 0864, 1185 y 1212 (se repiten 0480 y 0864).
  * E18.5: 0477, 0727, 1287, 1340, 1546, 1561, 1569 y 1793 (se repiten 0727 y 1340).

  Se escribieron 18 volúmenes y el fantoma en `data/manual/mtd/volumes/` (unos 1 GB, fuera de git), la hoja de sesiones
  y el manifiesto [HV, `results/morpho_trace/mtd/manifest.json`].
* **24 nov 2026 — `gates-pre`: G0-e no superada; G0-c pendiente** (falta la anotación del fantoma)
  [HV, `results/morpho_trace/mtd/gates_pre.json`].
  * E15.5: los 22 puntos dentro de la imagen y por encima de Otsu.
  * E18.5: los 22 dentro de la imagen, pero solo 12 por encima de Otsu. Fallan los landmarks 1, 2, 4, 5, 7, 10, 12, 16,
    18 y 21.

  Diagnóstico descriptivo, que no cambia la puerta [HV, `results/morpho_trace/mtd/g0e_diagnostico.json`]: los 10 están
  exactamente a 1 vóxel (0,054 mm) del vóxel sobre Otsu más cercano. Es decir, están en la superficie del tejido, no
  fuera del espacio de la imagen. Ya se conocía con los 540 puntos: G0-b de ONTO-MAP dio un 58 % sobre Otsu en el atlas
  E18.5, y se sustituyó por G0-b′ (distancia ≤ 0,23 mm), que superaron los dos atlas (`results/morpho_trace/g0b.json`
  y `g0b2.json`). Al redactar G0-e no se tuvo en cuenta; es un fallo de diseño de la puerta.

  **Según §6, el estudio queda parado en G0-e.** Seguir exige que el autor apruebe una enmienda a G0-e, que quedaría
  registrada como desviación decidida después de ver la puerta y antes de cualquier anotación.
