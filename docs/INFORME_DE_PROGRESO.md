# Informe de progreso — Geometría de la Vida (19 nov 2026)

> Formato del prompt rector (§18 v1, §21 v2). Rama `geovida/v0.1-desde-cero` (PR #3, abierta, sin fusionar).
> Etiquetas: [HV] hecho verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta · [PV] pendiente de validación.
> Este informe **no copia veredictos**: remite al documento de resultados de cada estudio (`docs/clinico/TRAZABILIDAD.md`).

## 1. Cómo se mide el avance

No se usa un porcentaje arbitrario (§21 v2). Cada fase del roadmap (§14 v1) tiene una **puerta de aceptación**
y uno de cuatro estados:

- **Cerrada:** el entregable existe y su criterio de aceptación tiene evidencia en el repositorio.
- **Parcial:** hay entregable y evidencia, pero falta parte del criterio (por ejemplo, datos reales o comparación externa).
- **En curso:** la medición que cierra la puerta se está ejecutando.
- **No iniciada:** no hay entregable, por decisión documentada o por falta de datos.

Resumen: **3 cerradas, 7 parciales o en curso, 1 no iniciada** de 11 fases.

## 2. Estado por fase

| Fase (§14 v1) | Estado | Evidencia | Qué falta para cerrar la puerta |
|---|---|---|---|
| 0 · Auditoría total | **Cerrada** [HV] | `docs/adr/ADR-001-base-canonica-geovida.md`, `docs/adr/ADR-002-cierre-pr-codex.md` | — |
| 1 · Estado del arte | **Parcial** | `docs/estado_del_arte/FICHAS_REFERENTES.md`, `docs/estado_del_arte/MATRIZ_CAPACIDADES.md`, `docs/onto_map/REVISION_ORIGINALIDAD.md`, `docs/estado_del_arte/REVISION_SISTEMATICA_MORPHOTRACE.md` | Revisión registrada hecha en PubMed y Europe PMC; faltan Scopus/Web of Science, un segundo revisor y la comparación de herramientas de morfometría y TDA |
| 2 · Pregunta y protocolo | **Cerrada** para P3, ONTO-MAP y H11 [HV] | `docs/PREREGISTRO_P3.md`, `docs/onto_map/PROTOCOLO_ONTOMAP.md`, `docs/PREREGISTRO_H11.md` | Revisión del protocolo por un asesor externo (recomendada, no bloqueante) |
| 3 · Motor 2D | **Parcial** | `src/geovida/twod.py`, `src/geovida/real2d.py`, `src/geovida/biometry.py`; `docs/RESULTADOS_V02.md`, `docs/RESULTADOS_V08.md` | Validación con más de una imagen real (hoy n = 1, exploratorio) |
| 4 · Motor 3D | **Cerrada** en lectura, calibración, métricas y topología con fantomas [HV] | `src/geovida/measure.py` (marching cubes y área por distancia con signo), `src/geovida/topology.py`, `src/geovida/minc.py`, `src/geovida/realdata.py`; `docs/RESULTADOS.md`, `docs/RESULTADOS_V04.md` | — Comparación externa hecha: volumen, componentes y área iguales a SimpleITK 2.5.7 en 140 de 140 máscaras; χ contrastado con un método independiente; `area_sdf` con sesgo de ≈ +3 % a resolución fina (`docs/COMPARACION_REFERENCIA.md`) |
| 5 · MORPHO-TRACE | **En curso** | Certificado confirmado en sintético (`docs/RESULTADOS_V03.md`, `docs/RESULTADOS_V04.md`); P3 piloto con datos reales (`docs/p3/RESULTADOS_PILOTO.md`); P3 confirmatorio midiendo | Veredictos de H-P3a/b/c; separación técnica frente a biológica con datos reales |
| 6 · Modelado 4D | **Parcial** | `src/geovida/traj4d.py`, `src/geovida/growth.py`; `docs/RESULTADOS_V03.md` (H8) | Solo pseudo-tiempo y sintético: no hay datos longitudinales reales del mismo espécimen [HV] |
| 7 · Contexto 5D | **No iniciada** | — | Decisión: no se construye hasta tener al menos dos contextos comparables con datos reales y el factor de atlas medido (ONTO-MAP mostró que sin eso el contexto confunde) [PROP] |
| 8 · Investigación prenatal | **Parcial** | H12–H16 en simulación (`docs/RESULTADOS_V05.md` a `docs/RESULTADOS_V10.md`), REAL2D n = 1, `docs/prenatal/BIBLIOTECA_ANOMALIAS.md`, H11 cerrado con ecografía real de ratón (`docs/h11/RESULTADOS_H11.md`: primaria no evaluable, guardia apoyada); H12R en curso | Datos humanos autorizados con aprobación ética; validación con más imágenes reales |
| 9 · Validación externa y traslación | **Parcial** (solo preparación documental) | `docs/clinico/USO_PREVISTO_Y_RIESGOS.md`, `docs/clinico/PLAN_DE_VALIDACION.md`, `docs/clinico/FICHA_DEL_MODELO.md` | Especialistas externos, comité de ética, validación independiente; registro sanitario DIGEMID si hubiera uso clínico (DS 003-2020-SA: el software autónomo es dispositivo médico activo) |
| 10 · Publicación | **Parcial** | Presentación v2 (`docs/exposicion/GUION_V2.md`), 27 erratas públicas (`docs/ERRATA.md`), licencia MIT | Manuscrito, manual de reproducción completo, versión etiquetada |

Proyecto asociado **ONTO-MAP (P4): cerrado con resultado negativo** [HV] — hipótesis contrarias, factor de
confusión del atlas identificado, método no original (`docs/onto_map/RESULTADOS_P4.md`,
`docs/onto_map/REVISION_ORIGINALIDAD.md`).

## 3. Validación por niveles (§12 v1, §11.4 v2)

| Nivel | Estado |
|---|---|
| Software (pruebas, CI en Python 3.12 y 3.13) | Hecho: 742 funciones de prueba en 65 archivos; CI en verde en cada commit [HV] |
| Datos sintéticos con verdad conocida | Confirmado para el certificado de volumen y de topología [HV] |
| Datos reales animales | Piloto P3 completo; ONTO-MAP negativo; **H11 cerrado**: la guardia negó el verde a las 1188 medidas de ecografía real y, sin ella, 540 de 540 verdes habrían sido falsos; la primaria no fue evaluable. P3 confirmatorio y H12R en medición [HV] |
| Comparación externa con software de referencia | **Hecha para el motor 3D** con SimpleITK 2.5.7 y una reimplementación independiente (`docs/COMPARACION_REFERENCIA.md`) [HV] |
| Validación independiente o biológica | **No iniciada** |
| Utilidad clínica | **No iniciada**; el software no es un dispositivo médico |

## 4. Matriz de riesgos

| Riesgo | Efecto | Mitigación | Estado |
|---|---|---|---|
| Recursos de cómputo (3,9 GB de RAM, sin GPU) | Mediciones de días; competencia por memoria entre cadenas | Caché reanudable por caso (`scripts/run_h11.py`), prioridad baja, lectura corte a corte | Activo |
| Segmentaciones publicadas imperfectas (interpoladas, desplazadas) | Sesgo en cualquier medida de MusMorph | Desviaciones D1, D3 y D5 registradas antes de medir | Mitigado y documentado |
| Atlas distinto por estadio | Diferencias entre estadios que no son biológicas | No atribuir **d** al desarrollo; proponer registro de los mismos especímenes a ambos atlas | Abierto (P1) |
| Sin revisión externa | Errores de método no detectados | Preregistros, erratas públicas; buscar asesor | Abierto (P1) |
| Código con asistencia de IA | Errores sutiles | Pruebas, verificación de huellas, CI; declarado en el repositorio | Mitigado parcialmente |
| Pesos de MEMOS con licencia no declarada | No redistribuibles | Uso solo local; ninguna salida de MEMOS se publica | Mitigado |
| Cifras de salud mal citadas | Pérdida de credibilidad | Fuente por cifra en `docs/exposicion/GUION_V2.md`; errata E28 | Mitigado |
| Interpretación clínica indebida | Daño potencial | Avisos de «no clínico» en informes y presentación; ruta regulatoria explícita | Mitigado |

## 5. Próximas tareas priorizadas (§19 v2)

| Prioridad | Tarea | Dependencia | Criterio de aceptación |
|---|---|---|---|
| **P0** | Cerrar P3 confirmatorio: `scripts/p3_report.py --confirm` y documento de resultados según §7 del preregistro | Fin de la medición en curso | Veredictos transcritos sin reinterpretar; erratas si las hay |
| **P0** | ~~Cerrar H11 (v0.4)~~ hecho el 17 nov (`docs/h11/RESULTADOS_H11.md`). Queda H12R y la sensibilidad de vóxel: `scripts/h11_report.py` y documento según `docs/PREREGISTRO_H12R.md` §5 | Fin de la cadena H12R | Veredictos transcritos sin reinterpretar |
| **P2** | Estudiar si la guardia debería distinguir «fuera de dominio» de «inservible» (en H11 todo quedó en amarillo, también errores de 3000 %) | Preregistro nuevo; nunca reajustar H11 | Diseño escrito y probado en sintético antes de tocar datos reales |
| **P2** | ~~Que `run_h11.py` registre las huellas del código cuando no hay git~~ hecho el 17 nov: `geovida.provenance.code_fingerprint` (blob de git por archivo) y `compare_fingerprint`; comprobado contra la rama en `42639a8`: 106 de 108 archivos iguales, los 2 distintos eran los recién editados | — | Cumplido (`tests/test_code_fingerprint.py`) |
| **P1** | ~~Comparación externa del motor 3D~~ hecha el 17 nov con una reimplementación independiente y con SimpleITK 2.5.7 (`docs/COMPARACION_REFERENCIA.md`) | — | Cumplido |
| **P2** | Preregistrar la evaluación de Crofton como estimador de área (sesgo de `area_sdf` ≈ +3 % a resolución fina) | — | Semillas y formas nuevas, con ruido y desenfoque |
| **P1** | Medir la contribución del atlas (MORPHO-TRACE): registrar los mismos especímenes a los atlas de E15.5 y E18.5. **Preregistrado el 18 nov** (`docs/morpho_trace/PREREGISTRO_ATLAS.md`): atlas, landmarks de atlas e imágenes de ambos estadios verificados en FaceBase; primaria f = fracción de d reproducida por el cambio de atlas. **Código listo** (`src/geovida/atlas_effect.py`, `tests/test_atlas_effect.py`): con una deformación conocida de 1,4 vóxeles el registro deja 0,22 vóxeles de error (0,58 solo con la afín). **Puertas G0-d y G0-c superadas** (d = 0,156707, igual a ONTO-MAP; los 540 puntos se corresponden entre atlas, ρ = 0,160 frente a ≥ 1,454). **Atlas y las 40 imágenes descargados el 19 nov** con MD5 correcto. **MT-A v1.0 y v1.1 cerrados como no evaluables** (`docs/morpho_trace/RESULTADOS_ATLAS.md`, `docs/morpho_trace/RESULTADOS_ATLAS_v1_1.md`). En v1.1, 6 de los 20 especímenes E15.5 del piloto tienen landmarks publicados a más de 0,23 mm del tejido; E18.5, 20 de 20 bien. Siguiente propuesto: control de calidad de los landmarks de MusMorph y su efecto sobre **d** de ONTO-MAP | Preregistro nuevo | Veredicto de MT-A1 según §5 del preregistro, con las puertas G0–G2 superadas o «no evaluable» |
| **P1** | ~~Revisión sistemática registrada (PubMed + Europe PMC) para MORPHO-TRACE~~ hecha el 17 nov (`docs/estado_del_arte/REVISION_SISTEMATICA_MORPHOTRACE.md`: 155 identificados, 42 cribados, 10 incluidos). Queda: Scopus/Web of Science y un segundo revisor | Acceso a esas bases | Estrategia, fecha, criterios y flujo publicados (cumplido) |
| **P2** | Leer las guías ISUOG completas y ampliar la biblioteca de anomalías | Acceso al texto completo | Registros sin [PV] en los campos de imagen |
| **P2** | Licencias de S-BIAD441, portal IMPC y UniCoN | — | Licencia verificada o conjunto descartado |
| **P3** | Modelo contextual 5D | Fase 5 cerrada y factor de atlas medido | Preregistro |
| **P3** | Línea de topología persistente | Pregunta en la que Betti y Euler no basten | Comparación contra métricas simples |

## 6. Estado de validación de este informe

Documento de gestión: resume evidencia existente y no aporta resultados nuevos. Las rutas citadas se pueden
comprobar en el repositorio; la cifra de pruebas se contó con `grep "def test_"` el 19 nov 2026.
