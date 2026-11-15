# P3 — Piloto: descarga y comprobaciones previas (15 nov 2026)

> Solo el piloto (20 especímenes), que según `docs/PREREGISTRO_P3.md` §4 **no entra en el análisis confirmatorio**. Aquí no se calcula τ, `p` ni ninguna medida de las hipótesis: solo se comprueba que los datos sirven para el diseño.
> Solo investigación y educación; datos animales publicados (CC BY 4.0), sin datos humanos. Los volúmenes están fuera de git (`data/external/`).
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PV] pendiente de validación.

## 1. Qué se hizo

| Paso | Orden | Resultado |
|---|---|---|
| Metadatos | `MusMorph_Metadata_Mar2024.csv` del repositorio de MusMorph (SHA-256 `9f5aa3de…98ed`) | — |
| Muestreo | `python scripts/p3_pilot.py select` (semilla 20261114) | 309 elegibles; piloto 20 (10 hembras, 10 machos); confirmatorio 60 (30 + 30), disjunto del piloto [HV] |
| Descarga | Catálogo ERMrest de FaceBase, registro 3-JZA6. Se hizo con un script de PowerShell equivalente; después se versionó la misma lógica como `python scripts/p3_pilot.py download` | 40 archivos (imagen y segmentación de cada espécimen), 1,83 GB; **los 40 con el MD5 del catálogo** [HV]. FaceBase los sirve sin autenticación |
| Manifiesto | `python -m geovida.manifest build` y `verify` | `results/p3/manifiesto_piloto.csv`: SHA-256 de los 40 archivos; `verify`: 40 correctos, 0 con diferencias [HV] |
| Comprobaciones | `python scripts/p3_pilot.py check` (regla `nearest`) | 3.1 y 3.2 **pasan** (§3) |

Entorno: Windows 11, Python 3.13.17, 4 CPU y 3,9 GB de RAM. Con esta memoria, la comprobación de los 20 especímenes tardó 43 minutos (≈ 2,1 min por espécimen) [HV]. Ese dato sirve para dimensionar el confirmatorio, según la regla de E4 de `docs/ERRATA.md`. Después se aceleró la búsqueda a 2 vóxeles (misma salida, ~3 veces más rápida en esa parte).

## 2. Hallazgo sobre el formato: segmentaciones interpoladas (desviación D1)

Las segmentaciones `<ID>_Segs.mnc` no son mapas de etiquetas enteras: son MINC2 en coma flotante. En los 20 especímenes, **entre el 28 % y el 32 %** de los vóxeles con valor > 0 tienen valores intermedios entre números de etiqueta [HV, `results/p3/diagnostico_segs.json`]. La causa es que el script de propagación de MusMorph remuestrea el atlas con interpolación trilineal [HV, `Processing/Label_Propagation.py`].

Se registró la desviación D1 en el preregistro **antes de medir nada** (commit `ca91d8d`). Fija:
- una regla principal (`nearest`), que recupera las etiquetas a partir de los vóxeles exactos vecinos;
- una regla de sensibilidad (`exact`), que descarta los vóxeles mezclados.

La regla `nearest` se validó con una sonda sintética (`tests/test_p3_data.py`).

Recuperación en los 20 especímenes (regla `nearest`) [HV, `results/p3/precheck_piloto.json`]:

| Medida | Mínimo | Mediana | Máximo |
|---|---|---|---|
| Vóxeles mezclados (fracción de los vóxeles con etiqueta) | 27,9 % | 29,3 % | 31,7 % |
| Mezclados con tres o más candidatos (asignación aproximada) | 0,4 % | 0,7 % | 1,5 % |
| Mezclados sin vecino exacto a 1 vóxel (buscados a 2) | 1,6 % | 3,7 % | 8,4 % |
| Mezclados que quedan sin candidato (pasan a fondo), en vóxeles | 7 | 86 | 1516 |

## 3. Comprobaciones previas (§3 del preregistro)

| Comprobación | Criterio | Resultado |
|---|---|---|
| 3.1 Existencia | segmentación para ≥ 80 % de los elegidos | **20/20, pasa** [HV] |
| 3.2 Espacio del espécimen | el volumen de cada etiqueta varía entre especímenes (CV > 0) en ≥ 90 % de las etiquetas | **50/50 etiquetas varían, pasa** [HV]. El CV entre especímenes va de 0,16 a 0,41 (mediana 0,26); es descriptivo y no se interpreta |
| 3.3 Fuga de datos de MEMOS | excluir los escáneres de entrenamiento de MEMOS si se pueden identificar | **Pendiente** [PV] |
| 3.4 MEMOS ejecutable | corre en ≥ 90 % de los volúmenes del piloto | **Pendiente**: necesita 3D Slicer [PV] |

Otros datos comprobados [HV]:
- Los 20 especímenes tienen el mismo vóxel: 0,027 mm isótropo.
- Todos tienen los ejes del mundo en el mismo orden (+z, +y, +x).
- Todos tienen las mismas 50 etiquetas: 1 a 48, más la 102 y la 103.
- La imagen y la segmentación comparten la rejilla, comprobado en 2 especímenes.

## 4. Qué NO se puede concluir

- Nada sobre las hipótesis: no se ha calculado ninguna τ ni ningún certificado.
- La predicción «las comprobaciones previas se superan» (60 %, §8 del preregistro) aún no se puede puntuar: faltan 3.3 y 3.4.
- La recuperación de etiquetas aproxima el remuestreo por vecino más cercano que MusMorph no hizo; no es una segmentación de referencia.
- [HIP] La 102 y la 103 corresponden a los ventrículos de KOMP2 (49 y 50) [PV].

## 5. Siguiente paso

1. 3.3 y 3.4: localizar la lista de escáneres de entrenamiento de MEMOS, y ejecutar MEMOS (3D Slicer) sobre los 20 volúmenes del piloto.
2. Lista de nombres de las 48 etiquetas de MusMorph y su correspondencia con KOMP2 (§10 del preregistro).
3. Si 3.3 y 3.4 se resuelven, aplicar el flujo completo de §5 al piloto, solo para tiempos y anchura de intervalos, y decidir con la regla de ampliación (60 o 120) **antes** de descargar el confirmatorio.
