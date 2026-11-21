# Preregistro — H21: ¿Crofton como estimador principal de área en lugar de `area_sdf`? (v1.0, 21 nov 2026; **borrador, pendiente de aprobación del autor**)

> Tarea P2 de `docs/INFORME_DE_PROGRESO.md`, propuesta en `docs/COMPARACION_REFERENCIA.md` §3. Se sube a la rama
> **antes** de ejecutar `scripts/run_h21.py run`. Solo datos sintéticos con verdad analítica; ningún dato real ni
> clínico. Etiquetas: [HV] hecho verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta ·
> [PV] pendiente de validación. Cualquier cambio posterior va a «Desviaciones», con fecha, sin editar lo anterior.

## 1. Por qué existe

* `area_sdf` (marching cubes sobre la distancia con signo, suavizado 0,5 vóxel) es el estimador principal de área
  desde H4 (`docs/RESULTADOS_V02.md`), elegido a resoluciones bajas.
* En máscaras **ideales** (sin ruido ni desenfoque), `area_sdf` no converge: sobreestima +2,3 % a +3,0 % a t/h = 16
  en todas las formas, y su error mediano crece de 1,9 % (t/h = 8) a 2,7 % (t/h = 16). El Crofton propio de 13
  direcciones converge (0,3 % a t/h = 16) y reproduce `Perimeter` de ITK a ≤ 0,004 puntos
  [HV, `docs/COMPARACION_REFERENCIA.md`, 120 máscaras de 8 formas].
* Aquello solo probó máscaras ideales. Con ruido, la frontera segmentada se vuelve rugosa. Crofton cuenta cada
  transición objeto/fondo y podría sobreestimar más que `area_sdf`, que suaviza [HIP]. **La pregunta es si la
  ventaja de Crofton se mantiene en máscaras segmentadas de imágenes con desenfoque y ruido, en formas nuevas.**

## 2. Qué es nuevo y qué es igual

| | H3/H4 y la comparación de referencia | H21 |
|---|---|---|
| Formas | 12 usadas (`ball` … `cup`) | **4 nuevas** (`geovida.phantoms.H21_NAMES`): esferoide alargado (lisa, convexa), media bola (borde vivo), cono (vértice y borde), herradura = medio toro de extremos planos (no convexa) |
| Semilla | 20261109–20261126 y otras | **20262101** (`geovida.h21.SEED`), no usada antes (prueba en `tests/test_h21.py`) |
| Simulador | `geovida.experiment` + `geovida.imaging` | el mismo, sin cambios; las formas nuevas van al final de `ALL_SHAPES`, así que ninguna semilla anterior cambia (prueba) |
| t/h | 1,5 a 12 | 3, 4, 6, 8, 12 |
| Anisotropía | 1, 2, 3 | 1 y 2 |
| Perfiles | `ideal`, `realistic` | `ideal`, `realistic` (PSF 1, SNR 10), `noisy` (PSF 1, SNR 5), `us_compound` (ecografía simulada con granulado) |
| Segmentadores | `global`, `otsu`, `smoothed_otsu` | los mismos tres |
| Estimadores | `area_sdf`, `area_mc`, `area_faces` | `area_sdf` (actual), **`area_crofton`** (candidato, sobre la **misma** máscara), `area_mc` (descriptivo) |
| Repeticiones | 200 | 50 por condición |

Total: 4 formas × 5 t/h × 2 anisotropías × 4 perfiles × 50 = **8000 imágenes**, cada una medida con los 3
segmentadores (24 000 filas). Cada realización tiene su propia rotación y desplazamiento al azar.

Verdad: área y volumen en forma cerrada (`geovida.phantoms`). Se comprobaron antes de medir, sin el simulador
[HV, `tests/test_h21.py`]:

* volumen frente a una rasterización fina (≤ 1 %);
* área frente a marching cubes sobre la cobertura de una rasterización girada (≤ 1,5 %);
* Betti (1, 0, 0) con conectividad 6 y 26;
* la forma cabe en su caja declarada.

## 3. Hallazgo previo a medir [HV, máscaras ideales sin el simulador]

Con caras planas **alineadas con la rejilla**, el Crofton de 13 direcciones infraestima el área: −2,7 % la media
bola y −3,1 % el cono a 24 vóxeles por t. Girando la misma forma al azar, el error baja a −0,4 % y −1,0 %. Es el
sesgo de orientación conocido de discretizar Crofton con pocas direcciones. En H21 cada realización se gira al
azar, así que este sesgo entra como variabilidad entre realizaciones y no como sesgo fijo. No se corrige: se
evalúa el estimador tal como está (`geovida.reference.crofton_area`, sin cambios desde la comparación con ITK).

## 4. Hipótesis y criterios (fijos; `geovida.h21`)

**Celda:** forma × t/h × anisotropía × perfil × segmentador, con 50 realizaciones. Se resume con la mediana del error
relativo con signo de cada estimador, (medido − verdad) / verdad.

**Celda evaluable:** |mediana del error de volumen| ≤ 20 %. Si la máscara ni siquiera mide bien el volumen, no se
compara su área. Las celdas no evaluables se cuentan y se informan.

* **H21a (primaria): Crofton es más exacto a resolución fina.** Celdas con t/h ∈ {8, 12} y anisotropía 1 (96
  celdas). Se cuenta la fracción de celdas evaluables en las que |mediana de Crofton| < |mediana de `area_sdf`|.
  * **Apoyada** si es ≥ 0,75.
  * **Contraria** si es ≤ 0,25.
  * **No concluyente** entre ambas.
  * **No evaluable** si hay menos de 48 celdas evaluables.
* **H21b: Crofton no es peor a resolución gruesa.** Celdas con t/h ∈ {3, 4, 6} y anisotropía 1 (144 celdas). Se
  cuenta la fracción de celdas evaluables con |mediana de Crofton| ≤ |mediana de `area_sdf`| + 2 puntos.
  * **Apoyada** si es ≥ 0,90; si no, **no apoyada**.
  * **No evaluable** con menos de 72 celdas evaluables.
* **H21c: anisotropía.** La misma regla que H21a, en las celdas con t/h ∈ {6, 8, 12} y anisotropía 2 (144 celdas;
  no evaluable con menos de 36). Es secundaria: no entra en la decisión, pero se informa.
* **Descriptivo:** mediana del error con signo de los tres estimadores por perfil y t/h; mediana entre celdas
  evaluables de |error| de cada estimador, a resolución fina y gruesa.

## 5. Orden

1. Este preregistro, `src/geovida/h21.py`, `scripts/run_h21.py`, las formas nuevas y `tests/test_h21.py` se suben a
   la rama, con la CI en verde, **antes** de medir.
2. `run_h21.py run` se ejecuta **una sola vez**: el script se niega a sobrescribir el barrido. El manifiesto guarda
   la huella del código, que se compara con la rama.
3. `run_h21.py analyze` aplica `verdicts` sin parámetros libres.
4. Los resultados van a `docs/h21/RESULTADOS_H21.md`, con los veredictos del código transcritos sin cambios.

## 6. Qué no se hace

* No se ajusta ningún parámetro de Crofton ni de `area_sdf` (σ = 0,5 vóxel) con estos datos.
* No se añaden formas, perfiles ni celdas después de ver los resultados.
* No se cambia el estimador principal de geovida hasta tener los resultados y aplicar la tabla del §8.

## 7. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| H21a apoyada | 35 % |
| H21a contraria | 20 % |
| H21b apoyada | 45 % |
| H21c con el mismo veredicto que H21a | 60 % |
| En el perfil `ideal`, Crofton gana en ≥ 75 % de las celdas finas evaluables (como en la comparación de referencia) | 75 % |
| Decisión «cambiar a Crofton» | 25 % |

Razonamiento [HIP]: en máscaras lisas (`ideal`, `smoothed_otsu`) Crofton debería ganar, como en la comparación de
referencia. Con `global` y `otsu` sobre `noisy` y `us_compound`, la frontera rugosa debería inflar más a Crofton.

## 8. Qué se hará con cada resultado (fijado ahora)

| Resultado | Decisión |
|---|---|
| H21a apoyada y H21b apoyada | **Cambiar a Crofton** como estimador principal de área, en una versión nueva, registrando el cambio. `area_sdf` queda como columna secundaria |
| H21a apoyada y H21b no apoyada | Mantener `area_sdf` como principal. Documentar Crofton como opción para t/h ≥ 8 |
| H21a no concluyente, contraria o no evaluable | **Mantener `area_sdf`**, con su sesgo de ≈ +3 % a resolución fina ya documentado |

## 9. Qué no se podrá concluir

* Nada sobre imágenes reales: es un banco sintético con verdad analítica, que **no** valida ningún estimador en
  datos reales [PV].
* Nada fuera de estas 4 formas, estos 4 perfiles y estos 3 segmentadores.
* El criterio de celda evaluable (volumen a ≤ 20 %) y los umbrales de 0,75, 0,25, 0,90 y 2 puntos son juicios
  previos, no valores validados.
* Una mediana por celda no describe la dispersión. Se informa, pero no entra en el criterio.

## 10. Candado

Antes de `run`: la huella del código (`geovida.provenance.git_state`, blob por archivo) quedará en el manifiesto del
barrido. Se comprobará que coincide con la rama para `src/geovida/h21.py`, `src/geovida/phantoms.py`,
`src/geovida/experiment.py`, `src/geovida/reference.py` y `scripts/run_h21.py`.

## Desviaciones

Ninguna.
