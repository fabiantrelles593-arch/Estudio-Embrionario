# Comparación del motor 3D con estimadores de referencia independientes (P1) — 17 nov 2026

> Tarea P1 de `docs/INFORME_DE_PROGRESO.md` (puerta de la fase 4). Criterios fijados en el docstring de
> `scripts/compare_reference.py` **antes** de ejecutar. Semilla 20261117.
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta · [PV] pendiente.

## 1. Qué se comparó y por qué así

No hay ninguna biblioteca de referencia instalada (SimpleITK, ITK o VTK), e instalar una exige descargarla
con permiso del autor. Por eso esta primera comparación usa **reimplementaciones independientes desde la
definición matemática** (`src/geovida/reference.py`), que no comparten código con `measure.py` ni con
`topology.py`, y tampoco usan `skimage.measure`:

| Métrica | geovida | Referencia independiente |
|---|---|---|
| Característica de Euler χ | `skimage.measure.euler_number` (tabla de configuraciones) | Conteo de celdas χ = V − E + F − C: cubos cerrados (conectividad 26) o complejo dual (conectividad 6) |
| Área | `area_sdf` (principal: marching cubes sobre distancia con signo), `area_mc`, `area_faces` | Cauchy–Crofton discreto con 13 direcciones y pesos de Voronoi sobre direcciones físicas (Lehmann y Legland 2012, solo la idea de la fórmula) |
| Volumen | Conteo de vóxeles × volumen del vóxel | Se compara con la verdad analítica (el método es el mismo por definición) |

Pruebas del módulo de referencia (`tests/test_reference.py`, 11 pasan): casos hechos a mano (vóxel, cubo,
cubo hueco, anillo, vóxeles diagonales con las dos conectividades), Crofton a ≤ 3 % en una bola grande y con
vóxeles anisótropos, y χ igual al de `topology.py` en 40 máscaras aleatorias.

Datos: 8 fantomas con verdad analítica (bola, elipsoide, cápsula, cilindro, oblato, cáscara, toro, mancuerna),
máscaras ideales a t/h = 4, 6, 8, 12 y 16 con 3 rotaciones al azar (120 máscaras); y 20 máscaras reales de
ventrículos cerebrales de Qiu et al. 2021 (CC BY), elegidas por tamaño de archivo ≤ 20 MB para no competir
por memoria con las mediciones en curso (todas E11).

## 2. Resultados

### C1 · χ (comprobación de errores) — **se cumple** [HV]

χ de geovida = χ de la referencia en **140 de 140 máscaras**, con conectividad 6 y 26 (120 fantomas y
20 reales). El cálculo topológico de `geovida` queda contrastado con un método independiente.

### C2 · Área frente a la verdad (descriptivo) — la expectativa [HIP] **no se cumple**

Mediana del error relativo absoluto, todas las formas:

| t/h | `area_sdf` (principal) | `area_mc` | `area_faces` | Crofton (referencia) |
|---|---|---|---|---|
| 4 | 3,9 % | 22,1 % | 46,6 % | 2,6 % |
| 6 | 2,0 % | 9,1 % | 49,4 % | 0,8 % |
| 8 | 1,9 % | 4,7 % | 50,1 % | 0,4 % |
| 12 | 2,3 % | 1,9 % | 50,3 % | 0,1 % |
| 16 | 2,7 % | 1,1 % | 49,8 % | 0,3 % |

- **Expectativa fijada:** a t/h ≥ 8, en formas convexas, `area_sdf` y Crofton a ≤ 5 % de la verdad. **No se
  cumple:** máximo 6,0 % (`area_sdf`) y 5,6 % (Crofton), ambos en la misma bola a t/h = 8. En esa máscara el
  **volumen** ya está a −5,3 % de la verdad: el error lo produce la discretización de la propia máscara
  (una bola de 8 vóxeles de diámetro centrada en un vóxel), no el estimador de área [HV]. Se informa como no
  cumplida, tal como se escribió.
- **Hallazgo nuevo [HV]:** `area_sdf` **no converge a la verdad**. Con resolución fina sobreestima entre
  +2,3 % y +3,0 % en todas las formas (cáscara +3,0 %, mancuerna +2,9 %, toro +2,8 %, elipsoide +2,4 %
  a t/h = 16), y su error mediano **crece** de 1,9 % (t/h = 8) a 2,7 % (t/h = 16). `area_mc` y Crofton sí
  convergen (1,1 % y 0,3 % a t/h = 16).
- **Explicación probable [HIP]:** la distancia con signo se calcula desde la máscara binaria, cuya frontera es
  escalonada; el suavizado de 0,5 vóxel no elimina del todo esa rugosidad, y marching cubes la convierte en
  área extra. Con objetos pequeños domina el encogimiento (que `area_sdf` corrige mejor que `area_mc`); con
  objetos grandes domina la rugosidad.
- `area_faces` sobreestima ≈ 50 %, como se esperaba (sesgo conocido de contar caras); Crofton con solo los
  3 ejes equivale a 2/3 de ese conteo.

### C3 · Datos reales (acuerdo, no exactitud)

En 20 máscaras de ventrículos (8760 a 39 875 vóxeles), `area_sdf` difiere de Crofton en una mediana de
**+1,0 %** (de −5,2 % a +2,3 %), y χ coincide en las 20 [HV]. Coherente con el sesgo positivo de `area_sdf`
visto en fantomas, pero con datos reales no hay verdad para decidir cuál está más cerca.

## 3. Consecuencias

1. **Puerta de la fase 4:** χ queda contrastado con un método independiente. El área queda caracterizada
   con un sesgo conocido de `area_sdf` (≈ +3 % a resolución fina). Falta la comparación con una herramienta
   externa establecida (SimpleITK o VTK), que necesita permiso para instalarla [PV].
2. **No se cambia ningún estimador ahora.** `area_sdf` se evaluó y se adoptó en H4 (`docs/RESULTADOS_V02.md`) a
   resoluciones bajas, donde su sesgo es pequeño y menor que el de `area_mc`. Cambiar el estimador principal
   exige un preregistro [PROP]: por ejemplo, evaluar Crofton como estimador principal de área con semillas y
   formas nuevas, y con ruido y desenfoque. Aquí solo se probaron máscaras ideales.
3. **Lo que no se demostró:** nada con imágenes con ruido o desenfoque; nada sobre otras estructuras reales;
   ninguna superioridad general de Crofton (solo este banco ideal).

## 4. Reproducir

```
python scripts/compare_reference.py --out results/summary/reference_comparison
```

Salidas: `results/summary/reference_comparison.json` (resumen), `..._phantoms.csv` y `..._real.csv`
(fila por máscara). Los CSV no se suben a git; el resumen JSON sí.
