# Correr la respuesta perfecta (MILP) en los casos medianos

Objetivo: probar el óptimo en casos más grandes que los chicos, para medir qué tan lejos queda
la heurística de cuartetos. En un Mac de 8 GB no cabe: el caso de 200 corridas usó ~13 GB.

## Casos

Están en `09-entrega3/octetos/casos/`. Todos son del sector 1, y cada caso contiene las rutas
del anterior:

| Caso | Corridas |
|---|---|
| `mediano_200_sector_1_2_rutas` | 200 |
| `mediano_250_sector_1_3_rutas` | 255 |
| `mediano_300_sector_1_4_rutas` | 298 |
| `mediano_400_sector_1_5_rutas` | 405 |

Cada carpeta trae todo lo necesario: `corridas.csv`, `distancias.csv` y `escenario.json`.

## Preparar el computador (una vez)

1. Instala Python 3.9 o más nuevo.
2. Instala tu licencia académica de Gurobi (`grbgetkey ...`). La licencia gratuita de pip no alcanza.
3. Desde la raíz del repositorio, crea el entorno:

```bash
python3 -m venv .venv-optimizacion
```

```bash
.venv-optimizacion/bin/pip install "gurobipy>=12,<13" numpy pytest
```

4. Comprueba que todo esté bien. Deberían pasar todas las pruebas:

```bash
.venv-optimizacion/bin/python -m pytest -q 09-entrega3/octetos/test_correr_metodos.py
```

## Correr

Solo la respuesta perfecta, de 2 horas como máximo por caso. Los casos se resuelven en orden,
del más chico al más grande:

```bash
.venv-optimizacion/bin/python 09-entrega3/octetos/correr_metodos.py --instancias 09-entrega3/octetos/casos/mediano_* --metodos exacta --presupuestos 7200 --presupuesto-exacta 7200 --salida 09-entrega3/octetos/resultados/casos_medianos_exacta.csv
```

- Si se corta, vuelve a lanzar el mismo comando con `--continuar` al final: retoma con los casos
  que faltan.
- Mientras corre, revisa la memoria. Si el computador empieza a usar el disco como memoria,
  conviene detener el caso de 400.
- Si un caso no termina en 2 horas, queda anotado como error, sin cota inferior.

## Qué devolver

Haz commit y push de `09-entrega3/octetos/resultados/casos_medianos_exacta.csv`, o envíalo por
el chat del grupo. Agrega cuánta memoria (RAM) tiene tu computador.
