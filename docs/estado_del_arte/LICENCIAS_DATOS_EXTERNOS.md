# Licencias de tres conjuntos externos pendientes: S-BIAD441, portal IMPC y UniCoN

> Comprobación del 20 nov 2026 (tarea P2 de `docs/INFORME_DE_PROGRESO.md` §5). Solo se leyeron registros y páginas
> públicas; **no se descargó ningún dato**. Etiquetas: [HV] hecho verificado · [EI] evidencia indirecta ·
> [PV] pendiente de validación.

## 1. Regla aplicada

ADR-004: la licencia MIT del repositorio no se extiende a datos de terceros. Un conjunto se usa solo si su
**licencia propia del conjunto** está escrita en el registro del depósito o del proveedor. La licencia del artículo
que lo describe **no** cuenta: cubre el texto del artículo, no los datos. Una licencia en el pie de un portal cuenta
como evidencia indirecta, no como licencia del conjunto.

## 2. Resultado

| Conjunto | Qué dice el registro del conjunto | Otras pistas | Estado | Decisión |
|---|---|---|---|---|
| **Portal IMPC** (mousephenotype.org) | La página «How do I cite the IMPC?» dice que el IMPC publica su conjunto de datos bajo CC BY 4.0, y que el contenido del sitio tiene la misma licencia [HV] | Pide citar el sitio y sus artículos cuando se usan datos o imágenes del IMPC [HV]. La página no dice de forma expresa si las imágenes están cubiertas [HV] | **CC BY 4.0 [HV]** para los datos; imágenes del portal [EI] | Usable con atribución y cita. Los volúmenes E15.5 que ya usamos vienen del subconjunto de FaceBase, con CC BY 4.0 propio [HV]: no cambia nada en P3 |
| **Dalmasso S-BIAD441** (BioStudies, publicado el 1 may 2022) | El registro **no tiene atributo de licencia** [HV] | La política del BioImage Archive dice que las entregas directas nuevas se publican con CC0 o CC BY 4.0, y que cuando un conjunto tiene otra licencia se indica como atributo [HV]. No dice qué pasa con un registro sin atributo ni desde qué fecha rige [HV]. El artículo (Dev Cell 2022, 10.1016/j.devcel.2022.08.005) es CC BY, pero eso cubre el artículo [HV] | **Sin licencia del conjunto [PV]** | **No se usa.** Para usarlo: pedir por escrito al BioImage Archive o al autor de contacto que confirmen la licencia (CC0 o CC BY 4.0), y registrar la respuesta aquí |
| **UniCoN, «Multi-age embryonic PTAe MicroCT Data Collection»** (Penn State Data Commons, 10.26208/6e6x-ps14, 2024) | En DataCite, la lista de derechos (`rightsList`) **está vacía** [HV]. La ficha del conjunto no tiene texto de licencia [HV] | El pie del portal Data Commons enlaza CC BY 4.0 como «copyright information» del sitio [EI]. El artículo (Sci Rep 2025, 10.1038/s41598-025-87797-9) es CC BY-NC-ND 4.0 y dice que los datos son «publicly accessible», sin licencia [HV] | **Probable CC BY 4.0 por el pie del portal [EI]; sin licencia del conjunto [PV]** | **No se usa** (además, el cartílago está fuera del alcance actual, `MATRIZ_CAPACIDADES.md`). Si se necesitara: pedir confirmación a Penn State Data Commons |

## 3. Qué cambia

* El portal IMPC sale de la lista de pendientes.
* S-BIAD441 y UniCoN **no se descartan**: quedan «en espera de licencia», con el paso concreto para resolverlo.
  Ninguno de los dos se necesita para los estudios en curso (P3, H20, MT-A v2).
* No se ha escrito a nadie: contactar a un tercero en nombre del proyecto requiere autorización del responsable.

## 4. Fuentes (consultadas el 20 nov 2026)

* IMPC, «How do I cite the IMPC?»: <https://www.mousephenotype.org/?p=2572>
* BioStudies, S-BIAD441 (API): <https://www.ebi.ac.uk/biostudies/api/v1/studies/S-BIAD441>
* BioImage Archive, políticas: <https://www.ebi.ac.uk/bioimage-archive/help-policies/>
* Dalmasso et al. 2022, *Dev Cell* 57(17):2140–2150.e5, [10.1016/j.devcel.2022.08.005](https://doi.org/10.1016/j.devcel.2022.08.005) (PMC9481268)
* DataCite, 10.26208/6e6x-ps14: <https://api.datacite.org/dois/10.26208/6e6x-ps14>
* Penn State Data Commons, ficha del conjunto 6443: <https://www.datacommons.psu.edu/commonswizard/MetadataDisplay.aspx?Dataset=6443>
* Sapkota et al. 2025, *Sci Rep*, [10.1038/s41598-025-87797-9](https://doi.org/10.1038/s41598-025-87797-9) (PMC11785758)
