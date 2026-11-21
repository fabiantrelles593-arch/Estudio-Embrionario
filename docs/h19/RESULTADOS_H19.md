# Resultados — H19: segmentador aprendido (U-Net 3D de dos etapas) y certificado calibrado con ecografía real (20 nov 2026)

> Transcripción de `docs/PREREGISTRO_H19.md` (§4–§7). **Nada se reinterpreta ni se reajusta.** Los números salen de
> `results/h19/calibrate.json`, `cal_rows.jsonl`, `coarse.log` y `fine.log` (fuera de git, como los datos y las redes).
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta. Solo datos animales
> publicados (Qiu et al. 2021, CC BY). Nada humano ni clínico.

## 1. Qué se hizo

| Elemento | Valor |
|---|---|
| Reparto | 109 casos de ajuste (102 embriones) y 27 de calibración (25 embriones), por embrión, semilla 20261121 (`results/h19/reparto.json`) [HV] |
| Etapa 1 | 150 épocas a ¼ de resolución; pérdida final 0,10 (19 nov 21:10 → 20 nov 03:06) [HV] |
| Etapa 2 | 100 épocas a ½ resolución en la caja de la etapa 1 (margen 6), 109 cajas; pérdida final 0,13 (20 nov 03:07 → 16:51) [HV] |
| Redes | SHA-256 `coarse` c76fe6be…6b9b26, `fine` 21d64425…6e2989 (completas en `calibrate.json`) [HV] |
| Calibración | Los 27 casos que la red no vio; certificado fuera de pliegue (5 pliegues por embrión), puertas S y C [HV] |
| Prueba | **No se abrió.** `calibrate` no congeló certificado (no existe `results/h19/h19_frozen.json`) y `test` no se ejecutó [HV] |
| Código | Huella en `calibrate.json`: `h19.py` a9ce1cc, `run_h19.py` 651a058, los mismos blobs que hay en la rama [HV] |

## 2. Segmentador, en calibración (puerta S)

| | Valor |
|---|---|
| Casos a ≤ 10 % de la referencia | **24 de 27** (88,9 %); a ≤ 5 %: 23 |
| \|error de volumen\| mediano | 2,3 %; error con signo mediano +0,1 % (14 sobrestiman, 13 subestiman) |
| Dice mediano (mínimo) | 0,938 (0,682) |
| Puerta S (≥ 50 % a ≤ 10 %) | **Superada** [HV] |

El Dice mediano queda junto al publicado (0,934), pero con otra red, otro tamaño y otro reparto: es una comparación
descriptiva, no una réplica [EI]. Frente a H18 (1 de 136 a ≤ 10 %, error mediano 194 %), el segmentador aprendido sí
mide el volumen del cuerpo en la mayoría de los casos [HV].

## 3. Certificado, en calibración (puerta C)

| | Valor |
|---|---|
| Luces fuera de pliegue | 16 verdes, 9 amarillas, 2 rojas; 24 de 27 dentro del dominio |
| Verdes con \|error\| > 10 % | **2 de 16 (12,5 %)** |
| Puerta C (≥ 10 verdes y ≤ 10 % de fallos) | **No superada** [HV] |

> Veredicto preregistrado: **la prueba no se abre; H19b no evaluable por diseño (puerta C).** H19a–H19d no se calculan.

Las dos verdes que fallan (descriptivo, no cambia el veredicto):

| Caso | Error de volumen | Dice | p(≤ 10 %) |
|---|---|---|---|
| `E10/20170327_En1_E10_E2a` | +71,9 % | 0,682 | 0,93 |
| `E12/20170619_En1_E12_Ex_E3a_reg` | +10,6 % | 0,895 | 0,97 |

## 4. Predicciones escritas de antemano (§6)

| Predicción | Probabilidad | Resultado |
|---|---|---|
| Pasa la puerta S | 45 % | Ocurrió (88,9 %) |
| Pasa la puerta C, dado S | 40 % | No ocurrió |
| Dice mediano en calibración ≥ 0,85 | 50 % | Ocurrió (0,938) |
| H19b evaluable, dado que se abre la prueba | 50 % | No aplica |
| H19b apoyada, dado que es evaluable | 55 % | No aplica |

## 5. Qué significa (fila «S sí, C no» de §7)

«La red acierta a veces, pero los observables no anticipan cuándo. Buscar observables de fiabilidad de la red (p. ej.
varias pasadas); preregistro nuevo.»

* **El certificado no aporta información en calibración [HV, descriptivo, n = 27].** Dar verde a los 27 casos habría
  fallado en 3 (11,1 %); las 16 verdes del certificado fallan en 2 (12,5 %). El peor caso de la calibración (+72 %) recibió
  verde con p = 0,93.
* **Los observables apenas se relacionan con el error [HV, descriptivo].** Correlación de Spearman con el |error|:
  banda incierta −0,30, d/h_geo −0,06, SNR estimada −0,01, anchura de borde −0,04. El signo de la banda incierta es el
  contrario del esperado (más vóxeles dudosos en el borde no acompañan a más error). Con 27 casos y 3 fallos no se puede
  decir más.
* **El cuello de botella cambió de sitio [HV].** En H18 no había medidas fiables que certificar; en H19 la mayoría lo son
  y lo que falta es saber cuáles. Eso apunta a observables de la propia red (dispersión entre varias pasadas o entre
  redes, confianza de la etapa 1 frente a la 2) [HIP], no a otro segmentador.
* **La prueba sigue intacta [HV]:** los 44 casos de prueba no se han leído con H18 ni con H19, así que un preregistro
  nuevo puede usarlos. Ese preregistro tendrá que declarar que los 27 casos de calibración ya se han visto con estos
  observables y estos errores.
* **Margen pequeño, sin reintento.** Con un fallo menos entre las verdes la puerta habría pasado. Eso no autoriza a
  cambiar la regla, los pliegues ni el umbral después de ver el resultado: el veredicto queda así.

## 6. Qué no se puede concluir

- Que el certificado falle o acierte en embriones nuevos: no se llegó a probar.
- Que la red mida al 10 % en la prueba: la puerta S es una condición necesaria con 27 casos, no una estimación.
- Que la red sea equivalente a la publicada: otra arquitectura, otro tamaño y otro reparto.
- Nada sobre humanos, obstetricia ni uso clínico.
