# Preregistro — H20: ¿anticipan las señales de fiabilidad de la propia red cuándo falla su medida? (v1.0, 20 nov 2026)

> Siguiente paso fijado por la fila «S sí, C no» de §7 de `docs/PREREGISTRO_H19.md`: «buscar observables de fiabilidad
> de la red (p. ej. varias pasadas); preregistro nuevo». Se sube a la rama con su código y sus pruebas **antes de
> calcular ninguna señal en ningún caso**, incluida la puerta G0.
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta. Solo datos animales
> publicados (Qiu et al. 2021, CC BY). Nada humano ni clínico.

## 1. Pregunta

H19 entrenó una red de dos etapas que mide bien el volumen del cuerpo (24 de 27 casos de calibración a ≤ 10 %), pero su
certificado, basado en observables de la imagen, no anticipó cuándo fallaba: sus verdes fallaron más (2 de 16) que dar
verde a todo (3 de 27) [HV, `docs/h19/RESULTADOS_H19.md`]. H20 pregunta si **la propia red** avisa de cuándo su medida
no es fiable: **¿una luz verde dada solo por la estabilidad de la red acierta en embriones que ninguna parte del
estudio ha visto?**

La idea de usar el desacuerdo entre predicciones de entradas transformadas como medida de incertidumbre de la
segmentación está publicada: Wang et al. 2019, aumento en tiempo de prueba con redes convolucionales en RM fetal y de
tumores [EI, doi:[10.1016/j.neucom.2019.01.103](https://doi.org/10.1016/j.neucom.2019.01.103)]; y su uso para señalar
segmentaciones erróneas en cascadas de redes [EI, doi:[10.3389/fncom.2019.00056](https://doi.org/10.3389/fncom.2019.00056)]
(según PubMed). Aquí se usa en ecografía 3D de embrión de ratón, con una regla fija y una prueba bajo candado.

## 2. Lo que ya se ha visto (declarado)

* **Red y medida:** las de H19, sin cambios (`results/h19/coarse.pt` y `fine.pt`, SHA-256 en
  `results/h19/calibrate.json`). La medida es `h19.segment_full` sobre la imagen tal cual.
* **Calibración (27 casos, 25 embriones):** se conocen sus errores de volumen, su Dice y sus observables de imagen, y
  cuáles son los 3 casos que fallan (H19). **Ninguna de las dos señales de H20 se ha calculado en ningún caso.** La regla
  no tiene parámetros que se ajusten con esos datos; el riesgo que queda es que los umbrales se eligieran mirando los
  errores: por eso se fijan desde la tolerancia (§4) y no desde la calibración, y la decisión final es la prueba.
* **Prueba (44 casos, 43 embriones):** **sin abrir.** Ni H18 ni H19 leyeron ningún volumen de prueba.
* **Entrenamiento de la red:** con volteos al azar en los tres ejes (`h19.train`), así que los 8 volteos de una imagen
  son entradas que la red aprendió a tratar igual [HV].

## 3. Datos y repartos (fijos)

Los de H19: 109 casos de ajuste (la red), 27 de calibración, 44 de prueba; por embrión y nunca un embrión a dos lados.
G0 usa 5 casos de **ajuste** elegidos con semilla **20261123** (la red ya los vio: solo sirven para factibilidad).

## 4. Señales y regla (fijas)

`src/geovida/h20.py`. Con V_k el volumen de la máscara de `h19.segment_full` sobre la imagen volteada por el k-ésimo
de los 8 subconjuntos de ejes (V_0 la identidad, que **es la medida de H19**) y V_c el volumen de la etapa 1 sola (¼ de
resolución, umbral 0,5, componente mayor):

* **s_flip** = (máx_k V_k − mín_k V_k) / V_0 — inestabilidad de la medida ante entradas igual de válidas.
* **s_stage** = |V_c − V_0| / V_0 — desacuerdo entre los dos estimadores de la cascada.

**Regla** (sin ajuste; τ = 10 %, la tolerancia de H11–H19):

| Luz | Condición |
|---|---|
| Verde | dentro del dominio **y** s_flip ≤ 0,05 (τ/2) **y** s_stage ≤ 0,10 (τ) |
| Rojo | s_flip > 0,20 (2τ) **o** s_stage > 0,30 (3τ) |
| Amarillo | el resto, incluidas señales no calculables (máscara vacía) y fuera del dominio |

*Por qué estos umbrales [PROP]:* si ocho respuestas igual de válidas se separan más de τ/2, la mitad de la tolerancia ya
se gasta en inestabilidad visible y queda la otra mitad para errores que los volteos no revelan (un sesgo común a
todos). Las dos etapas son estimadores distintos: si discrepan más de τ, al menos uno está a más de τ/2 de la referencia.
El rojo de la etapa 1 es más ancho (3τ) porque a ¼ de resolución tiene sesgo de volumen parcial conocido en embriones
pequeños. Son juicios declarados, no estimaciones, y no cambian con lo que dé G0 ni la calibración.

**Guardia de dominio:** la de H18/H19 (envolvente 1 %–99 % de `snr_hat` y `edge_width`). En calibración, ajustada sin el
embrión (los 5 pliegues de H19); para la prueba, con los 27 casos de calibración.

## 5. Orden de ejecución, puertas y candado

`scripts/run_h20.py`: `g0` → `calibrate` → *(SHA-256 al §10 y a la rama)* → `test --sha`.

* **G0 (factibilidad, en 5 casos de ajuste):** las dos señales calculables en los 5, la pasada identidad reproduce
  **exactamente** el volumen de `h19.segment_full`, y ≤ 300 s por caso (71 casos en menos de 6 h). Los valores de las
  señales se guardan pero no cambian nada. Si falla, se para y se documenta.
* **Puerta C (en calibración, la de H19 sin cambios):** ≥ 10 verdes y como mucho el 10 % de ellas con |error| > 10 %.
  Antes, `calibrate` comprueba que la pasada identidad reproduce el error de H19 en los 27 casos; si no, se para.
* Si falla una puerta, **la prueba no se abre**. Si pasa, `calibrate` congela umbrales, envolvente y huellas SHA-256 de
  las redes; `test` se niega a correr si el congelado, las redes o los umbrales del código no coinciden.

## 6. Hipótesis y criterios (fijos; los de H18b/H19b)

**Primaria: H20b.** Entre los casos de prueba con luz verde (con guardia), fracción con |error| > 10 %; IC 95 % por
remuestreo de embriones (2000 réplicas, semilla 20261120). *Apoyada* si la estimación es ≤ 10 %; *no apoyada* si el
límite inferior supera 10 %; *no concluyente* en otro caso. **Evaluable** con ≥ 20 verdes en ≥ 15 embriones.

**Secundarias (prueba, descriptivas):** H20a cobertura (fracción verde); H20c acuerdo de la red en la prueba (Dice y
|error| medianos, fracción a ≤ 10 % y ≤ 5 %: es la primera medida de la red de H19 en embriones nuevos); H20d
separación: fallos entre verdes frente a fallos entre no verdes, con su diferencia e IC por embrión, y verdes sin
guardia y cuántas fallan.

Un valor no calculable es «no evaluable», nunca «no apoyada».

## 7. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| Pasa G0 | 90 % |
| Pasa la puerta C | 40 % |
| H20b evaluable, dado que se abre la prueba (≥ 20 verdes de 44) | 45 % |
| H20b apoyada, dado que es evaluable | 60 % |
| En la prueba, ≥ 75 % de los casos a ≤ 10 % (H20c) | 60 % |

*Por qué C puede fallar [HIP]:* con 27 casos, una sola verde fallida de más tumba la puerta (H19 se quedó a una); y los
volteos solo ven la inestabilidad, no un error que la red cometa igual en las ocho entradas (p. ej. incluir tejido
vecino de forma consistente).

## 8. Qué significará cada resultado (antes de verlo)

| Resultado | Conclusión | Siguiente paso |
|---|---|---|
| G0 no superada | Las señales no se pueden calcular como se diseñaron en este equipo | Documentar la causa; nuevo preregistro si hay arreglo |
| Puerta C no superada | Ni la imagen (H19) ni la estabilidad de la red anticipan los fallos en la calibración | Más datos de calibración o un segundo modelo independiente; la prueba sigue intacta |
| H20b apoyada | En este conjunto, una luz verde dada solo por la estabilidad de la red acertó en embriones nuevos | Replicar con otro conjunto o equipo; estudiar los amarillos |
| H20b no apoyada | La red es estable también cuando se equivoca | Publicarlo; estudiar los verdes que fallan (errores consistentes) |
| H20b no evaluable / no concluyente | Pocas verdes o pocos embriones | Más datos, mismo protocolo; **la prueba usada no decide dos veces** |

## 9. Qué no se puede concluir

* La referencia es un contorno humano; 44 casos de prueba de un conjunto, un equipo y una especie.
* Los umbrales son juicios fijados de antemano: otros umbrales podrían ir mejor o peor, y eso no se probará con esta
  prueba.
* Las señales miden inestabilidad, no exactitud: un error que la red repite en todas las entradas no se ve.
* Nada sobre humanos, obstetricia ni uso clínico.

## 10. Desviaciones

(Ninguna al subir este preregistro.)

**Candado (21 nov 2026, antes de `test`).** G0 superada: 5 de 5 casos, identidad igual a H19 en los 5, entre 13 y 23 s
por caso. Puerta C superada: 12 verdes en la calibración y ninguna con |error| > 10 %. Congelado
`results/h20/h20_frozen.json` (umbrales, envolvente y huellas de las redes), SHA-256
`66d7ffcf3d9d8397aeefe208aa480deb870d6b616c5cc01c24f8abae7250804e`. `test` solo se corre con este valor.
