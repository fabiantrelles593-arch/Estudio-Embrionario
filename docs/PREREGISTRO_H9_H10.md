# Preregistro — H9 y H10: certificado vectorial (v0.4)

> Se confirma (`git commit` + `git push`) **antes** de correr la calibración
> (`scripts/run_h9.py --set cal`). El congelado (`results/summary/h9_frozen.json`) se confirma
> **antes** de los barridos de confirmación (`test`, `unseen`, `shift`). Los cambios posteriores
> van solo en «Desviaciones».

## 1. Pregunta y por qué importa

H6 dio un semáforo para el **volumen** y dejó fuera la topología. Además, se calibró y se confirmó
con el mismo simulador de imagen. Aquí se añaden dos piezas y se prueban donde pueden fallar:

1. **Semáforo topológico.** ¿Puede el instrumento estimar, sin conocer la verdad, la probabilidad
   de que el triple de Betti medido sea correcto?
2. **Guardia de dominio.** ¿Sigue siendo fiable el semáforo cuando la imagen tiene más desenfoque
   o más ruido que las de la calibración? Y si no, ¿puede el instrumento darse cuenta y negarse?

Ninguna de las ideas sueltas es nueva (ver `docs/ANTECEDENTES_V04.md`): el margen geométrico es la
persistencia en la filtración por distancia con signo (Robins et al. 2016), el de intensidad es la
persistencia por umbral (Chung y Day 2018) y la re-medición a escalas más gruesas es una
transferencia del Grid Convergence Index (Roache 1994). Lo que se pone a prueba es su uso como
**probabilidad calibrada contra una verdad conocida**, con formas y perfiles nunca vistos.

### Lo que mostró el piloto (semilla 20261122, **no** usada aquí; 2–3 réplicas por celda)

* **El margen solo no basta y la profundidad global tampoco.** Validación dejando una forma
  fuera, entropía cruzada media: T1 (profundidad) 0.459; solo margen geométrico 0.499 (peor que la
  línea de base); T4 0.388; T7 0.384.
* **Fallo silencioso.** De 878 fallos topológicos, el 21 % tenía todos los márgenes holgados y
  coincidía entre escalas: son rasgos que la imagen ya perdió por completo (cavidad de
  `shell_tight`: 58 % de sus fallos; hueco de `torus_tight`: 33 %; sólidos simples: 0 %). Ningún
  margen puede verlos.
* **El semáforo de volumen de H6 se rompe fuera de dominio.** Declarando `realistic` una imagen
  con el doble de desenfoque o la mitad de SNR, el verde falso fue 23 % a 97 % en cinco de seis
  estratos (5 % en el sexto). Es un defecto de H6 que H6 no podía ver.
* **La guardia, ajustada sobre las filas verdes de la calibración, lo impide en el piloto:** en los
  seis estratos desplazados dejó 0 luces verdes, y en dominio conservó 91–98 % de las verdes.
  (Una primera versión, ajustada sobre todas las filas, no detectaba el desenfoque: la envolvente
  era demasiado ancha a baja resolución.)
* **El eje de escala aporta poco al volumen** (entropía cruzada 0.254 → 0.244) y una regla universal
  «deriva pequeña ⇒ volumen fiable» falla (peor estrato: 31–64 % de acierto). Se descarta como regla
  propia; el acuerdo entre escalas entra solo como variable del modelo topológico.

## 2. Variables, protocolo y reglas fijas

Todas las variables se calculan con la imagen, el vóxel, la máscara y el nombre del segmentador
(`geovida.certsweep.cert_extra` no recibe la verdad).

| Conjunto | Variables |
|---|---|
| T1 (línea de base) | ln(d̄/h_geo), la variable del semáforo de volumen de H6 |
| T4 | τ_dil, τ_ero (margen geométrico, vóxeles finos, rejilla 0.6/1/1.5/2); m_lo, m_hi (margen de intensidad, fracción del contraste, rejilla 0.1–0.4); a1, a2 (el triple de Betti coincide al degradar ×2 y ×4) |
| T7 | T1 + T4 |

* **Calibración** (semilla 20261123, 15 réplicas por celda, las 10 formas de H6, rejilla 7 × 3,
  perfiles `ideal` y `realistic`, tres segmentadores): por estrato (segmentador × perfil),
  validación cruzada dejando una forma fuera. Se elige UN conjunto para todos los estratos: el de
  menor entropía cruzada media; a igualdad, el de menos variables. Logit con ridge = 1 sobre
  variables estandarizadas. Se congelan, por estrato: el modelo elegido, la línea de base T1 y el
  modelo elegido sin a1/a2.
* **Envolventes de dominio:** por estrato y por medida (volumen, topología), el intervalo entre
  los cuantiles 1 % y 99 % de `snr_hat` y `edge_width` sobre las filas de calibración **con luz
  verde** en esa medida. Con menos de 50 filas verdes no hay envolvente y la guardia rechaza todo.
* **Luces:** verde p ≥ 0.90; amarillo 0.50 ≤ p < 0.90; rojo p < 0.50. Variable no medible: p = 0.
  **Fuera de la envolvente no hay luz verde.**
* **Respuestas:** T_ok = triple de Betti exacto con adyacencia (26, 6); V_ok = |error de V| ≤ 5 %.
* **Confirmación en dominio** (`test`: semilla 20261124, 15 réplicas, las mismas 10 formas).
* **Formas nunca vistas** (`unseen`: semilla 20261124, 12 réplicas, `dumbbell` y `cup`).
* **Dominio desplazado** (`shift`: semilla 20261125, 5 réplicas, las 10 formas, cuatro perfiles que
  la calibración no vio: `blurry` FWHM 2 · SNR 10; `noisy` FWHM 1 · SNR 5; `mild_blur` FWHM 1.5 ·
  SNR 10; `mild_noise` FWHM 1 · SNR 7.5). El usuario «declara» `realistic` en todos.
* Un estrato es *evaluable* para verde falso con ≥ 200 filas verdes en `test` y ≥ 100 en `unseen` y
  `shift` (conjuntos más pequeños). ECE: 10 cajas de igual ancho. Entropía cruzada con p recortada
  a [0.001, 0.999].

## 3. Hipótesis y criterios (fijos)

**Primarias:** H9d y H10b. Las demás son secundarias.

### H9 — semáforo topológico

* **H9b — Discrimina.** AUC ≥ 0.85 en ≥ 5 de 6 estratos de `test`. *Parcial*: 4. *No apoyada*: ≤ 3.
* **H9c — Está calibrado.** ECE ≤ 0.10 en ≥ 5 de 6. *Parcial*: 4.
* **H9d — No da luz verde falsa (primaria).** Verde falso ≤ 0.10 en **todos** los estratos
  evaluables de `test`. *No evaluable* si ninguno lo es.
* **H9e — Mejora a la profundidad global.** Menor entropía cruzada que T1 en ≥ 5 de 6. *Parcial*: 4.
* **H9f — Vale en formas nunca vistas.** Verde falso ≤ 0.10 en todos los estratos evaluables de
  `unseen`.
* **H9g — Aguanta el desplazamiento sin guardia.** Verde falso ≤ 0.10 en todos los estratos
  evaluables de `shift` (24 = 3 segmentadores × 4 perfiles), usando el modelo `realistic` y sin
  aplicar la guardia. Se informa al lado cuántos estratos incumple la línea de base T1.

### H10 — guardia de dominio y eje de escala

* **H10a — El semáforo de volumen de H6 se rompe fuera de dominio.** En ≥ 3 estratos evaluables de
  `shift` el verde falso de volumen, sin guardia, supera 0.10.
* **H10b — La guardia lo impide (primaria).** Con la guardia, ningún estrato de `shift` que conserve
  ≥ 100 luces verdes de volumen supera 0.10 de verde falso. Un estrato que se queda con menos de 100
  verdes cuenta como *rechazado*, que es el comportamiento buscado. *No apoyada* si alguno falla.
* **H10c — La guardia cuesta poco en dominio.** En `test`, la guardia conserva ≥ 90 % de las luces
  verdes de volumen y de topología en todos los estratos.
* **H10d — El eje de escala aporta.** En `test`, el modelo congelado tiene menor entropía cruzada
  que el mismo modelo sin a1/a2 en ≥ 4 de 6 estratos. *Parcial*: 3. *No evaluable* si el conjunto
  elegido no usa a1/a2.

Un valor no calculable es «no evaluable», nunca «no apoyada».

**Extensión descriptiva (sin veredicto):** (i) fallo silencioso: de las medidas con topología
incorrecta, qué luz recibieron, por t/h y por forma; (ii) cobertura: fracción de las topologías
correctas que reciben verde; (iii) verde falso de volumen y de topología frente a la magnitud del
desplazamiento, con y sin guardia; (iv) intervalos de Wilson del verde falso; (v) la mancuerna por
separado.

## 4. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| La validación cruzada elige T7 | 60 % (T4: 30 %; T1: 10 %) |
| H9b apoyada (AUC ≥ 0.85 en ≥ 5/6) | 30 % (parcial o mejor: 65 %) |
| H9c apoyada | 80 % |
| H9d apoyada (primaria) | 60 % |
| H9e apoyada | 85 % |
| H9f apoyada | 65 % |
| H9g apoyada (sin guardia, los 24 estratos) | 20 % |
| H10a apoyada | 90 % |
| H10b apoyada (primaria) | 50 % — mi duda es `mild_blur`: puede colarse por la envolvente |
| H10c apoyada | 70 % |
| H10d apoyada (≥ 4/6) | 60 % |

## 5. Qué no se puede concluir

* Todo es sintético. Los perfiles desplazados siguen saliendo del mismo simulador (PSF y ruido
  gaussianos): prueban un desplazamiento de parámetros, no el salto a imágenes reales.
* El semáforo topológico **no detecta rasgos que la imagen ya perdió**. La tasa de fallo
  silencioso se informa; no se promete reducirla.
* La guardia es una alarma, no un estimador de la PSF ni del ruido. Rechazar no arregla la medida:
  obliga a recalibrar para ese tipo de imagen.
* La degradación por bloques no reproduce una adquisición real a menor resolución.
* Diez hipótesis sobre los mismos datos: por eso hay dos primarias y el resto se lee como apoyo.
* Sin datos reales ni fantomas físicos, nada de esto es una validación del instrumento.

## 6. Desviaciones

(Ninguna al momento del primer commit.)
