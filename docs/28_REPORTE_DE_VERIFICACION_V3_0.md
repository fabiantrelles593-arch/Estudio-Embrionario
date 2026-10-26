# Reporte de verificación técnica — Geometría de la Vida v3.0

**Fecha:** 26 de octubre de 2026.  
**Entorno local:** Linux x86_64, Python 3.13.5, pytest 9.0.2, NumPy 2.3.5, pandas 2.2.3, SciPy 1.17.0 y scikit-image 0.26.0.  
**Datos analizados:** cuatro máscaras sintéticas; no se usaron imágenes embrionarias humanas reales.

## Cambios implementados

1. Se añadieron siete momentos invariantes de Hu y transformaciones signed-log.
2. Se incorporó lectura compartida en escala de grises y análisis de sensibilidad en varios umbrales.
3. El análisis por manifiesto incluye medidas de Hu, estabilidad topológica, coeficientes de variación, niveles fallidos y el índice exploratorio de robustez.
4. El modo estricto falla si se produce un error base o de sensibilidad.
5. Se ampliaron las pruebas de invariancia, umbrales inválidos, máscaras vacías e integración.
6. GitHub Actions ejecuta la capa avanzada además de pruebas, demo y auditoría.

## Pruebas locales observadas

| Comprobación | Resultado |
|---|---|
| `python -m pytest tests -v` | **43 aprobadas, 0 fallidas** |
| Demo sintética y PCA | Ejecutadas; 4 observaciones sintéticas |
| Auditoría de la demo | `ok=true`, sin bloqueos de metadatos |
| Análisis avanzado por manifiesto | 4 filas, 0 errores base y 0 errores de sensibilidad |
| Perfil por observación | 5 umbrales intentados; 5 válidos y 0 fallidos en cada máscara |
| Estabilidad sintética | Índice 100 y estabilidad topológica 1.0 porque los umbrales generan la misma máscara |

## Integración continua remota — GitHub Actions

La ejecución [Python tests v3.0](https://github.com/fabiantrelles593-arch/Estudio-Embrionario/actions/runs/40319218654) terminó correctamente.

| Entorno | Pruebas | Pipeline avanzado |
|---|---|---|
| Python 3.12 | **43 aprobadas, 0 fallidas** | 4 máscaras analizadas; 0 errores base y 0 errores de sensibilidad |
| Python 3.13 | **43 aprobadas, 0 fallidas** | 4 máscaras analizadas; 0 errores base y 0 errores de sensibilidad |

GitHub generó los artefactos `synthetic-demo-py3.12` y `synthetic-demo-py3.13`. Solo contienen salidas sintéticas.

Los cambios están en la rama `development/v3.0-advanced-morphology` y en la [PR #2](https://github.com/fabiantrelles593-arch/Estudio-Embrionario/pull/2), abierta contra la rama `development/v2.5-manifest-pipeline`. La PR sigue abierta y no se ha fusionado.

## Comando reproducible

```bash
python -m pytest tests -v
python src/demo_pipeline.py
python src/audit_dataset.py demo/synthetic_morphology.csv --out demo/synthetic_audit.json --strict
python src/create_synthetic_manifest.py
python -m src.analyze_manifest demo/synthetic_manifest.csv --out demo/synthetic_mask_metrics.csv --sensitivity --sensitivity-thresholds 0.3,0.4,0.5,0.6,0.7 --strict
```

## Interpretación

El índice combina con pesos iguales la estabilidad topológica y la estabilidad de medidas continuas a través de los umbrales seleccionados. Es una señal exploratoria de sensibilidad computacional. **No es una probabilidad, intervalo de confianza, estimación validada de calidad anatómica ni prueba de desarrollo embrionario.** Una segmentación puede estar mal delimitada y aun así mantenerse estable entre umbrales; por eso hace falta revisión anatómica independiente.

Los momentos de Hu son invariantes en teoría ante traslación, escala y rotación, pero la discretización y el contorno segmentado pueden generar desviaciones. Referencia: [documentación oficial de scikit-image](https://scikit-image.org/docs/stable/api/skimage.measure.html#skimage.measure.moments_hu).

## Pendiente antes de conclusiones biológicas

- Verificar la instalación en Windows o Codespaces del equipo.
- Confirmar procedencia, condiciones de uso y escala de las imágenes biológicas que se seleccionen.
- Validar la segmentación anatómica con criterios documentados y revisión apropiada.
- Cuantificar sensibilidad a resolución y conectividad, además del umbral.
- Tratar imágenes múltiples del mismo espécimen como medidas dependientes.

**Conclusión técnica:** la v3.0 añade descriptores invariantes y sensibilidad reproducible, verificados localmente y en dos entornos remotos con 43 pruebas cada uno y cuatro formas sintéticas. No hay todavía validación de la hipótesis biológica.
