# Preregistro — H11: ¿transfiere el certificado a ecografía 3D real de embrión de ratón? (v0.5)

> Se confirma (`git commit` + `git push`) **antes** de abrir ningún dato real. El primer contacto con
> los datos es la **ficha** (`scripts/real_datasheet.py`: formas, vóxel, etiquetas, intensidades;
> no calcula ningún acuerdo con una referencia). Lo que la ficha obligue a precisar (qué archivo es
> imagen, qué etiqueta es cuerpo o ventrículo cerebral) se anota en «Desviaciones» **antes** de
> calcular ninguna medida contra la referencia.

## 1. Pregunta y por qué importa

Hasta v0.4 todo se calibró y se confirmó con imágenes sintéticas. Una luz verde decía «esta medida
se parece a las que, en el simulador, acertaban». No decía nada sobre una imagen real. H11 es la
primera prueba donde puede fallar de verdad: se aplica el certificado **congelado** (modelos y
envolventes de `src/geovida/frozen/h9_frozen.json` y de H6, sin reajustar nada) a ecografías 3D de
alta frecuencia de embriones de ratón con contornos dibujados por expertos.

Lo esperable, y lo que sería un resultado honesto y útil, es que la guardia de dominio **rechace**
gran parte de estas imágenes: el moteado de la ecografía no se parece al ruido gaussiano del
simulador. Un certificado que se niega cuando no se parece a su calibración está funcionando.

## 2. Datos

* **Conjunto previsto:** «Ultrasound Mouse Embryo Segmentation and Classification» (Qiu et al.,
  IEEE DataPort, DOI 10.21227/drmd-xq36): ecografía 3D de alta frecuencia de embriones de ratón,
  volúmenes `.nii`, contornos manuales para segmentación y clasificación (incluye embriones
  mutantes), archivo de 1.94 GB. Licencia declarada en la página: Creative Commons Attribution; la
  descarga exige una cuenta gratuita de IEEE DataPort. **No verificado por este proyecto más allá de
  esa página**; no se ha abierto ningún archivo.
* Es un conjunto **animal**. No contiene datos de personas. Las reglas de
  `docs/DATOS_REALES_Y_ETICA.md` para imágenes humanas siguen vigentes y no se aplican a este paso.
* Si la estructura del archivo no permite emparejar imagen y contorno sin ambigüedad, se dice en
  «Desviaciones» y no se emparejan casos dudosos.

## 3. Protocolo (fijo)

* **Unidad:** un par (volumen, estructura). Estructuras: **cuerpo del embrión** (primaria) y
  **ventrículo cerebral** (exploratoria; ver límite abajo), según las etiquetas reales.
* **Segmentadores:** `global`, `otsu`, `smoothed_otsu` tal como están en `geovida.segment`, sin
  cambios. Perfil declarado: `realistic` en los tres (la imagen real tiene ruido).
* **Medida:** `geovida.realdata.compare_case` → certificado de v0.4 (luz de volumen y de topología,
  con y sin guardia), volumen medido, volumen de la referencia, error relativo, Dice, Betti medido y
  de referencia (adyacencia 26/6).
* **Escala:** vóxel en milímetros tomado de la cabecera NIfTI. Si la cabecera no declara unidad, se
  asume milímetros y se anota. Sin remuestrear ni recortar.
* **Estructura pequeña:** el ventrículo cerebral no se puede segmentar con un umbral de toda la
  imagen. Para esa estructura el umbral se calcula **dentro de una caja alrededor de la referencia**
  (dilatada 25 % por lado). Esto usa la referencia para elegir dónde medir y **favorece al método**;
  se declara así y esa estructura nunca es primaria.
* **Tolerancia del error de volumen:** el certificado se calibró para |error| ≤ 5 %. La referencia
  humana tiene su propio error y no puede certificar 5 %. Por eso el criterio primario usa **10 %**
  y se informa también el de 5 %.
* **Incertidumbre:** los casos de un mismo embrión no son independientes. Los intervalos se calculan
  por remuestreo de **embriones** (percentil, 2 000 réplicas, semilla 20261126); si el conjunto no
  identifica al embrión, cada volumen cuenta como un embrión y se dice.
* **Sin reajuste:** ningún modelo, envolvente, umbral de luz ni segmentador se cambia después de
  ver los resultados. Cualquier idea de mejora va a una versión nueva con su propio preregistro.

## 4. Hipótesis y criterios (fijos)

**Primaria: H11b.** Las demás son secundarias o descriptivas.

* **H11a — La guardia rechaza lo que no se parece (descriptiva con criterio).** Para cada
  segmentador, fracción de volúmenes de **cuerpo** que la guardia deja «dentro del dominio» en la
  medida de volumen. *Apoyada* si es ≤ 50 % en los tres segmentadores. *Parcial*: en dos.
* **H11b — La luz verde no falla demasiado (primaria).** Entre las medidas de **cuerpo** con luz
  **verde** de volumen (ya con la guardia), la fracción con |error| > 10 % respecto de la
  referencia es ≤ 10 %, agrupando los tres segmentadores. *No evaluable* si hay menos de 30 luces
  verdes (o menos de 15 embriones distintos con verde). *No apoyada* si el límite inferior del
  intervalo del 95 % supera 10 %.
* **H11c — Sin guardia, el semáforo de volumen de v0.3 falla.** Entre las medidas de cuerpo con
  verde **antes** de aplicar la guardia, la fracción con |error| > 10 % supera 10 %. Apoyada si el
  punto estimado lo supera. *No evaluable* si hay menos de 30 verdes.
* **H11d — Acuerdo con la referencia (descriptiva).** Mediana y rango del Dice y del error relativo
  de volumen por segmentador y estructura. Sin criterio.
* **H11e — Topología del cuerpo.** Entre las medidas de cuerpo con luz **verde** de topología, la
  fracción cuyo triple de Betti difiere del de la referencia es ≤ 10 %. *No evaluable* si hay menos
  de 30 verdes. Se informa también la fracción de referencias con Betti distinto de (1, 0, 0), porque
  un contorno manual puede tener huecos que el embrión real no tiene.

Un valor no calculable es «no evaluable», nunca «no apoyada».

## 5. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| H11a apoyada (la guardia rechaza ≥ la mitad en los tres segmentadores) | 70 % |
| H11b evaluable (≥ 30 verdes y ≥ 15 embriones con verde) | 35 % |
| H11b apoyada, dado que es evaluable | 55 % |
| H11c apoyada, dado que es evaluable | 60 % |
| El Dice mediano del cuerpo con el mejor segmentador ≥ 0.90 | 55 % |

## 6. Qué no se puede concluir

* Una referencia dibujada por una persona no es la verdad: este paso mide acuerdo, no error exacto.
* Un ratón no es una persona, y una ecografía de alta frecuencia en el útero de una ratona no es una
  ecografía obstétrica humana. Nada de H11 dice algo sobre uso clínico.
* Pocos embriones dan intervalos anchos. Un «no evaluable» es un resultado válido.
* El ventrículo cerebral con caja alrededor de la referencia es optimista.
* Una luz verde seguirá sin ser una validación: es una estimación calibrada con un simulador.
* Si la guardia rechaza casi todo, lo que se aprende es que hace falta un simulador de ecografía
  (moteado, atenuación) y una calibración con datos reales validada por embrión: la ruta de H12.

## 7. Desviaciones

(Ninguna al momento del primer commit.)

### Aclaraciones del 2026-11-11 (escritas al implementar `src/geovida/h11.py`, antes de abrir ningún dato real)

No cambian ningún criterio; fijan lo que el texto dejaba abierto. Se prueban con tablas fabricadas
(`tests/test_h11.py`), no con imágenes reales.

1. **H11b «no concluyente».** El texto define *apoyada* (estimación puntual ≤ 10 %) y *no apoyada*
   (límite inferior del IC 95 % > 10 %). Si la estimación puntual supera 10 % pero el límite inferior
   del intervalo no llega a 10 %, el resultado es **«no concluyente»**: ni se apoya ni se refuta. No se
   interpreta como fallo ni como éxito.
2. **Intervalo.** Percentil 95 % por remuestreo de **embriones** (no de filas): 2000 réplicas,
   semilla 20261126 (`h11.N_BOOT`, `h11.BOOT_SEED`). Varias filas de un mismo embrión (tres
   segmentadores, dos estructuras) no se tratan como independientes.
3. **Evaluable.** Mínimo 30 luces verdes y 15 embriones con al menos una verde (H11b, H11c, H11e).
   Por debajo, el veredicto es «no evaluable», nunca «no apoyada».
4. **H11a.** Se mide por segmentador sobre las filas de cuerpo; «dentro del dominio» es el índice
   `in_domain_volume` del certificado. *Apoyada*: ≤ 50 % en los tres; *parcial*: en dos; si no, *no
   apoyada*.
5. **Emparejamiento.** Un manifiesto CSV (`embryo_id, structure, image, label, label_value`) lo arma
   una persona tras leer la ficha de `geovida datasheet`. Si imagen y etiqueta no tienen la misma forma
   ni el mismo tamaño de vóxel, o el valor de etiqueta no aparece, el caso se rechaza con error: no se
   adivina ni se omite en silencio.
6. **Dos calibraciones, un mismo protocolo.** Se corre con los modelos de v0.4 (`--tag v04`) y,
   aparte, con los de la ecografía simulada de H12 (`--frozen h12_frozen.json --tag h12`). Los dos
   resultados se publican. Los veredictos de la segunda se interpretan según `PREREGISTRO_H12R.md`
   (por escribir, también antes de abrir datos).
