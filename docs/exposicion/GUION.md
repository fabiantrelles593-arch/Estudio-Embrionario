# Guion de la exposición «¿Cuándo podemos fiarnos de una medida?»

Duración sugerida: 15 a 16 minutos más preguntas. El mazo (`exposicion-geovida.html`) lleva este guion
dentro: la tecla **G** lo muestra lámina por lámina.

## Antes de exponer (5 minutos)

1. Abre `exposicion-geovida.html` en el navegador del computador que vas a proyectar. No necesita
   internet. Pantalla completa con F11.
2. Pulsa «Ejecutar la prueba» (lámina 7) una vez, solo para comprobar que corre (5–7 segundos).
3. Mira que la demostración 1 muestre el cubo rojo de 2 vóxeles: es el punto de partida.
4. Ten abierta la tecla G para leer las notas de cada lámina si te pierdes.

## Orden y tiempos

| Láminas | Tema | Tiempo |
|---|---|---|
| 1–2 | Portada y problema: una imagen no es el objeto | 2 min |
| 3–4 | Por qué importa; pregunta, hipótesis y variables | 2 min |
| 5 | La solución en tres ideas | 2 min |
| 6 | Demostración 1: el semáforo en vivo | 2 min |
| 7 | **Demostración 2: la prueba de que funciona** (200 objetos al azar) | 2 min |
| 8–10 | Demostraciones 3, 4 y 5: volumen y forma, crecimiento 4D, eje de escala | 3 min |
| 11 | El programa real en Python (salida de `geovida plan` y `geovida certify`) | 1 min |
| 12–14 | Resultados, lo que salió mal, límites | 2 min |
| 15 | Impacto y siguiente paso | 1 min |
| 16–18 | Glosario, cuestionario, preguntas del jurado: para estudio o para el turno de preguntas | — |
| 19 | Cierre | 1 min |

(Los números de lámina pueden cambiar si el mazo se amplía; los títulos de la barra inferior son
la referencia.)

## Los tres mensajes

1. Una imagen no es el objeto: la resolución cambia el volumen y hasta el número de agujeros.
2. Con objetos de respuesta conocida se puede medir el error y construir un semáforo que avisa
   cuándo no fiarse de una medida, sin necesitar la respuesta.
3. Las reglas y las predicciones se escriben antes, y lo que sale mal también se publica.

## Qué decir de la prueba en vivo (lámina 7)

* Usa imágenes ideales, sin ruido, y umbral fijo: es la configuración más simple del proyecto.
* En cuatro corridas de prueba dio entre 2,2 % y 3,8 % de luces verdes falsas; el experimento
  completo dio 2,3 % en esa misma configuración. El criterio, escrito de antemano, era menos de 10 %.
* Salen unas 80 luces verdes, así que el porcentaje cambia de una corrida a otra. Si sale alto,
  repítela y explícalo: es parte de la honestidad del método.

## Frases que no conviene decir

«Primer método» o «nunca antes» (no lo sabemos: solo no encontramos algo igual); «validado» a secas
(es validado en objetos sintéticos); «detecta errores topológicos» (los fallos silenciosos no se
detectan); «5D» (en bioimagen ya significa otra cosa: aquí es un eje de escala de medición);
«diagnostica» o «reduce la mortalidad» (no hay validación clínica).

## Preguntas del jurado

* **¿Lo probaste con embriones reales?** No. Solo con formas matemáticas y un simulador de imagen,
  porque solo así se conoce la respuesta correcta. Siguiente paso: imágenes públicas con licencia.
  Una imagen de una persona solo con consentimiento, anonimización y aprobación ética.
* **¿Cómo sabes que el semáforo funciona?** Se calibró con unas imágenes y se comprobó con 50 400
  que no había visto, con el criterio escrito antes: en verde se equivocó entre 0,4 % y 2,6 %.
  La demostración 2 lo repite en vivo con objetos nuevos.
* **¿Qué tiene de nuevo?** Las ideas sueltas ya existen. No encontramos en la literatura la
  combinación: una probabilidad por medida, calibrada con verdad conocida, que además se niega a
  certificar imágenes distintas de las de su calibración. Es una ausencia en nuestra búsqueda, no
  una prueba de que nadie lo haya hecho.
* **¿Para qué sirve si no diagnostica?** Para que quien investiga sepa si puede fiarse de sus
  medidas y qué resolución necesita antes de tomar la imagen.
* **¿Lo hiciste tú?** Yo planteé el problema, dirigí las decisiones y revisé resultados. El código
  se desarrolló con asistencia de inteligencia artificial (Claude) y está declarado así en el
  repositorio. Aún no tiene revisión científica externa.
* **¿Cuál es la parte más débil?** Que no hay datos reales ni revisión externa, y que un rasgo que
  la imagen pierde por completo no se puede detectar.
