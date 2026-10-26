# Capa avanzada v3.0 — invariantes de forma y robustez de segmentación

## Objetivo

La v3.0 amplía el vector morfológico con dos controles complementarios: (1) siete momentos invariantes de Hu calculados sobre la componente conectada mayor y (2) un perfil de sensibilidad al variar el umbral de intensidad. El propósito es describir la forma de manera más rica y detectar cuándo las medidas cambian por decisiones de segmentación.

## 1. Momentos de Hu

Los momentos de Hu se calculan a partir de momentos centrales normalizados y ofrecen invariancia teórica ante traslación, escala y rotación. La implementación guarda los siete valores originales (hu_1 a hu_7) y una transformación signed-log (hu_log_1 a hu_log_7) para comprimir su amplio rango dinámico. Referencia oficial: https://scikit-image.org/docs/stable/api/skimage.measure.html#skimage.measure.moments_hu

Decisión explícita: los momentos de Hu se extraen de la componente conectada de mayor área para evitar que pequeños objetos desconectados dominen la firma de forma. Los momentos de Hu no representan automáticamente todas las componentes. Rasterización, muestreo y errores de contorno pueden generar diferencias aunque la transformación sea teóricamente invariante.

## 2. Sensibilidad a umbrales

La bandera --sensitivity evalúa una imagen con varios umbrales. Por defecto, se analizan cinco niveles alrededor del umbral principal: t−0.2, t−0.1, t, t+0.1 y t+0.2, limitados al rango [0, 1]. Se pueden definir manualmente:

```bash
python -m src.analyze_manifest demo/synthetic_manifest.csv \
  --out demo/synthetic_mask_metrics.csv \
  --sensitivity \
  --sensitivity-thresholds 0.3,0.4,0.5,0.6,0.7 \
  --strict
```

Para cada nivel se registran medidas geométricas y topológicas. Si la máscara queda vacía o no se puede medir, el intento se conserva como fallo del perfil de sensibilidad. El reporte calcula:

- topology_stability: fracción de niveles válidos que comparten la pareja topológica (beta0, beta1) más frecuente.
- area_cv, perimeter_cv, aspect_ratio_cv y circularity_cv: coeficientes de variación a través de umbrales válidos.
- topology_states: cantidad de parejas topológicas distintas observadas.
- robustness_index: índice exploratorio de 0 a 100 con pesos iguales para estabilidad topológica y estabilidad de medidas continuas. La estabilidad continua es la media de 1/(1+CV) de las variables con CV definido.
- sensitivity_flags y threshold_sensitivity_json: avisos y resultados detallados por umbral.

## 3. Interpretación rigurosa

El robustness_index no es una probabilidad, intervalo de confianza, estimación de exactitud anatómica ni resultado biológico. Resume la sensibilidad del pipeline para los umbrales y la imagen evaluados. Una imagen podría obtener estabilidad alta y aun estar segmentada incorrectamente; la validación anatómica necesita referencias adecuadas y revisión experta. En imágenes sintéticas, los umbrales pueden devolver exactamente la forma generada, por lo que un índice de 100 valida ese caso controlado, no datos embrionarios.

El cálculo predeterminado usa la polaridad intensidad > umbral, adecuada solo si el objeto es más brillante que el fondo. Si el objeto es oscuro sobre fondo claro, se requiere transformar la imagen de manera documentada o usar otra estrategia de segmentación. No se debe cambiar la polaridad para maximizar artificialmente la estabilidad.

## 4. Validación incorporada

Los tests cubren:
- estabilidad de momentos de Hu bajo traslación y rotación de 90 grados;
- componente mayor ante un artefacto aislado pequeño;
- umbrales estables (índice esperado de 100 en un caso sintético);
- máscaras vacías, variación topológica y pocos umbrales válidos;
- umbrales inválidos e intensidades fuera de rango;
- integración del manifiesto a las columnas de Hu y al resumen de sensibilidad;
- fallo del modo estricto cuando la evaluación opcional de sensibilidad falla.

## 5. Evolución científica pendiente

Esta capa es un control de calidad computacional. La etapa siguiente requiere comparar estrategias de segmentación, validar límites anatómicos, evaluar sensibilidad a resolución y conectividad, y separar secciones del mismo espécimen de unidades experimentales independientes. No se afirma novedad científica absoluta: la contribución debe justificarse con revisión bibliográfica y comparación con métodos existentes.

## Fuentes técnicas y de datos

- scikit-image, API de medición y momentos de Hu: https://scikit-image.org/docs/stable/api/skimage.measure.html#skimage.measure.moments_hu
- Human Developmental Biology Resource (HDBR), descripción de su Atlas y recursos de histología: https://hdbr.org/ . La existencia del recurso no concede por sí sola permiso para reutilizar cualquier imagen; se deben comprobar las condiciones específicas de acceso y uso.
