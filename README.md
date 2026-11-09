# Geometría de la Vida (`geovida`) v0.2

**Presupuesto de incertidumbre morfométrica y topológica, con fantomas de
verdad conocida, un banco de pruebas 4D sintético y una prueba de estrés 2D
tipo ecografía (también sintética).**

Antes de comparar la forma de embriones con imágenes hay que saber cuánto error
meten la resolución, la anisotropía del vóxel, el ruido (o el moteado) y la
segmentación. Este proyecto mide ese error sobre objetos cuya verdad (volumen,
área, perímetro, topología) se conoce exactamente, y lo propaga a trayectorias
en pseudo-tiempo.

> **Uso previsto: solo investigación y educación.** No está destinado a uso
> clínico, diagnóstico, cribado, estimación de riesgo fetal ni selección de
> embriones. Un software con finalidad médica es un dispositivo médico regulado.
>
> **Estado: solo datos sintéticos.** Ninguna imagen real, humana o animal, se ha
> procesado. Los resultados describen el comportamiento del *instrumento de
> medida*, no biología.

## Resultados principales

Detalle: [`docs/RESULTADOS.md`](docs/RESULTADOS.md) (v0.1) y
[`docs/RESULTADOS_V02.md`](docs/RESULTADOS_V02.md) (v0.2).

**v0.1**

* **Topología**: depende del rasgo más estrecho (sólido o vacío), no del
  grosor sólido. En condiciones ideales bastan ~1.5–2 vóxeles a través de él.
* **Volumen**: **no** es universal en t/h (una bola necesita ~8 vóxeles; una
  cáscara ~2). H1c (la anisotropía colapsa con el vóxel peor) quedó **falsada**.
* **4D**: con error de estadificación ≤ ½ intervalo, el sesgo de la media por
  etapa es ≤ 4.3 %; corregirlo cuesta más varianza de la que quita. Con n ≤ 3
  especímenes por etapa el IC bootstrap cubre ~70 %, no 95 %.

**v0.2** (criterios y predicciones fijados antes de correr)

* **Confirmación 3D (H3, formas y semillas nuevas): apoyada.** La longitud
  volumen/área Q = V/(S·h) predice mejor que el grosor, está calibrada y su
  umbral se conserva. Matiz: la ventaja es clara con el umbral oráculo y con
  Otsu en imagen realista, es un empate con Otsu en imagen ideal y queda dentro
  del ruido con suavizado. Solo sólidos simples; Q usa V y S verdaderos.
* **Área (H4): apoyada.** El estimador por distancia con signo baja el sesgo de
  v0.1 (a 4 vóxeles, de −17…−34 % a −3…−11 %), pero no sirve por debajo de ~3
  vóxeles.
* **2D tipo ecografía (H5): 3 de 5.** El área es fiable desde ~4 px; la
  circunferencia por elipse necesita ~12 px con moteado; la topología de un
  anillo no se recupera con fiabilidad ni con 20 px sin limpieza.
* **La limpieza mínima ayuda y daña:** +7 a +62 puntos de topología correcta en
  cáscaras, tubos y toros, pero borra cavidades reales < 8 vóxeles (cáscara
  fina a 4 vóxeles: 93 % → 0 %). `clean_report` lo hace visible.
* **Predicciones mías:** v0.1, 3 de 9; v0.2, 9 de 12.
* **Errores propios corregidos:** [`docs/ERRATA.md`](docs/ERRATA.md) (12 entradas,
  con causa y prevención).

## Lo que este proyecto NO afirma

* No reconstruye ni mide embriones humanos ni de ratón reales (aún).
* "4D" es **pseudo-tiempo transversal** (cada espécimen se mide una vez y se
  asigna a una etapa), no seguimiento longitudinal.
* "5D" no es una dimensión biológica: lo único defendible es el
  *hipercubo de error* (forma × resolución × anisotropía × perfil de imagen ×
  segmentador) que este código llena.
* No es una herramienta diagnóstica ni clínica, y no reduce la mortalidad
  neonatal ni mejora diagnósticos: eso requeriría validación clínica que no
  existe.
* "Pruebas en humanos" aquí significaría, como mucho, probar el *software* sobre
  una imagen, nunca un experimento con personas, y solo con las condiciones de
  [`docs/DATOS_REALES_Y_ETICA.md`](docs/DATOS_REALES_Y_ETICA.md).
* No hay revisión científica humana externa.

## Uso

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                                           # 184 pruebas, ~5 s
python scripts/run_h1.py --reps 200 --jobs 2     # ~32 min con 2 núcleos
python scripts/analyze_h1.py                     # veredictos, tablas y figuras
python scripts/run_h2.py && python scripts/analyze_h2.py          # ~1 min
python scripts/run_h3.py --reps 200 --jobs 2     # ~16 min con 2 núcleos
python scripts/analyze_h3.py
python scripts/run_2d.py && python scripts/analyze_2d.py
python scripts/explore_v02_extras.py             # exploratorio, ~3 min
```

Ejemplo mínimo (3D):

```python
import numpy as np
from geovida.phantoms import make_phantom
from geovida.imaging import render, spec_for_t_over_h
from geovida.segment import segment
from geovida.measure import measure_mask, relative_errors

ph = make_phantom("torus", t=1.0)                       # verdad analítica en ph.truth
spec = spec_for_t_over_h(t_over_h=4, anisotropy=2.0, profile="realistic")
img = render(ph, spec, np.random.default_rng(0))
mask = segment("smoothed_otsu", img.image, img.spacing)
print(relative_errors(measure_mask(mask, img.spacing), ph.truth))
```

## Estructura

| Módulo | Qué hace |
|---|---|
| `topology.py` | Betti y χ en 3D con adyacencia explícita (26,6) / (6,26) |
| `phantoms.py` | 10 clases 3D con V, S, β, χ y rasgos mínimos analíticos (7 de v0.1 + cápsula, cilindro, oblato) |
| `imaging.py` | Volumen parcial, anisotropía, PSF, ruido, orientación aleatoria |
| `segment.py` / `measure.py` | Segmentadores (3 preregistrados + `otsu_clean` con `clean_report`); V, S (3 estimadores, incl. `area_sdf`), Betti, Dice, HD95 |
| `experiment.py` / `analysis.py` | Barridos factoriales preregistrados (H1, H3) y su análisis, con veredictos de tres estados |
| `h3.py` | Evaluación confirmatoria de modelos congelados (H3) y del estimador de área (H4) |
| `twod.py` / `h5.py` | Fantomas 2D con moteado multiplicativo, medidas 2D (área, perímetro de Crofton, circunferencia por elipse, Betti) y veredictos H5 |
| `traj4d.py` | Cohortes con error de estadificación; estimadores lineales; bootstrap |
| `provenance.py` | Commit y estado «sucio» solo del código versionado, para los manifiestos |

Más en [`docs/METODOS.md`](docs/METODOS.md). Semillas deterministas por celda: el
resultado no depende del número de procesos.

## Método de trabajo (por qué se puede confiar en el proceso, no en mí)

* Criterios y predicciones se confirman en git **antes** de correr cada barrido.
* Un valor no calculable es «no evaluable», nunca «no apoyada».
* Toda expectativa numérica nueva en una prueba sale de un piloto citado.
* La suite completa corre antes de cada commit; cada figura se mira antes de
  publicarla.
* Los hallazgos *post hoc* se marcan como tales y no cuentan hasta confirmarse
  con datos nuevos.

## Origen y transparencia

Esta versión se reescribió desde cero a partir de una revisión crítica de las
versiones 2.5–4.1 del proyecto (cuya validación real era nula). **Fue
desarrollada con asistencia de IA (Claude, Anthropic); no ha tenido revisión
científica humana externa.** Las citas y afirmaciones sobre literatura que no se
verificaron están marcadas como pendientes en `docs/RESULTADOS.md`.

## Datos reales: pendiente

Candidatos (licencias por confirmar antes de usarlos): IMPC/MusMorph,
Dalmasso et al. 2022 (S-BIAD441), Matula et al. 2021 (solo pruebas técnicas); y,
para 2D, conjuntos públicos de ecografía fetal con licencia verificada. Imágenes
humanas **no** se procesarán sin consentimiento, anonimización, base legal y
aprobación ética (ver `docs/DATOS_REALES_Y_ETICA.md`).

## Licencia

MIT (por defecto; cámbiala si prefieres otra). Cita: ver `CITATION.cff`.
