# Ensayo de escala con 50 rutas laborales

Para la entrega 2 se recomienda usar **50 rutas completas como caso principal**, conservando una ruta para explicar la lógica y 20 rutas como ensayo previo. El tamaño recomendado está respaldado por una ejecución completa: no se supone que el código pueda escalar indefinidamente.

## Alcance

La muestra contiene 7.413 corridas laborales de 50 rutas: diez por cada uno de los cinco sectores. Se mantienen todas las salidas y variantes disponibles de cada ruta, los cuatro terminales comunes y los cinco electroterminales originales. La selección utiliza cuantiles de longitud media por sector, antes de resolver.

La muestra de 50 no contiene necesariamente las 20 rutas del ensayo anterior: son selecciones distintas con el mismo procedimiento. Por tanto, comparar sus tiempos describe el desempeño observado en dos instancias, no un experimento controlado en el que únicamente se incrementa el número de rutas.

## Resultados

| Etapa | Buses | Costo USD | Tiempo observado |
|---|---:|---:|---|
| Fases 1 y 2, sin restricciones energéticas | 832 | 293.570,24 | Gurobi: 6,78 s |
| Fase 3 constructiva, operación verificada | 949 | 327.923,64 | Tres fases y exportación: 22,33 s |
| Reparación dentro de cadenas | 940 | 325.603,51 | Reparación: 2,75 s adicionales |
| Intercambios entre jornadas | **886** | **310.656,91** | Búsqueda: 120,25 s adicionales |

Los tiempos tienen distintos alcances: la columna identifica qué mide cada uno. El comando completo de intercambios, incluida lectura, auditoría y exportación, tardó 124,18 segundos. La búsqueda usa un presupuesto de 120 segundos; el cierre y la auditoría pueden superarlo ligeramente.

El modelo de fase 1 contiene 14.619 nodos y 216.872 variables de flujo. Gurobi demostró optimalidad para esa fase sin energía. Sus 832 buses no son una solución energética ni un mínimo de flota demostrado por separado.

La reparación y los intercambios redujeron en conjunto 63 buses y USD 17.266,72 respecto de la fase 3 constructiva. El intercambio por sí solo redujo 54 buses y USD 14.946,59 frente a la solución reparada. Se evaluaron 938 alternativas y se aceptaron 168: 54 fusiones, 103 intercambios de sufijos y 11 movimientos individuales. Se alcanzó el presupuesto durante la primera ronda, sin demostrar optimalidad global.

La solución final cubre exactamente las 7.413 corridas y cumple continuidad espacial y temporal, sector, SOC entre 35 y 350 kWh, potencia, conexiones y estacionamiento. Suma 173.961,70 km, 8.335,83 kWh recargados y 188 sesiones. Los costos corresponden a un día aislado con energía inicial dada, como en las muestras anteriores.

| Electroterminal | Ocupación física máxima | Capacidad física | Cargas simultáneas máximas |
|---|---:|---:|---:|
| E1 | 104 | 150 | 4 |
| E2 | 75 | 180 | 8 |
| E3 | 69 | 120 | 5 |
| E4 | 100 | 100 | 7 |
| E5 | 150 | 150 | 5 |

E4 y E5 alcanzan su capacidad física; el ensayo sí incluye restricciones activas de estacionamiento. La disponibilidad de conexiones sigue siendo holgada en esta muestra. No se debe presentar este resultado como prueba de robustez frente a escasez de cargadores.

## Recomendación para la entrega

Mantener 50 rutas como alcance computacional principal y dedicar las siguientes pruebas a un caso base factible y a sensibilidad de parámetros. Aumentar nuevamente las rutas debería ser una prueba posterior, no una condición para cerrar esta entrega. Una mayor cantidad por sí sola no reemplaza la interpretación de resultados.

Para ampliar después conviene exigir cobertura completa y auditoría aprobada, tiempos medidos, conservación de la solución factible y capacidad de ejecutar varias comparaciones dentro del tiempo disponible. Lo verificado aquí es esta muestra de 50 rutas; no se garantiza el mismo desempeño para cualquier selección ni para la red completa.

## Repetir el ensayo

Desde la raíz del proyecto, usando el entorno con Gurobi:

```powershell
python tres_fases/ejecutar.py --cantidad 50
python tres_fases/mejorar.py --base output/tres_fases/muestra_50
python tres_fases/intercambiar.py --base output/tres_fases/muestra_50_reparada
```

El cambio de código de este ensayo amplía el rango admitido por `--cantidad` de 10–20 a 10–50. No se cambiaron las restricciones, la política de selección ni los algoritmos de las etapas. La verificación independiente se ejecutó sobre cada solución real; no se agregaron pruebas unitarias para un cambio de rango del argumento.

Resultados conservados en `output/tres_fases/muestra_50`, `muestra_50_reparada` y `muestra_50_reparada_intercambios`. El primer directorio contiene la selección de rutas y el modelo de Gurobi; los demás, los diagnósticos de mejora. La operación final y la comparación están en el último directorio.

El límite por tiempo hace que el número de intentos y las mejoras puedan variar con la carga del equipo. Las 20 rutas anteriores y sus resultados no se sobrescribieron. La licencia local de Gurobi observada en esta ejecución vence el 5 de octubre de 2027.
