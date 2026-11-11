# Ficha del modelo: el certificado de `geovida`

> Ficha de un modelo de investigación, no de un producto sanitario. Resume qué es, con qué se calibró,
> cómo rindió y dónde falla, con cifras tomadas de `docs/RESULTADOS_V04.md` (v0.4). Los resultados de
> la recalibración para ecografía simulada (H12) se añaden en su propio documento de resultados cuando
> existan. **Sin uso clínico.**

## 1. Qué es

* **Nombre:** certificado vectorial de `geovida` (volumen, topología y dominio).
* **Entrada:** una imagen 3D, el tamaño del vóxel, el segmentador (`global`, `otsu`, `smoothed_otsu`) y
  el perfil de imagen que declara quien la usa.
* **Salida:** para el volumen y para el triple de Betti, una probabilidad de que la medida sea fiable
  (error de volumen ≤ 5 %; triple de Betti correcto) y una luz (verde p ≥ 0.90, amarilla, roja
  p < 0.50); si la imagen cae fuera de la envolvente de calibración, la luz verde se degrada a amarilla.
* **Tipo de modelo:** regresión logística (con ridge para la topología) sobre variables medidas en la
  propia imagen, más una guardia de dominio por envolvente de dos índices (`snr_hat`, `edge_width`).
* **Versión:** `geovida.__version__` y el informe de cada certificado (`geovida certify --report`).

## 2. Datos de calibración

* **Todo sintético.** Doce fantomas con verdad analítica (diez en la calibración, dos reservados para
  probar formas nunca vistas), observados con un simulador de adquisición (orientación aleatoria,
  volumen parcial, PSF gaussiana, ruido gaussiano, anisotropía).
* v0.4: rejilla de 7 niveles de resolución × 3 anisotropías × 2 perfiles, 15 réplicas por celda, semilla
  20261123. v0.5 (H12): ecografía 3D simulada (moteado, atenuación); ver `PREREGISTRO_H12.md`.
* **Ninguna imagen real, ninguna imagen de personas.**

## 3. Cómo rindió (v0.4, imágenes sintéticas, semillas nuevas)

| Evaluación | Resultado |
|---|---|
| Verde falso de topología en dominio (6 estratos) | ≤ 7.0 % (máximo en `global · realistic`); IC 95 % superior 8.3 % |
| Calibración (ECE) | ≤ 0.10 en 6 de 6 estratos |
| Discriminación (AUC) | ≥ 0.85 en 4 de 6; los otros dos, 0.817 |
| Formas nunca vistas (mancuerna, copa) | verde falso ≤ 7.8 % (punto); IC superior llega a 11.1 % en `global · realistic` |
| Dominio desplazado, con guardia (volumen) | 10 de 12 estratos sin verdes suficientes; los 2 que conservan ≤ 4.1 % |
| Coste de la guardia en dominio | conserva 95.2 %–99.5 % de las luces verdes |

## 4. Dónde falla (lo que hay que leer antes de confiar en una luz verde)

* **Fallo silencioso de topología:** 6.6 % de las medidas con topología incorrecta recibió luz verde;
  se concentra en `shell_tight` y `torus_tight` (rasgos que la imagen ya perdió). Ningún margen puede
  verlos.
* **La guardia deja pasar algo:** `otsu · desenfoque ×2` dejó pasar 28 luces verdes de volumen y 6 eran
  falsas (21.4 %).
* **La guardia cubre el volumen, no la topología:** con `global` y desenfoque, el 10.4 % y el 12.1 % de
  las luces verdes de topología fueron falsas incluso con guardia.
* **Mancuerna:** es la forma más débil entre las no vistas (post hoc: 11.4 % de verde falso en
  `global · realistic`).
* **Solo vale para este simulador:** una luz verde es una estimación calibrada con imágenes simuladas,
  no una validación con datos reales (H11 espera datos).

## 5. Uso y limitaciones

* **Uso previsto:** investigación y educación; ver `USO_PREVISTO_Y_RIESGOS.md`.
* **Fuera de alcance:** diagnóstico, decisiones sobre una persona, imágenes de equipos o modalidades
  que la calibración no cubre, rasgos más finos que el vóxel.
* **Equidad y subgrupos:** no aplica a personas (no hay datos humanos). Los estratos por segmentador,
  perfil y forma son los únicos subgrupos evaluados.
* **Mantenimiento:** los modelos están congelados; cualquier cambio implica una versión nueva con su
  preregistro (`CICLO_DE_VIDA.md`).
* **Contacto y propiedad:** proyecto de código abierto de Fabián Trelles (licencia MIT).
