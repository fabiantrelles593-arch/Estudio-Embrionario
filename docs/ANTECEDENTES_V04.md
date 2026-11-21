# Antecedentes de v0.4: qué existe ya y qué se pone a prueba

Resumen de la cuarta investigación de antecedentes (noviembre de 2026; unas 18 consultas y un
subagente, no una revisión sistemática). Sirve para dos cosas: citar bien y no llamar «nuevo» a lo
que no lo es.

## Veredicto por componente

| Componente de geovida | Antecedente más cercano | Qué hace el antecedente | Qué añade geovida | Veredicto |
|---|---|---|---|---|
| Semáforo de volumen por profundidad media d̄/h (H6) | Horner et al. 2019; Bouxsein et al. 2010; perfiles QIBA de volumetría por TC; Kohlberger et al. 2012 | Reglas fijas de vóxeles por diámetro o grosor; predicción del Dice a partir de rasgos de la máscara | Una probabilidad por medida, calibrada con fantomas analíticos y congelada por segmentador | Combinación aparentemente nueva de ideas conocidas |
| Margen topológico geométrico (H9) | Robins, Saadatfar, Delgado-Friedrichs y Sheppard 2016 | Persistencia en la filtración por distancia euclídea con signo, en micro-CT de medios porosos | Su uso como predictor calibrado de que el Betti medido es correcto, contra verdad conocida | El objeto matemático ya existe; es una transferencia |
| Margen topológico de intensidad (H9) | Chung y Day 2018 | Homología persistente por umbral para elegir el umbral | Ídem: probabilidad calibrada | Transferencia |
| Incertidumbre topológica calibrada | Gupta, Zhang, Hu, Prasanna y Chen 2023 | Incertidumbre por estructura con redes entrenadas, evaluada con ECE | Sin red; descriptores explícitos; triple de Betti global | El antecedente más cercano en calibración |
| Eje de escala (H10d) | Roache 1994; Celik et al. 2008; Coeurjolly, Lachaud y Roussillon 2012; Cook y Stefanski 1994 (SIMEX) | Convergencia al refinar la malla; convergencia multimalla de estimadores digitales; degradar y extrapolar | Aquí solo se puede engrosar; se usa como variable, no como extrapolación | Transferencia |
| Certificado por medida, evaluado con calibración y verde falso | Zenk et al. 2025; Lambert et al. 2024 | Detección de fallos y predicción conforme en segmentación 3D | Fallo definido por cada medida derivada; fantomas analíticos | Las piezas existen; la combinación no se encontró |
| Guardia de dominio (H10) | Literatura de detección fuera de distribución y la advertencia de Lambert et al. sobre intercambiabilidad | — | Dos índices medidos en la imagen y una envolvente de calibración | No se buscó de forma específica: **confianza baja** |

## Cómo se redacta la novedad

> Hasta donde alcanza nuestra búsqueda (PubMed, arXiv, actas de MICCAI, NeurIPS e ICML y revistas
> de geometría digital, hasta noviembre de 2026), no hemos identificado trabajos que estimen, sin
> verdad de terreno y para cada medida, la probabilidad de que el volumen y los números de Betti
> cumplan una tolerancia, calibrada con fantomas de verdad analítica. Los componentes
> individuales tienen antecedentes claros: la persistencia en filtraciones por distancia con
> signo y por umbral, el Grid Convergence Index, la convergencia multimalla y la detección de
> fallos en segmentación.

Frases que este proyecto **no** usa: «primer método», «nunca antes», «marco 5D», «quinta
dimensión» (en bioimagen «5D» ya significa x, y, z, canal y tiempo: Moore et al. 2021), «sin
supuestos», «detecta errores topológicos» (el fallo silencioso es indetectable), «validado» a
secas (es «validado en fantomas sintéticos»).

## Riesgos que señalaría un revisor y qué se hizo

| Riesgo | Qué se hizo en v0.4 | Qué queda pendiente |
|---|---|---|
| Calibrar y validar con el mismo simulador | Cuatro perfiles de imagen nunca vistos (`shift`) y dos formas nunca vistas (`unseen`) | Un segundo generador independiente y fantomas físicos |
| Dependencia del perfil declarado | Guardia de dominio; se mide el verde falso con el perfil mal declarado | — |
| Fallo silencioso | Se mide y se informa por resolución y por forma; no se promete detectarlo | Declarar un tamaño mínimo detectable por perfil |
| Multiplicidad de hipótesis | Dos primarias (H9d, H10b); intervalos de Wilson | Corrección formal si se publican todas como confirmatorias |
| Colinealidad entre d̄/h y Q | Modelos anidados comparados fuera de muestra (T1, T4, T7) | — |
| Ambigüedad de la verdad topológica digital | Par de adyacencias (26, 6) fijo y verdad comprobada con rasterización fina | — |
| El promedio de bloques no es una adquisición más gruesa | Declarado como límite | Degradación con PSF escalada y ruido reinyectado |
| ECE con pocos casos | Se informa junto con AUC, cobertura y verde falso | ECE adaptativa |

## Referencias

Verificadas en la investigación (DOI o identificador comprobado):

* Bouxsein ML et al. (2010). *J Bone Miner Res* 25(7):1468–1486. doi:10.1002/jbmr.141
* Celik IB et al. (2008). *J Fluids Eng* 130:078001. doi:10.1115/1.2960953
* Christiansen BA (2016). *Bone Reports* 5:136–140. doi:10.1016/j.bonr.2016.05.006
* Chung Y-M, Day S (2018). *J Math Imaging Vis* 60:1167–1179. doi:10.1007/s10851-018-0802-4
* Coeurjolly D, Lachaud J-O, Roussillon T (2012). En *Digital Geometry Algorithms*, 395–424.
  doi:10.1007/978-94-007-4174-4_13
* Cohen-Steiner D, Edelsbrunner H, Harer J (2007). *Discrete Comput Geom* 37(1):103–120.
  doi:10.1007/s00454-006-1276-5
* Cook JR, Stefanski LA (1994). *JASA* 89:1314–1328. doi:10.1080/01621459.1994.10476871
* Gupta S, Zhang Y, Hu X, Prasanna P, Chen C (2023). NeurIPS 36. arXiv:2306.05671
* Horner M et al. (2019). *J Verif Valid Uncertain Quantif* 4(4):041002. doi:10.1115/1.4045487
* Kohlberger T et al. (2012). MICCAI. doi:10.1007/978-3-642-33415-3_65
* Lambert B, Forbes F, Doyle S, Dojat M (2024). MICCAI, LNCS 15010:633–643.
  doi:10.1007/978-3-031-72117-5_59
* Maier-Hein L et al. (2024). *Nat Methods* 21:195–212. doi:10.1038/s41592-023-02151-z
* Moore J et al. (2021). *Nat Methods* 18:1496–1498. doi:10.1038/s41592-021-01326-w
* Roache PJ (1994). *J Fluids Eng* 116:405–413. doi:10.1115/1.2910291
* Robins V, Saadatfar M, Delgado-Friedrichs O, Sheppard AP (2016). *Water Resour Res*
  52(1):315–329. doi:10.1002/2015WR017937
* Valindria VV et al. (2017). *IEEE Trans Med Imaging* 36(8):1597–1606.
  doi:10.1109/TMI.2017.2665165
* Zenk M et al. (2025). *Med Image Anal* 101:103392. doi:10.1016/j.media.2024.103392

**No verificadas** en esa búsqueda (citar solo después de comprobarlas): Kong y Rosenfeld 1989
(topología digital); Mecke 2002 y Vogel et al. 2005 (funciones de Minkowski); ISO 25178 y el
análisis área-escala; JCGM 100 y 101 (GUM); Stelldinger y Köthe 2005 (DOI sin comprobar).

Cálculo propio, no una fuente: para una bola de radio R, d̄ = R/4 y V/S = R/3, así que
d̄/h = (3/4)·Q. La profundidad media es, por tanto, pariente directo de las reglas de «vóxeles
por diámetro»; lo que se aporta es la calibración probabilística, no el descriptor.
