# Preregistro H24: una luz de fiabilidad con la tolerancia medida en vóxeles de borde (ventrículos cerebrales)

**Versión 1.0, 26 nov 2026. Aprobada por el autor tal como estaba escrita el 26 nov 2026.**

Código: `src/geovida/h24.py` y `scripts/run_h24.py`. Pruebas: `tests/test_h24.py`.

> **De dónde viene.** H23 se cerró como no evaluable: la regla de H20 dio **0 verdes de 34** en la calibración de
> ventrículo [HV, `docs/h23/RESULTADOS_H23.md`]. La comprobación de factibilidad, hecha solo con las etiquetas de los
> 142 casos de ajuste, explica por qué: **una capa de un vóxel sobre el borde es el 42 % del volumen del ventrículo**
> (mediana; P10 33 %, P90 55 %), frente al 7,6 % en el cuerpo [HV, `results/h23/h24_factibilidad.json`, fuera de git].
> Una tolerancia del 10 % del volumen queda por debajo de la resolución para el ventrículo.
>
> **Qué no es.** No es un reajuste de H23 ni una segunda oportunidad para su regla. **Es otra pregunta**, con otra
> unidad de error. Tampoco es una replicación: mismo conjunto, mismo equipo, misma especie.
>
> **Cuándo se sube.** A la rama, con su código y sus pruebas, **antes de calcular ninguna señal nueva** y antes de abrir
> la prueba de ventrículo.
>
> **Etiquetas:** [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta.
>
> **Datos:** solo datos animales publicados (Qiu et al. 2021, IEEE DataPort, doi:10.21227/drmd-xq36, CC BY). Nada
> humano ni clínico.

## 1. Pregunta

Si el error se mide en la unidad que la imagen puede resolver, el desplazamiento medio del borde en vóxeles, en lugar de
en porcentaje del volumen:

1. ¿una luz verde basada solo en la estabilidad de la red acierta en ventrículos nuevos?
2. ¿los casos no verdes fallan más que los verdes? Es la pregunta que H20 y H23 no pudieron responder.

## 2. Lo que ya se ha visto (declarado)

Esta sección pesa más que en H23, porque H24 nace después de mirar la calibración de H23.

- **Calibración de ventrículo (34 casos).** Se vieron todas las señales de H20 caso a caso:
  - s_flip y s_stage, el error relativo de volumen, el Dice y la guardia;
  - los agregados publicados: 22 de 34 a ≤ 10 %, Dice mediano 0,884, 0 verdes, s_flip ≤ 0,05 en 9 casos y
    s_stage ≤ 0,10 en 7.
  - **Consecuencia:** las puertas S′ y C′ de §6 se calculan sobre datos ya vistos. **No son evidencia independiente**;
    solo sirven de freno. La única evidencia confirmatoria es la prueba.
- **Etiquetas de ajuste (142 casos).** Se usaron para la factibilidad, es decir, la fracción del volumen en una capa de
  un vóxel.
- **Prueba de ventrículo (40 casos de 40 embriones).** **Intacta**:
  - ninguna red de ventrículo la ha procesado;
  - ninguna señal de ventrículo se ha calculado en ella;
  - sus etiquetas de ventrículo no se han leído con ningún método aprendido.
  - Son imágenes de los 40 embriones de prueba de cuerpo de H20; el resultado de cuerpo en ellas se conoce y no se usa.
- **Qué no se ha mirado.** Nadie ha calculado el error en vóxeles de borde ni las señales normalizadas de §5 en ningún
  caso. Los umbrales de §5 salen de una regla fijada por principio (§5.3), no de esos datos.

## 3. Datos y repartos (los de H23, sin cambios)

- Manifiesto: `results/h11/manifiesto_qiu2021.csv`. Estructura `ventricle`: 216 casos.
- Reparto por embrión con `h18.split_cases` y `h19.fit_calibration_split` (semilla 20261121):
  - ajuste: 142 casos de 130 embriones;
  - calibración: 34 casos de 33 embriones;
  - prueba: 40 casos de 40 embriones [HV, H23 §3].
- Vóxel isotrópico de **0,05 mm** (50 µm) en todos los volúmenes [HV, comprobado en el manifiesto el 26 nov 2026]. Un
  vóxel de borde son, por tanto, 50 µm en todas las direcciones.

## 4. Segmentador (congelado; no se entrena nada)

Se usan las dos redes ya entrenadas en H23, sin tocarlas, con la medida de la desviación D-1 de H23 (`h23.segment_all`
y `h23.coarse_volume_all`, que cuentan todas las piezas):

| Red | Archivo (fuera de git) | SHA-256 |
|---|---|---|
| Etapa 1 | `results/h23/coarse.pt` | `fa7f52117ab5dab3a7918eb53c89b56228c6a71e5931dd57e729436a0ba90038` |
| Etapa 2 | `results/h23/fine.pt` | `fc3f4dfdf9170ea6113acc457d05c389f1fe699ec7479bb66b4299dd92be9cf2` |

`run_h24.py` se niega a correr si alguna huella no coincide.

## 5. Error, señales y regla

### 5.1. Error en vóxeles de borde

Para cada caso, con la referencia manual R (volumen V_R, superficie A_R) y la medida M (volumen V_M):

**e_b = |V_M − V_R| / A_R**, en vóxeles.

Es el desplazamiento uniforme del borde que explicaría la diferencia de volumen.

- Las superficies se calculan con `geovida.measure._area_sdf`, el estimador que mantuvo H21, con espaciado (1, 1, 1),
  así que se miden en caras de vóxel.
- **Fallo: e_b > 0,5 vóxeles** (25 µm). Medio vóxel es el límite de redondeo de la discretización. Un borde desplazado
  menos de medio vóxel no se distingue del muestreo. El umbral no se eligió mirando datos.
- Equivalencias orientativas con la k mediana de la factibilidad: 0,5 vóxeles son un **21 %** del volumen del
  ventrículo y un **3,8 %** del cuerpo. En el cuerpo, esta tolerancia es más estricta que el 10 % de H20.
- También se informa el error relativo de H23, |V_M − V_R| / V_R, de forma solo descriptiva y para continuidad.

### 5.2. Señales (las de H20, expresadas en vóxeles de borde)

A_M es la superficie de la propia máscara medida, calculada con el mismo estimador y sin la referencia.

| Señal | Definición | Relación con H20 |
|---|---|---|
| **b_flip** | (máx_k V_k − mín_k V_k) / A_M, con los 8 volteos de H20 | s_flip · V_0 / A_M |
| **b_stage** | \|V_c − V_0\| / A_M, con V_c el volumen de la etapa 1 sola | s_stage · V_0 / A_M |

Si A_M = 0 o falta alguna pasada, la señal no es calculable.

### 5.3. Regla: los umbrales de H20 en la misma proporción respecto de la tolerancia

En H20, con una tolerancia de 0,10, los umbrales eran fracciones fijas de esa tolerancia:

- verde s_flip ≤ ½ · tol y s_stage ≤ 1 · tol;
- rojo s_flip > 2 · tol o s_stage > 3 · tol.

H24 conserva esas proporciones y cambia la unidad (tol = 0,5 vóxeles):

| Luz | Condición |
|---|---|
| Verde | dentro del dominio **y** b_flip ≤ 0,25 **y** b_stage ≤ 0,50 |
| Rojo | b_flip > 1,0 **o** b_stage > 1,5 |
| Amarillo | el resto, incluidas las señales no calculables y los casos fuera del dominio |

Así no queda ningún grado de libertad: cada número sale de H20 y de la tolerancia de §5.1.

### 5.4. Guardia de dominio (la de H23, sin cambios)

La envolvente del 1 % al 99 % de `snr_hat` y `edge_width`, calculados con la máscara de ventrículo:

- en calibración, ajustada en 5 pliegues por embrión, sin el propio embrión;
- para la prueba, con los 34 casos de calibración.

## 6. Orden, puertas y candado

`scripts/run_h24.py`, en este orden:

1. `check`: comprobar las huellas SHA-256 de §4.
2. `g0`
3. `calibrate`
4. SHA-256 del congelado al §11 y a la rama
5. `test --sha`
6. `explore-body`, opcional (§7)

**G0 (en 5 casos de ajuste, semilla 20261126):**
- A_M, b_flip y b_stage son calculables en los 5;
- la pasada sin voltear reproduce exactamente `h23.segment_all`;
- cada caso tarda ≤ 300 s.

**Puerta S′ (en calibración, no independiente):** ≥ 50 % de los 34 casos con e_b ≤ 0,5.

**Puerta C′ (en calibración, no independiente):** ≥ 10 verdes, y como mucho el 10 % de ellas con e_b > 0,5.

Si falla una puerta:
- **la prueba no se abre**;
- el resultado se publica como no evaluable.

Si pasan las dos, `calibrate` congela los umbrales, la envolvente y las huellas de las redes. `test` se niega a correr si
algo no coincide con lo congelado.

## 7. Hipótesis y criterios (fijos)

**Primaria 1, H24b (como H20b y H23b).** Fracción de los casos de prueba con luz verde que tienen e_b > 0,5, con IC 95 %
por remuestreo de embriones (2000 réplicas, semilla 20261120).

| Veredicto | Condición |
|---|---|
| Apoyada | estimación ≤ 10 % |
| No apoyada | límite inferior > 10 % |
| No concluyente | cualquier otro caso |

Es **evaluable** con ≥ 20 verdes en ≥ 15 embriones.

**Primaria 2, H24d (separación, como H23d).** Δ = fallos entre los no verdes − fallos entre los verdes, con fallo
e_b > 0,5 e IC 95 % por remuestreo de embriones (misma semilla).

| Veredicto | Condición |
|---|---|
| Separa | límite inferior de Δ > 0 |
| No separa | límite superior de Δ ≤ 0,05 |
| No concluyente | cualquier otro caso |

Es **evaluable** con ≥ 5 verdes y ≥ 5 no verdes.

Las dos primarias se informan juntas y sin corregir por multiplicidad. Su lectura conjunta está en §9.

**Secundarias (prueba, descriptivas):**
- H24a: cobertura (fracción verde y distribución de luces).
- H24c: rendimiento de la red: e_b mediana, fracción con e_b ≤ 0,5 y ≤ 0,25, Dice mediano y, para continuidad con H23,
  fracción a ≤ 10 % de volumen.
- H24e: verdes sin guardia y cuántas fallan.
- H24g: tasa de fallo en todos los casos de prueba (la de «dar verde a todo»), para leer H24b en contexto.

**Exploratoria, H24f (no decide nada).** La misma regla y la misma tolerancia aplicadas al cuerpo:
- con las redes de H20, sobre los 40 casos de prueba de cuerpo ya abiertos en H20;
- esa prueba ya se usó, así que el resultado es descriptivo;
- mira si una sola regla en vóxeles de borde se comporta de forma parecida en una estructura grande y en una pequeña;
- se corre solo después de `test`.

Un valor no calculable es «no evaluable», nunca «no apoyada».

## 8. Predicciones escritas de antemano

Son subjetivas, y se escriben sabiendo lo que se vio en la calibración de H23 (§2).

| Predicción | Probabilidad |
|---|---|
| Pasa G0 | 95 % |
| Pasa la puerta S′ | 90 % |
| Pasa la puerta C′, dado S′ | 50 % |
| H24b evaluable (≥ 20 verdes de 40), dado que se abre la prueba | 40 % |
| H24b apoyada, dado que es evaluable | 65 % |
| H24d separa, dado que es evaluable | 30 % |

*Por qué S′ es casi segura [HIP].* Un 10 % del volumen del ventrículo son unos 0,24 vóxeles de borde. En H23, 22 de 34
casos ya estaban dentro del 10 %, así que con 0,5 vóxeles la mayoría quedará dentro. **Por eso S′ no informa**: se
mantiene solo como freno.

*Por qué H24d separará probablemente poco [HIP].* Con una tolerancia más amplia habrá pocos fallos, y con 40 casos un Δ
pequeño no tendrá un IC por encima de 0.

## 9. Qué significará cada resultado (antes de verlo)

| Resultado | Conclusión | Siguiente paso |
|---|---|---|
| G0 no superada | Fallo de implementación, no de la pregunta | Corregir el código y documentarlo como desviación; no se toca la regla |
| Puerta S′ no superada | La red no localiza el borde del ventrículo ni con medio vóxel | Publicarlo; la prueba sigue intacta |
| Puerta C′ no superada | Ni con la unidad de error ajustada a la resolución anticipa la estabilidad los fallos | Publicarlo como límite de las señales de H20 |
| H24b apoyada y H24d separa | Con una tolerancia ligada a la resolución, la luz acierta y distingue en una estructura pequeña | Es la primera evidencia de separación de la línea. Hace falta otro conjunto |
| H24b apoyada y H24d no separa o no concluyente | La luz es segura, pero no informa más que dar verde a todo | Mirar H24g. Las señales de H20 no bastan para separar |
| H24b no apoyada | La red es estable también cuando desplaza el borde | Publicarlo; estudiar los verdes que fallan |
| No evaluable o no concluyente | Pocas verdes o pocos embriones | **La prueba usada no decide dos veces**: no habrá H25 sobre esta misma prueba de ventrículo |

## 10. Qué no se puede concluir

- No es una replicación: mismo conjunto, mismo equipo, misma especie. Las imágenes de prueba son las de H20.
- La tolerancia de 0,5 vóxeles es otra pregunta que la del 10 %. **Un resultado de H24 no dice nada sobre la regla de
  H23 ni la rescata.**
- e_b supone un desplazamiento uniforme del borde. Errores que se compensan (un lado de más, otro de menos) quedan
  ocultos, igual que con el error de volumen. El Dice se informa para verlo.
- La referencia es un contorno humano con su propia variabilidad, que no se conoce para este conjunto. Medio vóxel
  puede estar por debajo de ella.
- Las señales miden inestabilidad, no exactitud.
- Nada sobre humanos, hidrocefalia, obstetricia ni uso clínico.

## 11. Desviaciones

(Ninguna al subir este preregistro.)

**Cierre (26 nov 2026).**

- `check` y G0 superados.
- Puerta S′ superada: 29 de 34 con e_b ≤ 0,5.
- **Puerta C′ no superada: 3 verdes de 34** (1 falla).
- La guardia de dominio, sin cambios respecto de H23, deja dentro solo 5 de 34. Eso ya se veía en H23, y este
  preregistro debió advertir que hacía imposible la puerta C′.
- No se generó ningún congelado y la prueba no se abrió.
- H24 se cierra como no evaluable: `docs/h24/RESULTADOS_H24.md`.
