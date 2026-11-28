# Cuántos casos hacen falta para saber si la luz separa aciertos de fallos (26 nov 2026)

> **Qué es:** una nota de planificación hecha **solo con simulación**. No lee ningún dato real, no recalcula ningún
> veredicto publicado y no es un preregistro. Sirve para dimensionar un estudio futuro, por ejemplo con un segundo
> conjunto de datos.
>
> **Código:** `scripts/power_separation.py` (semilla 20261127; 1000 simulaciones por celda), probado en
> `tests/test_power_separation.py` contra la regla real (`geovida.h24.separation`).
>
> **Etiquetas:** [HV] verificado por la simulación · [HIP] hipótesis · [PROP] propuesta.

## 1. La pregunta

H20d, H23d, H24d y H25d preguntaban lo mismo: **¿fallan más los casos no verdes que los verdes?** La regla:

- Δ = fallos entre no verdes − fallos entre verdes;
- IC 95 % por bootstrap de percentiles, remuestreando embriones;
- «separa» si el límite inferior es > 0; «no separa» si el superior es ≤ 5 puntos; si no, «no concluyente».

Ninguna dio respuesta. Esta nota estima con cuántos casos podría darla.

## 2. Escenarios

Un caso por embrión y la mitad de los casos en verde (en la prueba de H25 fue el 47,5 %).

| Escenario | Fallo entre verdes | Fallo entre no verdes | De dónde sale |
|---|---|---|---|
| Nulo | 5 % | 5 % | Lo observado en la prueba de H25: la luz no separa |
| Débil | 5 % | 15 % | Una separación modesta |
| Como la calibración | 5 % | 27 % | Lo descriptivo de la calibración de H25 (§7 del preregistro) |
| Más fallos | 10 % | 30 % | Un conjunto donde la red falle más, por ejemplo otro equipo [HIP] |

## 3. Resultados [HV]

Probabilidad de que la regla diga **«separa»**:

| Casos | Nulo | Débil | Como la calibración | Más fallos |
|---|---|---|---|---|
| 40 | 0,4 % | 17 % | 54 % | 37 % |
| 80 | 1,7 % | 37 % | 83 % | 64 % |
| 120 | 3,5 % | 46 % | 95 % | 82 % |
| 200 | 2,6 % | 66 % | > 99 % | 95 % |
| 300 | 2,9 % | 87 % | 100 % | > 99 % |
| 400 | 2,8 % | 94 % | 100 % | > 99 % |

En el escenario nulo, la columna es la tasa de falsos «separa»: se queda cerca del 2,5 % que corresponde a un IC del
95 % de dos colas.

Para un 80 % de probabilidad de detectar la separación:

| Escenario | Casos | Fallos esperados en total |
|---|---|---|
| Como la calibración | unos 80 | unos 13 |
| Más fallos | unos 120 | unos 24 |
| Débil | unos 270 | unos 27 |

**Lo que manda es el número de fallos, no el de casos.** Con 40 casos y 2 fallos, como en la prueba de H25, ninguna
regla puede separar nada.

## 4. Un defecto de la regla de «no separa» [HV]

En el escenario nulo con 40 casos, la regla dice «no separa» en el 35 % de las simulaciones. Debería ser casi
imposible concluir con 40 casos que la diferencia es como mucho de 5 puntos.

La causa: de 144 «no separa» simulados con 40 casos, **140 tenían 0 fallos entre los no verdes**. Sin fallos, todas
las réplicas del bootstrap dan Δ ≤ 0 y el IC sale degenerado, con el límite superior en 0 o justo por encima. Con 200
casos el efecto casi desaparece: 2 de 149.

**Ningún veredicto publicado está afectado.** H20d dio un IC de −11,4 a 20,0 puntos y H25d fue «no concluyente»;
H23d y H24d no se evaluaron. Ninguno dijo «no separa». Pero un estudio futuro con pocos fallos podría concluir «no separa» por este defecto.

## 5. Qué se propone para el próximo preregistro de separación [PROP]

1. **Evaluabilidad por fallos, no solo por verdes:** exigir al menos 10 fallos en total y al menos 1 en cada grupo
   para dar cualquier veredicto de separación.
2. **Tamaño:** planificar unos 25 fallos esperados. Con la tasa de fallo global de H25 (5 %), eso son unos 500 casos.
   Con una tasa del 20 %, unos 125.
3. **IC:** mantener el bootstrap por embrión, pero declarar el número mínimo de fallos del punto 1 para que no se dé
   un IC degenerado.

Esto **no cambia** ningún estudio cerrado. Solo se aplicaría a un preregistro nuevo, que necesita la aprobación del
autor. **Adoptado por el autor el 26 nov 2026** como reglas S-1 a S-3 de `docs/REGLAS_PREREGISTRO.md`.

## 6. Qué significa para el segundo conjunto de datos

Con la tasa de fallo de la red en este conjunto, ninguna fuente razonable da unos 500 casos nuevos. La vía realista es
un conjunto donde la red **falle más**, por ejemplo otro equipo o un protocolo distinto. Ahí unos 100–150 casos
bastarían. Es un argumento más para pedir volúmenes al grupo de NYU, y para pedir los suficientes.

## 7. Límites

- Supuestos simplificados: un caso por embrión, fallos independientes y la fracción de verdes fija.
- No modela una luz que cambie con el conjunto de datos, ni una guardia que rechace parte de los casos.
- Las tasas de los escenarios son supuestos, no estimaciones; la de «como la calibración» sale de 34 casos.
