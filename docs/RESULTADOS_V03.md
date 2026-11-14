# Resultados de v0.3: el instrumento juzga su propia fiabilidad

Tres pruebas, las tres con criterios y predicciones confirmados en git antes de ejecutarse
(`PREREGISTRO_H6.md`, `PREREGISTRO_H7.md`, `PREREGISTRO_H8.md`). Todo es sintético: describe el
instrumento de medida, no biología.

| Prueba | Pregunta | Veredicto |
|---|---|---|
| H6 | ¿Puede el instrumento saber, solo con la máscara y el vóxel, si su volumen es fiable? | 5 de 5 apoyadas |
| H7 | ¿Arregla la topología 2D con moteado una limpieza que escala con el objeto? | 1 de 3 apoyadas |
| H8 | ¿Mejora la tasa de crecimiento 4D si se descartan las etapas que el semáforo marca en rojo? | 3 de 3 apoyadas |

## H6 — Semáforo de adecuación de resolución (volumen)

**Qué es.** Un modelo logístico por segmentador y perfil de imagen que convierte la profundidad
media interior de la máscara, d̄/h (media de la distancia a la frontera sobre los vóxeles del
objeto, en vóxeles), en la probabilidad de que el volumen medido tenga error ≤ 5 %. Verde si
p ≥ 0.90, amarillo si 0.50 ≤ p < 0.90, rojo si p < 0.50. No usa la verdad.

**Calibración** (semilla 20261116, 37 800 filas): la validación cruzada dejando una forma fuera
eligió d̄/h frente al cociente V̂/(Ŝ·h) (entropía cruzada 0.245 frente a 0.377): el área medida
colapsa a baja resolución y arrastra al cociente.

**Confirmación** (semilla 20261114, 10 formas, 50 400 filas, nada reajustado):

| Estrato | AUC | ECE | Luces verdes | Verde falso (IC 95 %) | Verde falso del modelo ingenuo |
|---|---|---|---|---|---|
| global · ideal | 0.926 | 0.025 | 3771 | 2.3 % (1.8–2.8) | 15.8 % |
| global · realistic | 0.937 | 0.024 | 3309 | 1.9 % (1.5–2.4) | 16.8 % |
| otsu · ideal | 0.925 | 0.029 | 2528 | 2.6 % (2.0–3.3) | 4.9 % |
| otsu · realistic | 0.969 | 0.010 | 2492 | 1.9 % (1.5–2.5) | 0.8 % |
| smoothed_otsu · ideal | 0.981 | 0.028 | 917 | 0.4 % (0.2–1.1) | 6.4 % |
| smoothed_otsu · realistic | 0.985 | 0.020 | 854 | 2.0 % (1.2–3.2) | 5.9 % |

* **H6a apoyada:** el modelo ingenuo (el de H3 aplicado al cociente medido) supera el 10 % de
  verde falso en 2 estratos.
* **H6b apoyada:** AUC ≥ 0.85 en 6 de 6. **H6c apoyada:** ECE ≤ 0.10 en 6 de 6.
* **H6d apoyada:** verde falso ≤ 10 % en los 6 estratos (máximo 2.6 %).
* **H6e apoyada:** mejor entropía cruzada que el ingenuo en 5 de 6 (en `otsu · realistic` el
  ingenuo es algo mejor: 0.218 frente a 0.224).

Figuras: `figures/h6_reliability.png`, `figures/h6_lights_by_resolution.png`,
`figures/h6_false_green_by_shape.png`.

**Lo que hay que leer con cuidado (extensión descriptiva, sin veredicto):**

* **Por forma, la bola es el peor caso:** verde falso de 12.9 % (`global · ideal`), 12.5 %
  (`otsu · ideal`) y 10.4 % (`global · realistic`). El criterio preregistrado era por estrato, no
  por forma, y se cumple; pero con objetos casi esféricos el semáforo es optimista.
* **Con Otsu y t/h ≤ 4** casi no hay luces verdes (≈ 1 % de las imágenes) y las pocas que hay
  aciertan solo 43–58 %.
* **Declarar mal el perfil entre `ideal` y `realistic`** apenas cambia nada (verde falso ≤ 3.6 %).
  Esto dio una falsa tranquilidad: v0.4 muestra que con perfiles más alejados el semáforo se rompe.
* **Coste:** con `smoothed_otsu` solo el 55 % de las imágenes llega a verde incluso a 12 vóxeles.

**Procedencia.** Los datos crudos de la primera corrida de confirmación se perdieron al
reciclarse el contenedor de trabajo antes de analizarlos. Se regeneraron con la misma semilla y
el mismo código de medición (`h6_run_manifest.json` lo explica y `h6_run_manifest_original.json`
conserva el manifiesto original). Que la regeneración es fiel se apoya en una comprobación directa
hecha en H8: dos corridas del mismo barrido dieron tablas idénticas fila a fila. La calibración no
se volvió a correr.

## H7 — Limpieza 2D que escala con el objeto

**Qué es.** Sobre la máscara de cada segmentador: quitar componentes y rellenar huecos de menos
de max(4, 0.5 % del área del componente mayor) píxeles. Cada versión limpia se compara con su
base **en la misma imagen** (8 400 imágenes, semilla 20261120).

* **H7a no apoyada.** Con moteado «compuesto», la limpieza recupera al menos la mitad del margen
  disponible solo en 8 de 18 celdas (44 %; el criterio pedía ≥ 75 %). Ayuda mucho en términos
  absolutos (`annulus`, `smoothed_otsu`, 20 px: 0 % → 82 %), pero con `smoothed_otsu` la base es
  casi 0 % y no llega a la mitad.
* **H7b no apoyada, tal como estaba escrita.** El criterio pedía que el error mediano de área
  cambiara menos de un punto en las 24 celdas; cambió ≥ 1 punto en 11. *Post hoc:* en 10 de esas
  11 el error **baja** (la limpieza quita motas del fondo; p. ej. disco a 6 px: 123 % → 96 %) y en
  una sube 1.2 puntos. El criterio estaba mal planteado (medía cambio, no daño); se puntúa como
  no apoyada y la lectura favorable queda marcada como posterior.
* **H7c apoyada.** En `ring_tight` (hueco tan estrecho como la pared), con moteado compuesto y
  t/h ≥ 6, la limpieza no bajó la topología correcta más de 1 punto en ninguna de las 8 celdas.

**Donde sí daña (descriptivo):** con imagen **ideal**, la limpieza rellena el hueco real de
`ring_tight` cuando mide menos que el umbral: `global` 100 % → 20 % a 2 px; `otsu` 100 % → 15 %;
`smoothed_otsu_s2` 99 % → 0 % a 6 px (`figures/h7_harm_ideal.png`). Con moteado «crudo» la
topología no se recupera (máximo 33 %). Con `global` y `otsu` la limpieza casi no ayuda.

Mensaje: la limpieza es una herramienta que exige saber el tamaño del rasgo real más pequeño. No
es un arreglo universal, y en 2D con moteado la topología sigue siendo la medida más frágil.

## H8 — El semáforo en la estimación de crecimiento 4D

**Qué es.** 900 series sintéticas de un objeto que crece ×1.35 por etapa durante 8 etapas con
vóxel fijo (de 2.0 a 16.3 vóxeles). La tasa es la pendiente de ln V frente a la etapa; la
verdadera es 0.900. Se compara ajustar con todas las etapas o sin las que el semáforo de H6 marca
en rojo (semilla 20261119).

| Estrato | Error mediano, todas | Error mediano, sin rojas | Series sin tasa | Regla «≥ 100 vóxeles» |
|---|---|---|---|---|
| global · ideal | 2.8 % | 1.1 % | 0 % | 0.6 % |
| global · realistic | 4.3 % | 1.2 % | 0 % | 1.1 % |
| otsu · ideal | 4.3 % | 0.9 % | 0 % | 1.1 % |
| otsu · realistic | 64.2 % | 1.1 % | 0 % | 72.2 % |
| smoothed_otsu · ideal | 10.7 % | 2.0 % | 70 % | 9.9 % |
| smoothed_otsu · realistic | 10.8 % | 2.2 % | 89 % | 10.7 % |

(Las dos primeras columnas son pareadas, sobre las series con tasa definida sin rojas. La última
columna es pareada con la del semáforo en `smoothed_otsu`.)

* **H8a apoyada:** descartar las rojas reduce el error en los 6 estratos.
* **H8b apoyada:** el error resultante es ≤ 5 % en los 6 (0.9–2.2 %).
* **H8c apoyada por el criterio (4 de 6 estratos con ≤ 25 % de series perdidas), con un coste que
  no se puede esconder:** con `smoothed_otsu` el 70 % y el 89 % de las series se quedan sin tasa,
  porque casi todas sus etapas son rojas.
* **Regla simple sin semáforo** (descartar etapas con menos de 100 vóxeles): iguala o gana al
  semáforo en 2 de 6 estratos (los de `global`) y fracasa con ruido (`otsu · realistic`: 72 % de
  error, porque las motas inflan el recuento de vóxeles).

Figuras: `figures/h8_lights_by_stage.png`, `figures/h8_rate_error.png`.

**Reproducibilidad comprobada.** El primer barrido de H8 quedó marcado `code_dirty` por un retoque
de una figura hecho mientras arrancaba. Se repitió con el árbol limpio y las dos tablas (21 600
filas) son **idénticas**.

## Mis predicciones, puntuadas

| Predicción | Probabilidad que di | ¿Ocurrió? |
|---|---|---|
| La validación cruzada elige la profundidad media | 70 % | sí |
| H6a apoyada | 85 % | sí |
| H6b apoyada | 80 % | sí |
| H6c apoyada | 60 % | sí |
| H6d apoyada | 45 % | sí |
| H6e apoyada | 85 % | sí |
| H7a apoyada | 60 % | no |
| H7b apoyada | 75 % | no |
| H7c apoyada o parcial | 25 % | sí |
| `ring_tight`, ideal, 2 px: `global_clean` < 20 % | 90 % | no (20 % exacto) |
| H8a apoyada | 80 % | sí |
| H8b apoyada | 70 % | sí |
| H8c apoyada | 70 % | sí |
| La regla de 100 vóxeles iguala al semáforo en ≥ 4 de 6 | 50 % | no (2 de 6) |

En H7 me equivoqué en las tres direcciones: esperaba que la limpieza ayudara más y dañara más de
lo que hizo en las celdas preregistradas.

## Qué no se puede concluir

* El semáforo vale para el volumen, para este simulador y para imágenes parecidas a las de su
  calibración. v0.4 muestra que fuera de ese dominio da luz verde falsa.
* H8 usa crecimiento exponencial, escalado isótropo y sólidos simples. No es crecimiento
  embrionario ni hay seguimiento longitudinal.
* H7 usa un modelo sencillo de moteado; no son ecografías.
* Ninguna imagen real, humana o animal, se ha procesado. No hay revisión científica externa.
