# Replicación de H20: búsqueda de un segundo conjunto

- **Fecha:** 24 de noviembre de 2026
- **Origen:** fila «H20b apoyada» de `docs/h20/PREREGISTRO_H20.md` §7 («replicar con otro conjunto o equipo») y fila
  P2 de `docs/INFORME_DE_PROGRESO.md`.
- **Etiquetas:** [HV] hecho verificado en la fuente primaria · [EI] evidencia indirecta · [PV] pendiente de validación ·
  [PROP] propuesta.
- **Nada descargado.** Solo se leyeron páginas públicas y los metadatos de la API de GitHub.

## 1. Qué tendría que tener el conjunto

Para que sea una replicación de H20 y no otro estudio:

1. Volúmenes de **ecografía 3D**.
2. Una **segmentación de referencia hecha por personas**, para medir el error de volumen.
3. **Licencia verificada** que permita usarlo en investigación.
4. **Otro conjunto o equipo** distinto de Qiu et al. 2021 (IEEE DataPort, doi:10.21227/drmd-xq36), que ya se usó
   entero en H11–H20: 180 casos de cuerpo.
5. Si es humano: anonimizado en origen y con consentimiento o aval ético declarado. Nunca datos identificables
   (`docs/DATOS_REALES_Y_ETICA.md`).

## 2. Búsqueda

- Búsquedas web (24 nov), en extendida y estándar:
  - «3D ultrasound embryo segmentation public dataset manual annotation license zenodo OR figshare»;
  - «high-frequency ultrasound mouse embryo 3D dataset segmentation open access»;
  - «first trimester 3D ultrasound fetus embryo segmentation open dataset CC BY».
- Lectura de las fuentes primarias de los dos candidatos más cercanos.
- **Límite:** no es una búsqueda sistemática. Faltan figshare, Hugging Face y Scopus o Web of Science.

## 3. Candidatos

| Conjunto | Contenido | Referencia | Licencia | Cumple §1 |
|---|---|---|---|---|
| Qiu et al. 2021 (NYU), el de H11–H20 | Ratón E10–E14, ecografía 3D de alta frecuencia, 40 MHz | Cuerpo y ventrículos dibujados por personas [HV] | CC BY [HV] | No cumple el punto 4: es el mismo conjunto. Otro trabajo del grupo describe 370 volúmenes con ventrículo segmentado [EI]; el archivo público trae 180 casos de cuerpo |
| **UterUS** (Boneš et al. 2024, doi:[10.1016/j.compbiomed.2024.108794](https://doi.org/10.1016/j.compbiomed.2024.108794); [GitHub](https://github.com/UL-FRI-LGM/UterUS)) | Humano, útero, ecografía 3D transvaginal. 141 volúmenes anotados y 174 sin anotar, NIfTI-2. Equipos GE y Samsung, varios centros (proyecto NURSE) [HV] | Cavidad uterina a mano. Quién anota, cuántas personas y con qué herramienta: **no declarado en el README** [HV] | **CC BY-NC-SA 4.0** según el README; el repositorio no tiene archivo LICENSE y GitHub no detecta licencia [HV] | Cumple 1, 2 y 4. Licencia: permite investigación no comercial; ShareAlike obliga a la misma licencia si se redistribuyen máscaras derivadas. Ética y consentimiento: **no declarados en el README** [PV] (hay que leer el artículo). **No es un embrión** |
| Rotterdam Periconceptional Cohort (Bastiaansen et al., MELBA 2022, doi:10.59275/j.melba.2022-cb15) | Embrión humano, 8–12 semanas, ecografía 3D Voluson E8/E10 [EI] | 186 segmentaciones [EI] | Datos **no públicos**: el texto de arXiv no ofrece los datos; el código sí es público en GitLab, sin licencia declarada [EI] | No cumple el punto 3 |
| FUSEP (2026) | Primer trimestre humano | Detección de estructuras | Sin comprobar | No cumple el punto 1: es 2D |
| HC18, PSFHS, Fetal Head Biometry | Feto humano | Elipses o máscaras | CC BY 4.0 (HC18) [HV] | No cumplen el punto 1: son 2D |

**Comprobación del artículo de UterUS (24 nov).**

- Según el resumen en PubMed (PMID 38941903, doi:[10.1016/j.compbiomed.2024.108794](https://doi.org/10.1016/j.compbiomed.2024.108794)):
  - la referencia son anotaciones manuales de clínicos expertos [HV];
  - los datos forman parte del estudio multicéntrico NURSE y se publican en el repositorio de GitHub [HV].
- El texto completo no se pudo leer:
  - ScienceDirect devuelve 403;
  - no hay copia en PMC.
- Siguen sin verificar [PV]: el aval ético, el consentimiento, el número de anotadores y el tamaño de vóxel.

## 4. Lectura

**No se encontró ningún conjunto público de ecografía 3D de embriones con referencia manual y licencia verificada
aparte del de Qiu et al. 2021 [EI].** Por eso no existe una replicación directa de H20, con la misma red, la misma
estructura y otro equipo, que se pueda hacer solo con datos abiertos.

Quedan tres caminos, ninguno equivalente a una replicación directa:

| Camino | Qué probaría | Qué hace falta | Coste y riesgos |
|---|---|---|---|
| **A. Pedir al grupo de NYU volúmenes no publicados** (contacto de la página de IEEE DataPort) | Replicación directa: misma estructura y modalidad, embriones nuevos | Tu autorización para escribir en tu nombre y una respuesta del grupo con licencia por escrito | Depende de terceros; puede no llegar nunca |
| **B. Replicación conceptual en UterUS** | Si los observables de H20 (dispersión entre volteos, desacuerdo entre etapas) separan aciertos y fallos **en otro órgano, otra especie y otros equipos**. Se reentrena la misma arquitectura; la red de H19 no sirve en útero | Tu permiso de descarga (unos **640 MB**, el repositorio entero de GitHub); leer antes el artículo para confirmar ética, consentimiento y anotación; preregistro nuevo | Datos humanos públicos y anonimizados en origen, pero el README no declara la ética [PV]. Licencia no comercial. No dice nada sobre embriones |
| **C. Ventrículos cerebrales del mismo conjunto de Qiu** (ya descargado) | Si los observables funcionan en una estructura pequeña del mismo equipo | Preregistro nuevo; sin descargas | **No es otro conjunto ni otro equipo.** Los agregados de H11/H12R ya incluyeron estos casos. Es la evidencia más débil |

## 5. Propuesta [PROP]

1. **A y B en paralelo.** A es la única replicación directa; B es la única que se puede hacer ya, y su resultado se
   presentará como **conceptual**, nunca como replicación de H20.
2. Antes de descargar UterUS:
   - leer el artículo de Boneš et al. 2024 y confirmar aval ético, consentimiento, anonimización y quién anotó;
   - si el artículo no declara aval ético o consentimiento, B se descarta.
   - Hay dos vías para confirmarlo:
     - que tú consigas el texto completo, por acceso institucional o pidiéndolo a la autora;
     - leer el README y el `info.csv` completos del repositorio, que son texto y no requieren descargar los volúmenes.
3. Si B sigue adelante, el preregistro fijará, antes de abrir ningún volumen:
   - reparto por centro, con un centro externo intacto como prueba;
   - umbral de error (10 %);
   - regla verde de H20 sin ajustar: ≤ 5 % y ≤ 10 %;
   - puerta S y puerta C como en H20.

## 6. Decisión del autor y estado (24 nov)

El autor eligió **A y B en paralelo**.

**A. Grupo de NYU.** El borrador del mensaje está en el equipo del autor: lleva datos personales, así que no se sube. Lo envía el autor desde su
correo; Claude no envía mensajes. Estado: pendiente de envío.

**B. UterUS.** El 24 nov se leyeron solo los archivos de texto del repositorio, sin ningún volumen:

- `dataset/info.csv`, 8125 B, 315 filas [HV]:
  - los **141 volúmenes anotados vienen solo de 3 centros**: 04 con 43, 13 con 43 y 22 con 55;
  - los otros 9 centros solo tienen volúmenes sin anotar;
  - equipos: sobre todo GE Voluson (E6, E8, E10, S8, S10, Swift) y Samsung (HS40, HS70, WS80).
- `README.md`: **no menciona** aval ético, consentimiento, anonimización ni quién anotó [HV].

Con la regla de §5, **B queda bloqueado** hasta leer el texto completo del artículo. Si se desbloquea:

- el diseño natural es reservar un centro anotado entero como prueba, con los otros dos para ajuste y calibración;
- son unos 40–55 casos de prueba, parecido a los 44 de H20;
- solo habría 3 centros, lo que limita la generalización.

### Texto completo del artículo de UterUS (24 nov): B descartado

El autor consiguió el PDF. Es un artículo de acceso abierto con licencia CC BY 4.0, de 13 páginas. Se leyó entero; el
PDF se queda en el equipo del autor, fuera del repositorio.

| Punto | Qué dice el artículo [HV] |
|---|---|
| Aval ético | **No lo menciona.** No aparece «ethic», «committee» ni «approval» |
| Consentimiento informado | **No lo menciona.** No aparece «consent» |
| Anonimización | **No la menciona** |
| Anotación | Una sola anotadora que no es profesional sanitaria, formada por un ginecólogo. Las anotaciones las revisó un ginecólogo. 3D Slicer, unos 20 min por volumen. No hubo varias anotadoras ni se midió acuerdo; los autores reconocen el posible sesgo |
| Datos | 298 volúmenes recogidos en centros europeos (estudio NURSE), uno por paciente. Vóxel isótropo de 0,50 mm. 141 anotados y 113 sin anotar, de 11 hospitales. Licencia CC BY-NC-SA 4.0 |

**Decisión: B se descarta**, por la regla de §5 escrita antes de leer el artículo. Son datos de salud de personas
publicados sin aval ético ni consentimiento declarados, y `docs/DATOS_REALES_Y_ETICA.md` no permite usarlos.

Si los autores confirmaran por escrito el aval y el consentimiento, se podría reabrir con un preregistro nuevo. Aun
así, la anotación de una sola persona no experta haría que la referencia fuera más débil que en H20.

**Estado de la replicación de H20:** depende solo del camino A. Si A no prospera, queda el camino C (ventrículos del
mismo conjunto), que es la evidencia más débil y no es una replicación.

## 7. Fuentes

- Qiu et al. 2021, IEEE DataPort: <https://ieee-dataport.org/open-access/ultrasound-mouse-embryo-segmentation-and-classification>
- UterUS: <https://github.com/UL-FRI-LGM/UterUS>; metadatos de la API de GitHub leídos el 24 nov (655 116 KB, sin
  licencia detectada, último push 11 ago 2025).
- Bastiaansen et al.: <https://arxiv.org/abs/2202.06599> (doi:10.48550/arXiv.2202.06599; MELBA doi:10.59275/j.melba.2022-cb15).
- FUSEP: <https://arxiv.org/pdf/2608.04766>
- Boneš et al. 2024 en ScienceDirect: <https://www.sciencedirect.com/science/article/pii/S0010482524008795>
  (Comput Biol Med 178:108794, PMID 38941903, CC BY 4.0).
