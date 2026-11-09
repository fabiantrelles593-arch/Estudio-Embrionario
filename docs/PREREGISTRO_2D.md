# Preregistro — Prueba de estrés 2D tipo ecografía (v0.2)

> Se confirma (`git commit`) **antes** de ejecutar `scripts/run_2d.py`. El hash
> del commit queda en `results/summary/h5_run_manifest.json`. Los cambios
> posteriores van solo en "Desviaciones".

## 1. Qué es y qué no es

Es una prueba de estrés del **instrumento de medida** sobre imágenes planas
**sintéticas** con moteado multiplicativo (ver `twod.py`). No contiene,
procesa ni representa ecografías reales y no tiene ningún uso clínico. Responde:
¿cuántos píxeles necesita una medida de área, de circunferencia por elipse
(estilo calibrador) o de topología para ser fiable cuando el moteado dispersa la
señal, y cuánto ayuda promediar realizaciones (compounding)?

## 2. Diseño

| Factor | Niveles |
|---|---|
| Forma (3) | `disk`, `ellipse` (semieje mayor 1.25 × menor), `annulus` (diámetro interior 3 t) |
| t/h (7) | 2, 3, 4, 6, 8, 12, 20 |
| Perfil (3) | `ideal`; `us_compound` (PSF FWHM 1 px, 4 realizaciones, grano 2 px, contraste 4:1); `us_raw` (igual con 1 realización) |
| Segmentador (4, medidas repetidas) | `global` (oráculo, 0.5), `otsu`, `smoothed_otsu` (σ = 1 px), `smoothed_otsu_s2` (σ = 2 px) |

R = 200 realizaciones independientes por celda (orientación y desplazamiento
aleatorios): 3 × 7 × 3 × 200 = 12 600 imágenes. Semilla base **20261112**.
Unidad experimental: la realización. Verdad: área, perímetro de frontera,
perímetro exterior y números de Betti exactos.

## 3. Hipótesis y criterios (fijos)

* **H5a — Área.** Con `ideal` y `global`, |mediana err_area| ≤ 5 % para t/h ≥ 4
  en las 3 formas.
* **H5b — El moteado crudo destruye la topología.** Con `us_raw` y `otsu`, la
  proporción de topología correcta del anillo es < 0.5 en **todos** los niveles.
* **H5c — Hay un régimen fiable con compounding.** En `us_compound`, existe al
  menos un segmentador para el cual la proporción de topología correcta del
  anillo es ≥ 0.95 desde algún nivel y se mantiene en todos los superiores
  (mismo criterio t/h\* de H1).
* **H5d — Circunferencia estilo calibrador.** Con `us_compound` y
  `smoothed_otsu`, |mediana err_hc| ≤ 3.3 % para t/h ≥ 8 en `disk` y `ellipse`
  (3.3 % es el límite de acuerdo intraobservador de la circunferencia cefálica
  en INTERGROWTH-21st; se usa solo como vara de comparación).
* **H5e — Promediar ayuda.** Con `smoothed_otsu` y t/h = 8, la mediana de
  |err_hc| de `us_raw` es mayor que la de `us_compound` en `disk` y en `ellipse`.

Un valor no calculable es «no evaluable», nunca «no apoyada». La estimación de
perímetro es el conteo de Crofton de 4 direcciones (sesgo −1.4 % a +0.8 % en
discos de 4 a 30 px, de una exploración previa).

## 4. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| H5a apoyada | 85 % |
| H5b apoyada | 80 % |
| H5c apoyada | 50 % |
| H5d apoyada | 55 % |
| H5e apoyada | 85 % |

## 5. Qué no se puede concluir

El moteado es un modelo gaussiano de grano uniforme: no incluye sombras,
atenuación, anisotropía del haz ni artefactos de reverberación. Pasar estos
criterios no dice nada sobre ecografías reales; solo fija una línea base de lo
que el instrumento puede hacer en el mejor de los casos de un modelo simple.

## 6. Desviaciones

- 2026-11-09 (después de la corrida): el manifiesto `h5_run_manifest.json`
  marca `code_dirty: true` y el commit `08e927b`. Durante la corrida se editaron
  `src/geovida/analysis.py` y `scripts/analyze_h1.py` (un ayudante de tres
  estados para los veredictos de H1, sin relación con 2D). `git diff 08e927b --
  src/geovida/twod.py src/geovida/h5.py scripts/run_2d.py` es vacío: el código
  ejecutado es el commiteado. Criterios y predicciones no se tocaron.
