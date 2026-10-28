# Mejora conjunta de tres jornadas del mismo sector

Se amplió el método a grupos de tres jornadas, conservando la estructura de las tres fases, la solución factible anterior y la auditoría independiente. La prueba utiliza las mismas 50 rutas y 7.413 corridas laborales. No se añadieron días, buses heterogéneos ni cambios a los terminales o costos.

## Resultado y control

Ambos ensayos comenzaron desde los mismos archivos de la solución de 883 buses, comprobados mediante SHA-256. Se ejecutaron sucesivamente con un presupuesto de 120 segundos y dos segundos por optimización local.

| Indicador | Entrada común | Continuación por parejas | Grupos de tres |
|---|---:|---:|---:|
| Buses | 883 | 881 | **858** |
| Costo total USD | 308.719,85 | 307.784,33 | **302.712,91** |
| Corridas cubiertas | 7.413 | 7.413 | 7.413 |
| Intentos | — | 885 | 603 |
| Mejoras aceptadas | — | 57 | 27 |
| Tiempo de búsqueda | — | 120,26 s | 120,31 s |
| Tiempo del comando | — | 123,65 s | 124,22 s |
| Auditoría completa | Cumple | Cumple | Cumple |

La búsqueda de tres jornadas ahorró 25 buses y USD 6.006,94 respecto de su entrada. Frente al control por parejas logró 23 buses menos y USD 5.071,43 menos de costo. Los dos procesos terminaron por presupuesto en su primera ronda: no se alcanzó un óptimo demostrado.

Se aceptaron 22 absorciones de una jornada por otras dos y cinco rotaciones de tramos finales. Algunas rotaciones también dejan jornadas vacías y eliminan buses; por eso las 27 mejoras no equivalen a 27 buses retirados. La solución final suma 173.258,35 km, 6.157,58 kWh recargados y 142 sesiones.

El costo disminuyó aunque aumentaron ligeramente los kilómetros y las recargas frente a la entrada: la reducción del costo fijo de flota compensó esos aumentos. Se mantiene el escenario de un día aislado con energía inicial dada; este ahorro no incorpora un costo nuevo de recuperar batería al final del día.

## Nuevas alternativas de asignación

**Absorción de tres jornadas en dos:** se elige una jornada candidata a eliminarse y se intenta insertar cada uno de sus servicios en alguna de las otras dos. Una parte puede ir al primer bus y otra al segundo; no se exige que un único receptor pueda realizar toda la jornada absorbida. El orden de los servicios originales de cada receptor se conserva.

La inserción mantiene un máximo de cuatro distribuciones parciales por paso. Se ordenan usando kilómetros vacíos y un término que favorece repartir el kilometraje de servicio entre receptores: `0,5 × km_vacíos + 0,002 × Σ(km_servicio_por_receptor)^2`. Es únicamente una regla para priorizar alternativas, no una modificación de la función objetivo económica ni una garantía de mejor balance energético final.

**Rotación entre tres jornadas:** se cortan las jornadas al inicio, a la mitad o al final y se rotan sus sufijos en ambos sentidos. Se conservan los servicios y sus horarios. Las secuencias vacías se eliminan. Se descartan propuestas repetidas o con enlaces incompatibles.

Se priorizan jornadas cortas. Los receptores se seleccionan entre jornadas del mismo sector, favoreciendo las que admiten más inserciones individuales y tienen menos servicios. El valor predeterminado es ocho vecinos y tres alternativas por grupo. Cada grupo se explora una vez por ronda; no se prueban exhaustivamente todos sus posibles donantes y todas las posiciones de corte.

La preparación de alternativas dispone de hasta 15 segundos por ronda dentro del presupuesto global. Por ello puede recorrer solo una parte de las jornadas; su orden influye en los resultados y no se garantiza una exploración uniforme de todos los sectores.

## Recarga y restricciones compartidas

El MILP de `conjunta.py` admite ahora entre una y tres secuencias fijas. Decide conjuntamente terminal inicial, terminal final, visitas a electroterminales y cantidad de recarga de cada bus resultante. Se retiran temporalmente las reservas de los tres buses originales y se mantienen fijas las de todos los demás.

Las restricciones de presencia física y conexiones suman las decisiones de todas las jornadas seleccionadas sobre la ocupación ajena. El mínimo de batería sigue siendo 35 kWh y el máximo 350 kWh; se conserva potencia máxima de 180 kW, bloques de cinco minutos, consumo de 1,4 kWh/km, capacidad compartida y retorno final factible. No se vuelve a imponer la reserva conservadora adicional de retorno a T después de cada servicio.

Las pruebas revelaron que ventanas solo al principio y al final de un hueco pueden excluir una solución válida de tres buses con un cargador. Para propuestas que mantienen **tres secuencias**, se agregó una posición central por duración dentro de cada tramo libre, alineada a cinco minutos. Se conservan también las posiciones anteriores y los cambios tarifarios. El catálogo sigue siendo acotado y no exhaustivo. Los modelos de una o dos secuencias mantienen su catálogo anterior.

La auditoría verifica todas las actividades contra el conjunto original de 7.413 servicios. Solo se aceptan propuestas con menor costo completo y sin incumplimientos. Ante infactibilidad local, límite de tiempo o fallo de auditoría, permanecen la solución y reservas anteriores. No se registraron rechazos por auditoría en la ejecución real de grupos de tres.

En el resultado final E4 alcanza 100 plazas y E5 alcanza 150, sus respectivos límites físicos. Las cargas simultáneas máximas son 3, 5, 7, 6 y 5 en E1–E5. La mayor escala del vecindario no elimina estas restricciones ni hace independientes a los sectores respecto de los recursos compartidos.

## Interpretación del ensayo

Este resultado muestra que ampliar el tipo de intercambio fue útil en esta instancia: se obtuvieron mejoras mayores que continuar únicamente por parejas con el mismo presupuesto. No demuestra superioridad universal. Cambian la generación de propuestas, el catálogo para tres secuencias y la cantidad de alternativas evaluadas, y solo se realizó una ejecución por modo. Para atribuciones más finas harían falta repeticiones y análisis por sector.

El modelo sigue siendo una heurística de mejora local con subproblemas de optimización. Las fases 1 y 2 no se reoptimizan mediante retroalimentación, los otros buses permanecen fijos en cada intento y no se consideran grupos mayores que tres. Tampoco se demuestra mínima flota global.

## Ejecución y trazabilidad

```powershell
python tres_fases/intercambiar.py --base output/tres_fases/muestra_50_reparada_intercambios_conjunta --coordinacion conjunta --grupo 3 --salida output/tres_fases/muestra_50_trios
```

Control desde la misma entrada:

```powershell
python tres_fases/intercambiar.py --base output/tres_fases/muestra_50_reparada_intercambios_conjunta --coordinacion conjunta --grupo 2 --salida output/tres_fases/muestra_50_control_pares_883
```

`--grupo` admite 2 o 3; el valor predeterminado sigue siendo 2. Los grupos de tres requieren `--coordinacion conjunta`. Se pueden ajustar presupuesto, límite local, vecinos, alternativas y rondas. En los resúmenes nuevos el número de alternativas se registra como `alternativas_por_grupo`.

La implementación de movimientos está en `trios.py`; el modelo conjunto generalizado está en `conjunta.py`; `reparar.py` añade opcionalmente las ventanas centrales. No se modificaron los CSV de resultados anteriores.

La carpeta `output/tres_fases/muestra_50_trios` contiene `comparacion.json`, `intercambios.csv`, `jornadas.csv`, `actividades.csv` y `recargas.csv`. El diagnóstico de intentos identifica los tres buses originales y conserva las cadenas de procedencia mediante `cadena_fase2`.

## Pruebas

Se aprobaron **39 pruebas automatizadas**, incluidas cinco nuevas: repartir una jornada entre dos receptores, reducción integral de tres buses a dos, prohibición de formar grupos entre sectores distintos, conservación ante presupuesto agotado y coordinación de tres buses con un solo cargador.

```powershell
python -m unittest tres_fases.test_trios tres_fases.test_conjunta tres_fases.test_intercambios tres_fases.test_reparar tres_fases.test_modelos fase1.test_modelo test_distancias_electroterminales
```

Las nuevas pruebas permitieron identificar y corregir la falta de ventanas centrales antes del ensayo real. La operación de 50 rutas fue auditada además durante cada aceptación y al terminar.
