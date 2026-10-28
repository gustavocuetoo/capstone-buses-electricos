# Implementación compacta de las tres fases

**Más del 50% del universo laboral verificado:** el ensayo de 212 rutas cubre el 50,84% de las rutas y el 51,50% de las corridas laborales, conservando las 100 rutas anteriores. La operación final cubre 33.220 corridas con 4.175 buses y costo USD 1.459.572,80. Se redujo el uso de memoria de la representación de la red, sin modificar la formulación. Véase [ESCALA_MITAD_RED.md](ESCALA_MITAD_RED.md) para cobertura, tiempos, restricciones y comandos.

**Ampliación a 100 rutas completada:** se conservaron las 50 rutas anteriores y se añadieron 50, hasta veinte por sector. Las 15.268 corridas laborales terminan con 1.782 buses y costo USD 632.889,30 tras reparación, parejas conjuntas y grupos de tres; toda la operación pasó la auditoría. Véase [ESCALA_100_RUTAS.md](ESCALA_100_RUTAS.md) para selección anidada, tiempos, resultados y límites. Las cifras siguientes conservan la evolución histórica del proyecto.

**Grupos de tres jornadas:** `--grupo 3 --coordinacion conjunta` permite repartir los servicios de una jornada entre otras dos y rotar los tramos finales de tres jornadas. Sobre las mismas 50 rutas, desde 883 buses, obtuvo 858 buses y USD 302.712,91. Un control por parejas desde la misma entrada obtuvo 881 buses; ambos usaron dos minutos de búsqueda. Véase [TRES_JORNADAS.md](TRES_JORNADAS.md) para el alcance y los límites de esta comparación.

**Coordinación conjunta implementada:** `--coordinacion conjunta` permite decidir simultáneamente recargas y terminales de dos jornadas. Partiendo de los 886 buses del ensayo de 50 rutas, obtuvo 883 buses y USD 308.719,85. Un control secuencial desde la misma entrada y con igual presupuesto obtuvo también 883 buses, con USD 172,15 más de costo. Véase [RECARGA_CONJUNTA.md](RECARGA_CONJUNTA.md) para el modelo, pruebas y comparación. Los resultados históricos siguientes se conservan como referencia.

**Ensayo de escala: 50 rutas verificadas.** El ejecutor admite ahora `--cantidad 50`. La muestra comprende 7.413 corridas laborales, diez rutas por sector, y termina con 886 buses después de reparación e intercambios. Se conservan las muestras anteriores. Véase [ESCALA_50_RUTAS.md](ESCALA_50_RUTAS.md) para resultados, tiempos y alcance recomendado para la entrega.

**Actualización 5 de octubre de 2026:** ya se permiten intercambios entre dos jornadas del mismo sector. Sobre la solución reparada de 20 rutas, la búsqueda de dos minutos reduce la flota de 507 a 467 buses y el costo de USD 174.702,43 a USD 164.004,80, con todas las restricciones verificadas. Véase [INTERCAMBIOS.md](INTERCAMBIOS.md) para el procedimiento, límites y comandos. Las tablas siguientes conservan resultados anteriores para comparación.

**Actualización: reparación local disponible.** Después de ejecutar las tres fases se puede usar `python tres_fases/mejorar.py`. Mantiene las rutas y jornadas de las fases 1–2 y reconsidera las recargas de fragmentos de una misma cadena mediante pequeños modelos locales en Gurobi. La comparación de 20 rutas baja de 513 a 507 buses y de USD 176.228,65 a USD 174.702,43. La reparación final tardó 2,14 segundos adicionales. Véase [REPARACION_LOCAL.md](REPARACION_LOCAL.md) para interpretar el resultado y sus límites. Los resultados de la versión inicial que siguen se conservan como referencia.

Implementado y ejecutado el 4 de octubre de 2026. El objetivo de esta versión es obtener una programación laboral comprobable y rápida, y disponer de una base que pueda ampliarse. Hay un modelo de optimización en la fase 1 y algoritmos heurísticos en las fases 2 y 3. No se implementa un MILP global por bus.

## Resultados observados

Cada caso incluye **todas las corridas laborales** de las rutas indicadas, con sus sentidos y variantes. Una ruta no equivale a una sola salida.

| Caso | Corridas | Buses fase 2, sin batería | Buses finales verificados | Sesiones de recarga | Tiempo total interno |
|---|---:|---:|---:|---:|---:|
| Ruta 101 | 171 | 21 | 26 | 5 | 3,63 s |
| 10 rutas | 2.164 | 271 | 314 | 63 | 4,52 s |
| 15 rutas | 2.169 | 224 | 288 | 53 | 5,23 s |
| 20 rutas | 4.001 | 422 | 513 | 113 | 7,20 s |

Los cuatro casos pasan la auditoría de cobertura exacta, continuidad espacial y temporal, batería, potencia, conexiones y capacidad física compartida. El costo final es respectivamente USD 8.864,71; 106.321,89; 97.920,53 y 176.228,65. Son costos del escenario de un día aislado con energía inicial dada; no incluyen comprar esa energía inicial ni recuperar el SOC al terminar.

Los ensayos de 10, 15 y 20 rutas usan muestras distintas, no anidadas: seleccionan cuantiles interiores de longitud media dentro de cada uno de los cinco sectores. Por eso 15 rutas pueden requerir menos buses que 10. Son pruebas de funcionamiento y tamaño, no una comparación controlada de escalabilidad ni una muestra estadística de toda RED. La selección ocurre antes de resolver, sin escoger rutas según sus resultados. Los IDs, sectores y cantidades están en `seleccion_rutas.csv` de cada ensayo.

Con 20 rutas, la fase 1 contiene 7.929 nodos y 88.682 variables de flujo y se resolvió en 0,65 s. El tiempo total incluye carga de CSV, construcción, solución, heurísticas, auditoría y exportación, pero excluye arranque del intérprete y generación previa de matrices. Equipo observado: Intel i5-10210U, Gurobi 12.0.3, cuatro hilos. Los tiempos dependen del equipo y la muestra. **Esto no garantiza resolver las 417 rutas en tiempos similares.**

## Supuestos aplicados

| Elemento | Valor o decisión |
|---|---|
| Servicios | Solo `service_id=L`; horarios y duración de los CSV derivados de GTFS |
| Tiempo vacío | `ceil(distancia_km × 3600 / 18)` segundos; 18 km/h no se aplica al servicio |
| Batería | 350 kWh, mínimo 35 kWh, máximo 350 kWh |
| Estado inicial | Todos los buses al 100% en el comienzo común del horizonte |
| Consumo | 1,4 kWh/km en servicio y en vacío; sin auxiliares ni pérdidas |
| Recarga | Hasta 180 kW; bloques completos de 300 s, hasta 15 kWh por bloque |
| Costo fijo | USD 250 por bus utilizado en la instancia |
| Kilómetros | USD 0,5/km en servicio y en vacío |
| Recargas | Energía según `electricity_prices.csv` y USD 5 por conexión continua |
| Espera, tiempo de carga y estacionamiento | Sin costo |
| Terminales comunes | T01 Pajaritos/Las Araucarias; T02 Miguel Mujica; T03 El Salto; T04 El Roble |
| Los Acacios | T05 excluido por decisión del grupo; no requiere coordenadas para este escenario |
| Espera | Permitida en extremos de servicios y terminales; regulación mínima cero |
| Estacionamiento común | Ilimitado, sin cargadores |
| Electroterminales | Cinco originales, sin cambiar coordenadas ni capacidades |
| Disponibilidad de E | 24 horas como supuesto; no se ha incorporado un calendario de cierres |
| Final | Terminal común o electroterminal; puede diferir del inicial; SOC ≥10%, sin objetivo adicional |
| Sectores | Los servicios de una ruta permanecen en su sector; todos acceden a los mismos cinco E |
| Flota | Cantidad endógena, sin imponer el valor histórico de 1.200 buses |

| Electroterminal | Capacidad física | Conexiones simultáneas |
|---|---:|---:|
| E1 Vespucio Norte | 150 | 150 |
| E2 El Conquistador | 180 | 180 |
| E3 Los Espinos | 120 | 120 |
| E4 La Reina | 100 | 100 |
| E5 Santa Rosa | 150 | 150 |

La capacidad física se lee de `depots.csv`; las conexiones, de `charger_capacity.csv`. Son restricciones diferentes aunque coincidan los números. No se supone un límite de potencia de transformador que no esté disponible en los datos.

**Horizonte:** para cubrir salidas cercanas a las 00:00, el inicio operacional se extiende hacia atrás lo suficiente para los traslados iniciales. Por ello aparecen segundos negativos respecto de las 00:00 y horas superiores a 24 al final. El 100% inicial se fija en ese inicio operacional, no se repone a medianoche. Un bus incorporado al dividir una jornada también existe desde ese instante y espera en un T hasta salir. El fin común incluye los retornos; todos los buses quedan estacionados hasta ese fin. Esto representa un día de servicio aislado y no la continuidad de varios días.

## Fase 1: flujo agregado de costo mínimo

Se reutiliza `fase1/modelo.py`, pasando los parámetros actuales desde el nuevo ejecutor: el costo de espera antiguo no se usa. Los nodos representan sector, lugar e instante. Hay arcos de servicio, espera, traslado, salida de terminal, retorno y cierre de flota.

Con flujo `x_a`, distancia `d_a` y flujo de cierre `F`, se minimiza:

`250 F + 0,5 Σ_a d_a x_a`.

Restricciones:

- Conservación de flujo en cada nodo.
- Flujo exactamente uno en cada arco de servicio obligatorio.
- Límites inferiores y superiores de cada arco.
- Capacidad física del estacionamiento final en E; T sin límite.
- Compatibilidad espacial, temporal y sectorial representada en los arcos.

Se resuelve como programación lineal de red. La matriz de incidencia y cotas enteras permiten obtener un flujo entero en una solución básica; el código comprueba integralidad y balances antes de descomponer. Un resultado fraccionario no se convierte arbitrariamente en buses. Si no hay solución, el ejecutor se detiene; ante infactibilidad demostrada se genera IIS.

El óptimo demostrado corresponde a esta fase sin energía. El número de buses de esa solución **no es un mínimo de flota demostrado por separado**: la función pondera buses y kilómetros.

## Fase 2: construir jornadas sin variables individuales

Se recorre el flujo positivo en orden topológico, retirando el arco de cierre. Cada unidad que sale del origen genera un prefijo de jornada. Cuando confluyen prefijos en el mismo nodo, los de mayor consumo acumulado reciben primero las continuaciones de menor consumo estimado hasta el siguiente servicio. Es una regla local de balance, no una optimización energética global.

Cada unidad de flujo se utiliza exactamente una vez. Se comprueba que no queden arcos sin descomponer y que las jornadas conserven cobertura, horarios, sectores, capacidad final y costo de fase 1. La estimación acumulada no es el SOC: **la factibilidad de batería se comprueba después**.

## Fase 3: recargas y reparación mediante división

Las jornadas se procesan por hora del primer servicio, con desempate por longitud e ID. Se simulan los movimientos y el estado energético:

`E_siguiente = E_actual − 1,4 × km + q`, con `35 ≤ E ≤ 350`.

En cada hueco entre servicios, si el consumo previsto del resto de la cadena supera la energía disponible, se consideran los cinco electroterminales. Se buscan bloques consecutivos libres que permitan llegar, cargar y alcanzar la siguiente salida. Se elige primero la mayor ganancia energética neta del desvío; luego el menor costo de energía, kilómetros y conexión. Se admite carga parcial, con `0 ≤ q_bloque ≤ 15 kWh`.

Un único calendario para todos los sectores reserva conexiones y presencia física. El bus espera en el extremo anterior hasta el momento de partir hacia la carga, y sale del E al terminar. La ocupación física se registra a segundo entero, incluyendo estacionamiento final; las conexiones se registran por bloque. Los intervalos son `[inicio, fin)`, para permitir reemplazos exactamente en el límite.

Si no se consigue el siguiente servicio con energía suficiente, termina la jornada anterior y el resto se asigna a un bus nuevo. Ambos tienen traslados de terminal comprobados, costo fijo y balance energético. No se crea un bus en el extremo del recorrido.

**Simplificaciones deliberadas de esta versión:**

- Como reserva conservadora, tras cada servicio se exige poder llegar directamente al menos a un T común. Al terminar se elige el T o E alcanzable más cercano con capacidad. Esta reserva puede agregar buses que un modelo más flexible evitaría.
- Se permite como máximo una visita a un E por hueco, con carga continua. No se exploran visitas múltiples, carga interrumpida ni viajes E→E.
- La reparación divide cadenas y puede cambiar terminales iniciales/finales. No intercambia servicios entre cadenas ni retrocede para modificar reservas anteriores.
- No se minimiza globalmente el costo final ni se demuestra que las particiones sean necesarias. Un fallo de esta heurística se informa como tal, no como prueba de infactibilidad física.
- Las salidas iniciales se hacen desde T con batería llena; no se insertan recargas antes del primer servicio. No se programa carga después del último servicio porque no hay SOC final objetivo.

Estos límites explican parte de los buses adicionales. La siguiente mejora natural es revisar las particiones y probar intercambios locales o reprogramación de recargas antes de ampliar el universo de rutas.

## Archivos y ejecución

Desde la carpeta raíz del proyecto, con Python, NumPy, SciPy y Gurobi 12 con licencia compatible:

```powershell
python tres_fases/ejecutar.py --rutas 101
python tres_fases/ejecutar.py --cantidad 10
python tres_fases/ejecutar.py --cantidad 15
python tres_fases/ejecutar.py --cantidad 20
```

En este equipo se comprobó el intérprete siguiente; se puede reemplazar `python` por:

```powershell
& 'C:/Users/LENOVO/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tres_fases/ejecutar.py --rutas 101
```

El ejecutor incorpora `.deps` al entorno de importación. En el ensayo de 50 rutas del 5 de octubre de 2026, Gurobi confirmó que la licencia local está vigente hasta el **5 de octubre de 2027**. Esta información sustituye el vencimiento observado en los primeros ensayos. No se instalaron nuevas dependencias.

También se pueden indicar rutas propias con `--rutas 101,102,103`, un tiempo límite de Gurobi con `--limite-segundos 120` y una carpeta con `--salida`. El tiempo límite corresponde solo al optimizador de fase 1. Las constantes del escenario están documentadas en `datos.py`; esta implementación está fijada a los supuestos anteriores y no presenta una interfaz general para cambiar batería o discretización.

| Archivo | Responsabilidad |
|---|---|
| `ejecutar.py` | Ejecuta las fases, valida y exporta |
| `datos.py` | Carga parámetros, distancias, corridas y selección de rutas |
| `fase2.py` | Descompone el flujo con balance local de consumo |
| `fase3.py` | Construye cargas, calendarios y divisiones de jornadas |
| `verificar.py` | Reconstruye energía, cobertura, costos y ocupación sin usar el calendario constructor |
| `test_modelos.py` | Casos sintéticos para fallos importantes |

Resultados en `output/tres_fases/rutas_101`, `muestra_10`, `muestra_15` y `muestra_20`:

- `escenario.json`: parámetros y decisiones de esta ejecución.
- `seleccion_rutas.csv`: rutas, sectores, corridas y longitud media.
- `resumen.json`: resultados, costos, máximos de ocupación y tiempos.
- `fase1/modelo.mps`, `solucion.sol`, `gurobi.log`: modelo y evidencia del optimizador.
- `fase2/jornadas.csv`, `actividades.csv`: jornadas previas a introducir recarga.
- `fase3/jornadas.csv`, `actividades.csv`: operación final, con energía inicial/final de cada actividad.
- `fase3/recargas.csv`: cada bloque de carga.
- `fase3/particiones.csv`: divisiones que generaron buses adicionales.

Las distancias reutilizan las matrices viales existentes; no se sustituyen por distancias en línea recta. El ejecutor usa S→S, T→S, S→T, S→E y E→S. Para esta política no hacen falta E→E ni T→E. Las distancias a E están redondeadas en el CSV original; los tiempos vacíos se recalculan de manera consistente desde los kilómetros almacenados. Los accesos a recintos siguen siendo aproximaciones cartográficas pendientes de validación operacional. Los resultados son factibles respecto de estos parámetros, no una certificación de operación en terreno.

## Verificaciones realizadas

Se ejecutaron **19 pruebas automatizadas**, todas satisfactorias: nueve nuevas y diez de regresión existentes.

```powershell
python -m unittest tres_fases.test_modelos fase1.test_modelo test_distancias_electroterminales
```

Las nuevas cubren recarga que evita un bus adicional, división sin hueco, capacidad compartida entre sectores, rechazo de cargas manipuladas y servicios duplicados, intervalos contiguos, estacionamiento que bloquea carga, continuidad energética a medianoche, servicio no alcanzable con un bus nuevo y conservación del flujo en la descomposición energética. Además, cada ejecución real se audita independientemente antes de exportar su resultado final verificado.

En la muestra de 20 rutas, E4 alcanza sus 100 plazas físicas, mientras el máximo de carga simultánea en cualquier E es tres buses. Esto comprueba un caso con estacionamiento saturado; las pruebas sintéticas de un cargador cubren la competencia por conexiones, que estas muestras reales no tensionan mucho.
