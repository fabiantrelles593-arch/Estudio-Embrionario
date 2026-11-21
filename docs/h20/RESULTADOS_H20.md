# H20 — Resultados: señales de fiabilidad de la propia red y regla fija

> Aplica `docs/h20/PREREGISTRO_H20.md` (v1.0, 20 nov 2026) sin desviaciones. Las cifras salen de
> `scripts/h20_report.py` sobre `results/h20/` (fuera de git); los veredictos son los del código preregistrado
> (`geovida.h20`), transcritos sin cambios. Datos: ecografía 3D de alta frecuencia de embriones de ratón (Qiu et al.
> 2021, IEEE DataPort, CC BY). Solo investigación con datos animales publicados; sin uso clínico. Etiquetas: [HV] hecho
> verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta · [PV] pendiente de validación.

## 1. Resumen

* **H20b (primaria): apoyada [HV].** Entre los 21 casos de prueba con luz verde, 1 tiene |error| de volumen > 10 %:
  4,8 % (IC 95 % por embrión: 0,0 % a 14,3 %). Evaluable: 21 verdes en 21 embriones (mínimo 20 en 15).
* **Pero la luz apenas separa en la prueba [HV].** La red de H19 falla poco en embriones nuevos: 3 de 44 casos
  (6,8 %) superan el 10 %. Entre los no verdes fallan 2 de 23 (8,7 %); la diferencia con los verdes es de 3,9 puntos,
  con un IC de −11,4 a 20,0 que incluye 0 (H20d). Dar verde a todos los casos también habría quedado por debajo del
  10 % de fallos. **El veredicto apoyado dice sobre todo que la red es exacta en este conjunto, no que el certificado
  distinga bien sus fallos.**
* **Primera medida de la red de H19 en embriones nuevos (H20c) [HV]:** Dice mediano 0,939; |error| mediano 2,6 %;
  93,2 % de los casos a ≤ 10 % y 75,0 % a ≤ 5 %.

## 2. Orden seguido (§5)

| Paso | Resultado | Dónde |
|---|---|---|
| G0 (5 casos de ajuste, ya vistos por la red) | Superada: señales calculables en los 5; la pasada identidad reproduce exactamente el volumen de H19; 13–23 s por caso (límite 300 s) | `results/h20/g0.json` |
| Calibración (27 casos) | La pasada identidad reproduce el error de H19 en los 27 (tolerancia 10⁻¹²) | `results/h20/cal_signals.jsonl` |
| Puerta C (la de H19, sin cambios) | **Superada:** 12 verdes, ninguna con \|error\| > 10 % (máximo permitido 10 %) | `results/h20/calibrate.json`, `cal_lights.csv` |
| Candado | SHA-256 del congelado `66d7ffcf…7250804e` anotado en el §10 y subido a la rama **antes** de `test`; se comprobó en la rama | `docs/h20/PREREGISTRO_H20.md` §10 |
| Prueba (44 casos de 43 embriones, cerrada hasta hoy) | Medida una sola vez con `run_h20.py test --sha`; redes, umbrales y envolvente comprobados contra el congelado | `results/h20/test_verdicts.json`, `test_cases.csv` |

Luces en la calibración (guardia de dominio ajustada fuera de pliegue):

| Luz | Casos (con guardia) | \|error\| > 10 % | Casos (sin guardia) | \|error\| > 10 % |
|---|---|---|---|---|
| verde | 12 | 0 | 13 | 0 |
| amarillo | 13 | 2 | 12 | 2 |
| rojo | 2 | 1 | 2 | 1 |

Con las mismas redes, la puerta C de H19 había fallado (2 de 16 verdes fallaban) con observables de imagen. Las
señales de estabilidad de la propia red la superaron [HV, 27 casos].

## 3. Prueba: veredictos y descriptivos

| Hipótesis | Estimación | IC 95 % | Veredicto |
|---|---|---|---|
| H20b (primaria): fallos entre verdes | 4,8 % (1 de 21) | 0,0 % a 14,3 % | **apoyada** |

* **H20a, cobertura:** 21 verdes (47,7 %), 22 amarillos, 1 rojo.
* **H20c, acuerdo de la red:** Dice mediano 0,939; |error| mediano 2,6 %; a ≤ 10 %: 93,2 %; a ≤ 5 %: 75,0 %.
* **H20d, separación:** fallos entre verdes 4,8 %, entre no verdes 8,7 %, diferencia 3,9 puntos (IC −11,4 a 20,0).
  Dentro del dominio: 77,3 %. Sin la guardia habría 25 verdes, de las que 1 falla.
* **|error| mediano por luz [HV]:** verdes 1,6 % (máximo 12,9 %); amarillos 4,3 % (máximo 23,7 %); el único rojo,
  0,6 %, es una falsa alarma.

Los tres casos con |error| > 10 % [HV]:

| Caso | Luz | En dominio | Error de volumen | s_flip | s_stage | Dice |
|---|---|---|---|---|---|---|
| `nii_test/E11/20170320_En1_E11_E1a.nii` | verde | sí | −12,9 % | 0,035 | 0,020 | 0,907 |
| `nii_test/E11/20170320_En1_E11_E2a.nii` | amarillo | no | −23,7 % | 0,063 | 0,007 | 0,854 |
| `nii_test/E12/20170329_En1_E12_E4a.nii` | amarillo | sí | +10,9 % | 0,091 | 0,003 | 0,918 |

La verde que falla infraestima el volumen un 12,9 % con las dos señales bajas. Es el tipo de error que el §9 ya
avisaba que no se ve: la red se equivoca igual en las 8 entradas [EI, 1 caso].

## 4. Predicciones escritas de antemano (§7)

| Predicción | Probabilidad escrita | ¿Ocurrió? |
|---|---|---|
| Pasa G0 | 90 % | Sí |
| Pasa la puerta C | 40 % | Sí |
| H20b evaluable, dado que se abre la prueba | 45 % | Sí |
| H20b apoyada, dado que es evaluable | 60 % | Sí |
| En la prueba, ≥ 75 % de los casos a ≤ 10 % (H20c) | 60 % | Sí (93,2 %) |

## 5. Qué significa (fila del §8) y qué no

* **Fila del §8, H20b apoyada:** en este conjunto, una luz verde dada solo por la estabilidad de la red acertó en
  embriones nuevos. Siguiente paso fijado: replicar con otro conjunto o equipo y estudiar los amarillos.
* **Matiz obligado [HV]:** con una tasa de fallo de base del 6,8 %, el criterio de H20b (≤ 10 % de fallos entre
  verdes) se cumplía casi por cualquier regla que dejara verdes suficientes. H20d, que mide la separación, no la
  demuestra: su IC incluye 0. El preregistro no fijó un criterio frente a «verde para todos», y no se añade ahora.
  Se informa como límite principal.
* **No se puede concluir** (§9): la referencia es un contorno humano; 44 casos de un conjunto, un equipo y una especie;
  los umbrales son juicios previos y no se han comparado con otros; las señales miden inestabilidad, no exactitud;
  nada sobre humanos, obstetricia ni uso clínico.
* **Lo que deja la serie H18–H20 [HV]:** H18 (segmentador de umbral con limpieza) no midió bien. H19 (red de dos etapas)
  sí mide, pero su certificado de imagen no pasó la puerta C. H20 (estabilidad de la red) pasó la puerta C y su
  primaria salió apoyada en la prueba. Esa prueba ya está usada y no decide dos veces.

## 6. Siguiente paso [PROP, sin decidir]

* Replicar en otro conjunto de ecografía 3D con licencia verificada, con un preregistro nuevo que **sí** compare con
  «verde para todos» o exija separación (H20d) como criterio, porque aquí la tasa de fallo de base era baja.
* Estudiar los amarillos de la calibración (13), nunca los de la prueba, para ver qué señal los vuelve amarillos.
