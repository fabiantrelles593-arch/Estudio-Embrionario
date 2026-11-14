# Preregistro — H13: ¿se puede certificar una medida biométrica temprana con la incertidumbre propagada hasta la decisión? (Programa B, v0.6)

> Se escribe **después** de un piloto con semilla propia (20261211) y **antes** de calibrar (semilla
> 20261212) y de confirmar (semilla 20261213). Solo investigación y educación. **Todo es simulación**: no hay
> ecografías de personas ni de animales en este estudio, y nada de lo que sigue dice algo sobre uso clínico.

## 1. Pregunta

El proyecto ya sabe certificar una medida de volumen o de topología (v0.4 y v0.5) y negarse fuera de lo
calibrado. La pregunta de H13 es la siguiente, y es la que importa para algo clínico:

> Si el error de medida se calibra en una cuadrícula de condiciones de imagen y se propaga hasta la
> pregunta que alguien tiene que contestar —**¿cuántos días de edad gestacional puede estar equivocada una
> datación por longitud cráneo-rabadilla (CRL)?** y **¿está el grosor medido del mismo lado de un umbral que
> el grosor verdadero?**— ¿acierta el certificado cuando dice «verde» y se niega cuando las condiciones no están
> calibradas?

Lo que es nuevo respecto de lo anterior: el certificado ya no habla de «% de error de volumen» sino de una
cantidad con significado para quien decide (días; lado de un umbral), y la prueba se hace con verdad exacta.
Lo que **no** es nuevo: la metodología (fantomas con verdad conocida, modelo de error congelado, confirmación
con semillas nuevas, guardia de dominio) es la de H12 aplicada a otra medida.

## 2. Diseño (fijo)

**Fantomas 2D con verdad exacta** (`geovida.biometry`):

* `body`: cápsula de largo `L` y ancho `L/2`. Imita la CRL. Verdad = `L`. Medida = diámetro máximo de Feret
  del mayor componente (entre esquinas de píxel).
* `slot`: bloque claro de `7T × 5T` con una ranura oscura de grosor `T` y largo `4T`. Imita la translucencia
  nucal (NT). Verdad = `T`. Medida = `2·máx(EDT) − 1` píxeles del hueco interior mayor del mayor componente
  (0 si no hay hueco).

**Imagen**: el simulador 2D de `geovida.twod` (rotación y desplazamiento subpíxel al azar; contraste 4:1;
moteado multiplicativo de **3 miradas** como `us_raw` de H12; grano `máx(2, fwhm)` píxeles). Segmentadores:
`smoothed_otsu` (σ = 1 px; **primario**, el único que obtuvo verdes en H12) y `otsu` (secundario, control).

**Variables de condición**: `n` = píxeles a lo largo de la magnitud medida (el píxel mide `h = tamaño / n`) y
`fwhm_px` = ancho de la función de dispersión del punto en píxeles.

| | `n` | `fwhm_px` |
|---|---|---|
| cuerpo | 50, 80, 130, 210, 300 | 1.0, 2.0, 3.5, 5.0 |
| ranura | 10, 15, 22, 33, 50 | 1.0, 1.5, 2.2, 3.3, 5.0 |

**Calibración** (semilla 20261212): 100 repeticiones por celda (2 000 imágenes de cuerpo, 2 500 de ranura).
Error `e = medido − verdad` en píxeles; por celda y segmentador se guardan media (sesgo) y desviación típica
(ddof = 1). El modelo interpola ambos **linealmente en (ln n, ln fwhm_px)** y devuelve «sin predicción» fuera
de la caja. Se congela en `results/summary/h13_frozen.json` con su SHA-256 y se commitea **antes** de confirmar.

**Confirmación** (semilla 20261213, modelos congelados, árbol de código limpio): por tipo, 1 500 casos con
`(n, fwhm_px)` log-uniformes **dentro** de la caja (fuera de los nodos) y 400 casos **claramente fuera** (a ≥ 1.2
veces del borde, repartidos en las regiones `n_high`, `n_low`, `f_high`, `f_low`). Tamaño verdadero: cuerpo
`L ∼ U[20, 90]` mm (dentro del rango 15–95 mm de la fórmula); ranura `T ∼ U[1.5, 4.5]` mm (alrededor del umbral).

**Certificados** (`geovida.dating`, `geovida.biometry`). Con la medida `m`, el píxel `h` y el ancho declarado
`f` se calcula `n = m / h`. Si `n` o `f` caen fuera de la caja, o `m ≤ 0`: **amarillo, nunca verde**.

* *Datación (cuerpo)*: edad `GA(CRL) = 40.9041 + 3.21585·√CRL + 0.348956·CRL` días (INTERGROWTH-21st,
  Papageorghiou et al. 2014; CRL 15–95 mm). El error de edad causado por la medida es `GA'(CRL)·e`; `p` =
  P(|error de edad| ≤ **1 día**) con `e ∼ N(sesgo, sd)` del modelo. Verde `p ≥ 0.90`; rojo `p < 0.50`; amarillo el
  resto; fuera de 15–95 mm nunca verde. Se informa además la **fracción de la varianza de la edad que pone la
  medida** frente a la dispersión biológica de la fórmula (`SD(GA) = 2.39102 + 0.0193474·CRL` días).
* *Decisión (ranura)*: el valor verdadero se modela `N(medido − sesgo, sd²)`; `p` = P(el lado del umbral del valor
  medido es el del verdadero). Umbral **ilustrativo de 3.0 mm; no es un criterio clínico ni diagnóstico**. Verde
  `p ≥ 0.90`; rojo `p ≤ 0.50` (con 0.5 el lado no es más fiable que una moneda); amarillo el resto.

**Acierto** (se calcula con la verdad, no con el certificado): cuerpo, |GA(medido) − GA(verdadero)| ≤ 1 día;
ranura, el lado del umbral de lo medido es el del verdadero (en el umbral cuenta como «arriba»).

## 3. Qué se sabe del piloto (y qué cambió por él)

Semilla 20261211, 10 repeticiones por celda, 100 casos dentro y 40 fuera por tipo. El piloto **solo** se usó
para ajustar el diseño y escribir predicciones; ninguna cifra de él es resultado.

* Con `fwhm_px = 5` la ranura medida es bimodal (a veces se halla, a veces la fragmentación del moteado la abre al
  exterior): sesgos de −4 a −23 px y desviaciones de hasta 21 px. Un modelo de sesgo y desviación **gaussiano**
  describe mal esas celdas; se espera que ahí el certificado sea rojo, pero el riesgo es que un verde caiga cerca.
* Dos de 40 casos de ranura fuera de la caja recibieron verde. No es un error de código: el `n` del certificado sale
  de la **medida**, no de la verdad (que no se conoce al certificar), y cerca del borde el `n` medido puede caer
  dentro. **Cambio**: el criterio de H13d dejó de ser «cero verdes fuera» (que no se puede garantizar) y pasó a «tasa
  de fuga ≤ 5 %» con intervalo.
* Un modelo que extrapolara al borde habría tenido falsos verdes en la ranura (4 de 31 en el piloto) y ninguno en el
  cuerpo (0 de 20): la guardia importa sobre todo en la ranura.
* **Cambio**: H13e se informa para todos los casos con certificado **y** para los verdes por separado, porque en el
  piloto los verdes tenían colas pesadas (mediana 0.04 mm, percentil 95 de 1.3 mm).

## 4. Hipótesis y criterios (fijos)

Remuestreo (bootstrap) por caso: 2 000 réplicas, semilla 20261214, intervalo percentil del 95 %. «No evaluable»
nunca es «no apoyada».

* **H13a — Datación: la luz verde no falla demasiado (primaria).** Entre las luces verdes del cuerpo
  (`smoothed_otsu`, dentro de la caja), la fracción de casos con |error de edad| > 1 día es ≤ 10 %.
  *Apoyada*: límite superior del IC ≤ 10 %. *No apoyada*: límite inferior > 10 %. *No concluyente*: el IC contiene el 10 %.
  *No evaluable*: < 30 verdes.
* **H13b — Decisión: la luz verde no falla demasiado (primaria).** Igual, con la ranura y «lado del umbral equivocado».
* **H13c — Calibración.** Error de calibración esperado (ECE, 10 cubos iguales) de la probabilidad `p` frente al acierto,
  con todos los casos dentro de la caja con certificado, por tipo. *Apoyada* si el ECE ≤ 0.10 en **ambos**; *no apoyada* si
  alguno > 0.10; *no evaluable* si < 200 casos. Se publica el IC por bootstrap, sin usarlo en el veredicto.
* **H13d — La guardia se niega fuera de lo calibrado.** Tasa de fuga = fracción de casos claramente fuera de la caja con luz
  verde, por tipo. *Apoyada*: límite superior del IC ≤ 5 %. *No apoyada*: límite inferior > 5 %. *No concluyente*: el IC
  contiene el 5 %. *No evaluable*: < 100 casos fuera. Se informan, sin criterio, el acierto de los verdes filtrados y los
  falsos verdes que habría tenido un modelo que extrapola al borde.
* **H13e — Frente a un operador humano (descriptiva, sin criterio).** Error de la NT simulada, corregido por el sesgo
  modelado, en mm: mediana, percentil 95, desviación y fracción dentro de 0.25 mm y 0.40 mm, para todos los casos con
  certificado y para los verdes. 0.25 y 0.40 mm son la repetibilidad publicada de la NT (PubMed 10895448: desviación
  típica de las diferencias entre dos mediciones 0.35 mm mismo operador y 0.56 mm entre operadores, dividida por √2 para
  una sola medición). **No se puede concluir «mejor que un operador»**: la tarea, la imagen y el píxel son otros.
* **H13f — ¿Es la medida lo que limita la datación? (descriptiva).** Mediana, percentil 90 y fracción > 0.5 de la fracción de
  varianza de la edad que pone la medida, entre los certificados de cuerpo con modelo.

## 5. Lo que se hace según el resultado (decidido de antemano)

| Resultado | Qué se concluye | Siguiente paso |
|---|---|---|
| H13a o H13b **apoyada** | En este simulador, con estas condiciones calibradas, las luces verdes acertaron. No se generaliza a imagen real. | Probar con ecografía real de animal con referencia (H11/H12R). |
| H13a o H13b **no apoyada** | El certificado dice «verde» y falla. Se publica tal cual. | Revisar celda por celda dónde falla (ver colas pesadas). |
| H13c **no apoyada** | El modelo gaussiano no es una probabilidad fiable. | **H14** (otra hipótesis, otro preregistro, otras semillas): certificado con la distribución empírica de residuos por celda en lugar de normal. |
| H13d **no apoyada** | La guardia por `n` medido deja pasar demasiado. | Guardia con margen en `n` o con el ancho de la función de dispersión estimado desde la imagen. |
| **no concluyente** | Faltan casos. | Más casos con las mismas reglas. |

## 6. Predicciones escritas de antemano (después del piloto, antes de calibrar)

| Predicción | Probabilidad |
|---|---|
| H13a **apoyada** | 85 % |
| H13b **apoyada** | 55 % (no concluyente 30 %, no apoyada 15 %) |
| H13c **apoyada** (ECE ≤ 0.10 en cuerpo y ranura) | 45 % |
| H13d **apoyada** en el cuerpo / en la ranura | 90 % / 35 % |
| El modelo que extrapola (sin guardia) tiene un falso verde mayor que 10 % en la ranura fuera de la caja | 60 % |
| Mediana del error de la NT en los verdes < 0.25 mm | 80 % |
| Mediana de la fracción de varianza que pone la medida (H13f) < 0.25 | 90 % |

## 7. Qué no se puede concluir

* **Esto es simulación.** El moteado, la relación entre el ancho de la función de dispersión y el píxel, y la forma de
  la ranura son **supuestos sin validar** con ecografía real. Un fantoma 2D con ranura limpia no es una nuca fetal.
* **La CRL de verdad se mide a mano** sobre un corte sagital de un feto que se mueve, con el calibrador en los
  extremos reales de la cabeza y las nalgas: aquí la medida es el diámetro de Feret de una cápsula segmentada.
* **El umbral de 3.0 mm es ilustrativo.** No es un criterio diagnóstico ni de cribado y no se evalúa ningún
  rendimiento de cribado.
* La fórmula de datación describe una población; la dispersión biológica de la edad (varios días) es mayor que
  la que pone la medida cuando esta es buena. **Una datación certificada no es una datación correcta.**
* Una luz verde sigue sin ser una validación clínica. El paquete clínico del proyecto sigue siendo un borrador
  de ingeniería, no aprobado por ninguna autoridad.
* No se procesó ninguna imagen de personas. Cualquier uso futuro con ecografías humanas exige consentimiento
  informado, anonimización completa, base legal y aprobación de un comité de ética.

## 8. Desviaciones

(Ninguna al momento del primer commit.)
