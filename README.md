# Geometría de la Vida — v2.5

**Proyecto:** modelado geométrico y topológico de transformaciones morfológicas. Esta versión fortalece la auditoría de metadatos y el entorno reproducible para el desarrollo colaborativo.

## Estado científico
Las demostraciones se construyen con máscaras sintéticas. No se afirma que sean datos biológicos ni que se haya validado una hipótesis embrionaria. Antes del análisis biológico se necesitan imágenes con procedencia, etapas, condiciones de uso, escala cuando exista y segmentación documentadas.

## Incluye
- `src/metrics_2d.py`: descriptores geométricos y topológicos de máscaras 2D; `pixel_size` debe ser finito y positivo.
- `src/morphology_space.py`: estandarización, PCA exploratorio y matriz de distancias.
- `src/audit_dataset.py`: auditoría de campos, IDs, etapas CS12–CS18, dependencia por espécimen, calidad y estado de uso.
- `src/image_io.py`: lectura inicial de imágenes y umbral simple a máscara binaria; no sustituye un protocolo anatómico de segmentación.
- `src/analyze_manifest.py`: pipeline por manifiesto; audita metadatos, resuelve rutas, calcula métricas y conserva errores por observación.
- `src/create_synthetic_manifest.py`: prepara un manifiesto de prueba solo con imágenes sintéticas.
- `src/demo_pipeline.py`: figuras sintéticas, CSV morfológico, PCA y matriz de distancias.
- `tests/`: pruebas automáticas.
- `.devcontainer/devcontainer.json`: configuración reproducible para GitHub Codespaces y extensiones.
- `.vscode/launch.json`: perfiles de depuración de la demo y del analizador de manifiesto.
- `docs/26_GITHUB_CODESPACES_PUESTA_EN_MARCHA.md`: pasos para publicar el paquete, crear un Codespace y verificar GitHub Actions.
- `.github/workflows/tests.yml`: pruebas y auditoría automatizadas al subir cambios.

## Ejecutar en Windows / VS Code
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest tests -v
python src/demo_pipeline.py
python src/audit_dataset.py demo/synthetic_morphology.csv --out demo/synthetic_audit.json --strict
python src/create_synthetic_manifest.py
python -m src.analyze_manifest demo/synthetic_manifest.csv --out demo/synthetic_mask_metrics.csv --strict
```

Si PowerShell no permite activar el entorno, usa directamente ` .\.venv\Scripts\python.exe` en los comandos Python.

## Qué mide y qué no
`area` y `perimeter` agregan todas las componentes. Ejes, solidez, extensión y excentricidad describen la componente conectada de mayor área; este criterio queda registrado en `component_policy`. `pixel_size=1.0` mantiene las medidas en unidades de píxel; solo se deben convertir a unidades físicas con una escala verificada.

La conectividad de topología está fijada a 8 vecinos en este módulo y debe registrarse si se comparan variantes. La auditoría excluye conjuntos vacíos, campos requeridos vacíos, IDs duplicados, etapas biológicas no enteras o fuera de 12–18, estados de uso no verificados y calidad no aceptada. Los registros sintéticos deben marcar `modality=SYNTHETIC` y `stage=not_applicable`; no se les asigna una etapa Carnegie ficticia.

## Análisis por manifiesto (v2.5)
`src/analyze_manifest.py` requiere una columna `image_path` además de los campos auditados. Las rutas relativas se resuelven desde la ubicación del manifiesto. Si se desconoce la escala, las métricas se quedan en píxeles; una escala declarada requiere unidad y valor finito positivo. La salida conserva `analysis_status` y `analysis_error` para que una imagen defectuosa no desaparezca sin explicación.

El estado `OK` indica que la máscara se pudo medir, no que la segmentación anatómica sea correcta. `--strict` devuelve código de salida distinto de cero si hay errores de procesamiento por imagen.

## Códigos de estado
- `OK`: no se detectaron bloqueos según las reglas automatizadas de auditoría; todavía requiere revisión científica.
- `NO OK`: existen datos faltantes, problemas de trazabilidad, licencia/permiso no resuelto o calidad que necesita revisión.

Un dataset puede superar la auditoría de metadatos y aun ser científicamente inadecuado. La auditoría no reemplaza la revisión de fuentes, anatomía ni segmentación.


## Reporte de verificación
Consulta `docs/25_REPORTE_DE_VERIFICACION_V2_5.md` para los comandos ejecutados, resultados observados y límites de interpretación de la versión 2.5.
