# Preguntas para el profesor — Planificación de operación de buses eléctricos (RM)

> 15 preguntas, derivadas de contrastar el enunciado, la bibliografía verificada (`bibliografia.md`) y una auditoría real de los archivos en `data-alumnos/`. Cada una cumple los 4 criterios de §7.1 del AGENT.md: no está respondida en el enunciado, es decisión-relevante, está anclada a literatura o evidencia de datos, y trae supuesto por defecto.

---

## 1. Bloqueantes (sin respuesta no se puede empezar a formular)

#### Q01 — Falta la tabla de viajes operacional: ¿la construimos nosotros o falta un archivo?
- **Categoría:** Datos · **Prioridad:** CRÍTICA (bloquea todo lo demás)
- **Contexto:** `data-alumnos/parametros_descripcion.csv` documenta campos como `distance_km`, `duration_min`, `energy_kwh`, `deadhead_distance_km`, `deadhead_time_min`, `pullout_km`, `pullout_time`, `pullin_km`, `pullin_time` por viaje. Revisamos **todos** los CSV entregados (`depots.csv`, `vehicles.csv`, `charger_capacity.csv`, `electricity_prices.csv`, `parameters.csv`, `charging_activities.csv`, `shape_distances.csv`) y ninguno contiene esas columnas a nivel de viaje — solo existe el GTFS crudo (`trips.txt`, `stop_times.txt`, `shapes.txt`) y `shape_distances.csv` (distancia total por *shape*, no por viaje ni por *deadhead*).
- **Pregunta:** ¿Debemos construir nosotros la tabla de viajes con distancia, duración, energía y *deadhead*/*pullout*/*pullin* a partir del GTFS crudo, o falta un archivo por entregar? Si la construimos nosotros: ¿el *deadhead* entre actividades se calcula con distancia geográfica (Haversine) entre paraderos, o se espera una distancia de red vial real?
- **Supuesto por defecto si no hay respuesta:** construimos la tabla nosotros: `distance_km`/`duration_min` desde `stop_times.txt` + `shapes.txt`/`shape_distances.csv`; `energy_kwh = distance_km × (battery_kwh / range_km)` usando la tasa implícita de `vehicles.csv` (350/250 = 1,4 kWh/km); *deadhead* y *pullout*/*pullin* como distancia Haversine × un factor de circuidad de ciudad (documentado explícitamente como supuesto, no como dato).
- **Impacto de la respuesta:** define si el primer sprint del proyecto es ingeniería de datos (varias semanas) o si podemos partir directo del modelo — cambia la planificación completa del proyecto, no solo el modelo.

---

#### Q02 — ¿Los horarios/recorridos del GTFS son fijos, y para qué día tipo?
- **Categoría:** Datos/Escala · **Prioridad:** CRÍTICA
- **Contexto:** `calendar.txt` define 6 patrones de servicio (`L`=lunes-viernes, `S`=sábado, `D`/`F`=domingo/festivo, `LJ`=lunes-jueves, `V`=viernes) vigentes 2026-07-04 a 2026-12-31. El enunciado no indica qué día se debe planificar, y Häll et al. (2018) (P-15) muestran que en la práctica el rediseño de horarios y rutas suele acoplarse al scheduling eléctrico — no es evidente que debamos tratar el GTFS como inmutable.
- **Pregunta:** ¿Se planifica para un día laboral tipo (`service_id = L`), y se asume el GTFS (rutas, horarios, paraderos) como dato fijo e innegociable, o el equipo puede proponer ajustes menores de *timetable* si mejoran la factibilidad energética?
- **Supuesto por defecto si no hay respuesta:** día laboral tipo (`service_id = L`), GTFS 100% fijo — no se modifican rutas ni horarios, solo la asignación de buses y la programación de carga.
- **Impacto de la respuesta:** determina el tamaño de instancia exacto (número de viajes/día) y si el espacio de decisión incluye o no el rediseño de horario.

---

#### Q03 — ¿Los datos de `data-alumnos` son un recorte deliberado del problema real, o representan la RM completa?
- **Categoría:** Alcance · **Prioridad:** CRÍTICA
- **Contexto:** el reporte ZEBRA/CMM-Chile/IEA (Galarza, 2020, P-20) documenta que RED tenía 6.756 buses en 2018 y ha seguido creciendo (>2.500-3.500 unidades eléctricas reportadas en prensa 2025); `parameters.csv` fija `fleet_size = 1200` y solo 5 depósitos en `depots.csv`. Ningún valor de `data-alumnos` coincide con cifras oficiales que verificamos (Ministerio de Energía, P-19; Galarza 2020, P-20).
- **Pregunta:** ¿Los 1.200 buses y los 5 electroterminales de `data-alumnos` son un universo cerrado y autocontenido para efectos del proyecto (no representan necesariamente la RM real), o se espera que contrastemos/ajustemos estos números contra fuentes públicas reales?
- **Supuesto por defecto si no hay respuesta:** tratamos `data-alumnos` como universo cerrado y autosuficiente — no se mezcla con cifras de fuentes externas para restricciones del modelo (aunque sí se usan para *validar realismo* en la discusión).
- **Impacto de la respuesta:** define si el reporte final necesita una sección de "brecha con la realidad" o si la validación externa está fuera de alcance.

---

#### Q04 — ¿La flota de 1.200 buses es un dato fijo o una variable de decisión?
- **Categoría:** Modelamiento · **Prioridad:** ALTA (bloquea la función objetivo)
- **Contexto:** `parameters.csv` da `fleet_size = 1200` y `vehicle_fixed_cost = 250`, lo que sugiere que el número de buses *usados* (no necesariamente el máximo disponible) podría ser una decisión que minimiza costo. Legault, Cabral & Sun (2025) (P-17) resuelven precisamente la versión donde flota e infraestructura son decisión de inversión — pero acoplan eso a horizontes multi-periodo, que no calza con un problema de un día.
- **Pregunta:** ¿`fleet_size = 1200` es una cota superior (el equipo decide cuántos de esos 1.200 usar, minimizando `vehicle_fixed_cost`), o es el número de buses que deben operar sí o sí ese día?
- **Supuesto por defecto si no hay respuesta:** cota superior — el modelo puede usar entre 1 y 1.200 buses, minimizando el costo total incluyendo `vehicle_fixed_cost` por bus activado.
- **Impacto de la respuesta:** cambia la función objetivo (¿minimizar buses es un objetivo real o una restricción de capacidad?) y el tipo de solución esperada.

---

## 2. De modelamiento

#### Q05 — Representación de red: ¿time-space network o connection-based?
- **Categoría:** Modelamiento · **Prioridad:** ALTA
- **Contexto:** Bunte & Kliewer (2009) (P-01) documentan dos familias de representación del VSP clásico; Kliewer, Mellouli & Suhl (2006) (P-02) muestran que el *time-space network* agregado escala mucho mejor a instancias grandes (miles de viajes) que el *connection-based network*. Dado que el GTFS entregado tiene ~26.000 *trips* totales (múltiples días de servicio) y 428 rutas, la elección de representación tiene impacto computacional real, no solo estético.
- **Pregunta:** ¿Se espera que el equipo justifique explícitamente la elección de representación de red en función del tamaño de instancia esperado, o basta con una formulación *connection-based* simple si se trabaja con una instancia reducida?
- **Supuesto por defecto si no hay respuesta:** *time-space network* agregado (siguiendo Kliewer et al. 2006) como formulación base, dado que el enunciado habla de "miles de viajes programados".
- **Impacto de la respuesta:** afecta directamente la escalabilidad del modelo exacto y la elección de solver/heurística.

---

#### Q06 — ¿Las ubicaciones de los electroterminales son dato fijo o parte de la decisión?
- **Categoría:** Modelamiento · **Prioridad:** MEDIA
- **Contexto:** Xylia et al. (2017) (P-14) resuelven la localización de electroterminales como problema de optimización (nivel táctico/estratégico); `data-alumnos/depots.csv` da 5 electroterminales con coordenadas y capacidad fijas.
- **Pregunta:** ¿Los 5 electroterminales de `depots.csv` son ubicaciones fijas para todo el proyecto, o se espera evaluar sensibilidad agregando/moviendo electroterminales hipotéticos?
- **Supuesto por defecto si no hay respuesta:** ubicaciones y cantidad de electroterminales fijas (dato, no decisión) — el proyecto es puramente operacional (E-VSP + *charging scheduling*), no de localización.
- **Impacto de la respuesta:** determina si el alcance incluye un componente de diseño de infraestructura (fuera del E-VSP puro) o no.

---

#### Q07 — Capacidad del electroterminal: ¿cargadores discretos, potencia agregada, o ambos?
- **Categoría:** Modelamiento · **Prioridad:** CRÍTICA (bloquea la formulación central del proyecto)
- **Contexto:** el enunciado menciona explícitamente "un número finito de cargadores **y** una capacidad eléctrica restringida", que son dos restricciones distintas. La literatura las trata por separado: de Vos, van Lieshout & Dollevoet (2024) (P-12), Jiang, Zhang & Zhang (2022) (P-13) y He, Liu & Song (2020) (P-11) modelan cupos discretos de carga simultánea; Zapata (2022) (P-23) dimensiona la restricción de **potencia agregada** (MW) a nivel de sistema eléctrico. En los datos entregados, `charger_capacity.csv` y `charging_activities.csv` solo dan cupos discretos (`max_simultaneous_charging`, bloques horarios de capacidad en N° de buses); **el campo `transformer_mw` que el propio `parametros_descripcion.csv` describe como "capacidad máxima de potencia disponible en el electroterminal, MW" no existe en ningún archivo entregado.**
- **Pregunta:** ¿Debemos modelar ambas restricciones simultáneamente (cargadores discretos **y** potencia agregada en MW), aunque el dato de potencia no esté en los archivos entregados y debamos asumir un valor, o basta con la restricción de cargadores discretos que sí está en los datos?
- **Supuesto por defecto si no hay respuesta:** modelamos solo la restricción de cargadores discretos (`max_simultaneous_charging` / bloques de `charging_activities.csv`), que es la única con dato real entregado, y reportamos como trabajo futuro la extensión a potencia agregada con un valor de MW supuesto y análisis de sensibilidad.
- **Impacto de la respuesta:** define si el modelo es un flujo en red con restricción de recurso discreto simple, o requiere restricciones de recurso acopladas (energía) por bloque horario — afecta directamente la elección del método de solución.

---

#### Q08 — Consumo energético y curva de carga: ¿modelos lineales o realistas?
- **Categoría:** Modelamiento · **Prioridad:** ALTA
- **Contexto:** `vehicles.csv`/`parameters.csv` dan una tasa constante `battery_kwh/range_km = 1,4 kWh/km` y una potencia de carga constante (`charge_power_kw = 180`), lo que implica consumo lineal en distancia y carga a tasa constante. van Kooten Niekerk et al. (2017) (P-08) comparan explícitamente un modelo simplificado (carga lineal) contra uno detallado (curva no lineal, depreciación por profundidad de descarga). Basso et al. (2024) (P-21), con datos reales desagregados de RED, muestran que el consumo real depende de conductor y ocupación de pasajeros, no solo de distancia — y el piloto real documentado en Galarza (2020) (P-20) reporta 1,006 kWh/km, distinto del 1,4 kWh/km implícito en nuestros datos.
- **Pregunta:** ¿Aceptan el supuesto de consumo lineal en distancia y carga a potencia constante (tal como están estructurados los datos entregados), o esperan que el equipo justifique/incorpore una relación más rica (no lineal, dependiente de variables operacionales)?
- **Supuesto por defecto si no hay respuesta:** consumo lineal en distancia con la tasa 1,4 kWh/km de `vehicles.csv`, y carga a potencia constante `charge_power_kw`; se documenta la brecha de 1,4 vs. 1,006 kWh/km (dato real) como limitación explícita, no se ignora silenciosamente.
- **Impacto de la respuesta:** cambia la complejidad matemática del submodelo energético (lineal = tratable exactamente; no lineal = requiere discretización o aproximación, como en van Kooten Niekerk et al. 2017).

---

#### Q09 — ¿Se descarta explícitamente el *battery swapping* como fuera de alcance?
- **Categoría:** Modelamiento · **Prioridad:** MEDIA
- **Contexto:** Li (2014) (P-10) modela *battery swapping* como alternativa a la recarga in situ. `vehicles.csv` no contempla esa opción (un solo tipo de vehículo, sin parámetro de tiempo de intercambio de batería), y no hay evidencia de infraestructura de *swapping* en la RM real.
- **Pregunta:** ¿Confirmamos que el alcance del proyecto es exclusivamente recarga in situ (plug-in), descartando *battery swapping* como alternativa a evaluar?
- **Supuesto por defecto si no hay respuesta:** sí, se descarta explícitamente *battery swapping* — no hay dato ni evidencia de esa infraestructura en el caso chileno.
- **Impacto de la respuesta:** acota el espacio de alternativas de modelamiento de la recarga; bajo impacto si se confirma el default.

---

#### Q10 — ¿El proyecto asume *vehicle scheduling* desacoplado de *crew scheduling*?
- **Categoría:** Modelamiento · **Prioridad:** MEDIA
- **Contexto:** Desaulniers & Hickman (2007) (P-03) ubican el *vehicle scheduling* y el *crew scheduling* (turnos de conductores) como problemas relacionados pero tradicionalmente resueltos por separado; ninguno de los datos entregados (`vehicles.csv`, `parameters.csv`) menciona restricciones de turnos, descansos o jornada de conductores.
- **Pregunta:** ¿Confirmamos que el proyecto solo cubre *vehicle scheduling* (asignación de buses a viajes + carga), dejando *crew scheduling* explícitamente fuera de alcance?
- **Supuesto por defecto si no hay respuesta:** sí, se excluye *crew scheduling*; se declara como supuesto de alcance en el informe.
- **Impacto de la respuesta:** bajo impacto en el modelo si se confirma el default; alto impacto si se esperara integración (obligaría a un modelo mucho más complejo, tipo P-16/branch-and-price integrado).

---

## 3. De alcance y evaluación

#### Q11 — ¿Contra qué baseline se evalúa el resultado?
- **Categoría:** Evaluación · **Prioridad:** ALTA
- **Contexto:** Oemick (2019) (P-22) y Basso et al. (2024) (P-21) comparan escenarios eléctricos contra una operación diésel de referencia usando costos reales de RED; nuestros datos no incluyen un escenario diésel ni una solución de referencia.
- **Pregunta:** ¿Se espera comparar el plan óptimo contra algún baseline (ej. asignación *greedy*/miope, o una cota inferior teórica), o basta con reportar factibilidad + costo total sin punto de comparación externo?
- **Supuesto por defecto si no hay respuesta:** comparamos contra una heurística *greedy* simple construida por el propio equipo (no contra diésel, por falta de datos comparables) y reportamos el *gap* respecto a la cota LP del modelo exacto en instancias reducidas.
- **Impacto de la respuesta:** determina si hay que construir un baseline adicional (trabajo extra) o si el informe se limita a caracterizar la solución propia.

---

#### Q12 — ¿Determinístico con análisis de sensibilidad, o incertidumbre modelada explícitamente?
- **Categoría:** Evaluación/Modelamiento · **Prioridad:** ALTA
- **Contexto:** Perumal, Lusby & Larsen (2022) (P-04) identifican la robustez/incertidumbre como el vacío más citado de la literatura de E-VSP; Ricard, Desaulniers, Lodi & Rousseau (2026) (P-18) ya proponen un modelo *chance-constrained* para consumo y degradación estocásticos. Todos los datos entregados (`parameters.csv`, `electricity_prices.csv`, etc.) son valores puntuales, sin distribuciones.
- **Pregunta:** ¿Se espera que el equipo aborde incertidumbre (tiempos de viaje, consumo energético) de forma explícita (chance-constrained, robusto), o basta un modelo determinístico con análisis de sensibilidad sobre los parámetros clave?
- **Supuesto por defecto si no hay respuesta:** modelo determinístico + análisis de sensibilidad ex-post sobre consumo energético (±15%) y tiempos de *deadhead* (±10%), sin modelo estocástico explícito en la formulación.
- **Impacto de la respuesta:** cambia sustancialmente la complejidad metodológica del proyecto — de un modelo determinístico tratable a uno con restricciones probabilísticas o programación robusta.

---

#### Q13 — Función objetivo: ¿suma ponderada única o multiobjetivo con trade-offs explícitos?
- **Categoría:** Evaluación/Modelamiento · **Prioridad:** ALTA
- **Contexto:** `parameters.csv` entrega varios componentes de costo en la misma unidad monetaria (`cost_per_km`, `waiting_cost_per_min`, `vehicle_fixed_cost`, `fixed_charge_cost`, tarifa eléctrica horaria), lo que sugiere una función de costo aditiva única. Sin embargo, Perumal et al. (2022) (P-04) tratan minimización de flota, costo de *deadhead* y costo energético como objetivos frecuentemente reportados por separado en la literatura revisada, y el enunciado enfatiza conceptualmente el *trade-off* energía-vs-*deadhead* como algo a "evaluar", no necesariamente a fusionar en un solo número.
- **Pregunta:** ¿Se espera una única función objetivo de costo total (suma ponderada de los componentes dados), o un análisis multiobjetivo/frontera de Pareto entre costo energético y costo de *deadhead*/flota?
- **Supuesto por defecto si no hay respuesta:** función objetivo única de costo total aditivo (todos los componentes de `parameters.csv` en la misma unidad monetaria), con un análisis de sensibilidad posterior mostrando el *trade-off* entre componentes (no una optimización multiobjetivo formal).
- **Impacto de la respuesta:** define si se necesita un solver multiobjetivo o basta un solver mono-objetivo estándar.

---

## 4. De validación de enfoque

#### Q14 — Ruta metodológica: ¿exacto en instancia reducida + heurística para escalar?
- **Categoría:** Validación de enfoque · **Prioridad:** ALTA
- **Contexto:** Wu, Lin & Li (2025) (P-16) resuelven a optimalidad hasta 101 viajes con branch-and-price — muy por debajo de los "miles de viajes" del enunciado y de los ~26.000 *trips* del GTFS entregado. Wen et al. (2016) (P-07) muestran que una metaheurística (ALNS) sí escala a instancias grandes, sacrificando garantía de optimalidad.
- **Pregunta:** Planeamos partir con una formulación exacta (time-space network, ver Q05) sobre una instancia reducida (un electroterminal o un subconjunto de rutas) para validar el modelo, y luego escalar con una metaheurística tipo ALNS extendida con capacidad de carga (P-07 + P-12) para la instancia completa. ¿Ven riesgos en esa ruta, o prefieren que prioricemos una sola de las dos etapas?
- **Supuesto por defecto si no hay respuesta:** seguimos la ruta de dos etapas (exacto en reducida → heurística para escala completa), reportando el *gap* de la heurística contra el óptimo de la instancia reducida como validación de calidad.
- **Impacto de la respuesta:** afecta la planificación de tiempo del proyecto (dos implementaciones en vez de una) y qué se reporta como resultado principal.

---

#### Q15 — ¿Empezamos con E-VSP puro (sin capacidad de carga) y añadimos la restricción de carga incrementalmente?
- **Categoría:** Validación de enfoque · **Prioridad:** MEDIA
- **Contexto:** casi toda la literatura de Capa 1 que resuelve instancias grandes (Wen et al. 2016, P-07; Adler & Mirchandani 2017, P-09) **no** modela capacidad limitada de carga simultáneamente — es justamente la brecha que el enunciado pide cerrar y que solo de Vos et al. (2024) (P-12) cubre de forma exacta, a costo de una instancia pequeña.
- **Pregunta:** ¿Es aceptable como estrategia de desarrollo construir primero un E-VSP sin restricción de capacidad de carga (validando factibilidad de horario y energía), y agregar la restricción de capacidad de electroterminal como una segunda iteración del modelo, en vez de intentar la formulación completa desde el inicio?
- **Supuesto por defecto si no hay respuesta:** sí — desarrollo incremental: (1) E-VSP + energía sin capacidad de carga, (2) + capacidad de cargadores discretos, (3) opcionalmente + potencia agregada (ver Q07) si el tiempo lo permite.
- **Impacto de la respuesta:** afecta el cronograma del proyecto y qué versión del modelo se presenta como resultado mínimo viable vs. extensión.

---

## Supuestos que adoptaremos si no hay respuesta

Si el profesor no alcanza a responder antes de que el equipo deba avanzar, estos son los supuestos con los que continuamos (y que declararemos explícitamente en el informe):

1. **(Q01)** Construimos la tabla de viajes desde el GTFS crudo; `energy_kwh` = distancia × 1,4 kWh/km; *deadhead*/*pullout*/*pullin* por distancia Haversine con factor de circuidad, documentado como supuesto.
2. **(Q02)** Día laboral tipo (`service_id = L`), GTFS fijo, sin rediseño de rutas ni horarios.
3. **(Q03)** `data-alumnos` es un universo cerrado y autosuficiente; no se mezcla con cifras externas para restricciones del modelo.
4. **(Q04)** `fleet_size = 1200` es una cota superior, no una obligación de uso total.
5. **(Q05)** Formulación base sobre *time-space network* agregado (Kliewer et al. 2006).
6. **(Q06)** Ubicaciones y cantidad de electroterminales fijas (dato, no decisión).
7. **(Q07)** Se modela solo capacidad de cargadores discretos (dato real disponible); potencia agregada (MW) queda como trabajo futuro con valor supuesto y sensibilidad.
8. **(Q08)** Consumo lineal en distancia (1,4 kWh/km) y carga a potencia constante; se documenta la brecha con el valor real (1,006 kWh/km, Galarza 2020).
9. **(Q09)** *Battery swapping* fuera de alcance.
10. **(Q10)** *Crew scheduling* fuera de alcance.
11. **(Q11)** Baseline de comparación: heurística *greedy* propia + *gap* contra cota LP en instancias reducidas.
12. **(Q12)** Modelo determinístico + análisis de sensibilidad ex-post (sin *chance-constraints* ni robustez formal).
13. **(Q13)** Función objetivo única de costo total aditivo, con análisis de *trade-off* posterior (no multiobjetivo formal).
14. **(Q14)** Desarrollo en dos etapas: exacto en instancia reducida, luego metaheurística (ALNS extendida) para la instancia completa.
15. **(Q15)** Desarrollo incremental: E-VSP + energía primero, capacidad de carga como segunda iteración.
