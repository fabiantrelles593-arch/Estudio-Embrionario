# Resultados v0.9 — integración del PDF externo, módulos de acuerdo y de color, y sensibilidad al mapa de color (n = 1)

> Solo investigación y educación. La parte de datos reales es **la misma imagen n = 1 de v0.8** (declaración de permiso no verificada; nada identificable en el repositorio) y **no valida nada**.
> Protocolo del análisis de color: `docs/PREREGISTRO_REAL2D_PILOTO.md` §8 (commit fded300, antes de aplicar la barra de color a la imagen).
> Integración del PDF: `docs/INTEGRACION_PDF_EXTERNO.md`.

## 1. Resumen honesto

* **El PDF se incorporó con verificación, no por copia.** Las 8 referencias principales existen y tratan lo que el PDF dice en lo esencial; **encontré 3 errores del PDF** (autoría y año de MEMOS; «Carnegie» para el ratón, que usa Theiler; «Dice medio» donde es mediana) y **1 contradicción interna** (rango de estadios de Yamada).
  Adopté lo que servía (etiquetas de evidencia, la regla «el individuo es la unidad», métricas de acuerdo, acuerdo entre lectores) y **no adopté** el `robustness_index`, la homología persistente ni la línea de cartílago nasal de ratón, con el motivo escrito.
* **Dos módulos nuevos, con 30 pruebas**: `geovida.agreement` (Dice, IoU, HD95 en dos convenciones, ASSD, diferencia relativa con signo, Bland–Altman) y `geovida.colorbar` (linealiza un mapa de color con la barra de la propia captura y marca los colores que no son del mapa).
  Las pruebas se escribieron antes, se vieron fallar y se comprobó con mutaciones que detectan errores reales. Con un mapa de color **inventado**, la barra recupera la intensidad con error mediano < 0.02 y bate a la luminancia por más del doble.
* **Sensibilidad al mapa de color en la imagen real: por mi propia regla, «no interpretable» — por 0.004.** La distancia mediana de los píxeles de la región a la curva de la barra fue 0.0642; el límite fijado de antemano era 0.06. No cambio la regla.
  **Descriptivamente** (sin leerlo como conclusión): la longitud nativa **no cambió** (37.568 mm con luminancia y con la barra), ni en 81 variantes de la caja de la barra; la máscara cambió en 67 píxeles (1.9 %) y el área, −1.7 %.
* **El resultado primario (37.57 mm) no se mueve.** El límite «el mapa de color no se probó en ninguna simulación» **sigue abierto**: este análisis es una sensibilidad en una imagen, no un modelo de la cadena.
* **`geovida.agreement` aún no se aplicó a ninguna comparación real**: hacen falta ≥ 2 lectores sobre varios individuos. Con un solo individuo no tiene sentido y el módulo lo dice.

## 2. Qué se hizo con el PDF (resumen; el detalle está en `docs/INTEGRACION_PDF_EXTERNO.md`)

| | |
|---|---|
| Referencias verificadas | Yamada 2010, Wong 2012, LAMA 2021, MusMorph 2022, MEMOS, Matula 2022, UniCoN 2025, Metrics Reloaded 2024 (PubMed y editoriales; texto completo no siempre) |
| Errores del PDF encontrados | MEMOS: «Rittschof 2022» → **Rolfe, Whikehart y Maga, 2023** (preprint 2022); ratón con «Carnegie ~18» → el ratón usa Theiler; Matula: «Dice medio» → **mediana** 84.44 %; Yamada: «13–23» y «14–22 (44 embriones)» a la vez |
| Cifras del PDF sin verificar | «184 etiquetas» (LAMA), «2 537 landmarks» (MusMorph), «14 volúmenes» y «E17.5» (Matula), «≈ 400 horas» (Wong), «44 embriones» (Yamada) |
| Adoptado | Etiquetas HECHO VERIFICADO / EVIDENCIA INDIRECTA / HIPÓTESIS / PROPUESTA; individuo como unidad; métricas de acuerdo; acuerdo entre lectores |
| No adoptado | `robustness_index` (sin validación; ya hay un certificado calibrado), homología persistente (sin pregunta que la pida), línea principal de cartílago nasal de ratón (sin volúmenes ni licencias) |

## 3. Módulos nuevos

### `geovida.agreement`
* `compare_masks(a, b, spacing=…)`: `b` es la referencia. Devuelve Dice, IoU, `hd95_pooled` (la convención de `geovida.measure`), `hd95_max` (el mayor de los dos percentiles 95 direccionales), `assd` (media de todas las distancias),
  `msd_mean_of_means` (la «distancia media» que ya usaba `measure`) y la diferencia relativa con signo de tamaño. **Las dos medias de distancia no coinciden cuando las superficies tienen distinto número de píxeles**, y una prueba lo muestra: quien compare una cifra con la de otra herramienta debe saber cuál convención usa.
* `bland_altman(x, y)`: sesgo, desviación de las diferencias, límites de acuerdo (± 1.96 DE), intervalos de confianza de Bland y Altman (1999) con la distribución t, y diferencia relativa media. **Exige al menos dos individuos**; el resultado recuerda que varias lecturas de un mismo individuo no son individuos.
* No valida nada por sí mismo: calcula cantidades que luego se comparan con un criterio fijado antes.

### `geovida.colorbar`
* `lut_from_bar(rgb, caja)`: mediana por fila de la barra, suavizado, remuestreo; orientación automática (el extremo más oscuro es la intensidad baja) o explícita; avisa si la luminancia de la barra no sube de forma monótona.
* `linearize(rgb, lut)`: posición del color más cercano de la curva (distancia RGB) para cada píxel, más la máscara de píxeles fuera del mapa y la distancia mediana.
* **Lo que no hace:** no corrige exposición ni viñeta, no sabe si la barra corresponde al mapa realmente aplicado a la imagen, y no convierte la posición en una magnitud física.

## 4. Sensibilidad al mapa de color en la imagen real (exploratoria; n = 1)

### 4.1 Resultados

| Cantidad | Valor |
|---|---|
| Barra (caja fijada de antemano: 7 × 60 px) | luminancia monótona en 91.8 % de los pasos; sin avisos |
| Distancia mediana de la ROI a la curva de la barra | **0.0642** (límite fijado: 0.06) → **falla por 0.004** |
| Fracción de la ROI fuera del mapa | 8.5 % (límite fijado: 20 %) |
| **Lectura por la regla fijada** | **no interpretable** |
| Longitud nativa con luminancia | 37.568 mm |
| Longitud nativa con la barra | 37.568 mm (diferencia 0.000 mm) |
| 81 variantes de la caja de la barra (±2 px arriba/abajo, ±1 px a los lados) | 37.568 mm en todas |
| Mínimo/máximo por filas de desenfoque, luminancia | 37.48–37.68 mm |
| Mínimo/máximo por filas de desenfoque, barra | 37.41–37.68 mm |
| Píxeles de la máscara (luminancia / barra) | 3 512 / 3 453 (67 distintos, 1.9 %; área −1.7 %) |
| Diferencia media entre ambas imágenes de gris en la ROI | 0.058 en escala 0–1 (Spearman 0.989) |
| Si la orientación se invirtiera (extremo claro = intensidad baja) | 52.03 mm: **la orientación importa** y «el extremo oscuro es lo bajo» es un supuesto |
| Control de calidad (barra) | no toca el borde; 1 componente grande; contraste/ruido 9.4 (con luminancia: 8.9) |

Los últimos cinco renglones (comparación de máscara, Spearman, diferencia media, orientación invertida) se calcularon **después de ver el resultado** para comprobar que no fuera un artefacto (que la imagen linealizada de verdad fuera otra): son exploratorios y no estaban en el protocolo.

### 4.2 Predicciones escritas de antemano (`PREREGISTRO_REAL2D_PILOTO.md` §8)

| Predicción | Prob. | Ocurrió |
|---|---|---|
| La barra pasa la comprobación de monotonía | 70 % | **sí** (91.8 %) |
| La ROI cumple distancia ≤ 0.06 y fuera del mapa ≤ 20 % | 45 % | no (0.0642) |
| Si es interpretable, |Δ| ≤ 1 px | 65 % | **no evaluable** (no fue interpretable) |
| El control de calidad marca algún problema | 10 % | no |
| Sigue habiendo un solo componente grande | 80 % | **sí** |

Del lado correcto 4 de 4 evaluables; Brier 0.086 (decir siempre 50 % daría 0.25). Cuatro predicciones no dicen nada sobre mi calibración.

### 4.3 Qué se puede y qué no se puede decir

* **Se puede decir (descriptivo, en esta imagen):** tratar el color con la barra en vez de con la luminancia cambió 67 píxeles del contorno y el área en −1.7 %, pero **no la longitud máxima** (CRL), ni con 81 variantes de la barra. La CRL de este piloto no depende de esa elección.
* **No se puede decir:** que el mapa de color no importe en general (una imagen; la regla de confianza no se cumplió), que la barra describa el mapa realmente aplicado, que la medida sea exacta, ni nada sobre salud. La sensibilidad mostró además que **el área es más sensible que la longitud**: si algún día se usa el área, esto cuenta.
* **Que falle por 0.004 no se redondea a «pasa».** Una distancia mediana de 0.064 en una foto de una hoja impresa (exposición distinta entre la barra y la imagen, viñeta) es plausible; no hay forma de separar eso de un mapa mal asignado con una imagen.

## 5. Desviaciones

* Al ubicar la barra vi unos valores de color de ella (no longitudes); declarado en §8 del preregistro antes de medir.
* En una prueba de `tests/test_colorbar.py` (barra invertida) comparaba el cuadro entero, y la barra misma queda invertida entre los dos cuadros por construcción; era un error mío de la prueba, no del módulo. Se corrigió antes de cualquier commit del módulo (el código no cambió).
* Los cinco renglones exploratorios de §4.1 se calcularon tras ver el resultado y se marcan como tales.

## 6. Qué no se puede concluir

* Nada clínico. Nada sobre exactitud en ecografía real. Este análisis es una sensibilidad en n = 1.
* El PDF es un plan generado con otra IA: de él se tomó lo que se pudo comprobar; no aporta datos ni resultados.

## 7. Siguiente

* **H16** (cadena de imagen): ¿puede el programa darse cuenta, a partir de la propia imagen, de que pasó por una cadena que invalida el certificado (H15: «el semáforo no se entera»)?
  **No iniciada** al momento de escribir esto.
* H17 sigue pendiente de datos seriados; `geovida.agreement` espera ≥ 2 lectores en varios individuos.
