# Arquitectura del programa «Geometría de la Vida» (geovida)

> Solo investigación y educación. Un único programa con un núcleo (instrumento + certificado), dos programas de investigación, una rama de datos reales y un paquete de gobernanza.
> **Validado con imagen real: nada todavía** (una imagen medida en el piloto REAL2D, n = 1, sin validar).

```mermaid
flowchart TB
  subgraph N[Núcleo]
    P[phantoms / twod / imaging<br/>fantomas con verdad conocida] --> M[measure / biometry<br/>medidas V, S, topología, longitud, grosor]
    M --> C[certificate / biometry<br/>modelo de error + semáforo]
    C --> G[domain / compuerta H14<br/>guardia fuera de lo calibrado]
  end
  subgraph A[Programa A · forma 3D/4D]
    A1[H1-H5 ley de error] --> A2[H6-H8 semáforo, 4D] --> A3[H9-H12 topología, ecografía simulada]
  end
  subgraph B[Programa B · biometría temprana]
    B1[H13 datación y decisión] --> B2[H14 compuerta] --> B3[H15 robustez a pantalla/impresión/foto]
  end
  subgraph R[Rama de datos reales]
    R1[realdata · volúmenes 3D NIfTI<br/>H11 / H12R pendientes] 
    R2[real2d · foto/2D con regla<br/>piloto REAL2D n=1 medido]
    R3[trajectory · franja de referencia<br/>H17 pendiente de datos seriados]
  end
  subgraph Y[Gobernanza]
    Y1[labeling · compuerta de consentimiento] 
    Y2[atlas Carnegie · rotulado · niveles de evidencia]
    Y3[clinico/ · riesgos, ciclo de vida, trazabilidad, ficha]
    Y4[panel de revisión · propuesta]
  end
  N --> A
  N --> B
  A --> R1
  B --> R2
  R --> Y
```

## Dónde está cada cosa

| Capa | Módulos | Documentos | Estado |
|---|---|---|---|
| Núcleo | `phantoms`, `twod`, `imaging`, `measure`, `segment`, `certificate`, `domain`, `biometry` | `docs/METODOS.md`, `docs/clinico/FICHA_DEL_MODELO.md` | Probado en simulación |
| Programa A | `h3`…`h12`, `growth`, `traj4d`, `scaleaxis`, `topomargin` | `RESULTADOS_V02`…`V05` | Confirmatorio en simulación |
| Programa B | `dating`, `atlas`, `biometry`, `h13`, `h14`, `h15` | `RESULTADOS_V06`, `PREREGISTRO_H13/H14/H15` | Confirmatorio en simulación |
| Datos reales | `realdata` (3D), `real2d` (2D), `trajectory` (franja de referencia) | `GUIA_DATOS_REALES`, `REAL2D_METODO`, `PREREGISTRO_REAL2D_PILOTO`, `PREREGISTRO_H11`, `PREREGISTRO_H12R` | Código listo; **sin imágenes reales medidas** |
| Acuerdo y color | `agreement` (solapamiento, distancia de contorno, Bland–Altman), `colorbar` (linealiza un mapa de color con la barra de la captura) | `INTEGRACION_PDF_EXTERNO`, `RESULTADOS_V09` | Probado con datos sintéticos; sin comparaciones reales |
| Gobernanza | `labeling`, `provenance` | `ATLAS_ESTADIOS`, `PANEL_DE_REVISION`, `clinico/*`, `ERRATA`, `RUTA_DE_VALIDACION_REAL` | Borrador; el panel no existe |
| Interfaces | `cli` (`plan`, `datasheet`, `certify`, `real2d`, `trajectory`) | `README`, laboratorio y exposición (v0.4), visor Unity sin compilar | Parcial |

## Principios que atraviesan todo

1. **Preregistrar antes de mirar**; lo que se ve antes se declara y se prueba con semilla nueva.
2. **Abstenerse es un resultado**: fuera de lo calibrado, el certificado se niega a dar verde.
3. **La simulación no se vende como real**: sobre imagen real el semáforo no sale verde hasta validar.
4. **Los errores propios se publican** (`ERRATA.md`), con causa y prevención.
5. **Privacidad por diseño**: nada identificable en el repositorio; los informes no llevan nombres ni rutas.
