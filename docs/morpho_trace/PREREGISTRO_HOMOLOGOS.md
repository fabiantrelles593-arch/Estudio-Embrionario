# Preregistro — MT-C: ¿la diferencia entre atlas se sostiene en los 22 landmarks anatómicos? (23 nov 2026)

> **Aprobado por el autor el 23 nov 2026, tal como estaba escrito el borrador** (decisiones del §0: las propuestas,
> incluida la descarga de D2). Se sube a la rama con su código (`src/geovida/atlas_anchor.py`, sección MT-C;
> `scripts/mtc_homologos.py`) y sus pruebas (`tests/test_mtc_homologos.py`) **antes** de calcular cualquier puerta o
> estimando.
>
> Antecedentes: MT-B (`RESULTADOS_ANCLAJE_ATLAS.md`) encontró, con los 540 puntos, que a lo largo de **d** la
> separación entre E15.5 y E18.5 es la diferencia entre las configuraciones de los dos atlas (r = 0,200, IC
> 0,192–0,212; f_A = 0,997). La búsqueda posterior (`BUSQUEDA_LANDMARKS_INDEPENDIENTES.md`) no encontró landmarks
> manuales de embriones publicados, y mostró que solo 22 de los 540 puntos son landmarks anatómicos homólogos; los
> otros son semilandmarks interpolados sobre 21 triángulos idénticos en los dos atlas [HV].
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta · [PV] pendiente.
> Solo datos animales publicados (MusMorph/IMPC, FaceBase, CC BY 4.0, Devine et al. 2022, *Sci Data* 9:230,
> doi:10.1038/s41597-022-01338-x). Nada humano ni clínico.

## 0. Decisiones del autor (23 nov 2026: se aceptan las cuatro propuestas)

| # | Decisión | Propuesta | Alternativa |
|---|---|---|---|
| D1 | ¿Se hace MT-C? | Sí: minutos, datos ya en disco, sin registro | Pasar directamente a anotación manual (camino B) o a pedir datos a los autores (camino C) |
| D2 | Cómo se comprueba que las filas 1–22 de nuestros `.tag` son los landmarks anatómicos | **Descargar** los dos `.tag` de atlas del repositorio MusMorph en GitHub (unos 37 KB cada uno; repositorio GPL-3.0), guardarlos fuera de git con su SHA-256 y usarlos **solo** para comparar coordenadas (puerta G0-o). Los autores declaran que las primeras 22 filas son las de los landmarks anatómicos | Sin descarga: solo la comprobación geométrica de G0-o(b). Es más débil: puede fallar con un orden correcto o pasar con uno equivocado |
| D3 | Qué landmarks | **Los 22 homólogos** (filas 1–22) en el análisis principal; los 25 (con las filas 23–25, propias de E15.5 y E18.5) como sensibilidad | Los 25 como análisis principal |
| D4 | Nombres de los landmarks en el informe | Leer la Tabla S2 del material suplementario de Devine et al. 2022 (CC BY 4.0), solo para nombrarlos en §6 del informe; no cambia ningún cálculo | Informar los landmarks por número |

## 1. Pregunta y por qué importa

Los 515 semilandmarks de cada atlas se construyen a partir de sus 22 landmarks y de su superficie. Si **d ≈ a** se
debiera a cómo cada superficie reparte los parches, en los 22 landmarks anatómicos la igualdad debería romperse.
Si se mantiene, la diferencia entre atlas está en dónde se colocaron los puntos anatómicos. Para saber si eso es
biología o anotación hace falta una anotación manual independiente (camino B). MT-C dice si el camino B tiene
sentido y en qué landmarks concentrarlo.

**Pregunta MT-C.** Con solo los 22 landmarks homólogos, ¿sigue siendo la separación entre estadios la diferencia
entre los dos atlas? ¿Se concentra esa diferencia en pocos landmarks?

## 2. Datos (todos en disco salvo los dos `.tag` de D2)

| Elemento | Origen | Estado |
|---|---|---|
| Landmarks de los atlas | `data/external/musmorph/atlas/IMPC_E1{5,8}.5_Head_Atlas_Landmarks.tag` (FaceBase), 540 puntos, sin etiquetas por punto | [HV] |
| Configuraciones publicadas | Las 597 de **d** (`results/morpho_trace/v2/seleccion_v2.json`, `confirm`: 199 E15.5, 398 E18.5) | [HV] |
| `.tag` de atlas de GitHub (solo si se aprueba D2) | `jaydevine/MusMorph`, `Postprocessing/Data/Atlases/IMPC_E1{5,8}.5_Head_Atlas_Landmarks.tag` (37 153 y 37 135 B en la API de GitHub; los de FaceBase tienen 540 B más) | [PV] |

**Lo que ya se ha visto (declarado):** todo MT-B con los 540 puntos (§3 de `RESULTADOS_ANCLAJE_ATLAS.md`); las 10
primeras filas del `.tag` de E15.5 (al inspeccionar el formato: las 8 primeras van por pares con x casi simétrica
respecto de x ≈ 6,4 mm y las dos siguientes caen cerca de ese plano, como landmarks bilaterales y medios) [HV]. Es
compatible con que las primeras filas sean los landmarks anatómicos, pero no lo prueba. **Nunca se ha calculado nada con un subconjunto de filas**: ni GPA, ni **d**, ni **a**.

## 3. Protocolo (fijo)

1. **Subconjunto.** Filas 1–22 de cada configuración publicada y de cada atlas (filas 1–25 en la sensibilidad 1).
2. **Espacio de forma, proyección y estimandos:** exactamente los de MT-B (§3 de `PREREGISTRO_ANCLAJE_ATLAS.md`),
   con las funciones de `geovida.atlas_anchor` aplicadas al subconjunto: GPA de las 597, atlas proyectados,
   **d₂₂**, **a₂₂**, e_s, r₂₂ = |d₂₂ − a₂₂| / |d₂₂|.
3. **Por landmark** (en coordenadas tangentes, 3 por landmark): aᵢ y dᵢ, su parte en el cuadrado de la norma,
   cᵢ = |aᵢ|² / |a₂₂|², y la dispersión dentro de estadio sᵢ (raíz de la media de |t(x)ᵢ − t̄ᵢ|² en los dos estadios
   juntos, cada uno respecto de su media).
4. **Incertidumbre:** remuestreo dentro de cada estadio, 2000 réplicas, semilla **20261125**, percentil 95 %, con
   las coordenadas tangentes fijas (como MT-B).

## 4. Hipótesis y criterios (fijos)

* **MT-C1 (primaria) — d ≈ a también en los 22 landmarks homólogos.** Mismo criterio que MT-B1, sobre r₂₂:
  *apoyada* si el límite superior del IC 95 % ≤ 0,25; *refutada* si el inferior ≥ 0,50; *no concluyente* en otro
  caso.
* **MT-C2 (secundaria) — La diferencia entre atlas se concentra.** La suma de cᵢ de los 5 landmarks con mayor cᵢ
  es ≥ 0,50 (con 22 landmarks iguales sería 5/22 ≈ 0,23). Punto estimado; los 5 se eligen con los datos y se
  informan.
* **MT-C3 (descriptiva).** f_A, |a₂₂| / |d₂₂| y ángulo(a₂₂, d₂₂); por landmark, cᵢ, |aᵢ| / sᵢ y ángulo(aᵢ, dᵢ);
  comparación de r₂₂ con el r = 0,200 de MT-B.

## 5. Puertas (en este orden; si una falla, el estudio se para y es no evaluable)

| Puerta | Qué se comprueba | Criterio |
|---|---|---|
| **G0-o** Orden de los landmarks | (a) Si D2 se aprueba: las filas 1–22 de cada `.tag` de FaceBase coinciden con las del `.tag` de GitHub del mismo estadio. (b) Siempre: en cada atlas, las 21 caras de `Patches.tsv` sobre las filas 1–22 son triángulos no degenerados (área > 1·10⁻⁶ mm²). (b) es débil: solo descarta órdenes groseramente equivocados | (a) diferencia máxima ≤ 1·10⁻⁴ mm en las 22 filas de los dos atlas; (b) en los dos atlas. Sin D2, G0-o se decide solo con (b) y el informe lo dirá |
| **G0-p₂₂** Proyección | Como G0-p de MT-B, con 22 filas | ≤ 1·10⁻⁸ |
| **G0-t₂₂** Validez tangente | ρ de cada atlas (22 filas) a la media | ≤ ρ máxima de las 597 a esa media (calculada en el mismo GPA) |

No hay una |d₂₂| de referencia: nunca se ha calculado. Se informa, no se pone a prueba.

## 6. Sensibilidad (declarada; no cambia el veredicto)

1. Filas 1–25 en lugar de 1–22: r₂₅ y concentración.
2. Atlas dentro del GPA (599 configuraciones, 22 filas): r₂₂.
3. GPA rehecho en cada réplica (200): IC de r₂₂.

## 7. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| Pasan las puertas | 85 % |
| MT-C1 apoyada | 55 % |
| MT-C1 refutada | 10 % |
| MT-C2: los 5 primeros llevan ≥ 50 % de \|a₂₂\|² | 50 % |
| r₂₂ mayor que el r de MT-B (0,200) | 60 % |

La última, porque con 22 puntos cada error de colocación pesa más que repartido entre 540 [HIP].

## 8. Qué significará cada resultado (antes de verlo)

| Resultado | Conclusión | Siguiente paso |
|---|---|---|
| MT-C1 apoyada | La diferencia entre atlas está en dónde se colocaron los landmarks anatómicos, no en el reparto de los parches | Camino B (anotación manual independiente), limitado a los landmarks que lleven **a** si MT-C2 se apoya |
| MT-C1 refutada | En los landmarks anatómicos, la separación entre estadios no es la diferencia entre atlas: la igualdad de MT-B depende de los parches | Repetir el análisis de ONTO-MAP con los 22 landmarks (preregistro nuevo) antes de pensar en el camino B |
| No concluyente | Con 22 landmarks no queda acotado | Documentar; el camino B sigue siendo la única salida independiente |
| MT-C2 apoyada / no apoyada | La anotación manual puede concentrarse en pocos landmarks / tiene que cubrir los 22 | Dimensionar el camino B |
| Falla G0-o | No se sabe qué filas son los landmarks anatómicos | No se sigue; se pide al autor decidir entre la Tabla S2, D2 u otra fuente |

## 9. Qué no se puede concluir

* Si **a** es biológica o de anotación: los landmarks de los especímenes siguen saliendo de los atlas.
* Nada sobre los parches más allá de compararlos con los 22 en r.
* Los 5 landmarks de MT-C2 se eligen con los datos: describen, no prueban nada sobre esos landmarks concretos.
* Dos estadios, solo la cabeza, solo ratón; nada sobre humanos ni uso clínico.

## 10. Ejecución

1. Código antes de medir: función de subconjunto y contribución por landmark en `src/geovida/atlas_anchor.py`
   (sin cambiar lo que usó MT-B), `scripts/mtc_homologos.py` (puertas, estimandos, sensibilidad) y pruebas con
   configuraciones sintéticas (subconjunto correcto, cᵢ suman 1, concentración detectada cuando se construye,
   comprobación de orden que falla si se permutan filas).
2. Si D2 se aprueba: descarga de los dos `.tag` a `data/external/musmorph/atlas_github/` con SHA-256, fuera de git.
3. Subir preregistro aprobado, código y pruebas con CI verde. Después, `gates` y `analyze`.
4. Resultados en `docs/morpho_trace/RESULTADOS_HOMOLOGOS.md`; brutos fuera de git en `results/morpho_trace/mtc/`.

## 11. Desviaciones

(Ninguna al subir este preregistro.)

### Notas previas a la subida (no cambian ningún criterio)

* **23 nov 2026 — descarga de D2.** Los dos `.tag` de atlas del repositorio MusMorph (commit `34e3f9e` del archivo
  de E15.5) están en `data/external/musmorph/atlas_github/`, fuera de git: E15.5, 37 153 B, SHA-256
  `e68a80bad69174ffbb4c6f380babad82e39bbc185134416305d59158609bb087`; E18.5, 37 135 B, SHA-256
  `7c348b807cdf7339b27a720d01a73b02b0af2639237ab62f179e3c1bb7639166`. No se han leído ni comparado: eso es G0-o.
* **Las 21 caras de `Patches.tsv`** se copian como constante en `atlas_anchor.PATCH_TRIANGLES` (21 tríos de
  índices, con la fuente citada); no se incorpora nada más del repositorio MusMorph.
