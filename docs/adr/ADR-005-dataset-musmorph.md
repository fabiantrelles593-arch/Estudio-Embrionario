# ADR-005: MusMorph como primer conjunto de datos reales

- **Estado:** Aceptada (elección del conjunto). Pendiente: subconjunto exacto y tamaño del piloto.
- **Fecha:** 13 de noviembre de 2026
- **Decisor:** autor del proyecto (aprobado en el chat)
- **Depende de:** ADR-001, ADR-004
- **Cierra:** decisión 6 de la auditoría de Fase 0 (pregunta P3)

## Contexto

Las 16 hipótesis de geovida (H1–H16) se evaluaron solo con datos simulados. La auditoría de Fase 0 propuso tres candidatos para la primera validación con datos reales: HC18 (ecografía 2D), el brote de miembro de Dalmasso y MusMorph (ratón, micro-TC 3D). Se elige MusMorph porque encaja con el núcleo embriológico y con MORPHO-TRACE, la separación de la variación técnica y la biológica. HC18 reforzaría la línea prenatal, que debe mantenerse aparte.

## Qué es MusMorph (verificado el 13 nov 2026)

- **Publicación:** Devine J, Vidal-García M, Liu W, … Hallgrímsson B (34 autores). *MusMorph, a database of standardized mouse morphology data for morphometric meta-analyses.* Sci Data 9, 230 (2022). DOI [10.1038/s41597-022-01338-x](https://doi.org/10.1038/s41597-022-01338-x). Corrección: Sci Data 10, 420 (2023). **[HV]**
- **Datos:** proyecto FaceBase [10.25550/3-HXMC](https://doi.org/10.25550/3-HXMC), publicado el 5 nov 2021, con más de 25 subconjuntos por línea genética. **[HV]**
- **Código:** <https://github.com/jaydevine/MusMorph>, licencia **GPL-3.0**. **[HV]**
- **Contenido:** imágenes de micro-TC alineadas rígidamente, landmarks densos (22 homólogos en embriones), atlas por estadio y, solo donde existen, segmentaciones. **[HV]**

| Estadio | Origen | Resolución (mm) | N | Segmentaciones |
|---|---|---|---|---|
| E10.5 | Calgary | 0,012 | 434 | No |
| E11.5 | Calgary | 0,012 | 531 | No |
| E14.5 | Calgary | 0,027 | 84 | No |
| **E15.5** | **IMPC** | **0,027** | **1426** | **Sí (48 estructuras del atlas publicado)** |
| E18.5 | IMPC | 0,054 | 1657 | No |
| Adulto | Calgary | 0,035 | 6000 | Sí (cráneo, endocráneo, mandíbula) |

Fuente: tabla 1 del artículo, según la extracción de PMC9133120. Las N de la tabla suman 10 132, mientras que el resumen dice N = 10 056. La discrepancia está **[PV]** y se resolverá con los recuentos de FaceBase.

- **Formatos:** las imágenes, los atlas y las segmentaciones están en MINC (`.mnc`); los landmarks, en `.tag` y `.csv`; las transformaciones, en `.xfm`. En el subconjunto IMPC, cada volumen E15.5 ocupa entre 15 y 135 MB (muestra de 25 archivos vista en FaceBase). **[HV]**

## Licencias y condiciones (verificado el 13 nov 2026)

| Activo | Licencia o condición | Fuente |
|---|---|---|
| Subconjunto **IMPC** (E15.5, E18.5) | **CC BY 4.0**: «The IMPC data are available for sharing and adaptation under the Creative Commons Attribution 4.0 International license» | Registro FaceBase 3-JZA6 **[HV]** |
| Subconjuntos **Calgary** (Ap2, Fgf, Bulgy, etc.) | **Sin licencia explícita.** Rigen las condiciones de uso de FaceBase: el copyright es de los investigadores, hay que citar el proyecto y las publicaciones, no se pueden redistribuir los archivos originales y hay que avisar a FaceBase de las publicaciones | Registro 3-JQMG; <https://www.facebase.org/policies/tou/> **[HV]** |
| Artículo | CC BY 4.0 | Sci Data **[HV]** |
| Código MusMorph | GPL-3.0 | GitHub **[HV]** |

## Decisión

1. **Primer subconjunto: IMPC E15.5.** Es el único estadio embrionario que tiene a la vez una licencia abierta explícita (CC BY 4.0), segmentaciones y una resolución homogénea. Los subconjuntos de Calgary quedan fuera hasta que se pida y documente un permiso explícito.
2. **Los datos no entran en el repositorio.** Se descargan fuera de Git, porque las condiciones de FaceBase piden no redistribuir los originales. En el repositorio solo quedan:
   - un manifiesto con el RID de FaceBase, el nombre de archivo, el SHA-256, la fecha de descarga y la licencia;
   - las medidas derivadas y los scripts.
3. **El código de MusMorph no se copia.** Es GPL-3.0 y geovida es MIT (ADR-004). Si hace falta algún paso de su flujo, se reimplementa a partir del artículo o se usa como herramienta externa, sin incorporarlo.
4. **Lectura de MINC:** se usará `nibabel`, que ya está entre las dependencias de desarrollo y lee MINC1 y MINC2. MINC2 necesita además `h5py`. Antes de medir nada, la lectura se prueba con un fantoma escrito en MINC: espaciado, orientación y volumen conocidos.
5. **Pregunta P3, versión piloto [PROP]:** en embriones E15.5 de tipo silvestre, ¿qué parte de la varianza del volumen y de la topología de una estructura segmentada se debe a la resolución (remuestreo ×1, ×2, ×4) y a la segmentación, y qué parte al espécimen? Antes de ejecutarlo se registrará el preregistro: estructura, N, métricas y criterio.

## Advertencias

- **Las segmentaciones por espécimen probablemente proceden del atlas propagado por registro, no de un trazado manual [EI, PV].** Si es así, no son una «verdad anatómica», y el acuerdo con ellas mide la coherencia con el flujo de MusMorph, no la exactitud anatómica. Hay que comprobarlo en el artículo antes de usarlas como referencia.
- **Disponibilidad:** FaceBase muestra el aviso «This repository is under review for potential modification in compliance with Administration directives». Los datos podrían cambiar o dejar de estar accesibles. Por eso el manifiesto con SHA-256 es obligatorio.
- **Cuenta:** la descarga (BDBag) exige una cuenta gratuita de FaceBase. La crea y la usa el autor del proyecto; el asistente no crea cuentas.
- **Cobertura:** sobre todo cabeza. El cuerpo entero está limitado y faltan los estadios E12.5–E14.5. Los embriones de tipo silvestre y heterocigotos están poco representados (limitación declarada por los autores).
- **Bienestar animal y ética:** son datos animales ya publicados por IMPC. No hay datos humanos ni identificables.

## Consecuencias

- Se desbloquea la Fase 2 (protocolo) con una especie (*Mus musculus*), un estadio (E15.5), una modalidad (micro-TC) y una licencia verificada.
- Trabajo técnico necesario: un lector MINC con pruebas, un manifiesto de datos externos y un `.gitignore` para la carpeta de datos.
- Sigue faltando un asesor humano (decisión 9) que revise la estructura elegida y la interpretación anatómica.
