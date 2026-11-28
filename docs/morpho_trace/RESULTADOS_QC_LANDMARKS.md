# Resultados — QC-LM: landmarks publicados de MusMorph lejos del tejido y su efecto sobre **d** (19 nov 2026)

> Transcripción de los veredictos de `docs/morpho_trace/PREREGISTRO_QC_LANDMARKS.md` (§4–§7). **Nada se
> reinterpreta ni se reajusta.** Los números salen de `results/landmark_qc/analisis.json` y de las 120 medidas por
> espécimen en `results/landmark_qc/medidas/` (fuera de git, como los datos). Etiquetas: [HV] verificado ·
> [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta. Solo datos animales publicados (MusMorph/IMPC,
> FaceBase 3-JZA6, CC BY 4.0, Devine et al. 2022). Nada humano ni clínico.

## 1. Qué se midió

| Elemento | Valor |
|---|---|
| Muestra | 60 E15.5 + 60 E18.5 del confirmatorio de ONTO-MAP, semilla 20261119, `results/landmark_qc/muestra.json` (SHA-256 `8c97e0b9…f49784`, el del preregistro) [HV] |
| Imágenes | 120, todas con el MD5 del catálogo de FaceBase: 102 descargadas y 18 copiadas de la descarga de P3 [HV]. Manifiesto SHA-256: `data/manifests/musmorph_qc_images.csv` |
| Medida | Distancia al tejido de los 540 landmarks publicados de cada espécimen (umbral de Otsu de toda la imagen, búsqueda hasta 0,5 mm); cumple si ≥ 95 % quedan a ≤ 0,23 mm (`geovida.atlas_effect.distance_to_tissue`) [HV] |
| Remuestreo | 2000 réplicas por espécimen dentro de cada estadio, semilla 20261119 [HV] |
| Ejecución | 19 nov 2026, `scripts/landmark_qc.py measure` y `analyze` |

**Procedencia del código [HV].** La copia local no es un repositorio git. La huella de código guardada por `analyze`
coincide con el código local al terminar, y los cuatro archivos que hacen la medida tienen los blobs subidos a la rama
antes de medir: `landmark_qc.py` 31522e8, `atlas_effect.py` 9369540, `minc.py` 8c59e44, `atlas_effect_gates.py`
97fed26.

**Recuento independiente [HV].** Desde los 120 archivos por espécimen, sin usar `analyze`: no cumplen 20 de 60 E15.5
y 0 de 60 E18.5. Coincide con el JSON.

## 2. Puertas

| Puerta | Resultado | |
|---|---|---|
| G1 — medidas completas (≥ 57 de 60 por estadio) | 60 y 60 | **superada** |
| G2 — misma rejilla que el atlas de su estadio | todas | **superada** |

## 3. Veredictos preregistrados

| Hipótesis | Criterio (§5) | Resultado | Veredicto |
|---|---|---|---|
| **QC1** (primaria) — más landmarks desplazados en E15.5 | Δ = fracción que no cumple en E15.5 − en E18.5; apoyada si el límite inferior del IC 95 % > 0 | 33,3 % − 0,0 % = **Δ 0,333**, IC 95 % **0,217 a 0,450** | **apoyada** |
| **QC2** (secundaria) — quitar los que no cumplen cambia **d** | r = (\|d\|cumplen − \|d\|todos)/\|d\|todos; refutada si el IC queda dentro de (−0,05; 0,05). Evaluable: ≥ 3 E15.5 que no cumplen (20) y ≥ 30 que cumplen por estadio (40 y 60) | \|d\| todos 0,15724; cumplen 0,15826; **r = +0,0065**, IC 95 % **−0,0019 a 0,0177** | **refutada** |

## 4. QC3 — descripción (sin criterio)

| | E15.5 | E18.5 |
|---|---|---|
| Fracción de landmarks a ≤ 0,23 mm: mínimo / cuartil 1 / mediana / cuartil 3 | 0,583 / 0,935 / 0,982 / 0,997 | 0,987 / 1,000 / 1,000 / 1,000 |
| Distancia mediana por espécimen: mediana (máximo) | 0,056 mm (0,140) | 0,032 mm (0,053) |
| p90 por espécimen: mediana (máximo) | 0,148 mm (0,343); sin p90 calculable en `IMPC_E15.5_0481` (65 de 540 landmarks, el 12 %, sin tejido a 0,5 mm) | 0,060 mm (0,138) |
| Especímenes con algún landmark sin tejido a 0,5 mm | 10 de 60 (102 landmarks en total; como máximo 65 en uno) | 0 de 60 |
| \|d\| con todos / con los que cumplen | 0,15724 / 0,15826 (muestra de 120) | |

Los 20 E15.5 que no cumplen van de 58,3 % (`IMPC_E15.5_0481`) a 94,3 % de landmarks a ≤ 0,23 mm; más de la mitad están
cerca del umbral (11 de 20 por encima del 90 %) [HV].

## 5. Predicciones escritas de antemano (§6)

| Predicción | Probabilidad | Resultado |
|---|---|---|
| Pasan G1 y G2 | 85 % | Ocurrió |
| QC1 apoyada | 65 % | Ocurrió |
| QC1 refutada | 10 % | No ocurrió |
| QC2 evaluable | 70 % | Ocurrió |
| QC2 apoyada, dado que es evaluable | 35 % | No ocurrió |
| QC2 refutada, dado que es evaluable | 30 % | Ocurrió |

## 6. Qué significa (fila de la tabla §7 decidida de antemano)

**QC1 apoyada, QC2 refutada** → «Hay errores, pero no mueven **d** a esta escala. **d** de ONTO-MAP se mantiene frente a
este error; el factor atlas sigue sin medir.»

1. **Lo del piloto se repite en especímenes nuevos [HV].** En el piloto de MT-A no cumplían 6 de 20 E15.5 y 0 de 20
   E18.5; aquí 20 de 60 y 0 de 60. Los landmarks publicados de E15.5 caen fuera del tejido con más frecuencia que los de
   E18.5.
2. **Pero no explican la separación de forma [HV].** Quitar a esos 20 especímenes cambia |d| un 0,65 % (IC −0,19 % a
   +1,77 %), muy por debajo del 5 % fijado. El error de colocación que mide QC-LM no es lo que separa E15.5 de E18.5 en
   ONTO-MAP.
3. **Por qué puede ser así [EI].** Más de la mitad de los que no cumplen están cerca del umbral, y GPA promedia 540 puntos:
   unos pocos landmarks desplazados en algunos especímenes apenas mueven la media de cada estadio.
4. **Lo que sigue abierto.** La confusión con el atlas de cada estadio (MT-A) no se ha medido: MT-A v1.0 y v1.1 quedaron
   «no evaluables» y QC-LM no la aborda. Un MT-A nuevo puede usar ahora la regla de QC-LM para filtrar especímenes sin
   temer que el filtro cambie **d** [PROP, con su propio preregistro].

## 7. Qué no se puede concluir

- «Lejos del tejido» no es «mal colocado»: un landmark bien colocado en una zona de poco contraste puede quedar fuera
  del umbral de Otsu; el umbral de 0,23 mm viene de cráneos adultos [EI].
- QC2 se midió en la muestra de 120, no en los 717 del confirmatorio; no corrige el resultado publicado de ONTO-MAP, lo
  pone a prueba frente a un error concreto.
- Nada sobre el efecto del atlas, otras especies, humanos ni uso clínico.

## 8. Estado

QC-LM queda **cerrado** con este documento. Siguiente paso propuesto: MT-A v2 (registro de los mismos especímenes a los
dos atlas) con especímenes filtrados por la regla de QC-LM, con preregistro nuevo [PROP].
