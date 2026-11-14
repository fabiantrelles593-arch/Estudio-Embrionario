# Preregistro — H12R: ¿transfiere a ecografía real de ratón el certificado recalibrado con ecografía simulada? (v0.5)

> Se escribe **después** de calibrar H12 (el modelo congelado ya está en git, commit 35f84aa) y
> **antes** de abrir ningún volumen real. Completa `PREREGISTRO_H11.md`: allí se fija el protocolo con
> datos reales; aquí se fija cómo se lee el resultado cuando se usan los modelos de H12.
> Solo investigación y educación. Nada de esto dice algo sobre uso clínico.

## 1. Pregunta

H11 aplica a ecografía real de ratón el certificado de v0.4 (calibrado con ruido gaussiano). Lo que se
espera es que su guardia rechace casi todo. H12 construyó un simulador de ecografía (moteado,
atenuación) y recalibró. H12R pregunta lo que de verdad importa para el siguiente paso:

> Con los modelos de H12, ¿la imagen real cae dentro del dominio que el simulador de ecografía
> cubre, y cuando el certificado dice «verde», acierta?

## 2. Qué se sabe antes de abrir datos (la calibración de H12, ya congelada)

* Solo `smoothed_otsu` obtiene luces verdes y envolvente en la calibración. Para `global` y `otsu` el
  moteado deja un sesgo de volumen que no depende de la resolución (−13 % a −35 %), así que nunca hay
  verde: son estratos «no evaluables» por construcción, no fallos del modelo.
* La envolvente de `smoothed_otsu` es estrecha (índice de ruido `snr_hat` ≈ 6.7–10.2 y ancho de borde
  `edge_width` ≈ 1.1–1.5 vóxeles). Una ecografía real con otro nivel de ruido o de nitidez quedará
  fuera y recibirá, como máximo, luz amarilla.
* Los modelos se ajustaron con simulación de ecografía de un solo tipo de moteado; no hay razón para
  pensar que el moteado de un equipo real de alta frecuencia se parezca.

## 3. Protocolo (fijo)

* Mismos datos, mismo manifiesto, mismos segmentadores y mismas estructuras que `PREREGISTRO_H11.md`.
* Se corre `python scripts/run_h11.py MANIFIESTO.csv --root CARPETA --frozen results/summary/h12_frozen.json --profile us_raw --tag h12`.
* **Perfil primario: `us_raw`** (el de menos promediado de los dos perfiles simulados: 3 «miradas» de
  moteado frente a 8 de `us_compound`). Se declara aquí, antes de ver imágenes. Se corre también `--profile us_compound --tag h12c` y se publica, pero **no** se puede
  elegir después el perfil que salga mejor.
* No se reajusta ningún modelo ni envolvente con los datos reales.

## 4. Hipótesis y criterios (fijos)

**Primaria: H12Rb.**

* **H12Ra — La guardia de H12 reconoce la imagen real (descriptiva con criterio).** Fracción de
  volúmenes de cuerpo «dentro del dominio», por segmentador, con los modelos de H12 y, aparte, con los
  de v0.4 (los de H11). *Apoyada* si en `smoothed_otsu` es mayor con H12 que con v0.4. No se espera
  que sea alta; solo se pregunta si la recalibración la acerca.
* **H12Rb — La luz verde de H12 no falla demasiado (primaria).** Entre las medidas de cuerpo con luz
  verde de volumen (ya con guardia), con `us_raw`, la fracción con |error| > 10 % respecto de la
  referencia es ≤ 10 %, agrupando segmentadores. Mismas reglas de «no evaluable» (< 30 verdes o < 15
  embriones con verde), de «no apoyada» (límite inferior del IC 95 % por embrión > 10 %) y de «no
  concluyente» que H11b.
* **H12Rc — Cobertura frente a v0.4.** Número de luces verdes de cuerpo con H12 menos con v0.4. Sin
  criterio de éxito: sirve para saber si la recalibración deja de ser «segura pero vacía».
* **H12Rd — Acuerdo (descriptiva).** Dice y error relativo de volumen por segmentador y estructura,
  igual que H11d.

Un valor no calculable es «no evaluable», nunca «no apoyada».

## 5. Lo que se hace según el resultado (decidido de antemano)

| Resultado | Qué se concluye | Siguiente paso |
|---|---|---|
| H12Rb **no evaluable** (la guardia rechaza casi todo) | El simulador de ecografía de H12 no cubre aún la ecografía real de alta frecuencia. La guardia hizo su trabajo: se negó. | Calibrar con los propios volúmenes reales, validando **por embrión** (nunca dos cortes del mismo embrión a ambos lados de la división). Eso es otra hipótesis, con su preregistro. |
| H12Rb **apoyada** | Con este conjunto y este protocolo, las luces verdes de `smoothed_otsu` acertaron. No se generaliza a otro equipo, especie ni estructura. | Replicar con un segundo conjunto antes de afirmar nada más. |
| H12Rb **no apoyada** | La luz verde falló con datos reales. Se publica tal cual. | Revisar qué rasgo de la ecografía real no estaba en el simulador. |
| H12Rb **no concluyente** | Faltan embriones para decidir. | Más embriones, mismo protocolo. |

## 6. Predicciones escritas de antemano (después de H12 y antes de abrir datos)

| Predicción | Probabilidad |
|---|---|
| H12Rb **no evaluable** con `us_raw` | 70 % |
| Con H12, `smoothed_otsu` deja dentro del dominio más volúmenes de cuerpo que con v0.4 (H12Ra apoyada) | 60 % |
| Dado que H12Rb es evaluable, queda **apoyada** | 40 % |
| Dice mediano del cuerpo con `smoothed_otsu` ≥ 0.90 | 50 % |

## 7. Qué no se puede concluir

* Una referencia dibujada por una persona no es la verdad: se mide acuerdo, no error exacto.
* Un ratón no es una persona; una ecografía de alta frecuencia no es una ecografía obstétrica.
* Un conjunto, un equipo, una especie. Pocos embriones dan intervalos anchos.
* Una luz verde sigue sin ser una validación clínica.

## 8. Desviaciones

(Ninguna al momento del primer commit.)

* 2026-11-11 (antes de abrir datos): la primera versión describía `us_raw` como «adquisición única, sin
  promediar ángulos». Es inexacto: en el simulador `us_raw` promedia 3 «miradas» de moteado y
  `us_compound` promedia 8. Se corrigió la descripción; la elección de `us_raw` como perfil primario y
  todos los criterios no cambian.
