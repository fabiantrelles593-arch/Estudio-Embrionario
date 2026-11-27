# Notas de envío: IEEE Transactions on Ultrasonics (26 nov 2026)

> **Decisión del autor (26 nov 2026): ruta A, revista T-UFFC por la vía tradicional, sin cargo de acceso abierto.**
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
| Resumen gráfico de 660 × 295 | **Falta** |
| Plantilla de T-USON (Word o LaTeX) | **Falta**: pasar el texto a la plantilla oficial |
| Ética con animales | Hecho: datos ya publicados, sin experimentos nuevos |
| Financiación y conflictos de interés | **Falta** (autor) |
| Autoría, afiliación y biografía | **Falta** (autor) |
| Revisión del inglés | **Falta**: recomendable una revisión profesional o de un hablante nativo |
| Búsqueda en Scopus o Web of Science y revisor externo | **Falta** (`docs/SINTESIS_CERTIFICADO.md` §6) |
| Extensión dentro de 10 páginas (Original Research) o 14 (Methods and Concepts) | Probable; se comprueba con la plantilla |
