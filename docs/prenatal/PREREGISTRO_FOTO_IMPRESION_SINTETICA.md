# Preregistro FI-1s: ¿cuánto error añade medir sobre una foto de una impresión? (con impresiones sintéticas)

**Versión 1.0, 25 nov 2026. Aprobada por el autor tal como estaba escrita el 25 nov 2026.**

Código: `src/geovida/fi1s.py`, `scripts/fi1s_hojas.py`, `scripts/fi1s.py` y `tools/marcador.html`. Pruebas:
`tests/test_fi1s.py`.

> **Por qué existe.** FI-1 (`docs/prenatal/PREREGISTRO_FOTO_IMPRESION.md`) está aprobado y bloqueado por G0-ética. Le
> faltan el consentimiento firmado por la gestante y el aval de un comité de ética, y una autorización familiar no los
> sustituye. FI-1s mide **la misma cadena** (foto → corrección de perspectiva → calibración con la escala → distancia
> entre calibres) sobre impresiones **generadas por el proyecto**, con distancias conocidas exactas.
>
> **Qué no toca.** Ningún dato de ninguna persona. **FI-1 sigue igual:** aprobado, bloqueado y sin cambios.
>
> **Etiquetas:** [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta.

## 1. Pregunta

Sobre fotos de móvil de hojas impresas que imitan una impresión de ecografía, calibrando con la escala impresa y
corrigiendo la perspectiva, **¿cuánto se aparta la distancia medida entre los calibres «+» de la distancia diseñada?**

FI-1s responde la parte técnica de FI-1 (foto, perspectiva, escala y marcado a mano) sin necesitar imágenes humanas. Si
la cadena ya falla aquí, no tiene sentido pedir datos clínicos para FI-1. Si funciona, FI-1 queda reducido a la
diferencia entre el papel real y el sintético.

## 2. Material (generado por código, fijo)

`scripts/fi1s_hojas.py`, con la semilla **20261125**, genera **6 hojas** A4 en PDF a escala 1:1. Cada hoja tiene:

- un recuadro negro con un fondo de moteado (*speckle*) sintético, parecido a una imagen de ecografía. No contiene
  ninguna anatomía;
- una escala vertical de profundidad con marcas cada 1 cm (8 marcas);
- **4 pares de calibres «+»**, con longitudes diseñadas al azar entre 10 y 60 mm y orientaciones al azar, sin cruzarse;
- un código de hoja (S01–S06). **Ningún valor de distancia aparece en la hoja.**

Las distancias diseñadas se guardan en `data/fi1s/valores_disenados.json`, en mm de la escala impresa. La persona que
marca no abre ese archivo hasta terminar las 3 sesiones.

**Referencia.** La distancia diseñada, medida en las mismas unidades que la escala impresa. Si la impresora escala la
hoja de forma uniforme, la escala y los calibres cambian igual y el error relativo no varía. Una impresora que deforme
más en un eje que en otro es una fuente de error real, y queda dentro de lo que se mide.

## 3. Protocolo (lo hace una persona; Claude no coloca puntos)

1. **Imprimir** las 6 hojas al 100 %, sin «ajustar a página», en papel normal.
2. **Medir con una regla**, sobre el papel, el ancho y el alto del recuadro de cada hoja, una vez (como D-1 de FI-1).
3. **Fotografiar** cada hoja 3 veces con el móvil, con la hoja plana sobre una mesa:
   - F1: de frente;
   - F2: inclinada unos 20–30° hacia un lado;
   - F3: inclinada hacia el otro lado y con otra luz.

   Son 18 fotos.
4. **Marcar** en la herramienta local de marcado (§7): las 4 esquinas del recuadro, los 4 puntos medios de los bordes,
   todas las marcas visibles de la escala y el centro de cada «+».
   - Cada foto se marca 3 veces, en 3 sesiones separadas por al menos 24 h.
   - En cada sesión, las fotos van en orden aleatorio (semilla 20261125).
5. **Medir y analizar** con `geovida.print_measure`, el código de FI-1 sin cambios: `rectify` con la razón medida,
   `scale_mm_per_unit`, `measure_photo`, `gate_photo` y `analyze`.

*Esfuerzo previsto:* unos 24 clics por foto × 54 marcados, es decir, entre 2 y 3 h repartidas en las 3 sesiones.

## 4. Hipótesis y criterios (los de FI-1, sin cambios)

Error relativo de cada medida: e = (d_foto − d_diseñada) / d_diseñada. Remuestreo por conglomerados (hoja → foto), con
2000 réplicas y semilla 20261125.

| Hipótesis | Apoyada | Refutada | En otro caso |
|---|---|---|---|
| **FI-1sa (primaria):** la foto añade poco error | límite superior del IC 95 % del \|e\| mediano ≤ 0,05 | límite inferior ≥ 0,10 | no concluyente |
| **FI-1sb (secundaria):** sin sesgo apreciable | el IC 95 % del error medio con signo contiene 0 y está entero en [−0,05; 0,05] | — | no apoyada |

**FI-1sc (descriptiva):**
- error sin corrección de perspectiva frente a con corrección;
- error según la longitud;
- error según el tipo de foto (F1, F2, F3);
- variación entre repeticiones del marcado.

Los umbrales y su justificación son los de FI-1 §4: Pexsters 2011, doi:10.1002/uog.8884; Souka 2012,
doi:10.1002/pd.3976; Verburg 2008, doi:10.1002/pd.1972.

## 5. Puertas (en este orden)

| Puerta | Criterio |
|---|---|
| **G0-impresión** | Antes de fotografiar, el ancho y el alto del recuadro medidos con la regla se apartan ≤ 2 % de los del PDF. Si no, la impresora escaló la hoja: se repite la impresión |
| **G0-escala** | CV de la separación entre marcas ≤ 5 % en cada foto (FI-1) |
| **G0-homografía** | Desviación de 180° de esquina–punto medio–esquina ≤ 2° en los 4 bordes de cada foto (FI-1, D-2) |

Si una foto falla G0-escala o G0-homografía, se informa y **no se repite**. El análisis principal usa todas las fotos
que pasan, y se informa cuántas fallaron.

## 6. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| Todas las fotos pasan G0-escala y G0-homografía | 75 % |
| FI-1sa apoyada | 65 % |
| FI-1sa refutada | 5 % |
| Sin corrección de perspectiva, el error mediano es al menos el doble | 70 % |
| F2 y F3 (inclinadas) tienen más error que F1 | 60 % |

## 7. Lo que se escribirá después de aprobar (antes de imprimir)

1. `scripts/fi1s_hojas.py`: genera las 6 hojas y el archivo de valores, con pruebas que comprueban que las distancias
   del PDF son las diseñadas.
2. `tools/marcador.html`: herramienta local de marcado.
   - Abre una foto desde tu equipo; nada se sube a ningún sitio.
   - Pide los puntos en orden fijo y guarda el JSON en el formato de `measure_photo`.
   - No muestra ninguna distancia mientras se marca.
3. `scripts/fi1s.py`: órdenes `plan`, `gates` y `analyze`, reutilizando `print_measure` sin cambios.
4. Todo se sube con sus pruebas y la integración continua en verde **antes de imprimir nada**.

## 8. Qué significará cada resultado (antes de verlo)

| Resultado | Conclusión | Siguiente paso |
|---|---|---|
| FI-1sa apoyada | La cadena foto → medida tiene un error ≤ 5 % en papel normal y con un móvil | FI-1 solo tiene que comprobar la diferencia con el papel real de ecografía. Sigue bloqueado por G0-ética |
| FI-1sa refutada | La cadena no sirve ni en condiciones controladas | No pedir datos clínicos para FI-1 con este método; revisar la cadena (por ejemplo, el escáner en lugar del móvil) con un preregistro nuevo |
| No concluyente | El error no queda acotado con 18 fotos | Más fotos o un segundo observador, con un preregistro nuevo |

## 9. Qué no se puede concluir

- Nada sobre ecografías reales: el papel térmico, el brillo, las curvaturas y la impresión del ecógrafo no se imitan.
- Nada clínico ni sobre ninguna persona.
- Un solo móvil, una sola impresora y una sola persona que marca: el error entre observadores no se mide.
- Las hojas son de diseño propio. Un acierto aquí es una condición necesaria para FI-1, no una prueba de que funcione
  con ecografías.

## 10. Desviaciones

(Ninguna al subir este preregistro.)

**Notas de implementación (25 nov 2026, antes de imprimir nada).** Ninguna cambia una hipótesis, un umbral o una
puerta.

- `data/fi1s/` se añade a `.gitignore`, para que los valores diseñados, las fotos y las marcas no lleguen a git.
- **Geometría fija de las hojas** (`geovida.fi1s`):
  - recuadro de 160 × 120 mm con la esquina superior izquierda en (25, 45) mm;
  - escala a 8 mm del borde derecho, con la primera marca a 15 mm del borde superior;
  - «+» con brazos de 1,6 mm y separados al menos 7 mm entre sí y de la escala;
  - junto a cada «+» va su etiqueta (1a, 1b, …), para que quien marca sepa qué pareja es. Ninguna distancia aparece en
    la hoja.
- **Marcador.** Los clics se guardan en píxeles de la foto original. Con la foto ajustada a la ventana, un píxel de
  pantalla equivale a varios de la foto, así que la herramienta pide hacer zoom antes de cada punto. Se comprobó en el
  navegador con una imagen generada: el error es 0 px a zoom ×3.
- **Pruebas sintéticas** (`tests/test_fi1s.py`): una foto simulada de cada hoja, con perspectiva y ruido de marcado de
  0,4 px, recupera las distancias diseñadas con la cadena de FI-1. El error mediano queda por debajo del 2 %.
