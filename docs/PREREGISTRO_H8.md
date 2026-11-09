# Preregistro — H8: el semáforo en la estimación de crecimiento 4D (v0.3)

> Se confirma (`git commit`) **antes** de correr `scripts/run_h8.py`. El commit queda en
> `results/summary/h8_run_manifest.json`. Los cambios posteriores van solo en «Desviaciones».
> H8 usa los modelos del semáforo **congelados en H6**; no reajusta nada.

## 1. Pregunta y por qué importa

Un embrión que crece empieza por debajo de la resolución: las primeras etapas se miden mal. Si se
ajusta una tasa de crecimiento (pendiente de ln V frente al tiempo) con todas las etapas, esas
medidas malas la distorsionan. ¿Reduce esa distorsión descartar las etapas que el semáforo marca en
rojo (p < 0.50), decidiéndolo solo con la imagen?

Piloto (semilla 20261118, **no** usada aquí; 3 réplicas = 45 series por estrato; el piloto detectó y
corrigió un fallo mío: el estimador «todas las etapas» también descartaba las rojas): error mediano
absoluto de la tasa, todas las etapas → sin rojas: `global·ideal` 3.3 % → 1.2 %; `global·realistic`
4.3 % → 1.2 %; `otsu·ideal` 4.7 % → 0.9 %; `otsu·realistic` 66 % → 1.2 %; `smoothed_otsu·ideal`
18 % → 2.1 %; `smoothed_otsu·realistic` 22 % → 2.1 %. **Coste:** con `smoothed_otsu`
quedaron sin tasa evaluable (< 3 etapas no rojas) 34 y 37 de 45 series; con los otros dos
segmentadores, ninguna. (En un mensaje de progreso escribí «~40 %»: era una división mal hecha,
el valor del piloto es ~76–82 %.)

## 2. Diseño

* Series sintéticas de un espécimen que crece: 8 etapas, tamaño × 1.35 por etapa (volumen × 2.46),
  vóxel fijo (h_xy = 1), primera etapa t/h = 2.0 y última 16.3. Tasa verdadera exacta:
  3·ln 1.35 = 0.900 por etapa. Cada etapa se renderiza por separado (pseudo-tiempo transversal).
* Formas (sólidos simples, escalado isótropo): `ball`, `ellipsoid`, `oblate`, `capsule`,
  `cylinder`. Anisotropía {1, 2, 3}. Perfiles {`ideal`, `realistic`}. 30 réplicas por celda:
  5 × 3 × 2 × 30 = 900 series × 8 etapas × 3 segmentadores. Semilla base 20261119.
* Segmentadores: los tres preregistrados. La luz de cada etapa sale de `budget.adequacy` con el
  modelo congelado de su estrato (segmentador × perfil), solo con la máscara y el vóxel.
* Estimadores de la tasa (mínimos cuadrados de ln V sobre la etapa): `all` (todas),
  `no_red` (sin etapas rojas), `green` (solo verdes; descriptivo) y `oracle` (volumen verdadero;
  comprobación, debe dar la tasa exacta). Con menos de 3 etapas válidas la tasa es NaN
  («no evaluable»), nunca un número.
* Error: |tasa / 0.900 − 1|. Estratos: 6 (segmentador × perfil).

## 3. Hipótesis y criterios (fijos)

Un estrato es *evaluable* si ≥ 30 series tienen la tasa `no_red` definida. La comparación `all` frente
a `no_red` es **pareada, sobre las series con `no_red` definida**.

* **H8a — Descartar las rojas reduce el error.** En cada estrato evaluable, la mediana del error de
  `no_red` es menor que la de `all`. *Apoyada*: en todos los evaluables; *parcial*: en todos menos uno;
  *no apoyada*: si no. *No evaluable*: ningún estrato evaluable.
* **H8b — La tasa resultante es útil.** En cada estrato evaluable, la mediana del error de `no_red`
  ≤ 5 %. Misma graduación.
* **H8c — El coste es aceptable.** La fracción de series sin tasa `no_red` evaluable es ≤ 25 % en
  ≥ 4 de 6 estratos. *Parcial*: 3. *No apoyada*: ≤ 2.

Un valor no calculable es «no evaluable», nunca «no apoyada».

**Extensión descriptiva (sin veredicto):** (i) comparación con una regla simple sin semáforo
(descartar etapas con menos de 100 vóxeles de máscara; el 100 se fija ahora); (ii) error mediano con
solo las verdes; (iii) percentil 90 del error y fracción de series en que `no_red` gana a `all`.

## 4. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| H8a apoyada (en todos los estratos evaluables) | 80 % |
| H8b apoyada (≤ 5 % en todos los evaluables) | 70 % |
| H8c apoyada (≥ 4 de 6 con ≤ 25 % sin tasa) | 70 % |
| La regla de 100 vóxeles iguala o supera al semáforo (error mediano ≤) en ≥ 4 de 6 estratos | 50 % |

## 5. Qué no se puede concluir

* Es una familia exponencial con escalado isótropo y sólidos simples; no es crecimiento
  embrionario real ni formas con ramas.
* Cada etapa es un espécimen independiente; no hay seguimiento longitudinal.
* El semáforo se calibró con el mismo simulador de imagen (otras semillas y otro diseño): un acuerdo
  aquí no demuestra que valga con imágenes reales.
* Las series que nunca alcanzan resolución adecuada quedan fuera (sin tasa evaluable): el método
  se niega a medir en vez de medir mal, y eso es un coste real (H8c).

## 6. Desviaciones

(Ninguna al momento de este commit.)
