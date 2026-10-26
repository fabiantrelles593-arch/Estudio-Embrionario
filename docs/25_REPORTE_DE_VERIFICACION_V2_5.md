# Reporte de verificación técnica — Geometría de la Vida v2.5

**Fecha de ejecución:** 25 de octubre de 2026  
**Entorno verificado:** Linux, Python 3.13.5, pytest 9.0.2, NumPy 2.3.5, SciPy 1.17.0, scikit-image 0.26.0, pandas 2.2.3.  
**Tipo de material evaluado:** código y ejemplos sintéticos creados para pruebas; no se usaron imágenes embrionarias reales.

## Cambios verificados

- Se añadió `src/analyze_manifest.py` para conectar un CSV con rutas de imágenes, auditar metadatos, convertir imágenes en máscaras, calcular métricas y preservar errores por observación.
- Se añadió `src/create_synthetic_manifest.py` para generar un manifiesto reproducible a partir de cuatro máscaras sintéticas.
- Se fortaleció la auditoría para que los ejemplos sintéticos usen `stage=not_applicable`, en vez de asignarles etapas Carnegie ficticias. Los registros biológicos siguen requiriendo etapas enteras dentro de CS12–CS18.
- Se añadieron casos de prueba para escala física, escala desconocida, imagen ausente, estado de permiso pendiente, escala inválida y columna `image_path` ausente.
- Se amplió el workflow de GitHub Actions para ejecutar el pipeline con manifiesto y guardar los resultados sintéticos como artefacto.
- La configuración de `.devcontainer` y `.vscode/extensions.json` mantiene declaradas las extensiones recomendadas para el entorno de desarrollo.

## Resultados observados en esta ejecución

| Comprobación | Resultado |
|---|---|
| `python -m pytest tests -v` | **30 pruebas aprobadas, 0 fallidas** |
| `python src/demo_pipeline.py` | Ejecutado correctamente; produjo tabla morfológica, proyección PCA y matriz de distancias sintéticas |
| Auditoría de `demo/synthetic_morphology.csv` con `--strict` | `ok: true`, 4 filas, 4 especímenes sintéticos, sin IDs duplicados, campos obligatorios ausentes, etapas inválidas, estado de licencia pendiente ni banderas de calidad no aceptadas |
| Creación del manifiesto sintético | 4 observaciones generadas con `stage=not_applicable` |
| `python -m src.analyze_manifest ... --strict` | 4 filas analizadas, 4 con estado `OK`, 0 errores de procesamiento |
| Escala física de prueba | 42 píxeles con tamaño lineal de 0,25 unidades/píxel produjeron área 2,625 unidades², coherente con 42 × 0,25² |

## Qué significa y qué no significa el resultado

Las pruebas y la demostración muestran que, en este entorno, las funciones responden como se espera a entradas sintéticas controladas. `OK` significa que la máscara se pudo medir; no confirma que la segmentación sea anatómicamente correcta. La auditoría verifica campos y reglas programadas, pero no certifica una licencia por sí sola ni confirma que los metadatos sean verdaderos.

## Verificaciones pendientes

- Ejecutar la instalación y los comandos en el ordenador Windows del equipo.
- Confirmar el resultado real de GitHub Actions en un repositorio accesible. La conexión revisada no devolvió repositorios accesibles, así que el workflow no se ha ejecutado remotamente.
- Seleccionar imágenes biológicas con procedencia, etapas, condiciones de uso y escala documentadas.
- Definir y validar el método de segmentación anatómica con supervisión experta antes de interpretar resultados biológicos.
- Separar observaciones del mismo espécimen de unidades experimentales independientes.

**Verificación del paquete:** después de crear el ZIP, se extrajo en una carpeta limpia y se repitieron las 30 pruebas, la demo, la auditoría y el analizador de manifiesto; las 30 pruebas aprobaron y el analizador volvió a producir 4 filas con 0 errores.

**Conclusión técnica limitada:** versión 2.5 verificada con 30 pruebas automatizadas y una demostración end-to-end de datos sintéticos en este entorno. No existe todavía validación biológica de la hipótesis.
