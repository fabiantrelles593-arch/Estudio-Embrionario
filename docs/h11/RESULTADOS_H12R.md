# Resultados — H12R: el certificado recalibrado con ecografía simulada frente a ecografía 3D real de ratón (19 nov 2026)

> Transcripción de los veredictos de `docs/PREREGISTRO_H12R.md` (§4 y la tabla de decisiones §5) y de la
> sensibilidad de vóxel de la desviación D1 de `docs/PREREGISTRO_H11.md`. **Nada se reinterpreta ni se reajusta.**
> Los números salen de `results/summary/h11_{h12,h12c,v04_rs,h12_rs}_verdicts.json` y `_cases.csv` (fuera de git,
> como los datos) y del informe generado `results/h11/informe_h11.md` (`scripts/h11_report.py`).
> Etiquetas: [HV] hecho verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta ·
> [PV] pendiente de validación.
>
> **Solo investigación con un conjunto animal.** Una referencia dibujada por una persona no es la verdad: aquí
> se mide acuerdo. Nada de esto dice algo sobre ecografía obstétrica humana ni sobre uso clínico.

## 1. Qué se midió

| Elemento | Valor |
|---|---|
| Datos | Qiu et al. 2021, IEEE DataPort, DOI 10.21227/drmd-xq36, CC BY; los mismos casos que H11 [HV] |
| Manifiesto principal | `manifiesto_qiu2021.csv`, SHA-256 `e0d2782a…` (el de H11) [HV] |
| Manifiesto de sensibilidad | `manifiesto_qiu2021_rs.csv`, SHA-256 `3504ae5b…`: los casos principales más 47 de cuerpo con otro vóxel en la cabecera de la etiqueta (D1) [HV] |
| Calibración | `h12_frozen.json`, SHA-256 `c5100049…dcdab1a0ceb`, sin reajuste. Perfil primario `us_raw` (§3); `us_compound` se publica pero no se puede elegir [HV] |
| Casos | Principal: 1188 filas (cuerpo 180 × 3 segmentadores + ventrículo 216 × 3), 213 embriones, 170 con cuerpo. Sensibilidad: 1329 filas, cuerpo 227 × 3, 213 embriones con cuerpo [HV] |
| Intervalos | Remuestreo de embriones, 2000 réplicas, semilla 20261126 [HV] |
| Ejecución | `h12` y `h12c`: 18–19 nov; `v04_rs` y `h12_rs`: 19 nov, con `--relaxed-spacing` [HV] |

**Procedencia del código [HV].** La copia local no es un repositorio git, así que cada corrida guardó su huella de
código (`meta.code_fingerprint`, blobs de git). Comparadas con la rama `geovida/v0.1-desde-cero`:

* `v04_rs` y `h12_rs`: coinciden los 111 archivos con la rama actual.
* `h12` y `h12c`: coinciden todos los archivos del motor salvo `h11.py` y `run_h11.py`, que son exactamente las
  versiones de los commits `ad3c043` y `c94123c`, las anteriores al arreglo de la sensibilidad (opción
  `relaxed_spacing`, desactivada por defecto). Las demás diferencias son archivos ajenos a H11 (`minc.py`,
  `atlas_effect.py`, `atlas_effect_gates.py`, `pyproject.toml`).

**Comprobación independiente [HV].** Se recontó todo desde las tablas por caso, sin usar `h11.evaluate_h11`, y
coincide con los JSON: con H12 `us_raw`, 0 de 540 medidas de cuerpo dentro del dominio; 0 verdes con guardia;
180 verdes sin guardia (todas de `smoothed_otsu`, 170 embriones), las 180 con |error| > 10 %; 0 verdes de topología.
El Dice y el error de volumen de cada caso son idénticos con las dos calibraciones (diferencia máxima 0): la
calibración solo cambia la luz, no la segmentación.

## 2. Veredictos preregistrados de H12R (perfil primario `us_raw`)

| Hipótesis | Criterio (§4) | Datos | Resultado | Veredicto |
|---|---|---|---|---|
| **H12Ra** — la guardia de H12 reconoce la imagen real | Con `smoothed_otsu`, dentro del dominio mayor con H12 que con v0.4 | v0.4 0 % → H12 0 % | No aumenta | **no apoyada** |
| **H12Rb** — la luz verde de H12 no falla demasiado (**primaria**) | Verdes con guardia y \|error\| > 10 % ≤ 10 %; evaluable con ≥ 30 verdes y ≥ 15 embriones | 0 verdes, 0 embriones | — | **no evaluable** |
| **H12Rc** — cobertura frente a v0.4 | Verdes de cuerpo con H12 menos con v0.4 (sin criterio de éxito) | 0 − 0 | 0 | descriptiva |
| **H12Rd** — acuerdo | Descriptiva, igual que H11d | Idéntico a H11d (§1) | Dice mediano del cuerpo: 0,20 / 0,30 / 0,31 | descriptiva |

Las hipótesis heredadas de H11 con la calibración H12 `us_raw`: H11a **apoyada** (0 % dentro del dominio en los tres
segmentadores), H11c **apoyada** (180 de 180 verdes sin guardia con error > 10 %), H11e **no evaluable** (0 verdes de
topología).

**Perfil `us_compound` (publicado, no elegible) [HV].** Los mismos veredictos: H11a apoyada, H11b no evaluable, H11c
apoyada (180 de 180), H11e no evaluable.

## 3. Consecuencia según la tabla §5 (decidida de antemano)

H12Rb es **no evaluable**. La fila correspondiente de §5 dice:

* **Qué se concluye:** el simulador de ecografía de H12 no cubre aún la ecografía real de alta frecuencia. La
  guardia hizo su trabajo: se negó.
* **Siguiente paso:** calibrar con los propios volúmenes reales, validando **por embrión** (nunca dos cortes del
  mismo embrión a ambos lados de la división). Es otra hipótesis, con su propio preregistro [PROP].

## 4. Lo que cambia respecto de v0.4: aparece el rojo [HV, descriptivo]

Con v0.4 (H11), las 540 medidas de cuerpo quedaron en amarillo. Con H12 `us_raw`:

| Segmentador | Rojo | Amarillo | Verde |
|---|---|---|---|
| global | 180 | 0 | 0 |
| otsu | 175 | 5 | 0 |
| smoothed_otsu | 0 | 180 | 0 |

Con `us_compound`: global 180 rojo; otsu 97 rojo y 83 amarillo; smoothed_otsu 180 amarillo.

La calibración de H12 marca como inservibles (rojo) las medidas de `global` y casi todas las de `otsu`, que en la
simulación de ecografía nunca alcanzan verde (§2 del preregistro). Esto toca la observación 4 de
`RESULTADOS_H11.md` (con v0.4 la guardia no distinguía grados) [EI]. No es un criterio de H12R y no responde a esa
observación: `smoothed_otsu` sigue en amarillo con errores de varios cientos por ciento, y sin la guardia las 180 habrían
salido en verde. La propuesta P2 (distinguir «fuera de dominio» de «inservible») sigue en pie [PROP].

## 5. Sensibilidad de vóxel (desviación D1 de H11)

Se añaden 47 casos de cuerpo cuya etiqueta tiene la misma forma que la imagen pero otro vóxel en la cabecera, medidos
con el vóxel de la imagen. **No puede sustituir al análisis principal** (D1).

| Calibración | H11a | H11b / H12Rb | H11c | H11e |
|---|---|---|---|---|
| v0.4 (`v04_rs`) | apoyada (0 %) | no evaluable (0 verdes) | apoyada (681 de 681) | **no apoyada** (49 verdes de topología en 48 embriones, los 49 con Betti distinto de la referencia) |
| H12 `us_raw` (`h12_rs`) | apoyada (0 %) | no evaluable (0 verdes) | apoyada (227 de 227) | no evaluable (0 verdes) |

* La conclusión principal no cambia con la sensibilidad: ninguna luz verde de volumen, y todas las verdes sin guardia
  erróneas [HV].
* **H11e cambia de «no evaluable» a «no apoyada» con v0.4 [HV].** Con los 47 casos añadidos, las luces verdes de
  topología (todas de `global`) pasan de 19 a 49 y superan el mínimo de 30; todas fallan. El análisis principal de H11e
  sigue siendo «no evaluable». La sensibilidad indica que, con más casos, el veredicto principal muy probablemente habría
  sido desfavorable [EI]. La causa más directa es la referencia: el 96,2 % de los contornos de cuerpo no son un sólido
  simple (Betti ≠ (1, 0, 0)), así que una segmentación topológicamente simple casi nunca coincide [HV para el
  porcentaje, EI para la causa].
* Dice mediano del cuerpo en la sensibilidad: 0,20 / 0,27 / 0,29 (global / otsu / smoothed_otsu); el menor |error| sigue
  siendo 58 % [HV].

## 6. Predicciones escritas de antemano (§6)

| Predicción | Probabilidad asignada | Resultado |
|---|---|---|
| H12Rb no evaluable con `us_raw` | 70 % | Ocurrió |
| H12Ra apoyada (más volúmenes de cuerpo dentro del dominio con H12) | 60 % | No ocurrió (0 % y 0 %) |
| H12Rb apoyada, dado que es evaluable | 40 % | No aplica |
| Dice mediano del cuerpo con `smoothed_otsu` ≥ 0,90 | 50 % | No ocurrió (0,31) |

## 7. Qué no se puede concluir

- Que el certificado funcione con ecografía real: con ninguna de las dos calibraciones hubo verdes que evaluar.
- Que el simulador de H12 sea inútil: H12 se diseñó para un tipo de moteado; aquí solo se ve que no cubre este equipo.
- Nada sobre humanos, obstetricia ni uso clínico; un conjunto, un equipo, una especie.
- Error exacto: la referencia es un trazado humano.

## 8. Estado

- H11 y H12R quedan **cerrados** con este documento y `docs/h11/RESULTADOS_H11.md` [HV].
- Siguiente paso fijado por §5: calibración con volúmenes reales validada por embrión, con preregistro nuevo [PROP].
- Pendiente aparte: P2, distinguir «fuera de dominio» de «inservible», con su preregistro [PROP].
