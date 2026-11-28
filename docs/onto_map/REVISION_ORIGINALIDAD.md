# ONTO-MAP — Revisión de originalidad (15 nov 2026)

> Tarea P2 del mandato v2.0: comprobar, antes de presentar ONTO-MAP como contribución, qué parte ya existe en la literatura.
> Búsqueda en PubMed el 15 nov 2026. No es una revisión sistemática: es una comprobación dirigida, y puede haber trabajos que no aparezcan con estas consultas.
> Etiquetas: [HV] verificado en esta búsqueda · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta · [PV] pendiente de validación.

## 1. Qué se comprobó

ONTO-MAP P4 compara, en el espacio tangente de un GPA conjunto, la dirección de la alometría estática dentro de cada estadio con el vector que une las formas medias de dos estadios (E15.5 y E18.5), usando ángulos entre vectores y bootstrap (`docs/onto_map/PROTOCOLO_ONTOMAP.md`).

Se separaron dos preguntas:

1. ¿Es nuevo el **método** (comparar alometría estática con el cambio de forma entre edades mediante ángulos entre vectores)?
2. ¿Es nuevo el **dato** (hacerlo con landmarks embrionarios de ratón de MusMorph)?

## 2. Consultas y resultado

| Consulta en PubMed | Resultados | Relevantes |
|---|---|---|
| `static allometry ontogenetic allometry` | 48 | Sí: es un tema establecido (ver §3) [HV] |
| `MusMorph` | 2 | El artículo del conjunto de datos y su corrección; ninguno compara alometría estática y entre estadios [HV] |
| `allometry mouse embryo` | 3 | Ninguno sobre forma (tratan de peso de órganos posnatal) [HV] |
| Variantes con *embryo/embryonic*, *face*, *landmarks*, *trajectory*, *micro-CT* | 0 | — |

La ausencia de resultados con las variantes largas se debe en parte a que PubMed exige todos los términos; **no** prueba que el análisis no exista [PV].

## 3. Literatura que ya cubre el método

- **El marco conceptual** de alometría estática, ontogenética y evolutiva en morfometría geométrica, incluida la comparación de direcciones, está revisado en Klingenberg 2016, *Dev Genes Evol* 226 ([10.1007/s00427-016-0539-2](https://doi.org/10.1007/s00427-016-0539-2)) [HV].
- **Ángulos entre vectores de alometría** como estadístico, con atención al error de muestreo: Cardini 2024, *Anat Rec* 308:868–891 ([10.1002/ar.25544](https://doi.org/10.1002/ar.25544)). Este trabajo advierte que las direcciones de la alometría estática son más variables que las ontogenéticas y que el error de muestreo las magnifica [HV].
- **Alometría estática, ontogenética y evolutiva comparadas** en un mismo conjunto 3D: Le Verger et al. 2024, *Evolution* 78:423–441 ([10.1093/evolut/qpad214](https://doi.org/10.1093/evolut/qpad214)) [HV].
- **Variación continua de la forma facial embrionaria** cuantificada con morfometría geométrica: Young et al. 2010, *Development* 137:3405–3409 ([10.1242/dev.052340](https://doi.org/10.1242/dev.052340)). Es en pollo, no en ratón [HV].
- **Los datos:** Devine et al. 2022, *Sci Data* 9:230 ([10.1038/s41597-022-01338-x](https://doi.org/10.1038/s41597-022-01338-x)), con atlas propio por estadio [HV].

## 4. Veredicto

- **[HV] El método no es original.** Comparar alometría estática con la dirección del cambio entre edades mediante ángulos entre vectores es práctica establecida. ONTO-MAP P4 aplica ese método; no lo propone.
- **[EI] La aplicación es, como mucho, una contribución empírica estrecha.** No encontré un análisis igual con los landmarks embrionarios de MusMorph para E15.5 frente a E18.5. Pero la búsqueda no es exhaustiva, y el grupo que publicó MusMorph trabaja en variación facial embrionaria, así que es plausible que exista un análisis parecido fuera de estas consultas [PV].
- **[HV] El resultado obtenido (negativo, `RESULTADOS_P4.md`) no puede separarse del factor de confusión del atlas por estadio.** Por eso no aporta, por sí solo, una afirmación biológica nueva.

## 5. Consecuencias para el proyecto

- **No presentar** ONTO-MAP P4 como método nuevo ni como hallazgo biológico. Presentarlo como réplica metodológica con un resultado negativo y un factor de confusión identificado [PROP].
- **Lo que sí podría ser original** es la pregunta de MORPHO-TRACE: **cuánto** de una diferencia de forma entre estadios se debe al atlas y al registro. Ninguna de las consultas devolvió una estimación de ese efecto para MusMorph [HIP]. Medirlo exige registrar los mismos especímenes a los dos atlas, y eso necesita las imágenes, no solo los landmarks [PV].
- **Antes de cualquier presentación externa:** revisión por un asesor con experiencia en morfometría geométrica, y una búsqueda bibliográfica más amplia (Scopus o Web of Science, y la literatura del grupo de Hallgrímsson sobre la cara embrionaria) [PROP].
