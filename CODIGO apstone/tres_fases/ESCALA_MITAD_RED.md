# Ensayo que abarca más de la mitad del universo laboral

Se completaron las tres fases, la reparación y las mejoras por parejas y grupos de tres para **212 rutas y 33.220 corridas laborales**. La operación final está verificada y utiliza **4.175 buses**, con costo **USD 1.459.572,80**. Se conservaron los resultados de todas las muestras anteriores.

## Qué significa cubrir el 50%

| Medida | Muestra resuelta | Universo laboral preparado | Cobertura |
|---|---:|---:|---:|
| Rutas | 212 | 417 | 50,84% |
| Corridas | 33.220 | 64.502 | 51,50% |

Los porcentajes se refieren al día laboral del proyecto, no al conjunto de días laborales, sábados y domingos. Cada ruta seleccionada incluye todas sus corridas laborales, sentidos y variantes disponibles; no se truncaron salidas para reducir el tamaño.

Con 209 rutas se supera la mitad de las rutas, pero la muestra obtenida por nuestra regla de selección reunía solo 30.780 corridas, menos de la mitad del total. Se evaluó el tamaño de las muestras antes de optimizar, conservando las 100 rutas anteriores. La selección de 212 rutas fue la primera entre las cantidades evaluadas desde 209 que superó ambos umbrales. Esto no significa que 212 sea el mínimo posible con cualquier otra selección.

Se conservan las 100 rutas previas y se agregan 112. Los sectores 1 y 2 tienen 43 rutas cada uno, y los sectores 3, 4 y 5 tienen 42. Se completan sus cuotas mediante cuantiles de longitud media entre las rutas restantes. Las cuotas equilibran el número de rutas por sector, no reproducen necesariamente sus proporciones en la red completa: no es una muestra estadística aleatoria.

La comprobación reproducible de porcentajes e inclusión está en `output/tres_fases/muestra_212/cobertura_universo.json`; el detalle de rutas está en `seleccion_rutas.csv`.

## Resultados por etapa

| Etapa | Buses | Costo USD | Tiempo y alcance |
|---|---:|---:|---|
| Fases 1–2, sin batería | 3.561 | 1.278.244,98 | Gurobi fase 1: 96,89 s |
| Fase 3 constructiva verificada | 4.322 | 1.497.326,26 | Tres fases iniciales y exportación: 188,34 s |
| Reparación dentro de cadenas | 4.308 | 1.493.749,18 | Reparación: 30,03 s adicionales |
| Parejas con recarga conjunta | 4.237 | 1.475.501,95 | Búsqueda: 121,82 s adicionales |
| Grupos de tres con recarga conjunta | **4.175** | **1.459.572,80** | Búsqueda: 121,27 s adicionales |

Las mejoras reducen 147 buses y USD 37.753,46 respecto de la solución energética constructiva. La solución sin batería no es una operación eléctrica válida ni constituye una prueba de mínima flota.

El modelo de fase 1 tiene **63.298 nodos, 2.092.978 variables de flujo y 4.185.956 coeficientes no nulos**. Se otorgó un límite de 300 segundos al optimizador y se obtuvo optimalidad en aproximadamente 97 segundos. Se comprobó la integralidad del flujo y su cobertura antes de construir jornadas.

La fase 2 tardó 12,86 segundos y la construcción energética 3,10 segundos. El total inicial de 188,34 segundos también incluye lectura, construcción de red, preparación y exportación del modelo, auditorías y CSV. No se debe confundir ese total con el tiempo del optimizador.

La reparación revisó 761 divisiones. La búsqueda por parejas evaluó 204 alternativas y aceptó 71 mejoras; la de grupos de tres evaluó 66 alternativas y aceptó 62. Cada búsqueda tuvo un presupuesto de 120 segundos, con hasta dos segundos por optimización local. Las comprobaciones y el cierre pueden exceder ligeramente el presupuesto; los comandos completos tardaron 131,14 y 131,08 segundos, respectivamente.

Los ahorros de cada etapa son mejoras sucesivas desde la salida de la anterior. No se ejecutaron controles adicionales para aislar causalmente el aporte de cada vecindario en esta muestra. Al crecer el número de jornadas, el presupuesto permite evaluar una fracción menor de las alternativas posibles.

## Factibilidad y recursos compartidos

La auditoría independiente verificó exactamente las 33.220 corridas, horarios, continuidad espacial, sector, SOC, potencia, conexiones, estacionamiento y costos. La lista de servicios esperados se mantiene fija durante las mejoras.

La operación final suma 803.264,37 km, 57.079,17 kWh recargados y 1.130 sesiones. Se mantienen batería de 350 kWh, SOC mínimo del 10%, consumo de 1,4 kWh/km, carga máxima de 180 kW y velocidad de 18 km/h exclusivamente para traslados vacíos.

| Electroterminal | Máximo de ocupación física | Capacidad física | Máximo de cargas simultáneas |
|---|---:|---:|---:|
| E1 | 150 | 150 | 20 |
| E2 | 179 | 180 | 21 |
| E3 | 120 | 120 | 12 |
| E4 | 100 | 100 | 14 |
| E5 | 150 | 150 | 17 |

El estacionamiento está fuertemente utilizado. Los máximos de distintos terminales no necesariamente coinciden en el tiempo. Las conexiones siguen teniendo holgura, según las capacidades declaradas en los datos. No se añade un límite de transformador no especificado.

La flota excede las 700 plazas de los E porque los cuatro terminales comunes mantienen estacionamiento ilimitado. No hay un máximo de flota de 1.200 buses en este escenario. Se conserva el supuesto de día aislado con energía inicial dada, disponibilidad de E de 24 horas y ausencia de SOC final objetivo adicional al mínimo. La factibilidad informada corresponde a esos supuestos y datos, no a una certificación de operación real en terreno.

## Reducción del uso de memoria

Antes de ampliar se detectó poca memoria disponible en el equipo. Para conservar la misma formulación y todos los arcos factibles, se hicieron estos cambios de representación:

- Los arcos se almacenan como registros inmutables compactos, en lugar de diccionarios individuales.
- Las cotas, costos e índices de la matriz de incidencia se construyen directamente como arreglos numéricos, sin listas intermedias de millones de objetos Python.
- Se liberan los arreglos temporales de la matriz y la red al terminar de extraer las cadenas que necesita la fase 3.

No se eliminaron enlaces ni servicios, no se redujeron capacidades y no se cambiaron costos ni restricciones matemáticas. Se aprobaron las **43 pruebas automatizadas** tras los cambios. No se presenta una medición comparativa del máximo de RAM, porque no se instrumentó ese indicador antes y después.

## Repetir el ensayo

Desde la raíz del proyecto con el entorno de Python y Gurobi:

```powershell
python tres_fases/ejecutar.py --cantidad 212 --incluir-rutas-desde output/tres_fases/muestra_100/seleccion_rutas.csv --limite-segundos 300
python tres_fases/mejorar.py --base output/tres_fases/muestra_212
python tres_fases/intercambiar.py --base output/tres_fases/muestra_212_reparada --coordinacion conjunta --grupo 2 --salida output/tres_fases/muestra_212_pares
python tres_fases/intercambiar.py --base output/tres_fases/muestra_212_pares --coordinacion conjunta --grupo 3 --salida output/tres_fases/muestra_212_trios
```

El rango del argumento `--cantidad` llega ahora a 212. La selección sigue rechazando cuotas sectoriales incompatibles con las rutas obligatorias o los datos disponibles.

Resultados en `output/tres_fases/muestra_212`, `muestra_212_reparada`, `muestra_212_pares` y `muestra_212_trios`. El último directorio contiene la operación final y su comparación con la etapa anterior. Los MPS, solución y log de Gurobi están en la subcarpeta `fase1` del primero.

Suite ejecutada:

```powershell
python -m unittest tres_fases.test_seleccion tres_fases.test_trios tres_fases.test_conjunta tres_fases.test_intercambios tres_fases.test_reparar tres_fases.test_modelos fase1.test_modelo test_distancias_electroterminales
```

## Interpretación

El ensayo demuestra que el código puede resolver y verificar una operación que abarca más de la mitad de las rutas y corridas laborales del proyecto en el equipo utilizado. Solo la fase 1 tiene optimalidad demostrada; la operación eléctrica final es una solución factible mejorada mediante búsqueda local acotada.

Este resultado no demuestra mínima flota ni garantiza tiempos similares para las 417 rutas. Tampoco permite extrapolar directamente el costo al doble. La siguiente ampliación debería medir memoria máxima, tiempo por auditoría y sensibilidad al presupuesto de búsqueda, además de conservar la comprobación de todos los servicios y recursos compartidos.
