# Preregistro — H19: ¿acierta la luz verde con un segmentador aprendido de dos etapas, en embriones que nunca vio? (v1.0, 19 nov 2026)

> Siguiente paso fijado por la tabla §7 de `docs/PREREGISTRO_H18.md` para el caso «puerta F no superada»: «hace falta un
> segmentador aprendido […] con su propio preregistro y la misma prueba intacta». Se sube **antes** de entrenar ninguna
> red con datos reales. Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta.
> Solo datos animales publicados (Qiu et al. 2021, CC BY). Nada humano ni clínico.

## 1. Pregunta

En H18, la mejor de las 18 configuraciones de umbral con limpieza dejó **1 de 136** casos de entrenamiento a ≤ 10 % de la
referencia (Dice mediano 0,30), y en las 136 × 18 medidas el volumen salió sobrestimado [HV,
`docs/h18/RESULTADOS_H18.md`]. Los autores del conjunto segmentan el cuerpo con
redes 3D en dos etapas y publican un Dice de 0,934 [EI: Xu et al. 2020, doi:10.1109/isbi45749.2020.9098387; Qiu et al.
2021, doi:10.1109/TUFFC.2021.3068156]. H19 pregunta:

> Con una red de dos etapas y un certificado entrenados y calibrados solo con embriones de entrenamiento, entre las medidas
> de cuerpo de embriones de prueba con luz verde, ¿la fracción con |error de volumen| > 10 % es ≤ 10 %?

## 2. Datos y repartos (fijos)

* **Mismo conjunto, mismas exclusiones y mismo reparto entrenamiento/prueba que H18** (`results/h18/reparto.json`):
  136 casos de entrenamiento (127 embriones) y **44 de prueba (43 embriones), que H18 no abrió**: su puerta F no se
  superó (0 verdes fuera de pliegue) y no existe ningún congelado ni fila de prueba de H18
  (`docs/h18/RESULTADOS_H18.md`) [HV].
* **Dentro del entrenamiento, por embrión y con semilla 20261121** (`geovida.h19.fit_calibration_split`;
  `results/h19/reparto.json`, calculado sin leer imágenes) [HV]: **ajuste 109 casos de 102 embriones** (entrenan las
  redes) y **calibración 27 casos de 25 embriones** (ajustan el certificado; las redes nunca los ven).
* *Por qué no validación cruzada de la red:* en esta CPU (4 núcleos, sin GPU) un paso de entrenamiento cuesta 1,1 s a ¼
  de resolución y 8,7 s a ½ [HV, piloto de tiempo con tensores aleatorios]; entrenar la red 5 veces llevaría días. Se
  entrena una sola vez y el certificado se calibra con casos que la red no vio.

## 3. Método (fijo)

**Segmentador** (`geovida.h19`, reimplementación propia de la idea publicada; no se copia código ni pesos):

* Etapa 1: U-Net 3D (8 canales base, 3 reducciones, InstanceNorm, LeakyReLU) sobre el volumen entero a ¼ de resolución
  (media por bloques 4³), intensidad normalizada por percentiles 1–99.
* Etapa 2: la misma arquitectura con 2 canales (imagen a ½ resolución y probabilidad de la etapa 1) en la caja de la
  etapa 1 (umbral 0,5) más 6 vóxeles por lado.
* Salida: probabilidad de la etapa 2 llevada a resolución completa por interpolación lineal, umbral 0,5, componente
  conectada mayor.
* Entrenamiento: Adam (lr 10⁻³), pérdida entropía cruzada + Dice, un volumen por paso, volteos al azar por eje;
  **150 épocas la etapa 1 y 100 la etapa 2**, semillas 20261121 y 20261122. Sin parada temprana ni elección de época:
  se usa la red de la última época. **No se prueba otra arquitectura ni otros hiperparámetros**; si esto no basta, el
  resultado es ese.

**Certificado:** como H18 (logit con ridge de Pr(|error| ≤ 10 %), luces de H6, guardia de cuantiles 1–99 %), con un
observable más, propio de la red: `uncertain_band`, la fracción del borde de la máscara con probabilidad entre 0,2 y 0,8.
Se ajusta con los 27 casos de calibración.

## 4. Orden de ejecución, puertas y candado

`scripts/run_h19.py`: `split` (hecho) → `train-coarse` → `train-fine` → `calibrate` → *(SHA-256 al §9 y a la rama)* →
`test --sha`.

* **Puerta S (segmentador), en calibración:** ≥ 50 % de los 27 casos a ≤ 10 % de la referencia.
* **Puerta C (certificado), en calibración:** con luces fuera de pliegue (5 pliegues por embrión dentro de la
  calibración), ≥ 10 verdes y como mucho el 10 % de ellas con |error| > 10 %.
* Si falla una puerta, **la prueba no se abre**. Si pasan, `calibrate` congela certificado y huellas SHA-256 de las dos
  redes; `test` se niega a correr si el congelado o las redes no coinciden.

Los mínimos de la puerta C son menores que los de la primaria porque la calibración tiene solo 27 casos: es una condición
necesaria, no una estimación.

## 5. Hipótesis y criterios (fijos; mismos que H18)

**Primaria: H19b.** Entre los casos de prueba con luz verde (con guardia), fracción con |error| > 10 %; IC 95 % por
remuestreo de embriones (2000 réplicas, semilla 20261120, la de H18). *Apoyada* si la estimación es ≤ 10 %; *no apoyada*
si el límite inferior supera 10 %; *no concluyente* en otro caso. **Evaluable** con ≥ 20 verdes en ≥ 15 embriones.

**Secundarias (prueba, descriptivas):** H19a cobertura (fracción verde); H19c acuerdo (Dice y |error| medianos, fracción
a ≤ 10 % y ≤ 5 %), comparado de forma descriptiva con el Dice publicado de 0,934 (otro reparto y otra red: no es una
réplica); H19d guardia (dentro del dominio, verdes sin guardia y cuántas fallan).

Un valor no calculable es «no evaluable», nunca «no apoyada».

## 6. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| Pasa la puerta S | 45 % |
| Pasa la puerta C, dado S | 40 % |
| Dice mediano en calibración ≥ 0,85 | 50 % |
| H19b evaluable, dado que se abre la prueba | 50 % |
| H19b apoyada, dado que es evaluable | 55 % |

*Por qué S puede fallar [HIP]:* ≤ 10 % de volumen es más exigente que un Dice alto (un Dice de 0,93 admite errores de
volumen de ±10 %), la red es mucho más pequeña que la publicada y se entrena con 109 casos.

## 7. Qué significará cada resultado (antes de verlo)

| Resultado | Conclusión | Siguiente paso |
|---|---|---|
| Puerta S no superada | Con esta red y estos datos el volumen del cuerpo no se mide al 10 % | Más capacidad de cómputo o más datos; el certificado no se puede probar aún |
| S sí, C no | La red acierta a veces, pero los observables no anticipan cuándo | Buscar observables de fiabilidad de la red (p. ej. varias pasadas); preregistro nuevo |
| H19b apoyada | En este conjunto, un certificado calibrado con datos reales acertó en embriones nuevos | Replicar con otro conjunto u otro equipo |
| H19b no apoyada | La luz verde falla aun con un segmentador aprendido | Publicarlo; revisar qué distingue los verdes que fallan |
| H19b no evaluable / no concluyente | Pocas verdes o pocos embriones | Más datos, mismo protocolo; la prueba usada no decide dos veces |

## 8. Qué no se puede concluir

* La referencia es un contorno humano; 44 casos de prueba de un conjunto, un equipo y una especie.
* No es una réplica de Qiu et al.: otra red, otro tamaño, otro reparto.
* Nada sobre humanos, obstetricia ni uso clínico.

## 9. Desviaciones

(Ninguna al subir este preregistro.)

* **20 nov 2026 — ejecución sin desviaciones.** `train-coarse`, `train-fine` y `calibrate` corrieron como estaba escrito
  con el código de la rama (`h19.py` a9ce1cc, `run_h19.py` 651a058). Puerta S superada (24 de 27); puerta C no (16 verdes,
  2 fallan: 12,5 % > 10 %). Por §4 no se congeló nada, no se escribe ningún SHA-256 aquí y **la prueba no se abrió**.
  Resultados en `docs/h19/RESULTADOS_H19.md`.
