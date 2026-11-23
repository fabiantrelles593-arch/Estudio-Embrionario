# Resultados — MT-A v2: efecto del atlas sobre la forma, con especímenes que pasan el control de calidad (23 nov 2026)

> Preregistro: `docs/morpho_trace/PREREGISTRO_ATLAS_v2.md` (subido antes de cualquier registro y de calcular la nueva
> **d**), que mantiene todo lo no cambiado de `PREREGISTRO_ATLAS.md` (v1.0) y su v1.1. Antecedentes:
> `RESULTADOS_ATLAS.md` (v1.0) y `RESULTADOS_ATLAS_v1_1.md` (v1.1), ambos no evaluables.
> Código: `scripts/atlas_effect_gates.py` (`register`, `analyze --protocol 2.0`; blob fb4a869),
> `scripts/mta_v2.py` (401f7d1), `src/geovida/atlas_effect.py` (9369540), los mismos que al superar G0-t.
> Datos: MusMorph/IMPC en FaceBase (CC BY 4.0, Devine et al. 2022), manifiestos en `data/manifests/`. Resultados
> brutos fuera de git (`results/morpho_trace/v2/analisis.json`, `registros/`, `registro_parte1.log`,
> `registro_parte2.log`). Solo datos animales; nada humano ni clínico.
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta.

## 1. Veredicto

**MT-A1, MT-A2 y MT-A3: no evaluables.** Falló la puerta G1: la mediana de ρ entre los landmarks
transferidos por el registro propio y los publicados es **0,219**, y la mediana de ρ entre especímenes distintos del
mismo estadio es **0,053**; el criterio exige que la primera sea menor [HV, `analisis.json`]. Según v1.0 §4 y §8, el
procedimiento de registro no reproduce lo publicado mejor que la variación entre especímenes, y **nada se puede
decir del atlas** con él.

Es el tercer MT-A no evaluable (v1.0: G0-a y G0-b; v1.1: G0-a′; v2: G1). Las causas son distintas: en v1.0 y v1.1
fallaba la geometría de los landmarks publicados; en v2 esa geometría es buena (G0-a″) y falla el registro.

## 2. Puertas

| Puerta | Criterio | Resultado | Estado |
|---|---|---|---|
| G0-a″ · muestra | Los 40 cumplen la regla de QC-LM | 40 de 40 | **Superada** [HV] (20 nov) |
| G0-b′ · atlas | (v1.1) | superada en v1.1 | **Superada** |
| G0-c · correspondencia | (v1.0) | superada en v1.0 | **Superada** |
| G0-d′ · d sin QC-LM | \|d\| entre 0,150 y 0,164 con las 597 configuraciones | 0,15678 | **Superada** [HV] (20 nov) |
| G0-t · tiempo | 80 registros en ≤ 72 h | prueba: 1323 s, ≈ 29,4 h estimadas; real: 22,9 h de cálculo | **Superada** [HV] (21 nov) |
| G2 · registros válidos | ≥ 16 de 20 por estadio con sus dos registros bien | 20 y 20 (80 de 80 terminaron con métrica finita) | **Superada** [HV] |
| **G1** · calidad del registro propio | mediana ρ(transferido, publicado) < mediana ρ entre especímenes del mismo estadio | **0,219** frente a **0,053** (40 especímenes, 380 pares) | **Fallida** [HV] |

## 3. Ejecución y una interrupción (nota de procedimiento, no desviación)

Los 80 registros empezaron el 21 nov a las 22:23. El proceso se detuvo el 22 nov a las 08:50, con **34 de 80**
registros guardados y todos correctos, porque terminó la sesión que lo había lanzado; no hubo error. El 22 nov a las
18:25 se comprobó que los tres archivos de código seguían con los blobs registrados en G0-t y se relanzó **la misma
orden**. `register` es reanudable (un JSON por registro; los que existen no se repiten), así que los 34 no se
rehicieron. Los 46 restantes terminaron el 23 nov a las 06:59. Tiempo de cálculo sumado: **22,9 h**; tiempo de
reloj desde el inicio, unas 32,6 h; ambos dentro de las 72 h. Ningún resultado parcial se miró antes de terminar.
Registros del proceso: `registro_parte1.log` y `registro_parte2.log`.

## 4. Predicciones frente a resultado

| Predicción (§5) | Probabilidad dada | Resultado |
|---|---|---|
| Pasa G0-d′ | 90 % | **Sí** |
| Pasa G0-t | 70 % | **Sí** |
| Pasa G1, dado que pasan las G0 | 70 % | **No** |
| MT-A1 apoyada / refutada, dado que es evaluable | 35 % / 30 % | No evaluable |
| MT-A2: ángulo < 45° | 60 % | No evaluable |

La predicción más confiada que falló es G1, la que el preregistro consideraba fácil porque las imágenes ya están en
la rejilla de su atlas (v1.0 §11, nota del 19 nov).

## 5. Diagnóstico de G1 (exploratorio, hecho después de ver el veredicto; no lo cambia)

`scripts/explore_mta_v2_g1.py` (resultado en `results/morpho_trace/v2/g1_diagnostico_exploratorio.json`) desglosa G1
por estadio y añade una referencia que el preregistro no tenía: los landmarks del atlas **sin transformar**
(identidad), comparados con los publicados de cada espécimen. Es una comparación razonable porque las imágenes de
MusMorph ya están remuestreadas a la rejilla de su atlas.

| Estadio | ρ transferido–publicado (mín · mediana · máx) | ρ identidad–publicado (mediana) | ρ entre especímenes (mediana) | Especímenes en que el registro mejora la identidad | Distancia mediana sin superponer (registro · identidad) |
|---|---|---|---|---|---|
| E15.5 (n = 20) | 0,071 · 0,113 · 0,304 | 0,047 | 0,068 | **0 de 20** | 0,35 mm · 0,41 mm |
| E18.5 (n = 20) | 0,045 · **0,525** · 0,957 | 0,031 | 0,042 | **0 de 20** | **2,13 mm** · 0,30 mm |

Lo que muestra [HV para los números; la lectura es descriptiva]:

* **El registro empeora la forma en los 40 especímenes.** En ninguno el registro propio deja los landmarks más cerca
  (en forma) de los publicados que no registrar nada. Los landmarks del atlas sin mover habrían quedado por debajo de
  la variación entre especímenes en los dos estadios.
* **El fallo es mucho mayor en E18.5.** La mediana de ρ es 0,525, y el máximo, 0,957, está cerca de ρ_max = 0,954
  (configuraciones prácticamente sin relación). En E18.5 los puntos se desplazan una mediana de 2,1 mm.
* **El registro mejora la semejanza de intensidades mientras deforma la anatomía.** En 79 de los 80 registros, la
  B-spline acaba con una información mutua mejor que la afín. La afín paró por tolerancia de gradiente en 70 y por
  el máximo de iteraciones en 10. La B-spline paró por tolerancia de la función en 15 y en las otras 65 la detuvo el
  límite de 100 iteraciones («User requested» en LBFGSBv4): seguía optimizando la intensidad.

Causas posibles, **sin comprobar** [HIP]:

1. La B-spline (malla 8³, LBFGS-B, 100 iteraciones) a ×4 se ajusta a la intensidad sin regularización; en 65 de
   80 registros seguía haciéndolo cuando la paró el límite de iteraciones. En E18.5 el
   vóxel ×4 es de 216 µm, el doble que en E15.5, y la deformación queda menos restringida por la anatomía.
2. Un defecto en la cadena de transferencia de puntos (convención de dirección o de coordenadas) que las pruebas con
   fantomas no detectan, porque usan transformadas casi de identidad o geometrías sencillas.

Las dos cosas se pueden distinguir sin datos nuevos: repitiendo un registro con `--affine-only` (sensibilidad 2 de
v1.0) y comprobando la transferencia con una deformación conocida aplicada a una imagen real.

## 6. Estimandos calculados por el código (no se interpretan)

`analyze` calcula los estimandos aunque falle una puerta. Se dan por transparencia, **sin ningún valor
inferencial**: con G1 fallida, δ(s) está dominado por el error del registro (§5) y no por la diferencia entre atlas.

| Estimando | Valor | Lectura |
|---|---|---|
| f (MT-A1) | 0,894 (IC 95 % 0,652–1,130) | **No se interpreta** |
| Ángulo δ̄ E15.5–E18.5 (MT-A2) | 55,5° (IC 44,2–75,7°) | **No se interpreta** |
| \|δ̄\|/\|d\|, ángulo(δ̄, d) (MT-A3) | 1,69; 58,0° | **No se interpreta** |
| Dispersión de δ a lo largo de d̂ frente a la publicada | 0,125 frente a 0,008 por estadio | Unas 15 veces mayor: coherente con un registro ruidoso |

**No debe citarse que «el atlas explica el 89 % de d».** El valor de f mide lo que deforma este registro, no el atlas.

## 7. Qué no se puede concluir

* Nada sobre el efecto del atlas en **d** de ONTO-MAP: MT-A no lo ha medido en ninguna de sus tres versiones.
* Nada en contra de los landmarks publicados de MusMorph: en esta muestra son coherentes con su atlas (identidad) y
  pasan QC-LM. Lo que falla es el registro de este proyecto.
* El diagnóstico de §5 es posterior al veredicto y no estaba preregistrado; orienta, no demuestra.
* Nada sobre humanos ni uso clínico.

## 8. Siguiente paso propuesto (no ejecutado)

* **No se repite MT-A cambiando parámetros del registro sobre esta muestra** hasta tener un preregistro nuevo.
  v1.0 §8 prevé, para un fallo de G1, «probar otro registrador con un preregistro nuevo».
* **[PROP] Antes de eso, verificar la cadena de registro (ingeniería, sin veredicto científico):** (a) prueba de
  transferencia con una deformación conocida aplicada a un atlas real; (b) un registro solo afín y otro con la
  B-spline regularizada sobre 2 especímenes ya vistos; (c) si el defecto es de código, corregirlo con pruebas que lo
  habrían detectado. Solo después, un MT-A v3 preregistrado (mismo registrador corregido u otro, como ANTs, si su
  licencia lo permite), con G1 medido primero sobre una submuestra pequeña antes de gastar 23 h de cálculo.
* **Lección para el protocolo:** G1 debería medirse con 2–4 especímenes **antes** de los 80 registros, como puerta
  barata. Se propone para v3.
