# Presentación final — cómo abrirla y qué contiene

## Abrir

1. Doble clic en `docs/exposicion/geovida-presentacion-final.html`. Se abre en Chrome, Edge o Firefox.
2. **Funciona sin internet:** imágenes, mallas 3D y three.js (r128, licencia MIT) van dentro del archivo (5,1 MB).
3. Para la exposición: pulsa **F** (pantalla completa) y **P** (modo exposición: oculta la barra; reaparece al pasar el ratón).

| Tecla | Acción |
|---|---|
| → · espacio · AvPág | Lámina siguiente |
| ← · RePág | Lámina anterior |
| Inicio · Fin | Primera · última lámina |
| G | Mostrar u ocultar el guion de la lámina |
| P | Modo exposición |
| F | Pantalla completa |
| Esc | Cerrar una imagen ampliada |

- Clic en una imagen o en una tarjeta de la galería para ampliarla con su ficha.
- En la lámina 13, arrastra para girar el modelo 3D, usa la rueda para acercar y haz doble clic para reiniciar.
- Los paneles «Detalles técnicos» se abren con un clic.
- `#n` al final de la dirección abre la lámina n (por ejemplo `...final.html#18`).

**Reconstruir** (solo si cambias la fuente). Las imágenes y las mallas no se guardan en git: se generan en local
a partir de los datos públicos.

1. `python scripts/figure_atlas.py`: figuras de MusMorph, Qiu y ONTO-MAP.
2. `python scripts/figure_final.py`: proceso real, resolución, Euler, mallas y `img/final_data.json`. Necesita los datos de Qiu 2021 en local.
3. `python docs/exposicion/final/build.py`.

El HTML resultante tampoco se sube; los valores numéricos de las láminas están en `img/final_data.json`.

Archivos:

- Fuente: `final/deck.html`.
- Imágenes y datos: `img/`.
- Copia del prototipo anterior: `geovida-presentacion-prototipo-v2.html`.

## Cambios frente al prototipo v2

- **Nuevo orden narrativo:** problema → importancia → objetivos → método → evidencia real → modelos 2D–5D → topología → morfometría → semáforo → MORPHO-TRACE → pruebas → arquitectura → futuro → conclusiones.
- **Nuevas láminas:**
  - qué es la plataforma, con la pregunta central;
  - importancia A–E, que termina con la frase pedida;
  - objetivos con su estado;
  - flujo metodológico en 7 etapas con su estado;
  - 2D/3D/4D/5D con su estado;
  - topología y Euler;
  - topología aplicada a una muestra real;
  - morfometría;
  - tabla de pruebas A–F;
  - arquitectura con los módulos reales;
  - conclusiones con la cita final;
  - anexo de fuentes.
- **Evidencia real nueva,** calculada por `scripts/figure_final.py` sobre el primer caso del manifiesto de H11, elegido por esa regla y no por su resultado:
  - imagen original → referencia → tres segmentaciones de geovida;
  - medidas 2D y 3D;
  - sensibilidad a la resolución;
  - **modelo 3D interactivo real** del cuerpo y los ventrículos (embrión E11, Qiu et al. 2021, CC BY).
- **Semáforo con su significado real:** p = Pr(|error de volumen| ≤ 5 %), umbrales 0,90 y 0,50, guardia de dominio. Lleva un caso real de H11: sin la guardia, 5 de 6 medidas habrían salido en verde de forma falsa; con ella, ninguna.
- **Etiqueta en cada figura:** dato real, salida del software, ilustración sintética o concepto.
- **Interacción:** modo exposición, paneles desplegables, barra de progreso con la sección actual y botón de pantalla completa.
- **Paleta:** azul profundo, azul petróleo, blanco y gris técnico, con acentos turquesa.

## Funcionalidades demostradas (y su estado)

| Funcionalidad | Dónde | Estado |
|---|---|---|
| Lectura calibrada de volúmenes reales (vóxel de 50 µm leído del encabezado) | Láminas 12 y 13 | Implementado |
| Segmentación clásica (umbral global, Otsu, Otsu suavizado) | Lámina 12 | Implementado |
| Volumen, área (Crofton), Betti y χ en 3D | Láminas 12, 16 y 19 | Implementado; contrastado con SimpleITK |
| Descriptores 2D (área, perímetro, circularidad, solidez, Hu) | Lámina 17 | Implementado (geovida y scikit-image) |
| Certificado de volumen (semáforo) con guardia de dominio | Lámina 18 | Confirmado en sintético; con ecografía real (H11, cerrado): la guardia negó el verde a las 1188 medidas, la primaria no fue evaluable |
| Sensibilidad a la resolución | Lámina 19 | Ilustración con un caso; el estudio formal (P3) está en medición |
| Malla 3D por marching cubes | Lámina 13 | Implementado (solo para visualizar) |
| 4D por pseudo-tiempo | Lámina 14 | Experimental, solo sintético |
| Contexto 5D | Lámina 14 | Propuesta |

## Trabajo futuro

1. Cerrar P3 confirmatorio y H11 (veredictos preregistrados).
2. Medir el efecto del atlas por estadio.
3. Validar la segmentación con más datos.
4. Comparar la topología persistente con las métricas simples.
5. Hacer 4D con series longitudinales reales.
6. Construir el contexto 5D.
7. Conseguir revisión externa.
8. Mantener la línea prenatal como investigación independiente, sin funciones clínicas.

Detalle en `docs/INFORME_DE_PROGRESO.md` §5.

## Fuentes

Ver la última lámina (anexo) y `docs/exposicion/GUION_V2.md`:

- **Datos:** MusMorph/IMPC (FaceBase 3-JZA6, CC BY 4.0) y Qiu et al. 2021 (IEEE DataPort, CC BY).
- **Cifras:**
  - OMS, nota «Congenital disorders», 2023;
  - informe de la OMS de 2026;
  - CDC-MINSA, 2022;
  - DIGEMID, DS 003-2020-SA.
- **Software:** SimpleITK 2.5.7, scikit-image y three.js r128.

## Límites que la presentación declara

- Investigación preclínica con datos de ratón. No es un dispositivo médico ni hace afirmaciones clínicas.
- El semáforo evalúa la fiabilidad de una medida, nunca la salud del embrión.
- Los casos reales mostrados son ilustraciones de un caso, no veredictos.
