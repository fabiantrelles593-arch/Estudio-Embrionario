# Resultados v0.6 — Programa B: biometría fetal temprana con certificado de incertidumbre (H13) y su compuerta (H14)

> Solo investigación y educación. **Todo es simulación**: fantomas 2D sintéticos, ninguna ecografía de
> personas ni de animales. Nada de esto es evidencia clínica. Reglas fijadas en `docs/PREREGISTRO_H13.md`
> (commit 0932c51, antes de calibrar). Modelos congelados: `results/summary/h13_frozen.json`, SHA-256
> `60943f48…315b0a` (commit b27443f). Confirmación con semilla 20261213, código limpio en el commit 9d14b15.
> **H14** (§8): reglas en `docs/PREREGISTRO_H14.md` (commit 59f0f8d, escrito tras ver H13 y antes de generar
> ninguna imagen de confirmación de H14); modelos con compuerta `results/summary/h14_frozen.json`, SHA-256
> `676c7c84…b7aeb97` (commit faf885e); confirmación con semilla nueva 20261215, código limpio en faf885e.

![H13](figures/h13_certificate.png)

## 1. Resumen honesto

* **Los cuatro criterios confirmatorios se cumplieron en el agregado**, con `smoothed_otsu` y dentro de la caja
  calibrada. Mi predicción para esto era más pesimista (ver §5).
* **Pero el agregado esconde un estrato donde el certificado de la ranura no es fiable**: con función de
  dispersión de más de 3.5 px hay 18.5 % de falsos verdes (15 de 81; IC 95 % 9.9–27.2 %). Es una estratificación
  **posterior** al preregistro, así que es exploratoria; aplicando la regla de H13 a ese estrato daría
  «no concluyente» (el límite inferior, 9.9 %, queda justo bajo el 10 %), pero la tasa es la peor de todo el estudio.
* **El control `otsu` falla en la ranura** (30.3 % de falsos verdes; IC 23.2–37.7 %): con ese segmentador el
  certificado no se puede usar.
* **Una datación certificada no es una datación correcta.** En mediana la medida pone el 0.9 % de la varianza de
  la edad; el resto es la variación biológica de la fórmula (unos 3 días a 45 mm).

## 2. Resultados confirmatorios (reglas de antemano)

| Hipótesis | Resultado | Veredicto |
|---|---|---|
| **H13a** Datación: falso verde ≤ 10 % | 755 verdes de 1 500; **0.53 %** [0.13–1.10] | **apoyada** |
| **H13b** Decisión: falso verde ≤ 10 % | 995 verdes de 1 500; **1.81 %** [0.99–2.69] | **apoyada** |
| **H13c** ECE ≤ 0.10 | cuerpo **0.081** [0.066–0.098] (n = 1 487); ranura **0.036** [0.026–0.049] (n = 1 252) | **apoyada** |
| **H13d** Fuga de la guardia ≤ 5 % | cuerpo 0/400 [0–0]; ranura 4/400 = **1.0 %** [0.25–2.0] | **apoyada** |
| **H13e** Frente a un operador (descriptiva) | ver §4 | sin criterio |
| **H13f** Peso de la medida en la datación (descriptiva) | ver §4 | sin criterio |

Matices que importan:

* **H13c**: en el cuerpo el ECE queda cerca del límite (0.081; el IC llega a 0.098). El error es de **pesimismo**:
  en probabilidades de 0.15 a 0.75 el acierto observado es mayor que el dicho (panel A). Es un error del lado seguro,
  pero cuesta cobertura: 450 de 1 500 casos de cuerpo quedaron en amarillo y 295 en rojo.
* **H13d**: sin guardia (un modelo que lleva el caso al borde de la caja y predice ahí) la ranura habría tenido
  **11.6 %** de falsos verdes fuera de lo calibrado (34 de 293), el cuerpo 1.1 % (2 de 187). La guardia importa
  sobre todo en la ranura. De los 4 verdes que se filtraron, 1 estaba equivocado (n = 4: no informa).
* **Sin certificado dentro de la caja**: cuerpo 13 casos, ranura 248 (la medida arrojó un `n` fuera de lo calibrado).
  Cuentan como amarillo.
* Los casos se muestrearon log-uniformes dentro de la caja. **La tasa de falso verde depende de cómo se reparten
  las condiciones reales**: si el uso se concentra en PSF grande, el agregado engaña.

## 3. Lo que falla (hallazgos no preregistrados, exploratorios)

**Estratos por ancho de la función de dispersión** (`results/summary/h13_strata.csv`, `smoothed_otsu`):

| Tipo | PSF ≤ 2 px | 2 – 3.5 px | > 3.5 px |
|---|---|---|---|
| Cuerpo | 0.6 % (508 verdes) | 0.5 % (219) | 0.0 % (28) |
| Ranura | 0.3 % (581) | 0.3 % (333) | **18.5 % (81)** [9.9–27.2] |

**Control `otsu`** (mismas reglas, solo informativo): cuerpo 108 verdes, 0 equivocados; ranura 155 verdes, **30.3 %**
equivocados. De los 1 500 casos de ranura dentro de la caja, 1 238 no recibieron certificado.

**Mecanismo (hipótesis apoyada por las 15 filas de `results/summary/h13_wrong_greens.csv`, no probada):**

1. En esas celdas la ranura casi no se halla: la fracción de medidas dentro de la mitad de la verdad es de 9–42 %
   con PSF = 5 px (`results/summary/h13_usable_rate_by_cell.csv`). El error es bimodal, y un modelo de sesgo y
   desviación normal lo describe mal.
2. El `n` del certificado sale de **la medida**. En 4 de los 15 casos la segmentación devolvió un fragmento de ≈ 1 mm
   (n medido 11–14 px, con n verdadero ≈ 45): el modelo se consulta en la celda equivocada, donde la desviación es
   pequeña, y declara verde con p = 1.0.
3. En los otros 11, la medida sobreestima; el modelo resta el sesgo negativo de la celda (−0.6 a −2.5 mm) y cree que
   el valor verdadero está lejos del umbral, cuando estaba cerca (2.3–3.3 mm).

La guardia protege contra el `n` que se sale de la caja, **no contra un `n` mal estimado dentro de ella**.

## 4. Descriptivas (sin criterio)

* **H13e — NT simulada frente a repetibilidad humana publicada** (error tras corregir el sesgo modelado; 0.25 mm y
  0.40 mm son la desviación de una sola medición, a partir de PubMed 10895448): en los 995 verdes la mediana del error
  absoluto es 0.058 mm, el percentil 95 es 1.32 mm, el 84 % queda dentro de 0.25 mm y el 89 % dentro de 0.40 mm. La
  cola es pesada: cerca de 1 de cada 9 verdes tiene un error corregido mayor que 0.40 mm (aunque el lado del umbral casi
  siempre sale bien porque esos casos están lejos del umbral). **No se puede decir «mejor que un operador»**: la tarea,
  la imagen, el píxel y la forma son otros.
* **H13f — peso de la medida en la datación** (1 487 certificados): mediana 0.9 %, percentil 90 de 30 %; en 3.8 % de los
  casos la medida pone más de la mitad de la varianza de la edad.

## 5. Mis predicciones

| Predicción | Probabilidad | Ocurrió |
|---|---|---|
| H13a apoyada | 85 % | sí |
| H13b apoyada | 55 % | sí |
| H13c apoyada | 45 % | **sí** (lado equivocado) |
| H13d apoyada en cuerpo / ranura | 90 % / 35 % | sí / **sí** (lado equivocado en la ranura) |
| El modelo sin guardia supera 10 % de falso verde en la ranura | 60 % | sí (11.6 %) |
| Mediana del error de la NT en los verdes < 0.25 mm | 80 % | sí (0.058 mm) |
| Mediana de la parte de varianza de la medida < 0.25 | 90 % | sí (0.009) |

Ocho de ocho ocurrieron; 6 de 8 del lado correcto; **Brier medio 0.146**. Fui más pesimista de lo que el simulador
justificaba. No se interpreta como que el método sea mejor de lo pensado: los criterios agregados son más fáciles de
cumplir que los estratos, y el simulador es mío.

## 6. Qué se puede concluir y qué no

**Sí (en este simulador):** con `smoothed_otsu`, dentro de la caja calibrada y repartiendo las condiciones como aquí, el
certificado de datación y el de decisión tuvieron falsos verdes de 0.5 % y 1.8 %, y su probabilidad estuvo razonablemente
calibrada; la guardia rechazó 99 % de lo no calibrado.

**No:**

* Nada sobre ecografía real. El moteado, la relación PSF–píxel y la ranura limpia son supuestos sin validar.
* Nada de la ranura con PSF > 3.5 px, ni de `otsu`.
* Nada sobre exactitud del grosor en milímetros: una cola de errores > 0.4 mm convive con un lado del umbral casi siempre bien.
* El umbral de 3.0 mm es ilustrativo; no se evaluó rendimiento de cribado.
* Una datación certificada no es una datación correcta: domina la variación biológica.

## 7. Siguiente paso (escrito tras H13; la primera mitad se ejecutó como H14, §8)

El mecanismo apunta a una corrección concreta, que **es otra hipótesis y exige otro preregistro y otra semilla**:
una compuerta de «tasa de medidas utilizables» por celda (rechazar donde la medida suele fallar) y un `n` que no dependa
de la medida que se está certificando. Después, ecografía real de animal con referencia (H11/H12R) cuando haya volúmenes.

## 8. H14 — la compuerta de «tasa de medidas utilizables» (confirmación con semilla 20261215)

La compuerta se diseñó **mirando los datos de H13**; por eso se probó con casos nuevos (los mismos casos se certifican
con el modelo de H13, `ungated`, y con el de H14, `gated`). Todo sigue siendo simulación.

| Hipótesis | Resultado | Veredicto |
|---|---|---|
| **H14a** Ranura, PSF > 3.5 px: verdes equivocados por caso ≤ 2 % | con compuerta **0 de 321** [0–0]; sin compuerta 5 de 321 = 1.56 % [0.31–3.11] | **apoyada** (ver «Lo que este resultado no dice») |
| **H14b** Cobertura retenida (≥ 80 % ranura y ≥ 95 % cuerpo) | ranura 864 de 984 = **87.8 %**; cuerpo 758 de 758 = **100 %** | **apoyada** |
| **H14c** El agregado no se rompe (falso verde ≤ 10 %) | cuerpo **0.26 %** [0–0.66]; ranura **0.58 %** [0.12–1.16] | **apoyada** |
| **H14d** Control `otsu`, ranura, todos los PSF | con compuerta **0 de 1 500**; sin compuerta 3.87 % por caso | **apoyada** |
| **H14e** Guardia: fuga fuera de la caja ≤ 5 % | cuerpo 0/400, ranura 0/400 | **apoyada** |

Mis cinco predicciones (80 %, 70 %, 95 %, 50 %, 85 %) ocurrieron; **Brier medio 0.081**. Es un puntaje bueno sobre cinco
puntos y un simulador mío: no demuestra que mi calibración sea buena.

**Lo que este resultado no dice (leer antes de citar H14a):**

* **H14a se cumple por construcción.** La compuerta cerró los 321 casos del estrato: no emitió ni un verde, así que no
  pudo equivocarse. El criterio lo fijé de antemano y se cumplió, pero un certificado que no certifica nada ahí no
  «arregla» la medida: **se niega a opinar**. Lo informativo es H14b (el costo) y la comparación de abajo.
* **El fallo, en casos nuevos, fue menor que en H13.** Sin compuerta, el estrato PSF > 3.5 dio 5 verdes equivocados de
  76 (**6.6 %** de los verdes, Wilson 2.8–14.5 %), frente a 15 de 81 (**18.5 %**, 9.9–27.2 %) en H13. Y por caso, sin
  compuerta, el criterio del 2 % habría quedado «no concluyente» (IC 0.31–3.11 %). Los intervalos se tocan; mi lectura
  es que elegí el estrato **después** de ver que era el peor, y esa selección infla la cifra («maldición del ganador»),
  pero no puedo separar eso del azar con estos datos. **El problema era real, pero probablemente más chico de lo que dijo H13.**
* **Qué hizo la compuerta (exploratorio, no preregistrado, mismos casos):** en la ranura quitó 120 verdes: 76 del
  estrato ancho (5 equivocados) y 44 del estrato 2–3.5 px (0 equivocados: costo puro). Entre los verdes quitados el 4.2 % estaba
  equivocado (5/120, 1.8–9.4 %); entre los que dejó, el 0.58 % (5/864). Es decir, filtra en la dirección correcta, pero con
  un costo que no se ve en el agregado: en el estrato 2–3.5 px los casos sin certificado pasaron de 37 a 170 de 539
  (31.5 %), y 26 casos que eran rojos pasaron a amarillo (se perdió la decisión «bajo el umbral»).
* **Los 5 verdes equivocados que quedan** (3 con PSF ≤ 2, 2 con PSF 2–3.5; el cuerpo tiene 2 más) son el nivel de fondo del
  método en este simulador, no un fallo de la compuerta. Siguen por debajo de los criterios de 10 % y 2 %, pero no son cero.
* **`otsu` con compuerta no emite ningún verde en la ranura:** es seguro en el sentido de no equivocarse, y vacío en el sentido
  de que no sirve para nada. No es una prueba de que `otsu` se haya vuelto fiable.

**Descriptivas (sin criterio), mismos casos** — error del grosor tras corregir el sesgo modelado, solo en los verdes de la ranura:

| | verdes | mediana | percentil 95 | dentro de 0.25 mm | dentro de 0.40 mm |
|---|---|---|---|---|---|
| Sin compuerta | 984 | 0.060 mm | 1.232 mm | 83.7 % | 88.9 % |
| Con compuerta | 864 | 0.050 mm | **0.286 mm** | 93.4 % | 97.8 % |

La cola pesada que señalaba H13e (percentil 95 de 1.2 mm) venía del estrato de PSF ancha; sin él, el percentil 95 baja a 0.29 mm.
Sigue sin poder decirse «mejor que un operador» (la tarea, la imagen, el píxel y la forma son otros). La parte de varianza
de la edad que pone la medida (H13f) es parecida a la de H13 (mediana 1.0 % frente a 0.9 %, percentil 90 de 26 % frente a 30 %,
3.5 % frente a 3.8 % de casos con más de la mitad) y es idéntica con y sin compuerta: la compuerta solo afecta a la ranura y la datación usa el cuerpo.

**Lo que sigue sin resolverse.** La compuerta consulta la tasa utilizable en el `n` **medido** y en el PSF **declarado**: trata
el síntoma (dónde falla la medida) pero no la causa (que `n` salga de la medida que se certifica). Con casos de PSF ancha el
síntoma está bien cubierto en este simulador; con otra mezcla de condiciones, otra forma de fallar o ecografía real, no hay razón
para pensar que el mismo umbral 0.90 y la misma definición de «utilizable» (|error| ≤ 0.5·n) sirvan.

**Qué se puede concluir de H14.** En este simulador, con casos nuevos, la compuerta eliminó el estrato que fallaba a un costo de
12 % de los verdes de la ranura y sin tocar el cuerpo. **No** se concluye nada sobre ecografía real, sobre la NT (el «slot» es
un bloque limpio con una ranura oscura), ni que el umbral de 3.0 mm sea clínico.

## 9. Siguiente paso (tras H14)

Según la tabla decidida de antemano (H14a y H14b apoyadas): mantener la compuerta en el certificado y **probar con ecografía real de
animal con referencia** (H11/H12R, pendientes de volúmenes del usuario). La limitación conocida que queda es la circularidad de `n`;
la hipótesis natural siguiente (H15, aún sin preregistrar) es estimar `n` con una referencia independiente de la medida
(por ejemplo, el tamaño del objeto desde la escala declarada del equipo o una segmentación gruesa independiente) y comprobar si
con eso la compuerta se vuelve innecesaria o menos costosa.
