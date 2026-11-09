# Preregistro — Experimento H1 (v0.1)

> Este documento se confirma (`git commit`) **antes** de ejecutar el barrido
> completo. El hash del commit queda registrado en
> `results/summary/h1_run_manifest.json`. Cualquier cambio posterior se
> anota solo en la sección "Desviaciones", con fecha, sin editar lo anterior.

## 1. Pregunta

¿La razón *t/h* (grosor característico del objeto en vóxeles) predice el error
relativo de volumen (V), área de superficie (S) y topología (β0, β1, β2) de
una máscara binaria segmentada, **con independencia** de la clase de forma, de
la anisotropía del vóxel y del método de segmentación?

*Diseño de datos*: fantomas con verdad analítica (ver `phantoms.py`), no
embriones reales. Nada de lo que se concluya aquí es evidencia sobre
embriones; solo sobre el comportamiento del instrumento de medida.

## 2. Diseño factorial completo

| Factor | Niveles |
|---|---|
| Forma (7) | `ball`, `ellipsoid`, `shell`, `torus`, `tube`, `shell_tight`, `torus_tight` |
| t/h_xy (7) | 1.5, 2, 3, 4, 6, 8, 12 |
| Anisotropía h_z/h_xy (3) | 1, 2, 3 |
| Perfil de imagen (2) | `ideal` (sin PSF, sin ruido); `realistic` (PSF FWHM = 1 h_xy, SNR = 10) |
| Segmentador (3, medidas repetidas sobre la misma imagen) | `global` (umbral 0.5, oráculo), `otsu`, `smoothed_otsu` |

* Réplicas: **R = 200** realizaciones independientes por celda
  (orientación SO(3) uniforme, desplazamiento subvoxel y ruido aleatorios).
  Total: 7×7×3×2×200 = 58 800 imágenes y 176 400 mediciones.
* Unidad experimental = realización. Nunca vóxel ni corte.
* Semilla base 20261109; cada celda/réplica deriva su semilla de forma
  determinista (`SeedSequence`), de modo que el resultado no depende del
  número de procesos.
* Un piloto de **tiempo** (60 condiciones, réplica 900, resultados
  descartados y no inspeccionados) se usó solo para dimensionar R.

## 3. Variables de respuesta

Primarias (binarias, por realización y segmentador):
* **V_ok**: |error relativo de V| ≤ 5 %.
* **Topo_ok**: (β0, β1, β2) medidos = verdad, con adyacencia **(26,6)**.

Secundarias: error con signo de V, S (marching cubes suavizado y conteo de
caras), Dice y HD95/distancia media frente a la máscara de referencia
(`cobertura ≥ 0.5` en la misma rejilla), topología con adyacencia (6,26).
No implementado en v0.1 (declarado, no omitido en silencio): error de
coeficientes de armónicos esféricos.

## 4. Predictores candidatos de la razón de resolución

Para el grosor sólido t_solid y el rasgo mínimo t_min = min(t_solid, t_vacío):

| | h = h_xy | h = h_geo = (h_xy² h_z)^(1/3) | h = h_max (= h_z) |
|---|---|---|---|
| t_solid / h | P1 | P2 | P3 |
| t_min / h | P4 | P5 | P6 |

Comparación por AIC y pseudo-R² de McFadden de regresiones logísticas
`Pr(ok) ~ log(P)`, ajustadas por separado para cada (segmentador, perfil) para
no repetir la misma imagen dentro de un mismo modelo. Sin p-valores
confirmatorios; se informan tamaños de efecto e intervalos.

## 5. Definición operativa de t/h\*

Para un estrato (forma, segmentador, anisotropía, perfil) y un criterio de
éxito (V_ok o Topo_ok), **t/h\*** es el menor nivel L de la rejilla tal que la
proporción observada de éxitos es ≥ 0.95 en L **y en todos los niveles
mayores**. Si no existe, se informa «no alcanzado» (no se extrapola). Se
informa además el límite inferior de Wilson al 95 % y el intervalo bootstrap
(1000 remuestreos de realizaciones dentro del estrato) del nivel t/h\*.

«Universalidad» = el rango de t/h\* entre clases de forma es ≤ **un paso de
la rejilla** (niveles adyacentes) en el estrato de referencia: perfil `ideal`,
anisotropía 1, segmentador `global`.

## 6. Hipótesis confirmatorias y criterios de falsación

* **H1a (volumen)**: V_ok es universal en t_solid/h_xy; t/h\* ≤ 6 para las 7
  formas en el estrato de referencia. *Falsada si* alguna forma queda en
  «no alcanzado» o t/h\* > 6, o el rango entre formas excede un paso.
* **H1b (topología)**: Topo_ok es universal en **t_min/h_xy**, no en
  t_solid/h_xy. *Falsada si* el rango de t/h\* basado en t_min excede un paso
  en el estrato de referencia. (Se espera, además, que con t_solid el rango
  sea ≥ 2 pasos por las clases `*_tight`; si no ocurriera, se informa.)
* **H1c (anisotropía)**: la razón con el vóxel peor (h_max) colapsa los
  niveles de anisotropía y la razón con h_xy no. *Falsada si* P3/P6 no
  alcanzan menor AIC que P1/P4 respectivamente, o si el rango de t/h\*
  (basado en h_max) entre anisotropías 1,2,3 excede un paso.
* **H1d (segmentación)**: t/h\* no depende del segmentador (rango ≤ un paso)
  en el perfil `ideal`. Se espera que falle para `otsu`/`smoothed_otsu`
  (sesgo de umbral en objetos pequeños).

Un resultado negativo en cualquiera se reporta con el mismo peso que uno
positivo, y es el producto científico del experimento.

## 7. Predicciones escritas antes de ver datos (para calibrar mi criterio)

1. En el estrato de referencia, V_ok se alcanza en t/h\* = 3–4 para formas
   convexas y en 4–6 para cáscara/tubo/toro.
2. Topo_ok con t_min en el estrato de referencia: t/h\* ≈ 3–4 (rasgo de al
   menos ~3 vóxeles); con t_solid, las clases `*_tight` exigirán ≥ 2 pasos más.
3. Con anisotropía 3, Topo_ok exigirá t/h_xy ≳ 9–12 (≈ 3–4 vóxeles en z).
4. `otsu` y `smoothed_otsu` sobrestimarán V en objetos pequeños (+3 a +10 %).
5. Con perfil `realistic`, `otsu` crudo tendrá peor topología que
   `smoothed_otsu` en todas las clases.

## 8. Chequeo de consistencia con la literatura (no es replicación)

Con `ball`, perfil `ideal`, anisotropía 1, `global`: la mediana del error
absoluto del **diámetro equivalente** (V/V_verdad)^(1/3) − 1 debe ser ≤ 2 % para
t/h ≥ 6 (la literatura revisada informa ≤ 2 % con ≥ 5 vóxeles de diámetro;
Horner 2019, según nuestra revisión; protocolo distinto, tolerancia ±0.5 pp).

## 9. Limitaciones declaradas de antemano

Formas simples y suaves; PSF y ruido gaussianos; sin artefactos de movimiento,
contraste no uniforme ni bordes borrosos reales; un solo tamaño de objeto
relativo a la rejilla por clase. **Estos resultados no se transfieren a
embriones reales sin validación con datos reales.**

## 10. Desviaciones

*(ninguna al momento de la firma)*
