# Resultados — MT-B: ¿la separación entre estadios es la diferencia entre los dos atlas? (23 nov 2026)

> Preregistro: `docs/morpho_trace/PREREGISTRO_ANCLAJE_ATLAS.md` (subido en 838cd55 antes de calcular nada; código y
> pruebas en 9095d8f, 432e5ca y 36bc16c, con CI en verde en Python 3.12 y 3.13). Código: `src/geovida/atlas_anchor.py`
> y `scripts/mtb_anclaje.py`, los de 36bc16c. Datos: MusMorph/IMPC en FaceBase (CC BY 4.0, Devine et al. 2022,
> doi:10.1038/s41597-022-01338-x). Resultados brutos fuera de git: `results/morpho_trace/mtb/` (`gates.json`,
> `analisis.json`). Sin registro y sin descargas. Solo datos animales; nada humano ni clínico.
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta.

## 1. Veredicto

**MT-B1 apoyada; MT-B2 apoyada** [HV, `analisis.json`]. En los landmarks publicados de MusMorph, la separación entre
E15.5 y E18.5 es, a lo largo de su propia dirección, la diferencia entre las dos configuraciones de landmarks de los
atlas: f_A = 0,997 (IC 95 % 0,987–1,004). La parte de **d** que no es esa diferencia, r = 0,200 (IC 0,192–0,212),
queda por debajo del umbral preregistrado de 0,25 y es casi perpendicular a **d**.

Esto **no** dice si la diferencia entre atlas es biológica o técnica (§6).

## 2. Puertas

| Puerta | Criterio | Resultado | Estado |
|---|---|---|---|
| G0-d‴ · reproducción de d | \|d\| = 0,15678 ± 0,0001 | 0,156785 (idéntico a G0-d′ de v2) | **Superada** [HV] |
| G0-p · proyección | Diferencia máxima ≤ 1·10⁻⁸ en 5 configuraciones | 7,6·10⁻¹⁷ | **Superada** [HV] |
| G0-t · validez tangente | ρ de cada atlas a la media ≤ 0,1573 | E15.5: 0,106; E18.5: 0,055 | **Superada** [HV] |

El GPA de las 597 (199 E15.5, 398 E18.5) convergió. La igualdad d = a + e₁₈ − e₁₅ cerró con error 1,7·10⁻¹⁸.

## 3. Estimandos (2000 réplicas, semilla 20261124)

| Estimando | Punto | IC 95 % |
|---|---|---|
| **r = \|d − a\| / \|d\|** (MT-B1) | **0,200** | **0,192 – 0,212** |
| f_A = ⟨a, d̂⟩ / \|d\| | 0,997 | 0,987 – 1,004 |
| \|a\| / \|d\| | 1,016 | 1,007 – 1,025 |
| ángulo(a, d) | 11,4° | 10,9° – 12,0° |
| \|e₁₅\| / \|d\| | 0,157 | 0,149 – 0,169 |
| \|e₁₈\| / \|d\| | 0,100 | 0,095 – 0,105 |
| ⟨e₁₈ − e₁₅, d̂⟩ / \|d\| | 0,003 | −0,004 – 0,013 |

**MT-B2** (punto estimado; distancias en el espacio tangente):

| Estadio | \|e_s\| (media del estadio → su atlas) | Mediana de \|t(x) − t̄_s\| (espécimen → media) | ¿Anclado? |
|---|---|---|---|
| E15.5 | 0,0246 (IC 0,0233–0,0264) | 0,0395 | Sí |
| E18.5 | 0,0156 (IC 0,0150–0,0165) | 0,0314 | Sí |

El punto estimado de r cae dentro de su IC: el desplazamiento hacia arriba del intervalo anunciado en la nota previa
a la subida (§11 del preregistro) es despreciable con 199 y 398 especímenes [HV].

## 4. Sensibilidad (declarada; no cambia el veredicto)

| Variante | r | IC 95 % |
|---|---|---|
| Principal (atlas proyectados, tangentes fijas) | 0,200 | 0,192 – 0,212 |
| 1. Atlas dentro del GPA (599) | 0,200 (f_A 0,997) | — |
| 2. GPA rehecho en cada réplica (200) | — | 0,191 – 0,211 |
| 3a. Mitad 1 de E18.5 (199) | 0,205 | 0,195 – 0,219 · apoyada |
| 3b. Mitad 2 de E18.5 (199) | 0,196 | 0,187 – 0,209 · apoyada |

En todas las variantes r queda entre 0,196 y 0,205, y ningún límite superior pasa de 0,22.

## 5. Predicciones frente a resultado

| Predicción (§7) | Probabilidad dada | Resultado |
|---|---|---|
| Pasan las tres puertas | 90 % | **Sí** |
| MT-B1 apoyada | 60 % | **Sí** |
| MT-B1 refutada | 10 % | No |
| MT-B2 apoyada en los dos estadios | 70 % | **Sí** |
| f_A entre 0,8 y 1,2 | 65 % | **Sí** (0,997) |

Como declaraba el preregistro, estas predicciones no eran ciegas: |a| ≈ |d| ya se conocía por G0-c (0,160).

## 6. Qué muestra y qué no

* [HV] **A lo largo de d, la separación entre estadios es la diferencia entre atlas**: f_A = 0,997, con un IC que
  contiene 1. Los especímenes no desplazan la separación en su propia dirección: ⟨e₁₈ − e₁₅, d̂⟩ / |d| = 0,003, con
  un IC que contiene 0.
* [HV] **El 20 % restante (r) es perpendicular a d.** Cada media de estadio se aparta de su atlas (16 % de |d| en
  E15.5, 10 % en E18.5), pero en direcciones que no alargan ni acortan la separación entre estadios; por eso a y d
  forman 11°.
* [HV] **Cada estadio está anclado a su atlas**: su media está más cerca del atlas que el espécimen típico de la media.
* [HIP] Lectura: la firma de ONTO-MAP (gran separación, poca dispersión a lo largo de **d**) es la que produce
  propagar a cada espécimen los landmarks de dos atlas distintos. Con estos landmarks, **d** no se puede tomar por sí
  sola como una trayectoria biológica.
* **No se puede concluir** si **a** es biológica (los embriones cambian de forma entre E15.5 y E18.5, y cada atlas
  lo recoge) o técnica (el punto *i* no está en el mismo lugar anatómico en los dos atlas). Probablemente es una mezcla;
  separarlas exige landmarks independientes de los atlas.
* Nada sobre la dispersión dentro de cada estadio, la calidad del registro de MusMorph, otros órganos, humanos ni
  uso clínico.

## 7. Siguiente paso (decisión del autor; nada ejecutado)

Según §8 del preregistro: antes de cualquier análisis de trayectorias con MusMorph, **buscar landmarks independientes
de los atlas** (anotación manual de especímenes de E15.5 y E18.5, publicada y con licencia clara) y escribir un
preregistro nuevo. [PROP] Primer paso barato: una búsqueda bibliográfica y de repositorios, sin descargar nada, de
landmarks manuales de cabeza de ratón en esos estadios (p. ej. los usados para validar MusMorph), con su licencia.

MT-A queda cerrada en sus cuatro versiones; MT-B responde la parte que se podía responder sin registrar.
