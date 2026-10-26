# Reporte de verificación técnica — Geometría de la Vida v3.0

**Fecha local:** 26 de octubre de 2026.  
**Entorno local:** Linux x86_64, Python 3.13.5, pytest 9.0.2, NumPy 2.3.5, pandas 2.2.3, SciPy 1.17.0 y scikit-image 0.26.0.  
**Datos evaluados:** cuatro máscaras sintéticas creadas por el proyecto; ninguna imagen embrionaria humana real.

## Cambios implementados

1. Se añadió src/advanced_morphology.py con siete momentos invariantes de Hu, sus transformaciones signed-log y análisis de sensibilidad al umbral.
2. Se añadió load_grayscale_image para cargar y normalizar la imagen antes de medirla a varios umbrales.
3. src/analyze_manifest.py añade los descriptores Hu y habilita sensibilidad con --sensitivity y --sensitivity-thresholds.
4. El resumen informa topología más frecuente, estados topológicos, coeficientes de variación, niveles fallidos y robustness_index exploratorio.
5. Se añadieron pruebas para invariancia de Hu, componente mayor, umbrales estables/vacíos e integración por manifiesto.
6. GitHub Actions ejecutará el flujo avanzado además de las pruebas y auditoría actuales.

## Resultados locales observados

| Comprobación | Resultado |
|---|---|
| python -m pytest tests -v | **43 aprobadas, 0 fallidas** |
| Demo sintética y PCA | Ejecutadas; 4 observaciones sintéticas |
| Auditoría del dataset de demostración | ok=true, sin bloqueos de metadatos |
| Análisis avanzado por manifiesto | 4 filas, 0 errores base y 0 errores de sensibilidad |
| Umbrales por observación | 5 intentos, 5 máscaras válidas y 0 fallidas en cada forma sintética |
| Estabilidad sintética | Índice 100 y estabilidad topológica 1.0 en las cuatro formas, porque los umbrales generaron la misma máscara |

## Comando reproducible

```bash
python -m pytest tests -v
python src/demo_pipeline.py
python src/audit_dataset.py demo/synthetic_morphology.csv --out demo/synthetic_audit.json --strict
python src/create_synthetic_manifest.py
python -m src.analyze_manifest demo/synthetic_manifest.csv --out demo/synthetic_mask_metrics.csv --sensitivity --sensitivity-thresholds 0.3,0.4,0.5,0.6,0.7 --strict
```

## Interpretación

El índice combina con pesos iguales la estabilidad topológica y la estabilidad de varias medidas continuas. Es una señal exploratoria de sensibilidad computacional. **No es una probabilidad, intervalo de confianza, estimación validada de calidad anatómica ni prueba del desarrollo embrionario.** Una segmentación incorrecta puede permanecer estable en todos los umbrales; por eso, una revisión anatómica independiente sigue siendo necesaria.

La documentación de scikit-image describe los momentos de Hu como invariantes en teoría ante traslación, escala y rotación, pero la discretización y el contorno segmentado pueden causar desviaciones. Referencia: https://scikit-image.org/docs/stable/api/skimage.measure.html#skimage.measure.moments_hu

## Pendiente antes de conclusiones biológicas

- Confirmar la ejecución remota de GitHub Actions para v3.0.
- Verificar instalación en Windows o Codespaces del equipo.
- Verificar procedencia, condiciones de uso y escala de cada imagen biológica.
- Validar la segmentación anatómica con criterios documentados y revisión apropiada.
- Cuantificar sensibilidad a resolución y conectividad, además del umbral.
- Tratar múltiples imágenes del mismo espécimen como medidas dependientes.

**Conclusión técnica local:** la v3.0 añade descriptores invariantes y sensibilidad reproducible, verificados con 43 pruebas y cuatro formas sintéticas. No hay validación de la hipótesis biológica.
