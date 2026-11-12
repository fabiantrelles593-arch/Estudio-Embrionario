# Preregistro — Piloto REAL2D: primera medida sobre una ecografía 2D real (n = 1, exploratorio)

> Se escribe **antes** de medir la imagen. Es un piloto de n = 1: **no confirma ni refuta nada**; solo muestra si la
> canalización funciona sobre una imagen real y cuánto discrepa de la medida impresa. Solo investigación y educación.

## 1. Origen y autorización (declarado, no verificado)

* La imagen es una ecografía 2D impresa de un embarazo temprano (fotografiada) que el usuario aportó el 11-11-2026.
  **El usuario declaró el 12-11-2026 que tiene el permiso legal** para usarla. **No se verificó ningún documento**;
  la declaración queda escrita aquí y en el informe (`--authorization-note`).
* Efecto práctico: se analiza. **Nada identificable** (nombres, fechas, clínica, la imagen, el recorte, la superposición)
  entra al repositorio ni a GitHub. Los informes se guardan fuera del repositorio. Los números derivados (una longitud, una
  diferencia) pueden citarse sin identificar a nadie.
* Para publicar, comparar con más casos o hacer cualquier afirmación sobre las personas se necesitan los documentos
  de `docs/RUTA_DE_VALIDACION_REAL.md` (consentimiento informado, anonimización completa, aprobación ética). No se hace ninguna
  afirmación clínica ni sobre la salud de nadie.

## 2. Qué se hace (fijo)

1. **Escala** desde la regla o las marcas impresas en la imagen (dos puntos y su longitud, o marcas igualmente espaciadas). Si no
   hay una escala legible, el piloto **se detiene** (sin escala no hay milímetros).
2. **ROI** que fija una persona al principio, con superposición revisable por el usuario (`superposicion.png`).
3. **Medida automática** con `geovida real2d` (segmentador `smoothed_otsu`, Feret, rejilla de desenfoque 0.25–2 mm,
   modelo congelado `results/summary/h14_frozen.json`). Sobre imagen real **el semáforo no sale verde** por diseño.
4. **Segunda lectura**: calibrador manual (dos puntos que marca una persona) sobre la misma imagen.
5. **Comparación descriptiva** con la medida impresa por el equipo u operador, si es legible: diferencia en mm y en %.
   No hay regla de éxito (n = 1).

## 3. Reglas contra autoengaño (fijas)

* **No se ajusta ningún umbral, ROI ni segmentador después de ver la medida para acercarla a la impresa.** Si el control
  de calidad falla (el objeto toca el borde de la ROI, contraste/ruido < 3, varios componentes grandes), se informa como **fallo del método**.
* Un cambio de ROI tras ver un resultado se anota como desviación (§6) con el motivo y los dos resultados.
* Se informan **todas** las filas de desenfoque, también las que quedan fuera de la caja (amarillas).
* Una discrepancia grande es un resultado, no un error que corregir: puede venir del objeto elegido, de la escala, de la compresión
  logarítmica del equipo o de la impresión (supuestos no verificados, `docs/REAL2D_METODO.md`).

## 4. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| La medida impresa es legible y sirve de referencia | 60 % |
| La escala se puede derivar de la regla o de las marcas de la imagen | 65 % |
| Con ROI válida, al menos una fila de desenfoque cae dentro de la caja calibrada | 85 % |
| La medida automática queda a ≤ 10 % de la impresa | 40 % |
| Alguna fila tiene, según la simulación, luz verde (antes del tope de imagen real) | 10 % |
| El control de calidad marca al menos un problema | 60 % |

## 5. Qué no se puede concluir

* Nada sobre exactitud, sesgo ni calibración del método en ecografía real: n = 1 y sin repetir operadores.
* Nada de la edad del embarazo ni de la salud de nadie: la edad por fórmula es informativa y el error de medida de esta imagen no está validado.
* Que coincida con la medida impresa no prueba el método; que no coincida tampoco lo refuta: pueden medir cosas distintas.

## 6. Desviaciones

(Ninguna al momento de escribir. La imagen no estaba disponible en la sesión al preparar este protocolo.)

## 7. Decisiones fijadas el 12-11-2026, DESPUÉS de ver la imagen y ANTES de correr la medida automática

La imagen llegó el 12-11-2026 (una hoja con tres capturas de pantalla fotografiadas; la capa de la medida de interés es la de la longitud cráneo-nalga, CRL).
Todo lo de abajo se fijó al mirar la imagen, **sin correr `geovida real2d`**. Los números están en píxeles de una copia **girada 90° en sentido antihorario sin remuestrear** (1233 × 873 px), que queda fuera del repositorio.

* **Qué se mide:** solo la captura de la CRL. Las otras dos (Doppler del latido, otra estructura) no se miden.
* **Escala, de las marcas de profundidad de la propia captura:** posiciones en y de las marcas igualmente espaciadas = 112, 138, 165, 192, 218, 246, 271, 298, 324, 351, 379, 403.
  Regla de exclusión fijada antes de usar la función: se descarta una marca que rompa la regularidad en más de 30 % del espaciado (se descartó una en y = 231, a media distancia, que es un marcador del equipo y no una marca de profundidad).
  **Supuesto que no se puede verificar desde la imagen: que el espaciado entre marcas pequeñas es 10 mm.** Apoyo indirecto: la profundidad de imagen indicada en los parámetros en pantalla es 11 cm y 11 marcas de 26–27 px llenan casi toda la altura del sector. No usé la medida impresa para elegirlo.
  Se usa la función `scale_from_ticks` (mediana de los espaciados, como dice §2). Como análisis de sensibilidad, sin cambiar la escala principal, se informa también la pendiente de un ajuste por mínimos cuadrados a las mismas marcas.
* **ROI** (una persona, mirando la imagen): x de 172 a 296, y de 175 a 241. Deja unos 8–13 px de margen alrededor del embrión. Incluye otras estructuras brillantes pequeñas (saco vitelino, un pliegue arriba); si la medida las toma, se informa como fallo del método, no se corrige la ROI.
* **Segunda lectura (calibrador manual)**, dos puntos puestos a ojo sobre la imagen ampliada: (186, 210) y (285, 204), extremos de la masa del embrión. **La puse sabiendo que la medida impresa era 37.4 mm**, así que **no es independiente**; además la hizo el asistente, no un ecografista.
* **La medida impresa de referencia** es la CRL que el equipo escribió en la captura (37.4 mm). No se sabe quién la midió ni cómo; es una referencia, no una verdad.
* **Qué NO se ajusta después:** ROI, escala, segmentador, rejilla de desenfoque, modelo congelado. Si algo falla (el objeto toca el borde, varios componentes grandes, contraste/ruido < 3), se informa como fallo del método.
* **Limitación que no estaba prevista en §2 y que cambia la lectura:** la captura está pintada con un mapa de color naranja (no es escala de grises) y fue fotografiada de una hoja impresa. H15 simuló una cadena de ese tipo **sin mapa de color**; el efecto del mapa de color no se ha probado en ningún sitio.
