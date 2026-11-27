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
| 7 | `segmentation quality estimation without ground truth deep learning` | 48 | 0 en esta ronda (sin revisar uno a uno; ver §5) |
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
- La consulta 7 devolvió 48 registros que no se revisaron uno a uno.
- No hubo segundo revisor.

## 6. Pendiente [PROP]

1. Repetir la búsqueda en Scopus o Web of Science (necesita acceso institucional del autor).
2. Revisar los 48 registros de la consulta 7.
3. Buscar en actas de MICCAI e IEEE ISBI trabajos sobre fiabilidad de la incertidumbre en segmentación y sobre
   detección de fallos por caso.
