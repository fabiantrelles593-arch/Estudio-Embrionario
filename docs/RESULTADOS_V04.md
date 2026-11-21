# Resultados de v0.4: el instrumento certifica la topología y se niega cuando no puede

Diez hipótesis (H9b–H9g y H10a–H10d), con criterios y predicciones confirmados en git antes de
correr (`PREREGISTRO_H9_H10.md`) y el modelo congelado en `c7661e5` antes de los barridos de
confirmación. Todo es sintético: describe el instrumento de medida, no biología. Las dos
hipótesis primarias son **H9d** y **H10b**.

| Hipótesis | Qué dice | Veredicto |
|---|---|---|
| H9b | El semáforo topológico discrimina (AUC ≥ 0.85 en ≥ 5 de 6 estratos) | **Parcial** (4 de 6) |
| H9c | Está calibrado (ECE ≤ 0.10 en ≥ 5 de 6) | Apoyada (6 de 6) |
| **H9d** (primaria) | Verde falso ≤ 10 % en todos los estratos | **Apoyada** (6 de 6; máximo 7.0 %) |
| H9e | Mejora a la profundidad global | Apoyada (6 de 6) |
| H9f | Vale en formas nunca vistas (mancuerna y copa) | Apoyada (6 de 6; máximo 7.8 %) |
| H9g | Aguanta imágenes desplazadas sin guardia | **No apoyada** (2 de 8 estratos evaluables incumplen) |
| H10a | El semáforo de volumen de H6 se rompe fuera de dominio | Apoyada (7 de 12 estratos) |
| **H10b** (primaria) | La guardia lo impide | **Apoyada** (10 de 12 estratos rechazados; los 2 que conservan verdes quedan en ≤ 4.1 %) |
| H10c | La guardia cuesta poco en dominio | Apoyada (conserva ≥ 95.2 % de las verdes) |
| H10d | El eje de escala aporta | Apoyada (6 de 6) |

## H9 — Semáforo de topología

**Qué es.** Un modelo logístico con ridge que convierte siete variables medidas en la imagen en la
probabilidad de que el triple de Betti medido sea correcto: ln(d̄/h), el margen de persistencia
geométrico (τ_dil, τ_ero), el margen de intensidad (m_lo, m_hi) y si el triple coincide al medir la
imagen más gruesa ×2 y ×4 (a1, a2). Verde si p ≥ 0.90, amarillo si 0.50 ≤ p < 0.90, rojo si p < 0.50.
No usa la verdad.

**Calibración** (semilla 20261123): la validación cruzada dejando una forma fuera eligió T7 (las
siete variables), con entropía cruzada media 0.378, frente a 0.386 de T4 y 0.461 de la profundidad
sola (T1). T7 gana a T4 por poco (0.008); la mejora grande es sobre la profundidad sola.

**Confirmación en dominio** (semilla 20261124, 18 900 filas, mismas diez formas, nada reajustado):

| Estrato | AUC | ECE | Luces verdes | Verde falso (IC 95 %) | Cobertura | Verde falso de la línea de base | Conserva la guardia (topología / volumen) |
|---|---|---|---|---|---|---|---|
| global · ideal | 0.921 | 0.013 | 2223 | 2.8 % (2.2–3.6) | 79 % | 3.5 % | 97.5 % / 98.7 % |
| global · realistic | 0.817 | 0.041 | 1667 | 7.0 % (5.9–8.3) | 60 % | 4.3 % | 95.6 % / 96.2 % |
| otsu · ideal | 0.906 | 0.010 | 2246 | 2.2 % (1.7–2.9) | 78 % | 3.9 % | 98.4 % / 99.5 % |
| otsu · realistic | 0.980 | 0.014 | 1407 | 3.2 % (2.4–4.3) | 84 % | 16.6 % | 95.2 % / 96.6 % |
| smoothed_otsu · ideal | 0.817 | 0.037 | 1233 | 0.4 % (0.2–0.9) | 48 % | 6.3 % | 98.5 % / 98.5 % |
| smoothed_otsu · realistic | 0.917 | 0.034 | 1203 | 0.8 % (0.4–1.4) | 55 % | 7.9 % | 96.6 % / 96.2 % |

* **H9b parcial:** AUC ≥ 0.85 en 4 de 6; los dos que no llegan (0.817) son `global · realistic` y
  `smoothed_otsu · ideal`.
* **H9d apoyada (primaria):** los seis estratos son evaluables (≥ 200 verdes) y ninguno pasa de
  10 %. El límite superior del intervalo más alto es 8.3 %.
* **H9e apoyada:** menor entropía cruzada que la profundidad sola en 6 de 6. En `otsu · realistic`
  la línea de base da 16.6 % de verde falso, y el modelo congelado 3.2 %.
* **H10d apoyada:** quitar a1 y a2 empeora la entropía cruzada en 6 de 6. La mejora es pequeña con
  `global` (0.221 frente a 0.225 y 0.331 frente a 0.333) y grande con `otsu · realistic` (0.137
  frente a 0.159) y con `smoothed_otsu · ideal` (0.337 frente a 0.369).

**Formas nunca vistas (H9f apoyada)** — mancuerna y copa, semilla 20261124, 3 024 filas:

| Estrato | Luces verdes | Verde falso (IC 95 %) | Verde falso de la línea de base | Cobertura |
|---|---|---|---|---|
| global · ideal | 436 | 0.0 % (0.0–0.9) | 0.7 % | 90 % |
| global · realistic | 347 | 7.8 % (5.4–11.1) | 9.6 % | 73 % |
| otsu · ideal | 439 | 1.1 % (0.5–2.6) | 0.7 % | 88 % |
| otsu · realistic | 279 | 4.3 % (2.5–7.4) | 21.9 % | 79 % |
| smoothed_otsu · ideal | 259 | 1.2 % (0.4–3.3) | 0.0 % | 51 % |
| smoothed_otsu · realistic | 240 | 0.4 % (0.1–2.3) | 0.0 % | 48 % |

El criterio es sobre la estimación puntual y se cumple. Pero en `global · realistic` el intervalo
llega a 11.1 %: no se puede descartar que el verdadero verde falso con formas nuevas supere 10 %.

Figura: `figures/h9_false_green.png`.

## H10 — Guardia de dominio y desplazamiento

**La guardia.** Dos números medidos en la imagen (ruido estimado y ancho del borde). Si caen fuera
de la envolvente que se observó, en la calibración, sobre las medidas con luz verde, no hay luz
verde: como mucho, amarilla.

**Dominio desplazado** (semilla 20261125, 12 600 filas): cuatro perfiles que la calibración nunca
vio, declarados «realistic» como si fueran normales.

| Estrato | Verde falso del volumen sin guardia | Verde falso del volumen con guardia (verdes que quedan) | Verde falso de la topología sin guardia | Verde falso de la topología con guardia (verdes que quedan) |
|---|---|---|---|---|
| global · ruido ×1.3 | 1.0 % | sin verdes | 21.7 % (60 verdes) | 20.0 % (40) |
| global · ruido ×2 | **80.4 %** | sin verdes | sin verdes | sin verdes |
| global · desenfoque ×1.5 | 12.4 % | 4.1 % (342) | 11.1 % | 10.4 % (511) |
| global · desenfoque ×2 | 24.2 % | 0.0 % (20) | 12.8 % | 12.1 % (379) |
| otsu · ruido ×1.3 | 2.0 % | sin verdes | 0.0 % (3) | sin verdes |
| otsu · ruido ×2 | **97.3 %** | sin verdes | sin verdes | sin verdes |
| otsu · desenfoque ×1.5 | 6.6 % | 0.4 % (255) | 4.8 % | 4.4 % (249) |
| otsu · desenfoque ×2 | 34.8 % | **21.4 % (28)** | 6.9 % | 25.0 % (4) |
| smoothed_otsu · ruido ×1.3 | 2.8 % | sin verdes | 0.5 % | 0.3 % (332) |
| smoothed_otsu · ruido ×2 | 1.9 % | sin verdes | 0.3 % | 0.0 % (20) |
| smoothed_otsu · desenfoque ×1.5 | 15.0 % | 6.2 % (65) | 1.5 % | 1.7 % (361) |
| smoothed_otsu · desenfoque ×2 | 41.4 % | sin verdes | 3.4 % | 2.5 % (122) |

(«Sin verdes» significa que la guardia no dejó ninguna luz verde: no hay verde falso que medir.)

* **H10a apoyada:** sin guardia, el semáforo de volumen de H6 supera 10 % de verde falso en 7 de
  12 estratos (hasta 97.3 % con `otsu` y el doble de ruido).
* **H10b apoyada (primaria):** con guardia, 10 de 12 estratos se quedan con menos de 100 luces
  verdes de volumen (rechazados, el comportamiento buscado) y los dos que conservan más
  (`global` y `otsu` con desenfoque ×1.5) quedan en 4.1 % y 0.4 %.
* **H10c apoyada:** en dominio, la guardia conserva entre 95.2 % y 99.5 % de las luces verdes.
* **H9g no apoyada:** sin guardia, el semáforo de topología pasa de 10 % en 2 de los 8 estratos
  evaluables (`global` con desenfoque ×1.5 y ×2: 11.1 % y 12.8 %). La línea de base incumple 9 de
  11. O sea, el modelo de siete variables aguanta mucho mejor el desplazamiento que la profundidad
  sola, pero no del todo.

Figura: `figures/h10_domain_shift.png`.

## Lo que hay que leer con cuidado (descriptivo, sin veredicto)

* **La guardia no es perfecta, y el criterio lo esconde un poco.** En `otsu · desenfoque ×2` deja
  pasar 28 luces verdes de volumen y 6 son falsas (21.4 %). El criterio preregistrado las cuenta
  como «rechazado» porque son menos de 100. Es un hueco real: una guardia que deja pasar alguna
  imagen mala no es una garantía.
* **La guardia de H10b cubre el volumen, no la topología.** Con `global` y desenfoque, la
  topología conserva cientos de luces verdes con 10.4 % y 12.1 % de falsas, incluso con guardia.
* **En `global · realistic` el modelo topológico tiene más verde falso que la línea de base** (7.0 %
  frente a 4.3 %) a cambio de más cobertura (60 % frente a 42 %). Ambos cumplen el criterio de 10 %.
* **Fallo silencioso.** De 4 395 medidas con topología incorrecta en `test`, el 6.6 % recibió luz
  verde y el 63.5 % roja. Se concentra en dos formas: `shell_tight` (1 052 fallos; 19.8 % verdes) y
  `torus_tight` (884; 7.2 % verdes), es decir, rasgos que la imagen ya perdió. Por resolución, a
  `t/h = 12` el 10.3 % de los 78 fallos recibió verde. Figura: `figures/h9_silent_failures.png`.
* **La mancuerna es la forma débil entre las nuevas** (post hoc): `global · realistic`, 11.4 %
  de verde falso frente a 2.8 % de la copa.
* **El AUC de `unseen` no es fiable donde casi todo es correcto:** en `smoothed_otsu · ideal` el 99.4 %
  de las topologías son correctas y el AUC sale 0.006; en `otsu · ideal` (98.4 % correctas) sale 0.721.
  Con tan pocas incorrectas el AUC no dice nada. No entra en ningún criterio.
* **Eje de escala:** aporta poco con `global` y bastante con Otsu y suavizado; la afirmación vale
  solo para la topología.

## Mis predicciones, puntuadas

| Predicción | Probabilidad que di | ¿Ocurrió? |
|---|---|---|
| La validación cruzada elige T7 | 60 % | sí |
| H9b apoyada | 30 % | no (parcial; la predicción «parcial o mejor», 65 %, sí) |
| H9c apoyada | 80 % | sí |
| H9d apoyada (primaria) | 60 % | sí |
| H9e apoyada | 85 % | sí |
| H9f apoyada | 65 % | sí |
| H9g apoyada | 20 % | no |
| H10a apoyada | 90 % | sí |
| H10b apoyada (primaria) | 50 % | sí |
| H10c apoyada | 70 % | sí |
| H10d apoyada | 60 % | sí |

Ocurrieron 9 de 11 eventos; los dos que no ocurrieron eran los que había puesto en 30 % y 20 %.
Sobre `mild_blur`, mi duda era que se colara por la envolvente: se coló (342 luces verdes de volumen con
`global`, 255 con `otsu`), pero con 4.1 % y 0.4 % de verde falso, dentro del criterio.

## Qué no se puede concluir

* Todo sale del mismo simulador. Los perfiles desplazados cambian parámetros de PSF y ruido
  gaussianos; no son imágenes reales.
* El semáforo no detecta rasgos que la imagen ya perdió (fallo silencioso). Se mide; no se
  promete reducirlo.
* La guardia es una alarma, no un estimador. Rechazar no arregla la medida: obliga a recalibrar
  para ese tipo de imagen.
* Diez hipótesis sobre los mismos datos: por eso hay dos primarias y el resto es apoyo.
* Sin datos reales ni fantomas físicos, esto no valida el instrumento.

## Procedencia y desviaciones

* Los tres barridos se corrieron con el árbol de código limpio (`code_dirty: false` en los tres
  manifiestos): `test` desde `46ede07`, `unseen` desde `b1d0526`, `shift` desde `7504bed`. El modelo
  quedó congelado en `c7661e5` y `results/summary/h9_frozen.json` no cambió desde entonces (la copia
  empaquetada en `src/geovida/frozen/` es idéntica byte a byte). Entre el congelado y los barridos
  solo se añadieron `certificate.py`, la orden `geovida certify/plan` en `cli.py`, esa copia del
  congelado, una exportación para Unity y entradas de `pyproject.toml`; ningún módulo que calcula
  los barridos (`h9.py`, `certsweep.py`, el simulador) cambió.
* Los barridos se interrumpieron una vez cuando el contenedor se reinició. No se usó ningún
  resultado parcial: se relanzaron desde cero con las mismas semillas y el mismo código.
* El preregistro dice «24 estratos» para H9g (3 segmentadores × 4 perfiles); la cuenta correcta es
  **12**. El veredicto usa los 12 (8 evaluables). No cambia nada del criterio (ERRATA E23).
* Después de correr los barridos, solo se movió la posición de las etiquetas de una figura en
  `scripts/analyze_h9.py`; los números no cambian.
