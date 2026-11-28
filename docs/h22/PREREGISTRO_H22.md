# Preregistro — H22: ¿puede la guardia distinguir «fuera de dominio» de «inservible»? (v1.0, 21 nov 2026; **aprobado por el autor el 21 nov 2026, antes de medir**)

> Tarea P2 de `docs/INFORME_DE_PROGRESO.md` («estudiar si la guardia debería distinguir "fuera de dominio" de
> "inservible"; diseño escrito y probado en sintético antes de tocar datos reales»). Se sube a la rama **antes**
> de ejecutar `scripts/run_h22.py run`. Solo imágenes sintéticas con verdad analítica; ningún dato real ni
> clínico. Etiquetas: [HV] hecho verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta ·
> [PV] pendiente de validación. Cualquier cambio posterior va a «Desviaciones», con fecha, sin editar lo anterior.

## 1. Por qué existe

* El certificado de v0.4 (`geovida.certificate.certify`) tiene una sola respuesta para una imagen fuera de su
  dominio de calibración: quitar el verde y dejar **amarillo**.
* En ecografía 3D real de ratón (H11), las 540 medidas de cuerpo quedaron en amarillo, también con errores de
  volumen de 3000 % [HV, `docs/h11/RESULTADOS_H11.md` §4]. Con la calibración de H12 aparece el rojo en `global` y
  `otsu`, pero `smoothed_otsu` sigue en amarillo con errores de varios cientos por ciento
  [HV, `docs/h11/RESULTADOS_H12R.md` §4].
* Amarillo significa «no puedo garantizarlo». No avisa de que la medida no sirve. **La pregunta es si una regla fija,
  calculada solo con la imagen, puede marcar como «inservible» las medidas groseramente erróneas sin marcar las
  aceptables.**
* Se prueba primero en sintético, donde se conoce la verdad. Aplicarlo a datos reales sería otro preregistro.

## 2. La regla (fija; `geovida.h22`)

La guardia ya mide dos índices en la imagen (`geovida.domain`): `snr_hat` (contraste / ruido del fondo) y
`edge_width` (grosor de la banda de transición del borde). Los compara con la envolvente congelada (percentiles
1–99 de la calibración) del segmentador y perfil declarados.

* **Exceso logarítmico:** para cada índice, ln(lo / v) si está por debajo de la envolvente, ln(v / hi) si está
  por encima, 0 si está dentro. Se toma el mayor de los dos.
* **Inservible:** máscara no vacía con exceso > **ln 2**, es decir, algún índice a más de un factor 2 fuera de lo
  que vio la calibración. Un índice no medible (no finito o ≤ 0) también cuenta como inservible: no se puede
  comprobar el dominio.
* El estado nuevo sustituye al amarillo o al rojo. Nunca a un verde, que ya exige estar dentro del dominio. La
  máscara vacía sigue en rojo, como hoy.
* Guardia aplicada: la congelada de v0.4 (`src/geovida/frozen/h9_frozen.json`, sin cambios), con el perfil declarado
  `realistic`, como en H11.

**Cómo se eligió el factor [HV], mirando solo las envolventes congeladas y ningún dato medido.** La envolvente de
`snr_hat` en `realistic` es muy estrecha: 8,5–9,7 en los tres segmentadores. Una distancia normalizada por la
anchura de la envolvente marcaría como inservible una imagen con SNR 7, que probablemente se mide bien. Por eso se
usa un factor absoluto: SNR por debajo de ~4,2, o borde más de dos veces más ancho que el mayor visto (~2,2 vóxeles
finos). El factor 2 es un juicio previo, no un valor validado. Los factores 1,5 y 3 se informan solo como
sensibilidad.

## 3. Diseño

| | Valor |
|---|---|
| Formas | Las 4 de H21 (`prolate`, `hemisphere`, `cone`, `horseshoe`). El certificado se calibró con las 10 formas de H6; estas no las vio nunca |
| t/h | 3, 4, 6, 8, 12 |
| Anisotropía | 1 |
| Perfiles (9) | `realistic` (control: el perfil de calibración) · desplazados de v0.4: `mild_blur`, `mild_noise`, `blurry`, `noisy` · ecografía simulada de H12: `us_compound`, `us_raw`, `us_atten`, `us_coarse`. Ninguno salvo `realistic` entró en la calibración de v0.4 |
| Segmentadores | `global`, `otsu`, `smoothed_otsu` |
| Repeticiones | 30 por condición, cada una con su propia rotación y desplazamiento al azar |
| Semilla | **20262201** (`geovida.h22.SEED`), no usada antes; remuestreo con 20262202 (prueba en `tests/test_h22.py`) |
| Total | 4 × 5 × 9 × 30 = **5400 imágenes**, 16 200 medidas |

Verdad: el volumen en forma cerrada de cada forma (`geovida.phantoms`, comprobado en `tests/test_h21.py`).

**Datos ya vistos [HV].** H21 ya midió estas 4 formas con `realistic`, `noisy` y `us_compound`, con otra semilla.
Se conocen sus errores de volumen por celda, pero no los índices de dominio, que H21 no calculó. La regla del §2 no
usa ese conocimiento. Las imágenes de H22 son nuevas.

## 4. Hipótesis y criterios (fijos; `geovida.h22`)

**Unidad:** una medida (imagen × segmentador). **Aceptable:** |error de volumen| ≤ 10 %. **Fallo grosero:**
|error de volumen| > 50 %. El intervalo de confianza remuestrea **imágenes** (las 3 medidas de una imagen van
juntas), con 2000 réplicas.

* **H22a (primaria): el estado inservible casi nunca cae sobre una medida aceptable.** Entre las medidas marcadas
  como inservibles, fracción aceptable.
  * **Apoyada** si el límite superior del IC 95 % es ≤ 5 %.
  * **Contraria** si la estimación puntual es > 10 %.
  * **No concluyente** entre ambas.
  * **No evaluable** con menos de 100 medidas marcadas.
* **H22b: el estado inservible encuentra los fallos groseros que hoy no son rojos.** Entre las medidas con fallo
  grosero que el certificado actual deja en verde o amarillo, fracción marcada como inservible.
  * **Apoyada** si es ≥ 50 %.
  * **Contraria** si es ≤ 20 %.
  * **No concluyente** entre ambas.
  * **No evaluable** con menos de 100 medidas en ese grupo.
* **H22c (control): en el perfil de calibración casi no salta.** Fracción de medidas de `realistic` marcadas como
  inservibles: **apoyada** si es ≤ 1 %; si no, **no apoyada**.
* **Descriptivo:** por perfil × segmentador, fracción dentro del dominio, inservible y roja, y mediana de
  |error|. Tabla cruzada de luz actual, estado nuevo y banda de error. Las tres cifras con factores 1,5 y 3.

## 5. Orden

1. Este preregistro, `src/geovida/h22.py`, `scripts/run_h22.py` y `tests/test_h22.py` se suben a la rama, con la
   CI en verde, **antes** de medir. El autor lo aprueba por escrito.
2. `run_h22.py run` se ejecuta **una sola vez**: el script se niega a sobrescribir el barrido. El manifiesto guarda
   la huella del código y el SHA-256 de la guardia congelada.
3. `run_h22.py analyze` aplica `classify` y `verdicts` sin parámetros libres.
4. Los resultados van a `docs/h22/RESULTADOS_H22.md`, con los veredictos del código transcritos sin cambios.

## 6. Qué no se hace

* No se cambia el factor 2, ni los umbrales del 10 % y el 50 %, ni la guardia congelada después de ver los datos.
* No se añaden perfiles, formas ni índices de dominio nuevos.
* No se toca el certificado de geovida hasta tener los resultados y aplicar la tabla del §8.
* No se usan los casos reales de H11 en este estudio.

## 7. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| H22a apoyada | 55 % |
| H22b apoyada | 40 % |
| H22c apoyada | 85 % |
| Decisión «añadir inservible» (las tres apoyadas) | 25 % |
| Algún perfil de ecografía simulada con más del 50 % de medidas inservibles | 60 % |

Razonamiento [HIP]: el ruido fuerte y el moteado bajan `snr_hat` muy por debajo de la envolvente, y ahí los
segmentadores de umbral fallan mucho. Pero `smoothed_otsu` puede medir bien con ruido fuerte (en H21 su error de área
quedó a ~1 % con `noisy`), y eso pondría en riesgo H22a. El desenfoque solo (`blurry`) ensancha el borde sin hundir el SNR y
puede quedarse por debajo del factor 2.

## 8. Qué se hará con cada resultado (fijado ahora)

| Resultado | Decisión |
|---|---|
| H22a, H22b y H22c apoyadas | **Añadir el estado «inservible»** al certificado, en una versión nueva, con el factor 2 congelado. Probarlo en datos reales requiere otro preregistro |
| H22a y H22c apoyadas, H22b no | Añadir el estado como alarma conservadora y documentar que encuentra pocos fallos groseros |
| H22a o H22c no apoyadas | **No añadir.** La guardia sigue con amarillo; se documenta por qué la regla no sirve |

## 9. Qué no se podrá concluir

* Nada sobre imágenes reales: es un banco sintético, que **no** valida la regla en datos reales [PV].
* Nada fuera de estas formas, perfiles, segmentadores y de la guardia de v0.4 con perfil declarado `realistic`.
* El factor 2, los umbrales del 10 % y del 50 %, y los criterios del 5 %, 10 %, 20 %, 50 % y 1 % son juicios
  previos, no valores validados.
* La mezcla de perfiles es un diseño, no una muestra de la práctica: las fracciones dependen de cuántas imágenes
  de cada tipo se incluyeron.

## 10. Candado

Antes de `run`: la huella del código (`geovida.provenance.git_state`, blob por archivo) quedará en el manifiesto del
barrido. Se comprobará que coincide con la rama para `src/geovida/h22.py`, `src/geovida/domain.py`,
`src/geovida/budget.py`, `src/geovida/certificate.py`, `src/geovida/frozen/h9_frozen.json`,
`src/geovida/experiment.py`, `src/geovida/imaging.py`, `src/geovida/segment.py`, `src/geovida/measure.py`,
`src/geovida/phantoms.py` y `scripts/run_h22.py`.

## Desviaciones

Ninguna.
