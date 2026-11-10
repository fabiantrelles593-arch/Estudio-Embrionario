# Visor 4D de geovida para Unity

**Estado: escrito, no compilado.** En el entorno donde se desarrolla geovida no hay Unity
instalado, así que este visor no se ha abierto ni probado en el Editor. El exportador de datos sí
se ejecuta y se comprueba. La primera vez que se abra en Unity puede hacer falta corregir algún
detalle; cuando eso ocurra, se anota aquí.

## Qué muestra

Un objeto de forma conocida que crece con el vóxel fijo, etapa por etapa. Los vóxeles se pintan
con la luz del semáforo de volumen (verde, amarillo, rojo), que se calcula solo con la máscara y
el tamaño del vóxel. Al lado, el error real, que aquí se conoce porque la forma es matemática.

## Cómo abrirlo

1. Genera los datos: `python scripts/export_unity.py` (escribe
   `unity/Assets/StreamingAssets/geovida_series.json`).
2. En Unity Hub crea un proyecto 3D (plantilla *Universal 3D*; Unity 6 o 2022 LTS).
3. Copia las carpetas `Assets/Geovida` y `Assets/StreamingAssets` de aquí dentro de la carpeta
   `Assets` de ese proyecto.
4. En una escena vacía crea un GameObject vacío y añádele el componente `GeovidaViewer`.
5. Pulsa Play. Deslizadores: forma y etapa. Arrastrar gira; la rueda acerca.

El script no usa `UnityEngine.Input` (la interacción va por `OnGUI`), para que funcione tanto con
el sistema de entrada antiguo como con el nuevo.

## Límites

Solo datos sintéticos. Investigación y educación; sin uso clínico. No representa embriones reales.
