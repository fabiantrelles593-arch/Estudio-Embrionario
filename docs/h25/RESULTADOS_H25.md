# Resultados H25: la luz de H24 con la guardia sin signo de contraste (26 nov 2026)

> Preregistro: `docs/h25/PREREGISTRO_H25.md` (v1.0, aprobado el 26 nov y subido a la rama en `4c22afa`, con el código
> en `938a591`–`4dd72a2`, antes de calcular ninguna luz; CI en verde). Huella del congelado anotada en `38348e5` antes de
> abrir la prueba.
>
> **Datos:** ecografía 3D de alta frecuencia de embriones de ratón (Qiu et al. 2021, IEEE DataPort,
> doi:10.21227/drmd-xq36, CC BY). Nada humano ni clínico.
>
> **Etiquetas:** [HV] verificado · [HIP] hipótesis.

## Veredicto

**Ninguna de las dos primarias da una respuesta.**

- **H25b: no evaluable.** Hubo 19 verdes en 19 embriones, y hacían falta 20 en 15. Entre esas 19 falla 1 (5,3 %), pero
  el preregistro no permite darle un veredicto.
- **H25d: no concluyente.** Las verdes fallan un 5,3 % (1 de 19) y las no verdes un 4,8 % (1 de 21). Δ = −0,5 puntos,
  IC 95 % [−15,0; +13,0]. El IC incluye 0 y su límite superior pasa de 5 puntos.

**La prueba de ventrículo queda usada.** Ningún estudio posterior decidirá con ella (§2 y §9 del preregistro).

## Orden de ejecución [HV]

| Paso | Resultado |
|---|---|
| `check` | Huellas de las redes de H23 correctas |
| G0 (5 casos de ajuste) | Superada: guardia nueva calculable en los 5; idéntica a la antigua en el único caso con C > 0; 10,9–30,3 s por caso |
| Puerta S′ (calibración) | Superada: 29 de 34 con e_b ≤ 0,5 |
| Puerta C′ (calibración) | Superada: 18 verdes, 1 con e_b > 0,5 (5,6 %). Guardia calculable en 34 de 34; dentro del dominio, 30 de 34 |
| Congelado | SHA-256 `91ba4f3dcff06281934e9e07207581db8b8e3c91167202869ac79c9737322f76` |
| `test` (40 casos de 40 embriones) | Corrido una vez con esa huella |

Archivos: `results/h25/` (`g0.json`, `calibrate.json`, `cal_lights.csv`, `h25_frozen.json`, `test_rows.jsonl`,
`test_cases.csv`, `test_verdicts.json`), fuera de git.

## Prueba: secundarias (descriptivas) [HV]

| Medida | Valor |
|---|---|
| H25a: luces | 19 verdes (47,5 %), 17 amarillas, 4 rojas |
| H25c: e_b mediana | 0,20 vóxeles |
| H25c: e_b ≤ 0,5 / ≤ 0,25 | 95 % / 62,5 % |
| H25c: Dice mediano | 0,890 |
| H25c: a ≤ 10 % de volumen (continuidad con H23) | 52,5 % |
| H25e: dentro del dominio (guardia nueva) | 90 % (36 de 40) |
| H25e: verdes sin guardia | 23, de las que falla 1 |
| H25g: fallo en todos los casos («dar verde a todo») | 5 % (2 de 40) |
| H25h: con la guardia antigua | dentro del dominio 22,5 %; 3 verdes, ninguna falla |

Los dos fallos de la prueba son muy distintos:

- uno verde, con e_b = 0,51, justo por encima del límite;
- uno amarillo, con e_b = 2,34 y Dice 0,52, un fallo grosero.

Las 4 rojas tienen e_b ≤ 0,31: ninguna falla.

## Qué significa (§9 del preregistro)

Corresponde a la fila «H25b no evaluable», con H25d no concluyente.

- **La red mide bien el ventrículo en embriones nuevos si el error se mide en vóxeles de borde.** El 95 % de los casos
  queda a menos de medio vóxel. Es el resultado más sólido de H25, aunque secundario.
- **Precisamente por eso, la luz no tiene nada que separar.** Con 2 fallos en 40 casos, «dar verde a todo» falla un
  5 %, y ninguna luz puede mostrar, con 40 casos, que mejora sobre eso.
- **La corrección de la guardia funcionó como se esperaba.** Pasó de admitir el 22,5 % de los casos de prueba al 90 %.
  Como se declaró en §5.3, es una guardia débil: casi no filtra.
- **No se puede decir que la luz separe aciertos de fallos, ni que no los separe.** La pregunta abierta de la línea
  sigue abierta.

## Predicciones frente a resultados

| Predicción | Probabilidad escrita | Resultado |
|---|---|---|
| Pasa G0 | 95 % | Sí |
| Pasa S′ | 99 % | Sí |
| Pasa C′, dado S′ | 80 % | Sí |
| H25b evaluable | 40 % | No (19 verdes, faltó 1) |
| H25b apoyada, si evaluable | 70 % | — |
| H25d evaluable | 90 % | Sí |
| H25d separa, si evaluable | 35 % | No concluyente |

## Qué no se puede concluir

- Que la luz sea segura en ventrículo: 1 de 19 verdes falla, pero H25b no fue evaluable.
- Que la luz no aporte nada: el IC de Δ es demasiado ancho.
- Que la guardia nueva sirva ante imágenes realmente distintas: en este conjunto apenas filtra.
- Nada sobre otros conjuntos o equipos: no es una replicación.
- Nada sobre humanos, hidrocefalia, obstetricia ni uso clínico.

## Lo que aprende la línea [HIP]

Para responder si la luz separa aciertos de fallos hacen falta **fallos**. En ventrículo, con la tolerancia ligada a la
resolución, la red casi no falla. En cuerpo, con el 10 % de H20, tampoco. Con 40 casos y un 5 % de fallos, ninguna
diferencia razonable tendría un IC por encima de 0. Un estudio que quiera responderla necesita:

- muchos más casos;
- o datos donde la red falle más a menudo, por ejemplo otro equipo u otro conjunto.

Ambas cosas apuntan, otra vez, a un segundo conjunto de datos.
