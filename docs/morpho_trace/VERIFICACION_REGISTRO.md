# Verificación de la cadena de registro de MT-A (23 nov 2026)

**Tipo:** nota de ingeniería. **No es un estudio ni un veredicto científico**, y no cambia el de MT-A v2
(`RESULTADOS_ATLAS_v2.md`: no evaluable por G1). Es la verificación propuesta en su §8 [PROP], hecha antes de
cualquier MT-A v3. Datos de ratón de MusMorph ya descargados; nada humano, nada clínico.

Código: `scripts/verify_registration_chain.py` (subórdenes `synthetic`, `specimens`, `geometry`), con pruebas en
`tests/test_verify_registration_chain.py`. Resultados fuera de git, en `results/morpho_trace/v2/verificacion/`
(`synthetic.json`, `specimens.json`, `geometry.json`).

## 1. Pregunta

MT-A v2 §5 dejó dos causas posibles [HIP] para el fallo de G1: (1) la B-spline se ajusta a la intensidad y deforma
la anatomía; (2) un defecto en la cadena de transferencia de puntos. Si fuera (2), habría que corregir el código
antes de nada. Esta nota distingue las dos.

## 2. Resultado en una frase

**No se encontró ningún defecto de código** [HV]: la transferencia de puntos es correcta con una deformación conocida,
imagen y landmarks comparten el espacio físico, y el registro reproduce los números de v2. El fallo viene del propio
**objetivo del registro**: optimizar la información mutua del cuerpo entero aleja los landmarks de la cabeza, ya desde
la inicialización, y la B-spline lo agrava, sobre todo en E18.5 [HV para los números; la causa es HIP].

## 3. Prueba con deformación conocida sobre el atlas real (`synthetic`)

Atlas E15.5 de MusMorph a ×4 como imagen fija; la móvil es el mismo atlas deformado por una afín conocida T (giro de
4° en z, escala 1,03, traslación (0,6, −0,4, 0,3) mm). Si la cadena es correcta, los 540 landmarks del atlas
transferidos deben caer en T(landmarks).

| Medida | Mediana | p90 |
|---|---|---|
| Desplazamiento real que introduce T | 0,741 mm | — |
| Error tras registro solo afín | **0,0048 mm** | 0,0061 mm |
| Error tras registro completo (afín + B-spline, como en v2) | **0,0067 mm** | 0,0097 mm |
| Error con el otro orden de composición | 0,0066 mm | — |

[HV] La transferencia recupera T con un error unas 100 veces menor que el desplazamiento y unas 15 veces menor que
el vóxel (0,108 mm). Descarta errores de convención de dirección (fija → móvil), de ejes NumPy/ITK o de origen.

**Límite:** aquí la B-spline apenas se movió (desplazamiento máximo 0,010 mm), así que esta prueba no distingue el
orden de composición afín/B-spline. Lo hace la §4.

## 4. Variantes del registro sobre dos especímenes ya vistos (`specimens`)

IMPC_E15.5_0313 e IMPC_E18.5_1284, de los 40 de MT-A v2. Se compara con sus landmarks publicados. ρ es la distancia
de Procrustes (forma); «mm» es la distancia sin superponer (mediana). Referencia de G1: mediana de ρ entre
especímenes del mismo estadio, 0,068 (E15.5) y 0,042 (E18.5) (v2 §5).

| Variante | E15.5 ρ | E15.5 mm | E18.5 ρ | E18.5 mm | Desplazamiento de la B-spline en E18.5 (mediana · máx) |
|---|---|---|---|---|---|
| Identidad (landmarks del atlas sin mover) | **0,036** | 0,57 | **0,049** | **0,30** | — |
| Solo afín | 0,053 | 0,27 | 0,053 | 0,65 | — |
| Preregistrado: malla 8³, muestreo aleatorio | 0,116 | 0,31 | 0,579 | 2,38 | 2,5 · 5,0 mm |
| Malla 8³, muestreo regular | 0,104 | 0,26 | 0,430 | 2,52 | 2,7 · 5,9 mm |
| Malla 4³, muestreo regular | 0,053 | **0,19** | 0,476 | 2,37 | 2,0 · 3,9 mm |

Lo que muestra [HV]:

* **Se reproduce v2.** La variante preregistrada da ρ = 0,116 y 0,579, en línea con las medianas de v2 (0,113 y
  0,525). El código de esta verificación hace lo mismo que el de MT-A.
* **El muestreo aleatorio no es la causa.** Con muestreo regular, el ruido del coste desaparece y E18.5 sigue en
  ρ ≈ 0,43.
* **Una malla más gruesa no basta.** La malla 4³ ayuda en E15.5, pero en E18.5 la B-spline sigue desplazando los
  puntos una mediana de 2 mm.
* **Ninguna variante mejora la forma de la identidad** en ninguno de los dos especímenes. En E15.5 la afín y la malla
  4³ acercan los puntos en posición (0,19–0,27 mm frente a 0,57), pero empeoran la forma (ρ 0,053 frente a 0,036).
* **El orden de composición usado en v2 es el bueno:** el otro orden da ρ peor en 5 de 6 casos (en el sexto, la
  diferencia es de 0,001).

## 5. Geometría e inicialización (`geometry`)

| Comprobación | E15.5_0313 | E18.5_1284 |
|---|---|---|
| ¿Atlas y espécimen en la misma rejilla (tamaño, origen, vóxel, dirección)? | Sí (0,108 mm) | Sí (0,216 mm) |
| Centroide del tejido, atlas · espécimen (mm) | (6,42, 7,44, 9,96) · (6,52, 7,30, 10,90) | (8,00, 9,52, 17,96) · (8,04, 9,48, 18,16) |
| Centroide de los landmarks, atlas · publicados (mm) | (6,29, 9,21, 14,21) · (6,43, 8,95, 14,10) | (8,02, 10,78, 26,45) · (7,96, 10,71, 26,21) |
| Información mutua (más negativa es mejor), identidad → inicialización por momentos | −0,159 → −0,163 | −0,368 → −0,386 |
| Distancia mediana a los publicados, identidad → inicialización por momentos | 0,57 → **1,05 mm** | 0,30 → **0,68 mm** |

[HV] Imagen y landmarks están en el mismo espacio y las imágenes de MusMorph ya vienen alineadas a su atlas. Aun así,
**el primer paso del registro, la inicialización por momentos, ya empeora los landmarks mientras mejora la
información mutua**: desplaza el cuerpo entero 0,4–0,8 mm en z para cuadrar la masa del tejido, y la cabeza se va
con él.

## 6. Interpretación

* [HV] No hay defecto de transferencia ni de coordenadas. **No se cambia código de producción**; las pruebas
  añadidas protegen las piezas de esta verificación.
* [HIP] Causa más probable: **el registro optimiza la semejanza de intensidades del cuerpo entero** (atlas
  `Body_Atlas`), mientras los landmarks están en la cabeza. Las diferencias de postura y de tejido fuera de la cabeza
  arrastran la transformación. Como las imágenes ya están prealineadas, cualquier movimiento que no esté guiado por
  la cabeza la aleja. En E18.5 (vóxel de 216 µm, cuerpo más largo) la B-spline sin regularización amplifica el efecto.
  Esta causa es coherente con los números de §4 y §5, pero no está demostrada: no se probó un registro restringido a
  la cabeza.
* [HV] Con estos datos, **la identidad es la mejor transferencia disponible** para los dos especímenes. Un registro
  que no la supere no aporta nada a MT-A.

## 7. Qué no se puede concluir

* Nada sobre el efecto del atlas en **d**: sigue sin medirse.
* Dos especímenes, elegidos entre los ya vistos: la §4 orienta, no estima la tasa de fallo de cada variante.
* Nada sobre otros registradores (ANTs, elastix) ni sobre un registro limitado a la cabeza.
* Nada sobre humanos ni uso clínico.

## 8. Implicaciones para un MT-A v3 [PROP] (requiere aprobación del autor y un preregistro nuevo)

1. **La identidad como referencia obligatoria en G1:** el registro debe superar a los landmarks del atlas sin mover,
   no solo a la variación entre especímenes.
2. **Registrar la región que se mide:** máscara o recorte de la cabeza, con la máscara derivada del atlas y fijada
   antes de medir.
3. **B-spline regularizada o sin B-spline:** si la afín de la cabeza ya pasa G1, la B-spline no hace falta.
4. **G1 primero, en 2–4 especímenes nuevos,** antes de los 80 registros (lección de v2).
5. Si se usa otro registrador, comprobar su licencia antes de instalarlo.

No se ha ejecutado nada de esta sección.
