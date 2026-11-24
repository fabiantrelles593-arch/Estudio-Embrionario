# Búsqueda de landmarks independientes de los atlas para E15.5 y E18.5 (23 nov 2026)

> Paso propuesto en `RESULTADOS_ANCLAJE_ATLAS.md` §7. Solo lectura de publicaciones y de metadatos públicos; **no se
> ha descargado ningún dato ni se ha calculado nada**. Etiquetas: [HV] verificado · [EI] evidencia indirecta ·
> [HIP] hipótesis · [PROP] propuesta · [PV] pendiente.

## 1. Pregunta

¿Existen landmarks de cabeza de ratón de E15.5 y E18.5 colocados a mano (sin pasar por los atlas de MusMorph),
publicados y con licencia clara, que permitan separar la parte biológica de la parte de anotación en la diferencia
entre atlas que encontró MT-B?

## 2. Respuesta corta

**No se ha encontrado ninguno.** Pero la búsqueda deja dos hechos útiles sobre los propios landmarks de MusMorph
(§4), que permiten una pregunta intermedia sin descargar nada (§5).

## 3. Qué se miró

| Fuente | Qué contiene | ¿Sirve? |
|---|---|---|
| Devine et al. 2022, MusMorph (doi:10.1038/s41597-022-01338-x), «Methods» y «Technical Validation» | Validaron los landmarks automáticos contra manuales **solo en adultos**: «that was the only stage with a large existing set of homologous manual landmarks» | No hay manuales de embriones [HV] |
| Percival et al. 2014, *BMC Dev Biol* 14:31 (doi:10.1186/1471-213X-14-31) | Conjunto estándar de landmarks faciales de superficie y su error intra e interobservador | Solo E10.5–E12.5 [HV]. Útil como modelo de protocolo de error |
| Matula et al. 2021, *GigaScience* 10:giab012 (doi:10.1093/gigascience/giab012) | 7 cabezas de E12.5 a E18.5 en µCT, con máscaras manuales de la cápsula nasal | Un espécimen por estadio y sin landmarks [HV]. No sirve para medias de estadio |
| Ho et al. 2015, *Dev Biol* 400:180 (doi:10.1016/j.ydbio.2015.02.010) | Landmarks óseos y volúmenes en E18.5 | Solo E18.5, mutantes y controles; no consta depósito de coordenadas [PV] |
| Percival et al. 2014, *Dev Dyn* 243:541 (doi:10.1002/dvdy.24095) | Volumen y densidad ósea prenatal (Fgfr2 P253R) | Segmentación, no landmarks [HV] |
| Laboratorio de Richtsmeier, *eLife* 2022 (doi:10.7554/eLife.76653) | Condrocráneo E13.5–E17.5 reconstruido por µCT | Segmentaciones, sin landmarks publicados en lo encontrado [EI] |
| FaceBase (búsqueda general) | MusMorph (doi:10.25550/3-HXMC) | Sus landmarks son los propagados desde los atlas |

Búsquedas en PubMed y en la web el 23 nov 2026. Una búsqueda negativa no prueba que no existan: puede haber
conjuntos sin publicar en laboratorios (p. ej. el de Hallgrímsson, que anota embriones a mano) [EI].

## 4. Lo que la búsqueda aclara sobre los landmarks de MusMorph

1. **De los 540 puntos, solo 22 son landmarks anatómicos homólogos** (más 3 específicos de E15.5 y E18.5, filas
   23–25); el resto son **semilandmarks de parche interpolados** entre ellos. Los autores los llaman «equivalentes»
   y no homólogos, «because the developmental origin of dense tissue regions between fixed landmarks is more
   ambiguous» (Devine et al. 2022, «Data Records: Landmarks»; definiciones en su Tabla S2) [HV].
2. **Los parches se construyen igual en los dos atlas.** Los archivos `IMPC_E15.5_Head_Atlas_Patches.tsv` y
   `IMPC_E18.5_Head_Atlas_Patches.tsv` del repositorio MusMorph (GitHub, GPL-3.0; solo leídos, no incorporados)
   definen los mismos 21 triángulos sobre los landmarks 1–22 [HV]. Los 515 semilandmarks de cada atlas salen, por
   tanto, de sus 22 landmarks y de la superficie de la cabeza; no son anotaciones independientes punto a punto [HIP].
3. **Los dos atlas no se hicieron igual.** El de E15.5 es un atlas previo (el de MICe/Toronto, con 48 estructuras
   segmentadas a mano) y el de E18.5 lo construyó MusMorph; las imágenes de E15.5 tienen 0,027 mm de vóxel y las de
   E18.5, 0,054 mm [HV, Tabla 1 y «Reference atlases»]. Es una fuente posible de diferencias técnicas entre atlas
   [HIP].

Consecuencia: la diferencia **a** de MT-B se decide sobre todo en dónde se colocaron 22 + 3 puntos en cada atlas, y
en cómo cada superficie reparte los parches. MT-B la midió con los 540 a la vez.

## 5. Caminos posibles (decisión del autor; nada ejecutado)

| Camino | Qué responde | Coste | Limitación |
|---|---|---|---|
| **A. MT-C: MT-B restringido a los 22 landmarks homólogos** [PROP] | Si la diferencia entre atlas (y d ≈ a) se sostiene en los puntos anatómicos definidos, o vive en los parches. Además, qué landmarks concretos llevan **a**, comparado con la variación dentro de cada estadio | Minutos; datos ya en disco; preregistro nuevo | Los landmarks de los especímenes siguen saliendo de los atlas: no separa del todo biología y anotación. Hay que comprobar antes que el orden de los `.tag` de FaceBase es el de la Tabla S2 [PV] |
| B. Anotación manual nueva | Landmarks independientes de verdad: los 22 de la Tabla S2 en una muestra pequeña de cada estadio, por una persona con formación, con error intra-observador medido como en Percival 2014 | Horas de anotación experta | No se puede hacer aquí: exige un anotador humano; los landmarks no se pueden inventar |
| C. Pedir datos a los autores | Landmarks manuales de embriones que pudieran existir sin publicar | Un correo del autor del proyecto | Comunicación externa: solo el autor puede decidirla y enviarla |

[PROP] A primero: es barato, no depende de nadie y dice si merece la pena B. Si la diferencia entre atlas se
concentra en pocos landmarks homólogos, B puede limitarse a esos.

## 6. Qué no se puede concluir de esta búsqueda

* Que no existan landmarks manuales de E15.5 o E18.5: solo que no se han encontrado publicados.
* Nada sobre si **a** es biológica o técnica.
