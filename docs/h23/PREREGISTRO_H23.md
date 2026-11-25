# Preregistro H23: las señales de fiabilidad de H20 en una estructura pequeña (ventrículos cerebrales)

**Versión 1.0, 24 nov 2026. Aprobada por el autor tal como estaba escrita el 25 nov 2026.**

Código: `src/geovida/h23.py` y `scripts/run_h23.py`. Pruebas: `tests/test_h23.py`.

> **De dónde viene.** Es el camino C de `docs/h20/CANDIDATOS_REPLICACION.md`. No hay un segundo conjunto público con
> licencia y ética verificadas: UterUS se descartó y la petición al grupo de NYU está pendiente.
>
> **Qué no es.** **No es una replicación de H20**: usa el mismo conjunto, el mismo equipo y la misma especie. Es un
> estudio exploratorio confirmatorio sobre otra estructura.
>
> **Cuándo se sube.** A la rama, con su código y sus pruebas, **antes de entrenar ninguna red de ventrículo y antes de
> calcular ninguna señal**.
>
> **Etiquetas:** [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta.
>
> **Datos:** solo datos animales publicados (Qiu et al. 2021, IEEE DataPort, doi:10.21227/drmd-xq36, CC BY). Nada
> humano ni clínico.

## 1. Pregunta

En H20, una luz verde dada solo por la estabilidad de la red acertó en embriones nuevos: 1 de 21 verdes falló (4,8 %;
IC 0–14,3 %). Pero la luz apenas separaba los aciertos de los fallos, porque la red casi no fallaba:

- el 93,2 % de los casos quedó a ≤ 10 % de la referencia;
- los fallos entre los casos no verdes fueron el 8,7 %, y el IC de la diferencia con los verdes incluía 0 (H20d)
  [HV, `docs/h20/RESULTADOS_H20.md`].

Con tan pocos fallos no se podía saber si la luz distingue. Los **ventrículos cerebrales** son una estructura pequeña,
llena de líquido y de bajo contraste. Con ellos fallaron todos los segmentadores de umbral de H11
[HV, `docs/h11/RESULTADOS_H11.md`]. Es de esperar que una red falle más en ventrículos que en cuerpo, y eso permite
probar lo que H20 no pudo.

**H23 pregunta:** con la misma arquitectura, el mismo procedimiento y la misma regla de H20 sin cambios, aplicados a
los ventrículos:

1. ¿la luz verde sigue acertando?
2. ¿los no verdes fallan más que los verdes?

## 2. Lo que ya se ha visto (declarado)

- **Etiquetas de ventrículo.**
  - H11 y H12R leyeron las 216 con tres segmentadores de umbral. Los agregados se conocen: Dice mediano 0,00–0,03 y
    0 % de casos a ≤ 10 %.
  - Ningún método que aprenda las ha leído.
  - Ninguna señal de H20 se ha calculado en ningún caso de ventrículo.
- **Imágenes de prueba.**
  - Los 40 casos de prueba de ventrículo (40 embriones) son imágenes de los 40 embriones de prueba de cuerpo de H20, que
    ya se midieron para el cuerpo [HV, comprobado con el manifiesto].
  - La red de ventrículo **no** se entrenará con ellas, y sus etiquetas de ventrículo solo se usan en `test`.
  - El riesgo que queda: conocer el resultado de cuerpo en esas imágenes. No se usa para nada, porque la regla está
    fijada.
- **Regla.** Es la de H20, que ya se conoce y acertó en cuerpo. Aquí no se ajusta nada.

## 3. Datos y repartos (fijos, calculados solo con el manifiesto)

- Manifiesto: `results/h11/manifiesto_qiu2021.csv`, el de H11–H20. Estructura `ventricle`: 216 casos.
- Reparto por embrión con `h18.split_cases`, el de los autores (carpetas `nii_train` y `nii_test`):
  - 2 embriones estaban en las dos carpetas (`20170619_E12_E4`, `20170619_E12_E6`); sus casos de prueba pasan a
    entrenamiento;
  - resultado: **entrenamiento 176 casos de 163 embriones; prueba 40 casos de 40 embriones** [HV].
- Ajuste y calibración dentro del entrenamiento, con `h19.fit_calibration_split` (20 % de los embriones, semilla de
  H19, 20261121): **ajuste 142 casos de 130 embriones** (entrenan las redes); **calibración 34 casos de 33 embriones**
  [HV].
- Nunca hay un embrión a dos lados.

## 4. Segmentador (fijo, sin ajuste)

La red de dos etapas de H19, con el código de `geovida.h19` sin cambios:

| Etapa | Configuración |
|---|---|
| 1 | U-Net 3D a ¼ de resolución, 150 épocas |
| 2 | U-Net 3D a ½ de resolución en la caja de la etapa 1, con margen de 6 vóxeles, 100 épocas |
| Común | 8 canales, lr 10⁻³, volteos al azar en el entrenamiento, semillas de H19 |

La única diferencia es la etiqueta: ventrículo en lugar de cuerpo. Se entrena una vez y no se cambia nada después.

*Coste previsto [HV, H19]:* unas 20 h de CPU para las dos etapas.

## 5. Señales, regla y guardia (las de H20, sin cambios)

`geovida.h20`, con las mismas constantes.

**Señales:**
- **s_flip** = (máx_k V_k − mín_k V_k) / V_0, donde V_k es el volumen con cada uno de los 8 volteos y V_0 el de la
  imagen tal cual;
- **s_stage** = |V_c − V_0| / V_0, donde V_c es el volumen de la etapa 1 sola.

**Regla:**

| Luz | Condición |
|---|---|
| Verde | dentro del dominio **y** s_flip ≤ 0,05 **y** s_stage ≤ 0,10 |
| Rojo | s_flip > 0,20 **o** s_stage > 0,30 |
| Amarillo | el resto, incluidas las señales no calculables y los casos fuera del dominio |

**Guardia de dominio:** la envolvente del 1 % al 99 % de `snr_hat` y `edge_width`, calculados con la máscara de
ventrículo.
- En calibración se ajusta en 5 pliegues por embrión, sin el propio embrión.
- Para la prueba, con los 34 casos de calibración.

## 6. Orden, puertas y candado

`scripts/run_h23.py`, en este orden:

1. `g0`
2. `train-coarse`
3. `train-fine`
4. `calibrate`
5. SHA-256 al §11 y a la rama
6. `test --sha`

**G0-escala (antes de entrenar; solo etiquetas de los casos de ajuste).** El ventrículo de referencia, reducido a ¼
como lo ve la etapa 1, tiene **≥ 27 vóxeles en ≥ 90 % de los 142 casos de ajuste**. 27 vóxeles son un cubo de 3³; por
debajo, la etapa 1 no tiene nada que localizar. Si G0 falla, el diseño no sirve, se para y se documenta; no se cambia
la resolución.

**G0-señales (tras entrenar, en 5 casos de ajuste elegidos con la semilla 20261124):**
- las dos señales son calculables en los 5;
- la pasada sin voltear reproduce exactamente `h19.segment_full`;
- cada caso tarda ≤ 300 s.

**Puerta S (en calibración):** ≥ 50 % de los 34 casos a ≤ 10 % de la referencia, como en H19.

**Puerta C (en calibración, la de H19 y H20):** ≥ 10 verdes, y como mucho el 10 % de ellas con |error| > 10 %.

Si falla una puerta:
- **la prueba no se abre**;
- el resultado se publica como no evaluable.

Si pasan las dos, `calibrate` congela los umbrales, la envolvente y las huellas SHA-256 de las redes. `test` se niega a
correr si algo no coincide con lo congelado.

## 7. Hipótesis y criterios (fijos)

**Primaria 1, H23b (como H20b).** Fracción de los casos de prueba con luz verde que tienen |error de volumen| > 10 %,
con IC 95 % por remuestreo de embriones (2000 réplicas, semilla 20261120).

| Veredicto | Condición |
|---|---|
| Apoyada | estimación ≤ 10 % |
| No apoyada | límite inferior > 10 % |
| No concluyente | cualquier otro caso |

Es **evaluable** con ≥ 20 verdes en ≥ 15 embriones.

**Primaria 2, H23d (separación; el criterio que faltó en H20).** Diferencia de fallos, Δ = fallos entre los no verdes
− fallos entre los verdes, con IC 95 % por remuestreo de embriones (misma semilla).

| Veredicto | Condición |
|---|---|
| Separa | límite inferior de Δ > 0 |
| No separa | límite superior de Δ ≤ 0,05 |
| No concluyente | cualquier otro caso |

Es **evaluable** con ≥ 5 verdes y ≥ 5 no verdes.

Las dos primarias se informan juntas y sin corregir por multiplicidad. Su lectura conjunta está fijada en §9.

**Secundarias (prueba, descriptivas):**
- H23a: cobertura (fracción verde y distribución de luces);
- H23c: rendimiento de la red (Dice y |error| medianos, fracción a ≤ 10 % y a ≤ 5 %);
- H23e: verdes sin guardia y cuántas fallan.

Un valor no calculable es «no evaluable», nunca «no apoyada».

## 8. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| Pasa G0-escala | 75 % |
| Pasa la puerta S, dado G0 | 35 % |
| Pasa la puerta C, dado S | 40 % |
| H23b evaluable, dado que se abre la prueba (≥ 20 verdes de 40) | 30 % |
| H23d separa, dado que es evaluable | 50 % |

*Por qué S puede fallar [HIP].* Un error de volumen del 10 % en una estructura de unos cientos de vóxeles es apenas una
capa de vóxeles en el borde. Qiu et al. 2021 dan para ventrículo un Dice menor que para cuerpo
(doi:10.1109/TUFFC.2021.3068156) [EI].

*Lo más probable es que H23 se cierre como no evaluable.* Aun así, decirlo antes vale: si la red no mide ventrículos
con un 10 % de tolerancia, la pregunta sobre la luz no tiene objeto con esta tolerancia.

## 9. Qué significará cada resultado (antes de verlo)

| Resultado | Conclusión | Siguiente paso |
|---|---|---|
| G0-escala no superada | La cascada a ¼ no puede localizar ventrículos en este conjunto | Documentar; otra arquitectura exige un preregistro nuevo |
| Puerta S no superada | La red de H19 no mide ventrículos con un 10 % de tolerancia | Publicarlo. La prueba sigue intacta. No se relaja la tolerancia a posteriori |
| Puerta C no superada | La estabilidad de la red no anticipa los fallos en ventrículo, ni siquiera en calibración | Publicarlo como límite de las señales de H20 |
| H23b apoyada y H23d separa | En una estructura difícil, la luz acierta y además distingue | Refuerza H20 dentro de este conjunto. Sigue haciendo falta otro conjunto |
| H23b apoyada y H23d no separa o no concluyente | La luz es segura, pero no informa más que dar verde a todo | Las señales de H20 no bastan para separar; buscar otras |
| H23b no apoyada | La red es estable también cuando se equivoca en ventrículo | Publicarlo; estudiar los verdes que fallan |
| No evaluable o no concluyente | Pocas verdes o pocos embriones | **La prueba usada no decide dos veces** |

## 10. Qué no se puede concluir

- No es una replicación: mismo conjunto, mismo equipo, misma especie. Las imágenes de prueba son las de H20.
- La referencia es un contorno humano; 40 casos de prueba.
- Los umbrales son juicios fijados para cuerpo en H20, y no se reajustan para ventrículo. Otros umbrales podrían ir
  mejor, pero eso no se probará con esta prueba.
- Las señales miden inestabilidad, no exactitud.
- Nada sobre humanos, hidrocefalia, obstetricia ni uso clínico.

## 11. Desviaciones

(Ninguna al subir este preregistro.)

**Nota de implementación (antes de ejecutar nada).** `h19.segment_full` y `h20.coarse_volume` se quedan con la pieza
conectada mayor de la máscara: el cuerpo es una sola pieza. No se cambia, porque §4 fija el código de H19 sin cambios.
Si el ventrículo de referencia tuviera varias piezas, eso sesgaría el volumen a la baja, y la puerta S lo recogería.
Para que se vea, `g0` registra, de forma solo descriptiva, la fracción de la referencia que cae en su pieza mayor en los
casos de ajuste. Ese dato no cambia ninguna puerta ni ningún umbral.
