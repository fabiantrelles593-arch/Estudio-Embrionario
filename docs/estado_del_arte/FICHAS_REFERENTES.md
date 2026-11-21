# Fase 1 — Fichas de referentes (estado del arte)

- **Fecha de verificación:** 14 de noviembre de 2026
- **Alcance:** los 12 referentes mínimos del §6 del prompt rector, más tres de prioridad alta de la auditoría de Fase 0 (Dalmasso 2022, HC18 y Christiansen 2016).
- **Fuentes:** metadatos y resúmenes de PubMed; texto completo de Europe PMC (secciones de disponibilidad y limitaciones); API de GitHub, PyPI, Zenodo, DataCite y BioStudies para licencias.
- **Etiquetas:** **[HV]** hecho verificado en la fuente primaria en esta fecha; **[EI]** evidencia indirecta; **[PV]** pendiente de validación; **[PROP]** propuesta del proyecto.
- **Regla:** «sin licencia» en un repositorio de código significa *todos los derechos reservados*: se puede leer y citar, pero no copiar.

> Nota de corrección respecto a la auditoría de Fase 0: Dalmasso et al. es *Dev Cell* 2022 (no un dataset de «69 superficies»: ese número no se pudo verificar). LAMA está validado solo en E14.5, no en E15.5. El código de Matula 2022 no tiene licencia.

---

## 1. Human Embryo Atlas (Yamada et al.)

| Campo | Información |
|---|---|
| Nombre | Human Embryo Atlas (Developmental atlas of the early first trimester human embryo) |
| Institución/autores | Yamada S, …, Lo CW (8 autores); NHLBI/NIH y Universidad de Kioto **[HV]** |
| Publicación | *Dev Dyn* 2010; DOI [10.1002/dvdy.22316](https://doi.org/10.1002/dvdy.22316); PMID 20503356 **[HV]** |
| Objetivo | Atlas digital de anatomía del desarrollo humano temprano **[HV]** |
| Especie/estructura | *Homo sapiens*, embrión completo, estadios de Carnegie 13–23 **[HV]** |
| Dimensionalidad | 3D (series 2D en tres planos + reconstrucciones 3D) **[HV]** |
| Modalidad | Resonancia magnética y EFIC (captura episcópica de fluorescencia) **[HV]** |
| Algoritmos | Reseccionado digital en planos arbitrarios; anotación y reconstrucción 3D **[HV]** |
| Segmentación | Anotaciones manuales de estructuras **[EI]** |
| Datos | Colección Kioto; número de especímenes por estadio **[PV]** |
| Software | Atlas web (<http://apps.devbio.pitt.edu/humanatlas/>); disponibilidad actual **[PV]** |
| Licencia | **[PV]** — sin licencia abierta conocida; tejido humano |
| Validación | Recurso descriptivo; no hay validación cuantitativa de medidas **[EI]** |
| Limitaciones | Pocos especímenes por estadio; acceso a datos crudos no garantizado **[EI]** |
| Posible integración | Referencia anatómica para la biblioteca de estructuras (§5) y para la estadificación de Carnegie |
| Reimplementación | Ninguna: es un recurso de datos, no un método |
| Mejora potencial | Ninguna directa para el proyecto |
| Prioridad | Media (biblioteca anatómica), no como datos de análisis |

## 2. Atlas 3D de desarrollo humano (de Bakker et al.)

| Campo | Información |
|---|---|
| Nombre | An interactive three-dimensional digital atlas and quantitative database of human development |
| Institución/autores | de Bakker BS, …, Moorman AFM (13 autores); Academic Medical Center, Ámsterdam **[HV]** |
| Publicación | *Science* 2016; 354(6315); DOI [10.1126/science.aag0053](https://doi.org/10.1126/science.aag0053); PMID 27884980 **[HV]** |
| Objetivo | Atlas 3D y base de datos cuantitativa de los dos primeros meses de desarrollo humano **[HV]** |
| Especie/estructura | *H. sapiens*; hasta 150 órganos y estructuras por espécimen **[HV]** |
| Dimensionalidad | 3D por estadio; crecimiento cuantificado entre estadios (pseudo-tiempo) **[HV]** |
| Modalidad | Histología: casi 15 000 cortes de la Colección Carnegie **[HV]** |
| Algoritmos | Etiquetado manual por corte y reconstrucción 3D; medidas de crecimiento y posición **[HV]** |
| Segmentación | Manual **[HV]** |
| Datos | Especímenes de la Colección Carnegie **[HV]**; número exacto **[PV]** |
| Software | Modelos 3D interactivos (formato y descarga **[PV]**) |
| Licencia | **[PV]** |
| Validación | Comparación con descripciones clásicas; aclara ambigüedades **[HV, resumen]** |
| Limitaciones | Un espécimen por estadio; deformación histológica **[EI]** |
| Posible integración | Biblioteca anatómica (§5); demuestra que «hacer un modelo 3D por estadio» no es una contribución nueva |
| Reimplementación | Ninguna |
| Mejora potencial | Ninguna directa |
| Prioridad | Baja |

## 3. HDBR (Human Developmental Biology Resource)

| Campo | Información |
|---|---|
| Nombre | Human Developmental Biology Resource (HDBR) y HDBR Atlas |
| Institución/autores | Gerrelli D, Lisgo S, Copp AJ, Lindsay S; UCL y Universidad de Newcastle **[HV]** |
| Publicación | *Development* 2015; DOI [10.1242/dev.122820](https://doi.org/10.1242/dev.122820); PMID 26395135 **[HV]** |
| Objetivo | Proveer tejido embrionario y fetal humano y recursos asociados para investigación **[HV]** |
| Especie/estructura | *H. sapiens*; embrión y feto **[HV]** |
| Dimensionalidad | Mayoritariamente 2D (cortes, expresión génica) **[EI]** |
| Modalidad | Histología, expresión génica, tejido **[HV]** |
| Algoritmos | No es un método |
| Segmentación | No aplica |
| Datos | Banco de tejidos; acceso con aprobación ética **[HV, resumen]** |
| Software | Portal web |
| Licencia | Recursos web posiblemente CC BY-NC-SA 4.0 **[EI, Notion]**; tejido bajo acuerdo **[PV]** |
| Validación | No aplica |
| Limitaciones | Material humano: exige aprobación ética e institucional |
| Posible integración | Fuente de imágenes de referencia autorizadas para la biblioteca anatómica, con licencia por activo |
| Reimplementación | Ninguna |
| Mejora potencial | Ninguna |
| Prioridad | Media (biblioteca), fuera del análisis cuantitativo |

## 4. LAMA

| Campo | Información |
|---|---|
| Nombre | LAMA: automated image analysis for the developmental phenotyping of mouse embryos |
| Institución/autores | Horner NR, …, Mallon AM (14 autores); MRC Harwell **[HV]** |
| Publicación | *Development* 2021; DOI [10.1242/dev.192955](https://doi.org/10.1242/dev.192955); PMID 33574040 **[HV]** |
| Objetivo | Fenotipado automático de embriones de ratón del IMPC mediante registro a un promedio poblacional **[HV]** |
| Especie/estructura | *Mus musculus*, embrión completo; 184 etiquetas, 103 analizadas **[HV]** |
| Dimensionalidad | 3D |
| Modalidad | Micro-TC, 14 µm isotrópico **[HV]** |
| Algoritmos | elastix (rígido, afín, B-spline multinivel) al promedio poblacional; propagación inversa de etiquetas; volumen de órgano ~ genotipo + volumen embrionario total, FDR por permutación; jacobianos suavizados por vóxel **[HV]** |
| Segmentación | Automática por registro de atlas **[HV]** |
| Datos | Promedio de 16 silvestres (8 + 8); 93 controles silvestres; líneas *Wfdc2* (4) y *Acan* (6) a E14.5 **[HV]** |
| Software | <https://github.com/mpi2/LAMA> (hoy responde 404 **[HV]**); PyPI `lama-phenotype-detection` 0.9.100 **[HV]** |
| Licencia | **Contradictoria**: PyPI declara «Apache2» y el clasificador «MIT» **[HV]** → tratar como **[PV]**. Atlas E14.5: CC BY 4.0 (Zenodo 4559800) **[HV]** |
| Validación | Control positivo por sexo (gónadas, q = 1,3e-25); tasa de falsos positivos media 0,07 % por etiqueta en 50 repeticiones **[HV]** |
| Limitaciones | Solo E14.5 validado; el retraso de desarrollo puede confundirse con dismorfología; los parámetros de registro intercambian precisión entre órganos; se excluyen estructuras pequeñas **[HV]** |
| Posible integración | Usar elastix (Apache-2.0) como dependencia externa para el registro; usar el atlas E14.5 (CC BY 4.0) si se trabaja a E14.5 |
| Reimplementación | El modelo estadístico «volumen ~ genotipo + volumen embrionario» es sencillo y reimplementable desde el artículo |
| Mejora potencial | LAMA no cuantifica la incertidumbre técnica de cada volumen de órgano: es justamente el componente E de MORPHO-TRACE **[PROP]** |
| Prioridad | **Alta** |

## 5. MusMorph

| Campo | Información |
|---|---|
| Nombre | MusMorph, a database of standardized mouse morphology data for morphometric meta-analyses |
| Institución/autores | Devine J, …, Hallgrímsson B (36 autores en PubMed); Universidad de Calgary y otros **[HV]** |
| Publicación | *Sci Data* 2022; DOI [10.1038/s41597-022-01338-x](https://doi.org/10.1038/s41597-022-01338-x); PMID 35614082; corrección *Sci Data* 2023 **[HV]** |
| Objetivo | Datos morfológicos estandarizados para metaanálisis, sobre todo craneofacial y cerebro **[HV]** |
| Especie/estructura | *M. musculus*; E10.5, E11.5, E14.5, E15.5, E18.5 y adulto **[HV]** |
| Dimensionalidad | 3D |
| Modalidad | Micro-TC **[HV]** |
| Algoritmos | Fenotipado basado en atlas: registro, aprendizaje profundo y morfometría; landmarks densos **[HV]** |
| Segmentación | «Si están disponibles»; en E15.5, 48 estructuras de un atlas publicado **[HV]**; probablemente propagadas por registro **[EI]** (ver ficha 6) |
| Datos | N = 10 056 según el resumen; la tabla 1 suma 10 132 **[PV]** |
| Software | <https://github.com/jaydevine/MusMorph> **[HV]** |
| Licencia | Código GPL-3.0 **[HV]**; subconjunto IMPC CC BY 4.0 **[HV]**; subconjuntos de Calgary sin licencia explícita (condiciones de FaceBase) **[HV]** — ver ADR-005 |
| Validación | Descrita en el artículo; no revisada en detalle **[PV]** |
| Limitaciones | Cobertura sobre todo craneal; pocos silvestres y heterocigotos; aviso de revisión en FaceBase **[HV]** |
| Posible integración | **Primer conjunto de datos reales** (ADR-005); lector MINC y manifiesto ya implementados en geovida |
| Reimplementación | No copiar el código (GPL); reimplementar desde el artículo solo lo necesario |
| Mejora potencial | Medir cuánto de la variación de un descriptor es técnica y cuánto es del espécimen (P3) **[PROP]** |
| Prioridad | **Alta** |

## 6. MEMOS

| Campo | Información |
|---|---|
| Nombre | MEMOS (Mouse Embryo Multi-Organ Segmentation) |
| Institución/autores | Rolfe SM, Whikehart SM, Maga AM; Seattle Children's Research Institute **[HV]** |
| Publicación | *Biol Open* 2023; DOI [10.1242/bio.059698](https://doi.org/10.1242/bio.059698); PMID 36802342 **[HV]** |
| Objetivo | Segmentación automática de 50 estructuras anatómicas con revisión y edición manual **[HV]** |
| Especie/estructura | *M. musculus*, E15.5 **[HV]** |
| Dimensionalidad | 3D |
| Modalidad | Micro-TC con contraste de yodo (IMPC KOMP2) **[HV]** |
| Algoritmos | Red UNETR; entrenamiento con segmentaciones generadas por registro ANTs (rígido + deformable) al atlas KOMP2 E15.5 **[HV]** |
| Segmentación | Automática con revisión humana en 3D Slicer **[HV]** |
| Datos | 91 escáneres silvestres de KOMP2; atlas de 35 especímenes C57BL/6 segmentado a mano (~400 h, Wong et al. 2012) **[HV]** |
| Software | <https://github.com/SlicerMorph/SlicerMEMOS> — extensión de 3D Slicer **[HV]** |
| Licencia | BSD-2-Clause **[HV]** |
| Validación | Comparación con segmentación por atlas y con fenotipos conocidos de *Cbx4* **[HV]** |
| Limitaciones | Resolución limitada por la memoria de la GPU (submuestreo); entrenado solo en KOMP2 E15.5 **[HV]** |
| Posible integración | Herramienta externa para obtener una **segunda segmentación independiente** de los mismos especímenes E15.5 de MusMorph **[PROP]** |
| Reimplementación | No necesaria: licencia permisiva; se puede usar como dependencia |
| Mejora potencial | Cuantificar el desacuerdo entre atlas y MEMOS por estructura como fuente de varianza técnica **[PROP]** |
| Prioridad | **Alta** (sube desde media: hace viable P3) |

**Hallazgo clave [HV + PROP]:** las «etiquetas de entrenamiento» de MEMOS son el atlas propagado por registro, no trazados manuales por espécimen. Eso confirma la advertencia de ADR-005: concordar con esas segmentaciones mide coherencia con el flujo de registro, no exactitud anatómica. A cambio, **atlas propagado frente a MEMOS** ofrece dos segmentadores distintos sobre el mismo espécimen, que es la condición técnica que P3 necesitaba.

## 7. Matula et al. 2021 — atlas μCT craneal

| Campo | Información |
|---|---|
| Nombre | X-ray microtomography-based atlas of mouse cranial development |
| Institución/autores | Matula J, …, Kaiser J (6 autores); CEITEC, Brno **[HV]** |
| Publicación | *GigaScience* 2021; DOI [10.1093/gigascience/giab012](https://doi.org/10.1093/gigascience/giab012); PMID 33677535 **[HV]** |
| Objetivo | Datos μCT reutilizables de la cabeza embrionaria **[HV]** |
| Especie/estructura | *M. musculus*, cabeza; cápsula nasal cartilaginosa y condensaciones mesenquimales **[HV]** |
| Dimensionalidad | 3D |
| Modalidad | μCT de laboratorio con tinción de ácido fosfotúngstico **[HV]** |
| Algoritmos | No es un método |
| Segmentación | Manual (cápsula nasal; condensaciones en E12.5–E13.5) **[HV]** |
| Datos | 7 cabezas, E12.5–E18.5 (n = 1 por edad) **[HV]**; GigaDB 10.5524/100862 |
| Software | No aplica |
| Licencia | **CC0 1.0** (DataCite, GigaDB) **[HV]** |
| Validación | No aplica |
| Limitaciones | n = 1 por edad: no permite estimar variación biológica **[HV]** |
| Posible integración | **Segmentaciones manuales reales con licencia CC0**: banco de prueba técnico para medir el efecto de la resolución sobre una segmentación experta **[PROP]** |
| Reimplementación | Ninguna |
| Mejora potencial | Ninguna directa |
| Prioridad | **Alta** para pruebas técnicas (sube desde media por la licencia CC0 y la segmentación manual) |

## 8. Matula et al. 2022 — CNN de cartílago

| Campo | Información |
|---|---|
| Nombre | Resolving complex cartilage structures … deep learning-based automatic segmentation of μCT |
| Institución/autores | Matula J, …, Kaiser J (8 autores) **[HV]** |
| Publicación | *Sci Rep* 2022; DOI [10.1038/s41598-022-12329-8](https://doi.org/10.1038/s41598-022-12329-8); PMID 35610276 **[HV]** |
| Objetivo | Segmentar automáticamente la cápsula nasal cartilaginosa **[HV]** |
| Especie/estructura | *M. musculus*, cápsula nasal, incluidos mutantes **[HV]** |
| Dimensionalidad | 3D tratado por cortes 2D **[EI]** |
| Modalidad | μCT, reescalado a 6 µm **[HV]** |
| Algoritmos | CNN optimizada para imágenes grandes (1792 × 1280) **[HV]** |
| Segmentación | Automática |
| Datos | Base de entrenamiento no compartible; subconjunto publicado como el atlas de la ficha 7 **[HV]** |
| Software | <https://github.com/janmatula/deep-mouse-cartilage> **[HV]** |
| Licencia | **Sin licencia** en GitHub **[HV]** → no se puede copiar el código ni los modelos |
| Validación | Dice mediano 84,44 %; de ~8 h manuales a 130 s **[HV]** |
| Limitaciones | Base pequeña; datos de entrenamiento no disponibles **[HV]** |
| Posible integración | Ninguna de código; solo como referencia de rendimiento |
| Reimplementación | Posible desde el artículo si hiciera falta (no prioritario) |
| Mejora potencial | Ninguna prioritaria |
| Prioridad | Baja |

## 9. UniCoN

| Campo | Información |
|---|---|
| Nombre | Universal conditional networks (UniCoN) for multi-age embryonic cartilage segmentation |
| Institución/autores | Sapkota N, …, Chen DZ (13 autores) **[HV]** |
| Publicación | *Sci Rep* 2025; DOI [10.1038/s41598-025-87797-9](https://doi.org/10.1038/s41598-025-87797-9); PMID 39890924 **[HV]** |
| Objetivo | Mejorar la segmentación de cartílago entre edades con anotación escasa **[HV]** |
| Especie/estructura | Ratón C57BL/6J, cartílago craneal, E13.5–E16.5 **[HV]** |
| Dimensionalidad | 3D por recortes |
| Modalidad | μCT (PTE) **[HV]** |
| Algoritmos | Módulos condicionados a la edad (discreta) y a la posición del recorte (continua), añadibles a CNN, Transformers o híbridos **[HV]** |
| Segmentación | Automática; entrenada con cortes 2D anotados parcialmente **[HV]** |
| Datos | 4 volúmenes parcialmente anotados por edad, ~1600 cortes cada uno **[HV]**; DOI 10.26208/6e6x-ps14 y 10.26208/3HY4-6S34 **[HV]**; licencia de datos **[PV]** |
| Software | No se encontró repositorio de código en el artículo **[HV, búsqueda]** |
| Licencia | Código **[PV]**; datos: `rightsList` vacía en DataCite **[HV]**, CC BY 4.0 solo en el pie del portal **[EI]** → **[PV]** (`LICENCIAS_DATOS_EXTERNOS.md`, 20 nov 2026) |
| Validación | +1,7 % de Dice de media; +7,5 % en datos no vistos **[HV]** |
| Limitaciones | Anotación escasa; mejora modesta **[HV]** |
| Posible integración | Ninguna inmediata |
| Reimplementación | La idea de condicionar a la edad es reimplementable si se entrenara un segmentador propio (no previsto) |
| Mejora potencial | Ninguna prioritaria |
| Prioridad | Baja |

## 10. IMPC — pipeline embrionario

| Campo | Información |
|---|---|
| Nombre | International Mouse Phenotyping Consortium (IMPC), pipeline embrionario |
| Institución/autores | Dickinson ME, …, Murray SA (consorcio) **[HV]** |
| Publicación | *Nature* 2016; DOI [10.1038/nature19356](https://doi.org/10.1038/nature19356); PMID 27626380 **[HV]** |
| Objetivo | Generar y fenotipar 5000 líneas knockout; 410 genes letales en las primeras 1751 **[HV]** |
| Especie/estructura | *M. musculus*, embrión completo, varios momentos **[HV]** |
| Dimensionalidad | 3D |
| Modalidad | Imagen 3D de alta resolución (micro-TC con contraste, entre otras) **[HV, resumen]** |
| Algoritmos | Plataforma estandarizada de fenotipado; análisis automáticos posteriores (LAMA, MEMOS) |
| Segmentación | Atlas KOMP2 E15.5 segmentado a mano (50 regiones) **[HV, vía MEMOS]** |
| Datos | Penetrancia incompleta y expresividad variable frecuentes **[HV]** |
| Software | Portal IMPC |
| Licencia | El subconjunto IMPC en FaceBase es CC BY 4.0 **[HV]**; portal IMPC CC BY 4.0, con cita pedida **[HV]** (`LICENCIAS_DATOS_EXTERNOS.md`, 20 nov 2026) |
| Validación | No aplica (recurso) |
| Limitaciones | Pocos mutantes por línea; variabilidad de protocolos entre centros **[EI]** |
| Posible integración | Fuente original de los embriones E15.5 de MusMorph |
| Reimplementación | Ninguna |
| Mejora potencial | Ninguna directa |
| Prioridad | **Alta** (como fuente de datos) |

## 11. Metrics Reloaded

| Campo | Información |
|---|---|
| Nombre | Metrics Reloaded: recommendations for image analysis validation |
| Institución/autores | Maier-Hein L, …, Jäger PF (73 autores; consorcio internacional) **[HV]** |
| Publicación | *Nat Methods* 2024; DOI [10.1038/s41592-023-02151-z](https://doi.org/10.1038/s41592-023-02151-z); PMID 38347141 **[HV]** |
| Objetivo | Guiar la elección de métricas según la «huella del problema» **[HV]** |
| Especie/estructura | Transversal |
| Dimensionalidad | Clasificación, detección, segmentación semántica y de instancias **[HV]** |
| Modalidad | Transversal |
| Algoritmos | Proceso Delphi; marco de decisión **[HV]** |
| Segmentación | No aplica |
| Datos | No aplica |
| Software | <https://github.com/Project-MONAI/MetricsReloaded> **[HV]** |
| Licencia | Apache-2.0 **[HV]** |
| Validación | Casos de uso biomédicos **[HV]** |
| Limitaciones | No cubre la regresión de medidas continuas (volumen, superficie) como tarea principal **[EI]** |
| Posible integración | Fijar las métricas del preregistro de P3 (Dice + HD95/ASSD + error de volumen) siguiendo el marco **[PROP]** |
| Reimplementación | No: usar la biblioteca como dependencia si hace falta |
| Mejora potencial | Ninguna |
| Prioridad | **Alta** |

## 12. Dalmasso et al. 2022 — reconstrucción 4D con armónicos esféricos

| Campo | Información |
|---|---|
| Nombre | 4D reconstruction of murine developmental trajectories using spherical harmonics (código FeARLesS) |
| Institución/autores | Dalmasso G, Musy M, …, Sharpe J (7 autores); EMBL Barcelona, CRG, CNIC **[HV]** |
| Publicación | *Dev Cell* 2022; DOI [10.1016/j.devcel.2022.08.005](https://doi.org/10.1016/j.devcel.2022.08.005); PMID 36055247 **[HV]** |
| Objetivo | Reconstruir la evolución continua de la forma de un órgano a partir de instantáneas 3D de especímenes distintos **[HV]** |
| Especie/estructura | *M. musculus*, brote de miembro (E10:10–E12:02) y corazón (10–29 somitas) **[HV]** |
| Dimensionalidad | 4D por **pseudo-tiempo** (especímenes distintos) **[HV]** |
| Modalidad | OPT (tomografía de proyección óptica) **[HV]** |
| Algoritmos | Expansión en armónicos esféricos; interpolación suave en el espacio de coeficientes **[HV]** |
| Segmentación | **[PV]** |
| Datos | BioStudies S-BIAD441 **[HV]**; número de especímenes **[PV]** |
| Software | Zenodo 6962145 (FeARLesS) **[HV]** |
| Licencia | Código MIT **[HV]**; datos S-BIAD441 sin licencia en el registro **[HV]** (comprobado de nuevo el 20 nov 2026, `LICENCIAS_DATOS_EXTERNOS.md`) → **[PV]** |
| Validación | Probado en miembro y corazón **[HV]** |
| Limitaciones | Requiere alineación previa; órganos más complejos necesitan más coeficientes **[HV]** |
| Posible integración | Referencia para el módulo 4D en pseudo-tiempo; código MIT reutilizable con atribución **[PROP]** |
| Reimplementación | La interpolación en coeficientes de armónicos esféricos es reimplementable y comparable con `traj4d` |
| Mejora potencial | Las trayectorias no llevan banda de incertidumbre técnica: candidato para MORPHO-TRACE componente F **[PROP]** |
| Prioridad | **Alta** para la Fase 6; media ahora |

## 13. HC18 (van den Heuvel et al. 2018)

| Campo | Información |
|---|---|
| Nombre | HC18 — Automated measurement of fetal head circumference using 2D ultrasound images |
| Institución/autores | van den Heuvel TLA, de Bruijn D, de Korte CL, van Ginneken B; Radboudumc **[HV]** |
| Publicación | *PLoS One* 2018; DOI [10.1371/journal.pone.0200412](https://doi.org/10.1371/journal.pone.0200412); PMID 30138319 **[HV]** |
| Objetivo | Medición automática de la circunferencia cefálica en los tres trimestres **[HV]** |
| Especie/estructura | Feto humano, cabeza **[HV]** |
| Dimensionalidad | 2D |
| Modalidad | Ecografía 2D **[HV]** |
| Algoritmos | Rasgos Haar + bosque aleatorio; Hough, programación dinámica y ajuste de elipse **[HV]** |
| Segmentación | Elipse de referencia trazada por un ecografista experimentado y un investigador **[HV]** |
| Datos | 999 imágenes de entrenamiento y 335 de prueba, con tamaño de píxel **[HV]**; Zenodo 1327317 |
| Software | No se publicó el sistema CAD original **[EI]** |
| Licencia | Datos **CC BY 4.0** (Zenodo 1327317) **[HV]** |
| Validación | Diferencias de edad gestacional comparables a un ecografista **[HV]** |
| Limitaciones | Un solo centro; imágenes seleccionadas en plano estándar **[EI]** |
| Posible integración | Validación metrológica 2D del certificado geovida (P1), **solo línea prenatal y sin uso clínico** |
| Reimplementación | No necesaria |
| Mejora potencial | Medir el error por imagen con abstención, que el artículo no reporta **[PROP]** |
| Prioridad | Alta para la línea prenatal; no bloquea el núcleo |

## 14. Christiansen 2016 — tamaño de vóxel y segmentación en μCT

| Campo | Información |
|---|---|
| Nombre | Effect of micro-computed tomography voxel size and segmentation method on trabecular bone microstructure measures in mice |
| Institución/autores | Christiansen BA; UC Davis **[HV]** |
| Publicación | *Bone Rep* 2016; DOI [10.1016/j.bonr.2016.05.006](https://doi.org/10.1016/j.bonr.2016.05.006); PMID 27430011 **[HV]** |
| Objetivo | Medir el efecto del tamaño de vóxel (6–30 µm) y del método de umbral sobre medidas trabeculares **[HV]** |
| Especie/estructura | Ratón, hueso trabecular vertebral **[HV]** |
| Dimensionalidad | 3D |
| Modalidad | μCT **[HV]** |
| Algoritmos | Dos métodos de umbral global (cualitativo e histograma) en varios tamaños de vóxel **[HV]** |
| Segmentación | Umbral global **[HV]** |
| Datos | **[PV]** (tamaño de muestra no leído) |
| Software | No aplica |
| Licencia | Artículo de acceso abierto (PMC4926804) **[HV]** |
| Validación | Comparación entre resoluciones **[HV]** |
| Limitaciones | Hueso adulto, no estructuras embrionarias **[HV]** |
| Posible integración | **Antecedente directo de H1/H3 y de P3**: el efecto de la resolución y del segmentador sobre la morfometría ya se ha estudiado en hueso |
| Reimplementación | El diseño (factorial resolución × segmentador) es el modelo para el piloto de P3 **[PROP]** |
| Mejora potencial | Estimar componentes de varianza (técnica frente a espécimen) en lugar de solo comparar medias **[PROP]** |
| Prioridad | **Alta** (impide afirmar novedad sin citarlo) |

## 15. Infraestructura de software (licencias verificadas en GitHub el 14 nov 2026)

| Herramienta | Función | Licencia | Uso permitido en geovida (MIT) |
|---|---|---|---|
| nibabel | Lectura de NIfTI y MINC | MIT según su archivo COPYING **[EI]** (GitHub: NOASSERTION; texto completo **[PV]**) | Dependencia (ya en uso) |
| scikit-image | Procesamiento de imagen, marching cubes | BSD-3-Clause **[HV]** | Dependencia (ya en uso) |
| SimpleITK | Registro, remuestreo | Apache-2.0 **[HV]** | Dependencia opcional |
| elastix | Registro (usado por LAMA) | Apache-2.0 **[HV]** | Herramienta externa |
| ANTs | Registro (usado por MEMOS) | Apache-2.0 **[HV]** | Herramienta externa |
| nnU-Net | Segmentación con aprendizaje profundo | Apache-2.0 **[HV]** | Herramienta externa |
| 3D Slicer | Visualización, revisión de segmentaciones | BSD con extensiones **[HV]** | Herramienta externa |
| SlicerMorph | Morfometría 3D en Slicer | BSD-2-Clause **[HV]** | Herramienta externa |
| SlicerMEMOS | Segmentación de 50 estructuras E15.5 | BSD-2-Clause **[HV]** | Herramienta externa |
| MetricsReloaded | Métricas de validación | Apache-2.0 **[HV]** | Dependencia opcional |
| GUDHI | Homología persistente | MIT **[HV]** | Dependencia opcional (Fase 5) |
| ripser.py | Homología persistente rápida | MIT **[HV]** | Dependencia opcional |
| giotto-tda | Aprendizaje topológico | NOASSERTION en GitHub; licencia propia de L2F **[HV]** | **Evitar** hasta revisar el texto completo |
| geomorph (R) | Morfometría geométrica | GPL (≥ 3) **[HV]** | Solo herramienta externa; **no copiar código** |
| PyVista / vedo | Mallas y visualización 3D | MIT **[HV]** | Dependencia opcional |
| MusMorph (scripts) | Flujo de MusMorph | GPL-3.0 **[HV]** | Solo lectura; **no copiar** (ADR-005) |
| deep-mouse-cartilage | CNN de Matula 2022 | Sin licencia **[HV]** | **No copiar** |
| LAMA | Fenotipado por registro | Contradictoria (Apache2/MIT) **[HV]** | Solo lectura hasta aclararla |

---

## Evidencia

Todas las referencias se obtuvieron de PubMed el 14 nov 2026 (PMID indicados). Textos completos de Europe PMC: PMC8015254 (LAMA), PMC9990908 (MEMOS), PMC9130254 (Matula 2022), PMC9481268 (Dalmasso), PMC11785758 (UniCoN), PMC7936920 (Matula 2021). Licencias: API de GitHub; PyPI `lama-phenotype-detection`; Zenodo 4559800, 6962145 y 1327317; DataCite 10.5524/100862; BioStudies S-BIAD441.

**Sin verificar todavía [PV]:** Belle et al. 2017 (*Cell*, 10.1016/j.cell.2017.03.008, no localizado en PubMed); licencia de los datos de UniCoN y de S-BIAD441 (sin licencia del conjunto el 20 nov 2026; la del portal IMPC quedó verificada ese día: `LICENCIAS_DATOS_EXTERNOS.md`); tamaño muestral de Christiansen 2016; disponibilidad actual del Human Embryo Atlas.
