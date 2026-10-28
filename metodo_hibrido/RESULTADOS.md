# Primer ensayo completo del método híbrido

Fecha: 5 de octubre de 2026. Datos y programación laboral de las mismas 212 rutas y 33.220 corridas. Se mantienen los cinco electroterminales originales, cuatro terminales comunes irrestrictos, las restricciones de sector y todos los costos y parámetros acordados. No se modificaron las fuentes de la metodología anterior.

## Resultado

| Etapa | Buses | Costo USD | Corridas verificadas |
|---|---:|---:|---:|
| Caso base cronológico, reconstruido desde cero | 4.014 | 1.415.348,70 | 33.220 |
| Híbrido después de parejas | 3.996 | 1.410.013,06 | 33.220 |
| Híbrido después de tríos, final | **3.973** | **1.404.610,25** | **33.220** |
| Referencia histórica: tres fases con mejoras | 4.175 | 1.459.572,80 | 33.220 |

El aporte de las mejoras híbridas respecto del caso base es **41 buses menos (1,02%) y USD 10.738,45 menos (0,7587%)**. La búsqueda por parejas reduce 18 buses y la de tríos otros 23. Las dos búsquedas son sucesivas: la segunda parte del resultado de la primera; no son ensayos independientes de cada vecindario.

Frente al prototipo anterior, son 202 buses menos y USD 54.962,55 menos. Esa diferencia combina la mejor construcción inicial con la búsqueda posterior: no debe atribuirse íntegramente a los modelos locales. Tampoco demuestra una ventaja universal ni optimalidad global.

## Indicadores finales

- Kilómetros totales: 802.225,65; de servicio: 704.414,10; vacíos: 97.811,55.
- Energía comprada: 34.394,77 kWh; sesiones: 799.
- Costo de buses: USD 993.250; kilómetros: USD 401.112,83; electricidad: USD 6.252,42; sesiones: USD 3.995.
- Ahorro frente al caso base: buses USD 10.250; kilómetros USD 471,40; sesiones USD 95; mayor costo de electricidad USD 77,95.

La energía comprada aumenta respecto del caso base mientras disminuyen flota y costo total. No debe interpretarse como un deterioro automático: la función objetivo evalúa todos los componentes. Se conserva el supuesto de batería inicial llena y ausencia de reposición final obligatoria; no se estima aquí un costo de operación semanal repetida.

| Electroterminal | Máxima ocupación / plazas | Máximas conexiones usadas / disponibles |
|---|---:|---:|
| E1 | 150 / 150 | 18 / 150 |
| E2 | 178 / 180 | 21 / 180 |
| E3 | 120 / 120 | 10 / 120 |
| E4 | 100 / 100 | 22 / 100 |
| E5 | 150 / 150 | 22 / 150 |

## Esfuerzo computacional

- Construcción cronológica y validación del constructor: 103,22 s, sin incluir la posterior exportación de la etapa.
- Búsqueda por parejas: 122,21 s; 169 alternativas evaluadas, 60 mejoras aceptadas, una ronda.
- Búsqueda por tríos: 122,66 s; 724 alternativas evaluadas, 23 mejoras aceptadas, una ronda.
- Etapas de búsqueda con copia protectora y validaciones exteriores: 125,46 y 127,06 s.
- Ejecución completa medida por el programa: **463,60 s (7 min 44 s)**, incluye carga de la instancia, construcción, búsquedas, auditorías y exportaciones de los planes por etapa hasta la medición final. No incluye arranque/importaciones iniciales ni la validación cruzada adicional posterior.

Ambas búsquedas terminaron por presupuesto. El límite nominal era de 120 s por búsqueda, dos segundos por MILP, ocho vecinos y tres alternativas por grupo. No se exploraron todos los grupos ni todas las ventanas de recarga. El tiempo adicional de exportar varias copias completas es parte del costo de conservar etapas revisables, no tiempo de Gurobi.

El método híbrido añade cómputo al caso base. Este ensayo demuestra una mejora de calidad en esa instancia y presupuesto; no demuestra que el híbrido sea más rápido. Una comparación rigurosa de velocidad con las tres fases requiere igualar los límites de medición y las exportaciones.

## Validación

Se aprobaron **22 pruebas**: 14 del caso base y ocho de integración y mejora. Entre ellas: rechazo de alternativas incompletas o inválidas, aislamiento de mutaciones, conservación del incumbente ante igualdad de costo, fusión factible de dos jornadas, restauración del calendario, coordinación de tres buses con un cargador, conservación de servicios en redistribuciones y respeto de sectores.

La solución exportada se volvió a leer y se verificó con `tres_fases/verificar.py` y los datos originales cargados mediante `tres_fases/datos.py`, únicamente como comprobación cruzada externa. Todos los indicadores coinciden exactamente con el resumen del híbrido. Este control no es una dependencia del ejecutor nuevo.

También se compararon las huellas de las fuentes adaptadas: los módulos originales siguen intactos. La constancia está en `resultados/ensayo_212/validacion_cruzada.json`.

## Archivos a consultar

- `resultados/ensayo_212/comparacion.json`: comparación inicial/final y estadísticas.
- `resultados/ensayo_212/comparacion_etapas.csv`: tabla de evolución.
- `resultados/ensayo_212/01_caso_base/`: referencia sin mejoras.
- `resultados/ensayo_212/02_pares/` y `03_trios/`: etapas y registro de intentos.
- `resultados/ensayo_212/04_final/`: jornadas, actividades, recargas, planes completos y resumen auditado.
- `resultados/ensayo_212/ejecucion.json`: parámetros y huellas de entradas y código al inicio del ensayo. Las pruebas se ampliaron durante la ejecución; los módulos de producción no cambiaron durante ella.

## Qué permite afirmar

En esta instancia, construir las jornadas cronológicamente y después aplicar optimización local conjunta produjo una solución factible de menor costo que el caso base y que el prototipo previo. Este resultado respalda evaluar el método híbrido como metodología propuesta, conservando el caso base sin modificaciones como referencia.

Los resultados con presupuesto temporal pueden variar entre ejecuciones por la cantidad de alternativas que alcanza a procesar el equipo. La garantía implementada es conservar el caso base y aceptar solo mejoras auditadas, no repetir necesariamente la misma reducción de 41 buses en cualquier ejecución.
