# ONTO-MAP — Evaluación de la hipótesis y protocolo del piloto P4 (15 nov 2026)

> **Estado:** fijado por el asistente con la autoridad delegada por el autor (15 nov 2026), **antes de descargar los landmarks del piloto**. Solo se miraron 2 archivos de landmarks, para comprobar el formato (§3). Pendiente: revisión del asesor.
> Solo investigación; datos animales publicados (CC BY 4.0); sin datos humanos ni clínicos.
> Etiquetas: [HV] verificado · [EI] evidencia indirecta · [HIP] hipótesis · [PROP] propuesta · [PV] pendiente de validación.

## 1. Qué cambia con el mandato v2.0

| Punto del mandato | Situación en el repositorio | Decisión |
|---|---|---|
| ONTO-MAP (nuevo, §6) | No existía | Este documento, más `src/geovida/landmarks.py` como primer incremento |
| MORPHO-TRACE como marco de estabilidad y trazabilidad (§5) | Ya es así: P3 descompone la variación en técnica y del espécimen (`docs/PREREGISTRO_P3.md`) y la procedencia se registra con `geovida.manifest` y `geovida.provenance` [HV] | Se mantiene. ONTO-MAP usa sus resultados, no los duplica (§6) |
| Arquitectura `src/geometria_vida/...` (§9) | El paquete canónico es `src/geovida/` (ADR-001) [HV] | No se renombra: se cambiarían todas las importaciones sin ganancia científica. Se adopta la separación por responsabilidades **dentro** de `geovida` (`landmarks` = morfometría geométrica, `p3_data` = datos, `minc` = lectura) |
| Matriz de validación de 6 niveles (§10–11) | Hay 3 niveles en `docs/clinico/TRAZABILIDAD.md` (software, imagen, biología) | Cada módulo nuevo declara su nivel. `landmarks`: nivel 1–3 (matemático, computacional, sintético) y comparación con SciPy (nivel 5 parcial). Sin validación biológica |
| Prioridades P0–P3 (§19) | El roadmap usa fases | Se etiqueta el roadmap con P0–P3 en §8 |

## 2. Antecedentes: la H1 de ONTO-MAP tal como está escrita no es original

Búsquedas en PubMed (15 nov 2026), verificadas por PMID y DOI [HV]:

| Trabajo | Qué establece | Consecuencia para ONTO-MAP |
|---|---|---|
| Adams y Collyer 2009, *Evolution* 63:1143 ([doi:10.1111/j.1558-5646.2009.00649.x](https://doi.org/10.1111/j.1558-5646.2009.00649.x)) | Análisis de trayectorias fenotípicas: tamaño, dirección y forma de trayectorias en un espacio multivariado, con pruebas de permutación. Cita la ontogenia como aplicación | «Representar el desarrollo como trayectorias en un espacio multivariado» es metodología establecida |
| Mitteroecker et al. 2004, *J Hum Evol* 46:679 ([doi:10.1016/j.jhevol.2004.03.006](https://doi.org/10.1016/j.jhevol.2004.03.006)) y *Ann Anat* 186:463 ([doi:10.1016/S0940-9602(04)80085-2](https://doi.org/10.1016/S0940-9602(04)80085-2)) | Trayectorias ontogenéticas en espacio de forma y de tamaño-forma, con landmarks y semilandmarks | La comparación de trayectorias ontogenéticas con morfometría geométrica está resuelta |
| Musy et al. 2018, *Development* 145:dev154856 ([doi:10.1242/dev.154856](https://doi.org/10.1242/dev.154856)) | Trayectoria ontogenética estándar del brote de miembro de ratón (E10–E15) y estimación del estadio a partir de la forma, con unos 2 h de incertidumbre (eMOSS) | En ratón ya existe una trayectoria ontogenética estándar basada en la forma |
| Amézquita et al. 2020, *Dev Dyn* 249:816 ([doi:10.1002/dvdy.175](https://doi.org/10.1002/dvdy.175)) | Revisión de TDA en biología, incluido el desarrollo | La topología persistente aplicada a la forma tampoco es nueva por sí misma |

**Conclusión.** H1, H1a y H1c describen métodos conocidos. ONTO-MAP solo puede aportar algo en una pregunta concreta que esos trabajos no respondan [HIP]. La revisión formal de originalidad (§8.3 del mandato) sigue pendiente [PV]: estas cuatro referencias son un punto de partida, no una revisión sistemática.

## 3. Datos: qué se comprobó

| Hecho | Evidencia |
|---|---|
| MusMorph (IMPC) tiene silvestres C57BL/6N con sexo conocido: 309 en E15.5 (144 hembras, 165 machos) y 510 en E18.5 (260 y 250) | `MusMorph_Metadata_Mar2024.csv` [HV] |
| Hay landmarks de cabeza `<ID>_Head_Landmarks.tag` para 1202 archivos de E15.5 y 1483 de E18.5 en FaceBase (registro 3-JZA6, CC BY 4.0) | Catálogo ERMrest de FaceBase [HV] |
| E18.5 **no tiene** segmentaciones en FaceBase (0 archivos `_Segs`) | Catálogo [HV] |
| Cada archivo tiene **540** puntos en mm (formato MNI Tag), derivados del registro no lineal con un atlas **distinto por estadio** (E14.5-15.5 y E18.5, según la cabecera) | `IMPC_E15.5_0040` e `IMPC_E18.5_0001`, MD5 correcto [HV] |
| El punto *i* corresponde entre los dos atlas: ρ de Procrustes = 0,170 con el orden dado, frente a un mínimo de 1,46 en 200 órdenes barajados | `geovida.landmarks.correspondence_check` sobre esos 2 archivos [HV en 1 par; EI para el conjunto] |
| El atlas de E15.5 se llama «E14.5-15.5»: el grupo E15.5 puede mezclar madurez | Cabecera del `.tag` [HV]; magnitud de la mezcla [PV] |
| Matula 2021 (CC0): 1 cabeza por edad, de E12.5 a E18.5 | `docs/estado_del_arte/FICHAS_REFERENTES.md` [HV] → sirve para describir, no para medir la variación entre especímenes |

## 4. Pregunta reformulada

> **¿La variación de forma asociada al tamaño *dentro* de un estadio (alometría estática, que refleja en parte diferencias de madurez) apunta en la misma dirección que el cambio de forma *entre* estadios (E15.5 → E18.5)?**

Si apunta en la misma dirección, la variación dentro del estadio está organizada a lo largo de la trayectoria ontogenética, y la posición de un espécimen sobre esa dirección sirve como reloj morfológico continuo dentro de un estadio. Si no, el cambio entre estadios no es una prolongación de la variación dentro del estadio.

Por qué no está respondida por §2: eMOSS construye la trayectoria con muchos estadios de un solo órgano en 2D. Aquí se pregunta, con 540 landmarks 3D de la cabeza y cientos de especímenes por estadio, si la variación **dentro** del estadio se alinea con la trayectoria **entre** estadios, cuantificando la incertidumbre por espécimen [HIP; la originalidad sigue PV].

## 5. Hipótesis y criterios (fijados ahora)

Sea **a15** la alometría estática de E15.5 (pendiente de la forma tangente sobre log CS), **a18** la de E18.5 y **d** el vector entre las formas medias (E18.5 − E15.5), todo en el mismo espacio tangente (GPA conjunta de los dos estadios). Los ángulos se miden con signo (`angle_deg`, de 0° a 180°). Intervalos: remuestreo por espécimen dentro de cada estadio, 2000 réplicas, semilla 20261116.

- **H-O1, primaria [HIP]: θ(a15, d) < 45°.** *Apoyada* si el límite superior del IC 95 % < 45°. *Contraria* si el límite inferior > 60°. *No concluyente* en el resto. Como referencia se informa el cuantil 1 % del ángulo entre rectas al azar en la dimensión efectiva (componentes con el 95 % de la varianza).
- **H-O2, secundaria [HIP]: θ(a18, d) < 45°**, con los mismos criterios.
- **H-O3, secundaria [HIP]: θ(a15, a18) < 45°.** La alometría estática se conserva entre estadios.
- **Descriptivo, sin criterio:** CS por estadio y sexo; varianza de forma por estadio; número de componentes para el 95 %; ρ máxima a la media (validez del espacio tangente).
- **Exploratorio:** por sexo; repetición con el tamaño de centroide eliminado por regresión; posición de cada espécimen de E15.5 sobre **d** frente a su CS.

## 6. Diseño (fijado ahora)

- **Unidad experimental:** el espécimen. Un archivo de landmarks por espécimen; nunca se reparten puntos o réplicas de un espécimen entre análisis.
- **Elegibles:** silvestres C57BL/6N de IMPC con sexo conocido y archivo de landmarks.
- **Piloto:** 20 por estadio (10 + 10), al azar con la semilla 20261116. Sirve solo para comprobar el flujo, y no entra en el confirmatorio.
- **Confirmatorio:** todos los elegibles restantes. Los archivos pesan unos 38 kB, así que no hace falta muestrear. Los especímenes de E15.5 de P3 (piloto y confirmatorio) **no se excluyen**: P3 no usa landmarks.
- **Comprobaciones previas, que pueden detener el estudio:**
  1. La correspondencia (`correspondence_check`) se cumple en ≥ 95 % de los pares del piloto, contra la media del otro estadio.
  2. La GPA converge.
  3. La ρ máxima a la media es < 0,3 (el espacio tangente es válido).
  4. Ningún archivo tiene un número de puntos distinto de 540.
- **Factores de confusión declarados:**
  - (i) Cada estadio tiene su atlas, así que **d** mezcla el cambio biológico con las diferencias entre atlas. No se puede separar con estos datos: es una limitación de H-O1 y H-O2, no de H-O3.
  - (ii) Si el error del registro depende del tamaño, podría crear una alometría artificial.
  - (iii) El origen de los especímenes (camada, fecha) no está en los metadatos.
- **Manifiesto:** SHA-256 de cada archivo descargado (`python -m geovida.manifest build`), antes de analizar.

## 7. Qué no se podrá concluir

- Con dos estadios, **d** es un segmento y no una curva: no hay «forma de trayectoria» (en el sentido de Adams y Collyer) que estimar.
- Son datos transversales. La posición sobre **d** es un pseudotiempo, no seguimiento longitudinal (§4.3 del mandato).
- Los landmarks proceden de un registro automático, no de anotación experta. Su error frente a una referencia manual no se conoce [PV].
- No dice nada sobre otros órganos, especies ni humanos, y nada clínico.

## 8. Roadmap con prioridades (mandato v2.0, §19)

| Prioridad | Tarea | Criterio de aceptación |
|---|---|---|
| P0 | Cerrar las comprobaciones 3.3 y 3.4 de P3 (MEMOS en los 20 del piloto) y la comparación con el atlas (D3) | `results/p3/memos/memos_run.json` con ≥ 18/20 correctos; informe actualizado |
| P1 | `geovida.landmarks` (lectura `.tag`, GPA, distancias, alometría, ángulos) | Pruebas sintéticas y comparación con `scipy.spatial.procrustes`. **Hecho en este incremento** |
| P1 | Piloto de ONTO-MAP: descargar los 40 `.tag`, manifiesto y comprobaciones previas de §6 | Las 4 comprobaciones registradas |
| P1 | Análisis de §5 en el confirmatorio, con IC por remuestreo | Informe con los veredictos fijados en §5 |
| P2 | P3 confirmatorio (decidido por la regla de ampliación del preregistro) | Según `docs/PREREGISTRO_P3.md` |
| P2 | Revisión formal de originalidad de ONTO-MAP (§8.3 del mandato) | Búsqueda documentada en PubMed, Europe PMC y OpenAlex |
| P3 | Topología persistente de las superficies (línea A del mandato) | Solo si P3 o ONTO-MAP muestran una necesidad que la morfometría no cubra |
| P3 | Línea prenatal | Sin datos autorizados ni supervisión clínica: no se inicia |
