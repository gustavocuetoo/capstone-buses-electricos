# Solución de la red laboral completa — 6 de octubre de 2026

Se obtuvo un plan para **64.502 viajes, 417 rutas y 7.427 buses**, con costo de **USD 2.638.494,33 para el día modelado**. El resultado cubre todos los viajes bajo los supuestos del método híbrido. No se demostró optimalidad global.

## Comparación

| Etapa | Buses | Costo USD |
|---|---:|---:|
| Construcción inicial | 7.570 | 2.677.607,52 |
| Mejora por parejas | 7.527 | 2.661.514,95 |
| Mejora por tríos: resultado final | 7.427 | 2.638.494,33 |

Respecto de la construcción inicial: **143 buses menos, USD 39.113,19 de ahorro y 1,46% de reducción del costo**. La ejecución de construcción y búsqueda duró 21,40 minutos; las comprobaciones posteriores no están incluidas en ese tiempo.

## Alcance y flota de los parámetros originales

El método dimensiona la flota; no impone el límite de 1.200 buses que aparece en `CODIGO apstone/parameters.csv`. Con ese límite, la instancia completa es imposible: a las **08:00:00 coinciden 6.601 viajes**. Cada uno necesita un bus distinto. Esta cota es independiente de los traslados y de la autonomía; esas restricciones pueden exigir más buses. El listado que acredita la coincidencia se guarda en `testigo_simultaneidad.csv`.

El usuario confirmó que el curso autorizó modificar el parámetro de flota. Por tanto, superar los 1.200 buses no constituye un incumplimiento del alcance autorizado. La incompatibilidad anterior se refiere únicamente a imponer literalmente ese límite a toda la demanda.

Se conservaron batería de 350 kWh, reserva de 35 kWh, consumo de 1,4 kWh/km, velocidad de 18 km/h en vacío, carga de hasta 180 kW en bloques de cinco minutos, los cinco electroterminales originales y los cuatro terminales comunes. Cada bus sirve un solo sector; los recursos de recarga y estacionamiento de los electroterminales son compartidos. Los terminales comunes tienen estacionamiento ilimitado.

Se mantiene el costo del híbrido: USD 250 por bus, USD 0,50 por km, tarifas originales de electricidad y USD 5 por sesión. Las esperas y el estacionamiento no tienen costo en este modelo. El archivo original tiene un costo de espera de USD 0,03/min; esa diferencia ya existía en la metodología anterior.

El día se modela aislado, con batería inicialmente llena y sin exigir reponerla al final. El horizonte completo, calculado con la misma regla de salidas y retornos, va de -7.145 a 99.119 segundos respecto de medianoche. No debe interpretarse este plan como una operación repetible todos los días sin modificar las condiciones energéticas de frontera.

## Costos y operación final

| Componente | USD |
|---|---:|
| Buses | 1.856.750,00 |
| Kilómetros | 762.954,38 |
| Electricidad | 11.604,94 |
| Sesiones de recarga | 7.185,00 |
| Total, calculado antes de redondear | 2.638.494,33 |

Kilómetros totales: 1.525.908,77. Energía comprada: 64.533,53 kWh. Sesiones: 1.437. Los componentes mostrados están redondeados individualmente.

## Verificación

- La entrada contiene todas las 417 rutas y sus 64.502 corridas laborales, sin selección por sector. Incluye exactamente los servicios de la instancia anterior de 212 rutas.
- La construcción inicial pasó la auditoría y la comprobación cruzada contra los datos y auditor originales durante la ejecución.
- Cada mejora aceptada y la exportación final pasaron la auditoría contra la lista fija de servicios de entrada: cobertura exacta, identidad y horarios, continuidad, sector, balance energético, reserva de batería y capacidades compartidas.
- Se volvieron a comprobar las actividades del plan final exportado, reconstruyendo energía y ocupación, y se conciliaron las jornadas, actividades y recargas de los CSV con ese plan. Los costos por bus suman el costo final informado.
- Pasaron las 22 pruebas existentes del constructor y las búsquedas locales, usando la licencia restringida incluida en Gurobi.

La relectura directa de los archivos originales se retrasó inicialmente porque iCloud bloqueó su acceso. Una vez disponibles, se completó y aprobó la validación cruzada del plan final contra las corridas, distancias, parámetros operativos y auditor originales. Se comprobó la igualdad de los 64.502 servicios, el horizonte, todos los CSV y las huellas de las fuentes. `verificacion_final.json` contiene esta verificación final aprobada.

## Esfuerzo de búsqueda

Se asignaron 600 segundos a parejas y 600 a tríos, con ocho vecinos, tres alternativas por grupo, hasta 30 rondas y dos segundos por modelo local. Se aceptaron 651 mejoras por parejas y 138 por tríos. Se enviaron 40.070 modelos locales; 48 excedieron el tamaño de la licencia restringida y se descartaron. Por estas limitaciones y por el carácter local de la búsqueda, el resultado es una solución encontrada, sin garantía de óptimo global.

## Entregables

- `04_final/planes.json`: secuencia completa de cada bus.
- `04_final/jornadas.csv`: asignaciones, kilómetros, energía y costos por bus.
- `04_final/actividades.csv`: viajes, traslados, esperas y cargas con energía reconstruida.
- `04_final/recargas.csv`: calendario de carga.
- `04_final/resumen.json`: indicadores y ocupaciones máximas verificadas.
- `comparacion.json`, `comparacion_etapas.csv`: evolución y tiempos de la búsqueda.
- `verificacion_final.json`: auditoría de exportados y huellas de los entregables.
- `testigo_simultaneidad.csv`: los 6.601 servicios activos a las 08:00.

Se conservó una copia local adicional fuera de la carpeta de iCloud en `/Users/anitasepulveda/.codex/artifacts/capstone_417_20261006/`, incluyendo los cinco archivos finales, este informe y la verificación.

## Reproducción

La entrada autocontenida está en `metodo_hibrido/instancia_417`. El script `preparar_completa.py` la genera desde los datos originales y rechaza sobrescribir una instancia existente.

Desde la raíz del proyecto, con el entorno preparado:

```sh
.venv-optimizacion/bin/python metodo_hibrido/buscar_mejor.py \
  --instancia metodo_hibrido/instancia_417 \
  --salida metodo_hibrido/resultados/completa_417_repetida \
  --presupuesto 600 --rondas 30 --licencia-restringida
```

`buscar_mejor.py` admite ahora `--instancia`, por lo que también permite continuar planes de esta red usando `--desde`. Para repetir la auditoría directa contra las fuentes originales:

```sh
.venv-optimizacion/bin/python -m metodo_hibrido.verificar_completa \
  metodo_hibrido/resultados/completa_417_20261006
```

Las carpetas de las soluciones anteriores se conservaron.
