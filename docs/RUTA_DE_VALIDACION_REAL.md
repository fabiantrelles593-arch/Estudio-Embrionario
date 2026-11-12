# Ruta de validación con ecografía real — qué haría falta, con números

> Solo investigación y educación. Hasta hoy **ninguna medida de este programa se ha validado con imagen real**. Esta ruta no es una promesa:
> es la lista de lo que haría falta para que un resultado pudiera sostenerse, con las cuentas hechas.

## Puertas (cada una exige la anterior; ninguna se alcanza escribiendo)

| Puerta | Qué se demuestra | Qué hace falta | Estado |
|---|---|---|---|
| **G0** | La canalización mide una imagen real y reporta sus límites | `geovida real2d`, protocolo `docs/PREREGISTRO_REAL2D_PILOTO.md`, una imagen con escala | Código listo; **falta la imagen en la sesión** |
| **G1** | El certificado no da verdes equivocados en ecografía real (H16R) | Imágenes 2D de primer trimestre anonimizadas, con consentimiento informado y aprobación ética, CRL medida por **dos operadores** | No iniciada |
| **G2** | Funciona entre equipos y sondas | ≥ 3 equipos, ≥ 2 sondas, calibración ampliada a objetos pequeños y desenfoque grande (ver `docs/REAL2D_METODO.md`) | No iniciada |
| **G3** | Revisión científica externa | Un panel que hoy **no existe** (`docs/PANEL_DE_REVISION.md`), informe de errores abierto | No iniciada |
| **G4** | Camino regulatorio | Asesoría regulatoria cualificada; el paquete `docs/clinico/` es un borrador de ingeniería, no está aprobado por ninguna autoridad | No iniciada |

## Cuántas imágenes (cuenta exacta, Clopper-Pearson, 95 % unilateral)

Para que el límite superior del falso verde sea ≤ 10 % (la regla del proyecto) se necesitan **verdes**, y de las imágenes solo una fracción da verde:

| Verdes equivocados observados | Verdes necesarios | Imágenes si 70 % dan verde | 50 % | 30 % | 15 % |
|---|---|---|---|---|---|
| 0 | 29 | 42 | 58 | 97 | 194 |
| 1 | 46 | 66 | 92 | 154 | 307 |
| 2 | 61 | 88 | 122 | 204 | 407 |

* En simulación dieron verde ≈ 50 % (cuerpo) y ≈ 66 % (ranura); **en imagen real puede ser mucho menos**: el tope de imagen real hoy lo impide por diseño.
* Si la tasa verdadera de falso verde fuera 2 %, la probabilidad de que 46 verdes den ≤ 1 equivocado es 0.77; si fuera 5 %, 0.32; si fuera 10 %, 0.05.
  Un resultado «apoyada» con ~50 verdes descarta tasas altas, no demuestra tasas bajas.
* La referencia no es la verdad: la CRL medida por un operador tiene su propio error; por eso se piden dos operadores y se informa su diferencia.

## Condiciones no negociables para cualquier imagen de personas

Consentimiento informado de quien corresponda (en menores, de madres/padres o tutores), anonimización completa (incluidos metadatos y texto en la imagen),
base legal, aprobación de un comité de ética, y `geovida.labeling.validate_manifest` en verde. Una declaración personal de permiso sirve para
un análisis privado y exploratorio como el piloto REAL2D; **no** sirve para publicar ni para validar.

## Qué podría importar, si saliera bien (y qué no)

Un certificado abierto, preregistrado y honesto sobre **cuándo una medida o una datación no se puede confiar** podría ser útil donde el equipo o la experiencia
son limitados. Eso es una hipótesis de uso, no un resultado. Nada de esto sustituye el criterio de un profesional de salud.
