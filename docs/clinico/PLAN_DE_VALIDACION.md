# Plan de validación (borrador de ingeniería)

> Borrador del equipo del proyecto. **No es un protocolo aprobado** ni sustituye a un comité de ética,
> a un grupo clínico ni a asesoría regulatoria. Describe qué evidencia hay, qué falta y en qué orden
> conseguirla. Cada criterio de aceptación se fija **antes** de ver los datos de la etapa
> correspondiente, como se ha hecho en todos los preregistros del repositorio.

## 1. Marco: los tres pilares de IMDRF/SaMD N41 y lo que hay en cada uno

| Pilar | Pregunta | Evidencia disponible hoy | Qué falta |
|---|---|---|---|
| 1. Asociación clínica válida | ¿Importa clínicamente medir volumen y topología de embriones y fetos, y saber cuánto fiarse de la medida? | Revisión de antecedentes (`ANTECEDENTES_V04.md`). Es una revisión del equipo, **no** una revisión sistemática | Revisión sistemática formal con un clínico; relación entre error de medida y decisión clínica (no establecida) |
| 2. Validación analítica | ¿El software mide, de forma correcta, fiable y reproducible, lo que dice medir? | Fantomas de verdad exacta; error de volumen y topología frente a `t/h` (H1, H3); semáforo de volumen (H6); semáforo de topología y guardia de dominio (H9, H10); ecografía simulada (H12). Todo con criterios preregistrados y errores propios documentados | **Imágenes reales con referencia** (H11); calibración con datos reales validada por embrión (H13); comparación con otra herramienta (O4); repetibilidad entre equipos |
| 3. Validación clínica | ¿Usarlo produce un resultado clínicamente significativo en la población prevista? | Ninguna | Todo. Exige estudio con grupo clínico, comité de ética y, en su caso, autoridad competente |

**Lectura honesta:** el proyecto tiene una parte del pilar 2 con datos sintéticos y está empezando la
parte real. Los pilares 1 y 3 no están cubiertos.

## 2. Etapas con puertas de decisión

(Detalle en `docs/OBJETIVOS_V05.md` §4. Aquí se añaden los criterios de aceptación propuestos.)

| Etapa | Material | Criterio de aceptación (fijado antes de abrir los datos) | Qué NO se afirma al cumplirla |
|---|---|---|---|
| 0. Sintético | Fantomas 2D/3D/4D | Hecho (H1–H10) | Nada sobre imágenes reales |
| 0b. Ecografía simulada | Simulador de moteado y atenuación | H12 (`PREREGISTRO_H12.md`); primaria: H12c | Que funciona en ecografía real |
| 1. Ecografía 3D de ratón real | Conjunto público con contornos de expertos | H11b: verde falso ≤ 10 % (tolerancia 10 %) con ≥ 30 verdes y ≥ 15 embriones; intervalo por embrión | Nada sobre humanos |
| 2. Calibración con datos reales | Mismo conjunto, validación dejando un embrión fuera | H13 (por preregistrar antes de abrir los datos) | Generalidad entre equipos o especies |
| 3. Otras especies y modalidades | Pez cebra, rata, micro-CT con verdad de mayor resolución | Al menos un conjunto independiente del de la etapa 1 | Generalidad en humanos |
| 4. Ecografía humana retrospectiva | **Solo** con las condiciones de `DATOS_REALES_Y_ETICA.md` §3 | Todas las condiciones por escrito + asesor clínico + comité de ética | Cualquier afirmación sobre la salud de una persona o un feto |
| 5. Estudio prospectivo y regulatorio | Diseño con grupo clínico | Aprobación del comité y de la autoridad competente | — |

## 3. Reglas de validación que ya se aplican (y deben mantenerse)

1. **Preregistro antes de los datos**: criterios, tolerancias y predicciones con probabilidad se
   confirman en git antes de correr o abrir nada (`PREREGISTRO_*.md`).
2. **Congelar antes de confirmar**: ningún modelo, envolvente ni umbral se reajusta tras ver los
   resultados; las ideas de mejora van a una versión nueva con su preregistro.
3. **Unidad de análisis correcta**: la realización o el embrión, nunca el vóxel ni el corte;
   intervalos por remuestreo de embriones (H11).
4. **«No evaluable» no es «no apoyada»**: lo que no se puede calcular se dice.
5. **Se publican los fallos**: erratas propias (`ERRATA.md`), hipótesis no apoyadas y huecos
   observados («Lo que hay que leer con cuidado» en `RESULTADOS_V04.md`).
6. **Procedencia**: cada barrido guarda el commit, si el código estaba limpio, las semillas y las
   versiones de las dependencias; cada certificado puede acompañarse de un informe con huellas
   SHA-256 de la imagen y de la calibración.

## 4. Cobertura de las listas de comunicación (TRIPOD+AI y CLAIM)

Mapeo **temático**, escrito de memoria de lo que cubren esas guías. **Antes de cualquier envío a una
revista hay que contrastarlo ítem por ítem con la lista oficial vigente.**

| Tema | Dónde está en el repositorio | Estado |
|---|---|---|
| Título y resumen que dicen que es un modelo y qué predice | `README.md`, `RESULTADOS_V04.md` | Parcial |
| Objetivo, población, uso previsto | `USO_PREVISTO_Y_RIESGOS.md`, `OBJETIVOS_V05.md` | Hecho en borrador |
| Origen de los datos, fechas, criterios de inclusión | Simulador, semillas y manifiestos (sintético); `PREREGISTRO_H11.md` §2 (real) | Sintético: hecho; real: pendiente |
| Referencia («verdad») y su variabilidad | Verdad analítica de los fantomas; H11: contorno humano con su propio error | Real: pendiente |
| Tamaño de muestra y unidad de análisis | Preregistros (réplicas por celda; embrión como unidad en H11) | Hecho en los preregistros |
| Datos faltantes | Regla «no evaluable»; variable no medible = p = 0 | Hecho |
| Desarrollo del modelo | `METODOS.md`, `h6.py`, `h9.py`, `h12.py` | Hecho |
| Validación interna y externa | Dejar una forma fuera; semillas nuevas; formas nunca vistas; dominio desplazado | Interna: hecha; **externa real: pendiente** |
| Métricas: discriminación, calibración, verdes falsos | AUC, ECE, verde falso con intervalo de Wilson | Hecho |
| Equidad / subgrupos | Estratos por segmentador, perfil y forma | Parcial (no hay subgrupos demográficos: no hay personas) |
| Disponibilidad de código, datos y modelo | Repositorio público; modelos congelados versionados; datos sintéticos regenerables | Hecho (los datos reales no se redistribuyen) |
| Limitaciones | `RESULTADOS_V04.md` «Lo que hay que leer con cuidado», `ERRATA.md` | Hecho |

## 5. Camino regulatorio y ético (qué se sabe y qué no)

* **Clasificación.** Según el DS 003-2020-SA, **la hace el fabricante** con el Anexo 1. No se afirma
  aquí ninguna clase: depende del uso previsto definitivo y del daño que un error podría causar.
  Una propuesta preliminar de clase de seguridad del software (IEC 62304) está en `CICLO_DE_VIDA.md`.
* **Requisitos que no se encontraron.** El texto revisado no permitió confirmar los requisitos de
  sistema de calidad ni la lista de documentos administrativos. Se piden a un asesor regulatorio.
* **Investigación con personas.** Declaración de Helsinki, consentimiento informado, anonimización
  completa, base legal para el tratamiento de datos y aprobación de un comité de ética **antes** de
  cualquier imagen humana (`DATOS_REALES_Y_ETICA.md` §3). Las imágenes no se guardan en el repositorio.
* **Quién tiene que intervenir:** un asesor regulatorio, un grupo clínico (obstetricia/ecografía fetal
  o la especialidad que corresponda), un comité de ética y, si hay uso clínico, la autoridad competente.

## 6. Cronograma de decisiones (sin fechas inventadas)

| Orden | Decisión | Depende de |
|---|---|---|
| 1 | ¿H11 se puede evaluar? | Que alguien entregue los volúmenes reales |
| 2 | ¿La guardia rechaza la ecografía real? Si sí → H13 con datos reales | Resultado de H11 |
| 3 | ¿Conviene una herramienta de comparación existente (O4)? | Elegir una herramienta con licencia que permita compararla |
| 4 | ¿Se abre la etapa 4? | Asesor clínico + comité de ética + condiciones por escrito |
