# Reparación local de las divisiones de jornadas

Se mantuvieron las mismas 20 rutas, las 4.001 corridas y los resultados de fases 1 y 2. La ejecución original se conserva en `output/tres_fases/muestra_20`. La nueva operación y la comparación están en `output/tres_fases/muestra_20_reparada`.

| Indicador | Original | Reparada |
|---|---:|---:|
| Corridas verificadas | 4.001 | 4.001 |
| Buses | 513 | 507 |
| Buses adicionales respecto de fase 2 | 91 | 85 |
| Costo total, USD | 176.228,65 | 174.702,43 |
| Cobertura, horarios, batería y capacidades | Cumple | Cumple |

Se ahorran seis buses y USD 1.526,22 por la instancia de un día. La reparación tardó 2,14 segundos adicionales en la ejecución final; no es el tiempo total de preparación y solución de las tres fases. Se comprobaron 23 pruebas automatizadas.

## Qué cambió

Antes de dar por definitiva una división, se intenta unir dos fragmentos consecutivos de la misma cadena de fase 2. Se retiran temporalmente sus reservas de carga y estacionamiento. Las reservas de los demás buses se mantienen fijas. Un modelo local decide terminal inicial/final, electroterminal, ventana de carga y cantidad de energía para la secuencia completa de servicios de ambos fragmentos.

La búsqueda considera huecos anteriores a la división y puede sustituir sus recargas por otras, incluyendo cambiar de electroterminal. Si se consigue fusionar y bajar el costo, se valida la operación completa y se actualiza el calendario. Si falla, se restituyen las reservas originales. Una fusión aceptada puede volver a intentar unirse al fragmento siguiente.

No se cambian horarios, servicios ni sectores. No se intercambian servicios entre cadenas diferentes en esta versión. La reparación se ejecuta sobre la solución constructiva completa, antes de publicar una versión mejorada; no altera los archivos de la solución base.

## Modelo local

Los servicios y su orden son fijos. Las variables son binarias de selección de terminal y de una opción de recarga por hueco, energía cargada por opción y energía al terminar cada servicio. No hay una matriz global de variables bus × servicio.

Para una opción `k` de duración de `n_k` bloques:

- `0 ≤ q_k ≤ 15 n_k y_k`, y como máximo una opción por hueco.
- `35 ≤ E_j ≤ 350` kWh.
- En el primer servicio se descuenta el traslado inicial y el servicio de una batería de 350 kWh.
- Entre servicios, `E_j = E_(j−1) − 1,4(directo + servicio_j) + Σ_k[q_k − 1,4(desvío_k − directo)y_k]`.
- Si se visita un E, se exige llegar con al menos 35 kWh y no superar 350 kWh al terminar la carga.
- Al finalizar se exige alcanzar el terminal elegido con al menos 35 kWh.

Las opciones ya cumplen el tiempo disponible, las conexiones y las plazas que dejan los otros buses. La energía de cada opción se distribuye uniformemente entre sus bloques, respetando 180 kW. Su tarifa es el promedio de las tarifas de esos bloques, por lo que el costo coincide con la energía efectivamente programada.

El objetivo local suma kilómetros vacíos, energía y sesiones de carga. Los kilómetros de servicio son constantes y el candidato usa un único bus. La aceptación compara el costo completo del candidato contra el de los dos buses anteriores: no basta con obtener factibilidad o reducir flota si el costo total aumenta.

## Qué explica las seis mejoras

Se ejecutaron dos variantes para cada intento:

1. Mantener la reserva de energía para volver directamente a un terminal común después de cada servicio.
2. Si la primera no obtiene una mejora, retirar esa reserva adicional y conservar las restricciones físicas: SOC mínimo de 10%, viajes posibles, capacidad y retorno final a T o E.

De 91 intentos, ninguno logró una fusión con la reserva conservadora. Seis lo hicieron al retirarla. **La mejora observada se atribuye a flexibilizar esa regla heurística; no demuestra que adelantar recargas, por sí solo, reduzca flota en esta muestra.** Las pruebas sintéticas sí comprueban que el modelo local puede insertar una recarga y unir dos fragmentos cuando hay un hueco suficiente.

Los otros 85 intentos fueron infactibles para el modelo local y su catálogo de opciones, en ambos modos. No hubo agotamiento del tiempo en estos intentos. Esto no demuestra que sus buses sean imprescindibles en una optimización global: el orden de servicios y las reservas de otros buses permanecen fijos, y el catálogo de recargas no es exhaustivo.

El diagnóstico CSV identifica cada unión intentada, el hueco inmediato disponible, energía al terminar el fragmento anterior, déficit directo para el siguiente servicio con/sin reserva de retorno, cantidad de opciones de recarga, estados del optimizador y ahorro. El déficit directo no incluye una nueva recarga; sirve para describir la situación inicial, no para concluir infactibilidad por sí solo.

## Límites y siguiente mejora

Por cada corrida de bloques libres se prueban duraciones de 1, 2, 3, 4, 6, 8, 12, 16, 21 y 24 bloques, recortadas al espacio disponible; se ubican al inicio, al final o en cambios tarifarios. Cada modelo tiene dos segundos de límite y una brecha relativa objetivo del 2%. Se acepta una solución incumbente solamente si pasa la auditoría y mejora el costo. Una falla local no se presenta como infactibilidad del proyecto.

Las operaciones siguen usando el supuesto de un día aislado, carga inicial dada, terminales comunes ilimitados y los cinco E originales. Se contabiliza toda presencia física y se respeta el calendario compartido. La validación completa ocurre antes de aceptar cada fusión y nuevamente al terminar.

El siguiente cambio útil sería permitir intercambios acotados de servicios entre cadenas del mismo sector, priorizando las divisiones que siguen sin reparar. Aumentar la muestra por sí solo no resolverá esas incompatibilidades. No se ha demostrado optimalidad global ni mínima flota.

## Cómo ejecutarlo

Desde la raíz, con el entorno de Python y Gurobi usado en las pruebas anteriores:

```powershell
python tres_fases/mejorar.py
python tres_fases/mejorar.py --base output/tres_fases/rutas_101
python -m unittest tres_fases.test_reparar tres_fases.test_modelos fase1.test_modelo test_distancias_electroterminales
```

El primer comando utiliza la muestra de 20 rutas existente. `--salida` permite elegir otra carpeta, diferente de la base, y `--limite-local` modifica el límite por resolución local. El script vuelve a comprobar la solución original antes de repararla.

Archivos nuevos de implementación: `reparar.py`, `mejorar.py` y `test_reparar.py`. La carpeta de resultados contiene `comparacion.json`, `diagnostico_reparaciones.csv`, `jornadas.csv`, `actividades.csv` y `recargas.csv`.

Las cuatro pruebas nuevas verifican una fusión con recarga, conservación del resultado tras un rechazo, bloqueo por estacionamiento ajeno y factibilidad física al retirar la reserva conservadora de retorno a T.
