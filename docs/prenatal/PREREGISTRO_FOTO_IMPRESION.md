# Preregistro — FI-1: ¿cuánto error añade medir sobre una foto de la impresión de una ecografía? (24 nov 2026)

> **Aprobado por el autor el 24 nov 2026, tal como estaba escrito el borrador** (las tres decisiones del §0 propuestas),
> con la cita del umbral del 5 % añadida antes de subir (§4, nota). No se ha abierto, medido ni analizado ninguna imagen
> para este estudio. Aprobar el plan **no** basta para ejecutarlo.
>
> **No se puede ejecutar** hasta que se cumplan **todas** las condiciones de `docs/DATOS_REALES_Y_ETICA.md` §3:
> * el consentimiento firmado de la gestante (plantilla en `docs/clinico/CONSENTIMIENTO_ECOGRAFIA_PLANTILLA.md`);
> * el aval de un comité de ética o la decisión escrita de una institución;
> * la anonimización con `scripts/anonimizar_imagen.py`, revisada a mano;
> * guardar las imágenes solo en `data/private/`.
>
> Estudio **metodológico del software**: no evalúa a ninguna persona ni a ningún embarazo, y no da ningún resultado
> clínico.
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta · [PV] pendiente.

## 0. Decisiones del autor (24 nov 2026: se aceptan las tres propuestas)

| # | Decisión | Propuesta | Alternativa |
|---|---|---|---|
| D1 | ¿Se hace FI-1? | Sí, cuando se cumplan las condiciones éticas. Es la forma más pequeña de probar el software con una imagen humana real sin hacer ninguna afirmación clínica | No usar imágenes humanas hasta tener un grupo clínico aliado (etapa 4 de `PLAN_DE_VALIDACION.md`) |
| D2 | Quién coloca los puntos | Una persona (el autor u otra), que marca los extremos de los calibres «+» **ya impresos** por el ecógrafo. No hace falta formación clínica: no interpreta anatomía, solo localiza marcas impresas. Claude no coloca puntos | Dos personas, para medir también el error entre observadores |
| D3 | Cuántas fotos | 3 fotos nuevas de cada impresión, con el móvil, en condiciones distintas (ángulo, luz). Así se mide el efecto de la foto y no solo el de una imagen concreta | Solo las fotos que ya existen |

## 1. Pregunta y por qué importa

Muchas ecografías solo existen como impresión en papel, y la forma práctica de digitalizarlas es fotografiarlas. Si el
proyecto llegara a medir sobre ese tipo de imagen, antes habría que saber cuánto error añaden la foto, la perspectiva y
la calibración con la escala impresa. La impresión trae su propia referencia: el ecógrafo imprime los calibres «+» y
el valor que midió entre ellos. Medir entre esos mismos «+» sobre la foto y comparar con el valor impreso aísla el error
de digitalización, sin interpretar ninguna anatomía.

**Pregunta FI-1.** Sobre fotos de impresiones de ecografía, calibrando con la escala de profundidad impresa y corrigiendo
la perspectiva, ¿cuánto se aparta la distancia medida entre los calibres impresos del valor que imprimió el ecógrafo?

## 2. Datos

* **Unidad de medida:** cada par de calibres «+» con su valor impreso en mm. Un mismo valor puede aparecer en varias
  impresiones y varias fotos.
* **Material previsto:** las impresiones aportadas por el autor. Su número exacto se registrará al recibir el
  consentimiento, sin ningún dato personal.
* **Antes de medir se registra solo:** el número de impresiones, de pares de calibres y de fotos. No se registra ninguna
  medida.
* **Verdad de referencia:** el valor impreso. Es el que midió el ecógrafo con su propia calibración, así que mide acuerdo
  con el equipo, no error frente a la anatomía.
* **Lo que ya se ha visto (declarado):** el autor envió fotos de impresiones en la conversación del 24 nov 2026. Se
  vieron en pantalla, pero no se guardaron ni se midieron, y ningún valor se ha usado para fijar estos criterios. Los
  umbrales del §4 se fijan por razones previas (§4, nota).

## 3. Protocolo (fijo)

1. **Anonimización** con `scripts/anonimizar_imagen.py` y revisión a mano. Las cajas negras no deben tapar ni los
   calibres ni la escala.
2. **Corrección de perspectiva:** homografía a partir de las 4 esquinas del recuadro negro de la imagen ecográfica,
   marcadas a mano y llevadas a un rectángulo.
3. **Calibración:** sobre la escala de profundidad impresa (marcas de 1 cm), se marcan todas las marcas visibles; mm por
   píxel = 10 / separación media entre marcas consecutivas, en la imagen corregida.
4. **Medida:** la persona de D2 marca el centro de los dos «+» de cada par. Cada foto se mide 3 veces, en sesiones
   distintas, en orden aleatorio (semilla 20261127), sin ver el valor impreso. La persona trabaja sobre una copia con el
   texto del valor tapado.
5. **Estimandos:**
   * error relativo de cada medida, e = (d_foto − d_impreso) / d_impreso;
   * error relativo absoluto mediano |e| sobre todas las medidas (primario);
   * error medio con signo (sesgo);
   * componentes de la variación: entre fotos de la misma impresión y entre repeticiones.
6. **Incertidumbre:** remuestreo por conglomerados (impresión → foto), 2000 réplicas, percentil 95 %.

## 4. Hipótesis y criterios (fijos)

* **FI-1a (primaria) — la foto añade poco error.** *Apoyada* si el límite superior del IC 95 % del |e| mediano es
  ≤ 0,05 (5 %). *Refutada* si el límite inferior es ≥ 0,10. *No concluyente* en otro caso.
* **FI-1b (secundaria) — sin sesgo apreciable.** El IC 95 % del error medio con signo contiene el 0 y está entero en
  [−0,05; 0,05].
* **FI-1c (descriptiva).** Error sin corrección de perspectiva frente a con corrección. Error según la longitud medida.

*Nota sobre los umbrales* (fuentes localizadas en PubMed; ningún dato de este estudio se ha mirado para fijarlos) [EI]:

* El 5 % queda por debajo de los límites de acuerdo al 95 % de repetir una medida de longitud cráneo-caudal (LCC/CRL):
  * transvaginal a las 6–9 semanas: ±8,9 % y ±11,4 % intraobservador y ±14,6 % interobservador (Pexsters et al. 2011,
    *Ultrasound Obstet Gynecol* 38:510–5, doi:10.1002/uog.8884);
  * a las 8–14 semanas: alrededor de ±8,5 % (Souka et al. 2012, *Prenat Diagn* 32:1158–65, doi:10.1002/pd.3976).
* El 5 % es más amplio que el coeficiente de variación intraobservador de la LCC transabdominal a las 9–14 semanas
  (1,4 %; límites de −2,7 % a 2,3 %; Verburg et al. 2008, *Prenat Diagn* 28:323–31, doi:10.1002/pd.1972).

Un error de digitalización ≤ 5 % sería, por tanto, menor que la variación que ya tiene la propia medida al repetirla.
Un 10 % o más sería comparable a ella, o mayor.

## 5. Puertas (en este orden; si una falla, el estudio se para)

| Puerta | Qué se comprueba | Criterio |
|---|---|---|
| **G0-ética** | Consentimiento firmado de la gestante, aval ético y anonimización revisada | Las tres, registradas con un código interno y sin nombres |
| **G0-escala** | Regularidad de las marcas de la escala en la imagen corregida | Coeficiente de variación de la separación entre marcas ≤ 5 % en cada foto |
| **G0-homografía** | Las esquinas del recuadro, corregidas, forman un rectángulo | Desviación máxima de 90° ≤ 2° |

## 6. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| Pasan G0-escala y G0-homografía en todas las fotos | 70 % |
| FI-1a apoyada | 50 % |
| FI-1a refutada | 15 % |
| Sin corrección de perspectiva, el error mediano es al menos el doble | 60 % |

## 7. Qué significará cada resultado (antes de verlo)

| Resultado | Conclusión | Siguiente paso |
|---|---|---|
| Apoyada | Con esta cadena, una foto de impresión permite medir con un error ≤ 5 % frente al ecógrafo | Documentar la cadena como herramienta de digitalización. Sigue sin haber ninguna validación clínica |
| Refutada | Las fotos de impresiones no sirven para medir con este método | No usar fotos de impresiones; pedir los archivos originales del ecógrafo (DICOM), con las mismas condiciones éticas |
| No concluyente | El error no queda acotado con estas fotos | Más fotos o un segundo observador, con preregistro nuevo |

## 8. Qué no se puede concluir

* Nada sobre la persona ni sobre el embarazo: ni diagnóstico, ni normalidad, ni edad gestacional, ni ninguna valoración
  de lo que se ve en la imagen.
* Nada sobre la exactitud del ecógrafo: el valor impreso se toma como referencia, no se valida.
* Un único equipo y un único centro: no se puede generalizar a otros ecógrafos o impresoras.

## 9. Ejecución (solo tras aprobar el preregistro y superar G0-ética)

1. Código antes de medir: corrección de perspectiva, calibración y estimandos en un módulo nuevo, con pruebas sobre
   impresiones **sintéticas** (líneas de longitud conocida, perspectiva y escala simuladas).
2. Subir el preregistro aprobado, el código y las pruebas con CI verde.
3. Anonimizar y revisar las imágenes; medir; analizar.
4. Resultados en `docs/prenatal/RESULTADOS_FOTO_IMPRESION.md`, solo con números agregados y sin ninguna imagen.

## 10. Desviaciones

(Ninguna al subir este preregistro.)

### Estado al subir

* **G0-ética no superada.** No hay consentimiento firmado de la gestante ni aval ético.
* Las fotos que se enviaron en la conversación no se guardaron en el proyecto y no se usarán hasta que exista G0-ética.
* El código de medida (§9.1) se escribirá y subirá antes de medir. De momento solo está en la rama la herramienta de
  anonimización (`src/geovida/deidentify.py`, `scripts/anonimizar_imagen.py`, `tests/test_deidentify.py`).
