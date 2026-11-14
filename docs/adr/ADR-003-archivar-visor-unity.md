# ADR-003: archivar el visor Unity

- **Estado:** Aceptada
- **Fecha:** 13 de noviembre de 2026
- **Decisor:** autor del proyecto (aprobado en el chat)
- **Depende de:** ADR-001

## Contexto

La rama `geovida/v0.1-desde-cero` contenía un visor 4D para Unity:

- `unity/Assets/Geovida/Scripts/GeovidaViewer.cs`
- `unity/Assets/StreamingAssets/geovida_series.json` (1,3 MB)
- `unity/README.md`
- Además, el exportador `scripts/export_unity.py`, que genera ese JSON.

Ese visor nunca se compiló, porque en el entorno de desarrollo no hay Unity. Tampoco aporta a la pregunta científica, ninguna prueba ni `pyproject.toml` dependen de él, y añade mantenimiento y peso al repositorio.

## Decisión

1. Conservar el visor completo en la rama **`archive/unity-viewer`**, creada desde el commit `1078731` de `geovida/v0.1-desde-cero`.
2. Quitar de `geovida/v0.1-desde-cero` la carpeta `unity/` y el script `scripts/export_unity.py`.
3. Actualizar la mención en el `README.md` para indicar dónde quedó archivado.

## Ejecución (13 nov 2026)

| Commit | Cambio |
|---|---|
| `66b5649` | Elimina `unity/` (3 archivos) |
| `79e895d` | Elimina `scripts/export_unity.py` |
| `66b86e4` | `README.md`: una línea modificada |

Comprobado con la API de GitHub: `unity/` y `scripts/export_unity.py` devuelven 404 en `geovida/v0.1-desde-cero` y `unity/` existe en `archive/unity-viewer`.

## Consecuencias

- Las menciones históricas en `docs/RESULTADOS_V04.md` y `docs/ARQUITECTURA.md` no se tocan: describen lo que existía en cada versión.
- Para recuperar el visor, basta con traer `unity/` y `scripts/export_unity.py` desde `archive/unity-viewer`.
- La rama `archive/unity-viewer` no se debe borrar.
