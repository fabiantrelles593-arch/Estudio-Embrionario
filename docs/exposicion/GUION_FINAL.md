# Guion de la exposición final (en el orden de las láminas)

> Generado a partir de las notas de `final/deck.html` (tecla **G** en la presentación). Duración orientativa:
> 20–25 minutos, unos 50 segundos por lámina; las láminas 12, 13, 18 y 19 merecen más tiempo.

## 1. Portada — GEOMETRÍA DE LA VIDA

Preséntate. Geometría de la Vida estudia con matemáticas y computación cómo cambia la forma de las estructuras durante el desarrollo embrionario, y dice para cada medida cuánto se puede confiar en ella. Aclara desde el inicio: es investigación en etapa preclínica con datos públicos de ratón; no es una herramienta clínica.

## 2. Qué es — Una plataforma para convertir imágenes del desarrollo en objetos matemáticos medibles

Recorre la cadena de izquierda a derecha. Lo importante: el proyecto trabaja sobre la forma. La forma es un efecto de mecanismos moleculares, celulares y mecánicos que la geometría por sí sola no explica. Termina leyendo la pregunta central: guía toda la exposición.

## 3. Importancia — Las anomalías congénitas son una de las grandes causas de muerte infantil

Cifras de la OMS. Unos 8 millones de bebés nacen cada año con un defecto congénito; 240 mil recién nacidos mueren por esa causa en su primer mes y 170 mil niños más antes de los 5 años. Nueve de cada diez casos graves ocurren en países de ingresos bajos y medios.

## 4. Importancia — En el Perú, 17 de cada 100 muertes neonatales se deben a malformaciones congénitas

En el Perú, según la vigilancia del CDC-MINSA, hasta 2021 las malformaciones congénitas eran la tercera causa de muerte neonatal: 17 de cada 100. No se encontró un desglose nacional más reciente publicado; por eso se dice el año.

## 5. Importancia — Por qué merece la pena un proyecto así

Cinco dimensiones. Insiste en la quinta: la contribución social es una posibilidad a largo plazo, condicionada a la investigación, no un resultado. El proyecto no diagnostica ni previene enfermedades.

## 6. Objetivos — Objetivo general

Lee el objetivo general. Luego señala los colores: verde, abordado con evidencia; amarillo, en curso; violeta, pendiente o futuro. Esta honestidad es parte del método.

## 7. Fundamento — Las anomalías estructurales se forman cuando se forman los órganos

Las anomalías estructurales nacen mientras se forman los órganos. El ratón es el modelo estándar del consorcio IMPC. Las imágenes de abajo son reales: un embrión distinto por estadio, así que es una comparación entre especímenes, no el mismo embrión creciendo.

## 8. Valor — Una diferencia en la imagen no siempre es una diferencia en el embrión

Este es el problema que resuelve el proyecto: una diferencia en la imagen no siempre es una diferencia en el embrión. Si no sabemos cuánto pesa cada fuente técnica, podemos confundir un artefacto con biología.

## 9. Método — Flujo metodológico, con el estado real de cada etapa

Siete etapas, cada una con su estado. Todas tienen código y pruebas; lo que falta es validación externa, sobre todo en interpretación. Abre el panel de detalles si te preguntan por formatos.

## 10. Muestras reales — Los embriones que la plataforma leyó, verificó y midió

Galería de muestras reales, al estilo de repositorios como FaceBase. Haz clic en una tarjeta: se amplía y aparece su ficha con especie, estadio, modalidad, fuente, licencia y huella.

## 11. Muestras reales — IMPC E15.5 · espécimen 0218

Ficha de un espécimen real. Tres cortes con las estructuras de la segmentación publicada. La huella SHA-256 garantiza que es exactamente el archivo publicado.

## 12. Muestras reales — Imagen → referencia → segmentaciones → medidas

Este es el paso de una imagen biológica a un objeto matemático, con una muestra real: el primer caso de la lista, elegido por esa regla y no por cómo salía. Panel 2: la referencia dibujada por personas. Paneles 3 a 5: lo que hacen los segmentadores clásicos de geovida. El umbral global marca casi todo el volumen, por eso no se ve contorno. Mira los números: 701, 309 y 317 mm³ frente a 57. Por eso hace falta el certificado.

## 13. Modelo 3D — Embrión de ratón E11: cuerpo y ventrículos cerebrales en 3D

Modelo 3D real e interactivo. Arrastra para girar y usa la rueda para acercar. La malla turquesa es el cuerpo del embrión E11 y la violeta, sus ventrículos cerebrales, ambos dibujados por personas en una ecografía real. La malla se suavizó solo para verla; las medidas se calcularon sobre la máscara de vóxeles.

## 14. Modelos 2D–5D — De 2D a 5D: qué significa cada nivel y en qué estado está

Cuatro niveles. 2D y 3D están implementados y probados. 4D existe como banco de pruebas sintético en pseudo-tiempo: no tenemos el mismo embrión seguido en el tiempo. 5D es una propuesta de organización analítica: la c es contexto biológico, no una quinta dimensión espacial, y no es lo que los ecógrafos comerciales llaman 5D.

## 15. Topología — Contar piezas, túneles y cavidades

La topología estudia lo que no cambia al deformar sin romper ni pegar: cuántas piezas, túneles y cavidades. Explica la fórmula con los dibujos: una región, dos componentes, un anillo, un toro y una cáscara. Los dibujos son sintéticos, pero los números los calculó el software.

## 16. Topología — Dos máscaras de aspecto parecido pueden tener topologías muy distintas

Topología de datos reales. La referencia del cuerpo, dibujada por personas, no es una bola: tiene 11 túneles y una cavidad con vecindad 26, y otros números con vecindad 6. La convención importa. Los segmentadores clásicos dan miles de piezas: es ruido de la ecografía. Por eso un cambio de χ no demuestra por sí solo una transformación biológica.

## 17. Morfometría — Cómo se cuantifica la forma de una estructura

Descriptores medidos en el corte real del panel 2 de la lámina 12. Di qué mide cada uno con una frase. Aclara qué los calcula: área, perímetro y Betti, geovida; circularidad, solidez, excentricidad y momentos de Hu, scikit-image.

## 18. Semáforo — Una luz para cada medida: ¿cuánto creerle al volumen?

El semáforo es exactamente esto: la probabilidad estimada de que el error de volumen sea de 5 % o menos, calculada solo con la máscara y el tamaño del vóxel. Umbrales preregistrados: verde desde 0,90, rojo por debajo de 0,50. Luego el caso real: sin guardia habría dado verde a medidas con más de 400 % de error; la guardia detecta que la ecografía real está fuera de su calibración y no da verde. Y ya con las 1188 medidas de H11: sin guardia, las 540 de cuerpo habrían salido en verde y todas fallaban; con guardia, ninguna. La pregunta primaria quedó sin evaluar porque no hubo verdes. No es un juicio de salud del embrión.

## 19. MORPHO-TRACE — Otra resolución: unas medidas aguantan y otras no

MORPHO-TRACE estudia cuánto de una medida depende de decisiones técnicas. Ejemplo real: la misma referencia del cuerpo medida a 50, 100, 150 y 200 micras. Lo único que cambia es el tamaño del vóxel. El volumen se mantiene dentro de 1,5 %, el área cae 12 % y los túneles pasan de 11 a 4. Unas medidas son robustas y otras no.

## 20. Resultados reales — La plataforma detectó problemas en datos publicados antes de medir

Primer hallazgo con datos reales. Muestra el 0218 bien alineado y el 0040, cuya segmentación publicada no coincide con su propia imagen: los pulmones y la columna no calzan. Si alguien mide sin revisar, mide mal.

## 21. Resultados reales — Mapa de formas de 717 cabezas de embrión: un resultado negativo honesto

ONTO-MAP: 717 cabezas reales. Los estadios se separan, pero cada uno se registró a su propio atlas. Las tres hipótesis escritas antes salieron contrarias. Un resultado negativo bien medido también es ciencia, y apunta justo a la pregunta de MORPHO-TRACE.

## 22. Validación — Qué se probó, con qué datos y qué demuestra

Seis categorías de pruebas, con su evidencia. Lee la frase final en voz alta: superar una prueba no es validación biológica. Las sintéticas comprueban el algoritmo, no la anatomía.

## 23. Arquitectura — Cómo fluye la información dentro del programa

Arquitectura real, construida a partir de los módulos del código. Cada caja nombra los archivos que existen. Nada de lo que aparece aquí es un plan: todo está en el repositorio con pruebas.

## 24. Futuro — Camino regulado: dónde estamos y qué falta

El destino puede ser clínico, pero el camino es largo y regulado. Hoy: preclínica. En el Perú el software autónomo es dispositivo médico activo: un uso clínico exigiría registro sanitario ante DIGEMID. La ecografía prenatal es una línea de investigación independiente, no una función implementada.

## 25. Futuro — Lo que falta, dicho con claridad

Di primero los límites, luego el futuro. Los límites dan credibilidad: pocas especies, referencias humanas que no son la verdad, ningún veredicto con datos reales todavía, sin revisión externa.

## 26. Conclusiones — Conclusiones

Cierra despacio. Lee la cita final. Ofrece el repositorio y pide lo que necesitas: revisión experta y un laboratorio o servicio de ecografía aliado.

## 27. Fuentes — Datos, cifras y métodos citados

Lámina de respaldo para el turno de preguntas: fuentes de datos, de cifras y de métodos.

## Preguntas probables

- **¿Ya sirve para diagnosticar?** No. Es investigación preclínica con datos de ratón. Un uso clínico exigiría datos humanos con aprobación ética, validación externa y registro sanitario ante DIGEMID.
- **¿Por qué el semáforo no dio verde en la ecografía real?** Porque la guardia detectó que la imagen no se parece a las de su calibración. Es el comportamiento buscado: abstenerse antes que dar una confianza falsa.
- **¿Por qué segmentadores tan simples?** Son métodos clásicos y reproducibles para probar el certificado. MEMOS (una red externa) se usa solo en local en P3, porque la licencia de sus pesos no está declarada.
- **¿Cuántos datos reales hay?** 80 embriones de micro-CT, 717 configuraciones de landmarks y 396 casos de ecografía 3D, todos de ratón y con licencia CC BY.
- **¿Qué es nuevo?** Hasta donde alcanza nuestra búsqueda registrada (PubMed y Europe PMC, 17 nov 2026), no encontramos un certificado por medida con guardia de dominio sin redes neuronales, ni la separación preregistrada entre variación técnica y biológica en embriones. No decimos «primer método».
