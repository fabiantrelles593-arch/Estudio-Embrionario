# Resultados — MT-A v3: efecto del atlas sobre la forma, con registro limitado a la cabeza (23 nov 2026)

> Preregistro: `docs/morpho_trace/PREREGISTRO_ATLAS_v3.md` (subido en 96fc788, antes de extraer la muestra y de
> cualquier registro; CI en verde en 77b9230). Código: `scripts/mta_v3.py` y `register_head` y funciones asociadas en
> `src/geovida/atlas_effect.py`, los de 77b9230. Datos: MusMorph/IMPC en FaceBase (CC BY 4.0, Devine et al. 2022,
> doi:10.1038/s41597-022-01338-x). Resultados brutos fuera de git: `results/morpho_trace/v3/` (`muestra_v3.json`,
> `g0a4.json`, `g0m.json`, `s.json`, `piloto/`, `pilot.log`). Solo datos animales; nada humano ni clínico.
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta.

## 1. Veredicto

**MT-A1, MT-A2 y MT-A3: no evaluables.** Falló la puerta **S**: ninguno de los tres candidatos de registro de cabeza
superó a los landmarks del atlas sin mover (identidad) en el piloto [HV, `s.json`]. Según §4 y §8 del preregistro, el
estudio se para aquí: no se hicieron G0-t′, G1′ ni ningún registro confirmatorio o cruzado. Los 36 especímenes
confirmatorios no se han registrado.

Es el cuarto MT-A no evaluable. v2 falló en G1 tras 80 registros (22,9 h); v3 se paró tras 12 registros
(unos 16 min), que es lo que la puerta S estaba para conseguir.

## 2. Puertas

| Puerta | Criterio | Resultado | Estado |
|---|---|---|---|
| G0-a‴ · muestra | Los 40 de P + C cumplen la regla de QC-LM | 40 de 40 | **Superada** [HV] |
| G0-m · caja | Cada caja contiene sus 540 landmarks y cabe en su imagen | Sí en los dos atlas | **Superada** [HV] |
| **S** · selección | Apto: mejora la identidad en ≥ 3 de 4 y mediana de ρ menor que la de la identidad | Ningún apto (tabla de §3) | **Fallida** [HV] |
| G0-t′, G1′, G2 | — | No se ejecutan | — |

## 3. Puerta S: ρ de Procrustes entre landmarks transferidos y publicados (registro propio)

Piloto extraído por semilla: `IMPC_E15.5_0024`, `IMPC_E15.5_1181`, `IMPC_E18.5_0142`, `IMPC_E18.5_1573`. Los 12
registros terminaron con métrica finita.

| Espécimen | Identidad | C1 (afín de cabeza) | C2 (+ B-spline 4³) | C3 (+ B-spline 8³) |
|---|---|---|---|---|
| E15.5_0024 | 0,0617 | **0,0602** | 0,1470 | 0,1244 |
| E15.5_1181 | 0,0350 | **0,0320** | 0,0584 | 0,0841 |
| E18.5_0142 | 0,0336 | 0,0460 | 0,0462 | 0,0459 |
| E18.5_1573 | 0,0270 | 0,0370 | 0,0392 | 0,0455 |
| **Mediana** | **0,0343** | 0,0415 | 0,0523 | 0,0650 |
| Mejora la identidad en | — | 2 de 4 | 0 de 4 | 0 de 4 |

En negrita, los casos en que el registro supera a la identidad.

## 4. Predicciones frente a resultado

| Predicción (§7) | Probabilidad dada | Resultado |
|---|---|---|
| Algún candidato es apto en S | 40 % | **No** |
| El resto (G0-t′, G1′, MT-A1, MT-A2) | — | No se llega a evaluar |

## 5. Lo que muestra el piloto (descriptivo; 4 especímenes, no estima tasas)

* [HV] **La B-spline empeora la forma en los 4 especímenes**, también limitada a la cabeza, mientras mejora la
  información mutua respecto de la afín en los 8 registros con B-spline (p. ej. E15.5_0024: −0,590 → −0,682 con 4³ y
  −0,748 con 8³). En E15.5 la B-spline paró por el límite de 50 iteraciones («User requested»); en E18.5, por
  tolerancia de la función. Es el mismo patrón que en v2: más semejanza de intensidad, peor anatomía.
* [HV] **La afín de cabeza (C1) mejora ligeramente la identidad en los dos E15.5** (0,0617 → 0,0602 y
  0,0350 → 0,0320) y **la empeora en los dos E18.5** (0,0336 → 0,0460 y 0,0270 → 0,0370). Limitar el registro a la
  cabeza y quitar la inicialización por momentos acercó C1 a la identidad (en v2 la afín de cuerpo entero daba
  ρ 0,053 en los dos especímenes de la verificación), pero no basta.
* [HV] La afín paró por el límite de 200 iteraciones en los 4 especímenes. No se cambia nada por ello: el
  preregistro fijó ese límite y no se reajusta después de ver los datos.
* [HV] **Los landmarks publicados son, ellos mismos, salidas de un registro.** Devine et al. 2022 («Image registration
  and label propagation») registraron cada espécimen a su atlas con una afín multirresolución y SyN geodésico
  (correlación cruzada) y llevaron los landmarks del atlas con la transformada invertida. G1 y S miden, por tanto,
  cuánto se acerca este registro a aquel, no a una anotación anatómica independiente.

[HIP] Lectura más probable: con imágenes ya remuestreadas a la rejilla de su atlas, los landmarks del atlas sin
mover ya están a ρ ≈ 0,03 de los publicados, y solo un registro no lineal tan fino como el de MusMorph puede
mejorarlos. Un registro de información mutua con SimpleITK, afín o con B-spline sin regularizar, no lo consigue.

## 6. Qué no se puede concluir

* Nada sobre el efecto del atlas en **d** de ONTO-MAP: sigue sin medirse en las cuatro versiones de MT-A.
* Nada sobre otros registradores (ANTs/SyN) ni sobre una B-spline regularizada.
* Nada en contra de los landmarks publicados de MusMorph.
* El piloto tiene 4 especímenes: decide la puerta, no estima con qué frecuencia mejora C1 la identidad.
* Nada sobre humanos ni uso clínico.

## 7. Siguiente paso (decisión del autor; nada ejecutado)

El preregistro (§8) fija que **no se repite con más variantes sobre los mismos datos** y deja dos caminos, ambos con
un preregistro nuevo:

1. **ANTs/SyN**, el registro con el que se hicieron los landmarks publicados. Antes, comprobar su licencia y su
   versión [PV] e instalarlo. Superar a la identidad sería más plausible, pero G1 pasaría a medir en parte si se
   reproduce el mismo programa.
2. **Pregunta alternativa (§10), ya con la premisa verificada:** como los landmarks publicados son landmarks del atlas
   deformados, el efecto del atlas se puede acotar sin registrar especímenes, comparando la forma de cada atlas con
   la media publicada de su estadio y con el registro atlas–atlas. Es más barata y no depende de la calidad de un
   registro propio.

[PROP] El camino 2 primero: es barato, usa solo datos ya descargados y responde directamente si la separación entre
estadios viene de los atlas.
