# Geometría de la Vida — v2.5

**Proyecto:** modelado geométrico y topológico de transformaciones morfológicas.

Esta versión añade un pipeline de análisis por manifiesto, auditoría de metadatos, registro explícito de errores y configuración reproducible para VS Code, Codespaces y GitHub Actions.

## Estado de verificación
- **30 pruebas aprobadas en local** con Python 3.13.5.
- **GitHub Actions pasó con Python 3.12 y 3.13**, con 30 pruebas aprobadas en cada matriz.
- La demostración y el análisis por manifiesto procesaron cuatro máscaras sintéticas, con cero errores.
- Los resultados son de figuras sintéticas; no constituyen datos embrionarios ni validación biológica.

En GitHub:
- Repositorio: [Estudio-Embrionario](https://github.com/fabiantrelles593-arch/Estudio-Embrionario)
- Rama de desarrollo: `development/v2.5-manifest-pipeline`
- [PR #1 — revisión de la v2.5](https://github.com/fabiantrelles593-arch/Estudio-Embrionario/pull/1)
- [Ejecución CI verificada](https://github.com/fabiantrelles593-arch/Estudio-Embrionario/actions/runs/40314446255)

La PR sigue abierta y no se ha fusionado a `main`.

## Componentes
- `src/metrics_2d.py`: descriptores geométricos y topológicos 2D; tamaño de píxel finito y positivo.
- `src/morphology_space.py`: estandarización, PCA exploratorio y matriz de distancias.
- `src/audit_dataset.py`: auditoría de campos obligatorios, IDs, etapas CS12–CS18, dependencias por espécimen, calidad y estado de uso.
- `src/image_io.py`: lectura inicial de imágenes y umbral simple para generar máscaras; no reemplaza un protocolo anatómico validado.
- `src/analyze_manifest.py`: audita metadatos, resuelve rutas de imagen, calcula métricas y conserva errores por observación.
- `src/create_synthetic_manifest.py`: crea un manifiesto reproducible de demostración sintética.
- `src/demo_pipeline.py`: genera figuras sintéticas, tabla morfológica, PCA y matriz de distancias.
- `tests/`: pruebas automatizadas.
- `.devcontainer/devcontainer.json`: dependencias y extensiones recomendadas para Codespaces.
- `.vscode/launch.json`: perfiles de depuración para la demo y el analizador de manifiesto.
- `.github/workflows/tests.yml`: integración continua para Python 3.12 y 3.13.

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

Si PowerShell no permite activar el entorno, usa ` .\.venv\Scripts\python.exe` en lugar de `python` en los comandos posteriores.

## Escala, métricas y límites
`area` y `perimeter` agregan las componentes; ejes, solidez, extensión y excentricidad describen la componente de mayor área. Esta política queda anotada en `component_policy`. Si falta una escala física verificada, las métricas se mantienen en píxeles. Si se declara `pixel_size`, se exige además unidad y un valor finito positivo.

La conectividad topológica usa 8 vecinos en el módulo actual y debe mantenerse constante al comparar resultados. Los registros sintéticos usan `modality=SYNTHETIC` y `stage=not_applicable`; no se les atribuye una etapa Carnegie ficticia.

Una salida `OK` indica que la máscara pudo medirse; no demuestra que la segmentación anatómica sea correcta. Las figuras sintéticas sirven para verificar el código, no la hipótesis biológica. El software no diagnostica.

## Próximos hitos
1. Revisar y fusionar la PR #1.
2. Repetir instalación y ejecución en el equipo Windows del grupo o en Codespaces.
3. Acordar una fuente de imágenes embrionarias autorizadas y comparables, con procedencia y metadatos completos.
4. Validar la segmentación anatómica y analizar sensibilidad a resolución, escala, conectividad y contornos.
5. Solo entonces evaluar si los descriptores caracterizan transformaciones biológicas.
