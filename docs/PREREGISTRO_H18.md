# Preregistro — H18: ¿acierta la luz verde de un certificado calibrado con ecografía real, en embriones que nunca vio? (v1.0, 19 nov 2026)

> Siguiente paso fijado por la tabla §5 de `docs/PREREGISTRO_H12R.md` («calibrar con los propios volúmenes reales,
> validando por embrión») y por `docs/h11/RESULTADOS_H12R.md` §3. Se sube **antes** de correr ningún segmentador
> nuevo sobre ninguna imagen. Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis ·
> [PROP] propuesta. Solo datos animales publicados (Qiu et al. 2021, CC BY). Nada humano ni clínico.

## 1. Pregunta y por qué cambia el plan de H12R

H11 y H12R terminaron sin ninguna luz verde que evaluar. Pero la causa no es solo la guardia: **ningún** caso de cuerpo
quedó a menos del 58 % de la referencia con los segmentadores de geovida (error mediano 278–735 %) [HV,
`RESULTADOS_H11.md` §3]. Un modelo de Pr(|error| ≤ 10 %) calibrado con esos datos tendría 0 éxitos de los que
aprender: daría rojo a todo. «Calibrar con datos reales» solo tiene sentido si antes hay un segmentador que a veces
acierte. Por eso H18 tiene dos partes, en este orden:

1. **Desarrollo, solo con embriones de entrenamiento:** elegir un segmentador de una familia fija y calibrar con él el
   certificado (modelo de probabilidad y envolvente de dominio).
2. **Prueba, una sola vez, con embriones que el desarrollo nunca leyó:** ¿falla poco la luz verde?

> Con un segmentador y un certificado elegidos y calibrados solo con embriones de entrenamiento, entre las medidas de
> cuerpo de embriones de prueba que reciben luz verde, ¿la fracción con |error de volumen| > 10 % es ≤ 10 %?

## 2. Datos y reparto (fijos)

* **Conjunto:** el mismo de H11 (`manifiesto_qiu2021.csv`, SHA-256 `e0d2782a…c016dd`), solo **cuerpo**: 180 casos de
  170 embriones. Las 47 etiquetas con otro vóxel (D1 de H11) quedan fuera, como en el análisis principal de H11.
* **Reparto:** el de los autores del conjunto, por carpeta (`nii_train` → entrenamiento, `nii_test` → prueba), **por
  embrión**: un embrión con casos en las dos carpetas pasa entero a entrenamiento (`geovida.h18.split_cases`).
  Resultado, calculado sin leer ninguna imagen (`results/h18/reparto.json`) [HV]:
  **entrenamiento 136 casos de 127 embriones; prueba 44 casos de 43 embriones**. Dos embriones (`20170619_E12_E4`,
  `20170619_E12_E6`) estaban en las dos carpetas; sus 2 casos de prueba pasaron a entrenamiento.
* **Lo que ya se vio de la prueba (se declara):** los resultados agregados de H11 y H12R, que incluyen estos 44 casos,
  con los segmentadores antiguos. Ningún segmentador de la familia de §3 se ha corrido sobre ninguna imagen.

## 3. Desarrollo (solo entrenamiento; fijo)

**Familia de segmentadores** `smooth_lcc` (`geovida.h18`): suavizado gaussiano de `sigma` vóxeles → umbral `thr` ×
Otsu → componente conectada mayor (26) → cierre con bola de radio `close` vóxeles → relleno de huecos. Rejilla fija de
**18 configuraciones**: `sigma` ∈ {1, 2, 4}, `thr` ∈ {0,9; 1,0; 1,1}, `close` ∈ {0, 3}. **No se prueba nada fuera de
esta rejilla**; si ninguna sirve, el resultado es ese.

*Por qué esta familia [EI]:* en H11 los umbrales sobrestimaron el volumen porque el moteado deja islas por encima del
umbral fuera del embrión (§3 de `RESULTADOS_H11.md`). Quedarse con la componente mayor y rellenar ataca justo eso. El
precio: una cavidad real se rellena, así que **este segmentador no se usa para topología** (no hay H18 de topología).

**Selección:** la configuración con más casos de entrenamiento a ≤ 10 % de la referencia; desempates: mayor Dice
mediano, menor `sigma`, `thr` más cerca de 1, menor `close` (`select_config`).

**Certificado:** con la configuración elegida, sobre los 136 casos de entrenamiento:

* observables sin verdad: `d_over_hgeo`, `snr_hat` y `edge_width` (los de v0.4);
* modelo: logit con ridge (λ = 1) de Pr(|error| ≤ 10 %) sobre sus logaritmos (`fit_logit_multi`);
* luces: verde si p ≥ 0,90, roja si p < 0,50 (umbrales de H6, sin cambiar);
* guardia: envolvente de cuantiles 1–99 % de `snr_hat` y `edge_width` en entrenamiento; fuera, verde → amarillo.

**Puerta F (viabilidad, en entrenamiento):** predicciones **fuera de pliegue** con 5 pliegues por embrión (semilla
20261120): cada caso recibe su luz de un certificado ajustado sin su embrión. Pasa si, con esas luces, la regla de
H18b de §5 da «apoyada» en el propio entrenamiento. **Si no pasa, la prueba no se abre** y H18 queda «no evaluable por
diseño». La selección de la configuración sí usó todo el entrenamiento, así que la puerta es optimista: es una
condición necesaria, no una estimación.

## 4. Orden de ejecución y candado

`scripts/run_h18.py`, en este orden:

1. `split` (hecho, §2). 2. `develop`: rejilla en entrenamiento. 3. `observe`: observables con la configuración
elegida. 4. `freeze`: puerta F; si pasa, escribe `results/h18/h18_frozen.json`.
5. **El SHA-256 del congelado se anota en §9 y se sube a la rama.** 6. `test --sha <ese valor>`: `check_frozen`
se niega a correr con cualquier otro archivo.

`develop` y `observe` solo leen casos de entrenamiento (`_cases` filtra por reparto; prueba incluida en
`tests/test_h18.py`). Nada del certificado se cambia después de abrir la prueba.

## 5. Hipótesis y criterios (fijos)

**Primaria: H18b — la luz verde no falla demasiado en embriones nuevos.** Entre los casos de prueba con luz verde (con
guardia), fracción con |error| > 10 %. IC 95 % por remuestreo de **embriones** (2000 réplicas, semilla 20261120).
*Apoyada* si la estimación es ≤ 10 %; *no apoyada* si el límite inferior del IC supera 10 %; *no concluyente* en otro
caso. **Evaluable** con ≥ 20 verdes en ≥ 15 embriones. El mínimo es menor que el de H11 (30) porque la prueba tiene
solo 44 casos; con 20 verdes el intervalo es ancho y una «apoyada» es evidencia débil (§8).

**Secundarias y descriptivas (prueba):**

* **H18a — Cobertura.** Fracción de casos de prueba con verde. Sin criterio: dice si el certificado deja de ser «seguro
  pero vacío».
* **H18c — Acuerdo.** Dice mediano, |error| mediano y fracción a ≤ 10 % y ≤ 5 % del segmentador elegido. Se compara,
  solo de forma descriptiva, con `smoothed_otsu` en los mismos casos (de `h11_v04_cases.csv`).
* **H18d — Guardia.** Fracción de casos de prueba dentro del dominio; verdes sin guardia y cuántos fallan.

Un valor no calculable es «no evaluable», nunca «no apoyada».

## 6. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| La mejor configuración deja ≥ 50 % de los casos de entrenamiento a ≤ 10 % | 35 % |
| Pasa la puerta F | 30 % |
| H18b evaluable, dado que pasa F | 50 % |
| H18b apoyada, dado que es evaluable | 55 % |
| Dice mediano en prueba ≥ 0,80 | 40 % |

La predicción más probable es que el desarrollo no llegue a abrir la prueba: un umbral global, aun limpio, puede no
bastar para separar el embrión de la pared uterina en esta ecografía [HIP].

## 7. Qué significará cada resultado (antes de verlo)

| Resultado | Conclusión | Siguiente paso |
|---|---|---|
| Puerta F no superada | Con segmentadores de umbral, ni con limpieza, hay medidas fiables en este conjunto; el certificado no tiene nada que certificar | Hace falta un segmentador aprendido (p. ej. una red entrenada con los contornos de entrenamiento), con su propio preregistro y la misma prueba intacta |
| H18b apoyada | En este conjunto, un certificado calibrado con datos reales acertó en embriones nuevos | Replicar con otro conjunto u otro equipo antes de afirmar más |
| H18b no apoyada | La luz verde falla aun calibrada con datos reales | Publicarlo; revisar qué distingue los verdes que fallan |
| H18b no evaluable o no concluyente | Faltan casos verdes o embriones | Más datos con el mismo protocolo; la prueba ya usada no se reutiliza para decidir |

## 8. Qué no se puede concluir

* La referencia es un contorno humano: se mide acuerdo, no error exacto.
* 44 casos de prueba de un conjunto, un equipo y una especie: intervalos anchos.
* El reparto de los autores se supone sin fugas por embrión salvo las dos corregidas; si la identidad del embrión
  (D1 de H11) junta embriones distintos, solo hace el reparto más prudente.
* Nada sobre humanos, obstetricia ni uso clínico. Una luz verde sigue sin ser una validación clínica.

## 9. Desviaciones

(Ninguna al subir este preregistro.)
