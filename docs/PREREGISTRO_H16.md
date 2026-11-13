# Preregistro — H16: ¿puede el certificado enterarse, solo con la imagen, de que pasó por una cadena? (Programa B, v0.10)

> Se escribe **después** de un piloto declarado (semilla 20261220) y **antes** de generar ninguna imagen de ajuste (semilla 20261221) ni de confirmación (semillas 20261222 y 20261223).
> Solo investigación y educación. **Todo es simulación**; ninguna imagen real entra en el ajuste ni en la confirmación.

## 1. Pregunta

H15 mostró que el certificado congelado de H14 **no se entera** de que la imagen pasó por pantalla, impresión y foto: con cadena, la datación por CRL tuvo 11.9 % de verdes equivocados
(frente a 1.2 % sin cadena) y el semáforo dio casi los mismos verdes (776 contra 774). La salida de H15 era: «inflar la incertidumbre según la cadena o exigir la imagen en bruto».

> ¿Puede el programa, **usando solo la imagen, el tamaño de píxel y el desenfoque declarado** (nunca la verdad ni los parámetros de la cadena), ajustar su certificado de modo que
> (a) los falsos verdes se mantengan ≤ 10 % con cadenas **que vio** y con cadenas **que no vio**, (b) su probabilidad siga calibrada, y (c) no regale su utilidad (siga dando verdes correctos) ni la pierda en imágenes sin cadena?

El interés está en la **tensión**: se puede lograr (a) trivialmente negándose a todo; por eso (c) es parte de la pregunta.

## 2. La guardia de cadena (`geovida.chainguard`) — fija

**Índices de la imagen** (solo de los píxeles; imagen dividida por su percentil 99.5):

* `ln_cv`: logaritmo de la mediana de la variación local (sd/media en ventanas de 7 × 7 px) en los píxeles «planos» (gradiente suavizado σ = 1.5 px por debajo de su mediana, media local > 0.02, sd local > 1e-4; mínimo 200 píxeles). Baja cuando una compresión tonal aplana el grano.
* `skew`: asimetría (tercer momento estandarizado) de las intensidades. Imagen menor de 32 px de lado o plana: `nan`, y `nan` nunca recibe certificado.

**Regímenes y soporte.** Con el conjunto de ajuste (§4) se definen dos regímenes por tipo (`clean`: la misma imagen sin cadena; `chain`: con cadena de la familia A). El **soporte** de cada régimen es la caja
`[percentil 1, percentil 99]` de `(ln_cv, skew)` observada en él. Una imagen fuera de **todas** las cajas (incluido el hueco entre regímenes) **no recibe luz verde** (amarillo, «la imagen no se parece a ninguna cadena vista»).
Si cae en más de una caja se toma la estimación más conservadora.

**Dos diseños**, ambos con el mismo soporte:

* **Diseño 2 — recalibración condicionada a la imagen (PRINCIPAL).** Por tipo y régimen, regresión logística con penalización L2 (λ = 1, sin penalizar el intercepto) de «la medida fue correcta» sobre `[logit(p_base), ln_cv, skew]`
  estandarizadas, con los casos de ajuste. `p_base` es la probabilidad que da el certificado congelado de H14. La luz se decide con los umbrales de siempre (verde ≥ 0.90; rojo < 0.50 en datación, ≤ 0.50 en decisión; datación fuera de 15–95 mm nunca verde).
* **Diseño 1 — ajuste paramétrico (SECUNDARIO).** Por tipo, régimen y tercil de `ln_cv`: desplazamiento medio del error de longitud (px) y varianza extra (px², no negativa) sobre lo que predice el modelo limpio; el modelo ajustado suma el desplazamiento al sesgo y la varianza extra a la varianza.

**Constantes fijadas aquí** (no se tocan después): ventana 7, ≥ 200 píxeles planos, terciles, cuantiles 0.01/0.99, ≥ 30 casos por tramo (diseño 1) y ≥ 100 filas por régimen (diseño 2), λ = 1, recorte de probabilidades a [1e-4, 1 − 1e-4].

**Por qué el diseño 2 es el principal (declarado):** el piloto mostró que el diseño 1 casi nunca deja pasar un verde de CRL con cadena (7 de 111), porque el error que mete la cadena no es gaussiano
(la mayoría de los casos sale bien y unos pocos fallan mucho) y una varianza media lo describe mal. El diseño 2 se escribió **después** de ver eso; por eso el piloto no puede contarse como evidencia a su favor.

## 3. Las dos familias de cadena (`geovida.printchain`) — fijas

* **Familia A** (la de H15, sin cambios): compresión logarítmica `a` log-uniforme en [3, 60]; gradiente de ganancia ±U[0, 0.25]; desenfoque σ = U[0.3, 1.0] px; ruido sd = U[0.01, 0.04]; JPEG calidad entera en [50, 90].
* **Familia B** (nunca vista por la guardia; **otro tipo de curva de tono, no un subconjunto de A**): la imagen pasa por `x^γ` y luego por la **luminancia de un mapa de color naranja inventado** (no es el de ningún equipo), normalizada; `γ` log-uniforme en **[0.3, 2.5]**
  (de 1/3.3 a 2.5: comprime u oscurece, como pantallas e impresoras; A nunca oscurece); gradiente de ganancia ±U[0, 0.40]; desenfoque σ = U[0.8, 1.6] px; ruido sd = U[0.03, 0.08]; JPEG calidad entera en [25, 60]. Todos los rangos de B superan a los de A en cada eje compartido.
* Semillas por caso `[semilla, 7, idx]`. **Ninguna es fiel a un equipo ni a una cámara**: son pruebas de esfuerzo de tipo plausible. El mapa de color es inventado; el efecto de un mapa real no se probó en ninguna simulación.

## 4. Qué se vio antes de escribir esto (declarado)

* **Exploración de índices** (semilla 20261220; 300 casos por tipo con familia A y 150 con familia B): vi cómo se reparten `ln_cv`, `skew` y otros índices candidatos (variación local, asimetría, razón p95/p50, pendiente de la variación local) sin cadena y con cadena, y su correlación con el desplazamiento de la medida.
  Con eso elegí `ln_cv` y `skew`. **Hallazgo trivial que no cuenta como prueba:** las imágenes sin cadena son envolvente cruda, así que cualquier imagen comprimida se separa de ellas (en el piloto, `ln_cv` va de ≈ 0.0 a 0.9 sin cadena y de ≈ −2.0 a −1.0 con cadena A); detectar «esto no es crudo» es fácil y no dice nada sobre una foto real, que nunca es cruda.
  La familia B se parece a A en `ln_cv` y se separa en `skew`.
* **Piloto** (semilla 20261220, 400 casos por tipo y familia; `results/summary/h16_pilot_manifest.json`, `h16_pilot_verdicts.json`): ajuste con los casos de índice par de A, evaluación con los impares de A y todos los de B. Resultado, **exploratorio**:
  * Diseño 1: con cadena A, 7 verdes de CRL de 111 que da el semáforo base; con B, 5 de 215. No es una guardia útil para la CRL; para la ranura sí (106 de 111).
  * Diseño 2 (cadena A, CRL): 67 verdes, 4.5 % equivocados (IC 95 % 0–10 %) frente al 13.5 % del semáforo base; conserva el 57 % de los verdes correctos de la imagen limpia. Con B: 57 verdes, 3.5 % equivocados, conserva el 25 %; rechaza (fuera de soporte) el 74 % de las imágenes con certificado base.
  * Sin cadena (CRL / ranura): 93 % y 92 % de los verdes del semáforo base.
* **Cambio de B tras el piloto (declarado):** la familia B original tenía `γ` en [0.5, 1.6]. En el piloto el semáforo base apenas fallaba con ella (0.6 % de falsos verdes de CRL), así que **no podía discriminar** si la guardia protege. Ensanché `γ` a [0.3, 2.5] (todo lo demás de B igual); con ese rango el semáforo base falla 7.4 % (CRL) y 3.8 % (ranura) en el piloto.
  Esta decisión usó resultados del piloto y se declara; las semillas de confirmación son otras.
* Modelos base: los congelados de H14 (`results/summary/h14_frozen.json`), sin recalibrar.

## 5. Diseño de la confirmación (fijo)

1. **Ajuste** (`python scripts/run_h16.py --set train`, semilla **20261221**): 1 500 casos por tipo dentro de la caja calibrada, familia A; cada caso aporta una fila sin cadena (régimen `clean`) y una con cadena (`chain`).
   Se ajustan **los dos diseños** y se escriben en `results/summary/h16_chain_frozen.json` (con su manifiesto y su SHA-256). **Se hace commit del congelado antes de generar ninguna confirmación.**
2. **Confirmación A** (`--set conf_a`, semilla **20261222**): 1 500 casos por tipo, familia A nueva.
3. **Confirmación B** (`--set conf_b`, semilla **20261223**): 1 500 casos por tipo, familia B (cadena nunca vista por la guardia).
4. Mismos casos sin y con cadena; segmentador primario `smoothed_otsu`; solo dentro de la caja calibrada. Código limpio (sin cambios sin commitear). **Un solo análisis** (`scripts/analyze_h16.py`), escrito antes de ver ningún resultado de confirmación.
5. Remuestreo por caso: 2 000 réplicas, semilla 20261214. «No evaluable» nunca es «no apoyada».

## 6. Hipótesis y criterios (fijos; para el diseño principal, y los mismos para el secundario)

* **H16a — Primaria. Datación con cadena vista.** Cuerpo, conjunto A, variante con cadena: falso verde entre los verdes ≤ 10 % (regla de H13a: *apoyada* si el límite superior del IC 95 % ≤ 10 %; *no apoyada* si el inferior > 10 %; *no concluyente* si el IC contiene el 10 %; *no evaluable* con < 30 verdes).
* **H16b — Datación con cadena no vista.** Igual, conjunto B.
* **H16c — Calibración.** ECE ≤ 0.10 (10 cubos) de la probabilidad de la guardia para el cuerpo, en A **y** en B (n ≥ 200 certificados cada uno; si uno no se cumple, no se apoya).
* **H16d — Utilidad.** Cociente entre los **verdes correctos de la guardia sobre la imagen con cadena** y los **verdes correctos del semáforo base sobre la imagen limpia** (mismos casos, cuerpo). *Apoyada* si el límite inferior del IC 95 % ≥ 0.5; *no apoyada* si el superior < 0.5; *no concluyente* en otro caso; *no evaluable* con < 30 verdes correctos de referencia. Se informa por familia; el veredicto combinado exige **A y B**.
* **H16e — Decisión (ranura).** Falso verde ≤ 10 % (misma regla que H16a) en A **y** en B.
* **H16f — Costo sin cadena.** Sobre las imágenes limpias del conjunto A: verdes de la guardia / verdes del semáforo base ≥ 0.90 **y** falso verde de la guardia no «no apoyada», para cuerpo **y** ranura.
* **Descriptivas (sin criterio):** falsos verdes del semáforo base con cadena (referencia); fracción rechazada por quedar fuera del soporte; verdes del semáforo base y de la guardia con y sin cadena.
* **Exploratorias:** (i) por tipo de curva de tono de B (`γ < 0.8`, `0.8–1.25`, `> 1.25`); (ii) con la imagen real n = 1 (permiso no verificado, nada identificable en el repositorio): solo **si cae dentro o fuera del soporte**, sin certificar nada.

## 7. Lo que se hace según el resultado (decidido de antemano)

| Resultado (diseño principal) | Qué se concluye | Siguiente paso |
|---|---|---|
| H16a, H16b, H16c, H16e y H16f apoyadas **y** H16d apoyada | En simulación, el certificado se vuelve robusto a cadenas vistas y no vistas **sin** vaciarse. | Mantener el tope de imagen real en `geovida.real2d`; la guardia no se aplica a imagen real hasta tener referencias reales (G1). |
| H16a y H16b apoyadas, **H16d no apoyada en B** | La guardia es segura por **rechazo**: protege porque se niega a lo que no vio, pero pierde utilidad frente a cadenas nuevas. | Se publica el costo; la mejora es aumentar la diversidad de cadenas del ajuste, no aflojar el soporte. |
| H16a **o** H16b no apoyadas o no concluyentes | La guardia **no** es segura frente a esa cadena. | No se usa; se documenta. |
| H16c no apoyada | La probabilidad de la guardia no es confiable. | Se publica la tabla de calibración. |
| H16f no apoyada | La guardia cuesta demasiado en imágenes limpias. | No se afloja nada: se rediseña el soporte. |
| Diseño secundario | Se informa con las mismas reglas; no sustituye al principal. | — |

**Nada de esto levanta el tope amarillo de `geovida.real2d`**: eso exige imagen real con referencia independiente (G1 de `docs/RUTA_DE_VALIDACION_REAL.md`).

## 8. Predicciones escritas de antemano (después del piloto)

| Predicción | Probabilidad |
|---|---|
| H16a **apoyada** (diseño 2) | 70 % |
| H16a **no apoyada** (diseño 2) | 8 % |
| H16b **apoyada** (diseño 2) | 50 % |
| H16c **apoyada** (diseño 2; A y B) | 40 % |
| H16d **apoyada** en A (diseño 2) | 40 % |
| H16d **apoyada** en B (diseño 2) | 3 % |
| H16e **apoyada** (diseño 2; A y B) | 90 % |
| H16f **apoyada** (diseño 2; cuerpo y ranura) | 55 % |
| Diseño 1: H16a **no evaluable** (< 30 verdes) | 85 % |
| La guardia rechaza > 50 % de las imágenes de B con certificado base (cuerpo) | 85 % |
| La imagen real n = 1 cae **fuera** del soporte | 85 % |

## 9. Qué no se puede concluir

* Es simulación: las dos familias de cadena son mías, sus rangos son supuestos y el mapa de color de B es inventado. Que la guardia resista **no** dice nada de ninguna ecografía real concreta.
* El diseño 2 se ajusta con **resultados verdaderos conocidos** (la simulación los da). Con imágenes reales harían falta objetos de verdad conocida (maniquíes) pasados por la misma cadena: eso es G1 y no existe.
* La guardia solo reconoce lo que se parece a lo visto; no estima la curva de tono, ni el desenfoque, ni identifica la cadena. «Fuera del soporte» es una alarma, no un diagnóstico.
* El desenfoque se declara verdadero, como en H15.
* Un resultado «apoyada» no levanta el tope de imagen real de `geovida.real2d`.

## 10. Desviaciones

*(Se llena después de la confirmación; si no hay ninguna, se dice.)*
