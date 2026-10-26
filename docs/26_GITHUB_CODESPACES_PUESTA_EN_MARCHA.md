# Publicación en GitHub y apertura en Codespaces — guía de una sola vez

## Situación actual
La configuración de Codespaces ya se encuentra en `.devcontainer/devcontainer.json`; las extensiones recomendadas están en `.vscode/extensions.json` y las configuraciones de depuración están en `.vscode/launch.json`. No obstante, la conexión utilizada para esta sesión no muestra un repositorio accesible y no permite crear uno nuevo desde las acciones disponibles. Por ello, este documento da los pasos puntuales que debe ejecutar la persona propietaria de la cuenta.

## 1. Crear el repositorio

1. Inicia sesión en GitHub con la cuenta propietaria del proyecto.
2. Crea un repositorio con el nombre `geometria-de-la-vida`.
3. Recomendación: mantenlo **privado** durante la etapa de desarrollo, revisión de fuentes y preparación de datos.
4. Para publicar el contenido de este paquete como primer commit, crea el repositorio vacío: no marques las opciones para generar README, licencia o `.gitignore`, porque el paquete ya trae esos archivos.

La URL esperada para el nombre de repositorio sugerido sería `https://github.com/fabiantrelles593-arch/geometria-de-la-vida`, si se crea bajo esa cuenta. Si eliges otro propietario o nombre, usa la URL real que GitHub te muestre.

## 2. Subir el paquete desde la carpeta extraída

Extrae `Geometria_de_la_Vida_v2_5.zip`, abre la carpeta `Geometria_de_la_Vida_v2_5` en VS Code y abre una terminal dentro de ella. Primero comprueba que Git esté instalado:

```powershell
git --version
```

Si devuelve una versión de Git, ejecuta los comandos siguientes, sustituyendo la URL por la real de tu repositorio:

```powershell
git init
git add .
git status
git commit -m "Build Geometría de la Vida v2.5"
git branch -M main
git remote add origin https://github.com/fabiantrelles593-arch/geometria-de-la-vida.git
git push -u origin main
```

Revisa `git status` antes de confirmar el commit. Si el nombre del repositorio es distinto, actualiza la URL de `origin`. Si GitHub solicita autenticación, completa su flujo oficial de inicio de sesión; **no pegues contraseñas ni tokens en el chat**.

## 3. Crear un Codespace

1. Abre el repositorio en GitHub.
2. En el botón `Code`, abre la pestaña `Codespaces` y elige crear un Codespace desde `main`.
3. La configuración del contenedor instalará las dependencias de `requirements.txt` y propondrá Python, Pylance, Python Debugger y Black Formatter.
4. Cuando el terminal del Codespace esté listo, ejecuta:

```bash
python -m pytest tests -v
python src/demo_pipeline.py
python src/audit_dataset.py demo/synthetic_morphology.csv --out demo/synthetic_audit.json --strict
python src/create_synthetic_manifest.py
python -m src.analyze_manifest demo/synthetic_manifest.csv --out demo/synthetic_mask_metrics.csv --strict
```

## 4. Confirmar la integración continua

Después de hacer `push`, abre la pestaña `Actions` del repositorio y comprueba el workflow `Python tests`. Solo marca la integración como verificada cuando el propio GitHub muestre una ejecución finalizada correctamente. El archivo de workflow en el ZIP significa que está configurado, no que ya se haya ejecutado remotamente.

## 5. Protección de los datos

El repositorio no incluye imágenes embrionarias humanas reales. Antes de añadir datos biológicos, confirma condiciones de uso, licencia o permiso, metadatos y aprobación del asesor. Las carpetas `data/raw/`, `data/private/`, `data/biological/` y `data/pending_permission/` están excluidas por defecto con `.gitignore` para reducir subidas accidentales. La exclusión de Git no es una medida de seguridad: sigue guardando esos datos con controles de acceso adecuados.
