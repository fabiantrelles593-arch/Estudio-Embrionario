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
