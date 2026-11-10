# Métodos (geovida v0.1 – v0.4)

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

## 8. Extensiones de v0.2

* **Área por distancia con signo** (`measure._area_sdf`): superficie de nivel 0
  de una función de distancia con signo de la máscara (frontera a medio paso
  entre centros de vóxel), suavizada con σ = 0.5 vóxel, y marching cubes. Evita
  el encogimiento de objetos pequeños que sufre el suavizado de la máscara
  (`area_mc`). σ se fijó con un piloto (`scripts/pilot_area_sdf.py`).
* **Segmentador de extensión `otsu_clean`**: Otsu crudo, elimina componentes de
  primer plano y rellena cavidades de menos de 8 vóxeles. No pertenece al
  conjunto preregistrado de H1.
* **Formas nuevas** (`capsule`, `cylinder`, `oblate`) y modelos congelados
  (`analysis.fit_frozen_logit`): confirmación H3 (`PREREGISTRO_H3.md`).
* **Módulo 2D** (`twod.py`): fantomas planos, moteado multiplicativo,
  circunferencia por elipse, topología (8,4) y (4,8) (`PREREGISTRO_2D.md`).
* **Procedencia** (`provenance.py`): commit y marca de código modificado.
* **Veredictos de tres estados**: «apoyada», «no apoyada», «no evaluable».

## 9. Extensiones de v0.3

* **Profundidad media interior** (`measure._mean_depth`): media, sobre los vóxeles del
  objeto, de la distancia a la frontera. No usa ningún estimador de área. En una bola de
  radio r vale r/4.
* **Semáforo de volumen** (`budget.py`, H6): logit por segmentador y perfil sobre
  ln(d̄/h_geo), elegido por validación cruzada dejando una forma fuera, congelado y
  confirmado con semillas nuevas. Verde p ≥ 0.90; rojo p < 0.50.
* **Limpieza 2D que escala con el objeto** (`twod._clean_mask_2d`, H7) y forma `ring_tight`.
* **Series de crecimiento** (`growth.py`, H8): objeto que crece ×1.35 por etapa con vóxel
  fijo; tasa = pendiente de ln V frente a la etapa, con todas las etapas o sin las rojas.

## 10. Extensiones de v0.4: certificado vectorial

* **Margen de persistencia topológica** (`topomargin.py`). Geométrico: mayor dilatación o
  erosión euclídea, en vóxeles finos, que conserva el triple de Betti (es la persistencia en
  la filtración por distancia con signo). De intensidad: cuánto puede moverse el umbral, en
  fracción del contraste medido, sin cambiarlo. `critical_sites` localiza el primer evento
  cuando es una separación, una fusión o un componente o cavidad pequeños.
* **Eje de escala de medición** (`scaleaxis.py`): la imagen se degrada ×2 y ×4 por promedio
  de bloques y se vuelve a segmentar y medir. Se usa el acuerdo del triple de Betti entre
  escalas como variable. En bioimagen «5D» ya significa x, y, z, canal y tiempo; este eje
  es otra cosa: una dimensión de la medición.
* **Guardia de dominio** (`domain.py`): `snr_hat` (contraste / ruido del fondo lejano) y
  `edge_width` (grosor de la banda de transición del borde) medidos en la imagen; envolvente
  entre los cuantiles 1 % y 99 % de las filas de calibración con luz verde. Fuera de la
  envolvente no hay luz verde.
* **Formas nunca vistas** (`dumbbell`, `cup`) y **perfiles nunca vistos** (`blurry`, `noisy`,
  `mild_blur`, `mild_noise`), que no entran en ninguna calibración.
* **Certificado** (`certificate.py`, orden `geovida certify`): luz de volumen, luz de
  topología, punto frágil y pertenencia al dominio para una imagen 3D. `geovida plan` da la
  resolución mínima para luz verde. Antecedentes y citas: `ANTECEDENTES_V04.md`.

## 11. Reproducibilidad

Semillas derivadas de la celda con `SeedSequence`: el resultado no depende del
número de procesos (hay una prueba). Cada ejecución escribe un manifiesto con
commit, versiones y duración; desde v0.3 el estado de git se toma al empezar. Dos
corridas del barrido de H8 dieron tablas idénticas fila a fila.
