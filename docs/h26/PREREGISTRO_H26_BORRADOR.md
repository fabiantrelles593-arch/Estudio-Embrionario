# H26 (BORRADOR): replicación con un segundo conjunto de volúmenes

> **Estado: borrador aprobado como base por el autor el 26 nov 2026. No es el preregistro final.** Se prepara antes de tener datos para que, si llegan, el preregistro pueda
> completarse y subirse antes de abrir ningún volumen. Los huecos marcados **[POR COMPLETAR]** dependen de los datos
> recibidos. Se sube a la rama como base fechada, para que conste que el diseño es anterior a los datos. No se mide
> nada hasta que:
>
> 1. lleguen los datos con una licencia o unas condiciones de uso por escrito;
> 2. se rellenen los huecos;
> 3. el autor apruebe el texto final.
>
> **Datos previstos:** volúmenes de ecografía 3D de alta frecuencia de embriones de ratón con segmentación manual, no
> incluidos en la publicación de Qiu et al. 2021 (IEEE DataPort, doi:10.21227/drmd-xq36). Se pidieron al grupo de NYU
> (`docs/h20/CANDIDATOS_REPLICACION.md`, camino A). Nada humano ni clínico.
>
> **Etiquetas:** [HV] verificado · [HIP] hipótesis · [PROP] propuesta.

## 1. Pregunta

Con el instrumento **congelado tal como está**, sin reentrenar ni recalibrar nada, en embriones que ninguna parte del
proyecto ha visto:

- **R1b (cuerpo):** ¿sigue siendo segura la luz verde de H20?
- **R1d (cuerpo):** ¿fallan más los casos no verdes que los verdes?
- **V1b y V1d (ventrículos):** las mismas preguntas con la luz de H25, solo si los volúmenes traen segmentación de
  ventrículo.

Es la replicación directa que pedían H20, H25 y la síntesis: misma estructura y modalidad, embriones nuevos.

## 2. Lo que ya se ha visto (declarado)

- **Del conjunto nuevo: nada.** Ningún volumen se ha abierto.
- Del conjunto público se conocen todos los resultados de H11–H25. El instrumento se congeló con él (§4).
- Sabemos por H25 que en el conjunto público la red casi no falla. Si el conjunto nuevo se parece, R1d y V1d pueden
  acabar «no evaluables» por S-1 (§8).

## 3. Datos

**G0-datos (antes de abrir ninguna imagen; solo metadatos y licencia):**

1. Licencia o condiciones de uso por escrito, que permitan este análisis y digan qué se puede publicar
   (resultados agregados, nunca los volúmenes). **[POR COMPLETAR: texto o referencia]**
2. Solo datos animales; ningún dato humano.
3. **Sin solapamiento** con la publicación pública: se comparan identificadores de embrión, fechas y la huella SHA-256
   de cada archivo con los 180 casos públicos. Un volumen que coincida se excluye y se informa.
4. Hay segmentación manual de cuerpo (y de ventrículo, si la hay) para cada volumen usado, hecha sin ver las salidas de
   nuestras redes.
5. Formato y tamaño de vóxel legibles por `geovida.realdata`. **[POR COMPLETAR: formato, tamaño de vóxel, equipo y
   frecuencia]**
6. Recuento: N volúmenes en E embriones. **[POR COMPLETAR]** Si un embrión tiene varios volúmenes, todos cuentan y el
   remuestreo es por embrión.

Si falla un punto, se para y se documenta. Ningún volumen se abre.

**Reparto:** todos los volúmenes que pasen G0-datos son **prueba**. No hay calibración ni ajuste: el instrumento no
cambia (§4). Por eso no hace falta reservar casos para ajustar nada.

## 4. Instrumento congelado (sin cambios)

| Parte | Qué | Huella |
|---|---|---|
| Cuerpo: redes | Las de H19 (`results/h19/coarse.pt` y `fine.pt`) | SHA-256 en `results/h19/calibrate.json` |
| Cuerpo: regla, guardia y envolvente | El congelado de H20 (`results/h20/h20_frozen.json`) | `66d7ffcf3d9d8397aeefe208aa480deb870d6b616c5cc01c24f8abae7250804e` |
| Ventrículos: redes | Las de H23 | `fa7f5211…0038` (gruesa) y `fc3f4dfd…f9cf2` (fina) |
| Ventrículos: regla, guardia y envolvente | El congelado de H25 (`results/h25/h25_frozen.json`) | `91ba4f3dcff06281934e9e07207581db8b8e3c91167202869ac79c9737322f76` |

La orden `test` se niega a correr si alguna huella no coincide.

**Declarado:** la guardia de cuerpo es la de H20, con el contraste con signo, porque así se congeló. En el conjunto
público el contraste del cuerpo fue positivo en 43 de 44 casos de prueba. Si con otro equipo no lo es, esos casos
saldrán fuera de dominio (amarillos). No se corrige: se informa (§7, R1e).

**Riesgo declarado [HIP]:** si el conjunto nuevo tiene otro tamaño de vóxel, otro equipo u otra ganancia, la guardia
puede dejar fuera muchos casos. Eso es parte de lo que se replica: el instrumento debe negarse a dar verde fuera de su
dominio.

## 5. Orden de ejecución

`scripts/run_h26.py` y `src/geovida/h26.py`, con sus pruebas en `tests/test_h26.py`. Están escritos para el formato
del conjunto público; si los datos nuevos llegan en otro formato, solo cambia la lectura, y el cambio se sube con el
preregistro final y con el CI en verde antes de abrir ningún volumen:

1. `check`: huellas de §4 y umbrales del código iguales a los congelados.
2. `g0-datos`: los puntos de §3 que se comprueban con archivos: columnas, archivos presentes, huella del documento de
   condiciones de uso y solapamiento con el conjunto público (por huella SHA-256 de cada imagen y por embrión).
3. `g0`: en 5 volúmenes de cuerpo elegidos con la semilla 20261128, **solo imagen, sin leer la referencia**: señales
   calculables y como mucho 300 s por caso. No ajusta nada; los 5 siguen en la prueba.
4. `test`: una sola vez, sobre todos los volúmenes. Lee las referencias por primera vez. Deja un candado al empezar y
   se niega a empezar otra vez.

Además, `replay-public` rehace la evaluación de H20 y H25 desde sus filas ya medidas, sin calcular ninguna red, y
comprueba que R1b y V1b dan exactamente los veredictos publicados de H20b y H25b.

## 6. Hipótesis y criterios

Remuestreo por embrión, 2000 réplicas, semilla 20261120, IC 95 % por percentiles (S-3 de `docs/REGLAS_PREREGISTRO.md`).

**Primaria 1, R1b (cuerpo).** El criterio de H20b sin cambios: fracción de verdes con |error de volumen| > 10 %.
Apoyada si la estimación es ≤ 10 %; no apoyada si el límite inferior es > 10 %; si no, no concluyente. **Evaluable con
≥ 20 verdes en ≥ 15 embriones.**

**Primaria 2, R1d (cuerpo).** Δ = fallos entre no verdes − fallos entre verdes. Separa si el límite inferior es > 0;
no separa si el superior es ≤ 0,05; si no, no concluyente. **Evaluable (S-1) con ≥ 5 verdes, ≥ 5 no verdes, ≥ 10
fallos en total y ≥ 1 fallo en cada grupo.**

**Confirmatorias de ventrículo (solo si hay referencia de ventrículo):** V1b y V1d, con la luz y la tolerancia de H25
(fallo: e_b > 0,5 vóxeles) y los mismos criterios y mínimos que R1b y R1d. Se informan aparte; el resumen del estudio
lo da el cuerpo.

Un valor no calculable es «no evaluable», nunca «no apoyada».

## 7. Secundarias (descriptivas)

- R1a / V1a: luces (verdes, amarillas, rojas).
- R1c / V1c: exactitud de la red en el conjunto nuevo (|error| mediano, fracción a ≤ 10 %, Dice; e_b para
  ventrículo).
- R1e / V1e: fracción dentro del dominio; verdes sin guardia y cuántas fallan; casos con contraste no positivo.
- R1g / V1g: fallo de «dar verde a todo».

## 8. Qué permite cada tamaño (escrito antes de conocerlo)

Con las tasas del conjunto público (cuerpo: unas 48 % de verdes y unos 7 % de fallos en la prueba de H20) y la nota de
tamaño muestral (`docs/h25/TAMANO_MUESTRAL_SEPARACION.md`):

| Volúmenes de cuerpo | R1b | R1d |
|---|---|---|
| < 40 | Probablemente no evaluable (< 20 verdes) | No evaluable por S-1 |
| 40–60 | Dudosa (unas 20–29 verdes) | No evaluable por S-1, salvo que la red falle mucho más |
| 60–150 | Probablemente evaluable | Evaluable solo si el fallo global es ≥ 7–10 % |
| > 150 | Evaluable | Evaluable por S-1; detectar Δ ≈ 10 puntos exige unos 270 casos, y Δ ≈ 20, unos 80–120 |

Si la guardia deja fuera muchos casos, las verdes bajan y R1b puede no ser evaluable aunque N sea grande.

Por S-2: si con el N real los fallos esperados son menos de 25, el preregistro final lo dirá, y dirá que lo más
probable para R1d es «no evaluable» o «no concluyente».

## 9. Predicciones (se completan con N antes de subir)

| Predicción | Probabilidad |
|---|---|
| Pasa G0-datos | **[POR COMPLETAR]** |
| R1b evaluable | **[POR COMPLETAR según N y §8]** |
| R1b apoyada, si evaluable | 60 % [HIP: como en H20, menos por el cambio de conjunto] |
| R1d evaluable | **[POR COMPLETAR según N y §8]** |
| R1d separa, si evaluable | 35 % [HIP: como H25d] |
| Fracción dentro del dominio < 50 % | **[POR COMPLETAR según el equipo]** |

## 10. Qué significará cada resultado

| Resultado | Conclusión | Siguiente paso |
|---|---|---|
| G0-datos no superado | No hay datos utilizables o la licencia no lo permite | Documentarlo; no se abre nada |
| R1b apoyada | La luz verde de H20 se sostiene en embriones de otro lote: primera replicación de la línea | Publicable junto con H20, con sus límites |
| R1b no apoyada | La luz no transfiere al conjunto nuevo | Publicarlo; estudiar las verdes que fallan |
| R1b no evaluable | Pocas verdes (pocos casos o guardia muy estricta) | Informar R1e: si es la guardia, es el freno funcionando |
| R1d separa | Primera evidencia de que la luz distingue aciertos de fallos | Replicar antes de afirmar algo general |
| R1d no separa | La luz es segura pero no informa más que dar verde a todo | Mirar R1g |
| R1d no evaluable / no concluyente | Pocos fallos | Lo previsto en §8; ninguna conclusión sobre la separación |

En todos los casos, el conjunto nuevo queda usado como prueba de H26.

## 11. Qué no se puede concluir

- Nada sobre otras especies, humanos, obstetricia ni uso clínico.
- Si los datos vienen del mismo grupo y del mismo equipo, es una replicación de lote, no de equipo.
- Los umbrales siguen siendo los fijados en H20 y H25; no se prueba si otros irían mejor.

## 12. Desviaciones

(Ninguna: borrador.)

**Aprobación como base (26 nov 2026).** El autor aprueba este texto como base. Cualquier cambio entre esta base y el
preregistro final, salvo rellenar los huecos [POR COMPLETAR], se anotará aquí con fecha y motivo.

**Cambio 1 (26 nov 2026): código escrito antes de tener datos.** §5 decía «por escribir cuando se conozca el formato».
Se escribió ya para el formato del conjunto público, para no retrasar el estudio cuando lleguen los datos. No cambia
ninguna regla, umbral ni criterio. Comprobaciones hechas sin datos nuevos:

- `check`: congelados y redes con las huellas de §4.
- `replay-public`: R1b reproduce exactamente H20b y V1b reproduce exactamente H25b. Con S-1, la separación de H20 y
  la de H25 habrían sido «no evaluables» (menos de 10 fallos), como se esperaba.
- `g0-datos` con 4 volúmenes públicos presentados como nuevos: los 4 se excluyen por huella y por embrión, y G0-datos
  no se supera.

Se fija la semilla de `g0` (20261128).
