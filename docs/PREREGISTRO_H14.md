# Preregistro — H14: ¿una compuerta de «tasa de medidas utilizables» arregla el fallo de la ranura con PSF ancha? (Programa B, v0.6)

> Se escribe **después** de ver los resultados de confirmación de H13 y **antes** de generar ninguna imagen de
> confirmación de H14 (semilla 20261215). **La compuerta se diseñó mirando los datos de H13**, por eso H14 se prueba
> con casos nuevos. Solo investigación y educación. **Todo es simulación**; ninguna imagen real.

## 1. Pregunta

`docs/RESULTADOS_V06.md` §3 mostró que, pese a pasar los criterios agregados, el certificado de la ranura daba
**18.5 % de falsos verdes** [9.9–27.2] cuando el ancho de la función de dispersión superaba 3.5 px (15 de 81 verdes), y
dio la hipótesis de mecanismo: en esas condiciones la ranura casi no se halla (9–42 % de medidas utilizables con
PSF = 5 px) y el `n` del certificado, calculado de la medida, consulta la celda equivocada.

> Si el certificado se niega a dar verde donde la **calibración** dice que la medida suele fallar, ¿desaparecen los
> verdes equivocados de ese estrato sin vaciar el resto?

## 2. Qué se vio antes de escribir esto (declarado)

* La compuerta se eligió **tras** mirar los datos de confirmación de H13. En esos datos (comprobación retrospectiva,
  exploratoria) una compuerta de tasa utilizable ≥ 0.90 habría cerrado los 15 verdes equivocados del estrato
  PSF > 3.5 (de 81 verdes quedaba 1) y conservado el 87 % de los verdes de la ranura (995 → 869); no habría tocado el
  cuerpo. Con ≥ 0.80 quedaban 14 verdes en el estrato, 0 equivocados, y 92 % de retención; con ≥ 0.95, 0 y 83 %.
  Los tres umbrales se miraron; **se fija 0.90 de antemano** por coincidir con el umbral de verde del certificado.
* No se miró retrospectivamente qué pasa con el control `otsu` bajo la compuerta.
* La compuerta **no** corrige que el `n` salga de la medida; solo cierra donde la calibración ve que la medida falla.

## 3. Diseño (fijo)

* **Tasa de medidas utilizables** de una celda de calibración = fracción de repeticiones con |error| ≤ 0.5·n (la medida
  queda a menos de la mitad de la magnitud verdadera). Se interpola en (ln n, ln fwhm_px) como el sesgo y la desviación.
* **Compuerta**: si la tasa interpolada en (n medido, fwhm declarado) es < **0.90** (o no hay tabla), el certificado no se
  emite: amarillo con motivo «tasa de medidas utilizables baja», nunca verde.
* **Modelos**: `results/summary/h14_frozen.json`, derivados de la **misma** calibración de H13 (semilla 20261212; ninguna
  imagen nueva). El script comprueba que sesgo y desviación coinciden con `h13_frozen.json` y solo se añade la compuerta.
  Se commitea antes de confirmar.
* **Confirmación**: semilla **20261215**, mismos muestreadores que H13 (1 500 casos dentro y 400 fuera por tipo), código
  limpio. **Los mismos casos** se certifican con el modelo de H13 (sin compuerta, `ungated`) y con el de H14 (`gated`).
* Segmentador primario `smoothed_otsu`; `otsu` como control.

## 4. Hipótesis y criterios (fijos)

Remuestreo por caso: 2 000 réplicas, semilla 20261214. «No evaluable» nunca es «no apoyada».

* **H14a — Primaria. El estrato difícil deja de dañar.** Ranura, `smoothed_otsu`, dentro de la caja, PSF > 3.5 px, con
  compuerta: **verdes equivocados por caso** (denominador = todos los casos del estrato; no los verdes, que casi se
  acaban). *Apoyada*: límite superior del IC 95 % ≤ 2 %. *No apoyada*: límite inferior > 2 %. *No concluyente*: el IC
  contiene el 2 %. *No evaluable*: < 100 casos. Se informa la tasa sin compuerta sobre los mismos casos (en H13: 4.5 %).
* **H14b — Costo de cobertura.** Verdes con compuerta / verdes sin compuerta, mismos casos, dentro de la caja,
  `smoothed_otsu`. *Apoyada* si ≥ 80 % en la ranura **y** ≥ 95 % en el cuerpo (estimaciones puntuales).
* **H14c — La compuerta no rompe el agregado.** Las reglas de H13a y H13b (falso verde ≤ 10 % entre verdes, IC superior)
  con el modelo con compuerta, por tipo.
* **H14d — Control `otsu`.** Igual que H14a pero con `otsu`, ranura, dentro de la caja, todos los PSF (en H13: 3.1 % por
  caso, 47 de 1 500).
* **H14e — La guardia sigue igual.** Tasa de fuga fuera de la caja ≤ 5 % (regla de H13d), por tipo, con compuerta.
* **Descriptivas** (sin criterio): verdes equivocados por caso y casos sin certificado por tramo de PSF, con y sin
  compuerta (`results/summary/h14_strata.csv`); H13e y H13f con compuerta.

## 5. Lo que se hace según el resultado (decidido de antemano)

| Resultado | Qué se concluye | Siguiente paso |
|---|---|---|
| H14a **apoyada** y H14b **apoyada** | En este simulador la compuerta cierra el estrato que fallaba a un costo de cobertura aceptable. | Mantenerla en el certificado; probar con ecografía real de animal. |
| H14a **apoyada**, H14b **no apoyada** | Arregla el daño pero deja el certificado casi vacío en la ranura. | Buscar un criterio de compuerta menos conservador (nueva hipótesis). |
| H14a **no apoyada** / **no concluyente** | La compuerta por tasa utilizable no basta: el `n` estimado de la medida sigue engañando. | Estimar `n` con una referencia independiente de la medida (nueva hipótesis). |
| H14c **no apoyada** | La compuerta rompió lo que funcionaba. | Se descarta. |

## 6. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| H14a **apoyada** | 80 % |
| H14b **apoyada** (≥ 80 % ranura y ≥ 95 % cuerpo) | 70 % |
| H14c **apoyada** | 95 % |
| H14d **apoyada** (otsu) | 50 % |
| H14e **apoyada** | 85 % |

## 7. Qué no se puede concluir

* Es simulación; la compuerta se ajustó **con los datos de H13**, de modo que H14 mide si el arreglo se sostiene con casos
  nuevos del **mismo simulador**, no si sirve en ecografía real.
* El umbral 0.90 y la definición de «utilizable» (|error| ≤ 0.5·n) son decisiones de diseño, no resultados.
* La compuerta trata el síntoma (dónde falla la medida), no la causa de fondo (que `n` salga de la medida).
* Un verde con compuerta sigue sin ser una validación clínica; el umbral de 3.0 mm sigue siendo ilustrativo.

## 8. Desviaciones

Ninguna en la ejecución: congelado en el commit faf885e, confirmación con semilla 20261215 sobre ese mismo commit (código limpio), análisis con
`scripts/analyze_h14.py` ejecutado una vez. Los cálculos de `docs/RESULTADOS_V06.md` §8 sobre verdes quitados frente a conservados, la
comparación con H13 y el error de los verdes con y sin compuerta son **exploratorios** (no estaban en este preregistro).
