# Uso previsto y gestión de riesgos (borrador de ingeniería)

> **Qué es este documento.** Un borrador de ingeniería escrito por el equipo del proyecto para
> preparar, con orden, un posible camino regulatorio futuro. **No es** un expediente, **no ha sido
> revisado ni aprobado por ninguna autoridad, comité ni asesor regulatorio**, y no autoriza ningún uso
> clínico. Hoy `geovida` es un instrumento de investigación y educación. Cada afirmación se apoya en
> un resultado del repositorio (ver `TRAZABILIDAD.md`) o está marcada como «pendiente».

## 1. Uso previsto (propuesta para discutir con un asesor)

| Elemento | Propuesta |
|---|---|
| Qué hace | Para una **medida** (volumen y triple de Betti) obtenida de una imagen 3D segmentada, estima la **probabilidad de que esa medida sea fiable** y emite una luz (verde ≥ 0.90, amarilla, roja < 0.50). Se **niega** a dar luz verde cuando la imagen no se parece a las usadas para calibrar. |
| Qué NO hace | No diagnostica, no clasifica anomalías, no estima edad gestacional, no sustituye la medida del profesional ni su criterio. No segmenta mejor que otras herramientas (no se ha comparado). |
| Usuario previsto | Personas que investigan o enseñan morfometría en imágenes 3D de embriones y fetos de animales de laboratorio, con formación para entender una probabilidad calibrada. |
| Población / material | **Hoy:** fantomas sintéticos (verdad exacta) y, en curso, ecografía 3D de embriones de ratón (H11). **No** se procesan imágenes de personas (`DATOS_REALES_Y_ETICA.md` §3). |
| Entorno | Ejecución local, sin red, sobre archivos del usuario (`.npy`, `.tif`, `.nii`). |
| Contraindicaciones | Cualquier decisión sobre una gestación, un feto o una persona. Imágenes de un tipo (equipo, modalidad, resolución) que la calibración no cubre. Rasgos más finos que el vóxel. |
| Estado | Investigación y educación. Sin uso clínico. |

**Aclaración que se repite en todo el proyecto:** «probar con una ecografía» significa probar el
software sobre una imagen, no hacer un experimento con personas.

## 2. Qué dice el marco regulatorio verificado (y qué no se encontró)

Fuentes consultadas el 2026-11-10 (ver `docs/OBJETIVOS_V05.md` §4 y la sección «Camino regulatorio»
de `PLAN_DE_VALIDACION.md`):

* **Perú, DS 003-2020-SA.** El software autónomo con finalidad médica se trata como dispositivo
  médico (activo). Hay cuatro clases de riesgo; **el fabricante clasifica** con el Anexo 1 y demuestra
  conformidad con los principios esenciales del Anexo 2. Las investigaciones clínicas siguen la
  Declaración de Helsinki. **No encontré en el texto** los requisitos concretos de sistema de gestión
  de calidad ni la lista de documentos administrativos: eso hay que confirmarlo con asesoría.
* **IEC 62304** (ciclo de vida del software de dispositivos médicos): clases A, B y C según el daño
  que un fallo del software podría causar. La edición 2 aún estaba en borrador.
* **IMDRF/SaMD N41** (evaluación clínica de software como dispositivo médico): tres pilares —
  asociación clínica válida, validación analítica y validación clínica.
* **TRIPOD+AI** (BMJ 2024) y **CLAIM** (actualización 2024): listas para informar modelos de
  predicción y trabajos de IA en imagen.

## 3. Gestión de riesgos (estructura de ISO 14971, aplicada de forma preliminar)

Severidad y probabilidad son **cualitativas y preliminares**: las debe revisar una persona con
formación en gestión de riesgos de dispositivos médicos. La columna «evidencia» cita lo que SÍ se midió.

| ID | Peligro | Situación peligrosa y daño posible | Evidencia (repositorio) | Controles actuales | Riesgo residual / pendiente |
|---|---|---|---|---|---|
| R1 | **Falso verde de volumen**: una medida errónea marcada como fiable | Alguien confía en un volumen que se desvía más de 5 % y lo usa para una conclusión | Verde falso ≤ 7.0 % en dominio (H9d, 6 estratos); con guardia, 10 de 12 estratos desplazados sin verdes y los 2 restantes ≤ 4.1 % (H10b); **pero** `otsu · desenfoque ×2` dejó pasar 28 verdes con 21.4 % falsos | Umbral 0.90; guardia de dominio; intervalo de Wilson informado | No es cero. Un 21 % local lo demuestra. Hace falta más escenarios y una guardia que cubra más |
| R2 | **Fallo silencioso topológico**: un rasgo que la imagen ya perdió (cavidad, hueco) | Se informa Betti = (1,0,0) con luz verde cuando el objeto real tiene cavidad o agujero | 6.6 % de las medidas con topología incorrecta recibió verde; concentrado en `shell_tight` (19.8 % de sus fallos) y `torus_tight` (7.2 %) | Aviso explícito en límites del informe; tabla de resolución mínima (`geovida plan`) | **Sin control técnico posible**: lo que no deja rastro en la imagen no se puede detectar. Solo se mitiga con resolución |
| R3 | **Uso fuera de dominio** (otro equipo, otra modalidad, otro ruido) | El modelo se aplica a imágenes distintas a la calibración y extrapola | Sin guardia, el semáforo de volumen de H6 pasó de 10 % de verde falso en 7 de 12 estratos (hasta 97.3 %, H10a); H12 midió la guardia entre modalidades: acepta como máximo 11.6 % de las imágenes de la otra modalidad (9 de 9 comprobaciones, `RESULTADOS_V05.md`) | Guardia con dos índices (ruido, ancho del borde); fuera de envolvente no hay verde | La guardia de H10b cubre el **volumen**, no la topología: con `global` y desenfoque quedaron 10.4 % y 12.1 % de verdes topológicos falsos. En ecografía simulada desplazada, sin guardia, el volumen dio 11.2 % de verdes falsos en un estrato y la topología de v0.4 un 97–100 % (menos de 100 verdes) |
| R4 | **Perfil declarado incorrecto** | El usuario declara `realistic` para una imagen que es distinta | Es exactamente el escenario de H10 | La guardia es independiente de lo declarado | Misma limitación que R3 |
| R5 | **Transferencia a imagen real no probada** | Se interpreta una luz verde como validada en imágenes reales | Toda la calibración es sintética; H11 (ecografía real de ratón) **no tiene datos todavía** | Aviso en cada certificado e informe («no validado con datos reales») | Abierto hasta que haya H11/H13 |
| R6 | **Sesgo de datos y de población** | Las conclusiones valen solo para lo que se probó (fantomas de 12 formas; un tipo de imagen simulada; un conjunto de ratón) y se generalizan | Diez formas de calibración, dos nunca vistas (H9f); un único conjunto real previsto | Documentación del alcance; etapa 3 del plan (otras especies y modalidades) | No evaluable sin más conjuntos. Sesgo demográfico humano: no aplica todavía, pero sería central en la etapa 4 |
| R7 | **Sobreconfianza del usuario** (sesgo de automatización) | Una luz verde se lee como «aprobado» | — | El texto habla de probabilidad calibrada con simulador, no de «válido»; el informe incluye el aviso | Requiere formación del usuario y una prueba de usabilidad (pendiente) |
| R8 | **Datos personales** | Un informe o un archivo expone la identidad de una persona | — | El informe omite el nombre del archivo por defecto; ejecución local; reglas en `DATOS_REALES_Y_ETICA.md` | El software no puede impedir que alguien lo use con datos humanos: es un control de política, no técnico |
| R9 | **Defecto de software o regresión** | Un cambio altera resultados sin que nadie lo note | Más de 400 pruebas; semillas fijas; los modelos congelados se vigilan con una prueba de igualdad y huella SHA-256; preregistro antes de cada barrido; 23 erratas propias documentadas | Pruebas, trazabilidad, control de cambios (ver `CICLO_DE_VIDA.md`) | Sin revisión independiente del código |
| R10 | **Dependencias (SOUP) que cambian** | Una nueva versión de numpy/scipy/scikit-image altera un resultado | Versiones usadas registradas en cada manifiesto de barrido | Registro de versiones | No hay fijación estricta (`pip freeze`/lock) de las dependencias |
| R11 | **Referencia humana tomada como verdad** | Se confunde acuerdo con un contorno de experto con error real | H11 lo advierte: mide acuerdo, no error exacto | Tolerancia de 10 % para la referencia humana; intervalos por embrión | Variabilidad entre expertos: no medida |
| R12 | **Uso para una decisión sobre una persona** | Se usa la luz verde para decidir algo de una gestación | — | Uso previsto y contraindicaciones escritas en el README, el informe y los certificados | **Control de política**: el software no verifica quién lo usa ni para qué |

## 4. Qué haría falta, y quién tiene que hacerlo

* Una revisión de este análisis por una persona con formación en ISO 14971 / gestión de riesgos.
* Una prueba de usabilidad con usuarios reales (R7).
* Un asesor regulatorio para clasificar el software según el Anexo 1 del DS 003-2020-SA y precisar los
  requisitos de calidad que no encontré en el texto.
* Un grupo clínico y un comité de ética para cualquier etapa con imágenes humanas.

Nada de esto se improvisa desde un repositorio, y este documento no lo sustituye.
