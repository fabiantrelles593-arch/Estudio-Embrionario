# Preregistro — H12: ¿se puede recalibrar el certificado para ecografía 3D simulada? (v0.5)

> Se confirma (`git commit` + `git push`) **antes** de correr la calibración
> (`scripts/run_h12.py --set cal`). El congelado (`results/summary/h12_frozen.json`) se confirma
> **antes** de los barridos de confirmación (`test`, `unseen`, `shift`). Los cambios posteriores van
> solo en «Desviaciones».

## 1. Pregunta y por qué importa

H11 prueba el certificado de v0.4 sobre ecografía 3D real de ratón y se espera que su guardia de
dominio **rechace** casi todo, porque el moteado de la ecografía no se parece al ruido gaussiano del
simulador de v0.1–v0.4. Un certificado que se niega es correcto pero **inútil** para quien trabaja con
ecografía. H12 pregunta si, con un simulador que sí tenga moteado y atenuación, se puede recalibrar el
certificado y conservar sus garantías (verde falso bajo, rechazo fuera de dominio) en imágenes de ese
tipo.

H12 es **sintético**. No toca ninguna imagen real ni dice nada sobre ecografía real: el simulador es
mínimo y sus parámetros son supuestos de diseño, no medidas de un ecógrafo. La prueba real es H11 (y
después H13, con datos reales).

### Lo que ya se sabe antes de preregistrar (sondeo exploratorio, **no** confirmatorio)

Un sondeo con una sola forma (bola), 3 niveles de resolución en dos perfiles y la semilla 20261122
(la del piloto de H9, reutilizada solo para esto) mostró:

* Con moteado, `global` y `otsu` tienen un **sesgo de volumen de −13 % a −35 % que no baja al subir la
  resolución** (hasta `t/h` = 32). El umbral se desplaza porque la intensidad del moteado no es
  gaussiana y porque la atenuación apaga la parte profunda. Un modelo que solo mira `d/h` no puede
  explicarlo: debería asignarles luz roja en todas partes.
* `smoothed_otsu` llega a Dice 0.93–0.98 y error de volumen ≤ 5 % desde `t/h` ≈ 12–16.
* Por eso se añadió a la rejilla el nivel `t/h` = 16 (el sondeo también miró 24 y 32: no cambian la
  historia). El nivel 24 se descartó por **coste de cómputo** (la mancuerna a `t/h` = 24 con vóxel
  isótropo tarda unos 95 s por realización; con 24 el barrido de calibración pasaba de ~35 a ~80 min).
  Es la única decisión de diseño que el sondeo y el coste cambiaron.

También se esperan, por tanto, **estratos no evaluables** (sin luces verdes suficientes). Eso es un
resultado válido, no un fallo del experimento.

### Lo que mostró el piloto (semilla 20261130, 1 réplica por celda; 480 realizaciones; **no** se reutiliza)

Se usó solo para ensayar el flujo completo (calibrar, congelar, evaluar) y para ajustar las predicciones.
Es diminuto y se evaluó en la misma muestra, así que **no prueba nada**.

* Fracción de medidas correctas por estrato (volumen / topología): `global` 0.8 % / 6.2 % (`us_compound`) y
  2.9 % / 0 % (`us_raw`); `otsu` 10.4 % / 0 % y 1.7 % / 0 %; `smoothed_otsu` 31.2 % / 30.8 % y 34.2 % /
  3.3 %. En `smoothed_otsu · us_compound` el volumen es correcto en 93 % de las realizaciones a `t/h` = 12
  y en 100 % a 16.
* El semáforo de volumen **de v0.4**, declarado `realistic`, no dio **ninguna** luz verde con `global` ni
  `otsu` (el moteado fragmenta la máscara y la profundidad media colapsa) y dio ~50 luces verdes con
  `smoothed_otsu`, **ninguna falsa**. La guardia de v0.4 rechazó el 100 % de las imágenes de
  `smoothed_otsu` y el 11 % y el 3 % de las de `global` y `otsu`. Es decir: contra lo que yo esperaba
  antes del piloto, v0.4 sin guardia no daba verdes falsos en ecografía simulada; con guardia, la
  certificación de ecografía queda **segura pero vacía**. Eso hace de H12h la hipótesis que importa.
* En el ensayo, las comprobaciones de H12b dieron 9 de 9 (en la misma muestra).

## 2. El simulador (extensión de `geovida.imaging`)

Pipeline: orientación aleatoria, volumen parcial, PSF gaussiana → **nivel de fondo** → **atenuación en
z** → **moteado multiplicativo** → ruido electrónico gaussiano aditivo.

| Parámetro | Significado | `us_compound` | `us_raw` | `us_atten` (desplazado) | `us_coarse` (desplazado) |
|---|---|---|---|---|---|
| `looks` | Promedio de campos de moteado independientes; contraste = 1/√looks | 8 | 3 | 8 | 8 |
| `grain_fwhm` | Tamaño del grano (× `h_xy`) | 1.5 | 1.5 | 1.5 | 3.0 |
| `psf_fwhm` | Desenfoque (× `h_xy`) | 1.5 | 1.5 | 1.5 | 2.5 |
| `atten` | Pérdida total en z (nepers) | 0.3 | 0.3 | **1.0** | 0.3 |
| `bg_level` | Fondo (objeto = 1) | 0.15 | 0.15 | 0.15 | 0.15 |
| `snr` (ruido electrónico) | contraste/σ | 20 | 20 | 20 | 20 |

* El moteado es completamente desarrollado: intensidad exponencial (contraste 1) por look, campo
  gaussiano complejo suavizado, media 1 (`geovida.imaging.speckle_field`).
* **No incluye** compresión logarítmica, sombras acústicas, reverberaciones ni variación espacial del
  grano. Los valores de la tabla son supuestos de diseño elegidos para producir moteado visible sin
  borrar el objeto; no se ajustaron a ninguna ecografía.
* Los perfiles antiguos (`ideal`, `realistic`, `blurry`, `noisy`, `mild_*`) producen **exactamente** las
  mismas imágenes que antes (prueba con huella fija); los nuevos van al final de la lista de semillas.

## 3. Diseño y protocolo (fijos)

| Conjunto | Formas | Perfiles | Niveles `t/h` | Anisotropía | Réplicas | Semilla |
|---|---|---|---|---|---|---|
| `cal` | las 10 de H6 | `us_compound`, `us_raw` | 1.5, 2, 3, 4, 6, 8, 12, **16** | 1, 2, 3 | 10 | 20261131 |
| `test` | las mismas 10 | ídem | ídem | ídem | 10 | 20261132 |
| `unseen` | mancuerna y copa | ídem | ídem | ídem | 8 | 20261132 |
| `shift` | las 10 | `us_atten`, `us_coarse` | ídem | ídem | 3 | 20261133 |
| `pilot` (solo depuración) | ídem | ídem | ídem | ídem | 2 | 20261130 |

* Segmentadores: `global`, `otsu`, `smoothed_otsu`, sin cambios. Seis estratos en `cal`, `test` y
  `unseen`; seis en `shift`.
* **Calibración** (`geovida.h12.freeze_us`): por estrato (segmentador × perfil), (i) modelo de volumen:
  logit de Pr(|error de V| ≤ 5 %) sobre ln(d̄/h_geo), como en H6; (ii) modelo topológico: conjunto de
  variables T1/T4/T7 elegido por validación cruzada dejando una forma fuera, igual que en H9; (iii)
  envolventes de la guardia (cuantiles 1 %–99 % de `snr_hat` y `edge_width`) sobre las filas de
  calibración con luz verde (p ≥ 0.90), solo con ≥ 50 filas verdes por estrato; si no, el estrato
  **no tiene envolvente y no puede dar verde**.
* **Luz emitida:** verde si p ≥ 0.90 **y** dentro de la envolvente; roja si p < 0.50.
* **Unidad:** una realización medida; los intervalos de verde falso son de Wilson.
* **Sin reajuste:** nada se cambia tras ver `test`, `unseen` o `shift`.
* **Estrato evaluable:** ≥ 200 luces verdes emitidas en `test`; ≥ 100 en `unseen` y `shift`. Un estrato
  sin ellas no se evalúa y se **lista**, no se esconde. Para AUC y ECE hacen falta ≥ 200 filas y que
  la clase minoritaria sea ≥ 5 %.
* **Comparación:** el certificado congelado de v0.4, declarado `realistic` (lo que haría un usuario que
  no sabe que su imagen tiene moteado).

## 4. Hipótesis y criterios (fijos)

**Primaria: H12c.** Las demás son secundarias.

* **H12a — v0.4 no transfiere sin guardia.** En `test`, el semáforo de **volumen** de v0.4 declarado
  `realistic` y **sin** guardia da verde falso > 10 % en al menos la mitad de los estratos evaluables
  (≥ 100 verdes) y en al menos uno.
* **H12b — La guardia distingue las modalidades en ambos sentidos.** (i) Las imágenes de `test` entran
  en el dominio de v0.4 (envolvente de volumen, declarado `realistic`) en ≤ 50 % para cada segmentador;
  (ii) las imágenes `realistic` del barrido de confirmación de v0.4 (`results/raw/h9_test.csv.gz`)
  entran en el dominio recalibrado en ≤ 50 % para cada segmentador y cada perfil de ecografía. Nueve
  comprobaciones. *Apoyada*: las 9. *Parcial*: ≥ 75 %. Un estrato sin envolvente cuenta como rechazo.
* **H12c — Verde falso bajo con luz emitida (primaria).** En `test`, en **todos** los estratos con algún
  extremo evaluable (≥ 200 verdes emitidos de volumen o de topología), el verde falso del extremo
  evaluable es ≤ 10 %. *No evaluable* si ningún estrato tiene un extremo evaluable. *No apoyada* si algún
  extremo evaluable supera 10 % (estimación puntual).
* **H12d — Calibración.** Entre los pares (estrato, extremo) con ≥ 200 filas y clase minoritaria ≥ 5 %,
  AUC ≥ 0.85 **y** ECE ≤ 0.10. *Apoyada* si cumplen ≥ 5/6 de los pares; *parcial* si ≥ 4/6; *no evaluable*
  si no hay pares.
* **H12e — Formas nunca vistas.** En `unseen` (mancuerna y copa), en todos los estratos evaluables
  (≥ 100 verdes emitidos), verde falso ≤ 10 % en volumen y topología. *No evaluable* si ninguno lo es.
* **H12f — Con guardia, el dominio desplazado se rechaza o es seguro.** En `shift`, declarando
  `us_compound`, los estratos con ≥ 100 verdes emitidos tienen verde falso ≤ 10 % en volumen y en
  topología. Los demás se cuentan como rechazados.
* **H12g — La guardia hace falta.** En `shift`, declarando `us_compound`, **sin** guardia, el semáforo
  de volumen supera 10 % de verde falso en al menos la mitad de los estratos evaluables (≥ 100 verdes) y
  en al menos uno.
* **H12h — Recalibrar paga.** En los estratos donde el certificado recalibrado es evaluable, entre las
  medidas correctas (|error de V| ≤ 5 %) la fracción que recibe verde emitido es **mayor** que con el
  certificado de v0.4 con su guardia.

Un valor no calculable es «no evaluable», nunca «no apoyada».

## 5. Predicciones escritas de antemano

(Escritas **después** del piloto y **antes** de calibrar. Un borrador previo daba 85 % a H12a y 40 % al
resto de lo que el piloto cambió; el piloto mostró que mi razonamiento sobre H12a estaba mal.)

| Predicción | Probabilidad |
|---|---|
| Los estratos `global` y `otsu` quedan **sin verdes de volumen** (no evaluables) | 90 % |
| Al menos un estrato (se espera `smoothed_otsu`) es evaluable en `test` | 92 % |
| H12a apoyada (v0.4 sin guardia da verdes falsos en ecografía simulada) | 12 % |
| H12b apoyada (las 9 comprobaciones) | 85 % |
| H12c apoyada (primaria), dado que es evaluable | 65 % |
| H12d apoyada | 35 % |
| H12e apoyada | 40 % |
| H12e no evaluable | 25 % |
| H12f apoyada | 70 % |
| H12g apoyada | 55 % |
| H12h apoyada, dado que es evaluable | 90 % |
| `smoothed_otsu · us_raw` no tiene verdes de topología evaluables (< 200) en `test` | 70 % |

## 6. Qué no se puede concluir

* Nada sobre ecografía real: el simulador es mínimo y sus parámetros son supuestos. Si H11 muestra que
  la guardia recalibrada también rechaza la ecografía real, se aprende que el simulador no se parece a
  ella (y el camino es H13: calibrar con datos reales).
* Que un segmentador «funcione» en ecografía: H12 mide si el certificado **sabe** cuánto fiarse, no si
  la segmentación es buena. Que `global` y `otsu` queden rojos es un resultado correcto del certificado.
* El verde falso se mide con formas de la familia usada y perfiles de moteado de este simulador.
* Una luz verde seguirá sin ser una validación: es una estimación calibrada con un simulador.

## 7. Desviaciones

(Ninguna al momento del primer commit.)
