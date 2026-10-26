# Entorno reproducible — v2.4

El repositorio incluye un Dev Container para GitHub Codespaces y un workflow de integración continua. El Dev Container declara Python 3.12, instala las dependencias de `requirements.txt` y recomienda extensiones de Python, Pylance, depuración y formato.

La configuración de Codespaces solo se aplicará una vez que los archivos estén en un repositorio y se cree un Codespace. `.vscode/extensions.json` recomienda extensiones al abrir la carpeta en la aplicación de escritorio; no instala nada silenciosamente en el equipo.

El workflow corre las pruebas, genera los resultados sintéticos, audita los metadatos de esa demostración y publica los archivos como artefacto de CI. Una ejecución local satisfactoria no equivale a una ejecución de GitHub Actions; la última solo podrá comprobarse después de publicar el código en el repositorio real.

## Referencias oficiales
- GitHub Docs, introducción a Dev Containers: https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/adding-a-dev-container-configuration/introduction-to-dev-containers
- GitHub Docs, configuración de un proyecto Python en Codespaces: https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/adding-a-dev-container-configuration/setting-up-your-python-project-for-codespaces
- VS Code, Python en Visual Studio Code: https://code.visualstudio.com/docs/languages/python
- GitHub Actions, `actions/checkout`: https://github.com/actions/checkout
- GitHub Actions, `actions/setup-python`: https://github.com/actions/setup-python
- GitHub Actions, `actions/upload-artifact`: https://github.com/actions/upload-artifact
