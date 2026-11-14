# Laboratorio Geovida (página interactiva)

Página de un solo archivo que voxeliza formas de verdad conocida en el navegador, las mide y
muestra la luz del semáforo de volumen (H6), una serie de crecimiento 4D y el eje de escala.

* `core.js`: núcleo numérico sin DOM (fantomas, volumen parcial, transformada de distancia exacta,
  números de Betti con adyacencia (26, 6), semáforo congelado de H6).
* `ui.js` y `page_head.html`: interfaz. La página publicada es `page_head.html` + los dos scripts.
* `check.js`: contraste con el paquete de Python. Con `fixtures.json` (seis máscaras exportadas
  desde geovida), el volumen, los números de Betti, la profundidad media (a 1e-6), la
  probabilidad y la luz coinciden en las seis.

Montaje: `cat page_head.html > lab.html; printf '<script>\n' >> lab.html; cat core.js >> lab.html;
printf '</script>\n<script>\n' >> lab.html; cat ui.js >> lab.html; printf '</script>\n' >> lab.html`

La simulación de la página es la más simple (volumen parcial, sin desenfoque ni ruido, umbral
0.5). Solo datos sintéticos; sin uso clínico.
