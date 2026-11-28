# Revisión sistemática registrada para MORPHO-TRACE (P1) — 17 nov 2026

> Tarea P1 de `docs/INFORME_DE_PROGRESO.md` y §8.3 del prompt rector v2 («revisión de originalidad»).
> Completa la revisión no sistemática de `docs/ANTECEDENTES_V04.md`, que dejó dos puntos con **confianza
> baja**. Etiquetas: [HV] verificado en el resumen indexado · [EI] evidencia indirecta · [PROP] propuesta ·
> [PV] pendiente.
>
> **Alcance honesto:** un solo revisor, cribado por título y resumen, y en las búsquedas grandes solo los
> primeros resultados por relevancia. Es una revisión **registrada y reproducible**, no exhaustiva: sirve
> para decir qué se buscó y qué se encontró, no para afirmar que algo no existe.

## 1. Protocolo (fijado antes de buscar)

**Preguntas.**

- **PA:** ¿Hay trabajos que separen, en morfometría de embriones por imagen 3D, la variación **técnica**
  (resolución, segmentador, registro) de la **biológica** (entre especímenes), con un diseño fijado de antemano?
  Es la pregunta de P3 (`docs/PREREGISTRO_P3.md`).
- **PB:** ¿Hay trabajos que, **sin una red neuronal**, decidan con estadísticos medidos en la propia imagen
  (ruido, desenfoque) si una medida queda fuera del dominio en que se calibró su fiabilidad? Es la guardia de
  dominio de H10 (`docs/RESULTADOS_V04.md`).

**Bases.** PubMed (con la herramienta de búsqueda de PubMed de esta sesión) y Europe PMC (API REST, que
incluye preprints). No se consultaron Scopus, Web of Science ni arXiv: no hay acceso [PV].

**Criterios de inclusión.** Artículo o preprint que (PA) cuantifique variación técnica de medidas
morfométricas embrionarias o fetales por imagen, o (PB) detecte fallos o datos fuera de distribución en
segmentación o medida de imágenes médicas. **Exclusión:** estudios clínicos que usan morfometría sin evaluar
el método, reconstrucción tomográfica, adaptación de dominio sin detección de fallos.

**Cribado.** Título y resumen; un revisor; en búsquedas con más de 10 resultados se cribaron los primeros por
relevancia (el número exacto consta en la tabla).

## 2. Búsquedas y flujo (estilo PRISMA)

| # | Base | Consulta (resumida; la literal está en §5) | Identificados | Cribados | Incluidos |
|---|---|---|---|---|---|
| B1 | PubMed | embrión/feto · micro-CT/RM/OPT · morfometría/volumen de órgano · variabilidad/reproducibilidad · segmentación/resolución/registro | 18 | 18 | 3 (PA) + 1 (ONTO-MAP) |
| B2 | PubMed | control de calidad/detección de fallos/incertidumbre · segmentación · cambio de dominio/fuera de distribución · RM/TC/ecografía | 21 | 8 | 6 (PB) |
| B3 | PubMed | calidad de imagen/ruido/desenfoque · error de medida/exactitud volumétrica · segmentación · fantoma/simulación | 23 | 6 | 0 |
| B4 | Europe PMC | embrión · micro-CT/RM · morfometría · variación técnica/error de medida/variabilidad de segmentación/componentes de varianza | 93 | 10 | 0 |
| | | **Total** | **155** | **42** | **10** |

## 3. Estudios incluidos (según PubMed)

### PA · variación técnica frente a biológica en embriones

| Estudio | Qué hace | Relación con P3 |
|---|---|---|
| Norris et al. 2012, *Magn Reson Med* 69:877–883, [10.1002/mrm.24306](https://doi.org/10.1002/mrm.24306) | Embriones de ratón por RM: volúmenes de cerebro y riñón por **propagación de un atlas** frente a segmentación manual; buen acuerdo, «misma variación que la manual» [HV] | Es el antecedente más cercano: compara dos segmentadores en el mismo embrión. No separa resolución ni estima componentes de varianza [HV, según el resumen] |
| Zamyadi et al. 2010, *Physiol Genomics* 42A:89–95, [10.1152/physiolgenomics.00091.2010](https://doi.org/10.1152/physiolgenomics.00091.2010) | Fenotipado de embriones de ratón E15.5 por RM y registro no lineal; variación anatómica residual dentro de cepa de unos 110 µm [HV] | Mide la variación biológica residual tras el registro; no la técnica |
| Oest et al. 2008, *Birth Defects Res B* 83:582–589, [10.1002/bdrb.20177](https://doi.org/10.1002/bdrb.20177) | Esqueleto fetal de ratón: micro-CT frente a tinción; error estándar medio 6,3 % frente a 10,8 % [HV] | Compara la variabilidad de dos métodos de medida; no separa fuentes |

Relevante para **ONTO-MAP** (no para PA): Hu et al. 2026, preprint en *bioRxiv*,
[10.64898/2026.09.17.752413](https://doi.org/10.64898/2026.09.17.752413) — morfoespacio de desarrollo con
morfometría geométrica 3D en 217 embriones de pollo por micro-CT; coautores del grupo de MusMorph [HV]. Refuerza
el veredicto de `docs/onto_map/REVISION_ORIGINALIDAD.md`: el análisis de trayectorias en morfoespacio es un
campo activo de ese grupo.

### PB · detección de fallos y de datos fuera de distribución

| Estudio | Mecanismo | ¿Necesita una red? |
|---|---|---|
| González et al. 2022, *Med Image Anal* 82:102596, [10.1016/j.media.2022.102596](https://doi.org/10.1016/j.media.2022.102596) | Distancia de Mahalanobis en el espacio de rasgos para detectar fallos silenciosos fuera de distribución (TC de tórax, RM) [HV] | Sí (rasgos de la red) |
| Mehrtash et al. 2020, *IEEE TMI* 39:3868–3878, [10.1109/TMI.2020.3006437](https://doi.org/10.1109/TMI.2020.3006437) | Calibración por conjuntos de modelos; predecir la calidad de la segmentación y detectar datos fuera de distribución [HV] | Sí |
| Ng et al. 2023, *IEEE TBME* 70:1955–1966, [10.1109/TBME.2022.3232730](https://doi.org/10.1109/TBME.2022.3232730) | Comparativa de incertidumbre en RM cardiaca, con imágenes con ruido y desenfoque; control de calidad por incertidumbre [HV] | Sí |
| Mojiri Forooshani et al. 2022, *Hum Brain Mapp* 43:2089–2108, [10.1002/hbm.25784](https://doi.org/10.1002/hbm.25784) | Red bayesiana con incertidumbre para control de calidad, probada con baja SNR, baja resolución y otro contraste [HV] | Sí |
| Matzkin et al. 2025, *Comput Biol Med* 196:110639, [10.1016/j.compbiomed.2025.110639](https://doi.org/10.1016/j.compbiomed.2025.110639) | Regularización de máxima entropía para que la incertidumbre anticipe errores bajo cambio de dominio [HV] | Sí |
| Bennett et al. 2026, preprint en *medRxiv*, [10.64898/2026.06.26.26356692](https://doi.org/10.64898/2026.06.26.26356692) | Seis métodos de detección de fallos en un segmentador de hígado desplegado, con datos externos de unos 70 centros [HV] | Sí (consenso entre predicciones) |

## 4. Conclusiones

- **PA [EI]:** en lo cribado, el trabajo más cercano (Norris et al. 2012) compara dos segmentadores en
  embriones de ratón, pero **no** estima por separado la parte de la variación debida a la resolución, al
  segmentador y al espécimen con un diseño fijado de antemano. La pregunta de P3 **no se encontró respondida**.
  Esto no prueba que no exista: un revisor, cribado parcial y sin Scopus ni Web of Science.
- **PB [EI]:** la detección de fallos y de datos fuera de distribución en segmentación es un campo maduro, pero
  todos los trabajos incluidos dependen de una **red neuronal** (rasgos internos, incertidumbre de la
  predicción o consenso entre modelos). No se encontró una guardia que use estadísticos de la propia imagen,
  sea válida para segmentadores clásicos y esté calibrada con fantomas de verdad conocida. La confianza sube
  respecto de `docs/ANTECEDENTES_V04.md` («baja»), pero sigue limitada por el alcance de la búsqueda.
- **Redacción que se mantiene:** «hasta donde alcanza nuestra búsqueda registrada (PubMed y Europe PMC, 17 nov
  2026), no encontramos…». Nunca «primer método».
- **Consecuencia para el proyecto [PROP]:** la diferencia defendible frente a lo publicado está en (1) separar
  fuentes de variación con un diseño preregistrado (P3) y (2) una guardia sin red neuronal aplicable a
  segmentadores clásicos. Ambas piezas deben compararse con un método de los incluidos aquí (por ejemplo,
  Mahalanobis en rasgos) antes de afirmar ventaja.

## 5. Consultas literales

- B1 (PubMed): `(embryo OR embryonic OR fetal) AND (micro-CT OR "micro-computed tomography" OR MRI OR "optical projection tomography") AND (morphometry OR morphometrics OR "organ volume") AND (variance OR variability OR reproducibility OR repeatability) AND (segmentation OR resolution OR registration)`
- B2 (PubMed): `("quality control" OR "failure detection" OR "uncertainty estimation") AND segmentation AND ("domain shift" OR "out-of-distribution" OR "distribution shift") AND (MRI OR CT OR ultrasound)`
- B3 (PubMed): `("image quality" OR "noise estimation" OR "blur estimation" OR "signal-to-noise") AND ("measurement reliability" OR "measurement error" OR "volumetric accuracy" OR "quantitative accuracy") AND (segmentation OR volumetry) AND (phantom OR simulation)`
- B4 (Europe PMC, API REST): `(embryo OR embryonic) AND ("micro-CT" OR MRI) AND (morphometry OR "organ volume") AND ("technical variation" OR "measurement error" OR "segmentation variability" OR "variance components")`

## 6. Pendiente

Repetir con Scopus o Web of Science y con un segundo revisor independiente; cribar los resultados de B2 a B4
que quedaron sin cribar; buscar en arXiv y en las actas de MICCAI los métodos de PB, donde publica buena parte
de ese campo [PV].
