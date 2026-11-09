# Geometría de la Vida (`geovida`) v0.1

**Presupuesto de incertidumbre morfométrica y topológica, con fantomas de
verdad conocida, y un banco de pruebas 4D sintético.**

Antes de comparar la forma de embriones con imágenes 3D hay que saber cuánto
error meten la resolución, la anisotropía del vóxel, el ruido y la
segmentación. Este proyecto mide ese error sobre objetos cuya verdad
(volumen, área, topología) se conoce exactamente, y lo propaga a trayectorias
en pseudo-tiempo.

> **Estado: solo datos sintéticos.** Nada aquí se ha validado con imágenes de
> embriones reales. Los resultados describen el comportamiento del *instrumento
> de medida*, no biología.

## Resultados principales (detalle en [`docs/RESULTADOS.md`](docs/RESULTADOS.md))

* **Topología**: depende del rasgo más estrecho (sólido o vacío), no del
  grosor sólido. En condiciones ideales bastan ~1.5–2 vóxeles a través de él.
* **Volumen**: **no** es universal en t/h (una bola necesita ~8 vóxeles; una
  cáscara ~2). Exploratorio: colapsa en V/(S·h).
* **Segmentación**: suavizar + Otsu protege la topología con ruido pero
  sobrestima el volumen de objetos pequeños; sin limpieza, la topología con
  ruido empeora al aumentar la resolución.
* **4D**: con error de estadificación ≤ ½ intervalo, el sesgo de la media por
  etapa es ≤ 4.3 %; corregirlo cuesta más varianza de la que quita.
  Con n ≤ 3 especímenes por etapa el IC bootstrap cubre ~70 %, no 95 %.
* De 9 predicciones escritas antes de ejecutar, 3 se cumplieron. Los criterios
  están preregistrados en [`docs/PREREGISTRO_H1.md`](docs/PREREGISTRO_H1.md) y
  [`docs/PREREGISTRO_H2.md`](docs/PREREGISTRO_H2.md).

## Lo que este proyecto NO afirma

* No reconstruye ni mide embriones humanos ni de ratón reales (aún).
* "4D" es **pseudo-tiempo transversal** (cada espécimen se mide una vez y se
  asigna a una etapa), no seguimiento longitudinal. El eje temporal de formatos
  como OME-NGFF no debe usarse para codificar etapas de especímenes distintos.
* "5D" no es una dimensión biológica: lo único defendible es el
  *hipercubo de error* (forma × resolución × anisotropía × perfil de imagen ×
  segmentador) que este código llena.
* No es una herramienta diagnóstica ni clínica.
* El estimador de área de v0.1 está sesgado para objetos pequeños (ver
  resultados).

## Uso

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                                  # 113 pruebas, ~3 s
python scripts/run_h1.py --reps 200 --jobs 2     # ~32 min con 2 núcleos
python scripts/analyze_h1.py            # veredictos, tablas y figuras
python scripts/run_h2.py && python scripts/analyze_h2.py     # ~1 min
```

Ejemplo mínimo:

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
| `phantoms.py` | 7 clases con V, S, β, χ y rasgos mínimos analíticos |
| `imaging.py` | Volumen parcial, anisotropía, PSF, ruido, orientación aleatoria |
| `segment.py` / `measure.py` | 3 segmentadores; V, S, Betti, Dice, HD95 |
| `experiment.py` / `analysis.py` | Barrido factorial preregistrado y su análisis |
| `traj4d.py` | Cohortes con error de estadificación; estimadores lineales; bootstrap |

Más en [`docs/METODOS.md`](docs/METODOS.md). Semillas deterministas: el
resultado no depende del número de procesos.

## Origen y transparencia

Esta v0.1 se reescribió desde cero a partir de una revisión crítica de las
versiones 2.5–4.1 del proyecto (cuya validación real era nula y cuyo código v4
nunca se había ejecutado). **Fue desarrollada con asistencia de IA (Claude,
Anthropic); no ha tenido revisión científica humana externa.** Las citas y
afirmaciones sobre literatura que no se verificaron están marcadas como
pendientes en `docs/RESULTADOS.md`.

## Datos reales: pendiente

Candidatos (licencias por confirmar antes de usarlos): IMPC/MusMorph,
Dalmasso et al. 2022 (S-BIAD441), Matula et al. 2021 (solo pruebas técnicas).
Embriones humanos (p. ej. etapas de Carnegie) **no** se usarán sin aprobación
ética e institucional.

## Licencia

MIT (por defecto; cámbiala si prefieres otra). Cita: ver `CITATION.cff`.
