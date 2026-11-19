# Resultados — H11: el certificado congelado frente a ecografía 3D real de embrión de ratón (17 nov 2026)

> Transcripción de los veredictos de `docs/PREREGISTRO_H11.md` (§4, con las aclaraciones del 11 nov y la
> desviación D1 del 16 nov). **Nada se reinterpreta ni se reajusta.** Los números salen de
> `results/summary/h11_v04_verdicts.json` y `h11_v04_cases.csv` (fuera de git, como los datos) y del informe
> generado `results/h11/informe_h11.md` (`scripts/h11_report.py`).
> Etiquetas: [HV] hecho verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta ·
> [PV] pendiente de validación.
>
> **Solo investigación con un conjunto animal.** Una referencia dibujada por una persona no es la verdad: aquí
> se mide acuerdo. Nada de esto dice algo sobre ecografía obstétrica humana ni sobre uso clínico.

## 1. Qué se midió

| Elemento | Valor |
|---|---|
| Datos | Qiu et al. 2021, IEEE DataPort, DOI 10.21227/drmd-xq36, CC BY; parte `BV_body_segmentation` [HV] |
| Manifiesto | `manifiesto_qiu2021.csv`, SHA-256 `e0d2782a…c016dd` (el mismo fijado en D1) [HV] |
| Casos | 1188 filas = cuerpo 180 casos × 3 segmentadores + ventrículo 216 × 3; 213 embriones distintos (170 con cuerpo) [HV] |
| Calibración | Congelada de v0.4 (`src/geovida/frozen/h9_frozen.json`), perfil `realistic`, sin reajuste [HV] |
| Intervalos | Remuestreo de embriones, 2000 réplicas, semilla 20261126 [HV] |
| Ejecución | 16–17 nov 2026, caché reanudable por caso (`results/h11/cache_v04.jsonl`, sello `frozen=v04 profile=realistic`); Python 3.13.17, numpy 2.5.4, scipy 1.18.1, scikit-image 0.26.0, pandas 3.1.1, nibabel 5.5.0 [HV] |

**Procedencia del código.** `meta.git_commit` dice `unknown` porque la copia local no es un repositorio git.
Para no dejarlo sin respaldo, se compararon las huellas de blob de git de los 10 archivos que producen H11
(`h11.py`, `realdata.py`, `certificate.py`, `domain.py`, `budget.py`, `segment.py`, `measure.py`, `topology.py`,
`frozen/h9_frozen.json`, `scripts/run_h11.py`) con la rama `geovida/v0.1-desde-cero` en el commit `cefe264`:
**coinciden las 10** [HV]. Los del motor no cambian desde el 14 nov y `run_h11.py` desde el 16 nov a las 16:11,
antes de crearse la caché (16:12) [HV]. Es una comprobación posterior, no un sello registrado en la ejecución;
queda como mejora pendiente que `run_h11.py` guarde estas huellas cuando no hay git [PROP].

**Comprobación independiente de los veredictos.** Se recontaron desde `h11_v04_cases.csv`, sin usar
`h11.evaluate_h11`: 0 de 540 medidas de cuerpo dentro del dominio en los tres segmentadores; 0 verdes con
guardia; 540 verdes sin guardia (170 embriones), las 540 con |error| > 10 %; 19 verdes de topología en 19
embriones. Coincide con el JSON [HV].

## 2. Veredictos preregistrados

| Hipótesis | Criterio (§4) | Datos | Estimación | IC 95 % | Veredicto |
|---|---|---|---|---|---|
| **H11a** — la guardia rechaza lo que no se parece | Dentro del dominio ≤ 50 % en los tres segmentadores | global 0 %, otsu 0 %, smoothed_otsu 0 % | 3 de 3 | — | **apoyada** |
| **H11b** — la luz verde no falla demasiado (**primaria**) | Verdes con guardia y \|error\| > 10 % ≤ 10 %; evaluable con ≥ 30 verdes y ≥ 15 embriones | 0 verdes, 0 embriones | — | — | **no evaluable** |
| **H11c** — sin guardia, el semáforo de v0.3 falla | Verdes sin guardia y \|error\| > 10 % supera 10 % | 540 verdes, 170 embriones | 100 % | 100 % a 100 % | **apoyada** |
| **H11e** — topología del cuerpo | Verdes de topología con Betti distinto de la referencia ≤ 10 %; evaluable con ≥ 30 verdes | 19 verdes, 19 embriones | — | — | **no evaluable** |

Referencias de cuerpo con Betti distinto de (1, 0, 0): **95,9 %** [HV]. El contorno manual casi nunca es un
sólido simple, como ya se veía en el caso mostrado en la exposición (β = (1, 11, 1)).

Por la regla final de §4, «no evaluable» no es «no apoyada»: **la hipótesis primaria no se apoya ni se refuta.**

## 3. H11d — acuerdo con la referencia (descriptivo, sin criterio)

| Segmentador | Estructura | n | Dice mediano (mín–máx) | \|error de volumen\| mediano | ≤ 10 % | ≤ 5 % |
|---|---|---|---|---|---|---|
| global | cuerpo | 180 | 0,20 (0,04–0,44) | 735 % | 0 % | 0 % |
| otsu | cuerpo | 180 | 0,30 (0,02–0,61) | 278 % | 0 % | 0 % |
| smoothed_otsu | cuerpo | 180 | 0,31 (0,02–0,62) | 286 % | 0 % | 0 % |
| global | ventrículo (caja) | 216 | 0,03 (0,00–0,09) | 3625 % | 0 % | 0 % |
| otsu | ventrículo (caja) | 216 | 0,00 (0,00–0,03) | 2133 % | 0 % | 0 % |
| smoothed_otsu | ventrículo (caja) | 216 | 0,00 (0,00–0,03) | 2213 % | 0 % | 0 % |

Ningún caso de cuerpo queda dentro del 10 % de la referencia con ningún segmentador; el menor error es
58 % (otsu) [HV]. Los segmentadores de umbral sobrestiman el volumen: el moteado de la ecografía cae por
encima del umbral fuera del embrión. El ventrículo, aun con la caja alrededor de la referencia que favorece al
método (§3), no se segmenta.

## 4. Predicciones escritas de antemano

| Predicción (§5) | Probabilidad asignada | Resultado |
|---|---|---|
| H11a apoyada | 70 % | Ocurrió |
| H11b evaluable (≥ 30 verdes y ≥ 15 embriones) | 35 % | No ocurrió (0 verdes) |
| H11b apoyada, dado que es evaluable | 55 % | No aplica |
| H11c apoyada, dado que es evaluable | 60 % | Ocurrió |
| Dice mediano del cuerpo con el mejor segmentador ≥ 0,90 | 55 % | No ocurrió (0,31) |

La predicción sobre el Dice fue claramente optimista: se esperaba que el contraste cuerpo-líquido amniótico
bastara para un umbral, y no basta [HV].

## 5. Qué significa (según §1 y §6 del preregistro)

1. **El certificado se negó cuando debía [HV].** Ninguna de las 1188 medidas recibió luz verde de volumen con
   la guardia: todas quedaron en amarillo. El preregistro lo anticipaba como «un resultado honesto y útil».
2. **Sin la guardia, el semáforo habría engañado siempre [HV].** Las 540 medidas de cuerpo habrían salido en
   verde (p ≥ 0,999 en todas) y todas con error > 10 %, la mayoría de varios
   cientos por ciento. Es la evidencia real más fuerte del proyecto a favor de la guardia de dominio, y repite
   con datos reales lo que H10 mostró en sintético.
3. **La pregunta primaria queda abierta [HV].** Sin luces verdes no se puede saber si una verde acertaría con
   ecografía real. Eso no es un fallo del certificado, pero tampoco una validación.
4. **La guardia, tal como está, no distingue grados [EI].** Con la guardia todo cae en amarillo; ninguna medida
   salió en rojo pese a errores de 3000 %. La guardia impide el verde, pero no avisa de que la medida es
   inservible. Es una observación sobre el diseño de v0.4, no un criterio del preregistro [PROP: estudiarlo en
   una versión nueva con su propio preregistro, nunca reajustando H11].
5. **Lo que se aprende para seguir (§6).** Hace falta un simulador de ecografía (moteado, atenuación) y una
   calibración con datos reales validada por embrión: la ruta de H12 y H12R, que se mide en la misma cadena con
   la calibración de ecografía simulada (`--frozen h12_frozen.json`) y se publicará aparte, según
   `docs/PREREGISTRO_H12R.md`.

## 6. Qué no se puede concluir

- Que el certificado funcione con ecografía real: no hubo verdes que evaluar.
- Que los segmentadores de geovida sirvan para ecografía: no sirven en este conjunto; nunca se diseñaron para ella.
- Nada sobre humanos, obstetricia ni uso clínico.
- Error exacto: la referencia es un trazado humano (y el 95,9 % no es un sólido simple).

## 7. Pendiente

- ~~**Sensibilidad de vóxel**~~ hecha el 19 nov (`docs/h11/RESULTADOS_H12R.md` §5): no cambia H11a, H11b ni H11c;
  H11e pasa a «no apoyada» en la sensibilidad (49 verdes de topología, todas erróneas). El veredicto principal de
  H11e sigue siendo «no evaluable».
- ~~**H12R**~~ cerrado el 19 nov (`docs/h11/RESULTADOS_H12R.md`): primaria no evaluable.
- ~~Registrar en `run_h11.py` las huellas del código cuando no hay git~~ hecho el 17 nov:
  `geovida.provenance.code_fingerprint` y `compare_fingerprint`, guardadas en `meta.code_fingerprint`
  (`tests/test_code_fingerprint.py`). Las corridas de H11 ya hechas no se repiten; la comprobación de §1 sigue siendo la suya.
