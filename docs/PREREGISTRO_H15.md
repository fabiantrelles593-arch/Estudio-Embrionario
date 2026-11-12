# Preregistro — H15: ¿resiste el certificado una imagen que pasó por pantalla, impresión y foto? (Programa B, v0.7)

> Se escribe **después** de un piloto pequeño y **antes** de generar ninguna imagen de confirmación (semilla 20261216).
> Solo investigación y educación. **Todo es simulación**; ninguna imagen real.

## 1. Pregunta

La calibración de H13/H14 usa imágenes simuladas «limpias». Una ecografía real que llega como foto de una impresión pasó por la
compresión logarítmica del equipo, un gradiente de ganancia, la impresión, la cámara y el JPEG.

> Si se aplica esa cadena (simulada) a las mismas imágenes, ¿el certificado congelado de H14 mantiene sus falsos verdes por debajo del 10 % y su probabilidad calibrada?

## 2. La cadena (fija) — `geovida.printchain`

Parámetros por caso, muestreados de rangos fijados aquí (semillas por caso `[semilla, 7, idx]`):

| Efecto | Rango |
|---|---|
| Compresión logarítmica `y = log1p(a·x)/log1p(a)` | `a` log-uniforme en [3, 60] |
| Gradiente de ganancia con la profundidad | pendiente ±U[0, 0.25] |
| Desenfoque de cámara/impresión | σ = U[0.3, 1.0] px de la escala de trabajo |
| Ruido aditivo (rango [0, 1]) | sd = U[0.01, 0.04] |
| JPEG | calidad entera uniforme en [50, 90] |

La imagen se sube 3× antes del ruido y el JPEG y se baja con promedio de área. **No pretende ser fiel a ningún equipo ni cámara**;
es una prueba de esfuerzo con efectos del tipo correcto. El certificado sigue consultándose con el **desenfoque y tamaño declarados** (los verdaderos):
H15 aísla el efecto de la cadena sobre el error de la medida, no el de no conocer el desenfoque.

## 3. Qué se vio antes de escribir esto (declarado)

* Un ejemplo de tres imágenes (limpia, cadena típica, cadena extrema) para comprobar a ojo que la cadena produce imágenes verosímiles; no se tocó ningún rango después.
* Un **piloto** (semilla 20261217; 150 casos por tipo, 600 filas por variante; `results/summary/h15_pilot_manifest.json`) para comprobar que todo corre.
  Resultado, **exploratorio y pequeño**: datación con cadena, 7 de 70 verdes equivocados (**10.0 %**, IC 95 % 4.3–18.2 %) frente a 2 de 70 (2.9 %) sin cadena;
  ranura con cadena 1 de 100 (1.0 %) frente a 1 de 108. La longitud medida del cuerpo cambia, en mediana, +1.1 % (percentil 95: +13 %) con `smoothed_otsu`.
  No se cambió ningún criterio tras ver el piloto.
* Los modelos son los congelados de H14 (`results/summary/h14_frozen.json`), sin recalibrar.

## 4. Diseño de la confirmación (fijo)

Semilla **20261216**, mismos muestreadores que H13 (1 500 casos dentro y 400 fuera por tipo), código limpio. **Los mismos casos** se miden sin cadena (`clean`)
y con cadena (`chain`). Segmentador primario `smoothed_otsu`; `otsu` como control. Remuestreo por caso: 2 000 réplicas, semilla 20261214. «No evaluable» nunca es «no apoyada».

## 5. Hipótesis y criterios (fijos)

* **H15a — Primaria. Datación con cadena.** Cuerpo, `smoothed_otsu`, dentro de la caja, variante `chain`: falso verde entre los verdes ≤ 10 %
  (regla de H13a: *apoyada* si el límite superior del IC 95 % ≤ 10 %; *no apoyada* si el inferior > 10 %; *no concluyente* si el IC contiene el 10 %; *no evaluable* con < 30 verdes).
* **H15b — Decisión con cadena.** Igual con la ranura.
* **H15c — Calibración con cadena.** ECE ≤ 0.10 (10 cubos) para cuerpo **y** ranura (n ≥ 200 certificados cada uno); si uno no se cumple, la hipótesis no se apoya.
* **H15d — Descriptiva (sin criterio).** Cambio de la longitud medida por la cadena, mismos casos (mediana, percentiles 5 y 95, en % de la verdad y en desviaciones del modelo);
  verdes con cadena / verdes sin cadena; el falso verde sin cadena sobre los mismos casos como referencia.
* **H15e — Control `otsu` (descriptiva).** La regla de H15a/H15b aplicada a `otsu`.
* **Exploratoria:** falsos verdes por tercil de compresión logarítmica (`results/summary/h15_compression_terciles.csv`).

## 6. Lo que se hace según el resultado (decidido de antemano)

| Resultado | Qué se concluye | Siguiente paso |
|---|---|---|
| H15a **y** H15b **y** H15c apoyadas | En simulación, el certificado resiste esta cadena. | Mantener el tope de imagen real en `geovida.real2d` hasta validar con imagen real (G1 de `docs/RUTA_DE_VALIDACION_REAL.md`). |
| H15a **no apoyada** o **no concluyente** | El certificado de datación no es robusto a imágenes que pasaron por la cadena: **no debe usarse sobre fotos de impresiones**. | Nueva hipótesis (H16): inflar la incertidumbre según la cadena o exigir la imagen en bruto (DICOM). |
| H15b **no apoyada** o **no concluyente** | Igual para la decisión sobre el umbral. | Igual. |
| H15c **no apoyada** | La probabilidad declarada deja de ser confiable con cadena. | Igual; se publica la tabla de calibración. |

## 7. Predicciones escritas de antemano (después del piloto)

| Predicción | Probabilidad |
|---|---|
| H15a **apoyada** | 30 % |
| H15a **no concluyente** | 55 % |
| H15b **apoyada** | 85 % |
| H15c **apoyada** (cuerpo y ranura) | 35 % |
| Cambio mediano de la longitud del cuerpo con `smoothed_otsu` ≥ +1.0 % | 55 % |
| H15e (ranura, `otsu`) **no evaluable** (< 30 verdes) | 80 % |

## 8. Qué no se puede concluir

* Es simulación: la cadena es mía y sus rangos son supuestos. Que el certificado resista (o no) **no** dice nada de ninguna ecografía real concreta.
* El certificado se consulta con el desenfoque verdadero; con una foto real el desenfoque no se conoce (ver `docs/REAL2D_METODO.md`).
* Un resultado «apoyada» no levanta el tope de imagen real de `geovida.real2d`: eso exige imagen real con referencia (G1).

## 9. Desviaciones

(Ninguna al momento del primer commit.)
