# Programación conjunta de recargas para dos jornadas

La búsqueda de intercambios dispone ahora de dos modos: `secuencial` y `conjunta`. El nuevo modo construye un único MILP para las dos secuencias de servicios del par. Los demás buses y sus reservas permanecen fijos. La generación de intercambios, los datos y las restricciones operacionales mantienen el alcance de las 50 rutas laborales.

## Qué se optimiza conjuntamente

Para cada jornada se decide terminal inicial, terminal final, electroterminal visitado en cada hueco, ventana de recarga y cantidad de energía. Las secuencias de servicios son las propuestas por la búsqueda local, no variables de este MILP. Si una alternativa fusiona ambos buses, se resuelve una sola secuencia.

Las variables `y_bjk` indican si el bus `b` elige la opción `k` del hueco `j`; `q_bjk` es su energía de carga; `E_bj` es la energía al finalizar el servicio. También hay binarias para los terminales iniciales y finales. Se mantienen:

- Una opción de recarga como máximo por hueco y una elección de cada terminal.
- Energía inicial de 350 kWh y balance con consumo de 1,4 kWh/km en servicio y vacío.
- `35 ≤ E_bj ≤ 350` y retorno final con al menos 35 kWh.
- Llegada al cargador con al menos 35 kWh y energía después de cargar no superior a 350 kWh.
- `0 ≤ q_bjk ≤ 15 n_bjk y_bjk`, con `n_bjk` bloques de cinco minutos.
- Compatibilidad temporal de las visitas, ya incorporada en el catálogo de opciones.

El objetivo suma el costo de traslados vacíos, energía y sesiones de ambos buses. Dentro de una propuesta, los kilómetros de servicio y la cantidad de buses son constantes. Al aceptar se compara el costo completo, incluyendo esos componentes y USD 250 por bus, contra la solución anterior.

## Restricciones compartidas nuevas

Sea `U_et` la ocupación física de los demás buses y `V_et` sus conexiones. Para cada E e intervalo relevante se exige:

`U_et + Σ opciones de carga activas y_bjk + Σ estacionamientos finales activos z_be ≤ capacidad_física_e`.

Para las conexiones:

`V_et + Σ opciones de carga activas y_bjk ≤ cargadores_e`.

El estacionamiento final se cuenta desde la llegada real hasta el cierre del horizonte, incluso si esa llegada no coincide con una frontera de cinco minutos. La ocupación física ajena se examina a segundo entero. Las cargas se conectan durante bloques completos de cinco minutos, incluida una opción cuya energía sea parcial.

La implementación divide el tiempo usando comienzos y finales de las opciones. Dentro de cada intervalo toma la mayor ocupación ajena. Como las decisiones de presencia del par son constantes en ese intervalo, esto representa exactamente su capacidad disponible. Los intervalos son semiabiertos `[inicio, fin)`.

Cuando quedan al menos tantas plazas o conexiones como buses del par, la restricción adicional se omite por redundante: cada jornada puede ocupar como máximo un lugar y un cargador a la vez. Esto evita añadir filas innecesarias sin eliminar conflictos reales.

## Conservación de la solución factible

Solo se retiran temporalmente las reservas del par examinado. El modelo conjunto no modifica el calendario al devolver su candidato; las reservas originales se restituyen incluso si no hay solución o vence el presupuesto. La búsqueda acepta el candidato únicamente cuando mejora el costo y pasa la auditoría independiente de toda la operación contra una lista fija de servicios esperados.

El límite de búsqueda continúa siendo 120 segundos y el de cada optimización local, dos segundos. El cierre y las verificaciones pueden añadir tiempo. Se mantienen el catálogo de ventanas y duraciones acotadas, la carga uniforme dentro de cada opción, un máximo de una visita por hueco y las demás simplificaciones del modelo local. No se demuestra optimalidad global de asignación ni mínima flota.

## Resultado del modo conjunto

Se partió de los 886 buses verificados de las mismas 50 rutas y 7.413 corridas. La nueva ejecución terminó con **883 buses y USD 308.719,85**, frente a USD 310.656,91 al inicio: tres buses y USD 1.937,07 menos. La búsqueda duró 120,32 segundos; el comando completo, 123,51 segundos.

Se evaluaron 1.278 alternativas y se aceptaron 108: tres fusiones, 95 intercambios de sufijos y diez movimientos individuales. Todas las aceptaciones y la solución final pasaron la auditoría. No se registraron candidatos rechazados por errores de auditoría. La operación final suma 173.168,07 km, 5.307,99 kWh recargados y 128 sesiones.

La reducción respecto de 886 incluye un nuevo período de búsqueda. Por sí sola no mide el aporte causal de resolver conjuntamente las recargas; debe contrastarse con una continuación secuencial desde la misma entrada.

## Comparación con continuar el método secuencial

Se ejecutó el control desde exactamente los mismos archivos de entrada, verificados mediante sus huellas SHA-256. Cada modo recibió 120 segundos de búsqueda, dos segundos por optimización, ocho vecinos y tres alternativas por par. Las ejecuciones se hicieron sucesivamente, no en paralelo.

| Indicador | Entrada común | Continuación secuencial | Coordinación conjunta |
|---|---:|---:|---:|
| Buses | 886 | 883 | 883 |
| Costo USD | 310.656,91 | 308.892,00 | 308.719,85 |
| Intentos | — | 542 | 1.278 |
| Mejoras aceptadas | — | 89 | 108 |
| Tiempo de búsqueda | — | 120,35 s | 120,32 s |
| Tiempo del comando | — | 124,87 s | 123,51 s |

El modo conjunto obtuvo un costo USD 172,15 menor que continuar el secuencial. **Ambos redujeron tres buses:** no se atribuye esa reducción exclusivamente a la nueva coordinación. En 306 de los intentos conjuntos se añadieron restricciones de capacidad compartida entre los buses; esto indica presencia de acoplamiento en los modelos, no necesariamente que esas restricciones quedaran saturadas en cada solución.

Se conserva la operación conjunta como el mejor resultado entre estas dos ejecuciones verificadas. No es una demostración general de superioridad: la selección y evaluación se detienen por tiempo, los dos modos recorren distinta cantidad de alternativas y no se hicieron repeticiones estadísticas. Para aislar el efecto matemático de la coordinación habría que comparar ambos evaluadores sobre el mismo catálogo fijo de propuestas y calendarios.

## Código y ejecución

`conjunta.py` contiene el modelo y sus restricciones de capacidad compartida. `intercambios.py` selecciona el evaluador y preserva la auditoría; `intercambiar.py` permite elegirlo mediante `--coordinacion`. El valor por defecto sigue siendo `secuencial` para conservar el comportamiento de los comandos anteriores.

```powershell
python tres_fases/intercambiar.py --base output/tres_fases/muestra_50_reparada_intercambios --coordinacion conjunta
```

El resultado se guarda en `output/tres_fases/muestra_50_reparada_intercambios_conjunta`. Contiene `comparacion.json`, jornadas, actividades con SOC, recargas y el registro de intentos. La columna de estados incluye cuántas restricciones de ocupación física y conexiones se añadieron al modelo local.

El control secuencial desde la misma entrada se reproduce con:

```powershell
python tres_fases/intercambiar.py --base output/tres_fases/muestra_50_reparada_intercambios --coordinacion secuencial --salida output/tres_fases/muestra_50_control_secuencial
```

Los resultados previos quedan conservados. Ambos modos tienen el mismo presupuesto global y el mismo límite por optimización; el secuencial puede resolver varios modelos por alternativa, mientras el conjunto resuelve uno.

## Verificación

Pasaron **34 pruebas automatizadas**: las 29 previas y cinco nuevas. Las nuevas verifican reparto entre dos buses con un solo cargador, rechazo por ventana de carga compartida insuficiente, competencia por estacionamiento final, ocupación ajena de un segundo fuera de la malla de cinco minutos y devolución de reservas al agotar presupuesto.

```powershell
python -m unittest tres_fases.test_conjunta tres_fases.test_intercambios tres_fases.test_reparar tres_fases.test_modelos fase1.test_modelo test_distancias_electroterminales
```

Estas pruebas verifican la implementación de los conflictos que la muestra real puede no activar con frecuencia. No sustituyen la validación operacional de accesos a terminales ni la evaluación de sensibilidad de los parámetros.
