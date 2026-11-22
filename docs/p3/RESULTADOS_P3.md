# P3 — Resultados del confirmatorio (MusMorph IMPC E15.5, 60 especímenes)

> Aplica `docs/PREREGISTRO_P3.md` con sus desviaciones D1–D5, todas registradas antes de calcular ninguna medida de
> las hipótesis. Cifras generadas por `scripts/p3_report.py --confirm results/p3/confirmatorio.json` (veredictos del
> código preregistrado, `geovida.p3`, transcritos sin cambios) y tablas de `results/p3/` (fuera de git). Solo
> investigación con datos animales publicados; sin uso clínico. Etiquetas: [HV] hecho verificado · [EI] evidencia
> indirecta · [HIP] hipótesis · [PROP] propuesta · [PV] pendiente de validación.

## 1. Resumen

* **H-P3a (primaria): apoyada [HV].** La fracción técnica τ del log-volumen es mayor en las estructuras pequeñas o
  delgadas que en las grandes o compactas. Las dos reglas de recuperación de etiquetas (D1) dan el mismo veredicto,
  así que se interpreta.
* **H-P3b (MORPHO-TRACE): no interpretable [HV].** Con la regla principal (`nearest`) sale «no apoyada»; con la
  regla `exact` sale «apoyada». El orden de las estructuras por τ discrepa entre reglas (ρ = 0,45 < 0,7), y D1 dice que
  en ese caso una hipótesis solo se interpreta si las dos reglas coinciden. **No se concluye nada sobre el
  certificado**, ni a favor ni en contra.
* **Tabla §7:** la combinación «H-P3a apoyada, H-P3b no interpretable» no está prevista. Se informa tal cual y no se
  reinterpreta.

## 2. Qué se ejecutó

* 60 especímenes del confirmatorio (30 + 30 por sexo, disjuntos del piloto, semilla 20261114), sin ausencias. La
  regla de ampliación de D4 fijó n = 60 a partir del piloto (`docs/p3/RESULTADOS_PILOTO.md`).
* 6 condiciones por espécimen (resolución ×1, ×2, ×4 × segmentador atlas propagado o MEMOS); 48 estructuras en 36
  unidades (18 «delgadas», 18 «compactas», grupos fijados con el atlas de consenso antes de ver especímenes, D4).
* Remuestreo por espécimen: 2000 réplicas, semilla 20261115.
* La pasada principal (`nearest`) terminó el 20 nov. El resumen se escribió después con
  `p3_analyze.py confirm --reuse-main`, que lee las tablas guardadas de esa pasada y comprueba que los especímenes son
  los de la selección, y añade la pasada `exact` de D1 (52 898 s, unas 14,7 h). Por eso el tiempo de la pasada
  principal no figura en el resumen.

## 3. Veredictos preregistrados

| Hipótesis | Regla `nearest` (principal) | IC 95 % | Veredicto | Regla `exact` (D1) | Veredicto tras D1 |
|---|---|---|---|---|---|
| H-P3a | Δ = 0,085 | 0,042 a 0,171 | apoyada | Δ = 0,216 (IC 0,144 a 0,288) → apoyada | **apoyada** |
| H-P3b | ρ = −0,016; ρ parcial = −0,084 | −0,280 a −0,047 (ρ parcial) | no apoyada | ρ = −0,511; ρ parcial = −0,436 (IC −0,590 a −0,355) → apoyada | **no interpretable (D1)** |

Concordancia de órdenes:

* τ con `nearest` frente a `exact`: ρ de Spearman = 0,45 en 48 estructuras → **discrepan** (umbral 0,7). Es esto lo
  que activa la regla de D1.
* τ por varianzas frente al modelo mixto (§5.4): ρ = 1,00; los 48 modelos convergieron. La medida de τ no depende de
  cómo se estime.

### 3.1 Una laguna en el texto del criterio de H-P3b (no cambia el veredicto)

El §6 define «apoyada» (|ρ| ≥ 0,5 y el IC de la correlación parcial excluye 0 en la dirección esperada) y «no
apoyada» (el IC de la parcial incluye 0). No define el caso intermedio: |ρ| < 0,5 con el IC de la parcial excluyendo 0.
Es justo el caso de la regla `nearest` (ρ = −0,016; IC de la parcial −0,280 a −0,047). El código congelado antes de
los datos (`geovida.p3`) lo clasifica como «no apoyada», porque todo lo que no es «apoyada» y es calculable recibe
esa etiqueta. Se transcribe ese veredicto y se declara la laguna. **El veredicto final no cambia:** con cualquier
etiqueta para ese caso, las dos reglas siguen dando veredictos distintos y H-P3b sigue siendo no interpretable.

## 4. Descriptivos (no son veredictos)

τ y certificado por grupo (regla principal, `results/p3/confirmatorio.units.csv`) [HV]:

| Grupo | Unidades | τ mediana (mín.–máx.) | Mediana de `p` del certificado (mín.–máx.) |
|---|---|---|---|
| Delgada | 18 | 0,405 (0,107–0,574) | 0,9997 (0,892–0,99999) |
| Compacta | 18 | 0,320 (0,077–0,544) | 0,999999 (0,99999–1,0) |

* **El certificado está casi saturado en estos datos [HV].** En 33 de las 36 unidades, la mediana de `p` es ≥ 0,99;
  el mínimo es 0,89. Los modelos de v0.4 (calibrados con fantomas, `otsu`, `realistic`, sin recalibrar, §5.7) juzgan
  adecuadas a casi todas las estructuras a 0,027 mm. La correlación de H-P3b se calcula, pues, sobre diferencias muy
  pequeñas de `p` [HV]. [HIP] Esto podría explicar que la correlación cambie tanto con la regla de etiquetas, pero esta
  prueba no lo puede comprobar.
* τ es moderada en los dos grupos (medianas 0,32 y 0,40): en el log-volumen de estas estructuras, la resolución y el
  segmentador pesan del orden de un tercio de la variación total entre especímenes y condiciones [HV, esta muestra].

## 5. H-P3c — acuerdo atlas frente a MEMOS (descriptivo; no es validación)

Ninguno de los dos segmentadores es una verdad anatómica (§6). Mediana entre estructuras de la mediana por
espécimen:

| Forma (D3/D5) | Estructuras | Dice | HD95 (mm) | ASSD (mm) | Dif. relativa de volumen |
|---|---|---|---|---|---|
| (a) sin trasladar | 48 | 0,75 | 0,26 | 0,19 | −0,02 |
| (b) con traslación (principal) | 48 | 0,75 | 0,24 | 0,18 | −0,02 |
| (b) sin los no rígidos (D5) | 48 | 0,77 | 0,21 | 0,18 | −0,02 |

* Con la forma (b), el Dice mediano es **0,85 en las estructuras compactas** y 0,64 en las delgadas [HV].
* D5 marca **14 de 60** especímenes como «desajuste no rígido» (dispersión > 4 vóxeles entre tercios): `0005`,
  `0029`, `0248`, `0280`, `0281`, `0290`, `0403`, `0432`, `0433`, `0434`, `0436`, `0437`, `0442`, `0449` (prefijo
  `IMPC_E15.5_`). Es un hallazgo sobre los archivos publicados; τ y el certificado no dependen de la colocación de la
  máscara (D3, D5).

## 6. Exploratorios y desviación posterior a la medida

* **Por sexo:** calculado (`results/p3/confirmatorio.sex.csv`); sin criterio, no se interpreta aquí.
* **D6 (21 nov 2026, registrada después de medir; solo afecta a un exploratorio) — MEMOS a ×4 no calculado.** El
  exploratorio de D2 (MEMOS otra vez sobre la imagen a ×4) falló en los 60 especímenes por un fallo del código: no se
  rellenaba la entrada hasta la ventana de 128 vóxeles, como hace MONAI. El fallo se corrigió y se probó contra MONAI
  (`scripts/p3_memos.py`, `tests/test_p3_memos.py`). El exploratorio se repetirá cuando haya memoria libre y se
  añadirá aquí como anexo. No toca τ, H-P3a, H-P3b ni H-P3c.

## 7. Predicciones escritas de antemano (§8)

| Predicción | Probabilidad escrita | ¿Ocurrió? |
|---|---|---|
| Las comprobaciones previas se superan | 60 % | Sí (3.1, 3.2 y 3.4 superadas; 3.3 como limitación declarada) |
| H-P3a apoyada | 70 % | Sí |
| H-P3b apoyada | 35 % | No: no interpretable (D1) |
| Dice atlas–MEMOS mediano ≥ 0,80 en las estructuras grandes | 75 % | Sí (0,85 en las compactas, forma b) |

## 8. Qué significa y qué no

* **Se sostiene [HV, esta muestra]:** en embriones E15.5 silvestres C57BL/6N de un escáner, la parte técnica
  (resolución simulada y segmentador) de la variación del log-volumen es mayor en las estructuras pequeñas o
  delgadas. Es lo que anticipaban los estudios sintéticos H1 y H3 [EI].
* **No se sostiene ni se refuta:** que el certificado de geovida anticipe esa fracción técnica mejor que el tamaño.
  MORPHO-TRACE no puede apoyarse en este resultado.
* **No se puede concluir** (§9): nada sobre exactitud anatómica (no hay referencia manual por espécimen); nada sobre
  otros estadios, cepas, modalidades o especies; la degradación de resolución es simulada sobre máscaras; nada humano
  ni clínico.

## 9. Siguiente paso

Según §7, se informa tal cual. Cualquier nueva prueba del certificado necesita un preregistro nuevo; esta muestra
ya no puede decidirla. Ideas, **sin decidir** [PROP]:

* Probar el certificado con etiquetas sin interpolar, para que no haga falta la regla de D1. Por ejemplo, propagando
  de nuevo el atlas con vecino más cercano; requiere las transformaciones de MusMorph [PV].
* Antes de volver a probar H-P3b, estudiar la saturación de `p` a esta resolución, con fantomas nuevos y nunca con
  estos especímenes.

## 10. Archivos (fuera de git)

`results/p3/confirmatorio.json` (resumen), `.units.csv`, `.tau.csv`, `.conditions.csv`, `.conditions_exact.csv`,
`.mixed.csv`, `.agreement.csv`, `.agreement_summary.csv`, `.sex.csv`, `.exploratory.csv` e
`informe_confirmatorio.md` (salida de `p3_report.py`). Del anexo ×4: `confirmatorio.x4.json`, `.conditions_x4.csv` y
`.tau_x4.csv`.

## 11. Anexo (21 nov 2026) — exploratorio MEMOS a ×4 (D2, D6)

> Exploratorio sin criterio. No cambia τ, H-P3a, H-P3b, H-P3c ni ningún veredicto. Calculado con
> `p3_analyze.py x4`, que reutiliza las tablas de la pasada principal y no escribe en el resumen confirmatorio.

**Qué se hizo [HV].** Se volvió a ejecutar MEMOS sobre la imagen nativa reducida a ×4 (≈ 0,108 mm; el doble de la
escala con la que se entrenó, D2) en los 60 especímenes, con el fallo de D6 corregido. El segmentador A (atlas) se
toma tal cual de la pasada principal; solo cambia B. 49 115 s (unas 13,6 h). El SHA-256 de
`results/p3/confirmatorio.json` es el mismo antes y después: el resumen confirmatorio no se tocó.

**Resultado [HV]:**

| | Pasada principal (B = MEMOS a ×2) | Exploratorio (B = MEMOS a ×4) |
|---|---|---|
| Filas de B con volumen 0 | 64 de 8640 (0,7 %) | 2030 de 8640 (23,5 %) |
| Volumen de B a ×1, mediana entre estructuras, relativo a la pasada principal | 1 | 0,11 |
| Especímenes descartados por estructura (mediana; máx.) | 0; 3 | 9,5; 60 |
| Estructuras con τ calculable | 48 | 47 (la etiqueta 25 queda vacía en los 60) |
| τ del log-volumen, mediana entre estructuras | 0,37 | 0,83 |
| τ mediana por grupo: compacta / delgada | 0,32 / 0,40 | 0,84 / 0,69 |
| Concordancia del orden por τ con la pasada principal | — | ρ = −0,21 en 47 estructuras (discrepa) |

**Lectura:**

* **MEMOS falla fuera de su escala de entrenamiento [HV].** A ×4, MEMOS deja vacías casi una cuarta parte de las
  máscaras y, en la estructura mediana, recupera el 11 % del volumen de la pasada principal. En 8 estructuras más de
  la mitad de las máscaras salen vacías.
* **Por eso τ sube y el orden se invierte.** La parte «técnica» crece porque el segmentador B deja de funcionar,
  no porque la resolución pese más en la anatomía. Que las compactas queden por encima de las delgadas en este
  exploratorio no dice nada contra H-P3a. **No se interpreta** [HV sobre las cifras; la causa es la escala, EI].
* **Qué sí confirma.** La decisión de D2 de ejecutar MEMOS a la escala de su entrenamiento (×2 sobre la nativa) era
  necesaria: una escala más gruesa cambia el resultado por completo.
* **Lo que no se puede concluir:** nada sobre la exactitud de MEMOS a su escala; nada sobre otros segmentadores; las
  salidas de MEMOS se usan solo en local y no se publican (pesos con licencia no declarada).
