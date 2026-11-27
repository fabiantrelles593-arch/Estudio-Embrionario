# Notas de envío: IEEE Transactions on Ultrasonics (26 nov 2026)

> **Decisión del autor (26 nov 2026): ruta A, revista T-UFFC por la vía tradicional, sin cargo de acceso abierto.**
> **Categoría elegida el mismo día: Methods and Concepts.** El texto para enviar es
> `docs/manuscrito/MANUSCRIPT_MC_EN.md` (v0.3-en).
> Las normas se leyeron ese día en la página oficial:
> <https://ieee-uffc.org/publication/t-uffc/guidelines-authors>. Hay que volver a comprobarlas antes de enviar.
>
> **Etiquetas:** [HV] verificado en la página oficial · [HIP] hipótesis · [PROP] propuesta.

## 1. Lo que dice la revista [HV]

- **Nombre actual:** IEEE Transactions on Ultrasonics (T-USON); antes, T-UFFC. Es híbrida.
- **Envío:** solo por ScholarOne Manuscript Central. Revisión simple ciega, con al menos dos revisores.
- **Tipos de artículo y páginas gratuitas** (páginas IEEE a doble columna, con figuras, referencias y biografías):

  | Tipo | Páginas gratuitas |
  |---|---|
  | Original Research | 10 |
  | Methods and Concepts | 14 |

  Cada página de más cuesta 275 USD, también en la vía tradicional.
- **Acceso abierto:** opcional, por 2195 USD, con exención o rebaja para autores de países de renta baja y un 20 % de
  descuento para miembros de la sociedad UFFC. La vía tradicional no tiene cargo.
- **Formato obligatorio:** la plantilla de T-USON (Word o LaTeX, en el IEEE Template Selector).
- **Estructura:** Abstract e Index Terms, una sección explícita de Introduction y, recomendada, una de Discussion
  separada. Figuras dentro del texto y referencias en estilo IEEE.
- **Resumen gráfico obligatorio:** horizontal, 660 × 295 píxeles; se evalúa en la revisión.
- **Otros requisitos:**
  - declarar la ética de los estudios con animales;
  - declarar toda la financiación y los conflictos de interés;
  - biografía y foto de cada autor (pueden darse al final);
  - un inglés claro: la revista puede devolver el texto sin revisarlo si está mal escrito.

## 2. El riesgo principal: el rechazo sin revisión [HV + HIP]

La revista exige que cada artículo de investigación presente «un avance nuevo y significativo», demostrado de forma
convincente más allá de la teoría, la simulación y la experimentación preliminar. Rechaza sin revisión los trabajos
«incrementales» o de «alcance modesto».

Este manuscrito tiene puntos fuertes:

- el protocolo (preregistro y prueba sellada);
- los resultados negativos;
- la honestidad sobre sus límites.

Pero también tiene puntos débiles para esa exigencia [HIP]:

- un solo conjunto de datos y un solo equipo;
- 44 casos de prueba;
- la separación entre aciertos y fallos sin demostrar;
- una red que es una reimplementación, no un método nuevo.

Es probable que el comité lo vea como un trabajo de alcance modesto. Si lo rechaza sin revisión, la revista no admite
reenviar una versión revisada.

## 3. Opciones [PROP]

| Opción | Ventaja | Inconveniente |
|---|---|---|
| **a. Original Research ahora** | Es la vía directa | Riesgo alto de rechazo sin revisión por «alcance modesto» |
| **b. Methods and Concepts ahora** | La revista pide en esta categoría documentar «buenas prácticas de un método o protocolo» para fomentar la ciencia abierta. El protocolo de preregistro y prueba sellada encaja ahí, y tiene 14 páginas gratuitas | Hay que reescribir el texto como guía del protocolo, con los estudios como ejemplo |
| **c. Esperar a H26** | Una replicación en un segundo conjunto haría el trabajo mucho más sólido para Original Research | Depende de NYU, sin plazo |

**Recomendación:** la opción b ahora, o la c si llegan los datos pronto. La a es la que más riesgo tiene.

## 4. Estado del borrador en inglés frente a estos requisitos

| Requisito | Estado |
|---|---|
| Abstract | Hecho |
| Index Terms (en orden alfabético) | Hecho (v0.2-en) |
| Introduction explícita | Hecho |
| Diferencia con trabajos previos | Hecho: párrafo de aportaciones, sin afirmar que sea el primero |
| Discussion separada | Hecho |
| Referencias en estilo IEEE numerado | Hecho (v0.2-en) |
| Figuras | Hechas, generadas por `scripts/figure_manuscript.py`; falta colocarlas dentro del texto en la plantilla |
| Resumen gráfico de 660 × 295 | Hecho: `docs/figures/manuscript_graphical_abstract.png`, generado por `scripts/figure_manuscript.py` (solo en local) |
| Reestructurar como Methods and Concepts | Hecho (v0.3-en): protocolo en la sección II y estudios como ejemplos en la III. Tabla de verificación (Table I) hecha |
| Plantilla de T-USON (LaTeX, elegida el 27 nov 2026) | Hecho: `docs/manuscrito/tuson/manuscript_tuson.tex` (v0.4-tex). Ver §5 |
| Resumen de un solo párrafo, 150–250 palabras (norma de la plantilla) | Hecho: 240 palabras |
| Tres Highlights de 200 caracteres como máximo (norma de la plantilla) | Hecho: 165, 162 y 166 caracteres |
| Compilar el `.tex` y comprobar la extensión | **Falta**: no hay compilador LaTeX en el equipo; ver §5 |
| Ética con animales | Hecho: datos ya publicados, sin experimentos nuevos |
| Financiación y conflictos de interés | **Falta** (autor) |
| Autoría, afiliación y biografía | **Falta** (autor) |
| Revisión del inglés | **Falta**: recomendable una revisión profesional o de un hablante nativo |
| Búsqueda en Scopus o Web of Science y revisor externo | **Falta** (`docs/SINTESIS_CERTIFICADO.md` §6) |
| Extensión dentro de 10 páginas (Original Research) o 14 (Methods and Concepts) | Probable; se comprueba al compilar |

## 5. La plantilla LaTeX (27 nov 2026) [HV]

- **Origen:** IEEE Template Selector → Transactions, Journals and Letters → IEEE Transactions on Ultrasonics →
  Original Research → LaTeX. El selector no ofrece una plantilla aparte para Methods and Concepts.
- **Archivo:** `TUSON LaTeX Template.zip`, 4 670 624 bytes, SHA-256
  `9c614865e91fb2185551e817b1abfb6323d33cfe2cf49a6d323f08b063141804`. Contiene `Sample.tex`, `TUSON.sty`,
  `IEEEtran.cls` (V1.8b), dos logotipos, `GA.pdf` y `Sample.pdf`.
- **No se redistribuye** en el repositorio: `TUSON.sty` no declara licencia. Para compilar, descargar el zip y copiar
  `IEEEtran.cls` y `TUSON.sty` junto a `manuscript_tuson.tex`.
- **Normas de la plantilla que no estaban en la página web:**
  - tres Highlights, de 200 caracteres como máximo cada uno;
  - resumen de un solo párrafo, de 150 a 250 palabras, sin abreviaturas, notas ni referencias;
  - resumen gráfico de 6,25 × 2,5 pulgadas como máximo, al menos 300 ppp, fondo blanco y rótulos en Arial;
  - figuras en color a 300 ppp como mínimo; rótulos de subfiguras (a), (b).
- **Conflicto entre fuentes:** la página web pide un resumen gráfico de 660 × 295 píxeles; con el ancho fijo de 6,25
  pulgadas de la caja de la plantilla, esa proporción supera las 2,5 pulgadas de alto. El `.tex` ajusta la imagen por
  la altura (orden `\GAfit`). `scripts/figure_manuscript.py` escribe las dos versiones: 660 × 295 px para la web y
  1980 × 885 px (300 ppp) para la plantilla. Conviene confirmarlo con la revista si el editor lo señala.
- **Paquetes no libres:** el preámbulo de la plantilla carga `mathtime` y `linex`, que no están en una distribución
  libre estándar. El `.tex` los deja desactivados con un interruptor (`\tusonfontstrue` para activarlos).
- **Pendiente:** compilar. Opciones: instalar un compilador (MiKTeX o Tectonic, descarga que requiere permiso) o
  compilar en Overleaf con los archivos de la plantilla.
