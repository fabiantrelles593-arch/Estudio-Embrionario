# Imagen 2D real — método, límites y lo que se descartó

> Solo investigación y educación. No es un dispositivo ni una herramienta clínica. Módulo: `src/geovida/real2d.py`;
> orden: `geovida real2d`; pruebas: `tests/test_real2d.py` (con una «foto» sintética de verdad conocida, nunca con personas).

## Cómo se usa

```bash
geovida real2d FOTO.jpg --roi X0 Y0 X1 Y1 --ruler X1 Y1 X2 Y2 --ruler-mm 10 \
        --printed-crl-mm 12.3 --caliper X1 Y1 X2 Y2 --out ../informe_privado \
        [--human --authorization-note "quién autoriza y con qué base"]
```

Escribe `informe.md`, `informe.json` y `superposicion.png` (contorno rojo del objeto, ROI amarilla). Con `--human` la
nota es obligatoria y queda en el informe como **declaración, sin verificar**. Los metadatos (EXIF/GPS/nombres) se descartan al
cargar; el informe lleva solo el SHA-256 del archivo, nunca su nombre ni su ruta.

## Qué calcula

1. **Escala** (mm/px) desde la regla impresa (dos puntos y su longitud) o desde marcas igualmente espaciadas (mediana de los
   espaciados; informa su dispersión), o declarada.
2. **Medida nativa**: longitud máxima de Feret del mayor componente dentro de la ROI, con `smoothed_otsu`.
3. **Certificado por desenfoque en milímetros.** La foto no dice cuál es la función de dispersión (PSF). Para cada desenfoque de una
   rejilla (0.25, 0.5, 0.75, 1, 1.5, 2 mm) se remuestrea la imagen a una escala de trabajo donde `n` (50–300 px) y la PSF (1–5 px) caen dentro de la
   caja calibrada: remuestrear conserva el cociente `r = desenfoque / longitud`, y solo hay solución si `r` está entre ≈ 1/300 y 0.10.
   Después se mide de nuevo y se aplica el modelo congelado (H14). Fuera de la caja: amarillo con el motivo.
4. **Tope de imagen real**: la calibración es solo de simulación, así que el semáforo **nunca sale verde**; se guarda el que daría la
   simulación (`light_if_simulation_held`) rotulado como tal.
5. **Edad por fórmula** (INTERGROWTH-21st, rango 15–95 mm; Robinson): informativa, con la dispersión biológica; no incluye el error de medida.
6. **Control de calidad**: objeto recortado por la ROI, fracción ocupada, componentes grandes, contraste/ruido.

## Hallazgo sobre el dominio (cálculo, no medida)

Para una longitud de 12 mm el cociente `r` llega a 0.10 con un desenfoque de **1.2 mm**; con 1.5 mm ya no hay escala de trabajo dentro de la
caja. Una ecografía transvaginal tiene una resolución lateral del orden de 0.5–1 mm y una abdominal peor (orden de magnitud de memoria, **sin fuente verificada**): **la caja calibrada apenas
cubre los embriones más pequeños** (CRL < 15 mm queda además fuera del rango de la fórmula INTERGROWTH). Ampliar la calibración a cocientes
`r` mayores (objetos pequeños, desenfoque grande) es trabajo pendiente.

## Lo que probé y descarté (resultado negativo, exploratorio)

Estimador del desenfoque desde la propia imagen, ajustando una función error al perfil medio a través del borde segmentado
(`n` = 80, 130 y 210; 12 imágenes simuladas por celda, el desenfoque verdadero es la PSF de la simulación):

| PSF verdadera (px) | estimada (mediana) | cociente |
|---|---|---|
| 1.0 | 1.84–1.96 | 1.8–2.0 (piso) |
| 2.0 | 2.00–2.09 | 1.0 |
| 3.5 | 2.11–2.53 | 0.60–0.72 |
| 5.0 | 2.67–3.12 | 0.53–0.62 |

Subestima entre 28 % y 47 % con PSF ≥ 3.5 px y tiene un piso cerca de 1.9 px: el borde lo fija el propio ruido de moteado (sesgo de selección: el
contorno cae donde el ruido «afila» el perfil). **Se descartó y no se usa**; por eso el desenfoque se barre en vez de estimarse. Una vía
alternativa (autocorrelación del moteado) depende de que el simulador ate el tamaño del grano a la PSF, así que no probaría nada sobre imagen real.

## Supuestos no verificados

* El error de la medida se calibró con fantomas simulados (cápsula, moteado, PSF gaussiana). Nadie lo comparó con una ecografía real.
* No se modelan la compresión logarítmica, la ganancia, la impresión, la fotografía ni el JPEG (la hipótesis H15 los pone a prueba en simulación).
* La ROI la elige una persona; si incluye otras estructuras brillantes (pared del saco, saco vitelino), la medida es de otra cosa.
* El tamaño de trabajo sale de la propia medida nativa: la circularidad que H14 dejó abierta.
