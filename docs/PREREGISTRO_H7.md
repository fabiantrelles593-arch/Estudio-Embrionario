# Preregistro — H7: limpieza 2D que escala con el objeto, probada donde ayuda y donde daña (v0.3)

> Se confirma (`git commit`) **antes** de correr `scripts/run_h7.py`. Los cambios posteriores van
> solo en «Desviaciones». H7 no modifica ningún veredicto de H5 (v0.2) ni los datos de ese barrido.

## 1. Pregunta y por qué importa

En H5 la topología de un anillo no se recuperó de forma fiable ni con 20 px sin limpieza: el moteado
fragmenta la máscara en componentes y huecos diminutos. En 3D, la limpieza mínima ayudó pero borró
cavidades reales pequeñas (ERRATA E11; cáscara fina a 4 vóxeles: 93 % → 0 %). Aquí se prueba una
limpieza 2D **que escala con el objeto** y, por la lección de E11, también donde puede hacer daño.

**Intervención** (`twod._clean_mask_2d`): se quitan componentes (8-conexos) y se rellenan huecos
(4-conexos, no el exterior) menores que `max(4, ceil(0.005 · A))` píxeles, con A = área del componente
mayor. Es una extensión del segmentador, no cambia los cuatro preregistrados de H5.

Piloto (semilla 20261121, **no** usada aquí; 12 réplicas por celda; ejecutado antes de fijar
estos criterios):

* Ayuda: con `smoothed_otsu_s2` y moteado «compuesto», el anillo pasa de 50 %/67 %/67 % a
  92 %/100 %/100 % de topología correcta (t/h = 8/12/20); el disco de 25 %/42 %/75 % a
  67 %/83 %/100 %. Con `global` y `otsu` casi no ayuda. Con moteado «crudo» apenas llega a 33 %.
* Daño: en `ring_tight` (hueco de diámetro t) con imagen ideal, `global` pasa de 100 % a 8 % a
  t/h = 2 y `smoothed_otsu_s2` de 92 % a 0 % a t/h = 6 (el suavizado encoge el hueco por debajo
  del umbral y se rellena).

## 2. Diseño

* Formas: `disk`, `ellipse`, `annulus` (hueco 3 t) y **`ring_tight`** (nueva: ancho t, hueco de
  diámetro t; Betti (1,1)). Niveles t/h {2, 3, 4, 6, 8, 12, 20}; perfiles `ideal`, `us_compound`,
  `us_raw` (igual que H5). 100 réplicas por celda: 4 × 7 × 3 × 100 = 8 400 imágenes. Semilla base
  20261120.
* Segmentadores: los cuatro de H5 y sus cuatro versiones `_clean`. Cada versión limpia se evalúa en
  **la misma imagen** que su base (comparación pareada).
* Respuestas: `topology_ok` (Betti exactos con adyacencia (8,4)) y |error de área|.
* **Segmentadores primarios** (fijados ahora): `smoothed_otsu` y `smoothed_otsu_s2`. Motivo (mecanismo,
  confirmado en el piloto): con suavizado los fragmentos del moteado son manchas pequeñas que el
  umbral de tamaño puede quitar; con `global`/`otsu` los fragmentos son grandes y el umbral no
  los alcanza.

## 3. Hipótesis y criterios (fijos)

* **H7a — La limpieza ayuda.** Celdas: primarios × `us_compound` × {`disk`, `ellipse`, `annulus`} ×
  t/h ∈ {8, 12, 20} (18). Solo cuentan las celdas con margen: topología base < 0.90. En cada una,
  la limpieza «cierra» el margen si `topo_limpia − topo_base ≥ 0.5 · (1 − topo_base)` (criterio
  relativo al margen disponible: lección de ERRATA E12). *Apoyada* si cierra el margen en ≥ 75 % de
  las celdas con margen; *parcial* ≥ 50 %; *no apoyada* < 50 %; *no evaluable* si ninguna tiene margen.
* **H7b — No distorsiona el área.** En las mismas formas y segmentadores primarios, `us_compound` y
  t/h ∈ {6, 8, 12, 20}, el error mediano absoluto de área cambia en menos de 0.01 (un punto)
  al limpiar. *Apoyada* si se cumple en todas las celdas; *parcial* en todas menos una.
* **H7c — El daño es acotado.** En `ring_tight` × primarios × `us_compound` × t/h ∈ {6, 8, 12, 20}, la
  limpieza no reduce la topología correcta en más de 0.10 en ninguna celda. *Apoyada* si ninguna;
  *parcial* si una; *no apoyada* si más de una.

Un valor no calculable es «no evaluable», nunca «no apoyada».

**Extensión descriptiva (sin veredicto):** las tablas completas pareadas (imágenes arregladas
y estropeadas por la limpieza) para los 8 segmentadores, los tres perfiles, todas las formas y
t/h ≤ 4 en `ring_tight`; el perfil `us_raw`; el informe de qué se borra (`clean_report_2d`).

## 4. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| H7a apoyada (≥ 75 % de las celdas con margen) | 60 % |
| H7b apoyada (área estable en todas las celdas) | 75 % |
| H7c apoyada o parcial (a lo sumo una celda con daño > 10 puntos) | 25 % |
| `ring_tight` con imagen ideal y t/h = 2: `global_clean` queda por debajo de 20 % de topología correcta | 90 % |

## 5. Qué no se puede concluir

* Moteado sintético con un modelo sencillo; no son ecografías. Con moteado «crudo» (un solo look) la
  topología sigue sin recuperarse y no se propone nada para ello.
* El umbral (4 px, 0.5 %) son dos números míos, fijados con un piloto; no se optimizaron en este barrido.
* Una mejora en topología no es una mejora en un diagnóstico, y no hay uso clínico.
* Si H7c sale como espero, el mensaje es: la limpieza es una herramienta que hay que usar sabiendo
  el tamaño del rasgo mínimo real, no un arreglo universal.

## 6. Desviaciones

(Ninguna al momento de este commit.)

- 2026-11-09 (antes de correr `scripts/run_h7.py`; los criterios de §3 no se tocan):
  1. **El código del piloto no estaba versionado** y se perdió al reciclarse el contenedor de
     trabajo. `twod._clean_mask_2d` se escribió de nuevo siguiendo la regla de §1, con pruebas.
     Los números del piloto de §1 no se han vuelto a comprobar con el código nuevo.
  2. **Detalles que la regla no fijaba y se fijan ahora:** A es el área (en píxeles) del
     componente mayor de la máscara de entrada; «menores que» es estricto (un componente de
     exactamente el umbral se conserva); primero se quitan los componentes y después se rellenan
     los huecos de la máscara resultante.
  3. `ring_tight` se añade como `EXTRA_2D` sin mover los índices de semilla de las tres formas
     de H5 (una prueba lo comprueba).
