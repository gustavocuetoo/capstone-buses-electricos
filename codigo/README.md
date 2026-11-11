# Capstone: asignación de buses RED con Python y Gurobi

**Actualización 4 de octubre de 2026:** la implementación vigente de las **tres fases compactas**, con batería, recarga y comprobación independiente, está documentada en [tres_fases/README.md](tres_fases/README.md). Se ejecutaron casos de 1, 10, 15 y 20 rutas completas. Ese módulo aplica espera gratuita, los cinco electroterminales originales y cuatro terminales comunes; Los Acacios queda excluido. Los apartados que siguen conservan la documentación histórica de la primera fase y sus resultados, incluidos supuestos anteriores que no se usan en el nuevo ejecutor.

Este proyecto implementa una primera fase de asignación de buses a corridas programadas de RED, Santiago. A partir del GTFS, una red vial y terminales disponibles, construye distancias y tiempos de traslado vacío y determina jornadas que cubren los servicios seleccionados, minimizando costos de flota, kilómetros y espera.

**Estado actual:** están implementadas la preparación de datos, las matrices de distancias, la sectorización, el modelo de flujo en Gurobi y la extracción y verificación de jornadas. Se resolvió una prueba completa de las **171 corridas laborales de la ruta 101**, usando cuatro terminales de espera activos. **Todavía no se modelan batería, recarga ni continuidad entre días.** Por lo tanto, el resultado no acredita una operación eléctricamente factible.

Este README documenta la implementación existente y sus decisiones de modelación. La formulación detallada está en [fase1/MODELO_MATEMATICO.md](fase1/MODELO_MATEMATICO.md).

## 1. Objetivos y metodología

El objetivo general del proyecto es avanzar hacia una programación de buses eléctricos que cubra la oferta de servicios y permita estudiar las necesidades de flota y recarga.

La primera fase implementada responde: **¿cómo encadenar las corridas seleccionadas en jornadas de buses, considerando horarios, ubicaciones y traslados vacíos, y cuánto cuesta esa asignación bajo los supuestos definidos?**

El procedimiento implementado es:

1. Identificar rutas, variantes, extremos y patrones de servicio del GTFS.
2. Construir distancias dirigidas sobre la red vial entre extremos y terminales.
3. Reconstruir corridas individuales desde las frecuencias GTFS.
4. Asignar cada ruta completa a un sector asociado a un electroterminal.
5. Construir una red de eventos de ubicación y tiempo, con servicios, esperas y traslados compatibles.
6. Resolver el flujo de costo mínimo con Gurobi.
7. Descomponer el flujo en jornadas y verificar cobertura, continuidad temporal, capacidades finales y costos.

La evaluación energética y la coordinación de recargas quedan para una fase posterior. Extraer jornadas en esta implementación sirve para auditar la fase 1; no constituye por sí solo la fase energética.

## 2. Conceptos utilizados

| Concepto | Significado en el proyecto |
|---|---|
| Ruta o recorrido | Identificador del servicio RED, por ejemplo, 101. Puede incluir distintos sentidos y variantes. |
| Variante | Combinación de ruta, sentido, geometría y paradas inicial y final. |
| Corrida | Una salida concreta, con hora de inicio, hora de término y extremos definidos. |
| Traslado vacío o reposicionamiento | Movimiento del bus sin prestar un servicio a pasajeros. Consume tiempo y kilómetros; no es lo mismo que permanecer esperando. |
| Espera | Tiempo sin movimiento entre servicios. En esta fase no tiene capacidad limitada. |
| Terminal de espera | Lugar habilitado por supuesto para iniciar y terminar jornadas y estacionar, sin recarga. |
| Electroterminal | Instalación original con capacidad física de estacionamiento. Su capacidad no determina el número de cargadores. |
| SOC | Estado de carga de la batería. Su evolución aún no está implementada. |

En las matrices, `electroterminal_a_inicio` significa viajar desde el electroterminal hasta la primera parada de una variante; `fin_a_electroterminal` significa viajar desde la última parada de la variante hasta el electroterminal. Las distancias tienen dirección: no se supone que ambos sentidos midan lo mismo.

## 3. Supuestos del modelo actual

| Tema | Supuesto o decisión implementada |
|---|---|
| Oferta de servicios | Se cubre exactamente una vez cada corrida seleccionada. El modelo no modifica frecuencias ni calcula demanda de pasajeros. |
| Velocidad en vacío | Constante de **18 km/h**. Se aplica a traslados sin pasajeros. |
| Duración del servicio | Se conserva la duración del GTFS; no se recalcula a 18 km/h. |
| Ida y vuelta | Una ida puede continuar con una vuelta programada si horarios y ubicaciones son compatibles. No se obliga a regresar vacío al comienzo de la ida. |
| Espera entre corridas | Puede realizarse en la última parada. No se impone capacidad de espera ni máximo de espera. |
| Terminales adicionales | Capacidad de espera y estacionamiento ilimitada y sin recarga, por supuesto del estudio. Esto no afirma que tales condiciones existan físicamente en la operación real. |
| Ubicación inicial | El modelo decide cuántos buses salen de cada terminal de espera activo. No se proporciona un inventario inicial fijo. |
| Ubicación final | Puede ser cualquier terminal de espera activo o cualquiera de los cinco electroterminales originales. No se exige volver al terminal inicial. |
| Flota | Se determina mediante el costo por bus. No se impone un máximo de 1.200 buses. |
| Estacionamiento en electroterminales | Se respetan sus capacidades individuales para los buses que finalizan allí. No se modela ocupación dinámica durante el día. |
| Sectores | Cada ruta completa pertenece a un único sector. No se permiten conexiones de servicio entre sectores. |
| Regulación mínima | Cero minutos adicionales entre corridas. El código actual no admite activar una regulación positiva sin adaptar la representación de eventos. |
| Tránsito | Tiempos deterministas, sin congestión variable ni incertidumbre. |
| Conductores | No se modelan turnos, descansos ni restricciones laborales. |
| Energía | No se imponen autonomía, SOC, potencia ni cargadores en esta fase. |

Cuando la red ubica una espera después de un traslado vacío, esta se puede trasladar a la parada final del servicio anterior sin cambiar costo ni factibilidad: la velocidad es constante y no hay restricciones de capacidad de espera. No se exige pasar por un terminal de espera entre cada par de corridas; en la implementación actual esos terminales se utilizan para salida y estacionamiento final.

### Acuerdo para la futura fase energética

El supuesto acordado es comenzar el **día 0 con SOC de 100 %** y seguir la evolución de cada batería en los días siguientes, sin reiniciarla artificialmente a 100 % cada día. No se exige recuperar un SOC objetivo al término del horizonte; el mínimo operativo que se incorpore deberá cumplirse también al final.

Este acuerdo aún no se ha convertido en restricciones energéticas. El valor `soc_inicial_dia0` registrado en la configuración no hace que el modelo actual calcule baterías. Del mismo modo, los campos descriptivos sobre recarga y capacidad de espera no habilitan automáticamente formulaciones nuevas si se modifican.

## 4. Terminales considerados

### Electroterminales originales

Se conservan los valores entregados en [depots.csv](depots.csv). Sus coordenadas tienen solo dos decimales y deben entenderse como datos aproximados del caso de estudio.

| ID | Nombre del archivo original | Latitud | Longitud | Espacios físicos |
|---|---|---:|---:|---:|
| 1 | Vespucio Norte | -33.37 | -70.68 | 150 |
| 2 | El Conquistador | -33.42 | -70.70 | 180 |
| 3 | Los Espinos | -33.52 | -70.65 | 120 |
| 4 | La Reina | -33.44 | -70.54 | 100 |
| 5 | Santa Rosa | -33.53 | -70.65 | 150 |
| | **Total** | | | **700** |

**700 espacios físicos no significan 700 cargadores.** La cantidad de cargadores, su potencia y su disponibilidad requieren datos propios para la fase energética. Además, los terminales de espera ilimitados hacen que los 700 espacios no sean un límite global a la flota del modelo actual.

### Terminales de espera propuestos

Las direcciones entregadas y sus fuentes se conservan en [fase1/terminales_espera.json](fase1/terminales_espera.json).

| ID | Terminal | Dirección proporcionada | Coordenadas utilizadas (latitud, longitud) | Estado |
|---|---|---|---|---|
| T01 | Pajaritos / Las Araucarias | Av. General Óscar Bonilla 6100, Lo Prado | -33.4567043, -70.71989665 | Activo, recinto aproximado |
| T02 | Depósito Miguel Mujica | Miguel Mujica 11396, La Florida | -33.5632625, -70.60430455 | Activo, recinto aproximado |
| T03 | El Salto | Av. El Salto 4651, Huechuraba | -33.3879710, -70.6220394 | Activo, recinto aproximado |
| T04 | El Roble | Av. El Roble 200, Pudahuel | -33.4402940, -70.7911183 | Activo, recinto aproximado |
| T05 | Los Acacios | Valle de Los Reyes 863, Maipú | Sin asignar | Pendiente de confirmación |

Las coordenadas activas representan centros aproximados de los recintos cartografiados, no puertas vehiculares verificadas. La cantidad de decimales no indica precisión equivalente del acceso.

Observaciones pendientes:

- **Pajaritos:** se utilizó el recinto Las Araucarias identificado en cartografía; no se debe confundir con la estación intermodal.
- **Miguel Mujica:** la cartografía consultada emplea numeración 11590 y la dirección entregada fue 11396. Se identificó el recinto por nombre, pero falta validar su acceso.
- **El Roble:** el recinto aparece en la cartografía con el nombre anterior Terminal Metbus Los Cipreses.
- **Los Acacios:** existe una discrepancia entre Valle de Los Reyes 863 y la referencia DTPM a 5 Poniente 01460. No se inventaron coordenadas ni se incorporó un quinto terminal sin resolverla.

Mientras T05 siga pendiente, la ejecución normal se detiene. La opción `--permitir-pendientes` permite expresamente trabajar con los cuatro terminales disponibles. No sustituye la ubicación faltante ni representa una prueba con cinco terminales.

## 5. Datos y reconstrucción de corridas

| Entrada | Uso |
|---|---|
| `gtfs/routes.txt`, `trips.txt`, `stops.txt`, `stop_times.txt`, `frequencies.txt` y geometrías GTFS | Rutas, patrones, extremos, tiempos y frecuencias de servicio. |
| `shape_distances.csv` | Longitudes de servicio asociadas a geometrías. |
| `depots.csv` | Electroterminales originales, coordenadas y capacidades. |
| `chile.gpkg` | Red vial para calcular distancias y cartografía utilizada para identificar recintos. |
| `parameters.csv`, `vehicles.csv` | Datos originales del proyecto; su existencia no implica que todos sus parámetros se utilicen en la fase 1. |
| `fase1/configuracion.json` | Parámetros efectivos de costos y velocidad de esta implementación. |
| `fase1/terminales_espera.json` | Terminales adicionales, coordenadas, fuentes y pendientes. |

Se seleccionaron **417 rutas** de buses de la agencia `RM`, con `route_type = 3`. Se identificaron **839 variantes geométricas**, **641 paradas extremas distintas** y **14.464 patrones de viaje** para los tipos de día considerados.

Las frecuencias se expanden en salidas `inicio + n × intervalo`, mientras la salida sea estrictamente menor que el final de la franja. En datos con `exact_times = 0`, esto constituye una reconstrucción determinista para modelar; no debe interpretarse como una lista de salidas exactas observadas.

| Tipo de día | Código | Corridas reconstruidas |
|---|---|---:|
| Laboral | L | 64.502 |
| Sábado | S | 43.619 |
| Domingo | D | 37.377 |
| **Total de los tres tipos** | | **145.498** |

La duración de una corrida es la diferencia entre la llegada a su última parada y la salida de su primera parada. Las horas GTFS superiores a 24:00 se mantienen: no se recortan ni se convierten en servicios independientes al cruzar medianoche.

## 6. Construcción de distancias y tiempos

Se construyeron dos grupos de datos:

1. **Recorridos–electroterminales:** para cada variante y electroterminal, `fin_a_electroterminal` y `electroterminal_a_inicio`. Son **8.390 registros**: 839 variantes × 5 electroterminales × 2 movimientos.
2. **Conexiones de fase 1:** final de corrida → inicio de otra corrida, final de corrida → terminal de espera y terminal de espera → inicio de corrida. La preparación actual generó **130.576 conexiones**, sin pares reportados como sin camino en esa matriz.

La primera matriz también permite definir los sectores. El modelo utiliza sus distancias de retorno a electroterminales; las salidas iniciales de buses se realizan desde los terminales de espera activos.

### Método vial

Se utiliza la capa `gis_osm_roads_free` de `chile.gpkg`. La red conserva la dirección de circulación indicada en los datos y conecta segmentos por vértices compartidos. No se crean cruces nuevos solamente porque dos líneas se intersecten geométricamente.

Las longitudes se calculan geográficamente sobre los segmentos. Los extremos y terminales se proyectan sobre segmentos cercanos y se agregan conectores geométricos. El cálculo de camino mínimo es dirigido, mediante Dijkstra. Los arcos paralelos conservan el menor costo al construir la matriz de la red.

Los conectores son aproximaciones, no accesos vehiculares certificados. La proyección evita autopistas, enlaces de autopistas, puentes, túneles y niveles distintos de cero. Los accesos mayores a 100 m se señalan para revisión. Un conector corto tampoco demuestra que la dirección o puerta elegida sea correcta.

No se modelan restricciones de giro, permisos de ingreso, altura, peso ni todas las restricciones específicas para buses. Por estas razones, las distancias viales son una aproximación más informativa que la distancia en línea recta, pero necesitan validación operacional.

El tiempo de traslado vacío se calcula como:

```text
tiempo_segundos(u,v) = techo(3600 × distancia_km(u,v) / 18)
```

Entre identificadores distintos se impone al menos un segundo; en una misma ubicación, distancia y tiempo son cero. Una distancia faltante no se reemplaza por cero: las claves ausentes producen error y las conexiones explícitamente sin camino se excluyen.

Más detalles: [metodología de distancias](output/distancias_electroterminales/LEEME.md).

## 7. Sectorización y relación entre subproblemas

Para cada ruta se suma, para cada electroterminal, la distancia electroterminal → inicio y final → electroterminal de todas sus variantes. La ruta completa se asigna al electroterminal con menor suma; un empate se resuelve por el menor identificador. Esta regla no pondera variantes por frecuencia.

Los dos sentidos y las variantes de una misma ruta permanecen juntos. Los terminales adicionales de espera **no crean cinco sectores nuevos**: están disponibles para los sectores existentes.

La sectorización limita las combinaciones posibles y puede perder eficiencia frente a una optimización sin sectores. En el código actual, los sectores se incluyen en **una misma red de optimización**, porque comparten las capacidades físicas finales de los electroterminales. No deben describirse como cinco problemas completamente independientes ni sumarse soluciones separadas sin revisar esos límites compartidos.

## 8. Formulación matemática implementada

Se construye una red de eventos `(sector, ubicación, tiempo)`. Un flujo representa buses, y una trayectoria representa la secuencia de actividades de un bus.

### Parámetros

- `I`: corridas seleccionadas; cada corrida tiene inicio `s_i`, término `f_i`, extremos y longitud `L_i`.
- `T`: terminales de espera activos.
- `E`: electroterminales originales, con capacidad física `C_e`.
- `D_uv`, `tau_uv`: distancia y tiempo de traslado vacío entre ubicaciones.
- `c_F = 250 USD/bus`, `c_K = 0,50 USD/km`, `c_W = 0,03 USD/minuto de espera`.

### Arcos y variables

| Arco | Función |
|---|---|
| Servicio | Une inicio y término de una corrida. Su flujo se fija en uno. |
| Espera | Une eventos consecutivos de una misma ubicación y sector. |
| Traslado vacío | Conecta un término con la primera salida alcanzable en otra ubicación del mismo sector. Incluye la espera residual hasta esa salida. |
| Salida de terminal | Permite llegar desde un terminal de espera al inicio de una corrida. |
| Retorno | Permite terminar la jornada en un terminal de espera o electroterminal. |
| Estacionamiento final | Aplica la capacidad correspondiente al lugar de término. |
| Cierre contable | Cuenta los buses utilizados y aplica el costo por bus. No representa movimiento físico ni recarga nocturna. |

La variable `x_a` es el número de buses que utiliza el arco `a`. La flota es `F = x_cierre`.

Conectar con el primer evento alcanzable no elimina las salidas posteriores: se llega a ellas mediante los arcos de espera. No se aplican recortes arbitrarios por cantidad de vecinos ni por espera máxima. Esta representación se apoya en tiempos constantes y espera lineal sin capacidad; deberá revisarse al introducir energía y recursos adicionales.

### Función objetivo

```text
Minimizar:
    250 × F
  + 0,50 × kilómetros totales
  + 0,03 × minutos de espera entre servicios
```

Los kilómetros totales incluyen servicio y vacío, incluidas salidas iniciales y retornos finales. Con todas las corridas fijadas, los kilómetros de servicio son constantes: se incluyen para reportar el costo, aunque no cambian la elección entre asignaciones.

No se cobra inactividad anterior al primer servicio ni posterior al último. No se incluyen energía ni eventos de carga. Por tanto, este valor no es el costo completo de una operación eléctrica.

### Restricciones

```text
Conservación de buses en cada nodo v:
    suma de flujos entrantes = suma de flujos salientes

Cobertura de cada corrida i:
    x_servicio_i = 1

Capacidad final de cada electroterminal e:
    x_estacionamiento_e <= C_e

Límites:
    l_a <= x_a <= u_a; x_a no negativo
```

La compatibilidad temporal se incorpora al construir los arcos: una conexión solo existe si el bus puede llegar a tiempo. Los arcos sin capacidad física explícita usan el número de corridas como cota suficiente.

Aunque los buses son indivisibles, esta fase es una circulación de costo mínimo con matriz de incidencia de red y cotas enteras. Existe un óptimo entero de su relajación lineal. El código usa variables continuas y simplex, y verifica integralidad y balances antes de extraer jornadas. No redondea una solución fraccionaria arbitraria. Añadir restricciones generales de batería o cargadores puede invalidar esta propiedad y requerir otra formulación.

### Horizonte de resolución

Se resuelve un tipo de día aislado. El horizonte permite los traslados iniciales antes de la primera corrida y los retornos después de la última; puede empezar antes de 00:00 y terminar después de 24:00.

Resolver L, S y D por separado no construye una semana. Para encadenar jornadas habrá que heredar ubicaciones, cantidades de buses y baterías, además de tratar correctamente las corridas que cruzan medianoche. Una menor demanda dominical no elimina esa necesidad de continuidad.

## 9. Resultado de la prueba realizada

Fuente: [output/fase1/prueba_101/resultado.json](output/fase1/prueba_101/resultado.json).

| Indicador | Resultado |
|---|---:|
| Ruta y día | 101, laboral (L) |
| Corridas seleccionadas / cubiertas | 171 / 171 |
| Terminales de espera activos | 4; T05 pendiente |
| Buses utilizados | 21 |
| Cota inferior por simultaneidad | 20 |
| Kilómetros de servicio | 4.179,7434 |
| Kilómetros vacíos | 311,8680 |
| Espera entre servicios | 3.517,5333 minutos |
| Costo objetivo | USD 7.601,33 |
| Nodos / arcos | 353 / 3.057 |
| Estado Gurobi | Óptimo demostrado, código 2 |
| Tiempo reportado del solver | Aproximadamente 0,027 segundos |
| Factibilidad energética | No evaluada |

El tiempo del solver no incluye preparar la red vial, reconstruir datos ni construir matrices.

| Componente del costo | USD |
|---|---:|
| 21 buses × 250 | 5.250,00 |
| Kilómetros de servicio × 0,50 | 2.089,87 |
| Kilómetros vacíos × 0,50 | 155,93 |
| Espera × 0,03 | 105,53 |
| **Total** | **7.601,33** |

La distribución inicial fue de 16 buses en T01 y 5 en T03; al finalizar quedaron 10 en T01 y 11 en T03. Esta diferencia es admisible porque no se impuso retorno al mismo terminal ni equilibrio entre días.

El óptimo corresponde a **esta instancia y a sus supuestos**. No demuestra que 21 sea la flota mínima, porque se minimiza costo total; para minimizar flota se necesita ese objetivo explícito. Tampoco demuestra optimalidad de toda la red RED ni factibilidad eléctrica. La red completa aún no se ha resuelto en esta prueba.

## 10. Organización de archivos

| Archivo o carpeta | Contenido |
|---|---|
| `construir_distancias_electroterminales.py` | Construcción de la matriz original recorridos–electroterminales. |
| `test_distancias_electroterminales.py` | Pruebas de geometría, proyección y red dirigida. |
| `output/distancias_electroterminales/` | Matriz original, asociación de patrones a variantes, metodología y validaciones. |
| `fase1/configuracion.json` | Costos, velocidad y supuestos registrados. |
| `fase1/terminales_espera.json` | Catálogo de terminales propuestos y su estado. |
| `fase1/preparar.py` | Reconstrucción de corridas, sectorización y matriz adicional de traslados. |
| `fase1/modelo.py` | Construcción, resolución y auditoría del modelo. |
| `fase1/test_modelo.py` | Pruebas pequeñas de comportamiento del modelo. |
| `fase1/requirements.txt` | Versiones de dependencias utilizadas. |
| `fase1/MODELO_MATEMATICO.md` | Formulación detallada. |
| `output/fase1/corridas.csv` | Corridas reconstruidas para L, S y D. |
| `output/fase1/sectores.csv` | Sector de cada ruta. |
| `output/fase1/traslados.csv` | Distancias y tiempos dirigidos de las conexiones adicionales. |
| `output/fase1/metadatos.json` | Terminales incluidos, velocidad y cobertura de la preparación. |
| `output/fase1/red_vial_cache.npz`, `puntos_red_cache.json` | Red y proyecciones guardadas para futuras ampliaciones; no se editan manualmente. |
| `output/fase1/prueba_101/` | Resultados y evidencia de la prueba resuelta. |

Cada resolución genera:

- `resultado.json`: indicadores, estado del solver, alcance y verificaciones.
- `jornadas.csv`: resumen de cada bus.
- `actividades.csv`: servicios y arcos elegidos por bus. En un traslado, `espera_min` distingue la espera residual del movimiento.
- `modelo.mps`, `solucion.sol` y `gurobi.log`: modelo, solución y registro de resolución.

En caso de infactibilidad, el código intenta generar `conflicto.ilp` para diagnosticar restricciones incompatibles.

## 11. Instalación y ejecución

### Entorno utilizado

Se utilizó Python 3.12 y las siguientes versiones:

```text
gurobipy==12.0.3
numpy==2.5.3
scipy==1.18.1
```

Las bibliotecas se instalaron localmente en `.deps`; los scripts incorporan esa ruta. Para preparar otro entorno con Python disponible:

```powershell
python -m pip install -r fase1/requirements.txt
```

Se requiere una licencia válida de Gurobi. La licencia académica probada en este equipo fue compatible con Gurobi 12 y reportó vencimiento el **6 de octubre de 2026**. La instalación no modificó la licencia; para ejecuciones posteriores a esa fecha se debe verificar su vigencia.

Todos los comandos siguientes se ejecutan desde la carpeta raíz `Capstone`. Si `python` no está disponible en este equipo, se puede usar el intérprete utilizado durante la implementación, sustituyendo `python` por:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
```

### Preparar datos

La matriz original de electroterminales ya está generada. Con los archivos actuales:

```powershell
python fase1/preparar.py --permitir-pendientes
```

Este paso reconstruye corridas y distancias y puede ser considerablemente más lento que resolver la prueba pequeña. Los archivos de caché guardados no implican que el preparador omita automáticamente ese trabajo en ejecuciones posteriores.

### Reproducir la prueba de la ruta 101

```powershell
python fase1/modelo.py --rutas 101 --dia L --permitir-pendientes --salida output/fase1/prueba_101
```

Se incluyen todas las corridas seleccionadas: no se utiliza un recorte por cantidad. Reutilizar una carpeta de salida reemplaza los archivos de resultados de esa ejecución; elegir otra carpeta permite conservar pruebas anteriores.

### Otras selecciones

```powershell
python fase1/modelo.py --rutas 101,102 --dia L --permitir-pendientes --salida output/fase1/prueba_101_102
python fase1/modelo.py --rutas 101 --dia S --permitir-pendientes --salida output/fase1/prueba_101_sabado
python fase1/modelo.py --todas --sector 1 --dia L --tiempo-limite 300 --permitir-pendientes --salida output/fase1/sector_1
```

| Opción | Uso |
|---|---|
| `--dia L`, `S` o `D` | Tipo de día. Por defecto, L. |
| `--rutas 101,102` | Selección de rutas. Por defecto, 101. |
| `--todas` | Selecciona todas las rutas. Sin `--sector`, mantiene toda la red sectorizada. |
| `--sector 1` | Filtra un sector. Para incluir todas sus rutas se debe combinar con `--todas`. |
| `--limite N` | Recorta expresamente a las primeras N corridas seleccionadas para pruebas. Por defecto, cero: sin recorte. |
| `--tiempo-limite N` | Límite del solver en segundos; por defecto, 120. |
| `--salida carpeta` | Carpeta de resultados. |
| `--permitir-pendientes` | Acepta una prueba con los terminales cuya ubicación esté disponible. |

Los comandos ampliados son formas de ejecutar el modelo, no evidencia de que esas instancias ya se hayan resuelto. Debe revisarse el estado reportado por Gurobi antes de afirmar optimalidad. Una prueba con `--limite` no acredita cobertura de un día completo.

### Ejecutar verificaciones

```powershell
python -m unittest fase1.test_modelo test_distancias_electroterminales
```

En la implementación se aprobaron **10 pruebas**: seis del modelo y cuatro de distancias. Las pruebas del modelo requieren Gurobi y una licencia válida.

## 12. Verificaciones realizadas

El modelo comprueba cobertura única de corridas, conservación e integralidad del flujo, factibilidad temporal de conexiones, salidas desde terminales, capacidades finales compartidas, flota no inferior a la simultaneidad y concordancia entre costo reconstruido y objetivo.

Las pruebas pequeñas incluyen:

- Ida seguida de vuelta sin exigir un retorno vacío innecesario.
- Corridas superpuestas que necesitan buses distintos.
- Conexiones que no alcanzan a realizarse por su tiempo de traslado.
- Cobro de espera entre servicios.
- Posibilidad de terminar en otro terminal y respeto de capacidad final compartida entre sectores.
- Error ante una distancia faltante, en lugar de interpretarla como cero.
- Lectura geométrica, caminos dirigidos y proyección respetando sentidos de circulación.

Estas verificaciones cubren el comportamiento programado. No validan accesos reales, autonomía ni factibilidad de carga.

## 13. Qué falta para continuar

1. **Confirmar Los Acacios:** decidir cuál ubicación se utilizará y registrar coordenadas y fuente. Luego regenerar traslados e incluir los cinco terminales en una nueva prueba.
2. **Validar accesos y ubicaciones:** especialmente las coordenadas aproximadas de electroterminales y las puertas de los terminales adicionales.
3. **Ampliar las pruebas:** resolver más rutas y sectores y evaluar tamaño, tiempos y resultados antes de afirmar cobertura de toda la red.
4. **Incorporar energía:** capacidad útil de batería, consumo en servicio y en vacío, SOC mínimo, potencia y eficiencia de carga y compatibilidades entre buses y cargadores.
5. **Incorporar recursos de carga:** número de cargadores y disponibilidad por electroterminal, ocupación simultánea y eventuales límites de potencia. No derivarlos de los 700 espacios físicos.
6. **Encadenar jornadas:** conservar ubicación, inventario y SOC desde el día 0; definir el horizonte de días y su secuencia, sin redistribuir libremente buses al inicio de cada día.
7. **Evaluar la sectorización:** comparar su impacto o introducir coordinación entre sectores si corresponde al alcance acordado con el grupo.

Si se cambia la velocidad, se deben regenerar los tiempos de preparación antes de resolver. Si se cambian terminales, extremos o datos viales, se deben reconstruir las matrices afectadas. Cambiar solo el README o un indicador descriptivo de configuración no modifica las restricciones del modelo.

## 14. Referencias y trazabilidad

Las entradas GTFS, `depots.csv`, `parameters.csv`, `vehicles.csv`, `shape_distances.csv` y `chile.gpkg` corresponden a los archivos disponibles en el proyecto. Los supuestos adoptados en esta implementación están explicitados arriba; una descripción de infraestructura externa no se toma automáticamente como una condición del modelo.

Fuentes geográficas registradas durante la implementación:

- [Recinto Las Araucarias en cartografía](https://mapcarta.com/es/W1200222695).
- [Recinto Miguel Mujica en cartografía](https://mapcarta.com/W1204061563).
- [Recinto El Salto en cartografía](https://mapcarta.com/es/W1164897071).
- [DTPM: resolución de visitas a terminales, referencia para El Roble](https://www.dtpm.cl/descargas/licitacion20/Resolucion%20Exenta%20N1651%202021%20visitas%20a%20terminales.pdf).
- [DTPM: documento con referencia a Los Acacios](https://www.dtpm.cl/descargas/licitacion21/Res%20Ex%20N2626%202021%20Aprueba%20instr%20Panne%20y%20ZPM.pdf).

Para revisar el resultado matemático utilizar `resultado.json`, `modelo.mps`, `solucion.sol` y `gurobi.log` de la misma ejecución. Para interpretar las ubicaciones consultar el catálogo de terminales y los metadatos de preparación. Estos archivos permiten distinguir los datos utilizados, los supuestos del estudio y los resultados efectivamente obtenidos.
