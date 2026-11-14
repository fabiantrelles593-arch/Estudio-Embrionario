# Resultados de geovida v0.1

Todo lo de abajo sale de datos **sintéticos** (fantomas con verdad exacta y
cohortes simuladas). Es evidencia sobre el comportamiento del instrumento de
medida y del método de estadificación, **no sobre embriones reales**. Criterios
y predicciones se fijaron antes de ejecutar (`PREREGISTRO_H1.md`,
`PREREGISTRO_H2.md`); lo exploratorio está marcado como tal.

> **Actualización (v0.2).** Este documento describe v0.1. Dos cosas cambiaron:
> (1) H1c figura ahora como **falsada** (antes «parcial»; ver `ERRATA.md` E7);
> (2) los pasos 1–3 de la sección 8 ya se ejecutaron: Q se confirmó en formas
> nuevas, hay un estimador de área nuevo y una limpieza mínima con sus límites.
> Resultados en [`RESULTADOS_V02.md`](RESULTADOS_V02.md).

## 1. Resumen

1. **Topología (H1b, confirmada)**: la topología correcta depende del **rasgo
   más estrecho** (sólido *o* vacío), no del grosor sólido. En condiciones
   ideales basta con t_min/h ≈ 1.5–2 vóxeles; con el grosor sólido el rango
   entre formas es de 2.7× (frente a 1.33× con t_min).
2. **Volumen (H1a, falsada)**: el error de volumen **no** es universal en t/h.
   Una bola necesita ~8 vóxeles de diámetro para |error| ≤ 5 % en el 95 % de las
   realizaciones; una cáscara o un tubo, ~2.
3. **Hallazgo exploratorio (post hoc, por confirmar)**: el volumen sí colapsa en
   **Q = V/(S·h)**, la longitud volumen/área en vóxeles; Q supera a todos los
   predictores basados en t por 2 500–9 000 unidades de AIC en los seis
   estratos segmentador × perfil.
4. **Segmentación**: el suavizado + Otsu protege la topología con ruido pero
   **sobrestima el volumen** de objetos pequeños (+29 % a 6 vóxeles de grosor,
   +85 % a 4, en una bola con imagen ideal). Sin limpieza, la topología con
   ruido *empeora* al aumentar el tamaño de la imagen (motas aisladas).
5. **4D (H2)**: con un error de estadificación de hasta medio intervalo entre
   etapas, el sesgo de la media por etapa es ≤ 4.3 %; la corrección empeora el
   RMSE (×2.4 con n = 3) y, si σ se supone el doble, el sesgo salta a 22 %. Con
   n ≤ 3 por etapa el IC bootstrap cubre solo ~70 % en vez de 95 %.

## 2. H1 — veredictos preregistrados

Estrato de referencia: perfil ideal, vóxel isótropo, umbral oráculo; R = 200
por celda; 58 800 imágenes (`results/summary/h1_*.csv`, `h1_verdicts.json`).

| Hipótesis | Veredicto | Evidencia |
|---|---|---|
| H1a volumen universal en t/h, t/h\* ≤ 6 | **Falsada** | t/h\* de V: bola 8, elipsoide 6, toro 4, toro_tight 4, cáscara_tight 3, cáscara 2, tubo 2 (cociente 4.0 > 1.5) |
| H1b topología universal en t_min/h | **Confirmada** | t_min/h\*: 1.5–2.0 (cociente 1.33 ≤ 1.5); con t_solid: 1.5–4.0 (2.67 > 2.25, como se esperaba) |
| H1c anisotropía colapsa con el vóxel peor | **Falsada** (por el criterio preregistrado; ver E7) | Componente AIC ✓: ΔAIC(h_max − h_xy) = −387 (V), −1 276 (topología). Componente topología ✓: rango de t/h\*(h_max) entre anisotropías 1.5 (≤ un paso). Componente **volumen ✗**: rango 2.0 en cáscara y tubo (> un paso); la bola no alcanza el nivel con anisotropía 3 (solo esa celda es «no evaluable»). El criterio preregistrado dice «falsada si el rango excede un paso», así que basta un fallo. **Mejor predictor global: h_geo** (P2 en V, P5 en topología), no h_max |
| H1d t/h\* independiente del segmentador | **No confirmada** | cocientes hasta 2.67 (topología) y niveles no alcanzados en V |
| Consistencia con Horner 2019 (≤ 2 % de diámetro con ≥ 5–6 vóxeles) | **Pasa** | mediana |error diámetro| 0.85 % a t/h = 6; 1.5 % a 4; 2.8 % a 3 |

Figuras: `figures/h1_volume_error.png`, `h1_topology_collapse_shape.png`,
`h1_topology_collapse_anisotropy.png`, `h1_segmenter_bias.png`.

### Qué pasa con la anisotropía
Con h_z/h_xy = 3, la topología exige t/h_xy de 3–8 (ideal, oráculo): unas 2×
(2–2.7×) el valor isótropo. La resolución mala en z domina, como se esperaba,
pero el costo es menor que el que predije (9–12).

### Área de superficie (secundaria) — ambos estimadores tienen sesgo
* Conteo de caras: **+43 % a +51 %** siempre (sesgo ya conocido).
* Marching cubes sobre la máscara suavizada (σ = 1 vóxel): **−66 % en una bola de
  4 vóxeles, −15 % a 8, −6 % a 12**; en cáscara/tubo, −2 % a −9 % a 4 vóxeles. El suavizado
  que fijé es demasiado fuerte para objetos pequeños. **Limitación de v0.1**; no
  usar estas áreas como medidas fiables por debajo de ~12 vóxeles de grosor.

## 3. Exploratorio (post hoc) — el volumen colapsa en V/(S·h)

`scripts/exploratory_h1.py`, `results/summary/h1_exploratory_vq_aic.csv`,
figura `h1_exploratory_volume_collapse.png`. Razón: el error relativo de un
conteo de vóxeles escala con (S/V)·h, y la razón S/V no es proporcional a 1/t
entre formas (bola: 6/t; cáscara: ~2/t). Valor de Q con P(V_ok) = 0.95 (ajuste
logístico): Q/h_geo ≈ 1.2 (umbral oráculo), 1.6 (Otsu, ruido) y 3.3
(suavizado + Otsu). **Es una hipótesis generada con estos datos; requiere un
barrido nuevo y preregistrado para confirmarse.**

## 4. Ruido y segmentación: dos hechos que cambian la práctica

* **Motas**: con SNR = 10 y umbral oráculo, la topología de una cáscara a
  t/h = 12 es correcta solo en 62 % de las realizaciones y los fallos son
  componentes y cavidades *de más* (b0 +1…+4; b1 nunca falla). La probabilidad
  de al menos una mota crece con el número de vóxeles; con más resolución a SNR
  constante, la topología cruda **empeora**. Una limpieza mínima (eliminar
  componentes pequeños) o el suavizado es imprescindible; deliberadamente no la
  incluí para que el error fuera visible.
* **Compromiso del suavizado**: suavizado + Otsu mantiene la topología al 100 %
  con ruido (a t/h = 8–12), pero infla V: +204 %, +85 %, +29 % para una bola de
  3, 4 y 6 vóxeles de grosor (imagen ideal). Otsu sin suavizar: +2–7 % en V pero topología
  correcta solo en 72–97 % (según la forma) a t/h = 8, con ruido.

## 5. H2 — banco de pruebas 4D (pseudo-tiempo)

K = 7 etapas; 810 escenarios × 500 cohortes; bootstrap de 200 remuestreos por
especímenes (`results/summary/h2_*`).

| Hipótesis | Veredicto | Evidencia |
|---|---|---|
| H2a sesgo > 5 % solo en `switch` (σ_s = 0.5, n = 20) | **Falsada** | sesgo máx.: growth 3.6 %, saturating 4.3 %, switch 4.0 % (todos < 5 %) |
| H2b cobertura peor con n = 20 que con n = 3, y < 90 % | **Falsada** | cobertura sube con n: 70 % → 88 % (σ_s = 0.5) y 72 % → 92 % (σ_s = 0.25) |
| H2c el spline corregido reduce el sesgo ≥ 50 % | **Falsada** | 3.55 % vs 4.04 % (−12 %); con σ supuesto ×2: 21.9 % |
| H2d con n ≤ 3 domina la varianza (sesgo² < 50 % del MSE) | **Confirmada** | fracción de sesgo² ≤ 7.5 % en las 12 celdas |

Lectura: dentro del rango probado (σ_s ≤ medio intervalo; variación biológica
8 %), **el error de estadificación es de segundo orden**; lo que más engaña con
n pequeño es el propio bootstrap percentil (cobertura ≈ 70 % incluso con
σ_s = 0). Corregir el error de estadificación **no vale la pena** salvo que σ_s
se conozca bien (replicando la estadificación): el corregido duplica el RMSE a
n = 3 (21.8 % vs 9.2 %) y es frágil si σ se sobreestima.
Figuras: `h2_bias_by_stage.png`, `h2_coverage_vs_n.png`, `h2_irmse_vs_n.png`.

### Acople metrología → trayectoria (demostración, no confirmatoria)
Elipsoide que crece a vóxel fijo (t/h de 2.0 a 5.4 entre la etapa 0 y la 6),
tasa de crecimiento verdadera 0.5 por etapa:

| Cadena de medición | Tasa aparente | Distorsión |
|---|---|---|
| umbral oráculo, imagen ideal | 0.521 | +4 % |
| suavizado + Otsu, imagen realista | 0.297 | **−41 %** |
| Otsu crudo, imagen realista | −0.288 | **signo invertido** (fallo del umbral en objetos diminutos) |

La resolución sola, sin ninguna biología, puede aplanar o invertir una curva de
crecimiento cuando los especímenes jóvenes ocupan pocos vóxeles.

## 6. Marcador de mis predicciones escritas de antemano

| Predicción | Resultado |
|---|---|
| H1-1: V_ok en t/h\* 3–4 (convexas) y 4–6 (resto) | ✗ bola 8, elipsoide 6; cáscara/tubo 2 |
| H1-2: topología t_min/h\* ≈ 3–4 | ✗ 1.5–2 (más favorable) |
| H1-3: anisotropía 3 exige t/h_xy ≳ 9–12 | ✗ 3–8 |
| H1-4: Otsu sobrestima V +3–10 % | ◐ Otsu +2–7 % ✓; suavizado + Otsu +29–204 % (mucho peor) |
| H1-5: con ruido, Otsu crudo peor que suavizado en topología | ✓ |
| H2-1: sesgo < 2 % en growth/saturating, > 10 % en switch | ✗ 3.6 / 4.3 / 4.0 % |
| H2-2: cobertura < 60 % con n = 20, σ_s = 0.5 | ✗ 88 % |
| H2-3: el corregido tiene más varianza | ✓ |
| H2-4: sobrecorregir (×2) empeora | ✓ |

Aciertos: 3 de 9 (más uno parcial). Mi intuición fue sistemáticamente
pesimista sobre la resolución necesaria y optimista sobre el efecto del error
de estadificación; por eso se preregistró.

## 7. Limitaciones y lo que no se puede concluir

* Formas simples y suaves, PSF y ruido gaussianos, un solo tamaño relativo por
  clase. Nada se ha validado con imágenes reales.
* El estimador de área y el suavizado σ = 1 son decisiones mías que sesgan los
  resultados de S y de V con `smoothed_otsu`; no son "el" método.
* H1c en V: solo la bola con anisotropía 3 no alcanza el nivel dentro de la
  rejilla (≤ 12); las demás formas dan rangos finitos (2.0 en cáscara y tubo),
  que incumplen el criterio. Una versión anterior de este texto decía «no pudo
  evaluarse» y H1c «parcial»: era un error (ERRATA E7).
* H2 supone σ_s conocido, diseño balanceado y tres trayectorias que elegí yo;
  las conclusiones sobre "segundo orden" valen para esos tamaños de efecto.
* El análisis exploratorio de Q y la regla t_min no son resultados
  confirmatorios fuera de este barrido.
* No implementado en v0.1 (declarado): error de coeficientes de armónicos
  esféricos, diseño longitudinal, datos reales.

## 8. Siguientes pasos propuestos (v0.2)

1. Barrido **nuevo y preregistrado** para confirmar Q = V/(S·h) como predictor
   del volumen (y sus umbrales por segmentador).
2. Estimador de área con corrección de sesgo (curvatura / Crofton) y evaluación
   del suavizado σ.
3. Añadir limpieza mínima de componentes como cuarto segmentador y medir su
   efecto en topología y volumen.
4. Datos reales con licencia confirmada (IMPC/MusMorph; Dalmasso S-BIAD441 si su
   licencia lo permite): medir el presupuesto de error sobre segmentaciones
   reales y cotejarlo con esta predicción.
5. Diseño longitudinal y heterocronía por camada en el banco 4D.

## 9. Reproducir

```bash
pip install -e ".[dev]" && pytest                   # 113 pruebas
python scripts/run_h1.py --reps 200 --jobs 2         # ~32 min en 2 núcleos
python scripts/analyze_h1.py && python scripts/exploratory_h1.py
python scripts/run_h2.py && python scripts/analyze_h2.py   # ~1 min
```
Barrido H1 ejecutado en el commit `c3a7111`; H2 en `bb356eb`; semilla base
20261109. Manifiestos en `results/summary/*_run_manifest.json`.
