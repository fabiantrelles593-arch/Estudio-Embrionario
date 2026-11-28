# Resultados — MT-C: ¿la diferencia entre atlas se sostiene en los 22 landmarks anatómicos? (23 nov 2026)

> Preregistro: `docs/morpho_trace/PREREGISTRO_HOMOLOGOS.md` (subido en 893f692 antes de calcular nada; código y
> pruebas en fc8bacd, a0fca9d y d9c3abf, con CI en verde en Python 3.12 y 3.13). Datos: MusMorph/IMPC en FaceBase
> (CC BY 4.0, Devine et al. 2022, doi:10.1038/s41597-022-01338-x) y, solo para G0-o, los `.tag` de atlas del
> repositorio MusMorph. Resultados brutos fuera de git: `results/morpho_trace/mtc/` (`gates.json`, `analisis.json`).
> Sin registro. Solo datos animales; nada humano ni clínico.
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta.

## 1. Veredicto

**MT-C1 apoyada; MT-C2 apoyada** [HV, `analisis.json`].

* Con solo los 22 landmarks anatómicos homólogos, la separación entre estadios sigue siendo la diferencia entre los
  dos atlas: r₂₂ = 0,206 (IC 95 % 0,197–0,220), por debajo del umbral de 0,25. La igualdad de MT-B no dependía de
  los parches.
* La diferencia entre atlas **se concentra en seis landmarks contiguos, del 17 al 22**: los cinco con más peso
  (18, 19, 22, 17 y 21) llevan el 77 % de |a₂₂|² (con un reparto uniforme sería el 23 %), y los seis juntos, el 83 %.

Esto sigue sin decir si esa diferencia es biológica o de anotación (§7).

## 2. Puertas

| Puerta | Criterio | Resultado | Estado |
|---|---|---|---|
| G0-o · orden | (a) filas 1–22 iguales a las de GitHub (≤ 1·10⁻⁴ mm); (b) 21 caras no degeneradas | (a) diferencia 0,0 en los dos atlas; (b) área mínima 0,0151 mm² (E15.5) y 0,0087 mm² (E18.5) | **Superada** [HV] |
| G0-p₂₂ · proyección | ≤ 1·10⁻⁸ | 3,1·10⁻¹⁶ | **Superada** [HV] |
| G0-t₂₂ · validez tangente | ρ de cada atlas a la media ≤ ρ máxima de las 597 (0,1516) | E15.5: 0,111; E18.5: 0,055 | **Superada** [HV] |

El GPA de las 597 con 22 landmarks convergió; |d₂₂| = 0,1532 (nunca calculada antes; se informa, no se pone a
prueba). La igualdad d = a + e₁₈ − e₁₅ cerró con error 6,9·10⁻¹⁸.

## 3. Estimandos (2000 réplicas, semilla 20261125)

| Estimando | 22 landmarks | IC 95 % | MT-B (540 puntos) |
|---|---|---|---|
| **r = \|d − a\| / \|d\|** (MT-C1) | **0,206** | **0,197 – 0,220** | 0,200 |
| f_A = ⟨a, d̂⟩ / \|d\| | 1,051 | 1,037 – 1,064 | 0,997 |
| \|a\| / \|d\| | 1,070 | 1,056 – 1,084 | 1,016 |
| ángulo(a, d) | 10,8° | 10,3° – 11,4° | 11,4° |
| \|e₁₅\| / \|d\| | 0,176 | 0,166 – 0,193 | 0,157 |
| \|e₁₈\| / \|d\| | 0,095 | 0,091 – 0,101 | 0,100 |
| ⟨e₁₈ − e₁₅, d̂⟩ / \|d\| | −0,051 | −0,064 – −0,037 | 0,003 |

Cada media de estadio sigue anclada a su atlas (|e_s| menor que la mediana de distancias espécimen–media: 0,027
frente a 0,043 en E15.5 y 0,014 frente a 0,030 en E18.5).

## 4. Contribución por landmark (MT-C2 y MT-C3; descriptivo)

| Landmark | cᵢ (parte de \|a₂₂\|²) | \|aᵢ\| / sᵢ | ángulo(aᵢ, dᵢ) |
|---|---|---|---|
| **18** | 0,208 | 6,3 | 3,0° |
| **19** | 0,193 | 7,7 | 5,5° |
| **22** | 0,133 | 5,6 | 4,4° |
| **17** | 0,125 | 6,0 | 4,8° |
| **21** | 0,115 | 4,9 | 8,6° |
| 20 | 0,060 | 4,0 | 6,8° |
| Los otros 16 | 0,001 – 0,042 cada uno; 0,166 en total | 0,5 – 3,2 | 2,9° – 38,5° |

sᵢ es la dispersión de ese landmark dentro de estadio. En los landmarks 17–22, la diferencia entre atlas es de 4 a
8 veces esa dispersión y casi paralela a la separación entre estadios en ese punto (3°–9°). En los otros 16 es del
orden de la dispersión (0,5 a 3,2 veces).

Según `Patches.tsv`, los landmarks 17–22 son vértices de un mismo grupo de caras contiguas (las cuatro primeras caras
comparten el 19; dos de ellas, también el 20) [HV]. Sus nombres anatómicos no se han comprobado (§7, desviación).

## 5. Sensibilidad (declarada; no cambia el veredicto)

| Variante | r | IC 95 % | Concentración (5 primeros) |
|---|---|---|---|
| Principal (22 landmarks) | 0,206 | 0,197 – 0,220 | 0,774 (18, 19, 22, 17, 21) |
| 1. Filas 1–25 | 0,210 | 0,201 – 0,224 · apoyada | 0,758 (los mismos 5) |
| 2. Atlas dentro del GPA | 0,206 (f_A 1,051) | — | — |
| 3. GPA rehecho en cada réplica (200) | — | 0,198 – 0,220 | — |

## 6. Predicciones frente a resultado

| Predicción (§7) | Probabilidad dada | Resultado |
|---|---|---|
| Pasan las puertas | 85 % | **Sí** |
| MT-C1 apoyada | 55 % | **Sí** |
| MT-C1 refutada | 10 % | No |
| MT-C2: 5 primeros ≥ 50 % | 50 % | **Sí** (77 %) |
| r₂₂ mayor que 0,200 | 60 % | **Sí**, por poco (0,206) |

## 7. Qué muestra y qué no

* [HV] **La igualdad d ≈ a de MT-B se sostiene en los landmarks anatómicos**; no era un efecto de cómo se reparten
  los parches.
* [HV] **La diferencia entre atlas vive en seis landmarks contiguos (17–22).** Allí es grande frente a la
  variación entre especímenes y apunta en la misma dirección que la separación entre estadios. En los otros 16 apenas
  hay diferencia entre atlas.
* [HV] Con 22 landmarks, la diferencia entre atlas supera un 5 % a la separación entre estadios a lo largo de **d**
  (f_A = 1,051): los especímenes acercan un poco los estadios respecto de sus atlas. Con 540 puntos ese efecto no se
  veía (0,003, con un IC que contenía 0).
* [HIP] Dos lecturas posibles, que estos datos no separan: (1) biológica, si la región de los landmarks 17–22 es la
  que más cambia entre E15.5 y E18.5; (2) de anotación, si en uno de los dos atlas esos puntos se colocaron en otro
  lugar anatómico (los atlas se construyeron por separado y con resolución distinta, ver
  `BUSQUEDA_LANDMARKS_INDEPENDIENTES.md` §4).
* **No se puede concluir** si **a** es biológica o técnica; tampoco nada sobre los landmarks concretos más allá de
  describirlos (se eligieron con los datos).
* Nada sobre humanos ni uso clínico.

**Desviación respecto de D4 (no toca ningún cálculo).** D4 preveía leer la Tabla S2 para nombrar los landmarks. El
material suplementario solo se obtiene como PDF descargable (la página de Nature pide identificarse y el enlace de PMC
devuelve una página intermedia), y una descarga exige autorización expresa con nombre y tamaño del archivo. Se
aplica la alternativa escrita en D4: los landmarks se informan por número.

## 8. Siguiente paso (decisión del autor; nada ejecutado)

Según §8 del preregistro: **camino B, limitado a los landmarks 17–22**. [PROP] Antes:

1. Nombrar los landmarks 17–22 con la Tabla S2 (descarga del PDF suplementario de Devine et al. 2022, con
   autorización).
2. Preregistrar una anotación manual de esos seis landmarks (y de unos pocos estables como referencia) en una muestra
   pequeña de imágenes de cada estadio ya en disco, con error intra-observador medido como en Percival et al. 2014.
   La anotación debe hacerla una persona con formación anatómica; aquí no se pueden generar landmarks.
