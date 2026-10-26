# Geometría de la Vida — guía para abrir Codespaces

## Situación actual
La versión 2.5 está publicada en el repositorio [Estudio-Embrionario](https://github.com/fabiantrelles593-arch/Estudio-Embrionario), en la rama `development/v2.5-manifest-pipeline`. La [PR #1](https://github.com/fabiantrelles593-arch/Estudio-Embrionario/pull/1) está abierta hacia `main`. GitHub Actions completó correctamente los trabajos de Python 3.12 y 3.13, con 30 pruebas aprobadas en cada entorno; se procesaron cuatro máscaras sintéticas sin errores. [Ver ejecución remota](https://github.com/fabiantrelles593-arch/Estudio-Embrionario/actions/runs/40314446255).

El archivo `.devcontainer/devcontainer.json` declara el contenedor y las dependencias. `.vscode/extensions.json` recomienda las extensiones para VS Code de escritorio y `.vscode/launch.json` incluye perfiles de depuración. La configuración de extensiones se activa al crear el Codespace; no instala nada directamente en el ordenador local. La PR aún no se ha fusionado en `main`.

## 1. Abrir la versión de desarrollo
1. Abre el [repositorio Estudio-Embrionario](https://github.com/fabiantrelles593-arch/Estudio-Embrionario).
2. Selecciona la rama `development/v2.5-manifest-pipeline` o abre la [PR #1](https://github.com/fabiantrelles593-arch/Estudio-Embrionario/pull/1) para revisar los cambios.
3. Antes de fusionar, revisa el contenido y el resultado de Actions. Las comprobaciones automatizadas han pasado, pero la fusión todavía está pendiente.

## 2. Crear un Codespace
1. En el repositorio, selecciona la rama `development/v2.5-manifest-pipeline`.
2. Desde el botón `Code`, abre la pestaña `Codespaces` y crea un Codespace desde esa rama.
3. El contenedor instalará las dependencias enumeradas en `requirements.txt` y propondrá Python, Pylance, Python Debugger y Black Formatter.
4. Espera a que el terminal del Codespace esté listo y ejecuta las comprobaciones siguientes.

## 3. Ejecutar el proyecto
```bash
python -m pytest tests -v
python src/demo_pipeline.py
python src/audit_dataset.py demo/synthetic_morphology.csv --out demo/synthetic_audit.json --strict
python src/create_synthetic_manifest.py
python -m src.analyze_manifest demo/synthetic_manifest.csv --out demo/synthetic_mask_metrics.csv --strict
```

El pipeline sintético genera cuatro formas de prueba. No son imágenes embrionarias y no validan la hipótesis biológica.

## 4. Seguridad y datos
No se han añadido imágenes embrionarias humanas reales. Antes de introducir datos biológicos, comprueba la fuente, las condiciones de uso, los permisos, los identificadores y el método de segmentación con tu asesor. Las carpetas `data/raw/`, `data/private/`, `data/biological/` y `data/pending_permission/` están excluidas por `.gitignore` para reducir subidas accidentales, pero esa exclusión no sustituye el control de acceso ni una revisión antes de publicar.

## 5. Estado que queda pendiente
- La PR #1 debe revisarse y fusionarse expresamente para llevar los cambios a `main`.
- El equipo debe comprobar la instalación en su entorno Windows o Codespaces.
- La selección y validación de imágenes biológicas autorizadas sigue pendiente.
