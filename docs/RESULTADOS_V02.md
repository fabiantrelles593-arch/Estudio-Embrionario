# Resultados de v0.2 (confirmación H3/H4 y prueba de estrés 2D H5)

> **Solo datos sintéticos.** Todo lo de este documento describe el
> *instrumento de medida* sobre objetos de verdad conocida. No hay embriones
> reales, ecografías reales ni afirmación clínica alguna. Desarrollado con
> asistencia de IA (Claude); sin revisión científica humana externa.

Criterios y predicciones se fijaron y se confirmaron (`git commit`) **antes** de
correr los barridos: [`PREREGISTRO_H3.md`](PREREGISTRO_H3.md) y
[`PREREGISTRO_2D.md`](PREREGISTRO_2D.md). Errores propios hallados al verificar:
[`ERRATA.md`](ERRATA.md). Lo exploratorio está marcado como tal.

## 1. Resumen

| Bloque | Hipótesis | Aciertos de mis predicciones |
|---|---|---|
| 3D (formas nuevas, semillas nuevas) | H3a–c y H4a–c **apoyadas** (6 de 6) | 6 de 7 |
| 2D tipo ecografía (sintético) | H5a, H5b, H5e apoyadas; H5c y H5d **no apoyadas** | 3 de 5 |
| v0.1 (para comparar) | 9 hipótesis | 3 de 9 |

Lo que se puede decir con cuidado:

1. **La longitud volumen/área Q = V/(S·h) predice mejor que el grosor** si el
   volumen de un sólido simple se medirá con ≤ 5 % de error, en formas que no
   participaron en el ajuste. La ventaja es clara con el umbral oráculo y con
   Otsu en imagen realista; es nula con Otsu en imagen ideal y queda dentro del
   ruido con suavizado (sección 2).
2. **El estimador de área por distancia con signo (v0.2) reduce el sesgo de
   v0.1** (a 4 vóxeles, de −17 … −34 % a −3 … −11 %; ≈ ±2 % desde 8 vóxeles),
   pero no sirve por debajo de ~3 vóxeles (a t/h = 2 subestima 18–44 %) y conserva un sesgo de ≈ +2 % a
   t/h = 12 en cápsula y oblato.
3. **La limpieza mínima ayuda donde se esperaba y daña donde no se probó**
   (sección 4): borra cavidades reales de menos de 8 vóxeles.
4. **En 2D, el área es fiable desde ~4 px; la circunferencia por elipse y la
   topología no lo son con moteado** hasta tamaños mucho mayores (sección 5).

## 2. H3 — ¿Q generaliza a formas que no vio?

Los modelos se ajustaron una vez con los datos de H1 (hash en
`results/summary/h3_frozen_models.json`) y no se reajustaron. Se evaluaron con
25 200 imágenes nuevas (cápsula, cilindro, oblato; semilla 20261110), por
estrato (segmentador × perfil de imagen). Respuesta: |error de V| ≤ 5 %.

| Estrato | n | Tasa base | Entropía cruzada: nada / Q / grosor | ECE Q / grosor | Q\* congelado → reajustado (cociente) |
|---|---|---|---|---|---|
| global · ideal | 12 600 | 0.64 | 0.654 / **0.295** / 0.363 | 0.029 / 0.081 | 1.19 → 1.16 (0.98) |
| global · realista | 12 600 | 0.53 | 0.691 / **0.263** / 0.364 | 0.042 / 0.126 | 1.44 → 1.36 (0.95) |
| otsu · ideal | 12 600 | 0.51 | 0.693 / 0.312 / 0.312 | 0.043 / 0.042 | 1.79 → 1.60 (0.90) |
| otsu · realista | 12 600 | 0.41 | 0.677 / **0.205** / 0.234 | 0.027 / 0.073 | 1.63 → 1.61 (0.99) |
| smoothed_otsu · ideal | 12 600 | 0.15 | 0.425 / 0.154 / 0.174 | 0.042 / 0.089 | 3.40 → 2.93 (0.86) |
| smoothed_otsu · realista | 12 600 | 0.15 | 0.414 / 0.136 / 0.152 | 0.039 / 0.107 | 3.33 → 2.79 (0.84) |

| Hipótesis | Criterio fijo | Resultado | Mi predicción |
|---|---|---|---|
| H3a Q mejor que grosor | menor entropía cruzada en 6 de 6 | **Apoyada** (6/6, con matices abajo) | 60 % |
| H3b Q calibrado | ECE ≤ 0.10 en ≥ 5 de 6 | **Apoyada** (6/6; ECE de Q ≤ 0.043) | 40 % |
| H3c Q\* se conserva | cociente en [0.667, 1.5] en ≥ 4 de 6 | **Apoyada** (6/6; cocientes 0.84–0.99) | 55 % |

**Matices que importan (auditoría exploratoria, `explore_v02_extras.py`):**

* H3a se cumple en la letra, pero el margen es desigual. Diferencia media de
  entropía cruzada (grosor − Q) ± error típico entre condiciones:

  | Estrato | Ganancia de Q | Condiciones donde Q gana |
  |---|---|---|
  | global · ideal | +0.067 ± 0.012 | 87 % |
  | global · realista | +0.101 ± 0.014 | 94 % |
  | otsu · ideal | **+0.0001 ± 0.011** (empate) | 51 % |
  | otsu · realista | +0.029 ± 0.010 | 81 % |
  | smoothed_otsu · ideal | +0.020 ± 0.030 (dentro del ruido) | 83 % |
  | smoothed_otsu · realista | +0.016 ± 0.031 (dentro del ruido) | 86 % |

  Por eso resumo H3a como «apoyada, con ventaja clara en 3 estratos, empate en
  1 y ventaja dentro del ruido en 2».
* Ambos modelos mejoran mucho sobre «no saber nada» (entropía 0.14–0.31 con Q
  frente a 0.41–0.69): predecir cuándo falla la medida de volumen es posible con
  cualquiera de los dos; Q lo hace mejor y, sobre todo, **colapsa las formas**
  (figura `docs/figures/h3_q_frozen_model_new_shapes.png`: con grosor, el oblato
  queda a la izquierda y cápsula/cilindro a la derecha de la curva; con Q se
  alinean).
* **Q\* reajustado fue siempre menor que el congelado** (cocientes < 1 en los 6
  estratos): las formas nuevas alcanzan el 95 % antes de lo que predecía H1. El
  modelo congelado es conservador en estas formas; no se sabe si lo sería en
  otras.
* **Interpretación (mía, no probada aquí):** 1/Q = S·h/V es la fracción de
  vóxeles de frontera. Que el error de volumen se organice por Q es lo que
  cabe esperar si el error viene de los vóxeles de borde; el resultado confirma
  la regla en 3 formas más, no descubre un mecanismo nuevo.
* **Límites:** (i) las tres formas son sólidos simples (Betti (1,0,0)); no se
  confirmó nada para cáscaras, toros ni formas con ramas. (ii) En el análisis,
  Q se calcula con el V y el S **verdaderos** del fantoma: sirve para dimensionar
  una adquisición («¿cuántos vóxeles necesito?»), no para corregir una medida
  real, donde S tendría que estimarse (y su sesgo importa; ver H4).

## 3. H4 — Estimador de área por distancia con signo

Condiciones: umbral oráculo, imagen ideal, vóxel isótropo; error mediano de área
(%), formas nuevas. `faces` = conteo de caras de v0.1; `mc` = marching cubes
suavizado de v0.1; `sdf` = v0.2 (σ = 0.5 vóxel, único parámetro libre, elegido en
un piloto con semillas distintas).

| t/h | cápsula sdf / mc / faces | cilindro sdf / mc / faces | oblato sdf / mc / faces |
|---|---|---|---|
| 1.5 | −70.4 / −100.0 / +20.2 | −75.4 / −100.0 / +5.1 | −29.8 / −100.0 / +28.3 |
| 2 | −38.1 / −100.0 / +31.3 | −44.2 / −100.0 / +22.8 | −17.6 / −63.2 / +38.6 |
| 3 | −13.5 / −56.2 / +45.0 | −19.7 / −61.9 / +37.4 | −7.5 / −29.8 / +45.4 |
| 4 | −6.0 / −27.5 / +47.2 | −11.3 / −33.7 / +42.1 | −3.2 / −17.4 / +47.9 |
| 6 | −0.7 / −11.2 / +50.3 | −5.1 / −17.1 / +45.8 | +0.1 / −8.0 / +49.5 |
| 8 | +1.0 / −6.0 / +50.4 | −2.4 / −11.0 / +47.5 | +1.4 / −4.5 / +50.8 |
| 12 | +2.1 / −2.5 / +50.9 | −0.2 / −6.1 / +49.6 | +2.3 / −1.9 / +49.4 |

| Hipótesis | Criterio fijo | Resultado | Mi predicción |
|---|---|---|---|
| H4a utilizable | mediana dentro de ±10 % para t/h ≥ 6 en las 3 formas | **Apoyada** (peor: cilindro, −5.1 % a t/h = 6) | 65 % |
| H4b mejor que v0.1 | menor |sesgo| que `mc` y `faces` en ≥ 10 de 12 celdas | **Apoyada** (11/12) | 70 % |
| H4c límite honesto a 4 vóxeles | mediana dentro de ±25 % en las 3 formas | **Apoyada** (peor: cilindro, −11.3 %) | 60 % |

* La celda que falla en H4b es **oblato, t/h = 12**: `sdf` +2.3 % frente a `mc`
  −1.9 %. A resolución alta el estimador viejo ya es bueno y el nuevo tiene un
  sesgo positivo residual de ≈ +2 %.
* Predije que el cilindro (aristas vivas) rozaría el límite del 10 %; no lo
  rozó (−5.1 %). La parte «cilindro peor que las otras formas» sí se cumplió.
* **No usar `sdf` por debajo de ~4 vóxeles sin declarar el sesgo:** a t/h = 3
  subestima 7–20 %, a t/h = 2 subestima 18–44 % y a 1.5, 30–75 %. `faces`
  sobrestima ≈ +50 % cuando el objeto está resuelto: no es un estimador de área.
* **Alcance:** solo con umbral oráculo, imagen ideal y vóxel isótropo. Con
  segmentación real el área hereda además el sesgo de la segmentación.

## 4. Extensión exploratoria: limpieza mínima (`otsu_clean`)

`otsu_clean` = Otsu + quitar componentes < 8 vóxeles + rellenar cavidades
< 8 vóxeles.

**En las formas nuevas (sólidos simples), perfil realista:**

| t/h | topología correcta: Otsu → limpio | cambio del error mediano de V |
|---|---|---|
| 6 | 85.3 % → 99.7 % (+14.3) | 0.0 puntos |
| 8 | 90.1 % → 99.8 % (+9.7) | 0.0 puntos |
| 12 | 87.3 % → 100 % (+12.7) | −0.01 puntos |

Mi predicción era «≥ 10 puntos en t/h ≥ 6 y cambio de V < 1 punto» (70 %): se
puntúa **no cumplida** (9.7 < 10 a t/h = 8). El criterio estaba mal planteado:
con Otsu ya en 90.1 %, el máximo posible era +9.9 (ERRATA E12). Con imagen
ideal y t/h = 1.5, la limpieza **empeoró** la topología (99.9 % → 78.8 %).

**Auditoría en las 7 formas de H1 (semilla nueva 20261113, 60 réplicas por
celda, realista, vóxel isótropo; no preregistrada):**

| Forma | Efecto de la limpieza en la topología correcta |
|---|---|
| cáscara, tubo, toro | **+7 a +62 puntos** para t/h ≥ 3 (p. ej. cáscara, t/h = 12: 38 % → 100 %) |
| bola, elipsoide | +2 a +15 puntos entre t/h = 3 y 12; 0 donde ya aciertan todos (bola a t/h = 12) o ninguno (t/h ≤ 3 en la bola) |
| toro fino | +3 a +18 puntos para t/h ≥ 3 |
| **cáscara fina** | **−28 puntos a t/h = 3 y −93 puntos a t/h = 4** (93 % → 0 %); +3 a +10 desde t/h = 6 |

La cavidad real de la cáscara fina mide ~2 vóxeles de diámetro a t/h = 4
(< 8 vóxeles de volumen) y la limpieza la rellena. Es un límite de principio
de cualquier limpieza por tamaño, y mi prueba de la extensión no podía
mostrarlo porque solo usaba formas sin rasgos pequeños reales (ERRATA E11).
Se añadieron `clean_report` (cuenta lo borrado, para no limpiar en silencio) y
una prueba que fija el límite.

## 5. H5 — Prueba de estrés 2D tipo ecografía (sintética)

12 600 imágenes planas con moteado multiplicativo (semilla 20261112). No contiene
ninguna ecografía real.

| Hipótesis | Predicción | Resultado | Dato que decide |
|---|---|---|---|
| H5a área con oráculo e imagen ideal, t/h ≥ 4 | 85 % | **Apoyada** | peor |mediana| = 3.5 % (disco, t/h = 4); con t/h = 2 el disco llega a −4.5 % |
| H5b moteado crudo + Otsu destruye la topología del anillo | 80 % | **Apoyada** | 0.00 de topología correcta en los 7 niveles |
| H5c algún segmentador logra ≥ 0.95 de topología con compounding | 50 % | **No apoyada** | el mejor (`smoothed_otsu_s2`) llega a 0.70 con t/h = 20; el resto, ≤ 0.005 |
| H5d circunferencia ≤ 3.3 % con compounding y `smoothed_otsu`, t/h ≥ 8 | 55 % | **No apoyada** | disco t/h = 8: 5.8 % (elipse 2.8 %); a t/h = 12: 0.1 % y 0.4 % |
| H5e promediar mejora la circunferencia (t/h = 8) | 85 % | **Apoyada** | 6.8 % → 16.9 % (disco) y 4.9 % → 11.8 % (elipse) sin promediar |

* **H5c es el resultado más importante.** Incluso con 20 px a través del anillo,
  ningún segmentador sin limpieza recupera la topología con fiabilidad: el
  moteado deja huecos y motas. Ver una ecografía real de esa manera exige
  probar primero una limpieza (y su límite de la sección 4) en 2D.
* H5d falla por un solo nivel (t/h = 8, disco): es una descripción, no una
  rectificación; el criterio decía t/h ≥ 8.
* «No apoyada» en H5c vale **dentro de la rejilla probada** (t/h ≤ 20, un modelo
  de moteado, 4 segmentadores): no demuestra que no exista un régimen fiable.
* Post hoc (no preregistrado): suavizar con σ = 2 px supera a σ = 1 px en
  topología. Falta confirmarlo con datos nuevos.

## 6. Marcador de predicciones

| Predicción | P | Resultado |
|---|---|---|
| H3a | 60 % | acertada |
| H3b | 40 % | acertada (sorpresa) |
| H3c | 55 % | acertada |
| H4a | 65 % | acertada (en la parte del cilindro, mal: no rozó el 10 %) |
| H4b | 70 % | acertada |
| H4c | 60 % | acertada |
| `otsu_clean` | 70 % | **fallada** (techo, E12) |
| H5a | 85 % | acertada |
| H5b | 80 % | acertada |
| H5c | 50 % | **fallada** |
| H5d | 55 % | **fallada** |
| H5e | 85 % | acertada |

9 de 12 (aciertos esperados con mis probabilidades: ≈ 7.8). Con 12 predicciones
esto no permite concluir que mi criterio esté calibrado; solo que en v0.2 acerté
más que en v0.1 (3 de 9), en parte porque las hipótesis eran más modestas.

## 7. Qué no se puede concluir

* Nada sobre embriones, ecografías ni imágenes clínicas.
* Nada sobre formas con ramas, plegamientos ni artefactos de adquisición
  (sombras, atenuación, reverberación), ni sobre ruido no gaussiano en 3D.
* Que Q sea «una ley»: es una regla empírica que se sostuvo en 3 formas
  convexas y finas, con una explicación geométrica plausible.
* Que la limpieza sea segura: ver sección 4.
* Que mis valores de umbral (8 vóxeles, σ = 0.5, σ = 1 o 2 px) sean óptimos: son
  decisiones mías.

## 8. Qué sigue (en orden)

1. Una limpieza 2D con tamaño dependiente de la resolución, probada **también**
   donde puede dañar (anillos finos), antes de mirar topología en ecografía.
2. Datos abiertos con licencia y consentimiento claros (ver
   [`DATOS_REALES_Y_ETICA.md`](DATOS_REALES_Y_ETICA.md)); cualquier imagen
   humana solo con base legal, anonimización y aprobación ética confirmadas.
3. Revisión científica humana externa antes de cualquier uso fuera de
   investigación y docencia.

## 9. Cómo reproducir

```bash
python scripts/freeze_h3_models.py     # ya hecho; los coeficientes están en results/summary
python scripts/run_h3.py --reps 200 --jobs 2      # ~16 min con 2 núcleos
python scripts/analyze_h3.py
python scripts/run_2d.py && python scripts/analyze_2d.py
python scripts/explore_v02_extras.py   # exploratorio, ~3 min
```
