# Intercambios acotados entre jornadas del mismo sector

Se incorporó una búsqueda local que cambia qué bus realiza cada servicio y reoptimiza sus recargas. Mantiene las tres fases y utiliza la solución factible previa como punto de partida. Fecha de prueba: 5 de octubre de 2026.

## Resultado sobre las mismas 20 rutas

| Indicador | Antes | Después |
|---|---:|---:|
| Corridas laborales cubiertas | 4.001 | 4.001 |
| Buses utilizados | 507 | 467 |
| Costo total, USD | 174.702,43 | 164.004,80 |
| Kilómetros totales | 93.471,55 | 92.274,69 |
| Energía recargada, kWh | 4.806,95 | 4.430,20 |
| Sesiones de recarga | 114 | 99 |
| Factibilidad auditada | Sí | Sí |

La mejora ahorra **40 buses y USD 10.697,63** en el escenario de un día aislado. Los kilómetros de servicio no cambian: la reducción de kilómetros corresponde a movimientos vacíos. El costo sigue usando energía inicial dada y sin objetivo de SOC final adicional al mínimo de 35 kWh.

Se evaluaron 720 alternativas y se aceptaron 91 mejoras: 40 fusiones de jornadas, 46 intercambios de sufijos y cinco movimientos de un servicio individual. La búsqueda tardó 120,31 segundos con un presupuesto de 120; la ejecución completa del nuevo comando tardó 129,80 segundos, incluyendo lectura, verificaciones y exportación. Se detuvo por presupuesto durante la primera ronda. Los resultados de las fases previas no se volvieron a optimizar.

La solución inicial compacta utilizaba 513 buses; la reparación dentro de cada cadena la redujo a 507. Esta nueva comparación parte de esos 507. No se atribuyen nuevamente los seis buses de la reparación previa al intercambio entre jornadas.

## Movimientos y decisiones

Se seleccionan pares del mismo sector, priorizando jornadas con pocos servicios y enlaces cercanos en espacio y tiempo. Para cada par se generan:

1. **Fusión:** ordenar todos los servicios de ambos buses en una sola jornada, si los enlaces temporales lo permiten.
2. **Intercambio de sufijos:** cortar ambas jornadas e intercambiar los servicios posteriores a esos puntos. El orden dentro de cada parte se conserva.
3. **Traslado individual:** retirar un servicio de una jornada e insertarlo en una posición compatible de la otra.

Toda alternativa conserva exactamente el conjunto original de servicios. Los horarios de servicio permanecen fijos. Se descartan secuencias que no permiten llegar a tiempo según las distancias y 18 km/h en vacío.

Las alternativas se ordenan usando una estimación de costo de buses y enlaces directos. Esa estimación sirve para priorizar: no se presenta como una cota demostrada de un modelo global. Se examinan hasta ocho vecinos por jornada y tres alternativas por par seleccionado, con un máximo de tres rondas. La preparación de alternativas dispone de hasta 15 segundos por ronda, dentro del presupuesto total.

## Reoptimización y calendario compartido

Para evaluar un par se liberan temporalmente sus reservas de conexión y estacionamiento. Los demás buses permanecen fijos. Para cada secuencia resultante se usa el modelo local de `reparar.py`, que decide terminales y recargas en los huecos disponibles. Se exige SOC entre 35 y 350 kWh, potencia máxima de 180 kW y retorno final factible.

Cuando quedan dos jornadas se resuelven secuencialmente: la primera reserva su operación y la segunda ve el calendario actualizado. Si no se consigue una mejora se prueba el orden contrario. **No es una optimización conjunta exacta de ambos buses:** una mala decisión del primero puede ocultar alternativas mejores, incluso probando ambos órdenes.

Se mantienen las ventanas de carga acotadas descritas en `REPARACION_LOCAL.md`: una visita por hueco, bloques completos de cinco minutos, duraciones seleccionadas y carga uniforme dentro de cada ventana. No se exige la reserva conservadora adicional de regreso a T tras cada servicio. La comparación inicial y final está auditada con las mismas restricciones físicas del escenario; retirar esa reserva no se cuenta como un nuevo beneficio del intercambio.

## Aceptación y conservación de la factibilidad

Una alternativa se acepta solo si reduce el costo completo —incluyendo USD 250 por bus— y pasa una auditoría independiente de toda la operación. La lista de servicios esperados se fija al inicio: no se reconstruye a partir de la propuesta, lo que evita que un servicio omitido desaparezca inadvertidamente del control de cobertura.

Si un modelo no encuentra solución, vence el tiempo, el costo no mejora o la auditoría detecta un incumplimiento, se conserva la solución anterior. Las reservas temporales se devuelven antes de aceptar o rechazar. La auditoría comprueba cobertura exacta, continuidad de lugar y tiempo, sector, batería, potencia, ocupación física, conexiones y costos. El estacionamiento final en E cuenta hasta el fin del horizonte.

El presupuesto es de búsqueda, no un límite duro para todo el proceso. Cada resolución recibe hasta dos segundos y nunca más que el tiempo restante detectado antes de optimizar. Construcción, cierre y auditoría final pueden agregar tiempo; por ello la duración observada supera ligeramente 120 segundos. La carga de datos y exportación también quedan fuera del tiempo de búsqueda informado.

La solución obtenida es factible bajo los parámetros existentes, **sin garantía de optimalidad global ni de mínima flota**. Conservarla permite detener la búsqueda sin perder el avance. La ejecución demuestra viabilidad computacional para esta muestra; no garantiza tiempos similares para toda RED. El número de intentos y el resultado pueden variar según el equipo y la carga del sistema, al detenerse por tiempo.

## Ejecución y archivos

Desde la raíz del proyecto:

```powershell
python tres_fases/intercambiar.py
```

En el equipo utilizado:

```powershell
& 'C:/Users/LENOVO/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tres_fases/intercambiar.py
```

Por defecto lee `output/tres_fases/muestra_20_reparada` y guarda en `output/tres_fases/muestra_20_reparada_intercambios`. Los resultados iniciales se conservan. Se puede indicar `--base`, `--salida`, `--presupuesto 120`, `--limite-local 2`, `--vecinos 8`, `--alternativas 3` y `--rondas 3`. La base debe ser una solución guardada por la reparación local o por este nuevo comando; no es directamente la carpeta histórica de fase 1.

El código de búsqueda está en `intercambios.py`; `intercambiar.py` carga, valida y exporta. `reparar.py` admite ahora un plazo adicional para no iniciar nuevas resoluciones después de agotado el presupuesto.

Resultados exportados:

- `comparacion.json`: indicadores antes/después, tiempos, parámetros y huellas SHA-256 de las jornadas y actividades de entrada.
- `intercambios.csv`: intentos, tipo de movimiento, par de buses, sector, estados de Gurobi, aceptación y ahorro.
- `jornadas.csv`: buses finales y sus indicadores.
- `actividades.csv`: secuencia completa con SOC inicial y final de cada actividad.
- `recargas.csv`: todos los bloques de carga programados.

Los IDs de bus se mantienen cuando es posible. La columna `cadena_fase2` puede contener varias cadenas originales separadas por `|`, porque la nueva jornada combina servicios que antes pertenecían a distintas cadenas.

## Pruebas

Se ejecutaron **29 pruebas automatizadas**, todas satisfactorias, incluyendo seis nuevas: fusión entre cadenas diferentes, prohibición de intercambio entre sectores, conservación al agotar presupuesto, restitución de reservas si falla el segundo bus, rechazo de una propuesta que omite servicios y conservación de cobertura en movimientos de sufijos e individuales.

```powershell
python -m unittest tres_fases.test_intercambios tres_fases.test_reparar tres_fases.test_modelos fase1.test_modelo test_distancias_electroterminales
```

La solución real de 4.001 corridas pasó además la auditoría completa durante cada aceptación y al terminar. Este nivel de complejidad ya permite estudiar mejoras sustanciales manteniendo un tiempo de búsqueda acotado. La siguiente evaluación debería medir sensibilidad al presupuesto y a la selección de vecinos antes de introducir grupos mayores de buses.
