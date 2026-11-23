# Preregistro — MT-A v2: efecto del atlas sobre la forma, con especímenes que pasan el control de calidad (19 nov 2026)

> Siguiente paso propuesto por `docs/morpho_trace/RESULTADOS_ATLAS_v1_1.md` §6 y `RESULTADOS_QC_LANDMARKS.md` §8. MT-A
> v1.0 y v1.1 quedaron **no evaluables** y esos veredictos no se tocan. Todo lo que este documento no cambia sigue como
> en `PREREGISTRO_ATLAS.md` (v1.0) y su v1.1: pregunta, registro, transferencia, espacio de forma, **δ(s)**, **f**,
> criterios de MT-A1–MT-A3, puertas G0-b′, G0-c, G1 y G2, sensibilidad y lo que no se puede concluir.
> Se sube a la rama **antes** de cualquier registro y de calcular la nueva **d**.
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta.
> Solo datos animales publicados (MusMorph/IMPC, FaceBase, CC BY 4.0). Nada humano ni clínico.

## 1. Qué cambia y por qué

1. **La muestra.** v1.1 falló porque 6 de los 20 especímenes E15.5 del piloto tenían landmarks publicados lejos del
   tejido. QC-LM midió la misma regla en 60 + 60 especímenes nuevos: cumplen **40 de 60 E15.5 y 60 de 60 E18.5** [HV].
   v2 toma **20 + 20 por semilla entre los que cumplen** (`scripts/mta_v2.py sample`, semilla **20261122**).
   Muestra ya extraída sin leer ninguna imagen: `results/morpho_trace/muestra_v2.json`, SHA-256 de
   `json.dumps(sample, sort_keys=True)`: `7ecc6e4bf8a590ef0d30909ce4192025c6175fb0e6bda587f70a7360dd245dd2` [HV].
2. **Independencia de d.** v1.0 exigía que los especímenes de MT-A fueran disjuntos de los que definen **d**. Los de
   QC-LM salen del confirmatorio de ONTO-MAP, así que en v2 **d se recalcula sin los 120 especímenes de QC-LM**:
   597 configuraciones publicadas (199 E15.5 y 398 E18.5) en lugar de 717 (`mta_v2.confirm_without`). Ni los 40 de
   la muestra ni los 80 restantes de QC-LM entran en **d**.
3. **Las puertas G0-a′ y G0-d se sustituyen** (§3). G0-b′, G0-c, G1 y G2 siguen como estaban.

## 2. Lo que ya se ha visto (declarado)

* De los 40 especímenes de la muestra se conoce solo la distancia de sus landmarks al tejido (QC-LM): todos cumplen, por
  construcción. Ninguno se ha registrado a ningún atlas.
* Las imágenes ya están en disco con el MD5 del catálogo (`data/manifests/musmorph_qc_images.csv`); **no hace falta
  descargar nada**.
* QC-LM calculó |d| con los 120 especímenes de su muestra (0,157) [HV]; la **d** de 597 no se ha calculado.

## 3. Puertas (sustituyen a G0-a′ y G0-d)

| Puerta | Qué se comprueba | Criterio |
|---|---|---|
| **G0-a″** Geometría de la muestra | Los 40 especímenes cumplen la regla de QC-LM (≥ 95 % de landmarks a ≤ 0,23 mm) | Todos (ya medido en QC-LM; se vuelve a comprobar desde los archivos de medida) |
| **G0-d′** Reproducción de d sin QC-LM | GPA solo de las 597 configuraciones; longitud de **d** | Entre 0,150 y 0,164 (la banda de v1.0). Si no, se para y se busca la causa antes de registrar |
| **G0-t** Tiempo | Un registro de prueba **atlas E18.5 → atlas E15.5** (la sensibilidad 3 de v1.0, sin especímenes) mide cuánto tarda un registro en este equipo | Si 80 registros llevan más de 72 h, se para y se documenta; no se cambia el procedimiento para que quepa |

## 4. Espacio de forma (cambia solo quién define la media y d)

Un único GPA con las **597** configuraciones publicadas y las **80** transferidas (40 especímenes × 2 atlas); media y
**d** = media E18.5 − media E15.5 de las 597. Para G1, la variación entre especímenes del mismo estadio se mide con los
landmarks publicados de los 40 de la muestra (en v1.0 eran los del piloto).

## 5. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| Pasa G0-d′ | 90 % |
| Pasa G0-t | 70 % |
| Pasa G1, dado que pasan las G0 | 70 % |
| MT-A1 apoyada, dado que es evaluable | 35 % |
| MT-A1 refutada, dado que es evaluable | 30 % |
| MT-A2: ángulo < 45° | 60 % |

## 6. Qué significará cada resultado (antes de verlo)

| Resultado | Conclusión | Siguiente paso |
|---|---|---|
| MT-A1 apoyada (f ≥ 0,50 con su IC) | Al menos la mitad de la separación E15.5–E18.5 de ONTO-MAP la reproduce el cambio de atlas: **d** mezcla biología con atlas | Rehacer ONTO-MAP con todos los especímenes registrados a un mismo atlas |
| MT-A1 refutada (f ≤ 0,25) | El atlas explica poco de **d** | **d** de ONTO-MAP queda reforzada frente a este factor y frente al error de landmarks (QC-LM) |
| No concluyente | El efecto existe pero no se puede acotar con 40 especímenes | Ampliar con los 20 E15.5 y 40 E18.5 restantes que cumplen, mismo protocolo |
| No evaluable | Falla una puerta | Documentar la causa; no se reintenta con otra muestra elegida después |

## 7. Qué no se puede concluir

* Lo mismo que en v1.0 §9: un procedimiento de registro, un par de atlas, imágenes ya remuestreadas al espacio de su
  atlas (G1 más fácil), nada sobre humanos ni uso clínico.
* La muestra sale de especímenes con landmarks cerca del tejido: f vale para ellos, no para los que no cumplen.

## 8. Ejecución

1. `scripts/mta_v2.py` (muestra; `tests/test_mta_v2.py`), subido con este preregistro.
2. Antes de registrar: adaptar `scripts/atlas_effect_gates.py` para leer la muestra de v2 y calcular **d** sin QC-LM,
   con pruebas, y subirlo. Luego G0-a″, G0-d′ y G0-t.
3. Los 80 registros (reanudables, a baja prioridad, cuando P3 y H19 dejen memoria), `analyze` y la sensibilidad.
4. Resultados en `docs/morpho_trace/RESULTADOS_ATLAS_v2.md`, transcribiendo los veredictos sin reinterpretar.

## 9. Desviaciones

(Ninguna al subir este preregistro.)

* **20 nov 2026 — código y primeras puertas, sin desviaciones.** El paso 2 de §8 se hizo como estaba escrito:
  `mta_v2.py selection` escribe `results/morpho_trace/v2/seleccion_v2.json` con la forma de la selección de ONTO-MAP
  (muestra de v2 y confirmatorio sin QC-LM: 199 + 398), y `atlas_effect_gates.py analyze --protocol 2.0` lee las
  puertas de v2 (pruebas en `tests/test_mta_v2.py`), subido antes de medir. **G0-a″ superada** (los 40 cumplen) y
  **G0-d′ superada**: |d| = 0,15678 con las 597 configuraciones (0,15671 con las 717) [HV,
  `results/morpho_trace/v2/g0a3.json`, `g0d2.json`]. G0-t y los registros esperan a que P3 y H19 dejen memoria.
* **21 nov 2026 — G0-t superada, sin desviaciones.** Con P3 y H22 terminados, el registro de prueba atlas E18.5 →
  atlas E15.5 tardó 1323 s; 80 registros ≈ 29,4 h (límite 72 h) [HV, `results/morpho_trace/v2/g0t.json`]. Código
  igual a la rama (`mta_v2.py` 401f7d1, `atlas_effect_gates.py` fb4a869, `atlas_effect.py` 9369540). Los 80 registros
  empezaron el mismo día, a prioridad baja.
* **23 nov 2026 — registros terminados y estudio cerrado, sin desviaciones.** El proceso se detuvo el 22 nov con 34
  de 80 registros guardados, porque terminó la sesión que lo lanzó. Se relanzó la misma orden, reanudable, con el
  código comprobado contra los blobs de G0-t. 80 de 80 válidos, 22,9 h de cálculo. Veredicto: **no evaluable**,
  porque falla G1. Detalles en `docs/morpho_trace/RESULTADOS_ATLAS_v2.md`.
