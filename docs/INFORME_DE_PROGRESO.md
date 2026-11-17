# Informe de progreso — Geometría de la Vida (16 nov 2026)

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
| 1 · Estado del arte | **Parcial** | `docs/estado_del_arte/FICHAS_REFERENTES.md`, `docs/estado_del_arte/MATRIZ_CAPACIDADES.md`, `docs/onto_map/REVISION_ORIGINALIDAD.md` | Revisión sistemática con estrategia registrada; comparación de herramientas de morfometría y TDA |
| 2 · Pregunta y protocolo | **Cerrada** para P3, ONTO-MAP y H11 [HV] | `docs/PREREGISTRO_P3.md`, `docs/onto_map/PROTOCOLO_ONTOMAP.md`, `docs/PREREGISTRO_H11.md` | Revisión del protocolo por un asesor externo (recomendada, no bloqueante) |
| 3 · Motor 2D | **Parcial** | `src/geovida/twod.py`, `src/geovida/real2d.py`, `src/geovida/biometry.py`; `docs/RESULTADOS_V02.md`, `docs/RESULTADOS_V08.md` | Validación con más de una imagen real (hoy n = 1, exploratorio) |
| 4 · Motor 3D | **Cerrada** en lectura, calibración, métricas y topología con fantomas [HV] | `src/geovida/measure.py` (marching cubes y área por distancia con signo), `src/geovida/topology.py`, `src/geovida/minc.py`, `src/geovida/realdata.py`; `docs/RESULTADOS.md`, `docs/RESULTADOS_V04.md` | Comparación externa con una implementación de referencia (3D Slicer, ITK o SimpleITK) sobre los mismos volúmenes [PV] |
| 5 · MORPHO-TRACE | **En curso** | Certificado confirmado en sintético (`docs/RESULTADOS_V03.md`, `docs/RESULTADOS_V04.md`); P3 piloto con datos reales (`docs/p3/RESULTADOS_PILOTO.md`); P3 confirmatorio midiendo | Veredictos de H-P3a/b/c; separación técnica frente a biológica con datos reales |
| 6 · Modelado 4D | **Parcial** | `src/geovida/traj4d.py`, `src/geovida/growth.py`; `docs/RESULTADOS_V03.md` (H8) | Solo pseudo-tiempo y sintético: no hay datos longitudinales reales del mismo espécimen [HV] |
| 7 · Contexto 5D | **No iniciada** | — | Decisión: no se construye hasta tener al menos dos contextos comparables con datos reales y el factor de atlas medido (ONTO-MAP mostró que sin eso el contexto confunde) [PROP] |
| 8 · Investigación prenatal | **Parcial** | H12–H16 en simulación (`docs/RESULTADOS_V05.md` a `docs/RESULTADOS_V10.md`), REAL2D n = 1, `docs/prenatal/BIBLIOTECA_ANOMALIAS.md`, H11 en curso | Datos humanos autorizados con aprobación ética; validación con más imágenes reales |
| 9 · Validación externa y traslación | **Parcial** (solo preparación documental) | `docs/clinico/USO_PREVISTO_Y_RIESGOS.md`, `docs/clinico/PLAN_DE_VALIDACION.md`, `docs/clinico/FICHA_DEL_MODELO.md` | Especialistas externos, comité de ética, validación independiente; registro sanitario DIGEMID si hubiera uso clínico (DS 003-2020-SA: el software autónomo es dispositivo médico activo) |
| 10 · Publicación | **Parcial** | Presentación v2 (`docs/exposicion/GUION_V2.md`), 27 erratas públicas (`docs/ERRATA.md`), licencia MIT | Manuscrito, manual de reproducción completo, versión etiquetada |

Proyecto asociado **ONTO-MAP (P4): cerrado con resultado negativo** [HV] — hipótesis contrarias, factor de
confusión del atlas identificado, método no original (`docs/onto_map/RESULTADOS_P4.md`,
`docs/onto_map/REVISION_ORIGINALIDAD.md`).

## 3. Validación por niveles (§12 v1, §11.4 v2)

| Nivel | Estado |
|---|---|
| Software (pruebas, CI en Python 3.12 y 3.13) | Hecho: 706 funciones de prueba; CI en verde en cada commit [HV] |
| Datos sintéticos con verdad conocida | Confirmado para el certificado de volumen y de topología [HV] |
| Datos reales animales | Piloto P3 completo; P3 confirmatorio y H11 en medición; ONTO-MAP negativo [HV] |
| Comparación externa con software de referencia | **Pendiente** [PV] |
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
| **P0** | Cerrar H11 (v0.4) y luego H12R: `scripts/h11_report.py` y documento de resultados según sus tablas | Fin de la cadena H11 | Ídem |
| **P1** | Comparación externa del motor 3D: volumen, área y Euler de `geovida` frente a una implementación de referencia independiente sobre fantomas y un volumen real | — (no necesita datos nuevos) | Diferencias informadas por métrica con su explicación; no se afirma superioridad |
| **P1** | Medir la contribución del atlas (MORPHO-TRACE): registrar los mismos especímenes a los atlas de E15.5 y E18.5 | Imágenes de MusMorph en ambos estadios; tiempo de cómputo | Preregistro antes de medir |
| **P1** | Revisión sistemática registrada (PubMed + Europe PMC) para MORPHO-TRACE | — | Estrategia, fecha, criterios y diagrama de selección publicados |
| **P2** | Leer las guías ISUOG completas y ampliar la biblioteca de anomalías | Acceso al texto completo | Registros sin [PV] en los campos de imagen |
| **P2** | Licencias de S-BIAD441, portal IMPC y UniCoN | — | Licencia verificada o conjunto descartado |
| **P3** | Modelo contextual 5D | Fase 5 cerrada y factor de atlas medido | Preregistro |
| **P3** | Línea de topología persistente | Pregunta en la que Betti y Euler no basten | Comparación contra métricas simples |

## 6. Estado de validación de este informe

Documento de gestión: resume evidencia existente y no aporta resultados nuevos. Las rutas citadas se pueden
comprobar en el repositorio; la cifra de pruebas se contó con `grep "def test_"` el 16 nov 2026.
