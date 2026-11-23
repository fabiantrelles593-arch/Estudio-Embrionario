# Preregistro — MT-A v3: efecto del atlas sobre la forma, con registro limitado a la cabeza (23 nov 2026)

> **Aprobado por el autor el 23 nov 2026, tal como estaba escrito el borrador** (decisiones del §0: las propuestas).
> Se sube a la rama con su código (`scripts/mta_v3.py`, funciones nuevas de `src/geovida/atlas_effect.py`) y sus
> pruebas (`tests/test_mta_v3.py`) **antes** de extraer la muestra y de cualquier registro de un espécimen.
>
> Antecedentes: MT-A v1.0, v1.1 y v2, los tres **no evaluables**; esos veredictos no se tocan. La verificación de
> ingeniería `VERIFICACION_REGISTRO.md` (23 nov) no encontró defectos de código y atribuye el fallo de G1 de v2 al
> objetivo del registro (cuerpo entero) [HIP].
> Todo lo que este documento no cambia sigue como en `PREREGISTRO_ATLAS.md` (v1.0) y su v2: pregunta, espacio de
> forma, **d** (de las 597 configuraciones, ya medida en G0-d′ de v2), **δ(s)**, **f**, criterios de MT-A1–MT-A3,
> G0-c, incertidumbre y lo que no se puede concluir.
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta · [PV] pendiente.
> Solo datos animales publicados (MusMorph/IMPC, FaceBase, CC BY 4.0, Devine et al. 2022, *Sci Data* 9:230,
> doi:10.1038/s41597-022-01338-x). Nada humano ni clínico. No hace falta descargar nada.

## 0. Decisiones del autor (23 nov 2026: se aceptan las cuatro propuestas)

| # | Decisión | Propuesta aceptada | Alternativa descartada |
|---|---|---|---|
| D1 | ¿Se hace MT-A v3? | Sí, con las puertas baratas de §4, que paran el estudio tras 12 registros si el registro no sirve | Cerrar MT-A y pasar directamente a la pregunta alternativa de §10 |
| D2 | Registrador | SimpleITK (ya instalado, Apache 2.0) con máscara de cabeza | ANTs (el de MusMorph; licencia y versión sin verificar [PV]): exige comprobarlas e instalarlo antes; más fiel a cómo se hicieron los landmarks publicados |
| D3 | Muestra | Los 60 especímenes de QC-LM que cumplen y no entraron en v2 (§2) | Reutilizar los 40 de v2: más comparables, pero ya vistos en G1 y en el diagnóstico |
| D4 | Candidatos de registro | Tres, fijados aquí (§3.3); se elige uno en el piloto con una regla escrita | Uno solo (C1, afín de cabeza): más simple, pero sin margen si la afín no basta |

## 1. Qué cambia y por qué

1. **El registro mira solo la cabeza.** En v2 la información mutua del cuerpo entero arrastró la cabeza: la
   inicialización por momentos ya alejaba los landmarks (0,57 → 1,05 mm y 0,30 → 0,68 mm) y la B-spline lo agravó
   en E18.5 [HV, `VERIFICACION_REGISTRO.md` §4–5]. En v3 la métrica se evalúa solo dentro de una caja de cabeza
   derivada de los landmarks **del atlas** (nunca de los del espécimen), y las imágenes se recortan a esa caja.
2. **No hay inicialización por momentos.** Se inicializa con una afín calculada solo entre los landmarks de los dos
   atlas (§3.2): para el registro propio es exactamente la identidad.
3. **La identidad es una referencia obligatoria.** G1 exige además que el registro supere a los landmarks del atlas
   sin mover (§4). En v2 la identidad habría quedado por debajo de la variación entre especímenes en los dos
   estadios (ρ 0,047 y 0,031 frente a 0,068 y 0,042) [HV, `RESULTADOS_ATLAS_v2.md` §5].
4. **G1 primero, en un piloto pequeño, antes de cualquier registro cruzado** (lección de v2, §8).
5. **Muestra nueva** (§2), disjunta de v2, de la verificación y de **d**.

**Procedencia de estas decisiones (declarada).** Los cambios 1–3 salen de la verificación sobre dos especímenes de
v2 (`IMPC_E15.5_0313`, `IMPC_E18.5_1284`) y del diagnóstico exploratorio de v2. Ninguno de los especímenes de v3 se
ha registrado ni mirado con ningún procedimiento. Elegir el diseño con datos de v2 y evaluarlo con especímenes
nuevos es legítimo; evaluarlo sobre los de v2 no lo sería.

## 2. Muestra (fija, sin leer ninguna imagen nueva)

QC-LM midió 60 + 60 especímenes; cumplen 40 E15.5 y 60 E18.5. v2 usó 20 + 20. Quedan **20 E15.5 y 40 E18.5 que
cumplen y no se han registrado nunca**, todos con imagen en disco con el MD5 del catálogo
(`data/manifests/musmorph_qc_images.csv`) [HV, comprobado el 23 nov sin abrir las imágenes].

Con una semilla nueva, **20261123**, y antes de leer ninguna imagen:

* **Piloto (P):** 2 E15.5 y 2 E18.5, para elegir el procedimiento (§4, puerta S).
* **Confirmatorio (C):** los 18 E15.5 restantes y 18 E18.5 elegidos al azar entre los 38 restantes.

La muestra se guarda en `results/morpho_trace/v3/muestra_v3.json` con su SHA-256, como en v2. Los 60 ya están
excluidos de **d**, que se calcula con las 597 configuraciones sin QC-LM (|d| = 0,15678, G0-d′ de v2) [HV]; ningún
espécimen de v3 entra en **d**.

**Lo que ya se ha visto de estos 60:** solo la distancia de sus landmarks publicados al tejido (QC-LM). Sus
landmarks publicados entraron en el cálculo de |d| de QC-LM (0,157), no en la **d** de 597.

## 3. Protocolo de registro (fijo)

### 3.1. Caja de cabeza

Para cada atlas, la caja alineada con los ejes que contiene sus 540 landmarks, **ampliada 1,0 mm** por cada lado
(máscara de la métrica) y **2,0 mm** (recorte de las imágenes, para dar soporte a la B-spline). Con los landmarks
de los atlas, la caja ampliada 1 mm mide unos 7,7 × 10,0 × 8,5 mm en E15.5 y 9,1 × 12,4 × 6,6 mm en E18.5 [HV,
`.tag` de los atlas]. Cada imagen de espécimen se recorta con la caja del atlas de **su** estadio, porque MusMorph
la distribuye en la rejilla de ese atlas [HV, v1.0 §11].

### 3.2. Inicialización

T₀ = afín de mínimos cuadrados que lleva los 540 landmarks del atlas fijo a los del atlas del estadio del
espécimen (correspondencia comprobada en G0-c). Registro propio: T₀ = identidad. Registro cruzado: T₀ solo depende
de los dos atlas, no del espécimen.

### 3.3. Candidatos (todos con SimpleITK 2.5.7, ×4 como en v2)

Común: información mutua de Mattes (50 contenedores) **solo dentro de la máscara de la imagen fija**, muestreo
**regular** del 20 % (semilla 20261123), afín de 12 grados de libertad desde T₀, descenso de gradiente regular,
3 niveles (4, 2, 1; suavizado 2, 1, 0 vóxeles). Transferencia como en v1.0 §3 paso 5, con el orden de composición
comprobado en la verificación.

| Candidato | Después de la afín |
|---|---|
| **C1** | Nada (solo afín de cabeza) |
| **C2** | B-spline con malla 4³ sobre la caja recortada, LBFGS-B, 50 iteraciones, 2 niveles |
| **C3** | B-spline con malla 8³ sobre la caja recortada, LBFGS-B, 50 iteraciones, 2 niveles |

Orden de simplicidad: C1 < C2 < C3. C2 y C3 parten de la afín de C1 del mismo par.

## 4. Puertas (en este orden; si una falla, el estudio se para y es no evaluable)

| Puerta | Qué se comprueba | Criterio |
|---|---|---|
| **G0-a‴** Muestra | Los 40 de P + C cumplen la regla de QC-LM | Todos (se relee desde las medidas de QC-LM) |
| **G0-m** Caja | La caja de cada atlas contiene sus 540 landmarks y queda dentro de la imagen | Ambas cosas, en los dos atlas |
| **S** Selección en el piloto | Los 4 de P, **solo registro propio**, con C1, C2 y C3 (12 registros). Para cada uno: ρ(transferido, publicado) y ρ(identidad, publicado) | Un candidato es **apto** si mejora la identidad en ≥ 3 de 4 especímenes **y** su mediana de ρ es menor que la de la identidad. Se elige el apto con menor mediana de ρ; en empate a 0,001, el más simple. **Si ninguno es apto, el estudio se para aquí** |
| **G0-t′** Tiempo | Un registro atlas E18.5 → atlas E15.5 con el candidato elegido | 72 registros en ≤ 72 h. Si no, se para; no se cambia el procedimiento para que quepa |
| **G1′** Calidad del registro propio | Los 36 de C, **solo registro propio** (36 registros), con el candidato elegido | Mediana de ρ(transferido, publicado) menor que **las dos**: la mediana de ρ(identidad, publicado) y la mediana de ρ entre especímenes del mismo estadio (publicados de C; pares dentro de cada estadio, juntos, como `gate_g1`). **Si falla, no se hacen los registros cruzados** |
| **G2** Registros válidos | Terminan sin error y con métrica finita, propio y cruzado | ≥ 15 de 18 por estadio |

G0-c sigue superada (v1.0). Solo si pasan S, G0-t′ y G1′ se hacen los 36 registros cruzados y se calculan MT-A1–MT-A3.

## 5. Hipótesis y criterios

Sin cambios respecto de v1.0 §5: **f = ⟨δ̄, d̂⟩ / |d|**, MT-A1 apoyada si el límite inferior del IC 95 % de f es
≥ 0,50, refutada si el superior es ≤ 0,25; MT-A2 ángulo < 45°; MT-A3 descriptiva. Remuestreo por espécimen,
2000 réplicas, semilla 20261123. Un valor no calculable es «no evaluable», nunca «refutada».

## 6. Sensibilidad (declarada; no cambia el veredicto)

1. Registro directo atlas E18.5 → atlas E15.5 con el candidato elegido (es el de G0-t′) y transferencia de sus
   landmarks: desplazamiento entre atlas sin especímenes, comparado con δ̄.
2. δ(s) con C1 si el elegido es C2 o C3 (requiere 72 registros afines más, solo si G0-t′ deja tiempo).

## 7. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| Algún candidato es apto en S | 40 % |
| El elegido es C1, dado que hay alguno apto | 50 % |
| Pasa G0-t′ | 90 % |
| Pasa G1′, dado que pasa S | 60 % |
| MT-A1 apoyada, dado que es evaluable | 35 % |
| MT-A1 refutada, dado que es evaluable | 30 % |
| MT-A2: ángulo < 45° | 60 % |

La probabilidad baja de S es deliberada: los landmarks del atlas sin mover ya están más cerca de cada espécimen
que los especímenes entre sí, y superarlos exige que el registro capte la forma propia de cada uno [HIP].

## 8. Qué significará cada resultado (antes de verlo)

| Resultado | Conclusión | Siguiente paso |
|---|---|---|
| Ningún candidato apto en S | Con SimpleITK y estas variantes, el registro no añade información de cada espécimen a los landmarks del atlas | No repetir con más variantes sobre los mismos datos; decidir entre ANTs con un preregistro nuevo (D2) y la pregunta alternativa (§10) |
| Falla G1′ | El candidato elegido en 4 especímenes no se sostiene en 36 | Igual que la fila anterior |
| MT-A1 apoyada | Al menos la mitad de **d** la reproduce el cambio de atlas | Rehacer ONTO-MAP con todos los especímenes registrados a un atlas común |
| MT-A1 refutada | El atlas explica poco de **d** | **d** queda reforzada frente a este factor |
| No concluyente | Efecto no acotado con 36 especímenes | Ampliar con los 20 E18.5 sobrantes; los E15.5 que cumplen se agotan |
| Falla otra puerta | Documentar la causa | No se reintenta con otra muestra elegida después |

## 9. Qué no se puede concluir

* Lo mismo que v1.0 §9 y v2 §7.
* Un registro limitado a la cabeza mide el efecto del atlas **en la cabeza**, que es donde están los landmarks; no
  dice nada del resto del cuerpo.
* S se decide con 4 especímenes: elige entre tres candidatos, no estima su tasa de éxito.

## 10. Pregunta alternativa, si MT-A no puede evaluarse [PROP, no forma parte de este preregistro]

Según v1.0 §9, los landmarks publicados de MusMorph salen de un registro automático no lineal (ANTs) de cada
espécimen a su atlas [EI; sin comprobar en la publicación el detalle del procedimiento]. Si es así, el efecto del atlas se podría acotar sin registrar nada,
comparando la configuración de cada atlas con la media publicada de su estadio. Habría que comprobar primero en la
publicación cómo se generaron exactamente los landmarks, y escribir un preregistro propio.

## 11. Ejecución

1. Código antes de medir: `scripts/mta_v3.py` (muestra, caja, T₀, candidatos, puerta S, G1′) y funciones nuevas en
   `src/geovida/atlas_effect.py` (`register_head`, con máscara, transformada inicial, muestreo regular e iteraciones;
   `head_box`, `box_mask`, `crop_to_box`, `landmark_affine`, `gate_g1_identity`). `register` **no cambia**, para que
   v2 siga siendo reproducible. Pruebas con fantomas: la máscara excluye
   lo de fuera de la caja; T₀ es la identidad con el mismo atlas; la regla de S elige bien en casos construidos; el
   comportamiento por defecto de `register` no cambia.
2. Subir preregistro, código y pruebas con CI verde. Luego `sample`, G0-a‴, G0-m, S (12 registros), G0-t′, G1′
   (36), los cruzados (36) y `analyze`.
3. Resultados en `docs/morpho_trace/RESULTADOS_ATLAS_v3.md`, transcribiendo los veredictos sin reinterpretar.

## 12. Desviaciones

(Ninguna al subir este preregistro.)

### Notas previas a la subida (no cambian ningún criterio)

* **23 nov 2026 — prueba mecánica solo con los atlas.** Antes de subir, se comprobó que el código corre de principio
  a fin con los dos atlas y ningún espécimen (atlas E18.5 → sí mismo, atlas E15.5 → sí mismo y atlas E18.5 → atlas
  E15.5, con C1, C2 y C3). Solo se miró si terminaba y cuánto tardaba; no se calculó ni se miró ninguna distancia a
  landmarks. El resultado de la sensibilidad 1 se calculará en G0-t′, como está escrito.

### Notas de ejecución (no cambian ningún criterio)

* **23 nov 2026 — preregistro, código y pruebas en la rama** (preregistro en 96fc788; cabeza 77b9230 con CI en verde
  en Python 3.12 y 3.13). Después: `sample` (SHA-256 de la muestra
  `f5d63f0306cb27f083c09beef4b4261c82de22ab927ef4f1748dc3fa411a73e0`), **G0-a‴ superada** (40 de 40 cumplen) y
  **G0-m superada** (las dos cajas contienen sus landmarks y caben en su imagen) [HV,
  `results/morpho_trace/v3/muestra_v3.json`, `g0a4.json`, `g0m.json`]. La puerta S empezó el mismo día.
* **23 nov 2026 — comprobación en la publicación de la premisa de §10** (lectura, sin datos). Devine et al. 2022
  (doi:10.1038/s41597-022-01338-x), sección «Image registration and label propagation»: cada imagen se registró por
  pares al atlas de su estadio con una afín multirresolución y después SyN geodésico (correlación cruzada), y los
  landmarks del atlas se llevaron a cada espécimen con la transformada compuesta invertida [HV]. Los landmarks
  publicados de los embriones son, por tanto, landmarks del atlas deformados por ese registro. La premisa de §10
  queda verificada; §10 sigue fuera de este preregistro.
* **23 nov 2026 — puerta S fallida; estudio cerrado como no evaluable, sin desviaciones.** Los 12 registros del
  piloto terminaron bien; ningún candidato fue apto (C1 mejora la identidad en 2 de 4, mediana de ρ 0,0415 frente a
  0,0343; C2 y C3, en 0 de 4) [HV, `results/morpho_trace/v3/s.json`]. Como fija §4, no se hicieron G0-t′, G1′ ni los
  registros confirmatorios. Detalles en `docs/morpho_trace/RESULTADOS_ATLAS_v3.md`.
