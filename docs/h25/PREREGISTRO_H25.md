# Preregistro H25: la luz de H24 con una guardia de dominio que no depende del signo del contraste (ventrículos)

**Versión 1.0, 26 nov 2026. Aprobada por el autor tal como estaba escrita el 26 nov 2026.** Se sube a la rama, con su
código y sus pruebas, antes de calcular ninguna luz con la guardia nueva.

Código previsto: `src/geovida/h25.py` y `scripts/run_h25.py`. Pruebas: `tests/test_h25.py`.

> **De dónde viene.** H24 se cerró como no evaluable: 3 verdes de 34 en calibración, porque la guardia de dominio dejó
> dentro solo 5 de 34 casos [HV, `docs/h24/RESULTADOS_H24.md`]. Al revisar por qué, se encontró la causa exacta (§2):
> **en 27 de los 34 casos los dos índices de la guardia no se pueden calcular**, porque el ventrículo es más oscuro que
> el fondo lejano y `domain_observables` declara «no calculable» cualquier contraste ≤ 0. Un índice no calculable cuenta
> como fuera del dominio. La guardia no juzgó esos casos como raros: **no llegó a medirlos**.
>
> **Qué cambia y qué no.** Solo cambia la guardia: usa el valor absoluto del contraste. Las redes, la tolerancia, las
> señales, la regla, las puertas y los criterios son los de H24, sin tocar un número.
>
> **Por qué no es evidencia limpia en calibración.** H25 nace después de ver toda la calibración de H23 y de H24,
> incluido que, sin guardia, salen 19 verdes con 1 fallo. **La calibración ya no frena nada en serio. La única evidencia
> es la prueba de ventrículo, que sigue intacta.**
>
> **Etiquetas:** [HV] verificado · [HIP] hipótesis · [PROP] propuesta.
>
> **Datos:** solo datos animales publicados (Qiu et al. 2021, IEEE DataPort, doi:10.21227/drmd-xq36, CC BY). Nada
> humano ni clínico.

## 1. Pregunta

Las dos preguntas de H24, sin cambios, con una guardia que puede medir estructuras más oscuras que su entorno:

1. ¿Una luz verde basada solo en la estabilidad de la red acierta en ventrículos nuevos (fallo: e_b > 0,5 vóxeles)?
2. ¿Los casos no verdes fallan más que los verdes?

## 2. Lo que ya se ha visto (declarado)

- **Calibración de ventrículo (34 casos de 33 embriones).** Todo lo de H23 y H24 caso a caso:
  - error relativo, e_b, Dice, s_flip, s_stage, b_flip, b_stage, luces con y sin guardia;
  - agregados publicados: 29 de 34 con e_b ≤ 0,5; 19 verdes sin guardia, de las que falla 1; 4 fallos entre las 15 no
    verdes; 3 verdes con la guardia de H23.
- **Diagnóstico de la guardia (26 nov 2026, después de cerrar H24, solo calibración).**
  - En los resultados de H24, `snr_hat` y `edge_width` son NaN en **27 de 34** casos [HV, `results/h24/cal_rows.jsonl`].
  - Con las máscaras de referencia de esos mismos 34 casos se recalculó el contraste de la guardia (media dentro −
    mediana del fondo a más de 3 vóxeles): **≤ 0 en 27 de 34**, mediana −0,14 (mín. −43,4; máx. 29,5). El anillo
    inmediato al ventrículo (tejido cerebral) es más brillante que el ventrículo y que el fondo lejano [HV, diagnóstico
    local del 26 nov 2026, fuera de git].
  - No se calculó ninguna luz, envolvente ni admisión con la guardia nueva.
- **Etiquetas de ajuste (142 casos).** Usadas en H24 para la factibilidad.
- **Prueba de ventrículo (40 casos de 40 embriones). Intacta:** ninguna red de ventrículo la ha procesado y no se ha
  calculado en ella ninguna señal ni índice de guardia. Son imágenes de los 40 embriones de prueba de cuerpo de H20; el
  resultado de cuerpo se conoce y no se usa.
- **Sobre la regla del §9 de H24** («no habrá H25 sobre esta misma prueba»): esa fila era para el caso en que la prueba
  se hubiera usado. En H24 no se abrió, así que H25 puede usarla. **H25 la abre como mucho una vez, y después ningún
  estudio de ventrículo vuelve a decidir con ella**, salga lo que salga.

## 3. Datos, repartos y segmentador (los de H24, sin cambios)

- Manifiesto `results/h11/manifiesto_qiu2021.csv`, estructura `ventricle`; repartos de H23 (semilla 20261121): ajuste 142
  casos, calibración 34 casos de 33 embriones, prueba 40 casos de 40 embriones. Vóxel isotrópico de 0,05 mm.
- Redes de H23 congeladas por SHA-256, medidas con `h23.segment_all` y `h23.coarse_volume_all`:

| Red | Archivo (fuera de git) | SHA-256 |
|---|---|---|
| Etapa 1 | `results/h23/coarse.pt` | `fa7f52117ab5dab3a7918eb53c89b56228c6a71e5931dd57e729436a0ba90038` |
| Etapa 2 | `results/h23/fine.pt` | `fc3f4dfdf9170ea6113acc457d05c389f1fe699ec7479bb66b4299dd92be9cf2` |

## 4. Error, señales y regla (los de H24 §5.1–§5.3, sin cambios)

- e_b = |V_M − V_R| / A_R; fallo si e_b > 0,5 vóxeles.
- b_flip = (máx − mín de los 8 volteos) / A_M; b_stage = |V_c − V_0| / A_M.
- Verde: dentro del dominio y b_flip ≤ 0,25 y b_stage ≤ 0,50. Rojo: b_flip > 1,0 o b_stage > 1,5. Amarillo: el resto.

Se reutiliza `geovida.h24` tal cual para todo esto.

## 5. La guardia revisada (el único cambio)

### 5.1. Definición

Los mismos dos índices de `geovida.domain.domain_observables`, con un único cambio: **el contraste se toma en valor
absoluto.**

| | Guardia de H23/H24 | Guardia de H25 |
|---|---|---|
| Contraste C | media dentro − mediana del fondo lejano | igual |
| No calculable si | C ≤ 0 | **C = 0** (o lo demás de antes: máscara vacía, < 30 vóxeles de fondo) |
| `snr_hat` | C / σ_fondo | **\|C\| / σ_fondo** |
| `edge_width` | vóxeles del borde con (I − fondo)/C entre 0,25 y 0,75, por área | igual: con C negativo, el cociente sigue midiendo la transición de 0 a 1 |
| Envolvente | 1 %–99 %; 5 pliegues por embrión en calibración; los 34 casos para la prueba | igual |

`domain.py` no se toca, para que los estudios anteriores sigan siendo reproducibles. La versión nueva vive en `h25.py`.

### 5.2. Por qué este cambio y no otro (criterio fijado por principio)

- **Es la corrección mínima.** Donde la guardia antigua estaba definida (C > 0), la nueva da exactamente los mismos
  valores. Solo cambia algo en los casos donde la antigua no medía nada. Lo comprueba una prueba automática. En cuerpo,
  la guardia estaba definida en los 27 casos de calibración de H19 y en 43 de los 44 de prueba de H20 [HV,
  `results/h19/cal_rows.jsonl`, `results/h20/test_rows.jsonl`]; el caso restante no se revisa, porque H20 está cerrado
  y no se reinterpreta.
- **El principio:** una alarma de calidad de imagen no debe depender de si la estructura es más clara o más oscura que
  su entorno. La guardia se diseñó en v0.4 con estructuras sintéticas brillantes y nunca se pensó para una cavidad
  llena de líquido.
- **No se elige mirando cuántos casos admite.** No se ha calculado la admisión con la guardia nueva (§2).

**Alternativa descartada: fondo local** (un anillo de 1 a 3 vóxeles alrededor de la máscara en lugar del fondo lejano).
Para una estructura interna probablemente tiene más sentido. Pero sería una guardia nueva, que nunca se validó (H10b
validó la del fondo lejano en sintético), y habría que elegir el grosor del anillo sabiendo ya cómo son estas imágenes.
Queda como propuesta [PROP] para otro conjunto.

### 5.3. Limitación declarada de antemano [HIP]

En ventrículo, el contraste frente al fondo lejano es casi nulo (mediana −0,14). Con `snr_hat` alrededor de 0,5, la
guardia nueva **apenas medirá calidad de imagen**. Lo esperable es que admita la mayoría de los casos y actúe casi como
«sin guardia». H25 es, por tanto, sobre todo una prueba de las señales en vóxeles de borde, con una guardia débil. Se
dirá así en los resultados, salga lo que salga.

## 6. Orden, puertas y candado

`scripts/run_h25.py`, en este orden:

1. `check`: huellas SHA-256 de §3.
2. `g0`: en 5 casos de ajuste (semilla 20261126):
   - señales calculables;
   - la pasada sin voltear reproduce `h23.segment_all`;
   - la guardia nueva es calculable;
   - en un caso con C > 0, coincide exactamente con la antigua;
   - cada caso tarda ≤ 300 s.
3. `calibrate`: los 34 casos, luces fuera de pliegue con la guardia nueva.
4. SHA-256 del congelado al §11 de este documento y a la rama.
5. `test --sha`: los 40 casos de prueba, una sola vez.

**Comprobación de factibilidad (la que faltó en H24).** Sin guardia, la calibración da 19 verdes [HV, H24]. La puerta C′
pide 10. Por tanto **la puerta es alcanzable**: basta con que la guardia nueva admita 10 de esas 19.

**Puerta S′ (calibración, no independiente):** ≥ 50 % de los 34 con e_b ≤ 0,5. Ya se sabe que pasa (29 de 34); se
mantiene como comprobación de que el código reproduce H24.

**Puerta C′ (calibración, no independiente):** ≥ 10 verdes, y como mucho el 10 % de ellas con e_b > 0,5.

Si falla una puerta, la prueba no se abre y H25 se publica como no evaluable. Si pasan, `calibrate` congela los
umbrales, la envolvente de los 34 casos y las huellas de las redes. `test` se niega a correr si algo no coincide.

## 7. Hipótesis y criterios (los de H24 §7, renombrados)

**Primaria 1, H25b.** Fracción de las verdes de prueba con e_b > 0,5; IC 95 % por remuestreo de embriones (2000
réplicas, semilla 20261120). Apoyada si la estimación ≤ 10 %; no apoyada si el límite inferior > 10 %; si no, no
concluyente. **Evaluable con ≥ 20 verdes en ≥ 15 embriones.**

**Primaria 2, H25d (separación).** Δ = fallos entre no verdes − fallos entre verdes; mismo IC. Separa si el límite
inferior > 0; no separa si el límite superior ≤ 0,05; si no, no concluyente. **Evaluable con ≥ 5 verdes y ≥ 5 no
verdes.**

Las dos se informan juntas y sin corregir por multiplicidad.

**Secundarias (prueba, descriptivas):**
- H25a: cobertura (fracción verde y luces).
- H25c: e_b mediana, fracción ≤ 0,5 y ≤ 0,25, Dice mediano y fracción a ≤ 10 % de volumen.
- H25e: admisión de la guardia nueva; verdes sin guardia y cuántas fallan.
- H25g: tasa de fallo en todos los casos (la de «dar verde a todo»).
- **H25h (nueva, descriptiva):** luces de prueba con la guardia antigua, para ver cuánto cambia la guardia.

Sin exploratoria de cuerpo: H24f no aporta a esta pregunta.

Los mínimos (20 verdes en 15 embriones; 5 y 5) son los heredados de H18 y H23. **No se bajan**, aunque eso haga probable
que H25b no sea evaluable (§8).

## 8. Predicciones escritas de antemano

Son subjetivas y se escriben sabiendo todo lo de §2.

| Predicción | Probabilidad |
|---|---|
| Pasa G0 | 95 % |
| Pasa S′ | 99 % |
| Pasa C′, dado S′ | 80 % |
| H25b evaluable (≥ 20 verdes de 40 en ≥ 15 embriones), dado que se abre la prueba | 40 % |
| H25b apoyada, dado que es evaluable | 70 % |
| H25d evaluable, dado que se abre la prueba | 90 % |
| H25d separa, dado que es evaluable | 35 % |

*Por qué H25b será probablemente no evaluable [HIP].* En calibración, el 56 % de los casos (19 de 34) da verde sin
guardia. Con 40 casos de prueba eso son unas 22 verdes, y la guardia quitará algunas. Llegar a 20 es aproximadamente
una moneda al aire, o algo menos.

*Por qué H25d separará con poca probabilidad [HIP].* En calibración, Δ descriptivo ≈ 27 % − 5 % = 22 puntos, pero con
40 casos y pocos fallos (5 de 34 en calibración) el IC será ancho.

## 9. Qué significará cada resultado (antes de verlo)

| Resultado | Conclusión | Siguiente paso |
|---|---|---|
| G0 no superada | Fallo de implementación | Corregir y documentar como desviación; no se toca la regla |
| C′ no superada | Ni con la guardia corregida hay verdes suficientes | Publicarlo; la prueba sigue intacta para un estudio con otro diseño |
| H25b apoyada y H25d separa | Primera evidencia de la línea de que la luz distingue aciertos de fallos, en una estructura pequeña y con una guardia débil | Replicar en otro conjunto antes de afirmar nada general |
| H25b apoyada y H25d no separa o no concluyente | La luz es segura, pero no se ha mostrado que informe más que dar verde a todo | Mirar H25g |
| H25b no apoyada | La red es estable también cuando desplaza el borde | Publicarlo; estudiar las verdes que fallan |
| H25b no evaluable | Pocas verdes en 40 casos | Informar H25d y las descriptivas. **La prueba queda usada** |

En todos los casos la prueba de ventrículo queda usada después de H25.

## 10. Qué no se puede concluir

- No es una replicación: mismo conjunto, mismo equipo, misma especie.
- La guardia se revisó después de ver la calibración; el criterio es de principio (§5.2), pero el momento no es neutro.
- Una guardia casi vacía en ventrículo (§5.3) no dice nada sobre cómo se comportaría ante imágenes realmente distintas.
- e_b supone un desplazamiento uniforme del borde; los errores que se compensan quedan ocultos (se informa el Dice).
- La variabilidad entre anotadores de la referencia no se conoce; medio vóxel puede estar por debajo de ella.
- Nada sobre humanos, hidrocefalia, obstetricia ni uso clínico.

## 11. Desviaciones

(Ninguna al subir este preregistro.)

## Anexo: corrección a `RESULTADOS_H24.md` (se sube con este preregistro)

Los resultados de H24 atribuyen el rechazo de la guardia a una envolvente ajustada con pocos casos. La causa real es que
los índices no se pudieron calcular en 27 de 34 casos (§2). Se añadirá una nota fechada al final de
`docs/h24/RESULTADOS_H24.md` y a la síntesis, sin cambiar el veredicto de H24 ni ninguno de sus números.
