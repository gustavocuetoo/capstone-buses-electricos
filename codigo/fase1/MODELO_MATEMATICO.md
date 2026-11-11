# Fase 1: asignación de corridas en una red tiempo-espacio

## Alcance y decisiones acordadas

Se cubren todas las corridas seleccionadas exactamente una vez y se minimiza el costo de buses, kilómetros y espera. La velocidad de los traslados sin pasajeros es 18 km/h. Los servicios conservan sus horarios y duraciones del GTFS. Cada sentido de un recorrido es un servicio independiente: después de una ida puede atenderse una vuelta si sus tiempos y ubicaciones son compatibles. No se exige regresar vacío al inicio de la ida.

Los cinco nuevos terminales son lugares de salida, espera y estacionamiento ilimitados y SIN recarga por supuesto del caso de estudio. El modelo decide cuántos buses comienzan en cada terminal. La ubicación inicial de todos los buses es uno de esos terminales. La ubicación final puede ser cualquiera de los terminales de espera activos o de los cinco electroterminales originales. No se exige igualdad entre terminal inicial y final.

La espera entre servicios puede realizarse en el extremo donde terminó el servicio anterior. Cuando la red representa espera después de un traslado, esta espera puede desplazarse antes del traslado sin alterar factibilidad ni costo porque tiempos y velocidades son constantes y la espera no tiene capacidad limitada. No se modelan estacionamientos intermedios obligatorios.

No se limita la flota a 1.200. Se mantienen los 700 espacios físicos de los electroterminales originales como límite a los buses que finalizan allí. Su número de cargadores NO se deduce de esos espacios. En la fase 1 no hay recargas, SOC, cargadores, potencia eléctrica, conductores ni incertidumbre de tránsito.

El SOC 100% corresponde al inicio del día 0 en la futura fase energética. No se reiniciará a 100% cada día. Esta implementación comprueba un día aislado de fase 1; aún NO encadena estados de batería o inventarios entre jornadas semanales.

## Parámetros

- I: corridas reconstruidas desde las frecuencias GTFS. Cada corrida i tiene inicio s_i, fin f_i, ubicación inicial o_i, ubicación final d_i y longitud de servicio L_i.
- K = {1,2,3,4,5}: sectores asociados a los cinco electroterminales. Cada ruta completa, incluidas ambas direcciones y sus variantes, pertenece a un solo sector k(i).
- T: terminales de espera con coordenadas disponibles; cinco previstos. Cada terminal tiene capacidad ilimitada y recarga prohibida.
- E: cinco electroterminales originales con capacidades C_e = 150,180,120,100,150 buses, respectivamente.
- D_uv: distancia vial aproximada dirigida entre ubicaciones u y v, incluyendo conectores geométricos de acceso.
- tau_uv = ceil(3600 D_uv / 18): tiempo de traslado vacío en segundos. Entre ubicaciones distintas se impone al menos un segundo para evitar ciclos instantáneos entre puntos coincidentes. De una ubicación a sí misma, D_uu = tau_uu = 0.
- c_F = 250 USD/bus; c_K = 0,5 USD/km; c_W = 0,03 USD/minuto de espera.

Las fuentes originales quedan intactas. Los conectores de acceso, las ubicaciones aproximadas y las limitaciones de la red de calles deben revisarse antes de afirmar factibilidad operacional real.

## Sectorización

Para cada ruta r se suma, por electroterminal e, la distancia electroterminal-inicio y final-electroterminal de todas sus variantes geométricas. Se asigna la ruta al electroterminal con menor suma. Al comparar terminales para una misma ruta, esta regla equivale a comparar el promedio por variante. No se pondera por frecuencia. En caso de empate se elige el identificador menor.

Esta asignación previa restringe las combinaciones posibles y puede perder calidad respecto de una asignación global. No implica que los buses deban comenzar en el electroterminal del sector: los terminales de espera están disponibles para todos los sectores.

## Red

Un nodo de evento es (k,p,t): sector, ubicación y tiempo. Se añaden origen O, destino Z y un nodo final por terminal. Los arcos son:

1. Servicio: (k(i),o_i,s_i) a (k(i),d_i,f_i), con flujo fijado en 1 y distancia L_i. Corridas distintas conservan arcos distintos, aunque coincidan sus extremos y horarios.
2. Espera: entre eventos consecutivos en una misma ubicación y sector. Tiene distancia cero y duración igual a la diferencia de tiempos.
3. Traslado vacío: desde un evento de fin (k,p,t) hacia el primer evento de salida (k,q,s) de otra ubicación q que satisface t + tau_pq <= s. Su costo incluye D_pq y la espera residual s-t-tau_pq.
4. Salida de terminal: O a un evento de inicio, etiquetado por el terminal h de origen. La salida física ocurre en s_i-tau_hi y su distancia es D_hi.
5. Retorno: un evento de fin a un nodo de terminal h, con distancia D_ih y llegada f_i+tau_ih.
6. Estacionamiento final: nodo de terminal a Z. Capacidad ilimitada en T y C_e en E.
7. Cierre contable: Z a O. Su flujo cuenta buses y tiene costo c_F. No representa un desplazamiento ni una recarga nocturna.

El enlace al primer evento alcanzable y los arcos sucesivos de espera representan también las conexiones a salidas posteriores. No se descartan conexiones por un número máximo de vecinos o una espera máxima arbitraria. Esta agregación depende de tiempos de traslado constantes, espera lineal sin capacidad y ausencia de restricciones energéticas en esta fase.

## Variables y función objetivo

x_a = número de buses que recorren el arco a. F = x_cierre.

Minimizar:

    c_F F + c_K sum_{a != cierre} D_a x_a + c_W sum_a W_a x_a

W_a está expresado en minutos. Incluye espera entre actividades de servicio; no se cobra el estacionamiento anterior al primer servicio ni posterior al último. La distancia de servicio es constante si todas las corridas deben atenderse, pero se conserva en el objetivo y en el costo reportado.

No se incluyen costos eléctricos ni actividades de carga en esta fase. Por ello, su costo no se presenta como costo completo de operación eléctrica.

## Restricciones

Conservación en cada nodo v, incluidos origen y destino:

    sum_{a que entran a v} x_a - sum_{a que salen de v} x_a = 0

Cobertura exacta de cada corrida:

    x_a = 1, para cada arco de servicio a

Capacidad física al final del horizonte:

    x_(e,Z) <= C_e, para cada electroterminal e

Límites y dominio:

    l_a <= x_a <= u_a; x_a entero y no negativo

Se usa u_a = número de corridas como cota válida de arcos no capacitados; los arcos de servicio tienen l_a = u_a = 1. En electroterminales, u_a = C_e en su salida al destino final.

Al ser una circulación de costo mínimo con matriz de incidencia de red y cotas enteras, existe un óptimo entero de su relajación lineal. La implementación usa simplex y verifica integralidad y conservación antes de interpretar el resultado como buses. No redondea una solución fraccionaria arbitraria. La propiedad dejaría de estar asegurada si se agregan restricciones generales de batería o recursos.

Los sectores no comparten arcos de servicio o traslado entre sí. Sí comparten los límites físicos de estacionamiento final en los electroterminales. Por ello, en esta implementación se resuelven dentro de una misma red con ese acoplamiento. Si solo se permiten retornos a terminales ilimitados, los sectores se vuelven independientes en la fase 1. Las recargas compartidas siguen pendientes para la fase energética.

## Horizonte y medianoche

Se conservan horas GTFS superiores a 24:00. Para no crear buses en la primera parada ni eliminar corridas de madrugada, el horizonte de preparación comienza lo suficientemente temprano para permitir los traslados iniciales. Puede empezar antes de 00:00 del día de servicio. Termina después de la última corrida y su retorno. Los segundos inicial y final se guardan en el resultado.

Esta elección es una condición explícita del prototipo diario, no una solución a la transición semanal. Para encadenar días habrá que fijar el inventario y estado heredados, atender servicios que cruzan medianoche y evitar que cada día vuelva a decidir una distribución inicial libre.

## Garantías e interpretación

- Si Gurobi demuestra optimalidad, esta corresponde al modelo relajado, los sectores y la selección de corridas utilizados.
- La cantidad de buses de una solución que minimiza costo total no es automáticamente la flota mínima. Para obtener esa cota habría que minimizar F explícitamente.
- La cota por simultaneidad se calcula sobre la misma instancia seleccionada y se compara con la flota obtenida.
- Un óptimo del modelo sectorizado no se presenta como óptimo de toda la operación ni como cota inferior del problema global sin sectorizar.
- La descomposición entregada aquí solo identifica jornadas para auditar el flujo. No implementa aún la heurística energética de la fase 2.
- Cubrir el 100% de las corridas en la fase 1 no garantiza autonomía ni posibilidad de recarga.

## Estado de terminales

Las coordenadas de los recintos se registran en `terminales_espera.json`, junto con fuentes y observaciones. Son centros de recintos, no accesos verificados. Los Acacios permanece deshabilitado mientras no se confirme la discrepancia entre Valle de Los Reyes 863 y 5 Poniente 01460. La ejecución normal se detiene si hay terminales pendientes; la opción `--permitir-pendientes` habilita únicamente una prueba explícita con los terminales disponibles.
