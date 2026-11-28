# ADR-004: licencia MIT para el código de geovida

- **Estado:** Aceptada
- **Fecha:** 13 de noviembre de 2026
- **Decisor:** autor del proyecto (aprobado en el chat)
- **Depende de:** ADR-001

## Contexto

La licencia MIT se puso por defecto en la rama `geovida/v0.1-desde-cero` durante el desarrollo, sin una decisión explícita del autor. Las ramas del linaje Codex (v2.5/v3.0) no tienen licencia.

Estado comprobado el 13 nov 2026, coherente en los tres sitios:

| Archivo | Contenido |
|---|---|
| `LICENSE` | MIT License, Copyright (c) 2026 Fabián Trelles |
| `CITATION.cff` | `license: MIT`, autor Fabián Trelles |
| `pyproject.toml` | `license = { text = "MIT" }`, autor Fabián Trelles |

## Decisión

Se **mantiene la licencia MIT** para el código, la documentación y los resultados sintéticos publicados en el repositorio.

## Alcance y límites

- MIT cubre solo el material propio del repositorio. **No se extiende a datos de terceros**: cada conjunto externo (HC18, MusMorph, IMPC/DMDD, S-BIAD441, etc.) conserva su propia licencia, que se verificará y registrará por separado antes de usarlo.
- Las imágenes reales con información personal no forman parte del repositorio y no quedan cubiertas por esta licencia.
- MIT permite el uso comercial y no ofrece ninguna garantía. El aviso de «solo investigación y educación, no uso clínico» del README sigue vigente como declaración de uso previsto; no restringe legalmente la licencia.

## Consecuencias

- No hacen falta cambios en `LICENSE`, `CITATION.cff` ni `pyproject.toml`.
- Si se porta código del linaje Codex (por ejemplo, los momentos de Hu), queda bajo MIT al incorporarse, porque el autor es el mismo.
