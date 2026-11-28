# Integración del PDF externo «Qué tenemos realmente hoy / Qué no tenemos todavía»

> Solo investigación y educación. El PDF (19 páginas) lo aportó el usuario el 12-11-2026 y es, en sus palabras, «una versión entre ChatGPT».
> No es una fuente revisada por pares. Este documento dice **qué se pudo comprobar, qué se corrigió, qué se adoptó y qué no, y por qué**.
> Fecha de la verificación: 12-11-2026 (PubMed y las páginas de las editoriales; no pude abrir el texto completo de todos los trabajos).

## 1. Qué es el PDF y cómo se leyó

* Es un plan de investigación («Prompt Maestro», fases, riesgos, lista de verificación) para una **versión anterior** del proyecto: describe un código de máscaras 2D con
  Hu, β₀, β₁, Euler, un `robustness_index` exploratorio y una capa 4D «diseñada pero no implementada» (versiones 2.5, 3.0 y 4.0).
  El repositorio actual (`geovida`, v0.8) se reescribió desde cero y ya tiene preregistradas las hipótesis H1 a H17 (con huecos de numeración); su «qué no tenemos» sigue siendo cierto en lo esencial
  (sin validación con imágenes reales a escala, sin procesamiento 3D validado), pero ya no en todo: hay **un** piloto con una ecografía 2D real (`docs/RESULTADOS_V08.md`).
* Los marcadores de cita del PDF (por ejemplo `【11†L15-L23】`) apuntan a una herramienta de búsqueda ajena a esta sesión: **no se pueden seguir**. No me apoyé en ellos.
  Comprobé cada referencia por mi cuenta.

## 2. Verificación de las referencias

| El PDF cita | Lo que encontré | Veredicto |
|---|---|---|
| **Yamada et al. 2010** (atlas humano 3D) | *Developmental dynamics*, PMID 20503356, doi 10.1002/dvdy.22316. RM más EFIC, estadios de Carnegie 13 a 23, atlas en la web con cortes 2D en tres planos, anotaciones y reconstrucciones 3D. | **Verificada.** El PDF dice a la vez «CS 13–23» y «etapas 14–22 (44 embriones)»: se contradice; el resumen dice 13–23 y no da el número de embriones (no verificado). |
| **Wong et al. 2012** (atlas de ratón) | *Development*, PMID 22872090, doi 10.1242/dev.082016. 35 embriones C57BL/6J a E15.5, 48 estructuras segmentadas a mano; los volúmenes de órgano varían 2.6–4.2 % (escala lineal, normalizados al cuerpo); con 8 por grupo se detecta una diferencia de volumen de 9–14 %. | **Verificada.** Error del PDF: dice «Carnegie ~18» para el ratón. **El ratón se estadifica con Theiler, no con Carnegie.** «≈ 400 horas de trabajo» no lo pude verificar. (PMID 24850858 es otro trabajo, Wong 2014, el *pipeline* automatizado.) |
| **LAMA, Horner et al. 2021** | *Development*, PMID 33574040, doi 10.1242/dev.192955. *Pipeline* automático (preprocesamiento, registro, estadística, segmentación), atlas E14.5, efecto del subestadio, dos líneas knock-out del IMPC. | **Verificada en lo esencial.** «E14.5/E15.5», «184 etiquetas» y «VBM» no aparecen en el resumen: **no verificados**. (PMID 41621112 es otro trabajo, de 2026.) |
| **MusMorph, Devine et al. 2022** | *Scientific Data* 9:230, doi 10.1038/s41597-022-01338-x. 10 056 especímenes; E10.5, E11.5, E14.5, E15.5, E18.5 y adulto; flujo de trabajo abierto; datos en FaceBase y GitHub; parte de los archivos «a pedido». | **Verificada en lo esencial.** «2 537 landmarks» no lo encontré (la página da 22 *landmarks* dispersos por embrión más una configuración densa): **no verificado**. El PDF omite los adultos. |
| **MEMOS, «Rittschof et al. 2022, Biology Open»** | *Biology Open* 12(2), 2023, doi 10.1242/bio.059698, PMID 36802342; versión previa en bioRxiv en 2022. Autores: **Rolfe SM, Whikehart SM, Maga AM**. Extensión de 3D Slicer, 50 estructuras, validada contra segmentación por atlas, datos del IMPC. | **La herramienta y su descripción son correctas; la autoría y el año del PDF son incorrectos.** PubMed lista tres autores y ninguno es Rittschof. |
| **Matula et al. 2022** | *Scientific Reports*, PMID 35610276, doi 10.1038/s41598-022-12329-8. CNN que segmenta la cápsula nasal cartilaginosa en μCT; **mediana** de Dice 84.44 %; de unas 8 h manuales a 130 s por muestra; base pequeña. | **Verificada.** El PDF dice «Dice medio»; es **mediana**. «E17.5» y «14 volúmenes» no están en el resumen: **no verificados**. |
| **UniCoN, Sapkota et al. 2025** | *Scientific Reports*, 31-1-2025, PMID 39890924, doi 10.1038/s41598-025-87797-9 (existe una corrección de autores, PMID 40082540). Módulos condicionados por edad discreta y posición de recorte, aplicables a cualquier arquitectura (CNN, transformers); +1.7 % de Dice en promedio y +7.5 % en datos no vistos. | **Verificada.** El PDF admite que solo vio el título; lo llama «CNN multitarea condicional», que **no coincide** con el resumen (condicionamiento, no multitarea). |
| **Metrics Reloaded, Maier-Hein et al. 2024** | *Nature Methods*, PMID 38347141, doi 10.1038/s41592-023-02151-z. Marco de selección de métricas **guiado por una «huella del problema»**; cubre clasificación de imagen, detección de objetos, segmentación semántica y de instancias. | **Verificada, con matiz.** El PDF lo resume como «recomienda usar múltiples métricas»; la recomendación real es **elegir las métricas según el problema**, no sumar métricas. Además **no cubre** medidas morfométricas con incertidumbre ni certificados: lo que `geovida` hace queda fuera de su alcance declarado. |

No verificadas (no las busqué): Muñoz-Solórzano 2016, Kaufman 1992, Eyasu et al., «DMDD», «IMPC/IGMM» como fuentes concretas. Quedan marcadas como **EVIDENCIA INDIRECTA** hasta que alguien las abra.

**Resultado de la verificación:** 8 de 8 referencias principales existen y tratan lo que el PDF dice en lo esencial; **encontré 3 errores** (MEMOS: autoría y año; ratón con Carnegie; media en vez de mediana) y **una contradicción interna** (Yamada). Sin esa comprobación habría copiado los errores.

## 3. Qué recomienda el PDF y qué se hizo con cada cosa

| Recomendación del PDF | Estado en `geovida` | Decisión |
|---|---|---|
| Separar lo que hay hoy de las metas; ser honesto con el límite | README, `RESULTADOS_V0x`, secciones «Qué no se puede concluir», `docs/ERRATA.md` | **Ya cubierta.** |
| Hipótesis falsable, preregistrada, criterios de aceptación antes de mirar | `docs/PREREGISTRO_*.md` (H1–H17, REAL2D) | **Ya cubierta.** |
| Unidad de análisis = individuo (embrión/gestación), no cada medida; modelos mixtos; sin pseudorreplicación | H17 ya usa la gestación como unidad y un par por gestación | **Adoptada como regla** para todo análisis con datos reales (§4); los modelos mixtos se usarán cuando haya medidas repetidas reales. |
| Varias métricas de acuerdo: Dice, IoU, HD95, ASSD, Δ de volumen/área | `geovida.measure` ya tenía Dice, HD95 y distancia media; **faltaban IoU, Δ relativo, ASSD estándar** y una convención explícita | **Adoptada ahora: `geovida.agreement`** (tarea #46), con las definiciones escritas y probadas. |
| Acuerdo intra e inter-observador; línea base de error humano | `RUTA_DE_VALIDACION_REAL` ya pide dos operadores; no había forma de resumir su acuerdo | **Adoptada ahora:** Bland–Altman (sesgo y límites de acuerdo) en `geovida.agreement`. |
| Conjunto retenido / validación externa | Confirmaciones con semilla nueva y modelos congelados (H9, H14), y H15 usó los modelos de H14 sin recalibrar; G2 de la ruta | **Ya cubierta** para simulación; H16 lo hará explícito para la cadena de imagen. Validación externa con equipos reales: no hecha (G2). |
| Potencia y tamaño de muestra previos | Clopper–Pearson (29/46/61 verdes) en `RUTA_DE_VALIDACION_REAL`; tabla de H17 | **Ya cubierta.** |
| Etiquetas de evidencia (HECHO VERIFICADO / EVIDENCIA INDIRECTA / HIPÓTESIS / PROPUESTA) | No había convención única | **Adoptada** (§5). |
| Reproducibilidad: CI, entorno, datos crudos inmutables, manifiestos | `.github/workflows/ci.yml`, manifiestos con commit y semilla, SHA-256 | **Ya cubierta.** Docker/Codespaces: no hecho. |
| 4D = pseudotiempo, no seguimiento longitudinal | Coincide con la rama `geovida trajectory` (dos escenarios, sin predecir, H17 para ponerla a prueba) | **Ya cubierta**; el PDF refuerza ese diseño. |
| Fases I–X de 24 semanas con asesor y «puertas» de revisión | Puertas G0–G4 (`docs/RUTA_DE_VALIDACION_REAL.md`) | **Mapeada**, no copiada: el calendario supone un equipo y un asesor que esta sesión no tiene. |
| `robustness_index` (0–100) | No existe en `geovida` | **No adoptada** (§6). |
| Homología persistente | No existe; hay números de Betti y el margen topológico de H9 | **No adoptada** (§6). |
| Línea principal en cartílago nasal de ratón E15–E18 (Matula/UniCoN) | No hay volúmenes ni licencia disponibles | **No adoptada como línea principal ahora** (§6); queda como opción si aparece un volumen con permiso. |

## 4. Reglas adoptadas (valen desde hoy)

1. **El individuo es la unidad.** Con datos reales, una gestación (o un embrión) es una observación; varias imágenes o medidas del mismo individuo son medidas repetidas, no observaciones independientes.
   Ningún IC ni prueba cuenta un píxel, un vóxel ni una medida repetida como muestra independiente.
2. **Las métricas se eligen por la pregunta.** Dice e IoU miden solapamiento y fallan con objetos finos o pequeños; HD95 y ASSD miden distancia de contorno; el Δ relativo de longitud, área o volumen es la cantidad
   que le importa a quien mide. Un informe de acuerdo muestra **varias**, con su definición, y no promedia en un solo índice.
3. **El acuerdo entre personas se informa antes que el acuerdo con la máquina.** El error de una persona fija el piso: pedir a la máquina más acuerdo con un lector del que ese lector tiene consigo mismo no tiene sentido.
4. **Toda afirmación de un documento nuevo lleva una etiqueta de evidencia** (§5).

## 5. Convención de etiquetas de evidencia

| Etiqueta | Cuándo se usa |
|---|---|
| **HECHO VERIFICADO** | Comprobado por mí contra la fuente primaria o con una ejecución reproducible del código, y con el alcance exacto (por ejemplo «en esta imagen», «en esta simulación»). |
| **EVIDENCIA INDIRECTA** | Hay una fuente, pero no la leí completa, no pude comprobar la cifra, o viene de un resumen de otro. |
| **HIPÓTESIS** | Plausible, no comprobada. Si está preregistrada, se cita su documento. |
| **PROPUESTA** | Una decisión de diseño o un plan; no afirma nada sobre el mundo. |

Aplicada a lo principal de este proyecto:

| Afirmación | Etiqueta |
|---|---|
| Las ecuaciones de INTERGROWTH-21st de `trajectory` son las publicadas y concuerdan con su Tabla 2 dentro de 2 mm | HECHO VERIFICADO |
| En la imagen real del piloto, la CRL automática (37.57 mm) coincide con la impresa (37.4 mm) en 0.5 % | HECHO VERIFICADO, **solo esa imagen** (n = 1) |
| El certificado de datación no resiste la cadena pantalla–impresión–foto | HECHO VERIFICADO **en simulación** (H15); en imagen real: EVIDENCIA INDIRECTA |
| Con la cadena, el certificado de decisión (ranura) aguanta | HECHO VERIFICADO en simulación; en real: HIPÓTESIS |
| El método es exacto en ecografía real | HIPÓTESIS (sin datos; la puerta G1 la pondría a prueba) |
| La envolvente de dos escenarios cubre la CRL futura | HIPÓTESIS (H17, preregistrada, sin datos) |
| La cifra «Dice 84.4 %» de Matula como referencia de lo que logra una red en cartílago nasal | EVIDENCIA INDIRECTA (solo el resumen) |
| Un certificado abierto puede servir donde el equipo o la experiencia son limitados | HIPÓTESIS de uso |
| `geovida.agreement` | PROPUESTA hasta que pase sus pruebas; luego, HECHO VERIFICADO de lo que sus pruebas cubren |

## 6. Lo que no se adoptó, y por qué

* **`robustness_index` (0–100).** El PDF mismo lo llama «heurístico, sin validación de significado anatómico» y propone conservarlo solo si mejora sobre alternativas estándar. No hay nada que lo compare.
  `geovida` ya tiene algo que **sí** se calibró contra una verdad conocida: la tasa de falso verde y la calibración (ECE) del certificado. Un índice de 0 a 100 sin esa calibración invita a leerlo como confianza.
  *Qué haría falta para adoptarlo:* una hipótesis preregistrada en la que el índice **prediga** el error real mejor que un indicador simple (por ejemplo el propio desenfoque), con datos que no se usaron para definirlo.
* **Homología persistente.** El PDF dice «solo si agrega valor claro». No hay una pregunta del proyecto que los números de Betti y el margen topológico de H9 no contesten. Añadirla sería adorno.
* **Cartílago nasal de ratón como línea principal.** Sería una línea razonable (hay referencia publicada, Matula; los datos de MusMorph y de IMPC son públicos en parte), pero **no tengo ningún volumen, ni sus licencias verificadas**, y la prioridad del usuario es la
  ecografía y el uso en la sociedad. Queda como opción si se consigue un volumen con permiso; entonces `geovida.agreement` ya estará listo para compararlo con segmentaciones de referencia.
* **Calendario de 24 semanas y asesor.** Se tomaron las puertas, no el calendario.
* **Estadificación.** Se mantiene Carnegie para humano (`docs/ATLAS_ESTADIOS.md`) y se deja explícito que el ratón usa Theiler; no se mezclan.

## 7. Lo que cambió por este documento

* `docs/RUTA_DE_VALIDACION_REAL.md`: la puerta G0 decía «falta la imagen en la sesión»; la imagen llegó y se midió (n = 1). Se corrigió y se aclaró que no avanza ninguna otra puerta.
* `docs/clinico/TRAZABILIDAD.md`: fila de esta integración.
* Tareas abiertas por esta integración: `geovida.agreement` (acuerdo y Bland–Altman), linealización del mapa de color con la propia barra de la captura, H16.

## 8. Qué sigue siendo cierto del PDF y qué no cambia

* «No hay datos embrionarios reales validados» **sigue siendo cierto**, con la excepción de un piloto de una imagen que no valida nada.
* «No hay validación con expertos en biología del desarrollo» **sigue siendo cierto**; `docs/PANEL_DE_REVISION.md` describe un panel que **no existe**.
* El PDF no aporta datos nuevos ni resultados: aporta una lista de comprobaciones razonable, de la que ya había cubierto buena parte (§3) y de la que se adoptó el resto que servía.
