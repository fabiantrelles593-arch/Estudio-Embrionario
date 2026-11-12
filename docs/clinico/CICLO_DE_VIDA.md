# Ciclo de vida del software, SOUP y control de cambios (borrador de ingeniería)

> Borrador del equipo. No es una declaración de conformidad con IEC 62304: describe qué prácticas ya
> existen en el repositorio, a qué actividad de la norma se parecen y qué falta. La norma, según lo
> consultado, clasifica el software en A, B o C; su edición 2 aún estaba en borrador.

## 1. Clase de seguridad del software (propuesta preliminar)

| Clase | Criterio de la norma (resumido) | Aplicación a `geovida` |
|---|---|---|
| A | Ningún daño a la salud es posible por un fallo del software | **Hoy:** investigación y educación, sin decisiones sobre personas. Se trabaja *como si* fuera A como mínimo |
| B | Es posible un daño no grave | Si en el futuro la luz verde informara una decisión clínica, se propone **B como mínimo** hasta que un análisis de riesgos formal demuestre lo contrario |
| C | Es posible la muerte o un daño grave | No se propone, pero un uso en decisiones sobre una gestación obligaría a revisarlo |

La clase la decide la gestión de riesgos (`USO_PREVISTO_Y_RIESGOS.md`), no este documento. El peligro
central es un **falso verde** (R1, R2): se midió y no es cero.

## 2. Qué práctica del repositorio se parece a cada actividad

| Actividad (resumida) | Lo que ya existe | Lo que falta |
|---|---|---|
| Planificación del desarrollo | `OBJETIVOS_V05.md`, preregistros con criterios y predicciones | Plan de desarrollo formal con roles |
| Requisitos | Hipótesis y criterios (`PREREGISTRO_*.md`), uso previsto | Especificación de requisitos de software numerada |
| Arquitectura y diseño | `METODOS.md`; módulos con docstrings que dicen qué hacen y qué NO hacen | Diagrama de arquitectura; interfaces documentadas aparte |
| Implementación y pruebas unitarias | Más de 400 pruebas; desarrollo con prueba primero en las funciones nuevas de v0.5 | Cobertura medida (no se mide) |
| Integración y pruebas de sistema | Barridos de calibración y confirmación con semillas separadas | Pruebas de sistema con datos reales (H11) |
| Liberación | Commits en una rama, empaquetado `geovida_v0.4.zip`, manifiestos con commit y estado del código | Procedimiento de liberación, etiquetas de versión, notas de versión |
| Mantenimiento y resolución de problemas | `ERRATA.md` (errores propios con su corrección) | Registro formal de anomalías y análisis de impacto |
| Gestión de riesgos | `USO_PREVISTO_Y_RIESGOS.md` (borrador) | Revisión por una persona con formación en ISO 14971 |
| Gestión de configuración | Git; huellas SHA-256 de la imagen y de la calibración en cada informe; modelos congelados versionados con prueba de igualdad | Congelar las dependencias (lock) |

## 3. SOUP (software de procedencia desconocida) usado

Versiones con las que se corrió la última batería de pruebas.

| Paquete | Versión | Para qué se usa | Si falla | Mitigación existente |
|---|---|---|---|---|
| numpy | 2.5.3 | Arreglos, álgebra | Resultados numéricos erróneos | Pruebas con verdad analítica (bola, elipsoide, toro…) |
| scipy | 1.18.1 | Filtros, distancias, rotaciones, ajuste | Ídem | Ídem; ruido y desenfoque con propiedades comprobadas por prueba |
| scikit-image | 0.26.0 | Umbral de Otsu, etiquetado, morfología | Segmentación o topología erróneas | Pruebas de topología con Betti conocidos |
| pandas | 3.0.5 | Tablas de barrido y análisis | Agrupaciones erróneas | Pruebas de las evaluaciones con datos fabricados de estructura conocida |
| matplotlib | 3.11.2 | Figuras | Figura engañosa | Las cifras de los informes salen de las tablas, no de las figuras |
| statsmodels | 0.15.0 | Declarado como dependencia, pero **no se importa en `src/`** (solo se registra su versión en manifiestos antiguos); el ajuste logístico es propio (`analysis.py`) | — | Candidato a retirarse de las dependencias |
| nibabel | 5.5.0 | Lectura de NIfTI (opcional) | Vóxel o intensidades mal leídos | Pruebas de ida y vuelta con tamaños de vóxel y unidades |

Pendiente: monitorear anuncios de defectos de estos paquetes y fijar versiones exactas con un archivo
de bloqueo.

## 4. Control de cambios (reglas que ya se siguen)

1. **Nada se cambia en `main`.** El trabajo va en una rama y se publica tras cada hito.
2. **Preregistro y congelado primero.** Un modelo, una envolvente o un umbral confirmado no se
   modifica después de ver resultados; cualquier mejora va a una versión nueva con su preregistro y
   las desviaciones se anotan en el mismo documento con fecha.
3. **Todo cambio de código con prueba.** Primero la prueba, que debe fallar por la razón correcta.
4. **Errores propios a la vista.** Una cifra o una afirmación errónea se corrige y se documenta en
   `ERRATA.md` (hasta ahora 26, incluida la discordancia de versión entre el paquete y `pyproject`).
5. **Cada barrido guarda su procedencia:** commit, si el código estaba sin guardar, semilla, número de
   filas, versiones de paquetes.
6. **Cada informe de certificado guarda su procedencia:** versión, commit, huella de imagen y
   calibración, parámetros declarados y límites (`geovida certify --report`).

## 5. Lo que este documento no puede decir

* Que el software cumpla IEC 62304 ni ninguna otra norma.
* Que el proceso sea auditable por un tercero: no hay hoy revisión independiente.
* Que las dependencias sean seguras frente a vulnerabilidades: no se ha hecho un análisis.
