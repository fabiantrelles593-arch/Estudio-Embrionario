# P3 — Piloto: datos, comprobaciones previas y flujo completo (15 nov 2026)

> Solo el piloto (20 especímenes), que según `docs/PREREGISTRO_P3.md` §4 **no entra en el análisis confirmatorio**. Sirve para comprobar el flujo, medir tiempos y proyectar la anchura de los intervalos. Las cifras de τ, Δ y ρ del piloto **no son resultados de P3**.
> Solo investigación y educación; datos animales publicados (CC BY 4.0), sin datos humanos. Los volúmenes están fuera de git (`data/external/`). Los pesos de MEMOS y el atlas de consenso tienen licencia no declarada: se usan solo en local.
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PV] pendiente de validación.

## 1. Qué se hizo

| Paso | Orden | Resultado |
|---|---|---|
| Metadatos | `MusMorph_Metadata_Mar2024.csv` del repositorio de MusMorph (SHA-256 `9f5aa3de…98ed`) | — |
| Muestreo | `python scripts/p3_pilot.py select` (semilla 20261114) | 309 elegibles; piloto 20 (10 hembras, 10 machos); confirmatorio 60 (30 + 30), disjunto del piloto [HV] |
| Descarga | Catálogo ERMrest de FaceBase, registro 3-JZA6 (`python scripts/p3_pilot.py download`) | 40 archivos, 1,83 GB; **los 40 con el MD5 del catálogo** [HV] |
| Manifiesto | `python -m geovida.manifest build` y `verify` | `results/p3/manifiesto_piloto.csv`: 40 correctos, 0 con diferencias [HV] |
| Comprobaciones 3.1–3.2 | `python scripts/p3_pilot.py check` (regla `nearest`) | Pasan (§3) |
| MEMOS (segmentador B) | `python scripts/p3_memos.py run` (D2: ×2, sin 3D Slicer) | **20 de 20** segmentados (§4) |
| Grupos (§5.6, D4) | `python scripts/p3_analyze.py groups` sobre el atlas de consenso | 36 unidades: 18 delgadas y 18 compactas (`results/p3/grupos.csv`, commit `86236eb`, **antes** de calcular ninguna τ) |
| Desfase (D3) | `python scripts/p3_memos.py compare` | §5 |
| Rigidez (D5) | `python scripts/p3_memos.py rigidity` | 3 de 20 no rígidos (dispersión > 4 vóxeles): `0120`, `0422`, `0429` (§5) [HV] |
| Análisis | `python scripts/p3_analyze.py pilot` | Decisión D4: **60 especímenes** (§6) [HV] |

Entorno: Windows 11, Python 3.13, 4 CPU y 3,9 GB de RAM, sin GPU.

## 2. Hallazgo sobre el formato: segmentaciones interpoladas (desviación D1)

Las segmentaciones `<ID>_Segs.mnc` son MINC2 en coma flotante: en los 20 especímenes, **entre el 28 % y el 32 %** de los vóxeles con valor > 0 tienen valores intermedios entre números de etiqueta [HV, `results/p3/diagnostico_segs.json`]. La causa es que el script de propagación de MusMorph remuestrea el atlas con interpolación trilineal [HV]. El atlas de consenso, en cambio, tiene etiquetas enteras (D4), lo que confirma que la mezcla aparece al propagar.

Se registró D1 **antes de medir nada** (commit `ca91d8d`): regla principal `nearest` y sensibilidad `exact`, validadas con una sonda sintética (`tests/test_p3_data.py`).

| Recuperación (regla `nearest`) | Mínimo | Mediana | Máximo |
|---|---|---|---|
| Vóxeles mezclados (fracción de los vóxeles con etiqueta) | 27,9 % | 29,3 % | 31,7 % |
| Mezclados con tres o más candidatos (asignación aproximada) | 0,4 % | 0,7 % | 1,5 % |
| Mezclados sin vecino exacto a 1 vóxel (buscados a 2) | 1,6 % | 3,7 % | 8,4 % |
| Mezclados que quedan sin candidato (pasan a fondo), en vóxeles | 7 | 86 | 1516 |

## 3. Comprobaciones previas (§3 del preregistro)

| Comprobación | Criterio | Resultado |
|---|---|---|
| 3.1 Existencia | segmentación para ≥ 80 % de los elegidos | **20/20, pasa** [HV] |
| 3.2 Espacio del espécimen | el volumen de cada etiqueta varía entre especímenes en ≥ 90 % de las etiquetas | **50/50, pasa** [HV] (CV entre especímenes 0,16–0,41, descriptivo) |
| 3.3 Fuga de datos de MEMOS | excluir los escáneres de entrenamiento si se pueden identificar | **No identificables: se declara como limitación** (D2) [EI] |
| 3.4 MEMOS ejecutable | corre en ≥ 90 % del piloto | **20/20, pasa** [HV] |

Con esto, la predicción «las comprobaciones previas se superan» (60 %, §8) se cumple en el piloto; 3.1 y 3.2 se repiten sobre el confirmatorio.

## 4. MEMOS sin 3D Slicer (desviación D2)

- **Tiempo [HV, `results/p3/memos/memos_run.json`]:** mediana 18 min por espécimen (de 4 a 110 min sin contar `0812`, ver abajo), 10 h en total para los 20, en CPU con 4 núcleos. El número de ventanas de 128³ va de 18 a 240 según el tamaño del cuerpo.
- **Incidencias de ejecución (no de MEMOS):**
  - `0479` falló la primera vez porque Windows bloqueó el borrado de un archivo temporal **después** de terminar la inferencia. Se corrigió la limpieza y se repitió; no cuenta como fallo de MEMOS.
  - Durante unas horas corrieron dos procesos de MEMOS a la vez (uno de la sesión anterior seguía vivo), lo que multiplicó por casi cuatro el tiempo de `0812` (118 min). No cambia sus resultados.
- **Etiquetas [HV, 1 espécimen, D3]:** las etiquetas 1–48 de MusMorph caen sobre la misma etiqueta de MEMOS (KOMP2). La 102 y la 103 de MusMorph no se corresponden con la 49 y la 50 de KOMP2, y se excluyen de τ.

## 5. MEMOS frente al atlas propagado (H-P3c, desviaciones D3 y D5)

Traslación entera del atlas que maximiza el Dice de las uniones (D3), y Dice mediano por estructura (1–48) sin y con esa traslación [HV, `results/p3/memos/memos_vs_atlas.json`]:

| Espécimen | Traslación (vóxeles) | Dice unión sin → con | Dice mediano sin → con | Dispersión D5 |
|---|---|---|---|---|
| `0040` | (16, 6, −4) | 0,70 → 0,90 | 0,22 → 0,74 | 4 |
| `0071` | (−1, −1, 0) | 0,89 → 0,90 | 0,72 → 0,73 | 4 |
| `0092` | (14, −11, 0) | 0,68 → 0,86 | 0,32 → 0,70 | 4 |
| `0120` | (−17, 16, −4) | 0,62 → 0,73 | 0,17 → 0,27 | **27 (no rígido)** |
| `0124` | (−1, −1, 0) | 0,85 → 0,86 | 0,73 → 0,75 | 2 |
| `0218` | (−1, 0, 0) | 0,90 → 0,91 | 0,79 → 0,78 | 1 |
| `0219` | (−1, 0, 0) | 0,91 → 0,91 | 0,78 → 0,78 | 2 |
| `0223` | (−2, −1, 1) | 0,83 → 0,83 | 0,67 → 0,69 | 2 |
| `0406` | (−2, 0, 0) | 0,69 → 0,70 | 0,60 → 0,58 | 4 |
| `0422` | (1, −4, 0) | 0,82 → 0,85 | 0,65 → 0,71 | **5 (no rígido)** |
| `0429` | (8, 17, −2) | 0,57 → 0,72 | 0,17 → 0,39 | **21 (no rígido)** |
| `0455` | (0, 0, 0) | 0,82 → 0,82 | 0,60 → 0,60 | 4 |
| `0479` | (−1, 0, 0) | 0,88 → 0,89 | 0,74 → 0,75 | 2 |
| `0742` | (−1, 0, 0) | 0,91 → 0,92 | 0,84 → 0,83 | 1 |
| `0812` | (0, 0, 0) | 0,90 → 0,90 | 0,85 → 0,85 | 2 |
| `0855` | (−1, 0, 0) | 0,90 → 0,91 | 0,84 → 0,83 | 1 |
| `1190` | (0, 1, 0) | 0,91 → 0,91 | 0,81 → 0,82 | 2 |
| `1200` | (−1, 0, 0) | 0,90 → 0,90 | 0,82 → 0,83 | 1 |
| `1209` | (0, 0, 0) | 0,91 → 0,91 | 0,83 → 0,83 | 1 |
| `1411` | (−1, 0, 0) | 0,87 → 0,87 | 0,80 → 0,79 | 3 |

- **[HV] El desfase grande es la excepción:** 4 de 20 especímenes (`0040`, `0092`, `0120`, `0429`) tienen traslaciones de 17–24 vóxeles de longitud (0,5–0,6 mm); en los otros 16, ninguna componente pasa de 4 vóxeles (y en 15 de ellos, de 2).
- **[HV] D5 marca 3 de 20 especímenes como no rígidos** (`results/p3/memos/memos_rigidity.json`): la dispersión es la mayor diferencia, por eje, entre las traslaciones óptimas de los tres tercios del cuerpo.
  - `0429` (21 vóxeles): la traslación en y del atlas cambia de forma casi lineal a lo largo del cuerpo (29, 22 y 8 vóxeles por tercios), compatible con un giro de unos 4°.
  - `0120` (27 vóxeles): los tercios no comparten ninguna traslación (en y: 21, −6 y 0), y por eso trasladar apenas mejora el acuerdo (0,17 → 0,27).
  - `0422` (5 vóxeles): queda justo por encima del umbral. Es un desajuste pequeño, pero la regla preregistrada (> 4) se aplica sin excepciones.
- **[HV] Los otros 17 tienen dispersión de 1 a 4 vóxeles**, incluidos `0040` y `0092`, cuyo desfase grande sí es una traslación casi rígida (dispersión 4). Cinco quedan justo en el umbral (dispersión 4: `0040`, `0071`, `0092`, `0406`, `0455`), así que en el confirmatorio la lista de no rígidos puede depender de 1 vóxel; por eso D5 es solo un análisis de sensibilidad de H-P3c y no cambia el análisis principal.
- **[HV] Sensibilidad de D5 en el piloto:** la mediana entre especímenes del Dice mediano con traslación pasa de 0,75 (n = 20) a 0,78 sin los 3 no rígidos (n = 17) [`results/p3/informe_piloto.md`].
- **[HV] Sin desfase, el acuerdo por estructura es moderado:** en los 16 especímenes bien alineados, el Dice mediano por estructura va de 0,58 a 0,85 (mediana del conjunto 0,75 con los 20).
- **[HIP] Causa del desfase:** error de registro del atlas al especímen, o diferencia de orientación entre la imagen y la segmentación publicadas. No se puede decidir cuál de las dos máscaras está mal colocada [PV].
- Como fija el preregistro, **ninguno de los dos segmentadores es una verdad anatómica**: esto describe su acuerdo, no su exactitud.

## 6. Análisis del piloto (solo tiempos y anchura de intervalos)

Orden: `python scripts/p3_analyze.py pilot --n-boot 2000` (semilla 20261115, regla `nearest`, valor `log_volume`, 36 unidades: 18 + 18) [HV, `results/p3/analisis_piloto.json`].

| Magnitud | Valor | Uso |
|---|---|---|
| Tiempo de medición | 17 561 s (4,9 h; unos 14,6 min por espécimen) | Planificación: el confirmatorio con 60 especímenes necesita unas 15 h solo para medir con la regla principal |
| Tiempo de evaluación (bootstrap) | 20 s | — |
| Semianchura del IC 95 % de Δ (n = 20) | 0,076 | Entrada de la regla de D4 |
| Semianchura proyectada a 60 (`hw × √(20/60)`) | **0,044** | ≤ 0,10 |
| **Decisión de tamaño (D4)** | **60 especímenes** | No hace falta ampliar a 120 |

- **[HV] La regla de ampliación se aplicó tal como se preregistró:** la proyección (0,044) queda muy por debajo del umbral de 0,10, así que el confirmatorio usa los 60 especímenes ya elegidos en el muestreo (`results/p3/seleccion.json`, sin cambios).
- **Las estimaciones puntuales del piloto (Δ, ρ y sus intervalos) no se informan aquí a propósito.** Están en `results/p3/analisis_piloto.json` para la auditoría, pero el preregistro (§4) las excluye del contraste y no deben leerse como un adelanto de H-P3a ni de H-P3b.
- **[HV] El flujo completo funciona de principio a fin** sobre datos reales: lectura MINC, recuperación de etiquetas (D1), degradación ×1/×2/×4, medidas, τ por unidad, bootstrap y decisión.

## 7. Qué NO se puede concluir

- Nada sobre las hipótesis H-P3a y H-P3b: el piloto no entra en el confirmatorio.
- Nada sobre exactitud anatómica de ninguno de los dos segmentadores.
- La recuperación de etiquetas aproxima un remuestreo por vecino más cercano que MusMorph no hizo.
- La degradación de resolución es simulada sobre máscaras; no equivale a reescanear.
- Nada humano ni clínico.
