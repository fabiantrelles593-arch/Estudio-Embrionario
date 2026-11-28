# Reglas comunes para preregistros nuevos (desde el 26 nov 2026)

> **Qué es:** reglas que todo preregistro nuevo debe incluir o justificar si se aparta de ellas. Recogen lo que ya se
> hizo en H18–H25 y lo aprendido después. **No cambian ningún estudio cerrado.** Cada preregistro sigue necesitando la
> aprobación del autor antes de medir.

## 1. Protocolo (lo que ya se hacía)

1. El preregistro, el código y sus pruebas se suben a la rama, con CI en verde, **antes** de calcular la cantidad
   que decide.
2. Puertas antes de la prueba (G0, calibración). Si una puerta no se supera, la prueba no se abre.
3. Los parámetros se congelan y su SHA-256 se anota en el preregistro **antes** de abrir la prueba. La orden `test`
   comprueba esa huella.
4. Una prueba sellada se abre **una sola vez**. Después queda usada y ningún estudio posterior decide con ella.
5. Tres estados por hipótesis: apoyada, no apoyada (o «separa», «no separa») y **no evaluable / no concluyente**.
   Un valor no calculable nunca cuenta como «no apoyada».
6. Las predicciones se escriben con su probabilidad antes de medir y se comparan con el resultado al cerrar.
7. Toda desviación se anota con fecha en el preregistro y la aprueba el autor antes de medir lo afectado.

## 2. Hipótesis de separación (nueva)

Se aplica a toda hipótesis del tipo «¿fallan más los casos no verdes que los verdes?» (como H20d–H25d).

**Regla S-1. Evaluabilidad por fallos.** La hipótesis solo es evaluable si:

- hay al menos **5 verdes y 5 no verdes** (como hasta ahora); y
- hay al menos **10 fallos en total** y **al menos 1 fallo en cada grupo** (verdes y no verdes).

Si no se cumple, la hipótesis es **no evaluable** y no se informa ningún veredicto de separación, solo los
descriptivos.

*Por qué.* Con pocos fallos, el bootstrap de percentiles da un IC degenerado. Con 40 casos y sin separación real, la
regla de H25d concluía «no separa» en el 35 % de las simulaciones, casi siempre cuando no había ningún fallo entre los
no verdes (`docs/h25/TAMANO_MUESTRAL_SEPARACION.md`, §4).

**Regla S-2. Tamaño planificado.** El preregistro declara la tasa de fallo esperada y el número de casos, y justifica
que los fallos esperados sean al menos 25. Con menos, debe decir de antemano que lo más probable es «no concluyente».
Las cifras de referencia están en la nota de tamaño muestral (§3).

**Regla S-3. IC.** Se mantiene el bootstrap por embrión (percentiles, 2000 réplicas), con el umbral de «no separa»
declarado en puntos.

## 3. Cómo se usa

Al escribir un preregistro nuevo, copiar las reglas que apliquen en su sección de criterios, o citar este documento
con el número de la regla (por ejemplo, «S-1 de `docs/REGLAS_PREREGISTRO.md`»). Cambiar una regla exige editar este
documento con fecha y motivo, y la aprobación del autor.
