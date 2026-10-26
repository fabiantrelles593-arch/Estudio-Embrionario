# v2.5 — análisis por manifiesto

## Propósito
Conectar el manifiesto de metadatos con el flujo de carga de imágenes y el módulo de métricas 2D, de forma que cada fila mantenga la trazabilidad de origen hasta el resultado.

## Ejecución reproducible
Desde la raíz del proyecto:

```powershell
python src/demo_pipeline.py
python src/create_synthetic_manifest.py
python -m src.analyze_manifest demo/synthetic_manifest.csv --out demo/synthetic_mask_metrics.csv --strict
```

El manifiesto de demostración se construye usando únicamente máscaras sintéticas ya creadas para pruebas del software. El campo de etapa se establece en `not_applicable` para evitar presentarlas como etapas Carnegie reales.

## Reglas de aceptación
- La auditoría de metadatos es un bloqueo: si falla, el programa guarda el informe de auditoría y no calcula métricas.
- La ruta de cada imagen se interpreta en relación con el directorio del manifiesto, salvo que sea absoluta.
- Una imagen que falte, una máscara vacía o una escala inválida crea una fila `ERROR` con la causa, en lugar de desaparecer de los resultados.
- Si no se conoce una escala física, las mediciones permanecen explícitamente en píxeles.
- Si se informa `pixel_size`, también se exige `pixel_size_unit` y que la escala sea finita y positiva. La columna `measurement_length_unit` indica la unidad lineal; `area` usa esa unidad al cuadrado y las longitudes usan la unidad lineal.
- El estado `OK` solo significa que la máscara pudo medirse; no valida la segmentación anatómica.
- El modo `--strict` devuelve un código distinto de cero si hay errores individuales, sin ocultar las filas fallidas.

## Etapas biológicas y ejemplos sintéticos
Los registros biológicos deben declarar una etapa entera CS12–CS18 según el protocolo elegido. Los registros sintéticos deben usar `stage=not_applicable` y `modality=SYNTHETIC`. Esta distinción evita asignar falsamente una etapa Carnegie a una figura matemática.

## Limitaciones
El umbral de intensidad es un método de segmentación simple. No es suficiente, por sí solo, para delimitar estructuras embrionarias complejas en histología, fotografías o reconstrucciones 3D. Los datos reales requieren una decisión anatómica documentada, control de calidad y condiciones de uso verificadas.
