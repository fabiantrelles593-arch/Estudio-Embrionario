# Datos reales, imágenes humanas y ética

**Estado actual: ninguna imagen real, humana o animal, ha sido procesada por
este proyecto.** Todo es sintético (`phantoms.py`, `twod.py`, `traj4d.py`).

## 1. Uso previsto (se repite en el README)

Herramienta de investigación y educación para cuantificar el error de medición
de formas en imágenes. **No está destinada a uso clínico, diagnóstico,
cribado, estimación de riesgo fetal ni selección de embriones.** Un software
con finalidad médica es un dispositivo médico regulado (en Perú, DS 003-2020-SA:
el software autónomo se considera dispositivo médico).

## 2. Orden en que se incorporan datos reales

1. **Sintéticos** (hecho).
2. **Públicos con licencia verificada y de origen no humano o ya anonimizado
   por sus autores:** conjuntos de ratón (IMPC, MusMorph, DMDD) y, para 2D, un
   conjunto público de ecografía fetal con licencia que permita este uso (la
   licencia exacta se verifica antes de descargar, no se supone).
3. **Imágenes aportadas por un laboratorio aliado**, con acuerdo de
   transferencia de datos y aprobación de su comité de ética.
4. **Imágenes humanas propias o de terceros:** solo con las condiciones de la
   sección 3.

## 3. Condiciones para procesar una ecografía humana

Una ecografía de embarazo es un dato de salud de dos personas. Antes de
abrirla se necesita **todo** lo siguiente:

* Consentimiento informado, por escrito, de la gestante, que cubra este uso
  específico (software de investigación, sin fines clínicos) y la posibilidad
  de retirarlo.
* Anonimización completa antes de que el archivo llegue al repositorio:
  metadatos (DICOM/EXIF), texto grabado en la imagen (nombre, fecha, centro) y
  cualquier dato que permita reconocer a la persona.
* Aval de un comité de ética de investigación o, si no existe, una decisión
  escrita de la institución responsable; y cumplimiento de la ley peruana de
  protección de datos personales (Ley 29733; **no verificada en detalle aquí**).
* Almacenamiento fuera del repositorio público: la imagen nunca se publica ni
  se sube a GitHub, Notion ni a ningún servicio de terceros.
* Un plan de análisis preregistrado **antes** de ver los datos.

Mientras eso no exista, no se pide ni se procesa ninguna ecografía humana.

## 4. Qué significaría «probar con una ecografía»

Significa probar el **software sobre una imagen**, nunca un experimento con
personas. Una ecografía real no tiene verdad exacta, así que no mide *error*;
mide **acuerdo** entre segmentadores y entre un contorno manual y los
automáticos. Es una prueba de estrés 2D de las medidas de `twod.py`.
No se haría ninguna afirmación sobre la salud de la persona ni del feto.

## 5. Lenguaje

| Se puede decir | No se debe decir |
|---|---|
| «cuantifica el error de medición en imágenes sintéticas» | «detecta malformaciones» |
| «benchmark metodológico» | «evalúa el crecimiento fetal» |
| «material educativo» | «apoya decisiones clínicas» |
| «solo investigación; no apto para uso clínico» | «mejora el diagnóstico prenatal» |

## 6. Conjuntos públicos de ecografía 2D identificados (investigación del 2026-11-09)

Informe de una búsqueda asistida por IA, **sin revisión humana**. Las licencias que la tabla marca
como «verificada» las leyó esa búsqueda en el registro del conjunto; lo demás no se verificó.
**Esto no autoriza a procesar ninguna imagen**: sigue vigente la sección 3. Que un conjunto sea
público con licencia abierta es una condición necesaria, no suficiente: antes de abrirlo hay que
confirmar por escrito la base legal y ética de nuestro uso con la institución responsable.

| Conjunto | Contenido | Verdad de referencia | Licencia | Utilidad aquí |
|---|---|---|---|---|
| **HC18** (van den Heuvel et al., PLOS ONE 2018; Zenodo 10.5281/zenodo.1327317) | 1 334 imágenes 2D de la cabeza fetal (551 gestantes), 800×540 px, píxel de 0.052 a 0.326 mm; 999 de entrenamiento y 335 de prueba | Elipse dibujada por el ecografista + CSV con píxel y HC en mm (solo entrenamiento) | CC BY 4.0 (verificada) | **Principal**: único que permite comparar nuestra elipse con una de referencia en mm. Los autores declaran aprobación ética (CMO Arnhem-Nijmegen), consentimiento exento por recogida retrospectiva y anonimización |
| FETAL_PLANES_DB (Burgos-Artizzu et al., Sci Rep 2020; Zenodo 10.5281/zenodo.3904280) | 12 400 imágenes de 1 792 pacientes | Solo etiquetas de plano | CC BY 4.0 (verificada) | Robustez entre equipos y operadores; no sirve para exactitud métrica (sin píxel ni geometría) |
| PSFHS (Chen et al., Sci Data 2024; Zenodo 10.5281/zenodo.10969427) | 1 358 imágenes intraparto | Máscaras de sínfisis y cabeza fetal | CC BY 4.0 (verificada) | Validar área y perímetro de máscaras reales; la geometría intraparto difiere de la biometría estándar |
| ACOUSLIC-AI (Zenodo 10.5281/zenodo.12697994) | Barridos ciegos con sonda de bajo coste | Máscaras de abdomen y circunferencia en mm | CC BY-NC-SA 4.0 (**solo no comercial**) | «Peor caso» de moteado; lección de metrología: en la v1.0 las circunferencias eran el doble por usar ejes en lugar de semiejes (corregido en la v1.1) |
| Planos fetales de 5 países africanos (Zenodo 10.5281/zenodo.7540448) | 450 imágenes | Etiquetas de plano | CC BY 4.0 | Generalización a entornos de pocos recursos (no verificado en la fuente primaria) |

Advertencias: no se debe suponer que todo lo de un mismo reto comparte licencia (un PDF asociado al reto
FH-PS-AOP es CC BY-NC-ND 4.0); un conjunto derivado que mezcla fuentes hay que revisarlo registro por
registro. Los conjuntos de animales o gastruloides (por ejemplo EmbryoNet, CC BY 4.0) son una primera
imagen real sin datos de personas; **no están verificados por este proyecto**.

**Qué implica para la prueba 2D (cálculo propio, aproximado):** una cabeza de HC18 mide del orden de
350 px de diámetro, muy por encima de la rejilla de H5 y H7 (t/h hasta 20). En esa escala el error
de píxel del perímetro queda muy por debajo de la variabilidad humana de referencia (±3.0 %
intraobservador y ±4.9 % interobservador, límites de acuerdo del 95 %, INTERGROWTH-21st, según la
búsqueda); lo difícil es el moteado y el borde, no la resolución. Un diseño razonable sería: error
porcentual de la elipse frente a la de referencia y Bland–Altman, preregistrados antes de ver datos.
Lo mismo vale para las estructuras pequeñas (hueco de pocos píxeles), donde sí se aplican los
límites de H5, H6 y H7.
