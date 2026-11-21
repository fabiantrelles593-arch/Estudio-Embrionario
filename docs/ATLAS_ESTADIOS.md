# Atlas de estadios del desarrollo embrionario humano, rotulado y niveles de evidencia

> Solo investigación y educación. Este documento **no** es una guía clínica ni de diagnóstico. La tabla de
> estadios sale de `geovida.atlas`; una prueba (`tests/test_atlas_doc.py`) impide que documento y módulo se
> separen.

## 1. Para qué sirve

El estudio del desarrollo embrionario avanza por fases: **blástula → gástrula → neurulación → órganos y estructuras
finales**, y en cada una hay que decir qué se midió, con qué rótulo, con qué evidencia y quién lo revisó. Este
atlas fija el vocabulario común (estadio de Carnegie, edad, longitud) para que los manifiestos de anotación
(`geovida.labeling`), los certificados de medida (`geovida.dating`, `geovida.biometry`) y la revisión de panel
([`PANEL_DE_REVISION.md`](PANEL_DE_REVISION.md)) hablen de lo mismo.

## 2. Fuente y base de edad

* Fuente: UNSW Embryology, «Carnegie stage table» (Dr. Mark Hill, última modificación 21-12-2017), basada en
  George L. Streeter, *Developmental Horizons in Human Embryos* (Carnegie Institution of Washington, 1942–1957).
* La edad es **embrionaria, en días post ovulación**. La edad gestacional clínica (desde la última menstruación) es
  esa edad **+ 14 días**.
* Los rangos de edad y de longitud **se solapan** entre estadios vecinos: el desarrollo varía entre embriones. Una
  edad o una longitud puede corresponder a más de un estadio.
* **Límite**: las edades y longitudes se transcribieron de la tabla. Los rasgos de la última columna son paráfrasis
  breves y orientativas que no se comprobaron una por una contra la fuente; consulte la fuente antes de citar un rasgo.
  La asignación de **fase** (columna 5) es una agrupación de trabajo de este proyecto, no una definición de la fuente.
* Las longitudes de la tabla no son comparables 1:1 con una longitud cráneo-rabadilla medida por ecografía in vivo;
  aquí no se afirma esa equivalencia.

## 3. Tabla de los 23 estadios

| Estadio | Edad embrionaria (días) | Edad gestacional clínica (días) | Longitud (mm) | Fase (agrupación de trabajo) | Rasgos (orientativo) |
|---|---|---|---|---|---|
| 1 | 1 | 15 | 0.1–0.15 | Blástula / blastocisto | cigoto con dos pronúcleos |
| 2 | 2–3 | 16–17 | 0.1–0.2 | Blástula / blastocisto | mórula; se forma el blastocisto con masa interna y externa |
| 3 | 4–5 | 18–19 | 0.1–0.2 | Blástula / blastocisto | se pierde la zona pelúcida; blastocisto libre |
| 4 | 5–6 | 19–20 | 0.1–0.2 | Blástula / blastocisto | el blastocisto se adhiere a la pared uterina |
| 5 | 7–12 | 21–26 | 0.1–0.2 | Blástula / blastocisto | implantación |
| 6 | 13–15 | 27–29 | 0.2 | Gástrula | mesodermo extraembrionario, línea primitiva; empieza la gastrulación |
| 7 | 15–17 | 29–31 | 0.4 | Gástrula | gastrulación; proceso notocordal |
| 8 | 17–19 | 31–33 | 1–1.5 | Gástrula | fosita primitiva; canal notocordal |
| 9 | 19–21 | 33–35 | 1.5–2.5 | Neurulación | somitas 1–3; pliegues neurales, primordio cardiaco, pliegue cefálico |
| 10 | 22–23 | 36–37 | 2–3.5 | Neurulación | somitas 4–12; fusión de los pliegues neurales |
| 11 | 23–26 | 37–40 | 2.5–4.5 | Neurulación | somitas 13–20; se cierra el neuroporo rostral |
| 12 | 26–30 | 40–44 | 3–5 | Neurulación | somitas 21–29; se cierra el neuroporo caudal |
| 13 | 28–32 | 42–46 | 4–6 | Organogénesis | 30 somitas; brotes de las piernas, placoda del cristalino, arcos faríngeos |
| 14 | 31–35 | 45–49 | 5–7 | Organogénesis | fosita del cristalino; copa óptica |
| 15 | 35–38 | 49–52 | 7–9 | Organogénesis | vesícula del cristalino; fosita nasal; placa de la mano |
| 16 | 37–42 | 51–56 | 8–11 | Organogénesis | las fosas nasales se mueven ventralmente; montículos auriculares; placa del pie |
| 17 | 42–44 | 56–58 | 11–14 | Organogénesis | radios de los dedos |
| 18 | 44–48 | 58–62 | 13–17 | Organogénesis | comienza la osificación |
| 19 | 48–51 | 62–65 | 16–18 | Organogénesis | el tronco se endereza |
| 20 | 51–53 | 65–67 | 18–22 | Organogénesis | miembros superiores más largos, codos doblados |
| 21 | 53–54 | 67–68 | 22–24 | Organogénesis | manos y pies girados hacia dentro |
| 22 | 54–56 | 68–70 | 23–28 | Organogénesis | se forman los párpados y las orejas externas |
| 23 | 56–60 | 70–74 | 27–31 | Organogénesis | cabeza redondeada; cuerpo y extremidades |

## 4. Qué resolución haría falta (aritmética, no resultado)

Cuántos vóxeles caben a lo largo de la longitud: el calibrado de H13 cubre de 50 a 300 píxeles a lo largo de una
cápsula. Para tener al menos 50 vóxeles a lo largo de la **longitud mínima** de un estadio hace falta un vóxel de
la tercera columna; la cuarta es cuántos vóxeles hay con un vóxel de 0.1 mm.

| Estadio | Longitud (mm) | Vóxel para 50 vóxeles (mm) | Vóxeles con vóxel de 0.1 mm |
|---|---|---|---|
| CS1 | 0.1–0.15 | 0.002 | 1 |
| CS5 | 0.1–0.2 | 0.002 | 1 |
| CS9 | 1.5–2.5 | 0.03 | 15 |
| CS12 | 3–5 | 0.06 | 30 |
| CS14 | 5–7 | 0.1 | 50 |
| CS17 | 11–14 | 0.22 | 110 |
| CS20 | 18–22 | 0.36 | 180 |
| CS23 | 27–31 | 0.54 | 270 |

Es solo división. No dice si una ecografía puede alcanzar esa resolución, ni si se ve la estructura que interesa,
ni que el modelo de H13 (fantomas 2D de cápsula y ranura) valga para un embrión de esa edad.

## 5. Rotulado: el manifiesto de anotación

El manifiesto es el CSV que consume H11 (`scripts/run_h11.py`). Lo valida `geovida.labeling.validate_manifest`
(no abre imágenes: revisa coherencia y aplica la compuerta humana).

| Columna | ¿Obligatoria? | Contenido |
|---|---|---|
| `embryo_id` | sí | identificador **anonimizado** del embrión (sin nombres ni fechas de nacimiento) |
| `structure` | sí | estructura rotulada (p. ej. `body`, `ventricle`) |
| `image`, `label` | sí | volumen y máscara de referencia |
| `label_value` | sí | valor de la máscara que marca la estructura |
| `species` | recomendada | `mouse`, `rat`, `zebrafish`, `chick`, `human`, `other` |
| `stage_system`, `stage` | opcional | escala de estadios y estadio; con `carnegie` solo para humanos (1–23) |
| `age_days`, `crl_mm` | opcional | edad (embrionaria) y longitud; se avisa si caen fuera del rango del estadio |
| `annotator_id`, `annotation_date` | recomendadas | sin anotador no se puede medir acuerdo entre anotadores |
| `consent_ref`, `ethics_ref` | **obligatorias si `species == human`** | referencia del consentimiento informado y de la aprobación de un comité de ética |
| `source` | opcional | de dónde vienen los datos |

**Compuerta humana.** Cualquier fila con `species == human` sin `consent_ref` **y** `ethics_ref` no vacíos hace que el
manifiesto no sea válido, aunque falten las columnas. El validador no puede comprobar que esas referencias sean
reales: solo impide omitirlas. La anonimización (incluido recortar el encabezado de una imagen impresa o exportada),
la base legal y la aprobación del comité son responsabilidad de quien aporta los datos.

**Reglas para quien rotula.** (1) Al menos dos personas rotulan un subconjunto (≥ 20 % de los embriones) para medir
acuerdo (Dice). (2) Quien rotula no ve el certificado del instrumento. (3) Una referencia dibujada por una persona
**no es la verdad**: se mide acuerdo, no error exacto. (4) Todo desacuerdo y toda exclusión de un embrión se registra.

## 6. Niveles de evidencia (propuesta de trabajo)

| Nivel | Qué es | Estado en este proyecto |
|---|---|---|
| E0 | Idea o hipótesis sin datos | — |
| E1 | Simulación con verdad exacta, criterios preregistrados | **H1–H13 (aquí estamos)** |
| E2 | Imagen real de **animal** con referencia de expertos, preregistrada | H11 / H12R: criterios listos, **faltan los volúmenes** |
| E3 | Datos **humanos** retrospectivos, anonimizados, con consentimiento y aprobación de ética; solo acuerdo, sin uso clínico | no iniciado; requiere la compuerta del §5 |
| E4 | Estudio prospectivo con comité de ética y, para cualquier uso clínico, autoridad regulatoria | no iniciado |

Ninguna afirmación del proyecto pasa de E1. Cada afirmación de un informe debe citar su nivel (ver el panel).

## 7. Qué no es este documento

No es un atlas validado por embriólogos, no sustituye la fuente, no define cuándo una ecografía es adecuada y no
autoriza procesar ninguna imagen de una persona. Una ecografía impresa de una persona real **no se procesa** sin
las condiciones del §5.
