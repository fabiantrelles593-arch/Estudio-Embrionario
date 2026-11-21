# Resultados v0.10 — H16: una guardia de cadena que se entera, solo con la imagen, de que el certificado dejó de valer (simulación)

> Solo investigación y educación. **Todo es simulación**: ninguna imagen real entra en el ajuste ni en la confirmación. La imagen real n = 1 de v0.8 solo aparece en un control exploratorio (§5.3) que no certifica nada.
> Protocolo: `docs/PREREGISTRO_H16.md` (commit 1a2bdd8, antes de generar el ajuste y la confirmación). Guardia congelada: `results/summary/h16_chain_frozen.json` (commit a72c735, antes de la confirmación).
> Confirmación con código limpio (`code_dirty: false`, a72c735), un solo análisis (`scripts/analyze_h16.py`).

## 1. Resumen honesto

* **Sí, en simulación, el certificado de datación puede dejar de ser engañado por la cadena** sin vaciarse: con cadenas que la guardia vio, los falsos verdes de CRL bajan de **13.9 %** (semáforo base, IC 95 % 11.6–16.4 %) a **5.6 %** (3.7–7.5 %) y la probabilidad queda calibrada (ECE 0.034).
  Se conserva el **64 %** de los verdes correctos que daba el semáforo sobre la imagen limpia.
* **Con una cadena que nunca vio** (familia B: otra curva de tono, mapa de color inventado, más desenfoque y ruido), los falsos verdes son **2.9 %** (1.1–5.2 %) y ECE 0.052. **Pero el precio es alto: solo conserva el 30 %** de los verdes correctos
  (IC 27.0–33.4 %; hipótesis de utilidad **no apoyada**), porque rechaza el 64 % de las imágenes de B por no parecerse a nada de lo visto. Es **seguridad por rechazo**, y así lo dejé escrito de antemano.
* **Lo que no demuestra la familia B por sí sola:** el semáforo base tuvo 9.5 % de falsos verdes de CRL en B (IC 7.5–11.6 %, «no concluyente»), de modo que B en conjunto no prueba que el semáforo base falle. La evidencia de que la guardia protege frente a lo no visto viene de un corte **exploratorio**:
  con curvas compresivas (`γ < 0.8`) el semáforo base falla **14.1 %** y la guardia **4.1 %** (173 verdes).
* **El primer diseño (sumar varianza extra) quedó como secundario por una razón de fondo:** casi no deja verdes de CRL (156 y 56 de ~800) y su probabilidad está mal calibrada (ECE 0.16 y 0.28). Que sus falsos verdes sean bajos es una seguridad vacía.
* **La imagen real n = 1 cae fuera del soporte de la guardia** (en los dos diseños, cuerpo y ranura): su variación local es más baja que la de cualquier cadena simulada. La guardia **se niega**, como debe; el tope amarillo de `geovida.real2d` **no cambia**.
* **No es evidencia sobre ninguna ecografía real.** Las dos cadenas son mías, el mapa de color es inventado y el diseño principal se ajusta con respuestas verdaderas conocidas que una imagen real no tiene.

## 2. Qué se construyó

* **`geovida.chainguard`** (34 pruebas; 16 daños deliberados al código comprobados, además de 12 en `geovida.h16`): dos índices de la propia imagen (`ln_cv`, variación local en zonas sin bordes; `skew`, asimetría), un **soporte** por régimen (caja de los percentiles 1–99 vistos en `clean` y `chain`) y dos formas de certificar:
  * **Diseño 2 (principal): recalibración condicionada a la imagen.** Regresión logística de «la medida fue correcta» sobre `logit(p_base)` y los dos índices, por tipo y régimen. No supone una forma para el error extra.
  * **Diseño 1 (secundario): ajuste paramétrico.** Desplazamiento medio y varianza extra por tercil de `ln_cv`.
  Fuera de todas las cajas: **no hay luz verde**.
* **`geovida.h16`** y **`geovida.printchain`** (familia B nueva): casos, ejecución (mismo render sin y con cadena), entrenamiento, certificado ajustado y reglas de veredicto de H13 reutilizadas.
* El certificado de la guardia recibe **solo** el valor medido, el tamaño de píxel, el desenfoque declarado y los dos índices. Nunca la verdad ni los parámetros de la cadena.

## 3. Resultados de la confirmación (1 500 casos por tipo y familia; bootstrap 2 000, semilla 20261214)

### 3.1 Diseño principal (recalibración)

| Hipótesis | Resultado | Veredicto |
|---|---|---|
| **H16a** CRL, cadena vista (A): falso verde ≤ 10 % | 540 verdes, **5.6 %** (IC 3.7–7.5 %) | **apoyada** |
| **H16b** CRL, cadena no vista (B): falso verde ≤ 10 % | 242 verdes, **2.9 %** (1.1–5.2 %) | **apoyada** |
| **H16c** ECE ≤ 0.10 (A y B) | A: 0.034 (0.028–0.057), n = 1 417 · B: 0.052 (0.039–0.084), n = 525 | **apoyada** |
| **H16d** utilidad: verdes correctos conservados ≥ 0.5 | A: 510/797 = **0.64** (0.607–0.671) · B: 235/780 = **0.30** (0.270–0.334) | A **apoyada**, B **no apoyada** → combinada **no apoyada** |
| **H16e** ranura: falso verde ≤ 10 % (A y B) | A: 854 verdes, 0.8 % (0.2–1.4 %) · B: 310 verdes, 0.3 % (0.0–1.0 %) | **apoyada** |
| **H16f** costo sin cadena (≥ 0.90 de los verdes y falso verde no «no apoyada») | CRL: 801 → 913 verdes (1.14), falso verde 1.1 % · ranura: 878 → 871 (0.99), 0.5 % | **apoyada** |

Según la tabla de decisión escrita de antemano, la fila que corresponde es: *«H16a y H16b apoyadas, H16d no apoyada en B → la guardia es segura por rechazo; pierde utilidad frente a cadenas nuevas»*.
(H16f en CRL da más de 1: sin cadena la guardia recalibrada da más verdes que el semáforo base con 1.1 % de falsos verdes; no lo leo como una mejora del método, sino como que el semáforo base es conservador sin cadena.)

### 3.2 Referencia: el semáforo base con cadena (descriptivo)

| | Verdes | Falso verde (IC 95 %) | Regla |
|---|---|---|---|
| CRL, A | 798 | 13.9 % (11.6–16.4 %) | no apoyada |
| CRL, B | 778 | 9.5 % (7.5–11.6 %) | no concluyente |
| Ranura, A | 841 | 0.2 % (0.0–0.6 %) | apoyada |
| Ranura, B | 781 | 2.8 % (1.7–4.0 %) | apoyada |

### 3.3 Diseño secundario (ajuste paramétrico)

| | Resultado |
|---|---|
| H16a / H16b | 156 y 56 verdes; falsos verdes 0.6 % y 0.0 % → «apoyadas», pero con casi ningún verde: seguridad vacía |
| H16c | ECE A 0.156, B 0.279 → **no apoyada** |
| H16d | A 0.194, B 0.072 → **no apoyada** |
| H16e, H16f | apoyadas |

### 3.4 Rechazo por quedar fuera del soporte (descriptivo)

| | Con certificado base | Rechazadas por la guardia |
|---|---|---|
| CRL, A | 1 486 | 69 (4.6 %) |
| Ranura, A | 988 | 35 (3.5 %) |
| CRL, B | 1 452 | 927 (**63.8 %**) |
| Ranura, B | 870 | 524 (**60.2 %**) |

## 4. Predicciones escritas de antemano (después del piloto)

| Predicción | Prob. | Ocurrió |
|---|---|---|
| H16a apoyada (diseño 2) | 70 % | **sí** |
| H16a no apoyada (diseño 2) | 8 % | no |
| H16b apoyada | 50 % | **sí** |
| H16c apoyada (A y B) | 40 % | **sí** |
| H16d apoyada en A | 40 % | **sí** |
| H16d apoyada en B | 3 % | no |
| H16e apoyada | 90 % | **sí** |
| H16f apoyada | 55 % | **sí** |
| Diseño 1: H16a no evaluable (< 30 verdes) | 85 % | **no** (156 verdes; con 400 casos del piloto eran 7) |
| La guardia rechaza > 50 % de las imágenes de B (CRL) | 85 % | **sí** (63.8 %) |
| La imagen real n = 1 cae fuera del soporte | 85 % | **sí** |

Brier de las 11 predicciones: **0.186** (decir siempre 50 % daría 0.25). El error grande fue el del diseño 1: extrapolé el piloto de 400 casos a 1 500 sin pensar que el número de verdes crece con el tamaño de la muestra. Once predicciones, muchas correlacionadas, dicen poco de mi calibración.

## 5. Exploratorio (no estaba en las reglas de veredicto)

### 5.1 Familia B por curva de tono (CRL, diseño principal)

| Curva | Casos | Semáforo base: verdes · falso verde | Guardia: verdes · falso verde | Rechazadas |
|---|---|---|---|---|
| Compresiva (`γ < 0.8`) | 708 | 361 · **14.1 %** | 173 · **4.1 %** | 268 |
| Intermedia (0.8–1.25) | 325 | 164 · 0.0 % | 64 · 0.0 % | 245 |
| Oscurecedora (`γ > 1.25`) | 467 | 253 · 9.1 % | **5** · (no se interpreta) | 462 |

Ranura: con `γ > 1.25` el semáforo base falla 9.3 % y la guardia da 3 verdes. **Lectura:** donde la cadena nueva es una compresión (parecida en espíritu a la vista), la guardia conserva verdes y baja los falsos verdes; donde la cadena oscurece (algo que A nunca hace), la guardia **no la reconoce** y rechaza casi todo.

### 5.2 «Detectar que no es crudo» es trivial (como se avisó en el preregistro)

La imagen sin cadena es envolvente cruda, así que cualquier imagen comprimida se separa de ella en `ln_cv`. Esto no cuenta como resultado: una foto real nunca es cruda.

### 5.3 La imagen real n = 1

`scripts/real2d_chainguard.py` (escrito **después** de ver los resultados de confirmación; imprime solo números): en la ROI, `ln_cv = −2.61` y `skew = 0.35`; en la ROI ensanchada, `−2.90` y `0.12`.
La caja de las cadenas simuladas es `ln_cv` ∈ [−2.02, −0.96] (CRL) y [−2.07, −0.95] (ranura): la imagen real es **más plana que cualquier cadena simulada**, y cae fuera del soporte en los dos diseños y los dos tipos.
Esto **no dice que la imagen real sea mala**: dice que el simulador no se le parece (el tejido real tiene su propio grano y el equipo suele suavizarlo). **El certificado de la guardia no se aplica a esa imagen.**

## 6. Qué se puede y qué no se puede decir

* **Se puede decir (en simulación):** un certificado que condiciona su probabilidad a dos índices de la propia imagen mantiene los falsos verdes de CRL por debajo del 10 % y calibrada su probabilidad frente a una cadena vista y frente a una nueva de otro tipo, y deja de regalar los verdes que se vuelven engañosos.
  Lo hace en parte **rechazando** lo que no se parece a lo visto, y ese rechazo cuesta utilidad (30 % conservada en B).
* **No se puede decir:** que funcione con una cadena real, con un equipo real o con fotos de impresiones reales (la imagen real n = 1 ni siquiera cae en el soporte); que la guardia reconozca *qué* cadena pasó (no estima la curva de tono ni el desenfoque);
  que el diseño principal sirva sin respuestas verdaderas conocidas (hacen falta maniquíes pasados por la misma cadena); que B por sí sola pruebe que el semáforo base falla (9.5 %, «no concluyente»).
* **No levanta el tope amarillo de `geovida.real2d`.**
* **Novedad:** no revisé la literatura para afirmar que esta combinación (soporte por régimen + recalibración condicionada a índices de la imagen) sea nueva. Está emparentada con la detección de datos fuera de distribución y con la recalibración de probabilidades; es una **propuesta técnica** probada en simulación, no un hallazgo establecido.

## 7. Desviaciones y errores míos (declarados)

* **El piloto cambió dos decisiones** (declaradas en el preregistro §2 y §4): el diseño 2 se escribió después de ver que el diseño 1 vaciaba los verdes de CRL, y el rango de `γ` de B se ensanchó de [0.5, 1.6] a [0.3, 2.5] porque con el original el semáforo base casi no fallaba (0.6 %) y B no podía discriminar nada.
  Las semillas de ajuste y de confirmación son otras; aun así, B no es una prueba «ciega» de la guardia: la elegí después de ver cómo se comportaba el semáforo base.
* **Errores de mis pruebas, corregidos antes de usarlas:** una prueba de familia B comparaba un solo segmentador cuya longitud es múltiplo de píxel y coincidió por azar (ahora compara los dos y cuenta en varios sorteos); la tolerancia de una prueba de recuperación era menor que dos errores estándar del tramo más ruidoso (ahora es 4 errores estándar por tramo);
  una prueba de ranura usaba un `n` fuera de la caja que yo mismo había definido; una prueba no probaba nada (la quité); una línea basura en otra (la quité).
* **Mutaciones:** al comprobar mis pruebas con daños deliberados al código, 5 sobrevivieron (qué probabilidad gana cuando se solapan dos regímenes, el umbral verde, el intercepto penalizado, el filtro de casos fuera de la caja y el conteo de rechazos de la guardia elegida) y escribí pruebas para cada una; una vez, un fallo de mi propio script de mutaciones dejó una mutación puesta unos minutos en `chainguard.py`: se restauró desde copia y se volvió a correr todo.
* **Las reglas de veredicto y el análisis no cambiaron** tras ver los datos de confirmación. `scripts/figure_h16.py` y `scripts/real2d_chainguard.py` se escribieron después de ver los resultados (solo dibujan o miden descriptivamente).

## 8. Siguiente

* **H17** sigue esperando datos seriados reales; `geovida.agreement` espera ≥ 2 lectores en varios individuos.
* La mejora honesta de esta guardia es **diversidad de cadenas en el ajuste**, no aflojar el soporte; y, para llegar a una imagen real, **maniquíes de verdad conocida fotografiados por la misma cadena** (G1 de `docs/RUTA_DE_VALIDACION_REAL.md`).
* Prototipo interactivo en el navegador (calibrar escala, medir CRL, propagar la incertidumbre a la edad y mostrar cuándo la herramienta se niega): en preparación.
