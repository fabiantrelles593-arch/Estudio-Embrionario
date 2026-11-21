# Preregistro — H6: el semáforo de adecuación de resolución (v0.3)

> Se confirma (`git commit`) **antes** de correr el barrido de calibración y el de
> confirmación (`scripts/run_h6.py`). Los hashes de commit quedan en
> `results/summary/h6cal_run_manifest.json` y `h6_run_manifest.json`. Los cambios
> posteriores van solo en «Desviaciones».

## 1. Pregunta y por qué importa

Con datos reales no se conoce la forma verdadera: no se puede calcular Q = V/(S·h)
con el V y el S verdaderos (como en H3). ¿Puede el instrumento estimar, **solo con
la máscara y el tamaño del vóxel**, la probabilidad de que su propio volumen tenga
error ≤ 5 %, y encender una luz roja cuando no debe fiarse?

Contexto del piloto (semilla 20261115, **no** usada aquí; 4 réplicas por celda):
Q̂ = V̂/(Ŝ h_geo), con Ŝ = `area_sdf`, **sobrestima** Q a baja resolución (mediana de
Q̂/Q = 1.4–1.5 a t/h = 3, 1.8–2.5 a t/h = 1.5 y ≈ 1.0 desde 8 vóxeles); una bola de
1.5 vóxeles puede dar área 0. Un ajuste ingenuo con los modelos de H1 daría luz
verde de más. Además, un primer intento de ajustar Q̂ con los datos de H3 produjo
una pendiente casi plana en el segmentador `global` (Q̂ no es monótono a
resolución muy baja, cuando el área colapsa): por eso se compara con una segunda
variable que no usa el área.

## 2. Variables, protocolo y reglas fijas

| Variable candidata | Definición (solo máscara + vóxel) |
|---|---|
| F1 | ln(Q̂/h_geo), Q̂ = V̂/Ŝ, V̂ = conteo de vóxeles, Ŝ = `area_sdf` |
| F2 | ln(d̄/h_geo), d̄ = profundidad media interior (`d_mean`: media de la distancia a la frontera sobre los vóxeles del objeto; bola de radio r: ≈ r/4) |

* **Calibración** (semilla 20261116, 30 réplicas por celda, las 10 formas, rejilla
  7 × 3 × 2, tres segmentadores preregistrados): por estrato (segmentador × perfil),
  validación cruzada *dejando una forma fuera* (ajustar con 9, evaluar con la 10.ª).
  Se elige UNA variable para todos los estratos: la de menor entropía cruzada
  promedio (suma de los 6 estratos y 10 formas). Luego se ajusta el logit final por
  estrato con las 10 formas y se **congela** en `results/summary/h6_frozen_models.json`
  (con el hash de los datos) y se confirma en git.
* **Confirmación** (semilla 20261114, 40 réplicas por celda, mismas formas y rejilla):
  no se reajusta nada.
* **Máscara vacía o variable no medible** (área ≤ 0, V̂ ≤ 0): p = 0 y luz roja.
* **Semáforo:** verde si p ≥ 0.90; amarillo si 0.50 ≤ p < 0.90; rojo si p < 0.50.
* **Respuesta:** V_ok = |error relativo de V| ≤ 5 %.
* **Modelo ingenuo (A):** los modelos de H1 (`h3_frozen_models.json`, Q verdadero)
  aplicados a Q̂ (F1), con la misma regla de no medible.
* **Estratos:** 6 = {`global`, `otsu`, `smoothed_otsu`} × {`ideal`, `realistic`}.
* ECE: 10 cajas de igual ancho en la probabilidad. AUC por rangos.
* «Verde falso»: filas con p ≥ 0.90 donde V_ok = 0. Un estrato es evaluable si tiene
  ≥ 200 filas en verde.

## 3. Hipótesis y criterios (fijos)

* **H6a — El modelo ingenuo es demasiado optimista.** Existe ≥ 1 estrato evaluable
  donde la tasa de verde falso de A supera 0.10. *No evaluable* si ningún estrato
  tiene ≥ 200 filas verdes con A.
* **H6b — El semáforo discrimina.** AUC del modelo congelado ≥ 0.85 en ≥ 5 de 6
  estratos. *Parcial*: 4. *No apoyada*: ≤ 3.
* **H6c — Está calibrado.** ECE ≤ 0.10 en ≥ 5 de 6 estratos. *Parcial*: 4. *No
  apoyada*: ≤ 3.
* **H6d — No da luz verde falsa.** La tasa de verde falso ≤ 0.10 en **todos** los
  estratos evaluables. *No evaluable* si ninguno lo es. *No apoyada* si alguno falla.
* **H6e — Mejora al ingenuo.** Menor entropía cruzada que A en ≥ 5 de 6 estratos.
  *Parcial*: 4. *No apoyada*: ≤ 3.

Un valor no calculable es «no evaluable», nunca «no apoyada».

**Extensión descriptiva (sin veredicto):** (i) uso del modelo del perfil equivocado
(modelo `realistic` en imágenes `ideal` y al revés); (ii) tasa de verde falso por
forma; (iii) comportamiento a t/h ≤ 2.

## 4. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| La validación cruzada elige F2 (profundidad media) sobre F1 | 70 % |
| H6a apoyada | 85 % |
| H6b apoyada (≥ 5/6) | 80 % |
| H6c apoyada (≥ 5/6) | 60 % |
| H6d apoyada | 45 % |
| H6e apoyada (≥ 5/6) | 85 % |

## 5. Qué no se puede concluir

* Solo vale para el **volumen** y para este modelo de imagen sintético (PSF y ruido
  gaussianos, formas de nuestra familia). La topología queda fuera.
* El modelo es monótono (un logit de una variable): no capta casos raros.
* El usuario debe declarar segmentador y perfil de imagen; si se equivoca, el
  semáforo puede fallar (la extensión (i) mide cuánto).
* Pasar H6 no dice nada sobre embriones ni ecografías reales.

## 6. Desviaciones

(Ninguna al momento del primer commit.)

- 2026-11-09 (después de la calibración y antes del barrido de confirmación; nada de lo anterior
  se tocó):
  1. **Aclaración sobre la entropía cruzada.** El preregistro fija p = 0 para una variable no
     medible pero no decía cómo evaluar la entropía cruzada con p = 0 (log 0). Se recorta la
     probabilidad a [0.001, 0.999] **solo** para la entropía cruzada (`h6.P_FLOOR`); el semáforo y
     el verde falso siguen usando p = 0. Se escribió antes de analizar la calibración.
  2. **Se retiró `scripts/freeze_h6_models.py`**: ajustaba sobre los datos de H3 con un diseño que
     el piloto descartó (ver §1) y escribía en el mismo archivo que ahora produce
     `scripts/calibrate_h6.py`.
  3. **Resultado de la calibración** (semilla 20261116, 37 800 filas, `code_dirty: false`, commit
     `db7e37c`): la validación cruzada eligió **F2** (profundidad media): entropía cruzada media
     0.245 frente a 0.377 de F1; F2 gana en 5 de 6 estratos (en `otsu · realistic` F1 es
     ligeramente mejor: 0.202 frente a 0.213). Las seis pendientes son positivas (5.7 a 12.5).
     Mi predicción de que F2 ganaría (70 %) se cumplió.
  4. El barrido de calibración tardó 737 s (no ~6 min): el de confirmación (40 réplicas) tardará
     ~16 min.
