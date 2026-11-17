# Fase 1 — Matriz de capacidades, catálogo de datos y oportunidades

- **Fecha:** 14 de noviembre de 2026
- **Base:** `FICHAS_REFERENTES.md` (15 fichas verificadas en fuentes primarias) y el código de geovida v0.11.
- **Etiquetas:** [HV] hecho verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta · [PV] pendiente de validación.

## 1. Matriz de capacidades

| Capacidad | Estado fuera del proyecto | Estado en geovida | Decisión |
|---|---|---|---|
| Lectura de volúmenes NIfTI/MINC con orientación | Resuelto (nibabel) [HV] | Implementado con pruebas de fantoma (`realdata`, `minc`) [HV] | Mantener |
| Registro a atlas / promedio poblacional | Resuelto (elastix en LAMA, ANTs en MEMOS) [HV] | No existe | **Integrar** como herramienta externa; no reimplementar |
| Segmentación multiórgano de embrión E15.5 | Resuelto en parte (MEMOS, 50 estructuras; entrenado con atlas propagado) [HV] | Solo segmentadores de umbral sobre fantomas | **Integrar** MEMOS como segundo segmentador externo |
| Segmentación de cartílago embrionario | Resuelto en parte (Matula 2022, Dice 0,84; UniCoN) [HV] | No | Fuera de alcance |
| Fenotipado estadístico por órgano (volumen ~ genotipo + tamaño) | Resuelto (LAMA) [HV] | No | Reimplementar el modelo si se comparan genotipos (Fase 7) |
| Métricas de validación de segmentación | Resuelto como guía (Metrics Reloaded) [HV] | Dice y error de volumen en `measure` [HV] | Añadir HD95 y ASSD según Metrics Reloaded |
| Efecto de la resolución y del umbral sobre la morfometría μCT | Estudiado en hueso adulto (Christiansen 2016) [HV] | Estudiado en fantomas (H1, H3) [HV] | **Citar**; trasladar a estructuras embrionarias reales |
| Trayectorias 4D por pseudo-tiempo | Resuelto para miembro y corazón (Dalmasso 2022, armónicos esféricos) [HV] | `traj4d` sintético, etiquetado como pseudo-tiempo [HV] | Comparar con FeARLesS (MIT) en la Fase 6 |
| Incertidumbre técnica por medida (certificado con abstención) | No encontrado en los referentes revisados [EI] | Implementado y calibrado en sintético [HV] | **Validar con datos reales** (núcleo de MORPHO-TRACE) |
| Separación de varianza técnica frente a biológica en embriones | No encontrado en los referentes revisados [EI] | No implementado | **Contribución candidata** (P3) |
| Homología persistente aplicada a forma embrionaria | Herramientas maduras (GUDHI, ripser) [HV] | Margen topológico propio (`topomargin`) [HV] | Usar GUDHI solo si añade información a Betti + margen (§7 del prompt) |
| Atlas anatómicos humanos | Existen (Yamada 2010, de Bakker 2016, HDBR) [HV] | No | Solo referencia para la biblioteca anatómica |

**Lectura:** lo que ya está resuelto por otros (registro, segmentación, atlas, métricas) se integra; lo que nadie en esta lista resuelve —la incertidumbre técnica por medida y su separación de la variación biológica— es donde tiene sentido la contribución propia. Esto es [EI]: la lista no es una revisión sistemática, así que **no autoriza a afirmar novedad**.

## 2. Catálogo de datos candidatos

| Conjunto | Especie / estructura | Modalidad | Segmentación de referencia | Licencia verificada | Uso propuesto |
|---|---|---|---|---|---|
| MusMorph IMPC E15.5 | Ratón, embrión | μCT 0,027 mm | 48 estructuras, probablemente atlas propagado [EI] | CC BY 4.0 [HV] | **Piloto P3** (ADR-005) |
| MusMorph landmarks de cabeza (FaceBase 3-JZA6) | Ratón, cabeza E15.5 y E18.5 | 540 landmarks por registro automático | Sin anotación experta [HV] | CC BY 4.0 [HV] | **ONTO-MAP P4** (717 especímenes, `docs/onto_map/RESULTADOS_P4.md`) |
| Qiu et al. 2021 (IEEE DataPort) | Ratón, embrión E10–E14 | Ecografía 3D de alta frecuencia | Cuerpo y ventrículos cerebrales, dibujados por personas [HV] | CC BY [HV] | **H11 / H12R** (desviación D1 en `docs/PREREGISTRO_H11.md`; medición en curso) |
| Matula 2021 (GigaDB 10.5524/100862) | Ratón, cabeza E12.5–E18.5 | μCT | **Manual** (cápsula nasal) [HV] | **CC0 1.0** [HV] | Banco técnico: efecto de la resolución sobre una segmentación experta |
| LAMA atlas E14.5 (Zenodo 4559800) | Ratón, embrión | μCT 14 µm | Atlas de 184 etiquetas [HV] | CC BY 4.0 [HV] | Referencia si se trabaja a E14.5 |
| Dalmasso S-BIAD441 | Ratón, miembro y corazón | OPT | [PV] | Sin licencia en el registro [HV] → [PV] | Fase 6, tras aclarar la licencia |
| HC18 (Zenodo 1327317) | Feto humano, cabeza | Ecografía 2D | Elipse experta [HV] | CC BY 4.0 [HV] | Línea prenatal metrológica (P1), sin uso clínico |
| UniCoN (10.26208/6e6x-ps14) | Ratón, cartílago E13.5–E16.5 | μCT | Parcial, por cortes [HV] | [PV] | Ninguno por ahora |
| Human Embryo Atlas, de Bakker, HDBR | Humano | RM, EFIC, histología | Manual | [PV] / restringida | Solo biblioteca anatómica |

## 3. Consecuencia para el diseño del piloto P3 [PROP]

La auditoría de Fase 0 señaló como riesgo de P3 que «depende de que existan reescaneos o segmentaciones múltiples». La Fase 1 lo resuelve sin datos nuevos:

| Factor técnico | Cómo se obtiene | Licencia |
|---|---|---|
| Resolución | Remuestreo controlado ×1, ×2, ×4 del mismo volumen (geovida) | Propia |
| Segmentador A | Segmentación de MusMorph (atlas propagado) | CC BY 4.0 |
| Segmentador B | MEMOS ejecutado sobre el mismo volumen | BSD-2-Clause |
| Referencia manual (control) | Cápsula nasal de Matula 2021, con su propio diseño | CC0 |

Diseño propuesto: modelo de componentes de varianza `descriptor ~ (1 | espécimen) + resolución + segmentador + resolución:segmentador`, con el espécimen como unidad experimental. Estructuras candidatas: las que coinciden entre las 48 de MusMorph y las 50 de MEMOS (lista exacta **[PV]**). La estructura, el N y el criterio se fijan en el preregistro, con revisión de un asesor.

**Hipótesis falsable [HIP]:** para estructuras grandes y compactas la varianza entre especímenes domina a la técnica; para estructuras pequeñas o delgadas la técnica alcanza o supera a la biológica, y el certificado de geovida marca esas medidas en amarillo, rojo o abstención. Si el certificado no separa ambos grupos mejor que un intervalo bootstrap simple, MORPHO-TRACE se modifica o se descarta (§9.6 del prompt).

## 4. Qué queda pendiente de la Fase 1

- ~~Revisión sistemática formal de antecedentes (PubMed + Europe PMC con estrategia registrada) antes de afirmar novedad.~~ Hecha el 17 nov 2026: `docs/estado_del_arte/REVISION_SISTEMATICA_MORPHOTRACE.md` (falta Scopus/Web of Science y un segundo revisor).
- ~~Lista exacta de estructuras comunes entre MusMorph E15.5 y MEMOS.~~ Resuelto en el piloto de P3: las etiquetas 1–48 coinciden; la 102 y la 103 de MusMorph no se corresponden con la 49 y la 50 de KOMP2 (`docs/p3/RESULTADOS_PILOTO.md` §4).
- Licencia de S-BIAD441, del portal IMPC y de los datos de UniCoN.
- Herramientas de morfometría geométrica y análisis de superficies: solo se verificaron licencias, no se compararon métodos.
- Línea prenatal: PSFHS y FETAL_PLANES_DB sin ficha todavía. Biblioteca de anomalías congénitas iniciada (4 registros con fuente): `docs/prenatal/BIBLIOTECA_ANOMALIAS.md`.
