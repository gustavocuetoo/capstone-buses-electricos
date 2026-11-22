# KPI y uso de electroterminales

Scripts para calcular todos los KPI de cada plan y el uso de los cargadores de cada electroterminal
durante el día, para el caso base y el método, en día laboral, sábado y domingo. Responden a lo que
pidió el profesor en la reunión del 17-nov: calcular todos los KPI y revisar la ocupación de cada
electroterminal a lo largo del día.

No dependen de la elección de cuartetos, octetos u otra agrupación: leen planes ya resueltos y
auditados. Para el plan final, basta agregar su carpeta en `PLANES` de `planes.py`.

## Uso

Desde la raíz del repositorio (solo necesita pandas y matplotlib, sin Gurobi):

```bash
python3 09-entrega3/kpi/kpi_planes.py
python3 09-entrega3/kpi/uso_electroterminales.py
python3 -m pytest -q 09-entrega3/kpi/
```

La ocupación de plazas necesita `actividades.csv`, que no está en GitHub pero sí en las carpetas
`04_final` del computador donde se corrió el método:

```bash
python3 09-entrega3/kpi/ocupacion_plazas.py --plan metodo_hibrido/resultados/completa_417_20261006/04_final --nombre metodo_L
```

El script comprueba que su pico coincida con la `ocupacion_maxima` del auditor.

## Archivos

| Archivo | Qué hace |
|---|---|
| `planes.py` | Lista de planes, lectura de `resumen.json`, `jornadas.csv` y `recargas.csv`, y validación de que los tres cuadren |
| `kpi_planes.py` | 30 KPI por plan, ahorro del método contra el caso base y tabla por sector |
| `uso_electroterminales.py` | Perfil de carga por electroterminal en bloques de 5 min, resumen, matriz sector × electroterminal y figuras |
| `ocupacion_plazas.py` | Ocupación de plazas por electroterminal cada 5 min desde `actividades.csv`, separando buses cargando, esperando durante la operación y estacionados al cierre |
| `test_kpi.py`, `test_ocupacion_plazas.py` | Pruebas con planes chicos y con los planes del repositorio |
| `resultados/` | Salidas: CSV, `kpi_planes.md` y figuras PNG |

## Controles

- Antes de usar un plan se comprueba que `jornadas.csv`, `recargas.csv` y `resumen.json` den los mismos
  buses, corridas, km, energía, sesiones y costo. Los seis planes cuadran.
- El pico de buses cargando a la vez en cada electroterminal coincide con el que reportó el auditor en
  `resumen.json` (`cargas_simultaneas_maximas`), en los seis planes.

## Planes usados

| Plan | Carpeta |
|---|---|
| Caso base L, S, D | `codigo/output/tres_fases/red_417_{L,S,D}_caso_base/` |
| Método L | `metodo_hibrido/resultados/completa_417_20261006/04_final/` (7.427 buses) |
| Método S, D | `metodo_hibrido/resultados/completa_417_{S,D}_20261027/04_final/` |

El plan de cuartetos (7.351 buses) no tiene `jornadas.csv` ni `recargas.csv` en el repositorio. Cuando
esté, se agrega a `PLANES` y las cifras se recalculan solas.

## Primeros hallazgos (día laboral)

- **Ahorro contra el caso base:** −1.257 buses (−14,5 %) y −USD 424.223 al día (−13,9 %). En sábado,
  −14,6 % de buses; en domingo, −10,0 %.
- **Los cargadores no son el cuello de botella del método.** El pico es de 21 a 45 buses cargando a la
  vez, entre 17,5 % y 26 % de las conexiones, y ocurre entre las 17:00 y las 19:30, casi siempre antes
  del tramo caro de 19:00 a 22:00. El caso base, que recarga al 100 %, llena las conexiones de E2, E4 y E5 entre las
  20:00 y las 22:00.
- **Las plazas llegan al 100 % al menos al cierre del día.** En el método, exactamente 700
  buses terminan el día estacionados en un electroterminal: 180 + 150 + 150 + 120 + 100, que es la
  capacidad total. Por eso la verificación reporta ocupación máxima de plazas igual a la capacidad. En
  el caso base ningún bus termina en un electroterminal. Para saber si también se llenan durante la
  operación hace falta la ocupación de plazas hora a hora, que necesita `actividades.csv`.
- **Desbalance entre sectores.** El sector 3 (Los Espinos) carga solo el 34 % de su energía en su propio
  electroterminal, y el 38 % en E2 El Conquistador y el 20 % en E5 Santa Rosa. Los demás sectores
  cargan entre 53 % y 77 % en el suyo. Santa Rosa (sector 5, 117 rutas) carga el 64 % en el suyo.
- **La energía casi no pesa en el método:** 0,4 % del costo. Se carga el 3,0 % de la energía consumida,
  porque los buses parten llenos y terminan con 71 kWh en promedio. Para repetir el día habría que
  reponer 2,07 GWh de noche.
