# Preregistro — Confirmación H3 y evaluación del estimador de área H4 (v0.2)

> Este documento se confirma (`git commit`) **antes** de ejecutar el barrido
> `scripts/run_h3.py`. El hash del commit queda en
> `results/summary/h3_run_manifest.json`. Cualquier cambio posterior se anota
> solo en "Desviaciones", con fecha, sin editar lo anterior.

## 1. Por qué existe

En H1 (v0.1) el volumen **no** colapsó en t/h (H1a falsada). Después de ver los
datos descubrí que sí colapsa en **Q = V/(S·h)**, la longitud volumen/área en
vóxeles. Ese hallazgo es *post hoc*: no cuenta como resultado hasta que una
regla fijada con los datos de H1 acierte sobre datos que no pudieron influir
en ella. H3 hace esa prueba. H4 evalúa, con los mismos datos nuevos, un
estimador de área que sustituye al de v0.1 (sesgo de −64 % a 4 vóxeles).

## 2. Qué es nuevo y qué es igual

| | H1 | H3 |
|---|---|---|
| Formas | 7 (`ball`…`torus_tight`) | **3 nuevas**: `capsule`, `cylinder`, `oblate` (ver `phantoms.py`) |
| Semilla base | 20261109 | **20261110** |
| Rejilla t/h, anisotropía, perfiles | igual | igual (7 × 3 × 2) |
| Segmentadores | `global`, `otsu`, `smoothed_otsu` | los mismos tres **más** `otsu_clean` (extensión, solo descriptiva) |
| Repeticiones | 200 | 200 |
| Estimador de área | `area_mc`, `area_faces` | los mismos **más** `area_sdf` |

Total: 3 × 7 × 3 × 2 × 200 = 25 200 imágenes. Unidad experimental: realización.

Las tres formas nuevas son sólidos simples (Betti (1,0,0)) con proporciones
fijas del menor grosor *t*: cápsula (radio t/2, tramo cilíndrico 3t), cilindro
(radio t/2, altura 3t), esferoide oblato (semiejes 2.5t, 2.5t, t/2).

## 3. Modelos congelados

`scripts/freeze_h3_models.py` ajusta con los datos de H1, por estrato
(segmentador × perfil), dos logits de Pr(|error de V| ≤ 5 %):

* **modelo Q:** sobre ln(Q/h_geo), con h_geo = (h_xy² h_z)^(1/3);
* **modelo de grosor:** sobre ln(t_solid/h_geo).

Los coeficientes están en `results/summary/h3_frozen_models.json` (con el hash
de los datos de H1) y **no se reajustan** para H3a ni H3b.

## 4. Hipótesis y criterios (fijos)

Estratos: los 6 de segmentador (3 preregistrados) × perfil. Respuesta V_ok:
|err_volume| ≤ 0.05.

* **H3a — Q generaliza mejor que el grosor.** En cada estrato, la entropía
  cruzada fuera de muestra del modelo Q congelado es **menor** que la del modelo
  de grosor congelado. *Apoyada* si ocurre en 6 de 6; *parcial* en 4–5;
  *no apoyada* en ≤ 3.
* **H3b — El modelo Q está calibrado en formas nuevas.** Error de calibración
  esperado (10 cajas de igual ancho en la probabilidad predicha) ≤ 0.10 en al
  menos 5 de 6 estratos. *Parcial*: 4. *No apoyada*: ≤ 3.
* **H3c — El Q\* se conserva.** Q\* (Pr = 0.95) reajustado con los datos de H3,
  por estrato, dentro de un factor 1.5 del Q\* congelado de H1 (cociente en
  [0.667, 1.5]) en al menos 4 de 6 estratos. Un Q\* no alcanzable cuenta como
  «no evaluable», nunca como «no apoyada».
* **H4a — El área SDF es utilizable.** En `global`/`ideal`/anisotropía 1, la
  mediana de err_area_sdf está dentro de ±10 % para t/h ≥ 6 en cada una de las
  3 formas nuevas.
* **H4b — Mejor que los estimadores de v0.1.** En esas mismas condiciones y
  para t/h ∈ {4, 6, 8, 12}, |mediana err_area_sdf| es menor que la de
  `area_mc` y que la de `area_faces` en al menos 10 de las 12 celdas
  (forma × nivel).
* **H4c — Límite honesto a 4 vóxeles.** A t/h = 4 la mediana de err_area_sdf
  está dentro de ±25 % en cada forma. Si no, se declara que el estimador no
  sirve por debajo de ese tamaño.

Extensión (sin veredicto; solo descriptiva): efecto de `otsu_clean` frente a
`otsu` en la proporción de topología correcta y en el error de volumen.

## 5. Reglas de análisis

* Un valor no calculable (NaN) nunca cuenta como «no apoyada»: se informa como
  **no evaluable**. (Corrige un defecto de v0.1.)
* El script de análisis (`scripts/analyze_h3.py`) se escribe después de este
  commit y antes de mirar los datos; solo se corrigen errores de código, y toda
  corrección se anota en `docs/ERRATA.md`.
* Los resultados fuera de estos criterios se marcan como exploratorios.

## 6. Predicciones escritas de antemano

Las escribo antes de ver un solo resultado de H3, para medir mi intuición:

| Predicción | Probabilidad que le asigno |
|---|---|
| H3a apoyada (6/6) | 60 % |
| H3b apoyada (≥ 5/6) | 40 % |
| H3c cumplida (≥ 4/6) | 55 % |
| H4a apoyada para cápsula y oblato; el cilindro (aristas vivas) roza el límite del 10 % | 65 % |
| H4b apoyada (≥ 10/12) | 70 % |
| H4c apoyada | 60 % |
| `otsu_clean` sube ≥ 10 puntos la topología correcta de `otsu` con perfil realista y t/h ≥ 6, y cambia el error de volumen en < 1 punto | 70 % |

Contexto del piloto de área (semillas 20261111, no usadas aquí): con σ = 0.5 el
sesgo de `area_sdf` fue de +3 % en la asíntota y −16 % para una bola de 4
vóxeles; el piloto usó 4 formas de H1 y 8 réplicas, y de él salió el único
parámetro libre del estimador (σ = 0.5 vóxel).

## 7. Qué no se puede concluir

Todo es sintético. Pasar H3 diría que Q describe bien **estas** formas
convexas y finas bajo este modelo de imagen; no diría nada sobre embriones
reales, formas con ramas ni artefactos de adquisición.

## 8. Desviaciones

(Ninguna al momento de este commit.)
