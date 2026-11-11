# Guía: cómo entregar volúmenes reales para H11 (paso a paso)

Para que el certificado se pruebe con ecografía real de embriones de **ratón** hace falta que alguien
ponga los volúmenes (`.nii` o `.nii.gz`) al alcance del proyecto. Estas son las dos rutas. Las figuras
de un artículo (capturas, PNG, JPG) **no sirven**: son imágenes 2D sin tamaño de vóxel ni etiquetas.

> **Solo animales.** Esta guía es para el conjunto de ratón (u otro conjunto animal). Con imágenes
> **de personas** no se hace nada hasta cumplir todas las condiciones de
> [`DATOS_REALES_Y_ETICA.md`](DATOS_REALES_Y_ETICA.md) §3: consentimiento, anonimización completa,
> base legal, comité de ética y asesor clínico.

## Ruta A — Obtener la ficha en tu computadora (no sale ninguna imagen)

1. Instala Python 3.11 o superior (python.org).
2. En una terminal (en Windows, «Símbolo del sistema» o PowerShell):

   ```bash
   pip install "geovida[real] @ git+https://github.com/fabiantrelles593-arch/Estudio-Embrionario.git@geovida/v0.1-desde-cero"
   geovida datasheet "C:\ruta\a\la\carpeta\con\los\volumenes" --out ficha.json
   ```

   (En Mac o Linux la ruta se escribe como `/ruta/a/la/carpeta`.) También acepta un `.zip` o un solo
   archivo `.nii`/`.nii.gz`.
3. El programa imprime, por archivo: forma, tamaño del vóxel en milímetros, intensidades o etiquetas.
   **No compara con ninguna referencia.** Guarda un JSON pequeño (`ficha.json`) sin imágenes.
4. Envía ese `ficha.json` (se puede adjuntar aquí). Con eso se decide qué archivo es imagen y cuál es
   etiqueta y se anota en «Desviaciones» de [`PREREGISTRO_H11.md`](PREREGISTRO_H11.md) **antes** de
   calcular ningún acuerdo.

Si los nombres de archivo pudieran identificar algo que no debe salir, agrega `--hide-names`
(los nombres se sustituyen por `vol_001`, `vol_002`…; avisa antes de enviar para que se conserve el
orden de emparejamiento).

## Ruta B — Adjuntar unos pocos volúmenes aquí

Si prefieres no instalar nada, adjunta de 3 a 5 casos completos (imagen y etiqueta de cada embrión) en
`.nii.gz` en esta conversación. Para H11 se necesitan al menos 15 embriones distintos con luz verde, así
que 3–5 casos sirven para **ensayar el flujo y ver la ficha**, no para sacar la conclusión.

## Qué pasa después

1. Se lee la ficha y se completa «Desviaciones» en el preregistro (qué archivo es imagen, qué etiqueta
   es cuerpo o ventrículo cerebral). Eso se confirma en git.
2. Se corre `geovida.realdata.compare_case` con los modelos **congelados** de v0.4 y, aparte, con los de
   la ecografía simulada (H12). Nada se reajusta.
3. Se publica el informe tal como salga, con los fallos. «No evaluable» es un resultado válido.

## Dónde conseguir el conjunto público

«Ultrasound Mouse Embryo Segmentation and Classification» (IEEE DataPort, DOI 10.21227/drmd-xq36). Según
la página del conjunto, la licencia es Creative Commons Attribution y la descarga pide una cuenta
gratuita de IEEE DataPort; el archivo pesa unos 1.94 GB. Ese dato viene de la página del conjunto y este
proyecto no lo ha verificado en otra fuente ni ha abierto ningún archivo.
