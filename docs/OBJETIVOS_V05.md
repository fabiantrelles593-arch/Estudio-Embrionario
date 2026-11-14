# v0.5 — Propósito, objetivos y ruta: de fantomas a embriones reales

## 1. Por qué este giro

Las versiones 0.1 a 0.4 construyeron y probaron un instrumento con objetos de respuesta exacta
(fantomas). Era el orden correcto para saber cuánto se equivoca una medida, porque en un embrión
real nadie conoce el volumen verdadero. Pero ese trabajo, por sí solo, es la base y no la meta:
todo sigue siendo sintético, y los programas que hoy se usan en clínica (por ejemplo, la
biometría fetal automática de los ecógrafos) sí se han usado con imágenes reales.

Qué sí puede aportar este proyecto frente a eso, y qué no:

* **No** es un segmentador mejor. Para afirmarlo habría que compararlo cabeza a cabeza con esas
  herramientas sobre las mismas imágenes, y eso no se ha hecho.
* **Sí** puede aportar lo que hasta donde alcanza nuestra búsqueda (`docs/ANTECEDENTES_V04.md`) no
  suele acompañar a una medida: una **probabilidad calibrada de que esa medida concreta sea fiable**
  (volumen y topología), y una **negativa explícita** cuando la imagen no se parece a aquellas con
  las que se calibró. En malformaciones congénitas lo que importa muchas veces es la forma y la
  topología (un cierre, un hueco, una conexión), no solo un diámetro.
* Eso solo se puede sostener con imágenes reales y referencias reales. De ahí v0.5.

## 2. Propósito

Que una persona que mide un embrión o un feto en una imagen sepa, **para cada medida**, cuánto
puede fiarse de ella y cuándo el programa se niega a opinar. Ese es el propósito de largo plazo.
Lo que existe hoy es un instrumento de investigación; el uso clínico exige las etapas de la
sección 4, y ninguna se da por hecha.

## 3. Objetivos medibles

| Objetivo | Cómo se sabrá que se cumplió |
|---|---|
| O1. Probar el certificado congelado en imágenes reales de embriones animales | H11: informe con criterios fijados antes de abrir los datos (`PREREGISTRO_H11.md`), con sus fallos |
| O2. Si la guardia rechaza la ecografía real, construir y probar un simulador de ecografía 3D (moteado, atenuación, desenfoque) | H12, preregistro propio, evaluado sobre las mismas imágenes reales sin reajustar |
| O3. Calibrar un certificado con datos reales, validado dejando un embrión fuera | H13, preregistro propio; solo con suficientes embriones |
| O4. Comparar con una herramienta existente en las mismas imágenes | Informe; sin comparación, no se dice «mejor» |
| O5. Preparar el camino ético y regulatorio antes de cualquier imagen humana | Documento de condiciones cumplidas (consentimiento, anonimización, comité de ética, plan preregistrado) |

## 4. Ruta por etapas, con puertas de decisión

| Etapa | Qué se hace | Puerta para pasar a la siguiente | Qué NO se afirma al terminarla |
|---|---|---|---|
| 0. Sintético (hecho, v0.1–v0.4) | Fantomas, simulador, certificado congelado, 10 hipótesis | — | Nada sobre imágenes reales |
| 1. Ecografía 3D real de embrión de ratón, con contornos de expertos (**en curso**) | H11: transferencia sin reajustar, con la guardia | Informe publicado; si no hay datos suficientes, se dice | Nada sobre humanos ni sobre uso clínico |
| 2. Simulador de ecografía y recalibración | H12 y H13 | Mejora medida frente a H11 sobre imágenes no usadas para ajustar | Que «funciona en ecografía»: solo en este conjunto de ratón |
| 3. Otras especies y modalidades (pez cebra, rata, micro-CT con verdad de mayor resolución) | Réplica con datos de laboratorios aliados o públicos con licencia | Al menos un conjunto independiente del de la etapa 1 | Generalidad entre especies |
| 4. Ecografía humana retrospectiva | **Solo** con las condiciones de `DATOS_REALES_Y_ETICA.md` §3: consentimiento, anonimización completa, comité de ética, almacenamiento fuera del repositorio, plan preregistrado | Todas las condiciones por escrito, y un asesor clínico | Cualquier afirmación sobre la salud de una persona o un feto |
| 5. Estudio prospectivo y regulatorio | Diseño con un grupo clínico; el software con finalidad médica es un dispositivo médico regulado (en Perú, DS 003-2020-SA) | Aprobación del comité y de la autoridad competente | — |

Aclaración que repetiremos siempre: **«probar con una ecografía» significa probar el software sobre
una imagen, no hacer un experimento con personas.** Hasta cumplir la etapa 4 no se procesa ninguna
imagen humana. Reducir enfermedades congénitas es el horizonte; con estas etapas se puede apuntar a
él sin afirmar nada que todavía no se haya medido.

## 5. Datos reales identificados (información de las páginas de cada conjunto, 2026-11-10)

No se ha descargado ni abierto ninguno desde este entorno: la red del entorno de trabajo solo
llega a los registros de paquetes y a GitHub. Las licencias son las que indica cada página; no se
han comprobado en otra fuente.

| Conjunto | Contenido | Referencia | Licencia indicada | Papel en v0.5 |
|---|---|---|---|---|
| **Ecografía 3D de alta frecuencia de embriones de ratón** (Qiu et al.; IEEE DataPort, DOI 10.21227/drmd-xq36) | Volúmenes `.nii` en un archivo de 1.94 GB; incluye embriones mutantes | Contornos manuales (segmentación y clasificación; el proyecto del grupo habla de ventrículo cerebral y cuerpo) | Creative Commons Attribution; la descarga requiere cuenta gratuita de IEEE DataPort | **Principal (etapa 1)** |
| Atlas de micro-CT de embrión E15.5 de ratón (Wong et al. 2012; mouseimaging.ca) | 35 embriones, 48 estructuras segmentadas a mano | Etiquetas manuales | **No indicada en la página**; hay que revisar sus términos de uso | Anatomía real de alta resolución para fantomas de forma real (etapa 3) |
| HREM de embrión de ratón (Francis Crick Institute; Zenodo 10.5281/zenodo.8222707) | Un volumen TIFF de 219 MB | Ninguna | CC BY 4.0 | Solo para probar el lector |
| BlastoSPIM (Flatiron Institute / Princeton; figshare+) | 573 + 80 volúmenes de embriones de ratón preimplantacionales, con segmentación de núcleos | Segmentación 3D de núcleos | **No visible en la página** | Posible, otra escala y otra modalidad |
| Pez cebra, microscopía de hoja de luz (varios registros de Zenodo) | Núcleos y membranas | Algunas máscaras 3D | Sin verificar | Etapa 3 |
| **Rata** | No encontré un conjunto público de ecografía o micro-CT de embrión de rata con referencia | — | — | Requiere un laboratorio aliado o imágenes propias |

## 6. Qué se necesita de afuera

* Descargar el conjunto de ecografía de ratón (cuenta gratuita en IEEE DataPort) y entregarlo, o una
  muestra, o ejecutar `geovida datasheet` y devolver la ficha (paso a paso en `GUIA_DATOS_REALES.md`).
* Un asesor (docente, laboratorio o clínico) que revise el método antes de cualquier uso externo.
* Para las etapas 4 y 5: un comité de ética, un grupo clínico y asesoría regulatoria. Eso no se
  improvisa desde un repositorio.
