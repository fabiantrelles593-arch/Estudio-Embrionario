# Guion de la presentación v2 — «Geometría de la Vida»

Archivo: `docs/exposicion/geovida-presentacion.html` (17 láminas, funciona sin internet; ←/→ para
avanzar, **G** muestra el guion de cada lámina, clic en las tarjetas del atlas para ampliar).
Fuente editable: `docs/exposicion/v2/deck.html`; se ensambla con `python docs/exposicion/v2/build.py`.
Las imágenes de embriones reales las genera `python scripts/figure_atlas.py` a partir de datos CC BY
(fuera de git). Las figuras (`docs/exposicion/img/`) y el HTML ensamblado tampoco están en git: se
reconstruyen en local con esos dos comandos, con los datos descargados según `docs/GUIA_DATOS_REALES.md`. El laboratorio interactivo anterior (`exposicion-geovida.html`) se abre desde la lámina 13.

Duración sugerida: 15 minutos más preguntas.

| Láminas | Bloque | Tiempo |
|---|---|---|
| 1–2 | Portada y propósito: medir, certificar, rastrear | 2 min |
| 3–4 | Importancia: cifras del mundo (OMS) y del Perú (CDC-MINSA) | 2 min |
| 5 | Fundamento: organogénesis, modelo ratón, estadios | 1 min |
| 6 | Valor: una diferencia en la imagen no siempre es del embrión | 1,5 min |
| 7 | Cómo funciona: las seis etapas | 1,5 min |
| 8–9 | Atlas de especímenes y ficha de un embrión real | 2 min |
| 10–12 | Resultados con datos reales: P3 piloto, H11 en curso, ONTO-MAP | 2,5 min |
| 13 | La prueba: validación con verdad conocida (y laboratorio en vivo) | 1 min |
| 14 | Calidad y niveles de validación | 0,5 min |
| 15 | Ruta hacia el uso clínico (DIGEMID) | 1 min |
| 16–17 | Límites y cierre | 1 min |

## Cifras y sus fuentes (no decir otras)

| Cifra | Fuente |
|---|---|
| ≈ 8 millones de bebés nacen cada año con un defecto congénito; casi 8 % de las muertes de menores de 5 años | OMS, informe técnico de junio de 2026 sobre tamizaje neonatal y defectos congénitos, citado por News-Medical (24 jun 2026) |
| 240 000 recién nacidos mueren al año por trastornos congénitos en sus primeros 28 días; 170 000 más entre 1 mes y 5 años; 9 de 10 casos graves en países de ingresos bajos y medios | OMS, nota descriptiva «Congenital disorders», 27 feb 2023 |
| Perú: malformaciones congénitas, 17 % de las muertes neonatales (3.ª causa, tras prematuridad 27 % y asfixia 18 %; infecciones 15 %), acumulado hasta 2021 | CDC-MINSA, presentación en la MCLCP, 15 nov 2022 (texto citado por el buscador; el PDF es una imagen y no se pudo extraer aquí) |
| «El software autónomo se considera dispositivo médico activo» | DIGEMID, DS 003-2020-SA, reglamento de dispositivos médicos (Ley 29459) |

La cifra de la exposición anterior («16,4 % de las muertes neonatales de 2024», citada como CDC-MINSA
vía MCLCP 2025) **no se pudo volver a encontrar** el 16 nov 2026, así que la v2 no la usa.

## Mensajes clave

1. Las anomalías congénitas matan a cientos de miles de niños al año; en el Perú son la 3.ª causa de
   muerte neonatal. Se originan cuando se forman los órganos.
2. Para estudiarlas se compara la forma de embriones en imágenes; una diferencia en la imagen puede
   venir del instrumento. Geometría de la Vida pone un certificado de confianza a cada medida.
3. Ya trabaja con embriones reales de ratón (micro-CT, ecografía 3D, landmarks) y encontró problemas en
   datos publicados. El destino es clínico; el camino (ética, validación externa, DIGEMID) está trazado.

## Frases que no conviene decir

«Diagnostica», «ya se usa en hospitales», «validado» a secas (es validado en sintético), «primero del
mundo» (no lo sabemos), «predice cómo será el bebé». Con datos reales: «acuerdo», no «exactitud».

## Preguntas probables

* **¿Se usa ya en pacientes?** No. Está en etapa preclínica. El uso clínico exige comité de ética,
  validación externa y registro sanitario en DIGEMID, porque en el Perú el software autónomo se
  considera dispositivo médico.
* **¿Por qué ratones?** Son el modelo estándar del desarrollo embrionario (IMPC) y sus datos son
  públicos y con licencia; permiten probar el método sin tocar datos de personas.
* **¿Qué encontraste con datos reales?** Que las segmentaciones publicadas de MusMorph están
  interpoladas (28–32 % de vóxeles mezclados) y que 4 de 20 están desplazadas medio milímetro. Y un
  resultado negativo en ONTO-MAP. Los veredictos de P3 y H11 aún no existen.
* **¿Cómo sabes que el certificado funciona?** Con 50 400 imágenes sintéticas nuevas, en verde se
  equivocó entre 0,4 y 2,6 % de las veces (criterio previo: menos de 10 %).
* **¿Lo hiciste tú?** Planteé el problema, dirigí las decisiones y revisé los resultados; el código se
  desarrolló con asistencia de inteligencia artificial (Claude), declarado en el repositorio.
