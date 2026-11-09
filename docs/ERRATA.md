# Fe de erratas y errores de verificación

Cada fila es un error real encontrado al verificar el proyecto, con su causa y
lo que se hizo para que no se repita. Las fechas son de 2026.

| # | Fecha | Qué estaba mal | Causa | Corrección | Prevención |
|---|---|---|---|---|---|
| E1 | 09-11 | Dos pruebas de v0.1 con expectativa numérica equivocada (percolación del Otsu crudo; sesgo de +7.7 % del volumen con suavizado) | Escribí el número esperado sin simularlo antes | Se corrigieron las expectativas, no el código, y se documentó la causa física | **Regla:** toda expectativa numérica nueva sale de una corrida piloto que la prueba cita en un comentario |
| E2 | 09-11 | La marca «sucio» del manifiesto de ejecución contaba cambios en `docs/` | Criterio demasiado amplio | `geovida.provenance.git_state`: solo cuenta código versionado (`src`, `scripts`, `pyproject.toml`), con pruebas | Los manifiestos de H1 y H2 conservan el campo viejo (`working_tree_dirty_src_docs`); los nuevos usan `code_dirty` |
| E3 | 09-11 | Un título de figura de v0.1 no correspondía al gráfico | Texto escrito a mano | Corregido antes de publicar | Mirar cada figura renderizada antes de publicarla |
| E4 | 09-11 | Estimación de tiempo del barrido H1 equivocada | No medí un lote piloto | Se mide un lote piloto antes de dimensionar | Piloto de tiempo con réplica descartada (H1, H3) |
| E5 | 09-11 | Token de GitHub inválido al publicar | Credencial caducada | Publicación por el conector | Comprobar el commit en el remoto tras cada push |
| E6 | 09-11 | Un valor no calculable (NaN) se contaba como hipótesis «no apoyada» | Código de veredictos de v0.1 | `tristate_all` y `status_label`: tercer estado «no evaluable» | Los veredictos de H3, H4 y H5 usan el tercer estado desde el diseño |
| E7 | 09-11 | `RESULTADOS.md` decía que H1c en volumen era «no evaluable» | Confundí un caso sin nivel alcanzado (bola con anisotropía 3) con todos | Los datos muestran cocientes finitos de 2.0 en cáscara y tubo (> 1.5): el componente de volumen de H1c **no se cumple**; el de topología sí (≤ 1.5). H1c sigue «parcial» | Los veredictos incluyen ahora el campo `status` generado por código, no escrito a mano |
| E8 | 09-11 | En v0.2, una prueba exigía ±3 % al área SDF de una bola fina | Tolerancia por intuición | El piloto mostraba una asíntota de +3 %: tolerancia 4.5 % con el piloto citado | Misma regla que E1 |
| E9 | 09-11 | Un ayudante de prueba nuevo tenía el mismo nombre que uno existente y rompió cuatro pruebas | Nombre repetido en el mismo archivo | Renombrado | Correr la suite completa antes de cada commit |
| E10 | 09-11 | El área de v0.1 (`area_mc`) tenía sesgo de −64 % a −66 % a 4 vóxeles | Suavizado σ = 1 demasiado fuerte para objetos pequeños | `area_sdf` (v0.2), evaluado de forma preregistrada en H4 | No usar `area_mc` por debajo de ~12 vóxeles; ver `RESULTADOS_V02.md` |

## Lo que NO es una errata

Mis predicciones preregistradas de H1 y H2 que no se cumplieron (3 aciertos de
9) no son errores del código: son resultados. Están en `RESULTADOS.md`.
