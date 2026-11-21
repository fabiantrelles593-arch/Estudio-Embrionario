# Exposición interactiva de geovida

**Presentación final (17 nov 2026):** `geovida-presentacion-final.html`, 27 láminas con el orden
problema → importancia → objetivos → método → evidencia real → modelos 2D–5D → topología → morfometría →
semáforo → MORPHO-TRACE → pruebas → arquitectura → futuro → conclusiones. Incluye un modelo 3D real
interactivo y medidas reales de un embrión E11 (Qiu 2021). Fuente en `final/deck.html` y
`final/build.py`; figuras y datos con `scripts/figure_final.py` (valores en `img/final_data.json`).
Cómo abrirla, cambios y funcionalidades: `README_FINAL.md`. Guion: `GUION_FINAL.md`.

**Presentación anterior (v2, 16 nov 2026):** `geovida-presentacion.html`, 17 láminas con
propósito, cifras de anomalías congénitas (OMS, CDC-MINSA), atlas de especímenes reales de ratón,
resultados con datos reales y ruta clínica. Fuente en `v2/deck.html`; se ensambla con
`python docs/exposicion/v2/build.py` a partir de las figuras de `scripts/figure_atlas.py` (figuras y
HTML ensamblado se generan en local con los datos reales; no están en git). Guion y
fuentes de cada cifra: `GUION_V2.md`. El mazo de abajo queda como laboratorio interactivo.

Un mazo de 20 láminas (la 13, «Datos reales», resume P3, ONTO-MAP y H11 al 16 nov 2026) que se maneja con el teclado (←/→; **G** muestra el guion del expositor) y
que incluye cinco demostraciones en vivo, una prueba de «¿funciona?» con 200 objetos al azar, un
cuestionario de aprendizaje y las preguntas probables del jurado, con respuesta.

* `exposicion-geovida.html` — archivo único, funciona sin internet (three.js incrustado).
* Fuentes: `head.html` (estilos), `extra.css`, `body.html` (láminas), `deck.js` (mazo, laboratorio,
  prueba en vivo, cuestionario), `trial.js` (diseño y medida de la prueba, sin DOM), `core.js`
  (núcleo numérico, idéntico al de `docs/laboratorio/`). `sh build.sh offline` reconstruye el
  archivo único (necesita `three.min.js` en `node_modules/three/build/`).
* `h9data.js` — resultados de la confirmación de H9/H10 (cifras de `results/summary/h9_verdicts.json`):
  rellena las dos últimas filas de la tabla de resultados.
* `check_trial.js` — comprueba en Node que la prueba en vivo da menos de 10 % de luces verdes
  falsas (`node docs/exposicion/check_trial.js`).

## Qué demuestra y qué no

La prueba en vivo usa imágenes **ideales** (sin ruido) y el umbral fijo: es la configuración
«global · ideal» de H6, en la que el experimento completo dio 2.3 % de verdes falsas. En el
navegador, cuatro corridas de 200 objetos dieron 2.2–3.8 %. Con unas 80 luces verdes por corrida,
el porcentaje cambia de una corrida a otra. No representa los otros segmentadores ni el ruido.

Las demostraciones 3 y 5 (mancuerna y anillo estrecho) y la 4 (crecimiento) usan los fantomas y
semillas indicados en el atributo `data-demo` de cada lámina; los números citados en el guion de
cada una salen de 24 orientaciones sondeadas antes de escribirlos (ver ERRATA E22).
