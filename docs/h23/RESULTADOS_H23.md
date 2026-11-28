# Resultados H23: señales de H20 en ventrículos cerebrales (25 nov 2026)

> Preregistro: `docs/h23/PREREGISTRO_H23.md` (v1.0, aprobado el 25 nov; desviación D-1 aprobada antes de entrenar).
>
> **Datos:** ecografía 3D de alta frecuencia de embriones de ratón (Qiu et al. 2021, IEEE DataPort,
> doi:10.21227/drmd-xq36, CC BY). Nada humano ni clínico.
>
> **Etiquetas:** [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis.

## Veredicto

**H23 se cierra como no evaluable: la puerta C no se superó.** En la calibración, ninguno de los 34 casos recibió luz
verde, y la puerta pide al menos 10. **La prueba no se abrió:** las etiquetas de ventrículo de los 40 casos de prueba
siguen sin leerse con ningún método que aprenda. H23b y H23d no se evaluaron.

## Orden de ejecución [HV]

| Paso | Resultado |
|---|---|
| G0-escala (142 casos de ajuste, solo etiquetas) | Superada: 142 de 142 con ≥ 27 vóxeles a ¼ (mínimo 90, mediana 355). La pieza mayor tiene una mediana del 77 % de la referencia → desviación D-1 (contar todas las piezas) |
| Etapa 1 | 150 épocas a ¼; pérdida final 0,106 (25 nov, hasta las 13:16) |
| Etapa 2 | 100 épocas a ½ en 142 cajas de 142; pérdida final 0,109 (13:16 → 17:03) |
| G0-señales (5 casos de ajuste, semilla 20261124) | Superada: señales calculables en los 5, la pasada sin voltear reproduce `segment_all` exactamente, entre 8,4 y 18,5 s por caso |
| Puerta S (34 casos de calibración) | **Superada:** 22 de 34 a ≤ 10 % de la referencia (64,7 %; el mínimo es 50 %). Dice mediano 0,884 |
| Puerta C (34 casos de calibración) | **No superada: 0 verdes** (26 amarillas y 8 rojas) |

Archivos: `results/h23/` (`g0_scale.json`, `g0_signals.json`, `calibrate.json`, `cal_lights.csv`, las redes y sus
registros). No se generó ningún congelado.

## Por qué no hay verdes (descriptivo, solo calibración)

Para la luz verde hacen falta tres condiciones a la vez: dentro del dominio, s_flip ≤ 0,05 y s_stage ≤ 0,10.

| Condición | Casos que la cumplen (de 34) |
|---|---|
| s_flip ≤ 0,05 (mediana 0,080; rango 0,025–0,733) | 9 |
| s_stage ≤ 0,10 (mediana 0,128; rango 0,059–0,312) | 7 |
| Las dos señales | 3 |
| Dentro del dominio (guardia ajustada sin el embrión) | 5 |
| Las tres | **0** |

Lectura [HIP]:

- **La red mide mejor de lo que dice su estabilidad.** El 65 % de los casos queda a ≤ 10 %, pero solo el 9 % (3 casos)
  tiene las dos señales bajo sus umbrales. En una estructura de unos cientos de vóxeles a ½ de resolución, voltear la
  imagen o pasar de la etapa 1 a la etapa 2 cambia el volumen más de un 5–10 %, aunque la medida final sea buena.
- **Los umbrales se fijaron para el cuerpo** (H20) y no se reajustaron, como pedía el preregistro. Así, la regla resulta
  más estricta en ventrículo que en cuerpo.
- **La guardia de dominio** deja dentro solo 5 de 34. Con 34 casos repartidos en 5 pliegues, la envolvente del 1–99 % de
  cada pliegue es estrecha.

Es una lectura de la calibración y no se prueba aquí. Cambiar los umbrales o la guardia para ventrículo sería un estudio
nuevo, con su propio preregistro, y la prueba sigue intacta para él.

## Qué significa (§9 del preregistro)

Corresponde a la fila «Puerta C no superada». Con la regla de H20 sin cambios, la estabilidad de la red **no da ninguna
luz verde** en ventrículo, ni siquiera en la calibración. Por tanto, H23 no puede decir si la luz separa aciertos de
fallos (H23d), que era la pregunta que H20 dejó abierta.

Lo que sí aporta:

- **La arquitectura de dos etapas de H19 también mide ventrículos razonablemente** (65 % a ≤ 10 %, Dice mediano 0,88 en
  la calibración), una vez que se cuentan todas las piezas (D-1).
- **La regla de H20 no se traslada tal cual** a una estructura pequeña: es un límite de esas señales, que hay que
  publicar.

## Qué no se puede concluir

- Nada sobre la prueba: no se abrió.
- Nada sobre otros conjuntos o equipos: todo sale de un solo conjunto.
- Que otros umbrales funcionen: elegirlos ahora, mirando la calibración, sería ajustar después de ver los datos.
- Nada sobre humanos, hidrocefalia ni uso clínico.

## Siguiente paso posible (requiere decisión y preregistro nuevo)

Una regla de luz verde con umbrales **relativos a la estructura**, por ejemplo escalados por la relación superficie /
volumen. Se fijaría antes de mirar la prueba de ventrículo, que sigue intacta.
