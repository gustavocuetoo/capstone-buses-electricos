# Implementación de la fase 1

La formulación completa está en `MODELO_MATEMATICO.md`. `terminales_espera.json` conserva nombres, direcciones, coordenadas aproximadas, fuentes y dudas pendientes. `configuracion.json` fija la velocidad de traslados vacíos en 18 km/h.

## Instalación

Python 3.12, numpy, scipy y gurobipy. El equipo dispone de una licencia académica compatible con Gurobi 12; la prueba de instalación reportó vencimiento el **6 de octubre de 2026**. No se alteró la licencia.

Las bibliotecas se instalaron en `.deps` dentro del proyecto, sin modificar los datos originales. Los scripts incorporan esa ruta. Para otro entorno:

```text
python -m pip install -r fase1/requirements.txt
```

## Ejecutar

Desde la carpeta Capstone:

```text
python fase1/preparar.py
python fase1/modelo.py --rutas 101 --dia L
python -m unittest fase1.test_modelo test_distancias_electroterminales
```

Mientras Los Acacios esté pendiente, la preparación y las pruebas deben usar expresamente `--permitir-pendientes`:

```text
python fase1/preparar.py --permitir-pendientes
python fase1/modelo.py --rutas 101 --dia L --permitir-pendientes
```

El modelo inicial selecciona todas las corridas laborales de la ruta 101, sin truncarlas. Para otra selección:

```text
python fase1/modelo.py --rutas 101,102 --dia L --salida output/fase1/prueba_101_102 --permitir-pendientes
python fase1/modelo.py --todas --sector 1 --dia L --tiempo-limite 300 --salida output/fase1/sector_1 --permitir-pendientes
```

El segundo comando amplía considerablemente el tamaño; no supone que todos los sectores se hayan resuelto ya. `--limite N` es una reducción EXPRESA para pruebas, no debe usarse para reportar cobertura de un día completo. `--todas` sin sector selecciona toda la red y mantiene las restricciones de sectorización.

## Entradas y salidas

`preparar.py` genera en `output/fase1`:

- `corridas.csv`: todas las salidas reconstruidas L/S/D, con identificador único, sector y extremos. Conserva horas más allá de medianoche.
- `sectores.csv`: sector elegido para cada ruta completa, manteniendo ambos sentidos juntos.
- `traslados.csv`: conexiones dirigidas final-inicio, final-terminal de espera y terminal de espera-inicio; kilómetros y segundos a 18 km/h. Mismas paradas tienen distancia y tiempo cero. La columna `estado` señala accesos para revisar.
- `metadatos.json`: velocidad usada, terminales activos y pendientes y cobertura de distancias.
- `red_vial_cache.npz` y `puntos_red_cache.json`: red y proyecciones para futuras ampliaciones. No son entradas que se deban modificar manualmente.

El modelo lee también las distancias previamente construidas a los cinco electroterminales y convierte los retornos a segundos a 18 km/h. Una distancia ausente produce un error; una conexión explícitamente sin camino se excluye, no se reemplaza por cero.

Cada ejecución genera en su carpeta:

- `resultado.json`: alcance, costo, flota, cobertura, distribución inicial/final, cota de simultaneidad y estado del solver.
- `jornadas.csv`: resumen de cada bus.
- `actividades.csv`: arcos elegidos y servicios de cada bus. Los traslados pueden incluir espera residual; `espera_min` la separa de su tiempo de movimiento. Los nodos permiten auditar continuidad.
- `modelo.mps`, `solucion.sol` y `gurobi.log`: modelo y evidencia reproducible de resolución.

Los buses de esta salida NO están certificados como factibles eléctricamente. No se calculó SOC ni recarga. Tampoco se simuló todavía una semana.

## Verificaciones

Se comprueban cobertura única, flujos enteros, balances, tiempos de conexiones entre servicios, capacidad final compartida de los electroterminales, flota no inferior a simultaneidad y reconciliación del costo. Las pruebas pequeñas incluyen ida-vuelta sin retorno vacío, corridas superpuestas, traslado que no alcanza, espera cobrada y capacidad final compartida entre sectores.

## Fuentes

GTFS, `depots.csv`, `shape_distances.csv`, `parameters.csv`, distancias previamente construidas y `chile.gpkg` del proyecto. Fuentes geográficas adicionales y discrepancias están registradas por terminal. La red de calles conserva las limitaciones descritas en `output/distancias_electroterminales/LEEME.md`.
