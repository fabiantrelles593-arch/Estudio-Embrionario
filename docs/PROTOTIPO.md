# Calibre Geovida: prototipo en el navegador (v0.11)

> Solo investigación y educación. No es un dispositivo médico, no sustituye la medición ni la opinión de quien hizo la ecografía y **no está validado con imágenes reales**.

## Qué es

Una página web de un solo archivo (`prototype/calibre_geovida.standalone.html`, sin servidor) con la que una persona:

1. abre una imagen (queda en su navegador: la página no tiene ninguna llamada de red ni guarda nada);
2. marca dos marcas de la regla de la imagen y escribe la distancia real entre ellas → escala en mm por píxel;
3. marca la cabeza y la rabadilla → **longitud cráneo-rabadilla (CRL)** con su incertidumbre;
4. ve el **certificado de la medida**: edad por CRL (INTERGROWTH-21st) con su dispersión, probabilidad de que el error de edad *causado por la medida* no pase de una tolerancia, semáforo y las razones;
5. ve la **franja de tamaño de referencia** de la población en las 4 semanas siguientes, con el error de la medida y la incertidumbre de la edad propagados, en dos escenarios extremos y sin pretender predecir a ningún feto.

También hay un ejemplo sintético (dibujado por la propia página, con moteado y una regla) que abre la herramienta ya medida. Está rotulado como ejemplo en la imagen y fuera de ella.

## Qué hereda del proyecto

| Pieza de la página | De dónde sale | Cómo se comprueba |
|---|---|---|
| Edad por CRL, dispersión, derivada, probabilidad, semáforo | `geovida.dating` | `tests/test_prototype_core.py` compara el JavaScript con el código Python sobre las mismas entradas (1e-9) |
| Ecuaciones de tamaño de referencia y franja por Monte Carlo (dos escenarios) | `geovida.trajectory` | Misma prueba; las franjas se comparan con tolerancia de Monte Carlo (0.6 mm) porque el generador de números aleatorios es otro |
| Huella de la imagen (`ln_cv`, asimetría) y cajas de soporte | `geovida.chainguard` y `results/summary/h16_chain_frozen.json` | Paridad a 1e-9 sobre imágenes de prueba, incluido un caso de rango dinámico extremo; las cajas incrustadas se comparan con el JSON congelado |
| Función de error `erf` (JavaScript no la trae) | Serie de Taylor y fracción continua | Contra `math.erf` a 1e-12 |

Las pruebas de mutaciones (más de 20 daños deliberados al núcleo) las atrapan todas salvo uno equivalente (un redondeo del núcleo gaussiano que da el mismo resultado). Las interacciones (cargar, marcar, arrastrar, tecla, rojo y «se niega», desbordamiento en teléfono) se prueban en Chromium real con `tests/test_prototype_ui.py` (se omite si no hay Playwright).

## Lo que lo hace distinto de una calculadora de edad

* **Se niega**: sin escala o sin longitud, con una CRL fuera de 15–95 mm, o con edad conocida fuera de 58–105 días, la página no inventa una edad ni una franja.
* **No emite verde**: aunque la probabilidad pase de 0.90, el tope es amarillo («verde bloqueado»), como `geovida.real2d`, hasta que haya validación con imagen real (compuertas G0–G4 de `docs/RUTA_DE_VALIDACION_REAL.md`).
* **Separa lo que mide de lo que supone**: la incertidumbre al marcar, el sesgo sospechado y la tolerancia son supuestos del usuario, escritos como tales.
* **Dice cuánto pesa la medida**: «la medida pone el X % de la varianza del error de edad». Una medida perfecta no hace correcta la edad de un feto concreto.
* **Huella de la imagen**: calcula, en la región de la longitud, los dos índices de la guardia de cadena (H16) y avisa si la imagen cae fuera de lo que se vio en simulación. Eso no invalida el calibre manual; significa que ningún certificado *automático* del proyecto la cubre.

## Presupuesto de incertidumbre del calibre

Cada punto marcado tiene una incertidumbre de puntería de σ píxeles (supuesto, 2 px por defecto). La longitud es L = (píxeles del objeto) · (mm/px de la regla). Con errores independientes en el objeto (L_px) y en la regla (R_px):

`var_rel(L) = 2σ² / L_px² + 2σ² / R_px²`

El sesgo relativo que el usuario declare no mueve la lectura; entra al certificado como sesgo de medida. Lo que el presupuesto **no** incluye: el desenfoque del borde, que la regla no marque lo escrito, la diferencia entre lectores, ni la posición real del extremo anatómico. Con σ = 2 px es una cifra de partida, no una medida de lectores humanos.

## Límites

* No hay datos de lectores humanos que respalden σ. Hace falta medir el acuerdo entre al menos dos lectores en varios individuos (`geovida.agreement`).
* No hay imagen real con referencia que valide el semáforo; sobre imagen real el proyecto lo mantiene en amarillo.
* La franja de referencia usa ecuaciones poblacionales; la correlación entre visitas del mismo feto no se conoce y por eso hay dos escenarios extremos (prueba H17, preregistrada, sin datos).
* La interfaz no se ha probado con usuarios. No hay lupa táctil con precisión de subpíxel más allá de las flechas (¼ de píxel; Mayús, 1 px).
* La página no puede mostrar «cómo se verá el bebé»: una medida de tamaño no determina el aspecto, los rasgos ni la salud.

## Cómo se construye y se publica

```bash
python scripts/build_prototype.py          # ensambla prototype/src/* en los dos archivos
python scripts/build_prototype.py --check  # falla si no coinciden con las fuentes
```

`prototype/calibre_geovida.html` es el fragmento que se publica como artefacto (la plataforma añade el esqueleto). `prototype/calibre_geovida.standalone.html` es el archivo completo, que se abre con doble clic. Solo las tipografías se piden a Google Fonts; sin red usa las del sistema.

## Siguiente

* Medir con dos o más lectores humanos y poner σ con datos (acuerdo de lectores, `geovida.agreement`).
* Maniquíes de verdad conocida fotografiados por la misma cadena (G1) para validar el semáforo sobre imagen real.
* Cuando H17 tenga datos seriados, sustituir los dos escenarios extremos por una correlación medida.
