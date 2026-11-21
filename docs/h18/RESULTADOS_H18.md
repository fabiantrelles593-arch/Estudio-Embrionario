# Resultados — H18: segmentador de umbral con limpieza y certificado calibrado con ecografía real (19 nov 2026)

> Transcripción de `docs/PREREGISTRO_H18.md` (§3–§7). **Nada se reinterpreta ni se reajusta.** Los números salen de
> `results/h18/grid_train.jsonl`, `obs_train_s4_t1.1_c3.jsonl` y `freeze.json` (fuera de git, como los datos).
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta. Solo datos animales
> publicados (Qiu et al. 2021, CC BY). Nada humano ni clínico.

## 1. Qué se hizo

| Elemento | Valor |
|---|---|
| Reparto | Por embrión, el de los autores: 136 casos de entrenamiento (127 embriones), 44 de prueba (43 embriones) [HV] |
| Desarrollo | Las 18 configuraciones de `smooth_lcc` en los 136 casos de entrenamiento (`develop`), observables con la elegida (`observe`), puerta F (`freeze`) [HV] |
| Prueba | **No se abrió.** No existe `results/h18/h18_frozen.json` ni ninguna fila de prueba [HV] |
| Código | Huella guardada por `freeze`: `h18.py` 34d59b9 y `run_h18.py` 0b3b67c, los blobs subidos con el preregistro [HV] |

## 2. Resultado del desarrollo (solo entrenamiento)

| | Valor |
|---|---|
| Configuración elegida por la regla de §3 | `sigma` 4, `thr` 1,1, `close` 3 |
| Casos a ≤ 10 % de la referencia | **1 de 136** (0,7 %); a ≤ 20 %: 2; a ≤ 50 %: 3 |
| \|error de volumen\| mediano | 194 % |
| Dice mediano (máximo) | 0,30 (0,68) |
| Mejor configuración posible caso a caso (cota optimista) | 1 de 136 a ≤ 10 %; \|error\| mediano 175 % |
| Signo del error | **Positivo en las 136 × 18 medidas**: siempre sobrestima [HV] |

Ninguna de las 18 configuraciones superó un caso a ≤ 10 % (dos llegaron a 1; las demás, a 0) [HV].

## 3. Puerta F

Con predicciones fuera de pliegue (5 pliegues por embrión), el certificado dio **rojo a los 136 casos** (probabilidad
máxima de acertar 0,021): **0 verdes**, así que la regla de H18b es «no evaluable» y la puerta **no se supera** [HV].

> Veredicto preregistrado: **H18 no evaluable por diseño.** H18a–H18d no se calculan porque la prueba no se abrió.

## 4. Predicciones escritas de antemano (§6)

| Predicción | Probabilidad | Resultado |
|---|---|---|
| La mejor configuración deja ≥ 50 % de los casos a ≤ 10 % | 35 % | No ocurrió (0,7 %) |
| Pasa la puerta F | 30 % | No ocurrió |
| H18b evaluable, dado F | 50 % | No aplica |
| H18b apoyada, dado que es evaluable | 55 % | No aplica |
| Dice mediano en prueba ≥ 0,80 | 40 % | No aplica (prueba sin abrir) |

## 5. Qué significa (fila «puerta F no superada» de §7)

«Con segmentadores de umbral, ni con limpieza, hay medidas fiables en este conjunto; el certificado no tiene nada que
certificar. Hace falta un segmentador aprendido […] con su propio preregistro y la misma prueba intacta.»

* **El fallo es sistemático, no de ajuste [HV].** Todas las medidas sobrestiman: la componente conectada mayor incluye
  tejido alrededor del embrión (pared uterina, membranas) que el umbral no separa. Ni el suavizado, ni el umbral, ni el
  cierre cambian eso dentro de la rejilla.
* **Coherente con la literatura del conjunto [EI].** Los autores segmentan el cuerpo con redes 3D de dos etapas y publican
  un Dice de 0,934 (Xu et al. 2020, doi:10.1109/isbi45749.2020.9098387; Qiu et al. 2021, doi:10.1109/TUFFC.2021.3068156).
* **La prueba sigue intacta [HV]:** los 44 casos de prueba no se han leído con ningún método nuevo, así que sirven para
  H19 (`docs/PREREGISTRO_H19.md`), el segmentador aprendido que pide §7.

## 6. Qué no se puede concluir

- Que un certificado calibrado con datos reales falle o acierte: no se llegó a probar.
- Que no exista un umbral que funcione fuera de esta rejilla: solo se probó la rejilla fijada.
- Nada sobre humanos, obstetricia ni uso clínico.
