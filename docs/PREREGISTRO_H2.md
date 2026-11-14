# Preregistro — Experimento H2 (banco de pruebas 4D sintético, v0.1)

> Se confirma en git **antes** de ejecutar `scripts/run_h2.py`. Cambios
> posteriores solo en "Desviaciones".

## 1. Aclaración sobre qué es "4D" aquí

No se sigue a un embrión en el tiempo. Cada espécimen se mide una sola vez y se
asigna a una **etapa nominal**; la dimensión temporal es **pseudo-tiempo
transversal**. El "eje t" de formatos tipo OME-NGFF no debe usarse para
codificar etapas de especímenes distintos como si fueran un seguimiento.

## 2. Pregunta

Con etapas nominales y error de estadificación (el tiempo verdadero de un
espécimen difiere de su etapa), ¿cuánto sesga y cuánto engaña (cobertura de IC)
la trayectoria media recuperada, para qué tamaños de muestra por etapa, y
cuándo ayuda corregirlo?

## 3. Modelo generativo (unidad de tiempo = intervalo entre etapas)

* K = 7 etapas nominales k = 0…6. Espécimen i en la etapa k tiene tiempo
  verdadero τ = k + ε, ε ~ N(0, σ_s²).
* Rasgo observado: Y = f(τ) · (1 + u) · (1 + e), u ~ N(0, 0.08²) (variación
  biológica entre individuos), e ~ N(0, m²) (error de medición relativo).
* Tres trayectorias verdaderas f (positivas):
  `growth` = exp(0.5 τ); `saturating` = 0.9 − 0.5·exp(−τ/2);
  `switch` = 0.2 + 0.6 · logística((τ − 3)/0.7) (transición morfológica
  abrupta entre las etapas 2 y 4).

## 4. Diseño

| Factor | Niveles |
|---|---|
| σ_s (error de estadificación) | 0, 0.1, 0.25, 0.5 |
| n por etapa | 1, 3, 5, 10, 20 |
| m (error de medición, ≈ error metrológico de H1) | 0, 0.02, 0.05 |
| Trayectoria | growth, saturating, switch |
| Estimador | `stage_mean`; `spline`; `spline_corrected` (σ supuesto = σ_s) |
| σ supuesto / σ_s (solo `spline_corrected`) | 0.5, 1, 2 |

500 réplicas Monte Carlo (cohortes independientes) por celda; bootstrap
percentil de 200 remuestreos de especímenes dentro de cada etapa; semilla
derivada de la celda. Cobertura no definida con n = 1 (se informa NaN).

## 5. Métricas (por celda)

Sesgo relativo por etapa y su máximo en valor absoluto (**max-sesgo**);
RMSE relativo integrado (**IRMSE**); fracción del MSE debida al sesgo²
(**bias2_share**); cobertura del IC bootstrap al 95 % (por etapa y media).

## 6. Hipótesis confirmatorias y criterios de falsación

Referencia de "error metrológico de H1": 5 % (criterio V_ok).

* **H2a (el sesgo existe solo donde hay curvatura)**: con `stage_mean`,
  σ_s = 0.5, n = 20, m = 0.02: max-sesgo > 5 % para `switch` y max-sesgo < 5 %
  para `growth`. *Falsada si* cualquiera de las dos desigualdades falla.
* **H2b (más especímenes, más engañoso)**: para `switch`, `stage_mean`,
  σ_s ≥ 0.25, m = 0.02, la cobertura media del IC al 95 % con n = 20 es
  **menor** que con n = 3, y es < 90 % con n = 20. *Falsada si* no se cumplen
  ambas.
* **H2c (corrección)**: para `switch`, σ_s = 0.5, n = 20, m = 0.02 y σ
  supuesto correcto, `spline_corrected` reduce el max-sesgo en ≥ 50 % respecto de
  `stage_mean` **y** de `spline`. *Falsada si* no. Robustez (descriptiva, sin
  umbral previo): se informa qué pasa con σ supuesto ×0.5 y ×2.
* **H2d (n pequeño: domina la varianza)**: para σ_s ∈ {0.25, 0.5}, n ∈ {1, 3},
  m = 0.02 y `stage_mean`, bias2_share < 0.5 en las tres trayectorias.
  *Falsada si* alguna celda lo excede. (Corrige la formulación original de H2:
  con n pequeño el error total supera 5 % trivialmente por varianza; la
  cuestión sustantiva es qué parte es sesgo.)

## 7. Predicciones escritas antes de ver datos

1. `growth` y `saturating` tendrán max-sesgo < 2 % incluso con σ_s = 0.5
   (poca curvatura relativa por intervalo); `switch` > 10 %.
2. La cobertura del IC de `stage_mean` en `switch` caerá por debajo de 60 % con
   n = 20 y σ_s = 0.5 (la etapa de la transición).
3. `spline_corrected` con σ correcto tendrá menor sesgo pero **mayor
   varianza** (la deconvolución amplifica ruido), sobre todo con n ≤ 3; puede
   perder en IRMSE frente a `stage_mean` en n pequeño.
4. Con σ supuesto ×2, el corregido sobrecorrige y puede empeorar el sesgo.

## 8. Acople metrología → trayectoria (demostración, no confirmatoria)

Si un espécimen crece a vóxel fijo, su t/h aumenta con la etapa y el sesgo de V
medido (H1) cambia con la etapa: el *crecimiento aparente* queda distorsionado
solo por la resolución. `measurement_bias_function` toma el sesgo mediano de H1
y `scripts/run_h2.py` lo aplica a la trayectoria `growth` (volumen ∝ exp(0.5 τ)) con
t/h = 2 en la etapa 0 y tamaño lineal coherente con ese volumen:
t/h(k) = 2·exp(0.5 k / 3). Se informa la tasa de crecimiento aparente (pendiente
de log V medido frente a la etapa) frente a la verdadera (0.5), para los
estratos (global, ideal), (otsu, realistic) y (smoothed_otsu, realistic) de la
elipsoide con vóxel isótropo.

## 9. Limitaciones declaradas

Diseño balanceado y transversal; ε y u normales e independientes; sin
heterocronía sistemática por camada; tres trayectorias elegidas por mí;
σ_s se supone conocido (en la práctica exige un estudio de estadificación
replicada). Sin datos reales.

## 10. Desviaciones

*(ninguna al momento de la firma)*
