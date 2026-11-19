# Preregistro — MT-A: ¿cuánto de la diferencia de forma entre E15.5 y E18.5 se debe al atlas? (v1.0, 18 nov 2026)

> Tarea P1 de `docs/INFORME_DE_PROGRESO.md` §5 y siguiente paso fijado por ONTO-MAP
> (`docs/onto_map/RESULTADOS_P4.md` §4). Es el primer experimento de MORPHO-TRACE que separa, con datos reales,
> una fuente **técnica** (el atlas de registro) de una diferencia que podría ser **biológica** (el cambio de
> forma entre estadios).
> Se sube a la rama **antes** de descargar los atlas y las imágenes de E18.5 y antes de escribir el código
> que mide. Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta ·
> [PV] pendiente de validación.
>
> Solo investigación con datos animales publicados (MusMorph/IMPC, FaceBase, CC BY 4.0). Nada humano ni clínico.

## 1. Pregunta y por qué importa

ONTO-MAP encontró que, en los landmarks de cabeza publicados por MusMorph, los estadios E15.5 y E18.5 quedan
separados por un vector **d** (longitud de Procrustes 0,157) unas 18 veces mayor que la dispersión dentro de
cada estadio a lo largo de él. Las tres hipótesis salieron contrarias, y el resultado no se pudo interpretar
porque **cada estadio se registró a su propio atlas**: un desplazamiento sistemático entre atlas produciría
exactamente esa firma (gran separación, poca dispersión) [HV, `RESULTADOS_P4.md` §3–4].

**Pregunta MT-A.** Si los mismos especímenes se registran a los **dos** atlas con el mismo procedimiento,
¿qué parte de **d** reproduce el simple cambio de atlas, con la biología fija?

Ninguna de las búsquedas de la revisión registrada devolvió una estimación de este efecto para MusMorph
[EI, `docs/estado_del_arte/REVISION_SISTEMATICA_MORPHOTRACE.md`; `docs/onto_map/REVISION_ORIGINALIDAD.md`].

## 2. Datos (verificados en el catálogo, sin descargar)

| Elemento | Archivo en FaceBase | Tamaño · MD5 del catálogo | Estado |
|---|---|---|---|
| Atlas E15.5 (imagen) | `IMPC_E15.5_Body_Atlas.mnc`, conjunto 6-2EPY | 76 534 006 B · `05245d18ee87ed25faec29b84bfb7adb` | [HV] en el catálogo, 18 nov |
| Atlas E18.5 (imagen) | `IMPC_E18.5_Body_Atlas.mnc`, 6-2EPY | 48 490 766 B · `7db10ed92076cfb325a9d9ef83c7c18a` | [HV] ídem |
| Landmarks del atlas E15.5 | `IMPC_E15.5_Head_Atlas_Landmarks.tag`, 6-2EPY | 37 693 B · `f7bb7275fb9a41d85968d5ff3771cf63` | [HV] ídem |
| Landmarks del atlas E18.5 | `IMPC_E18.5_Head_Atlas_Landmarks.tag`, 6-2EPY | 37 675 B · `fc7a3de827bd73c13dd053ee47be9733` | [HV] ídem |
| Imágenes de especímenes | `IMPC_E15.5_####.mnc` y `IMPC_E18.5_####.mnc`, conjunto 3-JZA6 | p. ej. `IMPC_E18.5_0001.mnc`, 29 408 247 B | [HV] existen en el catálogo |
| Landmarks publicados de esos especímenes | `…_Head_Landmarks.tag`, 3-JZA6 | ya descargados para ONTO-MAP, MD5 correcto | [HV] |

Licencia CC BY 4.0, con cita de Devine et al. 2022, *Sci Data* 9:230 [HV, como en P3 y ONTO-MAP]. Todo queda
fuera de git, con manifiesto SHA-256 verificable (`geovida.manifest`).

**Muestra (fija, sin elección nueva).** Los **20 + 20** especímenes del **piloto de ONTO-MAP**
(`results/onto_map/seleccion.json`, controles silvestres IMPC, semilla 20261116), porque tienen landmarks
publicados y son **disjuntos** del confirmatorio de ONTO-MAP, con el que se estimó **d**. Así **d** y el efecto
del atlas no se calculan con los mismos especímenes. De los 20 de E15.5, 6 tienen ya su imagen en local (de P3);
faltan 14 imágenes de E15.5 y 20 de E18.5 (unos 1,6 GB).

**Lo que ya se vio de estos datos.** Los landmarks publicados del piloto entraron en las comprobaciones
previas de ONTO-MAP; **d** sale del confirmatorio ya publicado. Ninguno de los dos se reajusta aquí. El análisis
de ONTO-MAP guardó los ángulos pero **no** el vector **d** (`results/onto_map/analisis_confirm.json` solo tiene
`n`, `rho_max`, `dim95`, `null_q01_deg`, `cs_mean`, `n_boot_valid` y `angles`) [HV]: se recalcula de forma
determinista a partir de las 717 configuraciones publicadas, y debe reproducir la longitud publicada (puerta G0-d).

## 3. Protocolo (fijo)

**Unidad experimental:** el espécimen. Cada uno se registra **dos veces**, al atlas de su estadio («propio») y
al del otro estadio («cruzado»), con el mismo procedimiento.

**Registro (SimpleITK 2.5.7, sin ajustar después de ver resultados):**

1. Lectura MINC con `geovida.minc.load_minc`, conservando la geometría del mundo (afín de la cabecera). Imagen
   y atlas se pasan a SimpleITK con origen, espaciado y dirección de esa afín. Todo el experimento usa la
   convención de coordenadas de MINC; no se mezcla con lectores que la cambien.
2. Submuestreo por media de bloques **×4** de imagen y atlas (de unos 27 µm a unos 108 µm), por la memoria del
   equipo (3,9 GB).
3. Inicialización por centros de masa; **afín** (12 grados de libertad), información mutua de Mattes
   (50 contenedores, 10 % de muestreo, semilla 20261118), descenso de gradiente regular, 3 niveles (factores
   4, 2, 1; suavizado 2, 1, 0 vóxeles).
4. **B-spline** sobre la afín: malla de 8 × 8 × 8 nodos, misma métrica, LBFGS-B, 100 iteraciones, 2 niveles.
5. **Transferencia:** con el atlas como imagen fija y el espécimen como móvil, la transformada lleva puntos del
   atlas al espécimen. Los 540 landmarks de cada atlas se llevan así al espacio del espécimen:
   **L₁₅(s)** desde el atlas E15.5 y **L₁₈(s)** desde el atlas E18.5.

**Correspondencia de puntos entre atlas.** El punto *i* es el mismo en los dos atlas: ya comprobado en un par
de especímenes (ρ de Procrustes 0,170 frente a ≥ 1,46 con órdenes barajados) [HV en 1 par,
`docs/onto_map/PROTOCOLO_ONTOMAP.md`]. Se repite sobre los dos `.tag` de los atlas (comprobación G0-c).

**Espacio de forma común.** Un único GPA (`geovida.landmarks.gpa`) con: las 717 configuraciones publicadas del
confirmatorio (definen la media y **d**) y las 80 transferidas (40 especímenes × 2 atlas). Coordenadas tangentes
respecto de esa media. **d** = media E18.5 − media E15.5 del confirmatorio publicado, en ese espacio;
**d̂** = d / |d|.

**Efecto del atlas por espécimen:** **δ(s) = L₁₈(s) − L₁₅(s)** en coordenadas tangentes. Con la biología fija,
δ(s) solo contiene la diferencia entre atlas más el error del registro cruzado.

**Incertidumbre:** remuestreo por espécimen (2000 réplicas, semilla 20261118), percentil 95 %. En cada réplica
se recalculan δ̄ y las proyecciones; **d** se toma fija (sale del confirmatorio publicado, no de esta muestra).

## 4. Comprobaciones previas (puertas; si una falla, no hay veredicto)

| Puerta | Qué se comprueba | Criterio |
|---|---|---|
| **G0-a** Geometría | Los landmarks publicados de 3 especímenes, leídos en coordenadas del mundo, caen dentro de la cabeza de su imagen | ≥ 95 % de los puntos en vóxeles con intensidad por encima del umbral de Otsu de la imagen |
| **G0-b** Geometría del atlas | Ídem con los landmarks de cada atlas sobre su imagen | Ídem |
| **G0-c** Correspondencia | Los 540 puntos se corresponden entre los dos atlas | `correspondence_check`: ρ con el orden dado menor que el mínimo de 200 órdenes barajados |
| **G0-d** Reproducción de d | GPA solo de las 717 configuraciones publicadas, con `geovida.landmarks` | Longitud de d entre 0,150 y 0,164 (publicada: 0,157). Si no, se para y se busca la discrepancia antes de seguir |
| **G1** Calidad del registro propio | Para cada espécimen, distancia de Procrustes ρ entre L_propio(s) y sus landmarks publicados | Mediana de ρ **menor** que la mediana de ρ entre pares de especímenes distintos del mismo estadio (landmarks publicados del piloto). Si no, el procedimiento no reproduce lo publicado mejor que la variación biológica y MT-A es **no evaluable** |
| **G2** Registros válidos | Registros que terminan sin error y con métrica final finita | ≥ 16 de 20 por estadio |

## 5. Hipótesis y criterios (fijos)

**Estimando primario:** **f = ⟨δ̄, d̂⟩ / |d|**, la fracción de **d** que reproduce el cambio de atlas, con δ̄ la
media de δ(s) sobre los especímenes válidos de los dos estadios.

* **MT-A1 (primaria) — El atlas explica buena parte de d.**
  *Apoyada* si el límite inferior del IC 95 % de f es **≥ 0,50**.
  *Refutada* si el límite superior es **≤ 0,25** (el atlas explica poco de d).
  *No concluyente* en cualquier otro caso. *No evaluable* si falla una puerta.
* **MT-A2 (secundaria) — El efecto es sistemático.** El ángulo entre δ̄ calculado con los especímenes de E15.5 y
  con los de E18.5 es **< 45°** (punto estimado; se informa el IC). Un efecto del atlas debería ser el mismo sea
  cual sea el estadio del espécimen.
* **MT-A3 (descriptiva).** |δ̄| / |d|, ángulo(δ̄, d) y la dispersión de δ(s) a lo largo de d̂ comparada con la
  de los especímenes publicados dentro de un estadio (0,0087 y 0,0082 en ONTO-MAP).

Un valor no calculable es «no evaluable», nunca «refutada».

## 6. Sensibilidad (declarada ahora; no cambia el veredicto)

1. Malla B-spline de 6³ y 10³ nodos en lugar de 8³.
2. Solo afín (sin B-spline): cota de lo que aporta la parte no lineal.
3. Registro directo **atlas E18.5 → atlas E15.5** (un solo registro) y transferencia de sus landmarks: estima el
   desplazamiento entre atlas sin especímenes; se compara con δ̄.

## 7. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| Pasan las puertas G0 | 75 % |
| Pasa G1 (el registro propio reproduce lo publicado mejor que la variación entre especímenes) | 50 % |
| MT-A1 apoyada, dado que es evaluable | 40 % |
| MT-A1 refutada, dado que es evaluable | 25 % |
| MT-A2: ángulo < 45° | 60 % |

## 8. Qué significará cada resultado (antes de verlo)

| Resultado | Conclusión | Siguiente paso |
|---|---|---|
| MT-A1 apoyada | Buena parte de la separación entre estadios de MusMorph es técnica. Las trayectorias de ONTO-MAP no se pueden estudiar con landmarks de atlas distintos | Registrar todos los estadios a un atlas común antes de cualquier análisis de trayectorias |
| MT-A1 refutada | El atlas no explica la mayor parte de d. La explicación biológica de ONTO-MAP gana peso, sin quedar demostrada | Repetir ONTO-MAP con los landmarks de atlas común como sensibilidad |
| No concluyente | Faltan especímenes o el registro es ruidoso | Más especímenes, mismo protocolo |
| No evaluable (G1) | Este registro no reproduce lo publicado; nada se puede decir del atlas | Probar otro registrador (p. ej. ANTs, el de MusMorph) con un preregistro nuevo |

## 9. Qué no se puede concluir

* δ(s) mezcla la diferencia entre atlas con el error del registro cruzado (un E15.5 hacia un atlas E18.5 exige
  más deformación). La sensibilidad 3 y G1 lo acotan, no lo eliminan.
* El registro de MusMorph (ANTs no lineal) no es el de aquí: se mide el efecto del atlas **con este registro**,
  validado por G1 contra lo publicado.
* Dos estadios transversales: nada sobre trayectorias continuas.
* Landmarks por registro automático, sin anotación experta [PV].
* Nada sobre otros órganos, especies, humanos ni uso clínico.

## 10. Plan de ejecución y recursos

1. Código `src/geovida/atlas_effect.py` y pruebas con fantomas de geometría conocida (transformada afín y
   deformación conocidas; transferencia de puntos con error medible) **antes** de descargar nada.
2. Descarga con MD5 del catálogo y manifiesto SHA-256 (`geovida.manifest`).
3. Puertas G0, luego registros (unos 80 + sensibilidad; del orden de 5 min por registro a ×4, estimación [PV]).
   Se ejecuta cuando terminen P3 confirmatorio y H12R, por la memoria del equipo.
4. Informe en `docs/morpho_trace/RESULTADOS_ATLAS.md`, transcribiendo los veredictos según §5 y §8.

## 11. Desviaciones

(Ninguna al subir este preregistro.)

### Notas de ejecución (no cambian ningún criterio)

* **18 nov 2026 — aclaración.** El vector **d** no se guardó, pero su **longitud** sí:
  `results/onto_map/exploratorio_confirm.json`, `d_norm` = 0,15670679 (el `rho_max` de `analisis_confirm.json`,
  0,15674, es otra magnitud que coincide casi por azar) [HV].
* **18 nov 2026 — G0-d superada.** `scripts/atlas_effect_gates.py g0d` sobre las 717 configuraciones del
  confirmatorio (259 + 458): longitud de **d** = **0,156707**, dentro de [0,150, 0,164] e idéntica a la guardada por
  ONTO-MAP [HV]. Se ejecutó antes de descargar nada porque solo usa landmarks ya publicados y analizados; no depende
  de ningún dato nuevo.
* **19 nov 2026 — descarga de los atlas.** `scripts/atlas_effect_gates.py download` comprobó primero que el
  catálogo de FaceBase (6-2EPY) daba los tamaños y MD5 de §3 y después el MD5 de cada archivo bajado: los cuatro
  coinciden [HV]. Manifiesto SHA-256 en `data/manifests/musmorph_atlas.csv`; incluye también
  `IMPC_E15.5_Body_Atlas_Segs.mnc`, del mismo registro, bajado el 15 nov para P3 y no usado en MT-A.
* **19 nov 2026 — G0-c superada.** `scripts/atlas_effect_gates.py g0c`: los dos `.tag` tienen 540 puntos; ρ de
  Procrustes con el orden dado = **0,160**, frente a un mínimo de **1,454** (mediana 1,521) en 200 órdenes
  barajados (semilla 20261118, la del estudio, porque §4 no fijaba otra) [HV]. Coincide con la comprobación de un
  par de especímenes de ONTO-MAP (0,170 frente a ≥ 1,46).
* **19 nov 2026 — imágenes de los especímenes.** `scripts/atlas_effect_gates.py download-images`: las 40 imágenes
  del piloto de ONTO-MAP (20 + 20) tienen el MD5 del catálogo de FaceBase (3-JZA6) [HV]. 34 se bajaron (unos
  2,0 GB, no los 1,6 GB estimados en §2: las de E15.5 pesan unos 94 MB cada una) y 6 se copiaron de la descarga de
  P3 tras comprobar su MD5. Manifiesto SHA-256 en `data/manifests/musmorph_mta_images.csv`.
* **G0-a** (landmarks publicados dentro de la cabeza) se pospone hasta que terminen P3 y H12R: cada imagen ocupa
  unos 800 MB en memoria y el equipo tiene 3,9 GB, con unos 700 MB libres mientras corren.
