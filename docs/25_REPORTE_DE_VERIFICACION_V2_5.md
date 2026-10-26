# Reporte de verificación técnica — Geometría de la Vida v2.5

**Fecha de ejecución:** 26 de octubre de 2026  
**Entorno local verificado:** Linux, Python 3.13.5, pytest 9.0.2, NumPy 2.3.5, SciPy 1.17.0, scikit-image 0.26.0 y pandas 2.2.3.  
**Material evaluado:** código y ejemplos sintéticos creados para pruebas; no se usaron imágenes embrionarias reales.

## Cambios implementados

- Se añadió `src/analyze_manifest.py` para conectar un CSV con rutas de imágenes, auditar metadatos, convertir imágenes en máscaras, calcular métricas y preservar errores por observación.
- Se añadió `src/create_synthetic_manifest.py` para generar un manifiesto reproducible a partir de cuatro máscaras sintéticas.
- La auditoría permite `stage=not_applicable` solo para ejemplos sintéticos; los registros biológicos siguen requiriendo una etapa entera dentro de CS12–CS18.
- Se añadieron pruebas de escala física/desconocida, imagen ausente, permiso pendiente, escala inválida y columna `image_path` ausente.
- Se incorporaron configuración de VS Code/Codespaces, perfiles de depuración y un workflow de GitHub Actions.

## Resultados locales observados

| Comprobación | Resultado |
|---|---|
| `python -m pytest tests -v` | **30 pruebas aprobadas, 0 fallidas** |
| `python src/demo_pipeline.py` | Generó la tabla morfológica sintética, PCA y matriz de distancias |
| Auditoría del CSV sintético | `ok: true`, 4 observaciones y ningún bloqueo de metadatos |
| Análisis por manifiesto | 4 máscaras analizadas, 4 con estado `OK`, 0 errores |
| Prueba de escala | 42 píxeles × (0,25 unidades/píxel)² = 2,625 unidades² |

## Integración continua remota — GitHub Actions

La versión se publicó en la rama `development/v2.5-manifest-pipeline` del repositorio [Estudio-Embrionario](https://github.com/fabiantrelles593-arch/Estudio-Embrionario), y se abrió la [PR #1](https://github.com/fabiantrelles593-arch/Estudio-Embrionario/pull/1) contra `main`.

La ejecución remota [Python tests](https://github.com/fabiantrelles593-arch/Estudio-Embrionario/actions/runs/40314446255) terminó correctamente para ambas versiones de Python:

| Entorno remoto | Pruebas | Pipeline y auditoría |
|---|---:|---|
| Python 3.12 | 30 aprobadas, 0 fallidas | Demo, auditoría, manifiesto y análisis end-to-end completados; 4 máscaras procesadas y 0 errores |
| Python 3.13 | 30 aprobadas, 0 fallidas | Demo, auditoría, manifiesto y análisis end-to-end completados; 4 máscaras procesadas y 0 errores |

GitHub generó los artefactos `synthetic-demo-py3.12` y `synthetic-demo-py3.13`. Contienen salidas sintéticas, no datos embrionarios.

## Verificaciones pendientes

- Repetir la instalación y los comandos en el ordenador Windows del equipo o en un Codespace.
- Revisar y aceptar la PR #1 antes de integrarla en `main`; la PR permanece abierta y no se ha fusionado.
- Seleccionar imágenes biológicas con procedencia, etapas, condiciones de uso y escala documentadas.
- Definir y validar la segmentación anatómica con supervisión experta antes de interpretar resultados biológicos.
- Separar observaciones del mismo espécimen de unidades experimentales independientes.

## Alcance de la conclusión

El paquete se extrajo en una carpeta limpia y volvió a pasar las 30 pruebas, la demo, la auditoría y el analizador de manifiesto. Esto verifica el comportamiento del software con ejemplos sintéticos en el entorno local y en dos trabajos de GitHub Actions; no valida la segmentación anatómica ni confirma la hipótesis biológica.
