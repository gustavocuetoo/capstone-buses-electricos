# Caso base simple: partición óptima de cadenas sin recarga

## Qué hace

Cubre las 212 rutas y las 33.220 corridas completas. Toma las 3.561 cadenas de servicios de la fase 2 antigua y decide la partición de menor costo en jornadas factibles sin recargas. No usa la solución del híbrido ni su constructor cronológico, búsquedas de parejas o tríos.

Cada fragmento se asigna a un bus diferente. Comienza con batería llena en un terminal común T y termina en un T. Mantiene 35 kWh de reserva, batería de 350 kWh y consumo de 1,4 kWh/km. Conserva sectores, horarios y traslados de los datos recibidos. No existe un límite de flota en este escenario. Los T tienen capacidad ilimitada según los supuestos originales; no utiliza los electroterminales E.

**Es un modelo entero de camino mínimo en una red acíclica, no una heurística de cortar al primer problema.** Enumera todos los fragmentos consecutivos factibles y elige la combinación de costo mínimo. Puede elegir terminar antes aunque aún quede batería si eso reduce el costo total.

## Por qué es fácil de resolver

Sin recargas ni estacionamiento en E, no hay recursos limitados compartidos entre cadenas. Por eso resolver cada cadena por separado es una descomposición exacta de ESTE caso base: no se están omitiendo corridas ni conflictos existentes dentro de esta formulación.

En los datos entregados hay 185.703 fragmentos candidatos en total, pero se resuelve un modelo por vez. El mayor tiene **465 variables binarias y 31 restricciones lineales**. No hay restricciones indicadoras, grandes constantes M ni variables de batería: la factibilidad energética se verifica al generar cada fragmento.

No se ha ejecutado Gurobi en el entorno de preparación. No se garantiza un tiempo en otro equipo; el tamaño y la estructura son mucho más favorables que los del modelo anterior. El arranque de 3.561 modelos también tiene un costo de tiempo. Se reutiliza un mismo entorno de Gurobi.

## Modelo matemático

Para una cadena con n servicios, crear nodos 0,1,...,n. Un arco (a,b), con a<b, representa un bus que atiende los servicios a+1,...,b de la cadena.

Solo generar el arco si la salida desde T y el regreso a T cumplen el horizonte y si:

    1,4 × (km de salida + km de servicios y enlaces + km de regreso) <= 350 - 35

Como no hay recargas y el consumo es no negativo, esta condición también garantiza la reserva durante toda la jornada. Los enlaces temporales y de sector se verifican al leer las cadenas.

Costo del arco: c(a,b) = 250 + 0,50 × km totales del fragmento.

Variable z(a,b) binaria: se elige o no ese fragmento.

    minimizar SUMA c(a,b) z(a,b)

    SUMA arcos que salen de v - SUMA arcos que entran en v =
        1 si v=0; -1 si v=n; 0 en los otros nodos.

Un camino de 0 a n cubre todos los servicios exactamente una vez. El número de arcos elegidos es la cantidad de buses. Se repite para todas las cadenas y se suman sus costos. La matriz de flujo de esta red admite soluciones óptimas enteras en su relajación; se usan variables binarias para entregar explícitamente un modelo de programación entera.

## Qué se comprobó realmente

Se resolvió la misma red mediante programación dinámica exacta, sin Gurobi, para las 212 rutas completas. El plan reconstruido pasó el auditor original:

- Buses: **5.150**.
- Costo total: **USD 1.685.098,05**.
- Distancia total: **795.196,093901 km**.
- Recargas y electricidad comprada durante el horizonte: **0**.
- Reserva mínima observada: **35,050338 kWh**.

La cifra es un resultado del modelo restringido obtenido por programación dinámica; **no es una corrida de Gurobi**. El motor Gurobi se incluye, pero su prueba de integración sigue pendiente. En ejecución compara automáticamente el óptimo de cada modelo con el cálculo por programación dinámica y después vuelve a auditar el plan completo. Ante discrepancias o un modelo no resuelto a optimalidad, falla explícitamente y no lo reemplaza silenciosamente por otro método.

El plan puede diferir por empates, pero debería tener el mismo costo dentro de tolerancias numéricas. El número de buses no es un objetivo lexicográfico adicional: se minimiza el costo total.

Este resultado es diferente del arranque voraz previo de 5.150 buses y USD 1.690.138,96: aquí se optimizan los cortes, reduciendo kilómetros.

## Cómo ejecutarlo con Gurobi

Requisitos: Python 3.10 o posterior, gurobipy 12 o posterior y una licencia válida de Gurobi. No se necesita NumPy, SciPy ni ejecutar el código antiguo. Los datos normalizados y las cadenas están incluidos.

Abrir una terminal dentro de la carpeta extraída:

```powershell
python -m pip install -r requirements.txt
python -m unittest -v test_modelo
python ejecutar.py --motor gurobi --salida corrida_gurobi
```

Por defecto se usa un hilo y un límite de 60 segundos POR CADENA, no para todo el proceso. Se exige estado óptimo y se fija MIPGap=0. Si algún modelo alcanza el límite, aumentar --tiempo-cadena y usar una carpeta nueva. No se sobrescriben resultados.

Para comprobar todo sin Gurobi:

```powershell
python ejecutar.py --motor dinamica --salida corrida_dinamica
```

## Archivos de salida

- resumen.json: cobertura, costo auditado, flota, tamaño y motor realmente utilizado.
- modelos.csv: tamaño, costo y buses por cadena; con Gurobi agrega estado, cota, gap y tiempo del solver.
- jornadas.csv y actividades.csv: planificación completa auditable.
- planes.json: plan completo estructurado.
- configuracion.json: opciones de la corrida.
- gurobi.log: registro disponible del entorno; la salida detallada de cada modelo se silencia para evitar miles de logs. La evidencia por modelo está en modelos.csv.
- fallo.json: error; no considerar completada una ejecución con este archivo.

El tiempo informado se mide hasta antes de exportar los archivos finales; no incluye todo el tiempo de escritura.

La carpeta evidencia_dinamica contiene el resumen y las jornadas de la ejecución verificada aquí, más el detalle de modelos. No confundir estos archivos con resultados obtenidos con Gurobi.

## Cómo funciona el código

ejecutar.py:
- segments: enumera fragmentos y calcula su costo. No descarta extensiones solo porque el regreso intermedio sea largo; el regreso de un servicio posterior puede ser más corto.
- shortest: calcula el camino mínimo por programación dinámica, para verificación independiente del solver.
- solve_gurobi: formula y resuelve un pequeño modelo entero por cadena.
- run: carga datos, une las soluciones, reconstruye actividades y ejecuta la auditoría original.

datos_y_auditoria.py contiene las funciones de lectura y reconstrucción adaptadas del paquete anterior. validador_grupo.py conserva el auditor original. test_modelo.py comprueba el camino mínimo frente a enumeración exhaustiva en 80 redes pequeñas, un caso donde una regla voraz falla, la detección de infactibilidad y una extensión cuyo regreso se vuelve más corto.

## Limitaciones para presentar

Este es un caso base simple sin recargas, no un competidor que aproveche toda la infraestructura. Una mejora del híbrido refleja conjuntamente recargas y cambios de asignación; no atribuir toda la diferencia a la heurística.

Las cadenas están fijadas y no se intercambian servicios. Se fija el T inicial y final factible más cercano para cada extremo, con distancias dirigidas. Dado que aquí no hay carga ni capacidades limitadas en T, minimizar esos kilómetros favorece tanto costo como autonomía para cada fragmento.

Los buses comienzan llenos y no se cobra reponer esa energía al final, igual que en el escenario recibido. No interpretar electricidad comprada cero como consumo energético cero. No representa una operación repetida entre días.

El óptimo y la cota se refieren SOLO a esta partición sin recargas, no al problema original ni al híbrido. Sigue siendo recomendable conservar la metodología antigua completa como comparación más exigente. No se entrega una nueva cota inferior global.

Origen: datos normalizados de las 212 rutas y cadenas de output/tres_fases/muestra_212/fase2/actividades.csv del ZIP anterior. No se utilizan resultados del híbrido para construir este caso base.
