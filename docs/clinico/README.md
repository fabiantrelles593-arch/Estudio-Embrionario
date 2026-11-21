# Paquete de preparación clínica (borrador de ingeniería)

Este paquete reúne lo que haría falta tener ordenado antes de acercarse a un uso clínico del
software. **No es un expediente, no ha sido revisado por ninguna autoridad, comité ni asesor
regulatorio, y no autoriza ningún uso clínico.** Hoy `geovida` es un instrumento de investigación y
educación; con imágenes de personas solo podría usarse tras cumplir todas las condiciones de
`../DATOS_REALES_Y_ETICA.md`.

| Documento | Para qué sirve |
|---|---|
| [`USO_PREVISTO_Y_RIESGOS.md`](USO_PREVISTO_Y_RIESGOS.md) | Qué hace y qué NO hace el software; contraindicaciones; 12 peligros con su evidencia, controles y riesgo residual |
| [`PLAN_DE_VALIDACION.md`](PLAN_DE_VALIDACION.md) | Los tres pilares de IMDRF N41 y qué evidencia hay en cada uno; etapas con criterios de aceptación; cobertura de TRIPOD+AI y CLAIM; camino regulatorio y ético |
| [`CICLO_DE_VIDA.md`](CICLO_DE_VIDA.md) | Clase de seguridad propuesta (IEC 62304), prácticas existentes y huecos, software de terceros (SOUP), control de cambios |
| [`FICHA_DEL_MODELO.md`](FICHA_DEL_MODELO.md) | Ficha del modelo: qué se calibró, con qué, qué rendimiento tuvo, dónde falla |
| [`TRAZABILIDAD.md`](TRAZABILIDAD.md) | Cada hipótesis con su preregistro, su código, sus pruebas y sus resultados (una prueba automática comprueba que los archivos citados existen) |

## Lo que sí se puede decir hoy

* El instrumento estima una probabilidad calibrada de que una medida sea fiable y se niega cuando la
  imagen no se parece a su calibración, **en imágenes sintéticas**, con criterios fijados antes de
  correr y con sus fallos publicados.
* Existe un informe por medida con huellas SHA-256 de la imagen y de la calibración, versión, commit y
  límites (`geovida certify --report`).

## Lo que NO se puede decir hoy

* Que funcione en imágenes reales de embriones (H11 espera datos).
* Que sea mejor que otras herramientas (no se ha comparado).
* Que sirva para algo clínico, que reduzca enfermedades congénitas o que sea un dispositivo médico
  autorizado.

## Quién tiene que intervenir para dar el siguiente paso

Un asesor regulatorio (clasificación y requisitos de calidad), un grupo clínico, un comité de ética y,
si hay uso clínico, la autoridad competente. Eso no se improvisa desde un repositorio.
