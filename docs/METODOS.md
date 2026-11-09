# Métodos (geovida v0.1)

## 1. Qué se mide y por qué así

Las mediciones morfométricas de una máscara binaria (volumen, área, números
de Betti) dependen de la resolución, del vóxel (anisotropía), del desenfoque
del instrumento, del ruido y del segmentador. Con datos biológicos no se sabe
cuánto de una diferencia es biología y cuánto es instrumento, porque falta la
verdad. Aquí se invierte el problema: se parte de objetos cuya verdad se
conoce exactamente y se mide cuánto la degrada cada eslabón de la cadena.

## 2. Fantomas (`phantoms.py`)

Siete clases con volumen, área, números de Betti y rasgos mínimos analíticos:
`ball`, `ellipsoid` (ejes 2 : 1.5 : 1), `shell` (cavidad 4 t), `torus`
(hueco 1.5 t), `tube` (lumen 2 t, longitud 5 t), `shell_tight` (cavidad 0.5 t)
y `torus_tight` (hueco 0.5 t). `t` es el menor grosor sólido. Las dos clases
`*_tight` existen para poder separar dos predictores rivales de la resolución
requerida: el grosor sólido t_solid y el rasgo mínimo t_min = min(t_solid,
t_vacío).

Cada fórmula se contrasta en las pruebas con una comprobación independiente
(rasterización fina del indicador para V y topología; cuadratura numérica para
el área del elipsoide; marching cubes para el área del resto).

## 3. Simulación de adquisición (`imaging.py`)

Orientación SO(3) uniforme y desplazamiento subvoxel aleatorios; fracción de
ocupación por supermuestreo 3×3×3 (volumen parcial); PSF gaussiana (FWHM en
múltiplos de h_xy, aplicada en unidades físicas); ruido gaussiano aditivo con
SNR = contraste / σ. Perfiles: `ideal` (sin PSF ni ruido) y `realistic`
(FWHM = 1 h_xy, SNR = 10). Espaciado (h_xy, h_xy, a·h_xy), a ∈ {1, 2, 3}.

## 4. Segmentación y medición (`segment.py`, `measure.py`)

Tres segmentadores sin limpieza morfológica (los errores topológicos deben
verse): umbral global 0.5 (oráculo), Otsu, suavizado + Otsu. Volumen = conteo
× volumen de vóxel. Área: marching cubes sobre la máscara suavizada (principal)
y conteo de caras expuestas (referencia ingenua). Topología: Betti con
adyacencia explícita; principal (26,6), secundaria (6,26).

## 5. Topología digital (`topology.py`)

b0 y b2 por etiquetado de componentes (primer plano y fondo con adyacencias
complementarias; el fondo conexo al borde rellenado es el exterior); χ por
`skimage.measure.euler_number`; b1 = b0 + b2 − χ. Verificado con casos
construidos a mano donde las dos adyacencias dan respuestas distintas.

## 6. Diseño experimental y análisis (`experiment.py`, `analysis.py`)

Diseño factorial completo y preregistrado (`PREREGISTRO_H1.md`). Unidad
experimental = realización. Resultados binarios (V_ok, Topo_ok) resumidos con
intervalos de Wilson; t/h\* = menor nivel con éxito ≥ 0.95 sostenido;
comparación de seis predictores por AIC en regresión logística (con un ridge
mínimo sobre la pendiente para tolerar separación perfecta).

## 7. Banco de pruebas 4D (`traj4d.py`)

Cohortes transversales con error de estadificación; estimadores lineales
(`stage_mean`, `spline`, `spline_corrected`); sesgo, varianza y cobertura
bootstrap por especímenes en forma cerrada (la matriz de suavizado es fija en
diseños balanceados). Ver `PREREGISTRO_H2.md`.

## 8. Reproducibilidad

Semillas derivadas de la celda con `SeedSequence`: el resultado no depende del
número de procesos (hay una prueba). Cada ejecución escribe un manifiesto con
commit, versiones y duración.
