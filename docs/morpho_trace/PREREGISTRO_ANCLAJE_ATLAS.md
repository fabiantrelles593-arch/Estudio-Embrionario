# Preregistro — MT-B: ¿la separación entre estadios es la diferencia entre los dos atlas? (23 nov 2026)

> **Aprobado por el autor el 23 nov 2026, tal como estaba escrito el borrador** (decisiones del §0: las propuestas).
> Se sube a la rama con su código (`src/geovida/atlas_anchor.py`, `scripts/mtb_anclaje.py`) y sus pruebas
> (`tests/test_mtb_anclaje.py`) **antes** de calcular cualquiera de las puertas o de los estimandos de §4.
>
> Antecedentes: MT-A v1.0, v1.1, v2 y v3, los cuatro **no evaluables**; esos veredictos no se tocan. v3 dejó
> verificado en la publicación que los landmarks publicados de cada embrión son los landmarks del atlas de su
> estadio, llevados al espécimen con un registro afín + SyN (Devine et al. 2022, sección «Image registration and
> label propagation») [HV, `PREREGISTRO_ATLAS_v3.md` §12]. Este estudio usa esa premisa y **no registra nada**.
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta · [PV] pendiente.
> Solo datos animales publicados (MusMorph/IMPC, FaceBase, CC BY 4.0, Devine et al. 2022, *Sci Data* 9:230,
> doi:10.1038/s41597-022-01338-x). Nada humano ni clínico. No hace falta descargar nada.

## 0. Decisiones del autor (23 nov 2026: se aceptan las cuatro propuestas)

| # | Decisión | Propuesta | Alternativa |
|---|---|---|---|
| D1 | ¿Se hace MT-B? | Sí: no registra, usa datos ya en disco y corre en minutos | Pasar directamente a ANTs/SyN con un preregistro de MT-A v4 (licencia y versión sin verificar [PV]) |
| D2 | ¿Se incluye el registro atlas E18.5 → atlas E15.5 que se anunció como parte de esta pregunta? | **No.** Haría falta un registro propio, y el de SimpleITK no superó a la identidad en v3; su resultado no tendría ninguna validación detrás | Incluirlo como descriptivo (C1 de v3), sin peso en el veredicto |
| D3 | Cómo entran los landmarks de los atlas en el espacio de forma | **Proyectados** sobre el espacio tangente del GPA de las 597 (§3): **d** queda exactamente como en G0-d′ de v2 | Meterlos en el GPA (599 configuraciones); queda como sensibilidad 1 |
| D4 | Incertidumbre | Remuestreo de especímenes dentro de cada estadio con las coordenadas tangentes fijas, 2000 réplicas | Rehacer el GPA en cada réplica; queda como sensibilidad 2 (200 réplicas) |

## 1. Pregunta y por qué importa

ONTO-MAP encontró que E15.5 y E18.5 quedan separados por un vector **d** (|d| = 0,157) mucho mayor que la
dispersión dentro de cada estadio a lo largo de él, y no pudo interpretarlo porque cada estadio se registró a su
propio atlas [HV, `docs/onto_map/RESULTADOS_P4.md`]. MT-A intentó medir el efecto del atlas registrando los mismos
especímenes a los dos atlas, y no pudo: el registro propio nunca reprodujo los landmarks publicados mejor que
dejar los del atlas sin mover.

Como los landmarks publicados son landmarks del atlas deformados, hay una pregunta más simple que no necesita
registrar: **¿cuánto de d es la diferencia entre las dos configuraciones de landmarks de los atlas, y cuánto
añaden los especímenes?**

En el espacio tangente se cumple, por álgebra, **d = a + e₁₈ − e₁₅**, con:

* **a** = t(A₁₈) − t(A₁₅): la diferencia entre las configuraciones de landmarks de los dos atlas;
* **e_s** = t̄_s − t(A_s): cuánto se aparta la media publicada del estadio *s* de la configuración de su atlas.

Si **d ≈ a**, la separación entre estadios de los landmarks publicados es, en lo esencial, la diferencia entre las
dos anotaciones de atlas; los especímenes no la desplazan. Si **d** se aparta mucho de **a**, los especímenes
aportan una diferencia sistemática propia.

**Lo que MT-B no puede decidir:** si **a** es biológica (los embriones cambian de forma entre E15.5 y E18.5) o
técnica (el punto *i* no se colocó en el mismo lugar anatómico en los dos atlas). Eso exige landmarks independientes
de los atlas (§9).

## 2. Datos (todos ya en disco; ninguna elección nueva)

| Elemento | Origen | Estado |
|---|---|---|
| Landmarks de los atlas | `data/external/musmorph/atlas/IMPC_E15.5_Head_Atlas_Landmarks.tag` y `…E18.5…`, 540 puntos cada uno | [HV] MD5 del catálogo comprobado en v1.0; correspondencia punto a punto superada en G0-c (v1.0) |
| Configuraciones publicadas | Las 597 del confirmatorio de v2 (`results/morpho_trace/v2/seleccion_v2.json`, `confirm`: 199 E15.5 y 398 E18.5), en `data/external/musmorph/landmarks_confirm/` | [HV] son las de **d** en G0-d′ de v2 (\|d\| = 0,15678) |

**Lo que ya se ha visto (declarado, porque condiciona las predicciones):**

* |d| = 0,15678 y ρ máxima de las 597 a su media = 0,1573 (G0-d′ de v2).
* ρ de Procrustes entre las dos configuraciones de los atlas = **0,160** (G0-c de v1.0). Es casi |d|.
* ρ entre la configuración del atlas y los landmarks publicados de especímenes concretos: medianas 0,047 (E15.5) y
  0,031 (E18.5) en los 40 de v2, y 0,0343 en los 4 del piloto de v3. Ninguno de esos especímenes está entre las 597.

Con esos números, que **d** y **a** se parezcan es probable antes de medir. Lo que falta, y lo que este estudio
aporta, es la dirección, la diferencia **d − a** con su intervalo y el reparto entre e₁₅ y e₁₈. **No se ha calculado
nunca** ninguna proyección de los atlas sobre el espacio de las 597, ni **a**, ni **e_s**, ni ningún ángulo con **d**.

## 3. Protocolo (fijo)

1. **Espacio de forma.** GPA (`geovida.landmarks.gpa`) de las 597 configuraciones publicadas, exactamente como en
   G0-d′ de v2. Media μ (‖μ‖ = 1); coordenadas tangentes con `geovida.landmarks.tangent_coordinates`.
2. **Proyección de cada atlas.** Preforma de A_s (centrada, tamaño de centroide 1), rotación sin reflexión que la
   lleva sobre μ (la misma de `gpa`) y proyección tangente v − ⟨v, μ⟩ μ. Es la operación que `gpa` aplica a cada
   espécimen en su última iteración, aplicada a una configuración que no entra en el ajuste.
3. **Medias y vectores.** t̄₁₅, t̄₁₈ = medias de las coordenadas tangentes de cada estadio; **d** = t̄₁₈ − t̄₁₅;
   **a** = t(A₁₈) − t(A₁₅); **e_s** = t̄_s − t(A_s); d̂ = d / |d|.
4. **Incertidumbre.** Remuestreo con reposición de especímenes **dentro de cada estadio** (199 y 398), 2000
   réplicas, semilla **20261124**, percentil 95 %. En cada réplica se recalculan t̄₁₅, t̄₁₈, **d**, **e_s** y los
   estimandos; las coordenadas tangentes y **a** quedan fijas (los atlas son dos configuraciones, sin muestreo).

## 4. Hipótesis y criterios (fijos)

**Estimando primario: r = |d − a| / |d| = |e₁₈ − e₁₅| / |d|**, la parte de **d** que no es la diferencia entre atlas.

* **MT-B1 (primaria) — La separación entre estadios es la diferencia entre atlas.**
  *Apoyada* si el límite superior del IC 95 % de r es **≤ 0,25**.
  *Refutada* si el límite inferior es **≥ 0,50**.
  *No concluyente* en cualquier otro caso. *No evaluable* si falla una puerta (§5).
* **MT-B2 (secundaria) — Cada estadio está anclado a su atlas.** Para cada estadio, |e_s| es menor que la mediana
  de |t(x) − t̄_s| sobre sus especímenes (la media del estadio está más cerca de su atlas que el espécimen típico
  de esa media). *Apoyada* si se cumple en los dos estadios, con el punto estimado; se informa el IC de |e_s|.
* **MT-B3 (descriptiva).** f_A = ⟨a, d̂⟩ / |d|; |a| / |d|; ángulo(a, d); |e₁₅| / |d| y |e₁₈| / |d|;
  ⟨e₁₈ − e₁₅, d̂⟩ / |d|. Todos con IC 95 %.

Un valor no calculable es «no evaluable», nunca «refutada».

## 5. Puertas (en este orden; si una falla, el estudio se para y es no evaluable)

| Puerta | Qué se comprueba | Criterio |
|---|---|---|
| **G0-d‴** Reproducción de d | GPA de las 597 con el código de este estudio | \|d\| = 0,15678 ± 0,0001 (el valor de G0-d′ de v2) |
| **G0-p** Proyección | El paso 2 de §3 aplicado a 5 de las 597 (las 5 primeras de la lista `confirm`) reproduce sus coordenadas tangentes del GPA | Diferencia máxima ≤ 1·10⁻⁸ |
| **G0-t** Validez tangente | ρ de cada configuración de atlas a μ | ≤ 0,1573 en los dos (no más lejos de μ que el espécimen más lejano de las 597) |

G0-c (correspondencia entre atlas) sigue superada desde v1.0.

## 6. Sensibilidad (declarada; no cambia el veredicto)

1. Los dos atlas **dentro** del GPA (599 configuraciones): r y f_A.
2. Remuestreo rehaciendo el GPA en cada réplica (200 réplicas, misma semilla): IC de r.
3. MT-B1 por separado con cada mitad del estadio más grande (las 398 de E18.5 partidas en dos con la semilla):
   cuánto cambia r con otra muestra del mismo tamaño que la de E15.5.

## 7. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| Pasan las tres puertas | 90 % |
| MT-B1 apoyada (r ≤ 0,25 en todo el IC) | 60 % |
| MT-B1 refutada | 10 % |
| MT-B2 apoyada en los dos estadios | 70 % |
| f_A entre 0,8 y 1,2 (punto estimado) | 65 % |

Estas probabilidades no son ciegas: salen de los números de §2. Por eso MT-B vale como cierre lógico y medida con
intervalo, no como descubrimiento.

## 8. Qué significará cada resultado (antes de verlo)

| Resultado | Conclusión | Siguiente paso |
|---|---|---|
| MT-B1 apoyada | La separación entre estadios de los landmarks publicados es, salvo un 25 % como mucho, la diferencia entre las dos configuraciones de atlas. La firma de ONTO-MAP (mucha separación, poca dispersión a lo largo de **d**) se explica por cómo se generaron los landmarks y no es por sí sola prueba de una trayectoria biológica | Buscar landmarks independientes de los atlas (anotación manual en algunos especímenes de cada estadio, publicada con licencia clara) antes de cualquier análisis de trayectorias con MusMorph; preregistro nuevo |
| MT-B1 refutada | Los especímenes desplazan la media de su estadio lejos de su atlas: **d** contiene información que no está en los atlas | La pregunta de MT-A sigue abierta; ANTs/SyN con un preregistro nuevo |
| No concluyente | La diferencia **d − a** no queda acotada | Documentar; no se amplía la muestra después de ver el resultado (**d** está fijada con las 597) |
| MT-B2 no apoyada en algún estadio | La media de ese estadio no está anclada a su atlas | Se informa; no cambia MT-B1 |
| Falla una puerta | Documentar la causa | Corregir solo si es un defecto de código, con una desviación declarada antes de calcular los estimandos |

## 9. Qué no se puede concluir

* Si **a** es biológica o técnica: con landmarks generados desde los atlas, no se puede separar con estos datos.
* Nada sobre la calidad del registro de MusMorph ni sobre ningún registro propio.
* La igualdad **d = a + e₁₈ − e₁₅** es álgebra: MT-B describe cómo se reparte **d**, no prueba una causa.
* Nada sobre la dispersión dentro de cada estadio (si el registro la reduce, aquí no se mide).
* Dos estadios transversales, solo la cabeza, solo ratón; nada sobre humanos ni uso clínico.

## 10. Ejecución

1. Código antes de medir: `src/geovida/atlas_anchor.py` (`project_to_tangent`, `anchor_decomposition`,
   `verdict_mtb1`, `verdict_mtb2`) y `scripts/mtb_anclaje.py` (puertas, estimandos, sensibilidad). Pruebas con
   configuraciones sintéticas: la proyección reproduce las coordenadas del GPA de una configuración que estaba en
   él; **d = a + e₁₈ − e₁₅** con error < 1·10⁻¹²; especímenes = atlas + ruido da r ≈ 0; especímenes desplazados
   en una dirección conocida dan el r esperado; los umbrales de veredicto se aplican bien en los bordes.
2. Subir preregistro aprobado, código y pruebas con CI verde. Después, `gates` y `analyze` (minutos).
3. Resultados en `docs/morpho_trace/RESULTADOS_ANCLAJE_ATLAS.md`, transcribiendo los veredictos sin reinterpretar.
   Resultados brutos fuera de git, en `results/morpho_trace/mtb/`.

## 11. Desviaciones

(Ninguna al subir este preregistro.)

### Notas previas a la subida (no cambian ningún criterio)

* **23 nov 2026 — sesgo del intervalo de r, visto en las pruebas sintéticas.** r es la longitud de un vector
  estimado; al remuestrear, el ruido de las medias se suma a esa longitud, así que el IC percentil de r tiende a
  quedar desplazado hacia arriba y puede no contener el punto estimado (lo mostró una prueba con 20 + 30
  configuraciones sintéticas ruidosas). Con 199 y 398 especímenes el desplazamiento esperado es pequeño [HIP], y
  va en contra de «apoyada» y a favor de «refutada». No se cambia el método aprobado (percentil, §3 paso 4); se informará
  el punto estimado junto al IC, y el desplazamiento se podrá ver comparando ambos.

### Notas de ejecución (no cambian ningún criterio)

* **23 nov 2026 — preregistro, código y pruebas en la rama** (preregistro en 838cd55; cabeza 36bc16c con CI en verde
  en Python 3.12 y 3.13). Después, `gates`: **las tres puertas superadas** (|d| = 0,156785; diferencia de proyección
  7,6·10⁻¹⁷; ρ de los atlas a la media 0,106 y 0,055) [HV, `results/morpho_trace/mtb/gates.json`]. Las 5
  configuraciones de G0-p son las 5 primeras de la lista `confirm` de E15.5, que va primero.
* **23 nov 2026 — `analyze`, sin desviaciones: MT-B1 apoyada (r = 0,200, IC 0,192–0,212) y MT-B2 apoyada**
  [HV, `results/morpho_trace/mtb/analisis.json`]. Detalles en `docs/morpho_trace/RESULTADOS_ANCLAJE_ATLAS.md`.
