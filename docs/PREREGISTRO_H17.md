# Preregistro — H17: ¿cubre la envolvente de referencia la CRL futura observada? (rama de trayectoria; **pendiente de datos reales seriados**)

> Se escribe **antes de tener ningún dato seriado**. Solo investigación y educación. No hay resultados: este documento fija qué se
> mediría, con qué criterios y qué datos hacen falta. No se afirma nada clínico.

## 1. Pregunta

`geovida trajectory` muestra, para una CRL medida, una envolvente que reúne dos escenarios extremos (el feto conserva su puntuación z / la pierde por completo)
construida con las ecuaciones poblacionales de INTERGROWTH-21st. Esos dos escenarios son **supuestos**: la correlación entre el tamaño de una visita y el de la siguiente no se conoce.

> En embarazos reales con dos o más medidas de CRL separadas por 1 a 4 semanas, ¿la CRL de la visita posterior cae dentro de la envolvente
> calculada con la medida de la primera visita en al menos el 90 % de los casos?, y ¿qué tan ancha resulta frente a la franja poblacional sin condicionar?

## 2. Datos que hacen falta (no están)

* Embarazos con **≥ 2 medidas de CRL** entre los 58 y 105 días, separadas por 7 a 28 días, con **edad cierta por otra vía** (fecha de última regla confirmada o fecundación asistida) para no dar la edad con la propia CRL.
* Cada medida con operador y protocolo conocidos (idealmente estandarizados); la unidad de análisis es el **embarazo**, no la medida.
* **Fuente de datos no identificada ni licencia verificada.** Los datos seriados de INTERGROWTH-21st no se han obtenido ni se sabe si son accesibles. Con datos de personas rigen `docs/DATOS_REALES_Y_ETICA.md`
  y `docs/RUTA_DE_VALIDACION_REAL.md` (consentimiento, anonimización, aprobación ética). **Mientras eso no exista, H17 no se evalúa.**

## 3. Diseño (fijo)

Para cada embarazo y cada par de visitas (la primera como origen), se calcula la envolvente de `geovida trajectory` con la **edad conocida** (`--ga-days`), la CRL de la primera visita y un error relativo
de medida declarado de antemano (SD 2 %), a la distancia en días real hasta la segunda visita. Se anota si la CRL de la segunda visita cae dentro. Un par por embarazo (el de la primera y la última visita elegibles) para evitar dependencia.
Intervalos de Clopper–Pearson al 95 %. Remuestreo por embarazo (2 000 réplicas, semilla 20261219) para lo descriptivo.

## 4. Hipótesis y criterios (fijos)

* **H17a — Primaria. Cobertura de la envolvente ≥ 90 %.** *Apoyada* si la cobertura observada es ≥ 90 % y el límite inferior del IC 95 % ≥ 85 %; *no apoyada* si el límite superior < 90 %;
  *no concluyente* en el resto; *no evaluable* con menos de 70 embarazos.
* **H17b — Descriptiva (sin criterio): ρ.** Correlación entre las puntuaciones z de la primera y la segunda visita (con la edad cierta), con IC por remuestreo por embarazo. Si ρ ≈ 1 el escenario «persistencia» basta; si ρ ≈ 0, el de «regresión».
* **H17c — Utilidad.** Razón entre el ancho de la envolvente y el de la franja poblacional del 90 % sin condicionar, a +14 días. Si es ≥ 1 la envolvente no aporta nada sobre la referencia; se informa, no se interpreta como éxito.
* **Exploratorio:** cobertura por horizonte (7, 14, 21, 28 días) y por tercil de la CRL de la primera visita.

## 5. Tamaños de muestra (Clopper–Pearson 95 %, dos colas)

| Embarazos | Cobertura observada 90 % | 93 % | 95 % |
|---|---|---|---|
| 100 | 82.4–95.1 % | 86.1–97.1 % | 88.7–98.4 % |
| 200 | 85.0–93.8 % | 88.5–96.1 % | 91.0–97.6 % |
| 300 | 86.0–93.2 % | 89.5–95.6 % | 91.9–97.2 % |

Con una cobertura observada de 93 % bastan 75 embarazos para que el límite inferior llegue a 85 %; con 90 % observado, ni 300 lo alcanzan con holgura: **una cobertura justo en el límite no se podrá declarar apoyada con muestras pequeñas**.

## 6. Qué se hace según el resultado (decidido de antemano)

| Resultado | Qué se concluye | Siguiente paso |
|---|---|---|
| H17a apoyada | La envolvente cumple lo que declara en esos datos (la envolvente es la unión de dos extremos: se espera que sea conservadora). | Mirar H17c: si la envolvente es casi tan ancha como la franja poblacional, no justifica la rama. |
| H17a no apoyada | La envolvente no cubre: el modelo de los dos extremos es insuficiente. | Estimar la dispersión con los datos (H17b) en vez de usar los extremos. |
| H17a no concluyente | Faltan embarazos. | Más datos, no cambiar criterios. |

## 7. Predicciones escritas de antemano

| Predicción | Probabilidad |
|---|---|
| H17a **apoyada** (si se llegara a evaluar) | 80 % |
| ρ entre 0.5 y 0.9 | 60 % |
| Envolvente más estrecha que la franja poblacional del 90 % a +14 días (H17c < 1) | 25 % |

## 8. Qué no se puede concluir

* Con cualquier resultado, nada sobre el crecimiento de un feto en particular ni sobre su aspecto, rasgos o salud.
* La envolvente es de referencia poblacional; que cubra en una muestra no la vuelve una predicción individual.
* El tamaño de la CRL depende del operador y la técnica: la cobertura vale para el protocolo de los datos usados.

## 9. Desviaciones

(Ninguna: no hay datos.)
