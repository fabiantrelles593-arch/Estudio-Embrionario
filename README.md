# Geometría de la Vida — v3.0 (capa avanzada de morfología)

**Propósito:** modelar transformaciones morfológicas mediante descriptores geométricos, topológicos y de forma, e inspeccionar la sensibilidad de las medidas a decisiones de segmentación.

**Verificación local y remota:** 43 pruebas aprobadas localmente y 43 aprobadas por GitHub Actions en Python 3.12 y 3.13. El pipeline avanzado procesó cuatro máscaras sintéticas sin errores. [Ver ejecución CI](https://github.com/fabiantrelles593-arch/Estudio-Embrionario/actions/runs/40319218654).

## Nuevo en v3.0
- Momentos invariantes de Hu: siete descriptores en valores originales y transformación signed-log.
- Perfil de sensibilidad: repite las medidas en varios umbrales, resume variación geométrica y detecta cambios topológicos.
- Índice exploratorio de robustez: combina estabilidad topológica y continuidad de medidas; no es una probabilidad ni una medida validada de exactitud anatómica.
- Pruebas adicionales para invariancia, umbrales vacíos/estables, errores de sensibilidad e integración por manifiesto.

## Estado científico
Las demostraciones usan máscaras sintéticas, no imágenes embrionarias humanas. No se afirma que la hipótesis biológica esté validada. La contribución requiere revisión de literatura y comparación con métodos existentes. La fuente de imágenes, sus condiciones de uso, los metadatos y la segmentación anatómica deben confirmarse antes de la etapa biológica.

## Módulos
- src/metrics_2d.py: medidas geométricas y topológicas 2D.
- src/advanced_morphology.py: momentos de Hu y sensibilidad al umbral.
- src/analyze_manifest.py: auditoría, métricas y sensibilidad opcional desde manifiesto.
- src/image_io.py: carga de escala de grises y máscara binaria.
- src/audit_dataset.py: auditoría de procedencia, etapa, identificadores, calidad y uso.
- src/morphology_space.py: estandarización, PCA exploratorio y matriz de distancias.
- tests/: pruebas automáticas.
- docs/27_CAPA_AVANZADA_ROBUSTEZ_MORFOLOGICA.md: método, fórmulas, límites y referencias.
- docs/28_REPORTE_DE_VERIFICACION_V3_0.md: informe local y remoto.

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

En las figuras sintéticas todos los umbrales producen la misma máscara, así que el índice sale 100. Eso valida un caso de control, no la precisión de segmentación biológica.

## Interpretación
- Hu 1–7: momentos de Hu originales; hu_log 1–7: transformación signed-log.
- topology_stability: proporción de umbrales válidos que comparten la topología más frecuente.
- *_cv: coeficientes de variación entre umbrales.
- topology_states: cantidad de parejas topológicas distintas (beta0, beta1).
- robustness_index: índice exploratorio de 0 a 100.
- sensitivity_flags y threshold_sensitivity_json: avisos y resultados detallados por observación.

analysis_status=OK solo indica que la máscara del umbral principal se pudo medir. Un índice de robustez alto no demuestra exactitud anatómica; la segmentación debe validarse aparte.

## Estado en GitHub
- Rama v3.0: development/v3.0-advanced-morphology.
- [PR #2 — v3.0](https://github.com/fabiantrelles593-arch/Estudio-Embrionario/pull/2), abierta contra la rama de v2.5.
- [Integración continua verificada](https://github.com/fabiantrelles593-arch/Estudio-Embrionario/actions/runs/40319218654).

La PR #2 no está fusionada. La integración final debe seguir el orden documentado en Notion: revisar v2.5 y después v3.0.
