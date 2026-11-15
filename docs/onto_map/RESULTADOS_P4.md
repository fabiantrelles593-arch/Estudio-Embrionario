# ONTO-MAP, P4 — Resultados (15 nov 2026)

> Análisis fijado en `docs/onto_map/PROTOCOLO_ONTOMAP.md` (commit `d5d8c7b`) y en el código `src/geovida/onto_map.py` (commit `02f0346`) **antes** de descargar el confirmatorio.
> Solo investigación; datos animales publicados (MusMorph IMPC, FaceBase 3-JZA6, CC BY 4.0); nada humano ni clínico.
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PV] pendiente de validación.

## 1. Flujo

| Paso | Resultado |
|---|---|
| Selección (`scripts/onto_map_pilot.py select`, semilla 20261116) | Elegibles con landmarks: 279 en E15.5 y 478 en E18.5. Piloto: 20 + 20. Confirmatorio: 259 + 458 [HV] |
| Descarga | 40 (piloto) y 717 (confirmatorio) archivos `.tag`, todos con el MD5 del catálogo [HV] |
| Manifiesto | `results/onto_map/manifiesto_piloto.csv` y `manifiesto_confirm.csv` (fuera de git); `verify`: 40 y 717 correctos, 0 con diferencias [HV] |
| Comprobaciones previas, piloto | Las 4 pasan: todos con 540 puntos; GPA convergida; ρ máxima a la media 0,113 (< 0,3); correspondencia en el 100 % [HV] |
| Comprobaciones previas, confirmatorio | Las 4 pasan; ρ máxima a la media 0,157 [HV] |

## 2. Hipótesis (confirmatorio, n = 259 en E15.5 y 458 en E18.5; 2000 réplicas válidas)

| Hipótesis | Ángulo | IC 95 % | Veredicto según §5 |
|---|---|---|---|
| H-O1: θ(a15, d) < 45° | 84,5° | 79,3°–89,5° | **Contraria** [HV] |
| H-O2: θ(a18, d) < 45° | 77,2° | 67,6°–91,8° | **Contraria** [HV] |
| H-O3: θ(a15, a18) < 45° | 84,8° | 69,6°–101,8° | **Contraria** [HV] |

Referencia nula: hacen falta 11 componentes para el 95 % de la varianza de forma, y en 11 dimensiones el 1 % de las rectas al azar forman menos de 45,5° entre sí. Los ángulos observados son los que se esperan entre direcciones no relacionadas.

## 3. Descriptivo y exploratorio (sin criterio)

- Tamaño de centroide medio: 72,4 mm en E15.5 y 89,5 mm en E18.5 [HV].
- La alometría estática explica el **13 %** de la varianza de forma en E15.5 y el **1 %** en E18.5 [HV]. La desviación típica de log CS es 0,070 y 0,038.
- Sobre la dirección **d**, los estadios están separados por unas **18 desviaciones típicas** de la variación dentro del estadio: longitud de **d** = 0,157, frente a una desviación típica sobre **d** de 0,0087 en E15.5 y 0,0082 en E18.5 [HV].
- Dentro de E15.5, la posición sobre **d** apenas se correlaciona con log CS (r = 0,18) [HV].
- Por sexo, θ(a15, d) vale 88,6° en hembras y 79,7° en machos: el resultado no depende del sexo [HV].

## 4. Interpretación

- **[HV] Resultado negativo.** Con estos datos, la variación de forma asociada al tamaño dentro de un estadio **no** apunta en la dirección del cambio de forma entre E15.5 y E18.5, y la alometría estática **no** se conserva entre los dos estadios. La posición de un espécimen sobre **d** no sirve como «reloj morfológico» dentro del estadio: los especímenes de E15.5 casi no se reparten a lo largo de **d**.
- **[HIP] Dos explicaciones que estos datos no pueden separar:**
  1. *Biológica:* el cambio de forma entre E15.5 y E18.5 (unos 3 días) ocurre en direcciones que la variación de madurez dentro de un estadio no explora.
  2. *Técnica:* cada estadio tiene su propio atlas (factor de confusión (i) del protocolo). Una diferencia sistemática entre atlas desplazaría a todos los especímenes por igual, y produciría exactamente lo observado: una separación grande sobre **d** con una dispersión mínima a lo largo de ella.

  El factor de confusión declarado de antemano es compatible con el resultado, así que **no** se atribuye **d** al desarrollo.
- **Implicación para ONTO-MAP.** La hipótesis original de «trayectorias reproducibles» no puede evaluarse con landmarks de atlas distintos por estadio sin estimar antes la contribución del atlas. Eso es justo la pregunta de MORPHO-TRACE (§5 del mandato): cuánto de una diferencia se debe al procesamiento. Siguiente paso propuesto [PROP]: medir la diferencia entre atlas con especímenes registrados a **los dos** atlas. Esto requiere las imágenes y el registro, que MusMorph no publica como landmarks [PV].

## 5. Qué no se puede concluir

- Nada sobre la ontogenia continua: son dos estadios transversales, y **d** es un segmento.
- Los landmarks se obtuvieron por registro automático y no se han comparado con una anotación experta [PV].
- Nada sobre otros órganos, especies, humanos ni aplicaciones clínicas.
