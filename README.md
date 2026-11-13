# Geometría de la Vida (`geovida`) v0.9

**Un instrumento de medida de formas que sabe cuándo no fiarse de sí mismo.**

Antes de comparar la forma de dos embriones con imágenes hay que saber cuánto error meten la
resolución, el vóxel alargado, el desenfoque, el ruido y la segmentación. Este proyecto mide ese
error sobre objetos cuya verdad (volumen, área, topología) se conoce exactamente, y con eso
construye un **certificado por medida**: una luz verde, amarilla o roja para el volumen y para la
topología, calculada sin conocer la respuesta, que se niega a certificar imágenes distintas de
las que vio al calibrarse.

> **Uso previsto: solo investigación y educación.** No está destinado a uso clínico, diagnóstico,
> cribado, estimación de riesgo fetal ni selección de embriones. Un software con finalidad médica
> es un dispositivo médico regulado.
>
> **Estado: solo datos sintéticos.** Ninguna imagen real, humana o animal, se ha procesado. Los
> resultados describen el comportamiento del *instrumento de medida*, no biología. No hay revisión
> científica externa.

## Qué puede hacer hoy

```bash
pip install -e ".[dev]"
geovida plan                      # ¿cuántos vóxeles necesito para que el volumen sea fiable?
geovida certify imagen.npy --spacing 1 1 2 --segmenter otsu --profile realistic --json cert.json
```

`geovida plan` responde antes de adquirir (guía derivada de fantomas, no una garantía):

| Segmentador · perfil | Bola (diámetro) | Cilindro (diámetro) | Lámina (grosor) |
|---|---|---|---|
| global · realistic | 6.7 vóxeles | 5.0 | 3.3 |
| otsu · realistic | 8.0 | 6.0 | 4.0 |
| smoothed_otsu · realistic | 13.2 | 9.9 | 6.6 |

`geovida certify` responde después de medir: luz del volumen, luz de la topología, dónde está el
punto más frágil de la forma (por ejemplo, el cuello que une dos partes) y si la imagen cae dentro
del dominio de calibración.

También hay un laboratorio interactivo en el navegador (`docs/laboratorio/`), una exposición
interactiva con demostraciones en vivo y cuestionario (`docs/exposicion/`) y un visor 4D para
Unity (`unity/`, **sin compilar**: en el entorno de desarrollo no hay Unity).

## Resultados, prueba por prueba

Cada prueba fijó criterios y predicciones en git **antes** de ejecutarse. Detalle en `docs/`.

| Prueba | Pregunta | Resultado |
|---|---|---|
| H1 (v0.1) | ¿Basta contar vóxeles a través del rasgo más fino? | Refutada en parte: vale para la topología, no para el volumen (bola: ~8 vóxeles; cáscara: ~2). H1c **falsada** |
| H2 (v0.1) | ¿Cuánto distorsiona una trayectoria 4D el error de estadificación? | Sesgo ≤ 4.3 %; corregirlo cuesta más varianza de la que quita; con n ≤ 3 el intervalo cubre ~70 % |
| H3 (v0.2) | ¿Predice mejor V/(S·h) que el grosor? | Apoyada (usa V y S verdaderos) |
| H4 (v0.2) | ¿Mejora el área un estimador por distancia con signo? | Apoyada; no sirve por debajo de ~3 vóxeles |
| H5 (v0.2) | ¿Aguanta una imagen 2D tipo ecografía? | 3 de 5; la topología con moteado no se recupera |
| H6 (v0.3) | ¿Puede saber, sin la verdad, si su volumen es fiable? | **5 de 5.** Verde falso 0.4–2.6 % |
| H7 (v0.3) | ¿Arregla la topología 2D una limpieza que escala con el objeto? | 1 de 3 |
| H8 (v0.3) | ¿Mejora la tasa de crecimiento 4D al descartar las etapas en rojo? | **3 de 3.** Error mediano de 3–64 % a 1–2 %; con suavizado, 70–89 % de series sin tasa |
| H9 (v0.4) | ¿Puede saber si la topología medida es correcta? | **Primaria apoyada** (verde falso ≤ 7.0 % en los 6 estratos; ≤ 7.8 % con formas nuevas). 4 de 6 apoyadas, 1 parcial, 1 no: sin guardia, 2 de 8 estratos de imágenes desplazadas superan 10 % |
| H10 (v0.4) | ¿Se da cuenta de que una imagen está fuera de su calibración? | **4 de 4.** Sin guardia, el semáforo de volumen daba hasta 97 % de verdes falsos con el doble de ruido; con guardia, 10 de 12 estratos quedan sin verdes y los otros 2 en ≤ 4.1 %. Deja pasar 28 verdes con 21 % de falsas en un caso |
| H12 (v0.5) | ¿Se puede recalibrar para ecografía 3D **simulada** (moteado, atenuación)? | **Primaria apoyada solo en 2 de 6 estratos** (`smoothed_otsu`: 0–0.2 % de verdes falsos de volumen, 6.6 % de topología); `global` y `otsu` nunca dan verde. 6 de 8 apoyadas, 1 parcial y 1 no apoyada (H12a: v0.4 sin guardia no daba verdes falsos, solo quedaba vacío); dos de las apoyadas lo son por margen mínimo. Mancuerna: 11 de 30 verdes de topología falsos (no evaluable) |

Documentos: [`RESULTADOS.md`](docs/RESULTADOS.md) (v0.1), [`RESULTADOS_V02.md`](docs/RESULTADOS_V02.md),
[`RESULTADOS_V03.md`](docs/RESULTADOS_V03.md), [`RESULTADOS_V04.md`](docs/RESULTADOS_V04.md),
[`RESULTADOS_V05.md`](docs/RESULTADOS_V05.md) (ecografía simulada),
[`ERRATA.md`](docs/ERRATA.md) (26 errores propios, con causa y prevención) y
[`ANTECEDENTES_V04.md`](docs/ANTECEDENTES_V04.md) (qué existe ya en la literatura).

## v0.5: ecografía simulada (H12), resultado

Se añadió un simulador de ecografía (moteado, atenuación) y se recalibró el certificado, con criterios
fijados antes de calibrar ([`PREREGISTRO_H12.md`](docs/PREREGISTRO_H12.md)) y el modelo congelado antes de los
barridos de confirmación. Resultado ([`RESULTADOS_V05.md`](docs/RESULTADOS_V05.md)): la primaria (H12c)
queda **apoyada solo en 2 de 6 estratos**; en el resto el certificado nunca da verde. Donde se evalúa
(`smoothed_otsu`), 0–0.2 % de verdes falsos de volumen y ≈ 60–66 % de las medidas correctas con verde
(v0.4 con su guardia: ≈ 0 %). Puntos débiles publicados: la topología de la mancuerna (11 de 30 verdes
falsos, por debajo del tamaño mínimo preregistrado), H12g apoyada por un solo estrato (11.2 %), y que
solo un segmentador de tres es certificable en ecografía. **Solo simulación.**

## v0.6 · Programa B: biometría temprana con certificado (H13, H14), resultado

Un segundo programa, que reutiliza el instrumento de incertidumbre pero lo propaga hasta una pregunta que
alguien tendría que contestar: **¿cuántos días puede estar equivocada una datación por longitud cráneo-rabadilla?** y
**¿está el grosor medido del mismo lado de un umbral que el verdadero?** Fantomas 2D con verdad exacta, modelo de error
congelado, confirmación con semillas nuevas ([`PREREGISTRO_H13.md`](docs/PREREGISTRO_H13.md),
[`RESULTADOS_V06.md`](docs/RESULTADOS_V06.md)). Los cuatro criterios agregados quedaron apoyados (falso verde 0.5 % en
datación y 1.8 % en decisión), **pero** la ranura con función de dispersión > 3.5 px tiene 18.5 % de falsos verdes
(exploratorio), el control `otsu` falla (30 %), y una datación certificada no es una datación correcta (domina la
variación biológica). Módulos nuevos: `geovida.dating` (INTERGROWTH-21st, Robinson), `geovida.atlas` (estadios de
Carnegie), `geovida.biometry`, `geovida.h13`, `geovida.labeling` (validador de manifiestos de anotación con
compuerta para datos humanos). **H14** ([`PREREGISTRO_H14.md`](docs/PREREGISTRO_H14.md)) probó con casos nuevos una compuerta
de «tasa de medidas utilizables»: cinco criterios apoyados, pero H14a se cumple porque la compuerta **se niega a certificar**
el estrato difícil (no lo arregla), cuesta 12 % de los verdes de la ranura, y en casos nuevos el fallo original fue menor que en
H13 (6.6 % de los verdes frente a 18.5 %; el estrato lo elegí después de verlo). Atlas de los 23 estadios con rotulado y niveles de evidencia:
[`ATLAS_ESTADIOS.md`](docs/ATLAS_ESTADIOS.md); protocolo de revisión de panel (propuesta; el panel aún no existe):
[`PANEL_DE_REVISION.md`](docs/PANEL_DE_REVISION.md). **Solo simulación; sin uso clínico.**

## v0.7 · De simulador a instrumento que mide una imagen real (H15), resultado

Lo nuevo es una **orden para medir una imagen 2D real** y, sobre todo, una prueba de cuánto hay que fiarse de ella:

```bash
geovida real2d FOTO.jpg --roi X0 Y0 X1 Y1 --ruler X1 Y1 X2 Y2 --ruler-mm 10 --printed-crl-mm 12.3 --out ../informe_privado
```

Saca la escala de la regla impresa, mide una longitud dentro de una región que fija una persona, aplica el modelo de error
congelado para cada desenfoque posible (en mm; la foto no dice cuál es) y escribe un informe con control de calidad y
superposición. Privacidad por diseño: sin EXIF, solo el SHA-256 del archivo, informes fuera del repositorio; con `--human` exige
una nota de autorización que queda como **declaración sin verificar**. **Sobre imagen real el semáforo no sale verde**, y ahora hay un
dato que lo justifica: la hipótesis **H15** ([`PREREGISTRO_H15.md`](docs/PREREGISTRO_H15.md),
[`RESULTADOS_V07.md`](docs/RESULTADOS_V07.md)) simuló la cadena pantalla → impresión → foto y encontró que el certificado de datación
**no resiste**: 11.9 % de falsos verdes (IC 95 % 9.7–14.1 %, veredicto *no concluyente* por la regla fijada) frente a 1.2 % sin cadena,
probabilidades demasiado optimistas (ECE 0.195) y un error que crece con la compresión logarítmica (4.3 %, 9.3 %, 22.0 %). El certificado de
decisión sí aguanta (0.8 %). El semáforo no se entera de la cadena (776 verdes con ella, 774 sin ella). **Todo es simulación y la cadena es mía.**
Otros documentos: [`REAL2D_METODO.md`](docs/REAL2D_METODO.md) (método, límites y lo descartado: un estimador del desenfoque que
fracasó), [`PREREGISTRO_REAL2D_PILOTO.md`](docs/PREREGISTRO_REAL2D_PILOTO.md) (el piloto n = 1, escrito antes de medir ninguna imagen real),
[`RUTA_DE_VALIDACION_REAL.md`](docs/RUTA_DE_VALIDACION_REAL.md) (compuertas G0–G4 y tamaños de muestra) y
[`ARQUITECTURA.md`](docs/ARQUITECTURA.md). **Todavía no se ha medido ninguna imagen real, y el uso es solo de investigación y educación.**

## v0.8 · Primera ecografía 2D real medida (n = 1) y trayectoria de referencia

* **Piloto REAL2D** ([`RESULTADOS_V08.md`](docs/RESULTADOS_V08.md)): el usuario aportó una ecografía (con la declaración, sin verificar, de que
  tiene el permiso legal). Con escala, región y segunda lectura fijadas antes de correr la medida, `geovida real2d` midió una longitud cráneo-nalga de **37.57 mm**
  frente a **37.4 mm** impresos por el equipo (+0.5 %), sin moverse al cambiar de segmentador ni de región. **Es una imagen y no valida nada**: la escala sale de un supuesto (10 mm entre marcas),
  la cifra impresa tiene operador desconocido y la imagen es una foto de una impresión con mapa de color, un caso donde H15 vio que el certificado de datación falla. Mis predicciones sobre el piloto
  fueron malas (3 de 6; Brier 0.31). Nada identificable está en el repositorio.
* **`geovida trajectory`**: franja de la referencia poblacional INTERGROWTH-21st (ecuaciones leídas en el texto abierto y comprobadas contra su Tabla 2) en las semanas siguientes, con el error de medida y
  la incertidumbre de la edad propagados y dos escenarios extremos. **No predice el crecimiento ni el aspecto de ningún feto**, solo calcula entre 58 y 105 días, y sus dos escenarios no están validados:
  **H17** ([`PREREGISTRO_H17.md`](docs/PREREGISTRO_H17.md)) pide datos seriados reales que no tengo.

## v0.9 · Plan externo incorporado con verificación, módulos de acuerdo y de color

* **PDF externo** ([`INTEGRACION_PDF_EXTERNO.md`](docs/INTEGRACION_PDF_EXTERNO.md)): un plan generado con otra IA se incorporó **verificando** cada referencia contra PubMed y las editoriales.
  Las 8 principales existen; encontré 3 errores del PDF y 1 contradicción interna. Se adoptaron las etiquetas de evidencia, «el individuo es la unidad» y métricas de acuerdo; **no** se adoptaron el `robustness_index`,
  la homología persistente ni la línea de cartílago nasal de ratón (motivos escritos).
* **`geovida.agreement`** (Dice, IoU, HD95, ASSD, diferencia relativa, Bland–Altman) y **`geovida.colorbar`** (linealiza un mapa de color con la barra de la propia captura): 30 pruebas, con mutaciones comprobadas.
* **Sensibilidad al mapa de color en la imagen real** ([`RESULTADOS_V09.md`](docs/RESULTADOS_V09.md)): por la regla fijada de antemano el resultado es **no interpretable** (distancia 0.0642 contra un límite de 0.06).
  Descriptivamente, la longitud no cambió (37.568 mm con luminancia y con la barra) y el área sí, −1.7 %. **n = 1; no valida nada.**

## Siguiente fase (v0.5, en curso): embriones reales

Hasta v0.4 todo es sintético. v0.5 lleva el certificado a **ecografía 3D real de embriones de ratón**
con contornos de expertos, sin reajustar nada y con los criterios fijados antes de abrir los datos
([`PREREGISTRO_H11.md`](docs/PREREGISTRO_H11.md)). Propósito, objetivos y ruta por etapas, hasta la
puerta ética y regulatoria que exigiría cualquier uso con humanos:
[`OBJETIVOS_V05.md`](docs/OBJETIVOS_V05.md). Ya existen el lector de volúmenes NIfTI
(`geovida.realdata`) y `geovida datasheet` (ficha de volúmenes; guía paso a paso en
[`GUIA_DATOS_REALES.md`](docs/GUIA_DATOS_REALES.md)). **Todavía no se ha procesado ninguna imagen real.** El código de H11 (`geovida.h11`, `scripts/run_h11.py`)
y el preregistro de su variante recalibrada ([`PREREGISTRO_H12R.md`](docs/PREREGISTRO_H12R.md)) están listos y
probados con volúmenes sintéticos; esperan los volúmenes.

## Lo que este proyecto NO afirma

* No reconstruye ni mide embriones humanos ni de ratón reales (aún).
* «4D» es **pseudo-tiempo transversal**: cada espécimen se mide una vez y se asigna a una etapa.
* «5D» no es una dimensión biológica. En bioimagen ya significa x, y, z, canal y tiempo. Lo que
  aquí se añade es un **eje de escala de medición**: la misma imagen, medida otra vez más gruesa.
* Las ideas sueltas no son nuevas (persistencia topológica, convergencia entre escalas, detección
  de fallos en segmentación). Lo que no hemos identificado en la literatura es su combinación como
  probabilidad por medida calibrada contra verdad conocida. Es una ausencia en nuestra búsqueda,
  no una prueba de novedad.
* Un rasgo que la imagen ya perdió por completo no deja rastro: ningún semáforo lo detecta.
* No es una herramienta diagnóstica ni clínica, y no reduce la mortalidad neonatal ni mejora
  diagnósticos: eso requeriría validación clínica que no existe.
* «Pruebas en humanos» aquí significaría, como mucho, probar el *software* sobre una imagen,
  nunca un experimento con personas, y solo con las condiciones de
  [`DATOS_REALES_Y_ETICA.md`](docs/DATOS_REALES_Y_ETICA.md).

## Reproducir

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                                           # 351 pruebas, ~15 s
python scripts/run_h6.py --phase test && python scripts/analyze_h6.py     # ~17 min, 2 núcleos
python scripts/run_h7.py && python scripts/analyze_h7.py                  # ~1 min
python scripts/run_h8.py && python scripts/analyze_h8.py                  # ~5 min
python scripts/run_h9.py --set cal && python scripts/calibrate_h9.py      # ~19 min
for s in test unseen shift; do python scripts/run_h9.py --set $s; done    # ~45 min
python scripts/analyze_h9.py
```

Semillas deterministas por celda: el resultado no depende del número de procesos, y dos corridas
del mismo barrido dan tablas idénticas (comprobado en H8).

## Estructura

| Módulo | Qué hace |
|---|---|
| `phantoms.py`, `twod.py` | 12 formas 3D y 4 formas 2D con volumen, área, Betti y rasgos mínimos analíticos |
| `imaging.py` | Volumen parcial, anisotropía, PSF, ruido, orientación aleatoria; perfiles de calibración y perfiles «desplazados» |
| `segment.py`, `measure.py`, `topology.py` | Segmentadores preregistrados; V, S (3 estimadores), profundidad media, Betti con adyacencia explícita |
| `budget.py`, `h6.py` | Semáforo de volumen por profundidad media (H6) |
| `topomargin.py` | Margen de persistencia topológica (geométrico y de intensidad) y localización del punto frágil |
| `scaleaxis.py` | Eje de escala: re-medición a ×2 y ×4 |
| `domain.py` | Guardia de dominio: ruido y ancho de borde medidos en la imagen |
| `h9.py`, `certsweep.py` | Calibración, congelado y veredictos de H9/H10 |
| `certificate.py`, `cli.py` | Certificado por medida y línea de órdenes |
| `growth.py`, `traj4d.py` | Series de crecimiento con semáforo (H8) y cohortes con error de estadificación (H2) |
| `experiment.py`, `analysis.py`, `h3.py`, `h5.py`, `h7.py` | Barridos factoriales preregistrados y su análisis, con veredictos de tres estados |
| `provenance.py` | Commit y estado del código al empezar cada corrida |

## Método de trabajo (por qué se puede confiar en el proceso, no en mí)

* Criterios y predicciones se confirman en git **antes** de correr cada barrido; los modelos se
  congelan **antes** de la confirmación.
* Un valor no calculable es «no evaluable», nunca «no apoyada».
* Toda expectativa numérica nueva en una prueba sale de un piloto citado.
* Una pieza calibrada se prueba también con condiciones que su calibración no vio.
* La suite completa corre antes de cada commit; cada figura se mira antes de publicarla.
* Los hallazgos *post hoc* se marcan como tales.

## Origen y transparencia

Reescrito desde cero a partir de una revisión crítica de las versiones 2.5–4.1 del proyecto (cuya
validación real era nula). **Fue desarrollado con asistencia de IA (Claude, Anthropic); no ha
tenido revisión científica humana externa.** Autor del proyecto: Fabián Trelles.

## Siguiente paso real

Datos públicos con licencia verificada, empezando por imágenes 2D (HC18, CC BY 4.0; EmbryoNet,
CC BY 4.0), con un preregistro propio; y un laboratorio aliado o fantomas físicos para comprobar
que el certificado se sostiene fuera del simulador. Hasta entonces, esto es una herramienta de
método, no un resultado biológico.

## Licencia

MIT. Cita: ver `CITATION.cff`.
