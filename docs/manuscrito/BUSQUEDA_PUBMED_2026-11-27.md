# Búsqueda de trabajos relacionados en PubMed (27 nov 2026)

> **Qué es:** la parte de la búsqueda bibliográfica que se pudo hacer con las herramientas disponibles, para el
> manuscrito `docs/manuscrito/MANUSCRIPT_MC_EN.md` y su versión LaTeX.
> **Qué no es:** la búsqueda en Scopus o Web of Science que pide `docs/SINTESIS_CERTIFICADO.md` §6. Esa sigue
> pendiente.
>
> **Etiquetas:** [HV] verificado en PubMed · [HIP] hipótesis · [PROP] propuesta.

## 1. Método

- **Base:** PubMed, consultada el 27 nov 2026 mediante el conector de PubMed. Cada referencia elegida se comprobó con
  sus metadatos (autores, revista, volumen, páginas, DOI y PMID).
- **Pregunta:** qué se ha publicado sobre (a) control de calidad por caso de segmentaciones automáticas, (b)
  incertidumbre como indicador de fiabilidad, en particular en ecografía, y (c) prácticas de validación,
  preregistro y comunicación en análisis de imagen médica con aprendizaje automático.
- **Criterio de inclusión:** trabajo que sirva de antecedente directo a una afirmación del manuscrito o que la
  matice. No se buscó exhaustividad.

## 2. Consultas y resultados

| # | Consulta (sintaxis de PubMed) | Resultados | Elegidos |
|---|---|---|---|
| 1 | `automated quality control segmentation deep learning failure detection` | 1 | 0 (una revisión de ecocardiografía, demasiado general) |
| 2 | `machine learning medical imaging methodological failures recommendations` | 1 | Varoquaux y Cheplygina 2022 |
| 3 | `confidence calibration predictive uncertainty deep medical image segmentation` | 15 | Mehrtash et al. 2020 |
| 4 | `Robinson R[Author] automated quality control image segmentation UK Biobank` | 1 | Robinson et al. 2019 |
| 5 | `Metrics reloaded recommendations image analysis validation[Title]` | 1 | Maier-Hein et al. 2024 |
| 6 | `Checklist for Artificial Intelligence in Medical Imaging CLAIM[Title]` | 12 | Tejani et al. 2024 (actualización de CLAIM) |
| 7 | `segmentation quality estimation without ground truth deep learning` | 48 | 3, tras revisar los 48 (ver §3b) |
| 8 | `preregistration machine learning research reproducibility` | 5 | Gallitto et al. 2025 |
| 9 | `ultrasound segmentation uncertainty test-time augmentation` | 15 | Pandey et al. 2022 |

## 3. Referencias añadidas al manuscrito [HV]

| Ref. | Trabajo | PMID | DOI | Para qué se cita |
|---|---|---|---|---|
| [3] | Robinson et al., J Cardiovasc Magn Reson 2019;21(1):18 | 30866968 | 10.1186/s12968-019-0523-x | Control de calidad por caso prediciendo el Dice (reverse classification accuracy) |
| [4] | Mehrtash et al., IEEE Trans Med Imaging 2020;39(12):3868–3878 | 32746129 | 10.1109/TMI.2020.3006437 | Calibración; predicción de la calidad de la segmentación |
| [5] | Pandey et al., Int J Comput Assist Radiol Surg 2022;17(5):825–832 | 35377036 | 10.1007/s11548-022-02597-0 | En ecografía, la incertidumbre (incluida la de aumentos en la prueba) no predijo bien el rendimiento |
| [6] | Varoquaux y Cheplygina, NPJ Digit Med 2022;5(1):48 | 35413988 | 10.1038/s41746-022-00592-y | Fallos metodológicos y sesgos en imagen médica con aprendizaje automático |
| [7] | Maier-Hein et al., Nat Methods 2024;21(2):195–212 | 38347141 | 10.1038/s41592-023-02151-z | Elección de métricas de validación |
| [8] | Tejani et al., Radiol Artif Intell 2024;6(4):e240300 | 38809149 | 10.1148/ryai.240300 | Lista CLAIM de comunicación de estudios de IA en imagen |
| [9] | Gallitto et al., Gigascience 2025;14:giaf036 | 40366867 | 10.1093/gigascience/giaf036 | Registro público de un modelo congelado antes de su validación externa |

## 3b. Revisión de los 48 registros de la consulta 7 (27 nov 2026) [HV]

- **Cribado por título:** 48 registros. 40 se descartaron por tema ajeno (imágenes de satélite, alimentos,
  dosimetría, síntesis de imágenes, eliminación de ruido, etiquetas ruidosas, etc.).
- **Lectura del resumen:** 8 registros (PMID 42981922, 41613551, 35976491, 39133935, 40250215, 41129432, 40934552 y
  29875312).
- **Incluidos (3):**

| Ref. | Trabajo | PMID | DOI | Para qué se cita |
|---|---|---|---|---|
| [10] | van Lente et al., Front Oncol 2025;15:1637198 | 41613551 | 10.3389/fonc.2025.1637198 | Umbral de incertidumbre elegido a partir de las distribuciones de casos correctos e incorrectos |
| [11] | Norajitra et al., Med Image Anal 2026;116:104351 | 42981922 | 10.1016/j.media.2026.104351 | Aceptar o rechazar segmentaciones con un umbral buscado para equilibrar riesgo y cobertura; el trabajo más cercano a nuestra pregunta de decisión |
| [12] | Li et al., Med Phys 2024;51(11):8317–8333 | 39133935 | 10.1002/mp.17343 | Puntuaciones de calidad sin referencia (aumentos en la prueba, dropout) en segmentaciones para medir volúmenes |

- **Leídos y no incluidos (5):** predicción del Dice con otra red (35976491) y con modelos bayesianos (40250215),
  predicción del esfuerzo de corrección manual (41129432), un desafío de calibración con varios anotadores
  (40934552) y segmentación de la placenta en ecografía 3D (29875312). Son pertinentes, pero no añaden a lo que ya
  citan [3] y [4].
- **Consecuencia:** los tres incluidos eligen el umbral a partir de datos. El manuscrito lo dice y explica por qué
  nuestra regla deriva los umbrales de la tolerancia: con pocos fallos, un umbral ajustado es inestable.

## 4. Consecuencias para el manuscrito

- **Gallitto et al. 2025 es un antecedente directo** del paso «congelar y registrar la huella antes de la prueba».
  El manuscrito no afirma ser el primero en congelar un modelo antes de validarlo; lo cita y se presenta como una
  combinación de prácticas para una pregunta más estrecha (si una bandera por caso sirve para decidir).
- **Pandey et al. 2022 refuerza un resultado negativo de la serie:** que una señal de incertidumbre no basta para
  fiarse de un caso. Coincide con la lección del ejemplo C (un fallo con las dos señales bajas).
- **Afirmación que se mantiene, con su límite:** no encontramos reglas de evaluabilidad para la pregunta de
  separación (S-1 a S-3) **en las fuentes revisadas**. Esta búsqueda no basta para decir que no existen [HIP].

## 5. Límites de esta búsqueda

- Solo PubMed. Muchos trabajos de visión por computador y aprendizaje automático (actas de MICCAI, IEEE ISBI,
  NeurIPS; arXiv) no están indexados en PubMed o lo están de forma incompleta.
- La revisión de la consulta 7 se hizo por título y, para 8 registros, por resumen; no se leyeron textos completos.
- No hubo segundo revisor.

## 6. Pendiente [PROP]

1. Repetir la búsqueda en Scopus o Web of Science (necesita acceso institucional del autor).
2. Buscar en actas de MICCAI e IEEE ISBI trabajos sobre fiabilidad de la incertidumbre en segmentación y sobre
   detección de fallos por caso.
