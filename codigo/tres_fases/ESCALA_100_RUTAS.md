# Ampliación a 100 rutas laborales

Se completó el ensayo de 100 rutas, conservando las 50 de la muestra anterior y agregando otras 50. La nueva muestra contiene **15.268 corridas laborales**, veinte rutas por sector, y representa aproximadamente el 24% de las 417 rutas con servicios laborales de los datos preparados.

La operación final utiliza **1.782 buses**, cuesta **USD 632.889,30** y pasa la auditoría de cobertura exacta, horarios, continuidad espacial, sectores, batería, potencia, conexiones y estacionamiento compartido. No se recortaron servicios de las rutas seleccionadas ni se relajaron restricciones físicas para conseguir factibilidad.

## Selección anidada

El ejecutor admite ahora `--cantidad` entre 10 y 100 y el argumento `--incluir-rutas-desde`. Este recibe el CSV de selección de una muestra que debe quedar incluida. Para cada sector se conservan las rutas obligatorias y se completa su cuota mediante cuantiles de longitud media entre las rutas restantes, antes de resolver.

Se comprobó que las 100 rutas son distintas, que incluyen las 50 anteriores y que cada sector contiene veinte rutas. Las 50 rutas anteriores aportaban 7.413 corridas; las 50 nuevas agregan 7.855. Las rutas, sectores, número de salidas y distancias medias están en `output/tres_fases/muestra_100/seleccion_rutas.csv`.

Los parámetros siguen siendo un día laboral aislado, 18 km/h solo en vacío, batería de 350 kWh, mínimo 35 kWh, consumo de 1,4 kWh/km, cuatro terminales comunes y cinco electroterminales originales. El inicio del horizonte cubre los traslados de madrugada; no se reinicia el SOC al pasar medianoche. El costo conserva la energía inicial dada y no exige recuperar esa energía al terminar.

## Resultados por etapa

| Etapa | Buses | Costo total USD | Tiempo medido |
|---|---:|---:|---|
| Fases 1–2, sin batería | 1.622 | 580.486,16 | Gurobi fase 1: 12,44 s |
| Fase 3 constructiva, verificada | 1.980 | 683.554,26 | Ejecución inicial de tres fases: 32,38 s |
| Reparación dentro de cadenas | 1.965 | 679.695,19 | Reparación adicional: 16,25 s |
| Intercambios por parejas, carga conjunta | 1.852 | 650.162,90 | Búsqueda adicional: 120,66 s |
| Grupos de tres, carga conjunta | **1.782** | **632.889,30** | Búsqueda adicional: 121,33 s |

Las tres mejoras reducen en conjunto 198 buses y USD 50.664,96 frente a la solución energética constructiva. La fase 1 sin batería no es una operación eléctrica factible ni su número de buses un mínimo de flota demostrado por separado.

Los tiempos de cada fila tienen alcances diferentes, indicados en la tabla. El comando completo de parejas tardó 125,26 s y el de grupos de tres 127,92 s, incluyendo lectura, comprobaciones y exportación. Sus presupuestos de búsqueda fueron de 120 s cada uno; terminar una comprobación y cerrar el proceso puede agregar tiempo.

La fase 1 contiene 29.734 nodos y 610.354 variables de flujo, frente a 14.619 y 216.872 en el ensayo de 50 rutas. Gurobi obtuvo el óptimo de esta fase en 12,44 s. La solución de flujo se comprobó integral antes de construir jornadas.

La búsqueda por parejas evaluó 666 alternativas y aceptó 146 mejoras, ahorrando 113 buses frente a la solución reparada. Los grupos de tres evaluaron 2.124 alternativas y aceptaron 70 mejoras, ahorrando otros 70 buses. Ambos procesos terminaron por presupuesto; la búsqueda de tres llegó a su segunda ronda.

Esta ejecución encadena reparación, parejas conjuntas y grupos de tres. No incluye ensayos de control adicionales desde cada punto intermedio. Por ello los ahorros por etapa describen la mejora observada al continuar el proceso, no una atribución causal aislada de cada algoritmo.

## Operación final y recursos

La solución final suma 360.673,53 km, 27.863,91 kWh recargados y 574 sesiones. La reducción de flota puede aumentar la carga necesaria por bus; el criterio de aceptación continúa siendo menor costo total con factibilidad, no minimizar simultáneamente cada componente.

| Electroterminal | Ocupación física máxima final | Capacidad física | Cargas simultáneas máximas |
|---|---:|---:|---:|
| E1 | 150 | 150 | 11 |
| E2 | 171 | 180 | 17 |
| E3 | 119 | 120 | 9 |
| E4 | 100 | 100 | 9 |
| E5 | 150 | 150 | 9 |

Los cinco E alcanzaron su capacidad física en algún momento de la solución constructiva. Después de las mejoras, E1, E4 y E5 siguen llegando a su límite. Los máximos de cada E no tienen por qué ocurrir a la misma hora. Las conexiones permanecen relativamente holgadas; esta muestra tensiona especialmente el estacionamiento físico.

La flota puede exceder las 700 plazas de los electroterminales porque los cuatro terminales comunes tienen estacionamiento ilimitado según el supuesto del grupo. No se impone la antigua cifra de 1.200 buses como límite de flota. Estos supuestos no cambiaron al ampliar la muestra y condicionan el resultado.

## Alcance de la evidencia

La implementación consiguió cubrir todas las salidas de esta muestra sin perder factibilidad y dentro de los límites de búsqueda establecidos. La selección anidada permite ver el crecimiento de la instancia manteniendo las rutas anteriores, pero los valores de costo y flota de muestras distintas no son comparaciones de calidad de solución: cambia la demanda.

Las mejoras finales siguen siendo heurísticas, con catálogos de recarga y grupos de búsqueda acotados. El presupuesto no permite recorrer exhaustivamente todas las jornadas; el orden de exploración puede favorecer algunas zonas de la muestra. No hay prueba de mínima flota ni garantía de tiempo para las 417 rutas completas.

## Ejecución reproducible

Desde la raíz del proyecto, usando el entorno de Python con Gurobi:

```powershell
python tres_fases/ejecutar.py --cantidad 100 --incluir-rutas-desde output/tres_fases/muestra_50/seleccion_rutas.csv
python tres_fases/mejorar.py --base output/tres_fases/muestra_100
python tres_fases/intercambiar.py --base output/tres_fases/muestra_100_reparada --coordinacion conjunta --grupo 2 --salida output/tres_fases/muestra_100_pares
python tres_fases/intercambiar.py --base output/tres_fases/muestra_100_pares --coordinacion conjunta --grupo 3 --salida output/tres_fases/muestra_100_trios
```

Se conservaron los directorios anteriores. Los nuevos resultados están en `output/tres_fases/muestra_100`, `muestra_100_reparada`, `muestra_100_pares` y `muestra_100_trios`. El último contiene la operación final: jornadas, actividades con SOC, recargas, registro de intentos y `comparacion.json`.

El cambio de código afecta a la selección de rutas y al rango del ejecutor; las formulaciones y heurísticas no se modificaron. Se añadieron y aprobaron cuatro pruebas de selección: inclusión y balance sectorial, rechazo de rutas desconocidas, conservación de una cuota ya completa y rechazo de una cuota incompatible. La cobertura y restricciones de las soluciones reales se verificaron en cada etapa.

```powershell
python -m unittest tres_fases.test_seleccion
```

La búsqueda detenida por tiempo puede recorrer diferentes cantidades de alternativas según el equipo y su carga. Se conservan parámetros y resultados para comparar esas ejecuciones sin confundir variaciones de búsqueda con cambios de datos.
