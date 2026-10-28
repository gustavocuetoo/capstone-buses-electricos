# Revisión de factibilidad de la instancia completa laboral

Fecha: 6 de octubre de 2026. Solución revisada: `metodo_hibrido/resultados/completa_417_20261006/04_final/planes.json`.

## Dictamen para la presentación

**INCLUIR como solución factible del escenario laboral reconstruido y de los supuestos de modelamiento acordados.** La solución cubre las **64.502 corridas de las 417 rutas con 7.427 buses**. La reconstrucción desde el GTFS, el verificador operativo existente y una implementación adicional de auditoría coinciden. No se detectaron violaciones fuera de la tolerancia numérica declarada.

El costo implementado es **USD 2.638.494,33**. Este resultado acredita factibilidad, no optimalidad global ni un mínimo de flota demostrado.

Texto utilizable en una lámina:

> Se obtuvo una solución factible para las 64.502 corridas laborales reconstruidas de 417 rutas, utilizando 7.427 buses. Se verificaron cobertura exacta, continuidad temporal y espacial, batería, recargas y capacidades compartidas. El costo del modelo es USD 2.638.494,33. La solución es heurística; no se ha demostrado optimalidad global.

## Qué escenario se certifica

Se revisa un día laboral representativo (`service_id=L`), con salidas reconstruidas desde frecuencias. Todas las 6.620 filas de frecuencia utilizadas tienen `exact_times=0`: los horarios individuales son una instancia determinística representativa de los datos, tal como declara el informe del grupo; no son observaciones de salidas reales.

Las definiciones utilizadas son las del escenario vigente documentado en `CODIGO apstone/tres_fases/README.md` y en la guía de preparación de la entrega 2:

- Flota dimensionada por el método, sin imponer la referencia de 1.200 buses. El usuario confirmó que modificarla fue autorizado; también lo documenta el informe del grupo, página 8.
- Batería inicial de 350 kWh (100%), reserva de 35 kWh y máximo de 350 kWh; consumo de 1,4 kWh/km en servicio y en vacío.
- Potencia de carga individual máxima de 180 kW y conexiones originales por electroterminal. **El usuario confirmó durante esta revisión que esos son los límites eléctricos acordados.** Por ello, la ausencia de un dato separado de potencia de transformador no constituye aquí una restricción adicional incumplida.
- Capacidad física original de E1–E5 compartida por todos los sectores, incluyendo esperas, cargas y estacionamiento final. El calendario original `charging_activities.csv` tiene capacidad constante durante las 24 horas y también fue verificado.
- Cuatro terminales comunes T01–T04 sin cargadores y con estacionamiento ilimitado. Inicio en T y final en T o E. Los Acacios está excluido del escenario.
- Día aislado; la energía inicial es un dato y no se exige recuperar 100% al terminar. No se reinicia la batería a medianoche. Esta revisión no amplía el resultado a una repetición diaria cíclica.
- Tiempos vacíos calculados a 18 km/h, regulación mínima cero y espera permitida. La espera tiene costo cero en este modelo. El costo reportado suma buses, kilómetros, electricidad efectivamente comprada durante el horizonte y sesiones de recarga.
- No se impone una jornada máxima por bus. El autor retiró su supuesto local; los turnos de conductores no forman parte de este escenario.

Estos supuestos deben coincidir con la formulación y la explicación de la presentación. Las variantes de sábado y domingo no son parte de este resultado laboral.

## Comprobaciones realizadas

| Control | Evidencia y resultado |
|---|---|
| Universo desde el GTFS original | Se filtraron directamente `agency_id=RM`, `route_type=3` y `service_id=L` en `01-datos`. Se reconstruyeron 417 rutas, 6.620 patrones y 64.502 corridas desde las frecuencias y los extremos de `stop_times.txt`. Coinciden los identificadores, horarios, paradas, sentidos, geometrías y distancias con las fuentes del grupo y la instancia completa. |
| Cobertura exacta | Cada una de las 64.502 corridas aparece exactamente una vez. No hay omisiones, duplicaciones ni corridas desconocidas. |
| Continuidad temporal y espacial | Se recorrieron las 206.426 actividades de los 7.427 buses. Cada actividad empieza donde y cuando termina la anterior, conserva los horarios de servicio y pertenece al sector correspondiente. |
| Traslados vacíos | Los 62.740 movimientos usan distancias de las matrices fuente y duraciones iguales a `ceil(km × 3600 / 18)`. No se usan conexiones inexistentes ni se asigna distancia cero por ausencia de dato. Las distancias usadas también satisfacen la cota geográfica de distancia directa. |
| Batería | Se reconstruyó la energía actividad por actividad, descontando servicio y vacío y sumando recarga. Se verificó el balance final de cada bus y el rango 35–350 kWh con tolerancia de 0,000001 kWh. |
| Recargas | 6.000 bloques de cinco minutos, agrupados en 1.437 sesiones; únicamente en E1–E5, con alineación temporal y potencia individual dentro del límite acordado. Energía comprada total: 64.533,53183 kWh. |
| Recursos compartidos | Se recalcularon ocupación física y conexiones por instantes, para todos los sectores conjuntamente, con intervalos `[inicio, fin)`. Se respetan tanto los cupos nominales como los horarios originales de carga. |
| Inicio, fin y horizonte | Cada bus tiene movimientos de salida y retorno coherentes con su batería y la matriz. Todos cierran y quedan estacionados hasta el fin común. El horizonte se recalculó desde las mismas corridas y traslados, sin cambiar horarios de servicios. |
| Archivos exportados | Actividades, jornadas, recargas y resumen se conciliaron con los planes; estados energéticos y costos se reconstruyeron. Los dos cálculos independientes del costo difieren en aproximadamente 0,000000009 USD, por orden de acumulación numérica. |
| Auditor existente | Se volvió a ejecutar `verificar_completa.py` contra los datos y el auditor originales en una carpeta separada. Aprobó y confirmó las huellas de las fuentes originales. |
| Auditor adicional | `auditoria_independiente.py` no importa código del optimizador ni de sus verificadores. Implementa por separado la reconstrucción GTFS, los controles de actividades, batería, capacidad, costo y exportaciones. Aprobó. |
| Red vial dirigida | Se recalcularon caminos mínimos para 3.699 pares realmente usados, desde 352 orígenes, sobre un grafo de 1.018.534 nodos y 1.924.807 arcos. La diferencia máxima frente a la matriz fue 0,000000500 km, consistente con el redondeo a seis decimales. Los otros 728 pares, correspondientes a E, proceden de la matriz separada de electroterminales y se contrastaron con esa fuente y la cota geográfica; no se afirma que se hayan recalculado en el caché de T. |
| Pruebas del proyecto | Las 22 pruebas de `metodo_hibrido.test_hibrido` y `metodo_hibrido.test_caso_base` aprobaron. Se utilizó una licencia restringida válida para estas pruebas pequeñas. |
| Pruebas de rechazo | El auditor adicional rechazó diez corrupciones deliberadas: discontinuidad, horario modificado, distancia alterada, exceso de potencia, omisiones, bus duplicado, corridas duplicadas entre buses distintos, exceso de estacionamiento, exceso de conexiones y reserva de batería violada. Se comprobó el motivo esperado del rechazo. |
| Integridad de la solución | La revisión no modificó el optimizador ni los planes. Se compararon las huellas de los archivos de código y los cinco entregables antes y después del auditor adicional; el auditor original contrastó las huellas históricas de sus entradas. Se añadieron únicamente archivos de revisión. |

## Capacidades observadas

Las columnas de ocupación y carga son máximos independientes y pueden ocurrir a distintas horas. La potencia corresponde al máximo de la suma de potencias de los bloques de carga programados, suponiendo potencia constante dentro de cada bloque, como establece el modelo.

| Electroterminal | Ocupación máxima / plazas | Cargas simultáneas máximas / conexiones | Potencia máxima programada |
|---|---:|---:|---:|
| E1 Vespucio Norte | 150 / 150 | 28 / 150 | 4.705,579 kW |
| E2 El Conquistador | 180 / 180 | 45 / 180 | 7.103,897 kW |
| E3 Los Espinos | 120 / 120 | 21 / 120 | 3.048,991 kW |
| E4 La Reina | 100 / 100 | 26 / 100 | 3.931,439 kW |
| E5 Santa Rosa | 150 / 150 | 39 / 150 | 5.408,476 kW |

Las plazas físicas sí se saturan, pero no se exceden. Esta saturación forma parte de la solución y fue incluida en la auditoría; comprobar solo las conexiones habría sido insuficiente.

## Precisión numérica y alcance de la conclusión

La menor energía reconstruida fue 34,99999999214588 kWh, es decir, 0,00000000785412 kWh por debajo de 35 debido a la representación y solución numéricas. La mayor fue 350,00000000001023 kWh. Ambas desviaciones son inferiores a la tolerancia declarada de 0,000001 kWh. No se relajaron los límites físicos del modelo ni se editaron los planes para aprobar el control.

El horizonte común es de −7.145 a 99.119 segundos respecto de medianoche, y se obtuvo incluyendo las salidas iniciales y retornos requeridos por las corridas. Una secuencia puede atravesar medianoche; su amplitud máxima observada es de 26 h 19 min 11 s. Eso no viola un límite de jornada del escenario vigente y no representa una certificación de turnos de un conductor.

La cota por simultaneidad es de 6.601 buses a las 08:00. Los 7.427 buses son compatibles con esa cota; esta comparación no demuestra que sean el mínimo posible.

El resultado acredita factibilidad matemática para los datos preparados y los supuestos descritos. Los accesos de los terminales T y la velocidad constante en vacío son aproximaciones del modelo, documentadas en las fuentes. Esta revisión no sustituye una validación de accesos y tiempos en terreno.

## Fuentes y respaldo

- [Enunciado oficial](</Users/anitasepulveda/Desktop/Universidad/SEMESTRES/SEMESTRE 8/Capstone/Proyecto/00-enunciado/P7 Planificación de la operación de buses eléctricos en la Región Metropolitana.pdf>), páginas 1–2: cobertura, continuidad, energía, infraestructura compartida y justificación del modelamiento.
- [Informe del grupo](</Users/anitasepulveda/Desktop/Universidad/SEMESTRES/SEMESTRE 8/Capstone/Proyecto/05-entrega1/informe/Planificación_buses_GRUPO_29.pdf>), páginas 8–11: flota dimensionada autorizada, SOC inicial y reconstrucción determinística de 64.502 corridas.
- [Escenario documentado del grupo](</Users/anitasepulveda/Desktop/Universidad/SEMESTRES/SEMESTRE 8/Capstone/Proyecto/CODIGO apstone/tres_fases/README.md>): terminales, costos, horizonte, energía y capacidades.
- [Guía de preparación](</Users/anitasepulveda/Desktop/Universidad/SEMESTRES/SEMESTRE 8/Capstone/Proyecto/08-entrega2/guia_preparacion_entrega_2.pdf>), página 6: supuestos vigentes del escenario de entrega 2.
- [Auditor adicional reproducible](</Users/anitasepulveda/Desktop/Universidad/SEMESTRES/SEMESTRE 8/Capstone/Proyecto/metodo_hibrido/revision_factibilidad_20261006/auditoria_independiente.py>).
- [Resultado detallado del auditor adicional](</Users/anitasepulveda/Desktop/Universidad/SEMESTRES/SEMESTRE 8/Capstone/Proyecto/metodo_hibrido/revision_factibilidad_20261006/auditoria_independiente.json>).
- [Revisión de red vial](</Users/anitasepulveda/Desktop/Universidad/SEMESTRES/SEMESTRE 8/Capstone/Proyecto/metodo_hibrido/revision_factibilidad_20261006/verificacion_red_vial.json>).
- [Reejecución del auditor original](</Users/anitasepulveda/.codex/artifacts/capstone_417_20261006/revision_factibilidad/verificacion_original_reejecutada.json>).
- [Acuerdos confirmados por el usuario](</Users/anitasepulveda/.codex/artifacts/capstone_417_20261006/revision_factibilidad/acuerdos_confirmados.json>).

Para repetir el auditor adicional desde la carpeta del proyecto:

```text
python3 -B metodo_hibrido/revision_factibilidad_20261006/auditoria_independiente.py
```

Para repetir la revisión de caminos mínimos, con NumPy y SciPy disponibles:

```text
python3 -B metodo_hibrido/revision_factibilidad_20261006/revisar_red_vial.py
```

La conclusión anterior corresponde exclusivamente a esta solución y a este escenario; no es una declaración de que cualquier resultado del método sea factible sin auditarlo.
