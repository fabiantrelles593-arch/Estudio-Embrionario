# Protocolo de revisión de panel (propuesta)

> **Estado: propuesta de trabajo. Este panel no existe todavía y ninguna persona ajena al proyecto ha revisado
> nada.** El documento dice cómo se haría para que cada afirmación del proyecto tenga un nivel de evidencia
> declarado y alguien independiente que la pueda rechazar. Solo investigación y educación.

## 1. Para qué

Hasta ahora el proyecto lo escribió una sola persona con un asistente de IA. Eso es un riesgo de método: los criterios
y los resultados pasaron por las mismas manos. Un panel convierte «confíen en mí» en «aquí está lo que se afirma,
con qué evidencia, y quién intentó refutarlo».

## 2. Composición (mínimo)

| Rol | Qué aporta | Qué puede bloquear |
|---|---|---|
| Embriólogo del desarrollo | ¿El fantoma y los rótulos representan algo biológico? ¿Los estadios se usan bien? | Cualquier afirmación sobre estructuras o estadios |
| Ecografista obstétrico / medicina materno-fetal | ¿Cómo se mide de verdad la CRL y la NT? ¿Qué falla en la práctica? | Cualquier afirmación sobre biometría |
| Bioestadístico | Criterios, tamaños de muestra, intervalos, calibración, múltiples comparaciones | Cualquier veredicto |
| Ingeniería de calidad / asuntos regulatorios | Trazabilidad, gestión de riesgos, uso previsto | Cualquier texto con lenguaje clínico |
| Bioética (o comité de ética de la institución) | Consentimiento, anonimización, base legal | **Todo uso de datos de personas** |
| Persona usuaria o representante de pacientes | ¿Se entiende? ¿Se promete algo que no está? | Texto dirigido al público |

**Independencia.** Nadie del panel es autor del código ni de los informes. Cada persona declara conflictos de interés
(financieros, laborales, de coautoría) por escrito antes de revisar. Quien tenga un conflicto sobre una afirmación no
vota esa afirmación.

## 3. Qué se entrega al panel (paquete versionado)

El repositorio en un commit concreto: `README.md`, los `PREREGISTRO_*` y `RESULTADOS_*`, `ERRATA.md`, el paquete
`docs/clinico/` (uso previsto, riesgos, ficha del modelo, trazabilidad, plan de validación, ciclo de vida), los
resúmenes de `results/summary/` y las instrucciones de reproducción. El acta registra el **hash del commit** revisado.

## 4. Registro de afirmaciones y nivel de evidencia (estado actual)

Niveles definidos en [`ATLAS_ESTADIOS.md`](ATLAS_ESTADIOS.md) §6.

| # | Afirmación | Nivel | Evidencia | Límite declarado |
|---|---|---|---|---|
| C1 | El semáforo de v0.4 (volumen y topología) no da verde falso fuera de lo calibrado | E1 | `RESULTADOS_V04.md` | Ruido gaussiano; fantomas 3D |
| C2 | Recalibrado para ecografía simulada, el certificado de volumen acierta donde da verde | E1 | `RESULTADOS_V05.md` | Apoyada en 2 de 6 estratos; solo un segmentador; topología de la mancuerna falla |
| C3 | Con `smoothed_otsu` dentro de la caja, el certificado de datación y el de decisión tienen falsos verdes de 0.5 % y 1.8 % | E1 | `RESULTADOS_V06.md` (H13a, H13b) | Fantomas 2D; supuestos de moteado y PSF sin validar |
| C4 | La ranura con PSF > 3.5 px **no** es fiable (18.5 % de falsos verdes) | E1, exploratorio | `h13_strata.csv` | Estratificación posterior al preregistro |
| C5 | Una datación certificada no es una datación correcta (domina la variación biológica) | E1 | `RESULTADOS_V06.md` (H13f) | Depende de la fórmula de INTERGROWTH-21st |
| C6 | El certificado transfiere a ecografía real de ratón | **sin evidencia (E2 pendiente)** | `PREREGISTRO_H11.md`, `PREREGISTRO_H12R.md` | No hay volúmenes reales |
| C7 | El proyecto tiene uso clínico | **no se afirma** | `docs/clinico/USO_PREVISTO_Y_RIESGOS.md` | Borrador de ingeniería; ninguna autoridad lo aprobó |

## 5. Formulario de revisión (una hoja por afirmación)

```
Afirmación: C__          Revisor/a: ________   Rol: ________   Fecha: ________
Commit revisado: ________________________
Conflictos de interés declarados: ____________________________

1. ¿La evidencia citada existe y se puede reproducir con las instrucciones?        Sí / No / Parcial
2. ¿El criterio estaba fijado antes de ver el resultado (preregistro con fecha)?   Sí / No / No aplica
3. ¿El nivel de evidencia declarado es correcto?                                   Sí / Debe bajar a __ 
4. ¿El texto afirma algo que la evidencia no sostiene?                              No / Sí: ________
5. ¿Falta un límite o una advertencia?                                              No / Sí: ________
6. Decisión:   ACEPTAR  /  ACEPTAR CON CAMBIOS (listar)  /  RECHAZAR (motivo)
7. Observaciones libres: ______________________________________________
```

## 6. Reglas de decisión (fijadas antes de reunir al panel)

1. Una afirmación **mantiene** su nivel si ninguna persona con rol vinculante la rechaza y la mayoría simple la acepta.
2. **Subir de nivel** (p. ej. de E1 a E2) exige unanimidad de quienes no tienen conflicto, y bioestadística y bioética
   deben haber firmado.
3. Una persona de bioética puede **bloquear** cualquier uso de datos de personas; el bloqueo no se vota.
4. Si hay un rechazo, se publica con el motivo junto a la afirmación; no se borra ni se reescribe en silencio.
5. Un desacuerdo no resuelto se publica como desacuerdo. El proyecto no elige el dictamen que le conviene.
6. Todo cambio posterior que toque una afirmación revisada reabre su revisión.

## 7. Condiciones previas antes de E2 o E3

| Antes de… | Debe existir |
|---|---|
| Procesar volúmenes de animales (E2) | Origen y licencia de los datos; referencia de expertos con ≥ 2 anotadores en un subconjunto; manifiesto validado con `geovida.labeling`; `PREREGISTRO_H11` anotado con cualquier desviación **antes** de calcular acuerdo |
| Procesar cualquier imagen de una persona (E3) | Consentimiento informado documentado (de madre/padre o tutores en el caso de un bebé), anonimización completa (incluido el encabezado de una imagen impresa o exportada), base legal, **aprobación del comité de ética**, acuerdo de uso de datos y firma de bioética |
| Cualquier lenguaje de uso clínico (E4) | Estudio prospectivo preregistrado, comité de ética, gestión de riesgos y autoridad regulatoria; este paquete no los sustituye |

## 8. Salida del panel

Un acta con: commit revisado, lista de revisores y roles (nombres solo con su permiso), conflictos declarados, la hoja
de cada afirmación, las decisiones y los desacuerdos. Se versiona en `docs/panel/` junto al commit que revisó.
