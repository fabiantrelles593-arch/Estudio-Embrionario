# Geometría de la Vida — v3.0 (capa avanzada de morfología)

**Propósito:** modelar transformaciones morfológicas con descriptores geométricos, topológicos y de forma, e inspeccionar la sensibilidad de los resultados a decisiones de segmentación.

**Verificación local v3.0:** 43 pruebas automatizadas aprobadas en Python 3.13.5; el flujo avanzado procesa cuatro máscaras sintéticas sin errores. La verificación remota de CI para esta versión aún debe confirmarse.

## Nuevo en v3.0

- **Momentos invariantes de Hu:** siete descriptores calculados sobre la componente mayor, en valores originales y forma signed-log.
- **Perfil de sensibilidad a umbrales:** repite la medición a varios niveles, resume variación de área/perímetro/forma, detecta cambios topológicos y conserva intentos fallidos.
- **Índice exploratorio de robustez:** resume consistencia topológica y estabilidad de descriptores continuos mediante una fórmula explícita. No es una probabilidad ni mide exactitud anatómica.
- **Pruebas adicionales:** invariancia de Hu en formas rasterizadas, sensibilidad con umbrales estables, máscaras vacías e integración del análisis avanzado desde el manifiesto.

## Estado científico

Las demostraciones usan formas sintéticas. No se han usado imágenes embrionarias humanas reales y no se afirma que la hipótesis biológica esté validada. La contribución requiere revisión bibliográfica y comparación con métodos existentes. La fuente de imágenes, sus condiciones de uso, los metadatos y la segmentación anatómica deben confirmarse antes de la etapa biológica.

## Módulos

- src/metrics_2d.py: descriptores geométricos y topológicos 2D.
- src/advanced_morphology.py: momentos invariantes de Hu y perfil de sensibilidad al umbral.
- src/analyze_manifest.py: auditoría, análisis por manifiesto, momentos Hu y sensibilidad opcional.
- src/image_io.py: lectura de imagen en escala de grises y creación de máscara binaria.
- src/audit_dataset.py: auditoría de trazabilidad, etapas, IDs, calidad y estado de uso.
- src/morphology_space.py: estandarización, PCA exploratorio y matriz de distancias.
- src/demo_pipeline.py: dataset, PCA y distancias con formas sintéticas.
- tests/: pruebas automáticas de módulos e integración.
- docs/27_CAPA_AVANZADA_ROBUSTEZ_MORFOLOGICA.md: método, fórmulas, límites y referencias.
- docs/28_REPORTE_DE_VERIFICACION_V3_0.md: reporte de las 43 pruebas y la demostración avanzada.

## Instalación y prueba en Windows / VS Code

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest tests -v
```

## Ejecutar la demo avanzada

```powershell
python src/demo_pipeline.py
python src/audit_dataset.py demo/synthetic_morphology.csv --out demo/synthetic_audit.json --strict
python src/create_synthetic_manifest.py
python -m src.analyze_manifest demo/synthetic_manifest.csv --out demo/synthetic_mask_metrics.csv --sensitivity --sensitivity-thresholds 0.3,0.4,0.5,0.6,0.7 --strict
```

Las formas binarias sintéticas mantienen su máscara con estos cinco umbrales; en ese escenario controlado, el índice puede ser 100. Esto no demuestra que el método pueda delimitar correctamente tejido biológico.

## Interpretación

- hu_1…hu_7: momentos de Hu originales; hu_log_1…hu_log_7: transformación signed-log para comprimir el rango.
- topology_stability: proporción de umbrales válidos que comparte la topología más frecuente.
- *_cv: coeficientes de variación a través de los umbrales válidos.
- topology_states: número de topologías (β₀, β₁) diferentes encontradas.
- robustness_index: índice exploratorio entre 0 y 100; consulta el documento técnico antes de interpretarlo.
- sensitivity_flags: avisos si una máscara no se pudo medir, hay pocos niveles válidos o cambia la topología.
- threshold_sensitivity_json: resultados detallados de cada umbral por observación.

analysis_status=OK solo indica que la máscara del umbral principal se pudo medir. Un índice de robustez alto tampoco demuestra exactitud anatómica; la segmentación debe validarse por separado.

## Limitaciones y siguientes pasos

La topología actual usa conectividad 8 en 2D. La segmentación de intensidad asume objeto más brillante que el fondo. Los momentos de Hu usan la componente mayor, mientras que área y perímetro describen todas las componentes. Estas decisiones deben mantenerse explícitas al comparar casos.

Próximas etapas: analizar sensibilidad a resolución y conectividad, definir anatomía y reglas de segmentación con revisión experta, seleccionar un conjunto biológico autorizado y comparable, y evitar tratar varias secciones del mismo espécimen como individuos independientes.
