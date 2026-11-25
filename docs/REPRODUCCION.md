# Manual de reproducción — estudios con datos reales (23 nov 2026)

> Cómo rehacer, desde cero y en otro equipo, cada estudio con datos reales de Geometría de la Vida: entorno,
> descarga con comprobación de integridad, orden de los pasos y cómo comprobar que el código es el mismo que produjo
> los resultados publicados. Los estudios solo con datos sintéticos (H1–H10, H12–H16, H21, H22) se reproducen con
> las órdenes del `README.md` y de cada preregistro.
> **Solo investigación con datos animales publicados.** Nada humano ni clínico. Ningún dato, peso de red ni
> resultado bruto está en git (`data/` y `results/` fuera del repositorio salvo `results/summary/`).
> Etiquetas: [HV] verificado · [PV] pendiente de validación.

## 1. Entorno

Versiones con las que se produjeron los resultados de noviembre de 2026 [HV, entorno local]: Python 3.13.17,
NumPy 2.5.4, SciPy 1.18.1, scikit-image 0.26.0, pandas 3.1.1, SimpleITK 2.5.7, PyTorch 2.15.0 (CPU), MONAI 1.6.1,
nibabel 5.5.0, h5py 3.16.0, pytest 9.2.0. La integración continua prueba Python 3.12 y 3.13 en Ubuntu
(`.github/workflows/ci.yml`).

```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cpu   # primero, para no bajar la versión con CUDA
pip install -e ".[dev]"                                   # incluye nibabel, h5py, SimpleITK y torch
pip install monai                                         # solo para MEMOS en P3 (no está en los extras)
pytest                                                    # 1021 pruebas en 82 archivos (25 nov 2026)
```

Las órdenes se ejecutan desde la raíz del repositorio con `PYTHONPATH=src` si el paquete no está instalado.
Equipo de referencia: 4 núcleos, 3,9 GB de RAM, sin GPU. Los tiempos de cada estudio están en su documento de
resultados; los más largos son P3 confirmatorio y MT-A (decenas de horas). Todos los pasos largos son
reanudables: guardan un archivo por caso y no repiten los que ya existen.

## 2. Datos externos y licencias

| Conjunto | Fuente | Licencia | Cómo se obtiene | Estudios |
|---|---|---|---|---|
| Ecografía 3D de embriones de ratón (Qiu et al. 2021) | IEEE DataPort, DOI 10.21227/drmd-xq36 | CC BY | Descarga **manual** con cuenta gratuita de IEEE DataPort (unos 1,94 GB); ver `docs/GUIA_DATOS_REALES.md` | H11, H12R, H18, H19, H20, H23 |
| MusMorph IMPC, especímenes (imágenes, segmentaciones, landmarks) | FaceBase, registro 3-JZA6 (Devine et al. 2022) | CC BY 4.0 | Automática desde el catálogo público, con MD5 del catálogo (`scripts/p3_pilot.py download`, `scripts/onto_map_pilot.py download`, `scripts/landmark_qc.py download`, `scripts/atlas_effect_gates.py download-images`) | P3, ONTO-MAP, QC-LM, MT-A |
| MusMorph, atlas E15.5 y E18.5 y sus landmarks | FaceBase, registro 6-2EPY | CC BY 4.0 | `scripts/atlas_effect_gates.py download`: exige antes el tamaño y el MD5 fijados en el preregistro | P3 (grupos), MT-A |
| Metadatos de MusMorph | `MusMorph_Metadata_Mar2024.csv`, repositorio de MusMorph (SHA-256 en `docs/p3/RESULTADOS_PILOTO.md`) | La del repositorio | Manual | P3, ONTO-MAP |
| Pesos de MEMOS | Enlace del README de SlicerMEMOS (Rolfe et al. 2023) | **No declarada** | Manual; **solo uso local**, no se redistribuyen ni se publica ninguna salida | P3 (segmentador B) |

Manifiestos SHA-256 de lo descargado: `data/manifests/musmorph_atlas.csv`, `data/manifests/musmorph_mta_images.csv`
y `data/manifests/musmorph_qc_images.csv`. Licencias de otros conjuntos evaluados y no usados:
`docs/estado_del_arte/LICENCIAS_DATOS_EXTERNOS.md`.

## 3. Estudio por estudio

El orden de los pasos es parte del método: cada estudio fija sus criterios en el preregistro antes de medir, y
los pasos que abren la prueba se niegan a correr sin el SHA-256 del modelo congelado anotado en el preregistro.
Reproducir no es volver a decidir: los veredictos se comparan con los publicados, no se recalculan con otros
criterios.

### H11 y H12R — certificado congelado sobre ecografía real

```bash
python scripts/real_datasheet.py data/external/ieee_qiu2021/nii --out results/summary/real_datasheet_qiu2021.json
python scripts/h11_manifest_qiu2021.py results/summary/real_datasheet_qiu2021.json --out results/h11/manifiesto_qiu2021.csv
python scripts/run_h11.py results/h11/manifiesto_qiu2021.csv --root data/external/ieee_qiu2021/nii --tag v04
python scripts/h11_report.py --dir results/summary --out results/h11/informe_h11.md
```

H12R usa el mismo `run_h11.py` con la calibración congelada de H12 (`--frozen`, etiqueta `h12`), y las
sensibilidades de vóxel usan `--relaxed-spacing` al armar el manifiesto. Los argumentos exactos de cada corrida
están en `docs/h11/RESULTADOS_H11.md` y `docs/h11/RESULTADOS_H12R.md`.

### H18, H19 y H20 — calibración con ecografía real y prueba sellada

```bash
python scripts/run_h18.py split    --manifest results/h11/manifiesto_qiu2021.csv
python scripts/run_h18.py develop  --manifest results/h11/manifiesto_qiu2021.csv --root data/external/ieee_qiu2021/nii
python scripts/run_h18.py observe  --manifest ... --root ...
python scripts/run_h18.py freeze   --manifest ...
python scripts/run_h19.py split && python scripts/run_h19.py train-coarse && python scripts/run_h19.py train-fine
python scripts/run_h19.py calibrate
python scripts/run_h20.py g0 && python scripts/run_h20.py calibrate
python scripts/run_h20.py test --sha <SHA-256 anotado en el §10 de docs/h20/PREREGISTRO_H20.md>
python scripts/h20_report.py --dir results/h20 --out results/h20/informe.md
```

H18 y H19 terminaron antes de abrir la prueba (puertas no superadas), así que sus `test` no se ejecutaron. La
prueba se midió **una sola vez**, en H20. Quien reproduzca H20 la mide de nuevo como comprobación de que el código da
lo mismo, no como un nuevo resultado. El entrenamiento de H19 en CPU tiene una parte no determinista (PyTorch):
los pesos pueden no ser idénticos bit a bit [PV]. Por eso `run_h20.py` comprueba el SHA-256 de las redes contra
`results/h19/calibrate.json`.

### H23 — señales de H20 en ventrículos (mismo conjunto)

```bash
python scripts/run_h23.py g0             # G0-escala: solo etiquetas de los casos de ajuste
python scripts/run_h23.py train-coarse   # unas 5 h de CPU
python scripts/run_h23.py train-fine
python scripts/run_h23.py g0-signals
python scripts/run_h23.py calibrate      # puertas S y C; congela si pasan
python scripts/run_h23.py test --sha <SHA-256 anotado en el §11 de docs/h23/PREREGISTRO_H23.md>
```

Cada orden se niega a correr si la puerta anterior no está superada. La medida cuenta todas las piezas de la máscara
(desviación D-1, `h23.segment_all`).

### P3 — variación técnica frente a biológica (MusMorph E15.5)

```bash
python scripts/p3_pilot.py select --metadata MusMorph_Metadata_Mar2024.csv --out results/p3/seleccion.json
python scripts/p3_pilot.py download --ids results/p3/seleccion.json --out data/external/musmorph/impc_e15_5
python scripts/p3_pilot.py check --ids results/p3/seleccion.json --data data/external/musmorph/impc_e15_5 \
    --out results/p3/precheck_piloto.json
python scripts/p3_memos.py run --model data/external/memos/model/best_metric_model_largePatch_noise.pth \
    --data data/external/musmorph/impc_e15_5 --ids results/p3/seleccion.json --out results/p3/memos
python scripts/p3_analyze.py groups --atlas data/external/musmorph/atlas/IMPC_E15.5_Body_Atlas_Segs.mnc \
    --out results/p3/grupos.csv
python scripts/p3_analyze.py pilot --data data/external/musmorph/impc_e15_5 --memos results/p3/memos \
    --groups results/p3/grupos.csv --out results/p3/analisis_piloto.json
```

El confirmatorio (`p3_analyze.py confirm`) y el exploratorio ×4 siguen las desviaciones D1–D6 de
`docs/PREREGISTRO_P3.md`; sus órdenes y tiempos están en `docs/p3/RESULTADOS_P3.md`.

### ONTO-MAP (P4) — alometría frente a cambio entre estadios

```bash
python scripts/onto_map_pilot.py select --metadata MusMorph_Metadata_Mar2024.csv --out results/onto_map/seleccion.json
python scripts/onto_map_pilot.py download --ids results/onto_map/seleccion.json --which pilot --out data/external/musmorph/landmarks
python scripts/onto_map_pilot.py check --ids results/onto_map/seleccion.json --which pilot \
    --data data/external/musmorph/landmarks --out results/onto_map/precheck_piloto.json
python scripts/onto_map_pilot.py analyze --ids results/onto_map/seleccion.json --which confirm \
    --data data/external/musmorph/landmarks_confirm --out results/onto_map/analisis.json
```

### QC-LM — control de calidad de los landmarks publicados

```bash
python scripts/landmark_qc.py select --ids results/onto_map/seleccion.json --out results/landmark_qc/muestra.json
python scripts/landmark_qc.py download --sample results/landmark_qc/muestra.json --out data/external/musmorph/qc_images
python scripts/landmark_qc.py measure --sample results/landmark_qc/muestra.json --out results/landmark_qc/medidas
python scripts/landmark_qc.py analyze --sample results/landmark_qc/muestra.json \
    --measures results/landmark_qc/medidas --out results/landmark_qc/analisis.json
```

### MT-A — efecto del atlas (v1.0, v1.1 y v2)

Puertas y descarga (v1.0): `scripts/atlas_effect_gates.py` con `g0d`, `download`, `g0c`, `download-images`, `g0a`
y `g0b` (cabecera del script). v1.1: `g0b2` y `g0a2`. v2:

```bash
python scripts/mta_v2.py sample && python scripts/mta_v2.py selection
python scripts/mta_v2.py g0a3
python scripts/atlas_effect_gates.py g0d --ids results/morpho_trace/v2/seleccion_v2.json \
    --data data/external/musmorph/landmarks_confirm --out results/morpho_trace/v2/g0d2.json
python scripts/mta_v2.py g0t
python scripts/atlas_effect_gates.py register --ids results/morpho_trace/v2/seleccion_v2.json \
    --images data/external/musmorph/qc_images --regs results/morpho_trace/v2/registros
python scripts/atlas_effect_gates.py analyze --protocol 2.0 --ids results/morpho_trace/v2/seleccion_v2.json \
    --landmarks data/external/musmorph/landmarks_confirm --regs results/morpho_trace/v2/registros \
    --gates-dir results/morpho_trace/v2 --out results/morpho_trace/v2/analisis.json
python scripts/explore_mta_v2_g1.py      # diagnóstico exploratorio de G1 (no cambia el veredicto)
# verificación de la cadena de registro (nota de ingeniería, docs/morpho_trace/VERIFICACION_REGISTRO.md)
python scripts/verify_registration_chain.py synthetic                                   # unos 25 min
python scripts/verify_registration_chain.py specimens --names IMPC_E15.5_0313 IMPC_E18.5_1284   # unas 1,6 h
python scripts/verify_registration_chain.py geometry --names IMPC_E15.5_0313 IMPC_E18.5_1284    # unos minutos
# MT-A v3 (docs/morpho_trace/PREREGISTRO_ATLAS_v3.md); cada orden se niega a seguir si falla una puerta anterior
python scripts/mta_v3.py sample        # una sola vez: 2 + 2 de piloto y 18 + 18 confirmatorios
python scripts/mta_v3.py g0a4
python scripts/mta_v3.py g0m
python scripts/mta_v3.py pilot         # puerta S: 12 registros de cabeza
python scripts/mta_v3.py g0t           # G0-t′ y sensibilidad 1
python scripts/mta_v3.py own           # G1′: 36 registros propios
python scripts/mta_v3.py cross         # 36 registros cruzados, solo si G1′ pasó
python scripts/mta_v3.py analyze
# MT-B (docs/morpho_trace/PREREGISTRO_ANCLAJE_ATLAS.md): sin registro ni descargas, unos 3 min en total
python scripts/mtb_anclaje.py gates    # G0-d‴, G0-p, G0-t
python scripts/mtb_anclaje.py analyze  # MT-B1–MT-B3 y sensibilidad; se niega si las puertas no pasaron
# MT-C (docs/morpho_trace/PREREGISTRO_HOMOLOGOS.md): G0-o compara con los .tag de atlas del repositorio MusMorph
# en data/external/musmorph/atlas_github/ (SHA-256 en §11 del preregistro); unos 2 min en total
python scripts/mtc_homologos.py gates
python scripts/mtc_homologos.py analyze
# MT-D (docs/morpho_trace/PREREGISTRO_ANOTACION_MANUAL.md): los puntos manuales los coloca una persona en 3D Slicer.
# prepare exporta 18 volúmenes NIfTI y el fantoma a data/manual/mtd/ (unos 1 GB, 1,5 min) y escribe la hoja de sesiones
python scripts/mtd_anotacion.py prepare
python scripts/mtd_anotacion.py templates    # plantillas de Slicer con las etiquetas puestas (sin reexportar)
python scripts/mtd_anotacion.py gates-pre    # G0-e y G0-c; G0-c necesita data/manual/mtd/annotations/P0000.mrk.json
python scripts/mtd_anotacion.py gates-post   # G0-ε y G0-r, con las anotaciones de los atlas
python scripts/mtd_anotacion.py analyze
```

Las imágenes humanas (FI-1, `docs/prenatal/PREREGISTRO_FOTO_IMPRESION.md`) **no se pueden reproducir desde el
repositorio**: no están en él y solo se usan con las condiciones de `docs/DATOS_REALES_Y_ETICA.md` §3. La
anonimización se hace en local con `python scripts/anonimizar_imagen.py preview|apply ...`, que solo escribe en
`data/private/`. Después, `python scripts/fi1_foto_impresion.py plan|gates|analyze`. Las tres órdenes se niegan a
hacer nada sin un registro completo de G0-ética en `data/private/ecografia/g0_etica.json`.

Los 80 registros de v2 tardaron 22,9 h de cálculo en el equipo de referencia. Si el proceso se corta, se relanza
la misma orden y continúa donde quedó.

## 4. Comprobar que el código es el mismo

Cada análisis guarda en su salida una huella del código (`provenance.code_fingerprint`): el blob de git de cada
archivo de `src/` y `scripts/` y de `pyproject.toml`, con finales de línea LF. Para comparar una salida con una
versión del repositorio:

```python
from geovida.provenance import code_fingerprint, compare_fingerprint
# huella = el campo provenance.code_fingerprint del JSON de salida
# arbol  = {ruta: sha del blob} de un commit, p. ej. de la API de GitHub (git/trees/<sha>?recursive=1)
#          o del código local: code_fingerprint(".")["files"]
compare_fingerprint(huella, arbol)   # {"match": [...], "differ": [...], "missing": [...]}
```

Los documentos de resultados citan además los blobs de los archivos clave (por ejemplo, MT-A v2:
`atlas_effect_gates.py` fb4a869, `mta_v2.py` 401f7d1, `atlas_effect.py` 9369540). Un blob distinto no invalida
la reproducción, pero obliga a explicar la diferencia antes de comparar resultados.

## 5. Qué no garantiza este manual

* Que los conjuntos externos sigan disponibles ni que sus archivos no cambien. Los MD5 y SHA-256 registrados
  permiten detectar el cambio, no evitarlo.
* Identidad bit a bit en los pasos con PyTorch o con muestreo aleatorio de SimpleITK, que dependen de la plataforma
  [PV]. Las semillas están fijadas, pero esa reproducibilidad entre plataformas no se ha comprobado.
* Nada sobre uso clínico ni sobre datos humanos.
