# Resultados H24: luz de fiabilidad con la tolerancia en vóxeles de borde (26 nov 2026)

> Preregistro: `docs/h24/PREREGISTRO_H24.md` (v1.0, aprobado el 26 nov y subido a la rama en `dfa8c9e` antes de
> calcular ninguna señal; CI en verde).
>
> **Datos:** ecografía 3D de alta frecuencia de embriones de ratón (Qiu et al. 2021, IEEE DataPort,
> doi:10.21227/drmd-xq36, CC BY). Nada humano ni clínico.
>
> **Etiquetas:** [HV] verificado · [HIP] hipótesis.

## Veredicto

**H24 se cierra como no evaluable: la puerta C′ no se superó.** En la calibración hubo **3 verdes de 34**, y la puerta
pide al menos 10. Además, 1 de esas 3 falla.

**La prueba de ventrículo no se abrió:** sus 40 casos siguen sin procesarse con ninguna red de ventrículo. H24b, H24d y
la exploratoria H24f no se evaluaron.

## Orden de ejecución [HV]

| Paso | Resultado |
|---|---|
| `check` | Las huellas SHA-256 de las dos redes de H23 coinciden con §4 |
| G0 (5 casos de ajuste, semilla 20261126) | Superada: señales y superficies calculables en los 5; la pasada sin voltear reproduce `segment_all`; entre 10,6 y 30,2 s por caso |
| Puerta S′ (34 casos de calibración) | **Superada:** 29 de 34 con e_b ≤ 0,5 vóxeles (85,3 %; el mínimo es 50 %) |
| Puerta C′ (34 casos de calibración) | **No superada: 3 verdes** (30 amarillas y 1 roja); 1 de las 3 con e_b > 0,5 |

Comprobación descriptiva: la medida coincide exactamente con la de H23 en los 34 casos (mismas redes, mismo código).

Archivos: `results/h24/` (`check.json`, `g0.json`, `calibrate.json`, `cal_rows.jsonl`, `cal_lights.csv`). No se generó
ningún congelado.

## Por qué hay tan pocas verdes (descriptivo, solo calibración)

| Condición | Casos que la cumplen (de 34) |
|---|---|
| b_flip ≤ 0,25 (mediana 0,22; P10–P90 0,09–0,68) | 20 |
| b_stage ≤ 0,50 (mediana 0,37; P10–P90 0,25–0,46) | 32 |
| Las dos señales | 19 |
| Dentro del dominio (guardia ajustada sin el embrión) | 5 |
| Las tres | **3** |

Error en vóxeles de borde: mediana 0,12 (P10 0,05; P90 0,57). Fallan 5 de 34. Dice mediano 0,884.

**El cuello de botella fue la guardia de dominio, no las señales.**

- Con la nueva unidad, las dos señales quedan bajo sus umbrales en 19 de 34 casos (en H23 eran 3).
- Pero la guardia, que el preregistro mantuvo sin cambios respecto de H23, deja dentro **solo 5 de 34**.
- La guardia depende solo de la máscara medida, y esa máscara es idéntica a la de H23. Por eso salen los mismos 5 casos
  que en H23.

**Error de diseño, declarado.** En H23 ya se veía que la guardia admitía 5 de 34 [HV, `docs/h23/RESULTADOS_H23.md`].
Con la guardia sin cambios, la puerta C′ nunca podía llegar a 10 verdes. **H24 no podía superar esa puerta, y el
preregistro debió verlo antes.** La predicción del 50 % para C′ (§8) era, por tanto, demasiado alta. Es un fallo de
quien diseñó el estudio, no de la pregunta.

Sin guardia (descriptivo, como H24e pero en calibración): 19 verdes en 18 embriones, de las que falla 1 (5,3 %); entre
las 15 no verdes fallan 4 (27 %). Son datos ya vistos y no prueban nada. [HIP] Sugieren que las señales en vóxeles de
borde podrían separar aciertos de fallos si la guardia no bloqueara.

## Qué significa (§9 del preregistro)

Corresponde a la fila «Puerta C′ no superada», pero la causa no es la que esa fila preveía:

- **No se puede decir** que la estabilidad de la red, medida en vóxeles de borde, no anticipe los fallos.
- **Lo que se puede decir** es que una guardia de dominio ajustada con 34 casos en 5 pliegues rechaza el 85 % de los
  casos de ventrículo, y con ella no hay luz verde posible.

## Qué no se puede concluir

- Nada sobre la prueba: no se abrió.
- Que quitar o ensanchar la guardia funcione: decidirlo ahora, mirando estas cifras, sería ajustar después de ver los
  datos. Las 19 verdes sin guardia son un dato visto, no una evidencia.
- Nada sobre otros conjuntos o equipos.
- Nada sobre humanos, hidrocefalia ni uso clínico.

## Siguiente paso posible (requiere decisión del autor y preregistro nuevo)

La prueba de ventrículo sigue intacta. Un estudio nuevo que revisara la guardia tendría un problema serio: se diseñaría
sabiendo que, sin ella, la calibración da 19 verdes con 1 fallo.

Las alternativas honestas son dos:

- revisar la guardia con un criterio fijado por principio, declarando todo lo que ya se vio, y aceptando que la
  calibración ya no frena nada;
- o reservar la pregunta para un segundo conjunto de datos (la petición al grupo de NYU sigue pendiente de envío).
