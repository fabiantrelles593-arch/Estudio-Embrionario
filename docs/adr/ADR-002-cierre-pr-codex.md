# ADR-002: cerrar las PR #1 y #2 sin fusionarlas y conservar sus ramas

- **Estado:** Aceptada
- **Fecha:** 13 de noviembre de 2026
- **Decisor:** autor del proyecto (aprobado en el chat)
- **Depende de:** ADR-001 (base canónica: `geovida`)

## Contexto

Las dos PR del linaje Codex llevaban abiertas y sin fusionar desde el 26 de octubre de 2026:

| PR | Rama | Base | Contenido |
|---|---|---|---|
| #1 | `development/v2.5-manifest-pipeline` | `main` | Pipeline 2D con manifiesto, auditoría y CI (30 pruebas declaradas) |
| #2 | `development/v3.0-advanced-morphology` | `development/v2.5-manifest-pipeline` | Momentos de Hu, sensibilidad al umbral e índice de robustez 0–100 (43 pruebas declaradas) |

Con el ADR-001, el desarrollo continúa sobre `geovida`. Fusionar estas PR en `main` dejaría allí un linaje que ya no se va a mantener.

## Decisión

1. **Cerrar la PR #2 y la PR #1 sin fusionarlas.** Primero la #2, porque su base es la rama de la #1.
2. **Conservar ambas ramas** (`development/v2.5-manifest-pipeline` y `development/v3.0-advanced-morphology`). No se borran.
3. Cerrar una PR es reversible: se puede reabrir desde GitHub en cualquier momento.

## Ejecución

- PR #2 cerrada el 13 nov 2026 a las 12:25:57 UTC, sin fusionar.
- PR #1 cerrada el 13 nov 2026 a las 12:26:15 UTC, sin fusionar.
- Comprobación con la API de GitHub: `merged_at = null` en ambas; las ramas `main`, `development/v2.5-manifest-pipeline`, `development/v3.0-advanced-morphology` y `geovida/v0.1-desde-cero` siguen existiendo.
- Cerré las PR sin dejar comentario de cierre.

## Consecuencias

- `main` sigue conteniendo solo el README hasta que se fusione la PR #3 (`geovida/v0.1-desde-cero` → `main`). La PR #3 se abrió como borrador el 13 nov 2026.
- El código útil de v3.0 (momentos de Hu, validaciones del manifiesto) se portará a `geovida` con pruebas propias, citando la rama de origen y el commit `0e22650`.
- La CI histórica de estas ramas sigue en GitHub como evidencia de las 30 y 43 pruebas declaradas.
