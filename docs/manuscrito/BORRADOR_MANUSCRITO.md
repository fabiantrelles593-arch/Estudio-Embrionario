# Borrador de manuscrito (v0.1, 26 nov 2026)

> **Estado: borrador interno. No se envía a ninguna revista.** Antes hacen falta, según §6 de
> `docs/SINTESIS_CERTIFICADO.md`:
>
> 1. la búsqueda en Scopus o Web of Science y un segundo revisor;
> 2. la revisión de un asesor externo;
> 3. la decisión del autor sobre la autoría, la afiliación y la revista.
>
> **Reglas de este texto:** cada cifra sale de un documento de resultados publicado en la rama, citado entre corchetes.
> Si una cifra no coincide con su fuente, manda la fuente. No hay ningún análisis nuevo. Se escribe en castellano para
> revisarlo; la versión para enviar se traducirá.
>
> Autoría y afiliación: **[POR COMPLETAR por el autor]**. No se inventa ninguna afiliación.

---

## Título propuesto

**Una luz de fiabilidad por caso basada en la estabilidad de la propia red, para medir el volumen embrionario en
ecografía 3D de alta frecuencia: evaluación preregistrada con una prueba sellada**

## Resumen

**Objetivo.** Saber si un instrumento puede decir, caso a caso y sin la referencia, cuándo su medida de volumen de un
embrión de ratón en ecografía 3D es fiable (a ≤ 10 % de la referencia manual).

**Métodos.** Usamos un conjunto público de ecografía 3D de alta frecuencia de embriones de ratón con segmentación
manual (Qiu et al. 2021). Todos los estudios se preregistraron antes de calcular la cantidad que decidía. Las pruebas
selladas se abrieron una sola vez, tras anotar la huella SHA-256 de los parámetros congelados. Comparamos tres fuentes
de fiabilidad:

- un certificado calibrado en simulación;
- un certificado basado en observables de la imagen, sobre una red de segmentación de dos etapas;
- una luz basada solo en la estabilidad de esa red ante los 8 volteos de la imagen y en el acuerdo entre sus dos
  etapas, con umbrales fijados desde la tolerancia y sin ajuste a los datos.

**Resultados.**

- Sin guardia de dominio, el certificado calibrado en simulación dio un 100 % de verdes falsas en datos reales
  (540 de 540). Con la guardia, se negó a dar verde.
- El certificado de observables de imagen no superó la puerta de calibración: 2 de 16 verdes fallaron.
- La luz de estabilidad superó la calibración. En la prueba sellada (44 casos, 43 embriones nuevos) falló 1 de 21
  verdes: 4,8 %, IC 95 % 0,0–14,3 %.
- La red midió a ≤ 10 % el 93,2 % de los embriones nuevos (Dice mediano 0,939).
- La luz no mostró que separe aciertos de fallos: diferencia de fallos entre no verdes y verdes de 3,9 puntos, IC −11,4
  a 20,0.
- En ventrículos cerebrales, con la tolerancia en vóxeles de borde, la red quedó a ≤ 0,5 vóxeles en el 95 % de 40 casos
  nuevos. Con 2 fallos, ninguna de las dos hipótesis primarias pudo responderse.

**Conclusión.** La estabilidad de la propia red dio una luz verde segura para el volumen corporal en embriones nuevos
de un conjunto. Que distinga aciertos de fallos sigue sin demostrarse, porque la red casi no falla en estos datos.
Hace falta un segundo conjunto, con más fallos o muchos más casos.

## 1. Introducción

Medir el volumen de un embrión en ecografía 3D exige segmentarlo. Ningún segmentador acierta siempre, y en la práctica
no se dispone de la referencia para saber si un caso concreto está bien medido. Una medida útil debería ir acompañada
de una indicación, por caso, de si es fiable.

Usar el desacuerdo entre predicciones sobre entradas transformadas como medida de incertidumbre de una segmentación
está publicado (Wang et al. 2019a), igual que su uso para señalar segmentaciones erróneas en cascadas de redes
(Wang et al. 2019b). Aquí se pone a prueba en ecografía 3D de alta frecuencia de embriones de ratón con
tres condiciones poco habituales:

1. una regla fija, con umbrales derivados de la tolerancia y no ajustados a los datos;
2. puertas de calibración que deben superarse antes de abrir la prueba;
3. una prueba sellada, abierta una sola vez tras congelar y anotar los parámetros.

Informamos también los resultados negativos que llevaron a esa regla.

## 2. Métodos

### 2.1. Datos

Conjunto público de ecografía 3D de alta frecuencia de embriones de ratón, con segmentación manual del cuerpo y de los
ventrículos cerebrales (Qiu et al. 2021; IEEE DataPort, doi:10.21227/drmd-xq36; licencia CC BY). El archivo público
contiene 180 casos de cuerpo y 216 de ventrículo [`docs/h11/RESULTADOS_H11.md`]. No se generaron datos animales nuevos
ni se usaron datos humanos.

**Reparto.** Se usa el reparto de entrenamiento y prueba de los autores del conjunto, por embrión: ningún embrión está
a los dos lados. Los embriones de entrenamiento se dividieron, con semilla fija, en ajuste de la red (109 casos) y
calibración del certificado (27 casos). La prueba de cuerpo tiene 44 casos de 43 embriones
[`docs/h20/PREREGISTRO_H20.md` §3].

### 2.2. Red de segmentación

Es una reimplementación propia, a partir de la publicación, de la idea de dos etapas de Xu et al. (2020) y Qiu et al.
(2021); no se copió código ni pesos. La etapa 1 es una U-Net 3D pequeña a ¼ de resolución sobre todo el volumen. La
etapa 2 trabaja a ½ de resolución en una caja alrededor de la etapa 1, con su probabilidad como segundo canal. Se
entrenó en CPU con volteos al azar en los tres ejes. La medida es el volumen de la máscara a resolución completa, con
la pieza conectada mayor [`src/geovida/h19.py`].

### 2.3. Señales y regla de la luz

Con V_k el volumen obtenido con el k-ésimo de los 8 volteos (V_0, la imagen tal cual, es la medida) y V_c el de la
etapa 1 sola:

- s_flip = (máx V_k − mín V_k) / V_0;
- s_stage = |V_c − V_0| / V_0.

Con la tolerancia τ = 10 %, la luz es:

- **verde** si el caso está dentro del dominio, s_flip ≤ τ/2 y s_stage ≤ τ;
- **roja** si s_flip > 2τ o s_stage > 3τ;
- **amarilla** en el resto de casos.

Los umbrales se fijaron antes de calcular ninguna señal [`docs/h20/PREREGISTRO_H20.md` §4].

**Guardia de dominio.** Una envolvente de percentiles 1–99 % de dos índices de la imagen (relación señal-ruido estimada
y ancho del borde), ajustada en la calibración.

### 2.4. Protocolo

Cada estudio se preregistró con:

- sus hipótesis;
- sus criterios;
- sus mínimos de evaluabilidad;
- sus predicciones con probabilidad.

El preregistro se subía con el código y las pruebas antes de calcular nada. El orden era fijo: factibilidad (G0),
puerta de calibración, congelado de los parámetros con su huella SHA-256 anotada en el preregistro y, solo entonces,
la prueba. El programa se negaba a abrir la prueba si la huella no coincidía.

**Criterio primario (cuerpo).** Fracción de verdes con |error de volumen| > 10 %. Se considera apoyado si la estimación
es ≤ 10 %, y es evaluable con al menos 20 verdes en al menos 15 embriones.

**Estadística.** IC 95 % por bootstrap de percentiles, remuestreando embriones (2000 réplicas).

## 3. Resultados

### 3.1. Un certificado calibrado en simulación no transfiere a datos reales

El certificado calibrado con datos sintéticos se aplicó a 1188 medidas reales: 180 casos de cuerpo y 216 de ventrículo,
cada uno con 3 segmentadores de umbral. La guardia de dominio no dio ningún verde. Sin la guardia, las 540 verdes
habrían sido falsas [`docs/h11/RESULTADOS_H11.md`]. Recalibrado con ecografía simulada, el resultado fue el mismo
(180 de 180 verdes falsas sin guardia) [`docs/h11/RESULTADOS_H12R.md`].

### 3.2. La red mide bien, pero los observables de imagen no anticipan sus fallos

Con segmentadores de umbral, incluso con limpieza, solo 1 de 136 casos de entrenamiento quedó a ≤ 10 %
[`docs/h18/RESULTADOS_H18.md`]. La red de dos etapas dejó 24 de 27 casos de calibración a ≤ 10 % (Dice mediano 0,938).
Su certificado basado en observables de la imagen no superó la puerta de calibración: 2 de 16 verdes fallaron, más que
dando verde a todos los casos [`docs/h19/RESULTADOS_H19.md`].

### 3.3. La luz de estabilidad, en la prueba sellada

Superó la puerta de calibración con 12 verdes y ningún fallo. En la prueba (44 casos de 43 embriones, abierta una vez)
[`docs/h20/RESULTADOS_H20.md`]:

| Medida | Valor |
|---|---|
| Luces | 21 verdes (47,7 %), 22 amarillas, 1 roja |
| Fallos entre verdes (primaria) | 1 de 21: 4,8 % (IC 0,0–14,3 %); **apoyada** |
| Fallos entre no verdes | 2 de 23: 8,7 % |
| Diferencia (no verdes − verdes) | 3,9 puntos (IC −11,4 a 20,0) |
| Fallo en todos los casos | 3 de 44: 6,8 % |
| Casos a ≤ 10 % / a ≤ 5 % | 93,2 % / 75,0 % |
| Dice mediano | 0,939 |

La verde que falla infraestima el volumen un 12,9 % con las dos señales bajas: la red se equivoca igual en las 8
entradas.

### 3.4. Ventrículos cerebrales

La misma regla, sin cambios, no dio ninguna verde en ventrículos [`docs/h23/RESULTADOS_H23.md`]. Con la tolerancia y las
señales expresadas en vóxeles de borde, el factor limitante pasó a ser la guardia de dominio, que no podía medir una
estructura más oscura que el fondo [`docs/h24/RESULTADOS_H24.md`]. Corregida la guardia, en la prueba de ventrículo
(40 casos de 40 embriones, abierta una vez) [`docs/h25/RESULTADOS_H25.md`]:

- la red quedó a ≤ 0,5 vóxeles de la referencia en el 95 % de los casos (Dice mediano 0,890);
- hubo 19 verdes, de las que falló 1; la primaria no fue evaluable, porque hacían falta 20;
- la separación no fue concluyente: falló 1 de 19 verdes y 1 de 21 no verdes, con una diferencia de −0,5 puntos
  (IC −15,0 a 13,0).

## 4. Discusión

**Qué se sostiene.** En un conjunto público de embriones de ratón, una luz verde dada solo por la estabilidad de la red
acertó en embriones nuevos, en una prueba sellada medida una vez. Los observables de la imagen no lo consiguieron con
la misma red. Un certificado calibrado en simulación, sin guardia de dominio, habría dado verdes falsas en todos los
casos.

**El límite principal.** Con un 6,8 % de fallos en la prueba, casi cualquier regla que dejara suficientes verdes habría
cumplido el criterio primario. El resultado dice sobre todo que la red es exacta en este conjunto. Que la luz separe
aciertos de fallos no está demostrado, ni en cuerpo ni en ventrículo. Una simulación de tamaño muestral muestra que
responderlo exige del orden de 10 a 25 fallos [`docs/h25/TAMANO_MUESTRAL_SEPARACION.md`].

**Lo que no ve la luz.** Un error que la red comete igual en todas las entradas no produce inestabilidad. La única
verde fallida de la prueba es de ese tipo.

**Otras limitaciones.**

- La referencia es un contorno humano: medimos acuerdo, no verdad.
- Todos los datos reales son de un conjunto, un equipo y una especie.
- Los umbrales son juicios fijados de antemano; no se compararon con otros.

**Siguiente paso.** Una replicación directa con volúmenes nuevos y el instrumento congelado. Ya está preregistrada como
base, con un mínimo de fallos para evaluar la separación [`docs/h26/PREREGISTRO_H26_BORRADOR.md`].

**Nada de esto se refiere a humanos ni a uso clínico.**

## 5. Disponibilidad de datos y código

- **Datos:** públicos, en IEEE DataPort (doi:10.21227/drmd-xq36, CC BY). No se redistribuyen.
- **Código, preregistros y resultados:** en el repositorio del proyecto (licencia MIT), rama `geovida/v0.1-desde-cero`.
- **Reproducción:** `docs/REPRODUCCION.md`.

## 6. Declaraciones

- **Ética:** solo se usaron datos animales ya publicados; el estudio no generó datos animales nuevos ni usó datos
  humanos.
- **Uso de IA:** el código y los textos se desarrollaron con asistencia de IA (Claude, Anthropic). El trabajo no ha tenido
  revisión científica humana externa.
- **Financiación y conflictos de interés:** **[POR COMPLETAR por el autor]**.

## Figuras

Se generan con `scripts/figure_manuscript.py` a partir de los casos de prueba ya medidos de H20 y H25, sin análisis
nuevos. El script comprueba antes que los recuentos son los publicados. Las imágenes
(`docs/figures/manuscript_fig1_lights.png` y `docs/figures/manuscript_fig2_signals.png`) se crean al ejecutarlo.

**Figura 1. Error de cada caso de prueba según su luz.**

- **A. Cuerpo, prueba sellada de H20 (44 casos):** |error de volumen| en %; la línea discontinua marca la tolerancia
  del 10 %.
- **B. Ventrículos, prueba de H25 (40 casos):** error de borde e_b en vóxeles; la tolerancia es de 0,5 vóxeles.

Las cruces son fallos. En A falla 1 de las 21 verdes: infraestima un 12,9 % con las dos señales bajas. En B, la verde
que falla queda justo por encima del límite (0,51), y el fallo grosero (2,34) es amarillo.

**Figura 2. Las dos señales de estabilidad en la prueba de cuerpo (H20).** Las líneas discontinuas marcan los umbrales
de la regla: τ/2 y 2τ para s_flip, y τ para s_stage. Los amarillos que caen dentro de la zona verde están fuera del
dominio según la guardia. Las tres cruces son los fallos: ninguna señal los distingue con claridad de los aciertos, que
es lo que H20d no pudo mostrar.

## Referencias

Las referencias 1, 3, 4 y 5 se comprobaron en PubMed el 26 nov 2026 (PMID entre paréntesis).

1. Qiu Z, Xu T, Langerman J, Das W, Wang C, Nair N, Aristizabal O, Mamou J, Turnbull DH, Ketterling JA, Wang Y. A
   deep learning approach for segmentation, classification, and visualization of 3-D high-frequency ultrasound images
   of mouse embryos. IEEE Trans Ultrason Ferroelectr Freq Control. 2021;68(7):2460–2471.
   doi:10.1109/TUFFC.2021.3068156 (PMID 33755564).
2. Ultrasound Mouse Embryo Segmentation and Classification [conjunto de datos]. IEEE DataPort.
   doi:10.21227/drmd-xq36. CC BY.
3. Xu T, Qiu Z, Das W, Wang C, Langerman J, Nair N, Aristizábal O, Mamou J, Turnbull DH, Ketterling JA, Wang Y. Deep
   Mouse: an end-to-end auto-context refinement framework for brain ventricle & body segmentation in embryonic mice
   ultrasound volumes. Proc IEEE Int Symp Biomed Imaging. 2020;2020:122–126. doi:10.1109/isbi45749.2020.9098387
   (PMID 33381278).
4. Wang G, Li W, Aertsen M, Deprest J, Ourselin S, Vercauteren T. Aleatoric uncertainty estimation with test-time
   augmentation for medical image segmentation with convolutional neural networks. Neurocomputing. 2019;335:34–45.
   doi:10.1016/j.neucom.2019.01.103 (PMID 31595105). [Wang et al. 2019a en el texto]
5. Wang G, Li W, Ourselin S, Vercauteren T. Automatic brain tumor segmentation based on cascaded convolutional neural
   networks with uncertainty estimation. Front Comput Neurosci. 2019;13:56. doi:10.3389/fncom.2019.00056
   (PMID 31456678). [Wang et al. 2019b en el texto]
