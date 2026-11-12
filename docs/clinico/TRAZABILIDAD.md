# Trazabilidad: hipótesis → preregistro → código → pruebas → resultados

> Cada fila enlaza una pregunta con los archivos donde se fijó, se implementó, se probó y se
> respondió. Una prueba automática (`tests/test_traceability.py`) comprueba que todos los archivos
> citados con comillas inversas en las tablas existen. **Eso verifica que los archivos existen, no que
> los resultados sean correctos ni que el software sea seguro.**
>
> Los veredictos no se copian aquí para que no puedan divergir de su fuente: están en el documento de
> resultados de cada fila.

## Matriz

| ID | Pregunta (resumida) | Preregistro | Código | Pruebas | Resultados |
|---|---|---|---|---|---|
| H1 | ¿Cuántos vóxeles hacen falta para medir volumen y topología? | `docs/PREREGISTRO_H1.md` | `src/geovida/experiment.py`, `src/geovida/imaging.py`, `src/geovida/phantoms.py`, `src/geovida/measure.py`, `scripts/run_h1.py`, `scripts/analyze_h1.py` | `tests/test_experiment.py`, `tests/test_imaging.py`, `tests/test_phantoms.py`, `tests/test_measure.py` | `docs/RESULTADOS.md`, `results/summary/h1_verdicts.json` |
| H2 | ¿Cuánto distorsiona una trayectoria 4D el error de estadificación? | `docs/PREREGISTRO_H2.md` | `src/geovida/traj4d.py`, `scripts/run_h2.py`, `scripts/analyze_h2.py` | `tests/test_traj4d.py` | `docs/RESULTADOS.md`, `results/summary/h2_verdicts.json` |
| H3, H4 | ¿Predice mejor V/(S·h) que el grosor? ¿Sirve el estimador de área por distancia con signo? | `docs/PREREGISTRO_H3.md` | `src/geovida/h3.py`, `scripts/run_h3.py`, `scripts/analyze_h3.py`, `scripts/freeze_h3_models.py` | `tests/test_h3.py` | `docs/RESULTADOS_V02.md`, `results/summary/h3_verdicts.json` |
| H5 | Prueba de estrés 2D tipo ecografía (moteado 2D) | `docs/PREREGISTRO_2D.md` | `src/geovida/twod.py`, `src/geovida/h5.py`, `scripts/run_2d.py`, `scripts/analyze_2d.py` | `tests/test_twod.py`, `tests/test_h5.py` | `docs/RESULTADOS_V02.md`, `results/summary/h5_verdicts.json` |
| H6 | ¿Sabe el instrumento cuándo la resolución no alcanza para el volumen? | `docs/PREREGISTRO_H6.md` | `src/geovida/h6.py`, `src/geovida/budget.py`, `scripts/run_h6.py`, `scripts/calibrate_h6.py`, `scripts/analyze_h6.py` | `tests/test_h6.py`, `tests/test_budget.py` | `docs/RESULTADOS_V03.md`, `results/summary/h6_verdicts.json`, `results/summary/h6_frozen_models.json` |
| H7 | Limpieza 2D que escala con el objeto | `docs/PREREGISTRO_H7.md` | `src/geovida/h7.py`, `scripts/run_h7.py`, `scripts/analyze_h7.py` | `tests/test_h7.py` | `docs/RESULTADOS_V03.md`, `results/summary/h7_verdicts.json` |
| H8 | El semáforo en la estimación de crecimiento 4D | `docs/PREREGISTRO_H8.md` | `src/geovida/growth.py`, `scripts/run_h8.py`, `scripts/analyze_h8.py` | `tests/test_growth.py` | `docs/RESULTADOS_V03.md`, `results/summary/h8_verdicts.json` |
| H9, H10 | Semáforo de topología y guardia de dominio | `docs/PREREGISTRO_H9_H10.md` | `src/geovida/h9.py`, `src/geovida/certsweep.py`, `src/geovida/topomargin.py`, `src/geovida/scaleaxis.py`, `src/geovida/domain.py`, `src/geovida/certificate.py`, `scripts/run_h9.py`, `scripts/calibrate_h9.py`, `scripts/analyze_h9.py` | `tests/test_h9.py`, `tests/test_certsweep.py`, `tests/test_topomargin.py`, `tests/test_scaleaxis.py`, `tests/test_domain.py`, `tests/test_certificate.py`, `tests/test_logit_multi.py` | `docs/RESULTADOS_V04.md`, `results/summary/h9_verdicts.json`, `results/summary/h9_frozen.json` |
| H11 | ¿Transfiere el certificado congelado a ecografía 3D real de ratón? | `docs/PREREGISTRO_H11.md` | `src/geovida/realdata.py`, `src/geovida/h11.py`, `scripts/real_datasheet.py`, `scripts/run_h11.py` | `tests/test_realdata.py`, `tests/test_h11.py` | **Pendiente de datos reales** (código y criterios listos; probados solo con volúmenes sintéticos) |
| H12R | ¿Transfiere a ecografía real de ratón el certificado recalibrado con ecografía simulada? | `docs/PREREGISTRO_H12R.md` | `src/geovida/h11.py`, `scripts/run_h11.py` | `tests/test_h11.py` | **Pendiente de datos reales** (preregistrado antes de abrir ningún dato) |
| H12 | ¿Se puede recalibrar para ecografía 3D simulada con moteado y atenuación? | `docs/PREREGISTRO_H12.md` | `src/geovida/h12.py`, `src/geovida/imaging.py`, `scripts/run_h12.py`, `scripts/calibrate_h12.py`, `scripts/analyze_h12.py` | `tests/test_h12.py`, `tests/test_ultrasound.py` | `docs/RESULTADOS_V05.md`, `results/summary/h12_verdicts.json`, `results/summary/h12_frozen.json` |
| H13 | ¿Se puede certificar una biometría temprana (edad por CRL, lado de un umbral de NT) con la incertidumbre propagada hasta la decisión? Todo simulado | `docs/PREREGISTRO_H13.md` | `src/geovida/biometry.py`, `src/geovida/dating.py`, `src/geovida/atlas.py`, `src/geovida/labeling.py`, `src/geovida/h13.py`, `scripts/run_h13.py`, `scripts/analyze_h13.py`, `scripts/figure_h13.py` | `tests/test_biometry.py`, `tests/test_dating.py`, `tests/test_atlas.py`, `tests/test_h13.py`, `tests/test_labeling.py` | `docs/RESULTADOS_V06.md`, `results/summary/h13_verdicts.json`, `results/summary/h13_frozen.json`, `results/summary/h13_strata.csv`. Criterios agregados apoyados; estrato de ranura con PSF > 3.5 px no fiable (exploratorio) |
| H14 | ¿Una compuerta de «tasa de medidas utilizables» arregla el fallo de la ranura con PSF ancha? Todo simulado | `docs/PREREGISTRO_H14.md` | `src/geovida/h14.py`, `src/geovida/biometry.py`, `scripts/run_h14.py`, `scripts/analyze_h14.py` | `tests/test_h14.py`, `tests/test_biometry.py` | `docs/RESULTADOS_V06.md`, `results/summary/h14_verdicts.json`, `results/summary/h14_frozen.json`, `results/summary/h14_strata.csv`. Cinco criterios apoyados con semilla nueva; H14a se cumple por construcción (la compuerta no emite verdes en ese estrato) y el costo es 12 % de los verdes de la ranura |
| REAL2D | Piloto n = 1: medida de una longitud en una ecografía 2D real con escala impresa (exploratorio) | `docs/PREREGISTRO_REAL2D_PILOTO.md` | `src/geovida/real2d.py`, `src/geovida/cli.py`, `docs/REAL2D_METODO.md` | `tests/test_real2d.py` | **Pendiente de la imagen** (código y protocolo listos; sin imagen real medida; informes fuera del repositorio) |
| H15 | ¿Resiste el certificado una imagen que pasó por pantalla, impresión y foto? Todo simulado | `docs/PREREGISTRO_H15.md` | `src/geovida/printchain.py`, `src/geovida/h15.py`, `src/geovida/biometry.py`, `scripts/run_h15.py`, `scripts/analyze_h15.py`, `scripts/figure_h15.py` | `tests/test_printchain.py`, `tests/test_h15.py` | `docs/RESULTADOS_V07.md`, `results/summary/h15_verdicts.json`, `results/summary/h15_conf_manifest.json`, `results/summary/h15_compression_terciles.csv`, `docs/figures/h15_chain.png` |
| Informe por medida | Procedencia de cada certificado | — | `src/geovida/cli.py`, `src/geovida/provenance.py` | `tests/test_cli.py`, `tests/test_provenance.py` | — |

## Errores propios

Todo error encontrado se documenta con su causa y su prevención en `docs/ERRATA.md`. No se borra ni se
reescribe la historia: una cifra equivocada se corrige y el error queda a la vista.

## Cómo se comprueba que un resultado se puede reproducir

1. Cada barrido guarda un manifiesto (por ejemplo `results/summary/h9_test_manifest.json`) con el commit, si el código estaba limpio,
   la semilla, el número de filas y las versiones de los paquetes.
2. Los modelos congelados están versionados (`results/summary/h9_frozen.json`; el de H12 es
   `results/summary/h12_frozen.json`) y el paquete lleva una copia del de v0.4 que una prueba compara
   con el original.
3. `geovida certify --report` imprime las huellas SHA-256 de la imagen y de la calibración usadas.
