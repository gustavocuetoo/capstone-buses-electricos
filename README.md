# Capstone ICS2122 — Planificación de la operación de buses eléctricos (RED, Santiago)

Problema P7. Programar la operación diaria de una flota finita de buses eléctricos
en la Red Metropolitana de Movilidad, con autonomía limitada y recarga en
electroterminales de capacidad restringida.

Nombre del problema en la literatura: **MD-E-VSP** (*Multi-Depot Electric Vehicle
Scheduling Problem*) con *charging scheduling* acoplado.

---

## Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| `00-enunciado/` | Enunciado P7, lineamientos de las Entregas 1 y 2 y el brief del agente de investigación. |
| `01-datos/` | Datos entregados por el curso, incluida la red vial `chile.gpkg`. **Solo lectura: nunca se modifican.** |
| `02-codigo/` | Scripts de análisis de la Entrega 1. |
| `03-resultados/` | Salidas de `02-codigo/`: figuras, macros y tablas LaTeX. **Regenerable, no editar a mano.** |
| `04-documentos/` | Documentos de trabajo en LaTeX (bibliografía, supuestos, preguntas, análisis). |
| `05-entrega1/` | Entrega 1: presentación entregada (`Presentación_1.pdf`), fuente LaTeX de la presentación e informe entregado (`informe/`). |
| `07-interrogacion1/` | Guía de estudio de la interrogación 1. |
| `08-entrega2/` | Entrega 2: informe en LaTeX (`informe2/`), barrido de presupuesto (`sensibilidad_presupuesto/`), presentación del grupo y guía de preparación. |
| `CODIGO apstone/` | Código del grupo: Fase 1, prototipo de tres fases y caso base miope (`tres_fases/caso_base.py`). `chile.gpkg`, `gtfs/` y `mapa_red.png` son enlaces a `01-datos/`. |
| `metodo_hibrido/` | Método híbrido (construcción cronológica + parejas y tríos con Gurobi), sus instancias y corridas en `resultados/`. |
| `caso_base_simple_gurobi/` | Caso base sin recargas resuelto con Gurobi. |
| `graphify-out/` | Grafo de conocimiento del repositorio (ver `CLAUDE.md`). |

Las corridas de `metodo_hibrido/resultados/presupuesto/` guardan solo los resúmenes
(`comparacion.json`, `busqueda.json`, `jornadas.csv`, …): el detalle (`planes.json` y
`actividades.csv` de cada etapa) se quitó el 13-oct-2026 para liberar espacio. Para
re-auditar una de esas corridas hay que volver a correrla con `barrido.py`.

---

## Cómo reproducir todos los números

```bash
python3 02-codigo/analisis_datos.py     # descriptivos del día de operación
python3 02-codigo/entrega1_kpis.py      # instancias, KPIs, complejidad y calidad de datos
python3 02-codigo/figuras_informe.py    # figuras y macros del informe de la Entrega 1
cd 04-documentos && ./compilar.sh       # documentos de trabajo -> 04-documentos/pdf/
cd 05-entrega1/presentacion && ./compilar.sh   # presentación -> presentacion1.pdf
```

Los dos scripts escriben en `03-resultados/`. Los documentos LaTeX leen esas
macros y tablas, de modo que **ninguna cifra está escrita a mano**: si cambia un
dato, se regenera y todo el texto queda consistente.

## Módulos de código

| Archivo | Rol |
|---|---|
| `02-codigo/analisis_datos.py` | Carga del GTFS, expansión de frecuencias a corridas, descriptivos y figuras. |
| `02-codigo/geografia.py` | Reconstrucción de los terminales de cada viaje y distancias de traslado en vacío. |
| `02-codigo/entrega1_kpis.py` | Instancias, KPIs, complejidad combinatoria y batería de verificación de datos. |
| `02-codigo/tablas.py` | Escritura de tablas LaTeX con el estilo del informe. |
| `02-codigo/figuras_informe.py` | Figuras y macros del informe entregado. Usa el filtro `agency_id=RM` + `route_type=3` y verifica las cifras publicadas. |

## Supuestos codificados (todos revisables)

| Supuesto | Valor | Dónde |
|---|---|---|
| Día de operación analizado | servicio `L` (lunes a viernes) | `analisis_datos.py` |
| Solo buses: se descartan Metro y Metrotren | `route_type == 3` | `analisis_datos.py` |
| Velocidad de traslado en vacío | 25 km/h | `geografia.py` |
| Factor de rodeo sobre distancia recta | 1,35 | `geografia.py` |
| Conexión mínima entre dos viajes de un bus | 5 min | `entrega1_kpis.py` |

## Estado

Informe de la Entrega 2 (entrega 16-oct-2026): ver [`08-entrega2/informe2/PLAN.md`](08-entrega2/informe2/PLAN.md).
Se compila con `cd 08-entrega2/informe2 && ./compilar.sh`.
