# Geometría de la Vida (`geovida`) v0.4

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

Documentos: [`RESULTADOS.md`](docs/RESULTADOS.md) (v0.1), [`RESULTADOS_V02.md`](docs/RESULTADOS_V02.md),
[`RESULTADOS_V03.md`](docs/RESULTADOS_V03.md), [`RESULTADOS_V04.md`](docs/RESULTADOS_V04.md),
[`ERRATA.md`](docs/ERRATA.md) (24 errores propios, con causa y prevención) y
[`ANTECEDENTES_V04.md`](docs/ANTECEDENTES_V04.md) (qué existe ya en la literatura).

## Siguiente fase (v0.5, en curso): embriones reales

Hasta v0.4 todo es sintético. v0.5 lleva el certificado a **ecografía 3D real de embriones de ratón**
con contornos de expertos, sin reajustar nada y con los criterios fijados antes de abrir los datos
([`PREREGISTRO_H11.md`](docs/PREREGISTRO_H11.md)). Propósito, objetivos y ruta por etapas, hasta la
puerta ética y regulatoria que exigiría cualquier uso con humanos:
[`OBJETIVOS_V05.md`](docs/OBJETIVOS_V05.md). Ya existen el lector de volúmenes NIfTI
(`geovida.realdata`) y `scripts/real_datasheet.py`. **Todavía no se ha procesado ninguna imagen real.**

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
