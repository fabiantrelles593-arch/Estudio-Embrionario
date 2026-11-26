# Síntesis: el certificado de fiabilidad de MORPHO-TRACE, de la simulación a la ecografía real (H6–H23)

- **Fecha:** 25 nov 2026.
- **Qué es:** un resumen de los veredictos ya publicados en cada `RESULTADOS_*.md`. No hay ningún análisis nuevo, ni
  ningún número recalculado ni reinterpretado. Si un número de aquí no coincide con su documento de origen, manda el
  documento de origen.
- **Etiquetas:** [HV] verificado en el documento citado · [HIP] hipótesis · [PROP] propuesta.
- **Datos:** solo simulación y datos animales publicados (Qiu et al. 2021, IEEE DataPort, doi:10.21227/drmd-xq36,
  CC BY). Nada clínico.

## 1. La pregunta de la línea

**¿Puede el instrumento decir, caso a caso y sin la referencia, cuándo su medida de volumen es fiable?** Para eso emite
una luz:

- **verde:** la medida está a ≤ 10 % de la referencia;
- **amarilla o roja:** no se garantiza.

El criterio común de todos los estudios: **entre las verdes, como mucho el 10 % puede fallar** (|error| > 10 %).

## 2. Cronología y veredictos [HV]

| Estudio | Datos | Qué se probó | Veredicto principal | Fuente |
|---|---|---|---|---|
| H6 | Sintético | Semáforo de adecuación con solo la máscara y el vóxel | 5 de 5 apoyadas | `docs/RESULTADOS_V03.md` |
| H9 / H10 | Sintético | Certificado calibrado (H9d) y guardia de dominio (H10b) | H9d apoyada (6 de 6 estratos; máximo 7,0 % de verdes falsas); H10b apoyada. **H9g no apoyada:** sin guardia, falla con imágenes desplazadas | `docs/RESULTADOS_V04.md` |
| H12 | Ecografía simulada | Recalibrar con moteado y atenuación | H12c apoyada solo en 2 de 6 estratos; los otros 4 nunca dan verde | `docs/RESULTADOS_V05.md` |
| **H11** | **Ecografía real** (1188 medidas) | El certificado de v0.4 con segmentadores de umbral | **Primaria no evaluable (0 verdes).** H11a apoyada (la guardia rechaza todo); H11c apoyada: sin guardia, 540 de 540 verdes eran falsas | `docs/h11/RESULTADOS_H11.md` |
| H12R | Ecografía real | La calibración de H12 sobre los mismos casos | Primaria no evaluable (0 verdes); 180 de 180 verdes sin guardia, falsas. El simulador no cubre el equipo real | `docs/h11/RESULTADOS_H12R.md` |
| H18 | Ecografía real | Segmentador de umbral con limpieza, calibrado con datos reales | No evaluable por diseño: solo 1 de 136 casos a ≤ 10 % | `docs/h18/RESULTADOS_H18.md` |
| H19 | Ecografía real | Red de dos etapas y certificado con observables de imagen | Puerta S superada (24 de 27 a ≤ 10 %; Dice 0,938). **Puerta C no:** 2 de 16 verdes fallan, peor que dar verde a todo | `docs/h19/RESULTADOS_H19.md` |
| **H20** | **Ecografía real, prueba sellada** | Luz basada en la estabilidad de la propia red (volteos y acuerdo entre etapas) | **H20b apoyada:** 1 de 21 verdes falla (4,8 %; IC 0–14,3 %). La red mide bien en embriones nuevos (93,2 % a ≤ 10 %), **pero la luz apenas separa** aciertos de fallos (H20d: IC de la diferencia incluye 0) | `docs/h20/RESULTADOS_H20.md` |
| H21 | Sintético | Crofton frente a `area_sdf` como estimador de área | No concluyente; se mantiene `area_sdf` | `docs/h21/RESULTADOS_H21.md` |
| H22 | Sintético | Un estado «inservible» además de «fuera de dominio» | No se añade: el rojo ya cubre el 99 % de los fallos groseros | `docs/h22/RESULTADOS_H22.md` |
| H23 | Ecografía real, ventrículos | La regla de H20, sin cambios, en una estructura pequeña | **No evaluable:** puerta S superada (22 de 34), puerta C no (0 verdes de 34). Prueba sin abrir | `docs/h23/RESULTADOS_H23.md` |

## 3. Lo que está establecido [HV]

1. **Sin guardia de dominio, el certificado calibrado en simulación da verdes falsas en datos reales.** Lo mostraron
   H11c y H12R: el 100 % de las verdes sin guardia eran falsas. La guardia es imprescindible, no un adorno.
2. **La guardia funciona como freno:** en H11 y H12R rechazó todas las medidas reales en lugar de dar verdes falsas.
3. **El segmentador era el cuello de botella.** Con segmentadores de umbral, casi ninguna medida real queda a ≤ 10 %
   (H11, H18). Con una red aprendida de dos etapas, la mayoría sí: cuerpo 93,2 % en embriones nuevos (H20) y ventrículos
   65 % en calibración (H23, con D-1).
4. **Los observables de la imagen no anticipan los fallos de una red** (H19, puerta C). **La estabilidad de la propia red
   sí dio una luz verde segura para el cuerpo** en embriones nuevos (H20b, prueba sellada medida una vez).
5. **Esa luz no se traslada tal cual a una estructura pequeña** (H23: 0 verdes). Con umbrales fijos, la estabilidad
   medida depende del tamaño de la estructura.
6. **El protocolo funcionó.** Cada prueba sellada se abrió como mucho una vez:
   - H18, H19 y H23 se pararon en sus puertas sin abrirla;
   - H20 la abrió una vez;
   - ningún umbral se cambió después de ver datos de prueba.

## 4. Lo que NO está establecido

- **Que la luz distinga aciertos de fallos.** En H20 casi no había fallos (H20d sin separación) y en H23 no hubo verdes.
  Es la pregunta abierta más importante de la línea.
- **Que algo de esto valga fuera de un conjunto, un equipo y una especie.** Todos los datos reales son de Qiu et al.
  2021. No se encontró otro conjunto público con referencia manual y licencia y ética verificadas
  (`docs/h20/CANDIDATOS_REPLICACION.md`).
- **Nada sobre humanos ni sobre uso clínico.**

## 5. Patrones que se repiten [HIP]

- **Simulación → realidad.** Cada vez que un componente calibrado en sintético llegó a datos reales (H11, H12R), falló o
  se negó a emitir. Lo que funcionó con datos reales (H19, H20) se ajustó con datos reales.
- **Las reglas de luz con umbrales absolutos** son frágiles al cambiar de estructura: H12 nunca daba verde en 4 de 6
  estratos, y H23 en ninguno. Una regla relativa a la escala de la estructura es la hipótesis natural.
- **El valor del «no evaluable».** La mitad de los estudios con datos reales acabaron así. No es un fracaso del
  protocolo: es el protocolo evitando una conclusión que los datos no permitían.

## 6. Qué se podría afirmar hoy en una publicación [PROP]

> En ecografía 3D de alta frecuencia de embriones de ratón (un conjunto público), una red de dos etapas mide el volumen
> corporal a ≤ 10 % de la referencia manual en el 93 % de los embriones nuevos. Una luz verde basada solo en la
> estabilidad de la propia red falló en 1 de 21 casos en una prueba sellada medida una sola vez. Esa luz no se traslada
> sin cambios a los ventrículos cerebrales, y no se demostró que separe aciertos de fallos. Un certificado calibrado en
> simulación, sin guardia de dominio, dio un 100 % de verdes falsas en datos reales.

Antes de publicar algo así hacen falta:

- la búsqueda en Scopus o Web of Science y un segundo revisor (P1 del informe);
- la revisión de un asesor externo.

## 7. Huecos y siguientes pasos posibles (cada uno requiere decisión y preregistro)

| Hueco | Paso | Bloqueo |
|---|---|---|
| Otro conjunto o equipo | Replicación directa de H20 | Respuesta del grupo de NYU (mensaje pendiente de envío) |
| ¿Separa la luz aciertos de fallos? | Una regla con umbrales relativos a la estructura, fijados por principio antes de abrir la prueba de ventrículo, que sigue intacta | Decisión del autor. Hay que declarar que la calibración de H23 ya se vio |
| Revisión sistemática completa | Scopus o Web of Science y un segundo revisor | Acceso a esas bases |
