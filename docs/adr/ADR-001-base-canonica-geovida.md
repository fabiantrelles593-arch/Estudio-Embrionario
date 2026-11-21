# ADR-001 — Base canónica del proyecto: `geovida`

- **Estado:** Aceptada
- **Fecha:** 13 de noviembre de 2026
- **Decisor:** autor del proyecto (aprobación en chat)
- **Contexto de origen:** Auditoría de Fase 0 (`AUDITORIA_FASE0_GEOMETRIA_DE_LA_VIDA.md`, §3 y §13)

## Contexto

En el repositorio `Estudio-Embrionario` hay dos linajes de código independientes:

| Linaje | Rama | Forma | Estado |
|---|---|---|---|
| Codex (ChatGPT) | `development/v2.5-manifest-pipeline`, `development/v3.0-advanced-morphology` (PR #1 y #2, abiertas) | Scripts planos en `src/*.py`: análisis 2D, manifiesto, Hu, índice de robustez 0–100 | CI verde, 30/43 pruebas declaradas, solo 2D |
| Codex (local) | `codex/advanced-3d-morphology` | v4.0: lectura NPY/TIFF/OME/NRRD, métricas 3D, sensibilidad a la resolución | **No publicada**, pruebas nunca ejecutadas |
| Claude | `geovida/v0.1-desde-cero` | Paquete `src/geovida/`: fantomas, certificado de incertidumbre, guardias, H1–H16 preregistradas, prototipo | CI verde en la punta, sin PR |

Los dos linajes no comparten código. Mantenerlos en paralelo duplicaría el esfuerzo y la documentación.

## Decisión

`geovida` (rama `geovida/v0.1-desde-cero`) es la **base canónica** de Geometría de la Vida. A partir de ahora, todo desarrollo nuevo se construye sobre el paquete `src/geovida/`.

## Consecuencias

1. **Nada se borra.** Las ramas v2.5 y v3.0 se conservan como historial. El destino de las PR #1 y #2 se decidirá en el ADR-002, y no se cerrarán ni fusionarán sin autorización expresa.
2. **Rescate selectivo del linaje Codex.** Lo que no exista en geovida se porta con pruebas propias, citando su origen:
   - Momentos de Hu (`advanced_morphology.py`, v3.0).
   - Lector de volúmenes NPY/TIFF/OME-TIFF/NRRD y manifiesto volumétrico (v4.0 local, **si se recupera**).
   - Validaciones del manifiesto CSV (`audit_dataset.py`, `analyze_manifest.py`), en lo que complementen a `provenance`/`labeling`.
3. **El índice de robustez 0–100 de v3.0 no se porta.** Lo sustituyen los semáforos separados de volumen y topología, con abstención (`certificate`, `domain`). La auditoría (§3.3) explica por qué.
4. **MORPHO-TRACE** se define como método sobre los módulos de incertidumbre de geovida (`scaleaxis`, `topomargin`, `certificate`, `budget`, `domain`, `chainguard`), no como un paquete paralelo. La pieza nueva, la descomposición de varianza técnica frente a biológica, se añadirá dentro de geovida.
5. **Migración gradual** hacia los subpaquetes propuestos en la auditoría (§7). Se hará por pasos pequeños y probados, sin una reestructuración masiva.
6. **Documentación:** el documento maestro de Notion debe enlazar a geovida y marcar v2.5/v3.0/v4.0 como historial.

## Pendientes derivados

- ~~ADR-002: destino de las PR #1 y #2~~: hecho; se cerraron sin fusionar y se conservaron sus ramas.
- Recuperar `codex/advanced-3d-morphology` del equipo original.
- Ejecutar la suite de geovida en un entorno limpio y aclarar la discrepancia entre las 351 pruebas declaradas y las 602 funciones contadas.
- ~~Decidir si se abre una PR hacia `main`~~: hecho, PR #3 (borrador), abierta el 13 nov 2026.

## Alternativas consideradas

- **v3.0 como base y portar geovida encima:** se descartó. v3.0 solo cubre 2D, no tiene fantomas 3D ni certificado, y el portado sería prácticamente una reescritura de geovida.
- **Mantener ambos linajes:** se descartó por duplicación y por el riesgo de que la documentación diverja.
