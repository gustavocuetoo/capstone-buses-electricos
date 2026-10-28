# Qué va al repositorio de GitHub (propuesta para el grupo)

El informe tiene que traer el enlace a un repositorio con el código ordenado. Este archivo propone qué subir para que cualquiera pueda reproducir cada cifra del informe 2. El repositorio lo crea el grupo; nada de esto se ha subido.

**Hay que conservar las rutas relativas tal como están en `Proyecto/`**: los scripts del informe (`08-entrega2/informe2/scripts/fuentes.py`) buscan los resultados por esas rutas.

## Código

| Carpeta o archivo | Qué es |
|---|---|
| `metodo_hibrido/*.py` | Método híbrido: construcción, parejas, tríos, MILP local, auditor y sus 22 pruebas |
| `metodo_hibrido/instancia_212/` | Instancia de 212 rutas: `corridas.csv`, `distancias.csv`, `escenario.json` (5,7 MB) |
| `metodo_hibrido/instancia_417/corridas.csv` | Corridas de la red completa; el capítulo 2 las usa para comparar la muestra con la red |
| `CODIGO apstone/tres_fases/` | Prototipo de tres fases y el caso base miope (`caso_base.py`, `test_caso_base.py`) |
| `caso_base_simple_gurobi/` (sin `corrida_gurobi/planes.json`) | Caso base sin recargas de la presentación |
| `01-datos/parameters.csv`, `01-datos/depots.csv` | Parámetros y electroterminales del curso |
| `08-entrega2/informe2/` (sin `salidas/*.png` ni archivos auxiliares de LaTeX) | El informe: `.tex`, `scripts/`, `figures/`, `tablas/` y `salidas/auditoria_miope.json` |

## Resultados: solo los archivos que leen los scripts

Las carpetas completas pesan unos 150 MB cada una por las etapas intermedias. Basta con subir:

- `metodo_hibrido/resultados/mejor_20261006_600/`: `comparacion.json`, `comparacion_etapas.csv`, `ejecucion.json`, `licencia.json`.
- `metodo_hibrido/resultados/mejor_20261006_refinamiento/`: lo mismo, más `verificacion_final.json`, `INFORME.md` y `04_final/` (`resumen.json`, `jornadas.csv`, `actividades.csv`, `recargas.csv`; `planes.json` es opcional, 28 MB).
- `metodo_hibrido/resultados/presupuesto/B*/comparacion.json`: las 15 corridas del barrido.
- `CODIGO apstone/output/tres_fases/muestra_212/resumen.json`: piso de la Fase 1 y prototipo.
- `CODIGO apstone/output/tres_fases/muestra_212_trios/comparacion.json`: prototipo con mejoras.
- `CODIGO apstone/output/tres_fases/muestra_212_caso_base*/`: `resumen.json`, `jornadas.csv`, `actividades.csv`, `recargas.csv` del caso base miope y de sus umbrales.
- `caso_base_simple_gurobi/corrida_gurobi/resumen.json`.

## No subir

Entornos (`.venv*`, `.deps`), `__pycache__/`, `graphify-out/`, `CODIGO apstone/tmp/`, PDFs del curso y de otros grupos, y licencias de Gurobi (`gurobi.lic`).

## Borrador del README raíz

```markdown
# Planificación de buses eléctricos — Grupo 29 (ICS2122, 2026-2)

## Requisitos
Python 3.12 con numpy, matplotlib y gurobipy 12 (la licencia restringida que trae el paquete basta).
Para el informe: una distribución de LaTeX con latexmk.

## Pruebas
python -m unittest metodo_hibrido.test_hibrido metodo_hibrido.test_caso_base   # 22 pruebas del método
cd 08-entrega2/informe2 && python3 -m unittest discover -s scripts -p 'test_*.py'   # pruebas de las cifras

## Reproducir la solución del informe (unos 30 minutos)
python metodo_hibrido/buscar_mejor.py --salida mejor_600 --presupuesto 600 --vecinos 8 --alternativas 3 --rondas 30 --licencia-restringida
python metodo_hibrido/buscar_mejor.py --salida refinamiento --desde mejor_600/04_final/planes.json --presupuesto 240 --vecinos 12 --alternativas 5 --rondas 30 --licencia-restringida
El presupuesto se mide en segundos de reloj: el resultado es similar, no idéntico, según el equipo.

## Reproducir el caso base
python "CODIGO apstone/tres_fases/caso_base.py" --base "CODIGO apstone/output/tres_fases/muestra_212"
python 08-entrega2/informe2/scripts/auditar_miope.py   # lo revisa con el auditor del método híbrido

## Compilar el informe
cd 08-entrega2/informe2 && ./compilar.sh   # genera cifras y figuras, compila y revisa las reglas
```
