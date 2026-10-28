# Bibliografía crítica — Planificación de operación de buses eléctricos (E-VSP), Red Metropolitana de Movilidad

> Metodología: cada referencia fue verificada abriendo su DOI/URL (Crossref, Semantic Scholar, página del editor o repositorio institucional) antes de fichar. Ninguna cita proviene de memoria. Las que no se pudieron verificar están en `## Por verificar` al final. Nomenclatura de OR en inglés (*deadhead*, *time-space network*, *column generation*, *SoC* = state of charge) con traducción la primera vez que aparece.

**Punto de partida de la búsqueda:** en vez de un solo review, se usaron **dos** reviews de anclaje para el *snowballing*, porque el más reciente encontrado (Wang et al. 2025) es más específico en scheduling/timetabling pero más nuevo, mientras que Perumal et al. (2022) es el review-marco del campo (259 citas) y el que EJOR indexa como referencia obligada. Backward snowballing se hizo sobre la lista completa de 55 referencias de Perumal et al. (2022) vía Semantic Scholar API; forward snowballing sobre sus ~95 citas más recientes (2025-2026).

---

## Capa 0 — Fundamentos del VSP clásico

### [P-01] Bunte & Kliewer (2009) — An overview on vehicle scheduling models
- **Capa:** 0 · **Prioridad de lectura:** ALTA
- **DOI/URL:** https://doi.org/10.1007/s12469-010-0018-5 (verificado vía Crossref y Springer Link)
- **Problema:** el Vehicle Scheduling Problem (VSP) clásico: asignar una flota de buses convencionales a un conjunto de viajes programados (timetabled trips), con múltiples depósitos y tipos de vehículo, minimizando flota y/o costo operacional. Sin restricciones de energía.
- **Formulación:** los autores clasifican los modelos en dos familias: **connection-based networks** (nodos = viajes, arcos = posibles encadenamientos factibles por tiempo/lugar) y **time-space networks** (nodos = eventos espacio-temporales, arcos = actividades; permite formulación de flujo de costo mínimo en redes). Señalan que Kliewer et al. fueron los primeros en aplicar el time-space network al VSP.
- **Método:** revisión metodológica, no propone algoritmo propio; compara enfoques exactos (flujo en redes, programación lineal entera) y las bases para column generation en problemas multi-depósito.
- **Supuestos clave:** (1) cada viaje se cubre exactamente una vez; (2) el bus retorna implícitamente a algún depósito; (3) no hay restricción de autonomía — el bus opera todo el día sin recarga; (4) el foco es factibilidad temporal/espacial, no energética.
- **Qué nos sirve:** es la base conceptual para decidir la representación de red de nuestro modelo (time-space vs. connection-based) antes de añadir la capa eléctrica. El enunciado exige exactamente la restricción de encadenamiento factible que aquí se formaliza.
- **Qué NO cubre:** nada de energía, batería ni carga — es la brecha exacta que llena la Capa 1.
- **Pregunta que gatilla:** → Q05 (representación de red: time-space vs. connection-based para la escala de la RM).

---

### [P-02] Kliewer, Mellouli & Suhl (2006) — A time-space network based exact optimization model for multi-depot bus scheduling
- **Capa:** 0 · **Prioridad de lectura:** ALTA
- **DOI/URL:** https://doi.org/10.1016/j.ejor.2005.02.030 (verificado vía Crossref) · EJOR 175(3):1616-1627
- **Problema:** Multi-Depot Vehicle Scheduling Problem (MDVSP) — versión con múltiples depósitos, que es NP-hard y mucho más difícil que el caso mono-depósito (polynomial).
- **Formulación:** modelo de flujo de costo mínimo sobre un **time-space network** agregado (agrega arcos entre eventos en la misma franja temporal para reducir el tamaño de la red), en lugar del connection-based network tradicional. Esto reduce drásticamente el número de arcos/variables sin perder la formulación exacta.
- **Método:** exacto — programación lineal entera con relajación LP + column generation / flujo en redes; resuelve instancias reales de tamaño práctico de una empresa de transporte alemana.
- **Supuestos clave:** (1) depósitos con capacidad; (2) sin restricción de energía; (3) el ahorro computacional viene de agregar arcos temporalmente equivalentes, lo que asume homogeneidad de tiempos de deadhead dentro de la franja agregada.
- **Qué nos sirve:** es la técnica que casi toda la literatura de E-VSP (Capa 1) extiende para incorporar el estado de carga (SoC) como una dimensión adicional del nodo/arco. Es candidato directo para nuestra formulación base si escalamos a miles de viajes.
- **Qué NO cubre:** energía, carga, ni capacidad de electroterminal.
- **Pregunta que gatilla:** → Q05.

---

### [P-03] Desaulniers & Hickman (2007) — Public Transit (cap. 2)
- **Capa:** 0 · **Prioridad de lectura:** MEDIA
- **DOI/URL:** https://doi.org/10.1016/S0927-0507(06)14002-5 (verificado vía Crossref) · en *Handbooks in Operations Research and Management Science*, Vol. 14 (Transportation), Elsevier, pp. 69-127
- **Problema:** capítulo de handbook, no un paper de investigación — revisión general de OR aplicada a transporte público: diseño de redes, timetabling, vehicle scheduling, crew scheduling, e integración vehicle-crew.
- **Formulación:** panorama de formulaciones estándar de la época (set-partitioning, network flow) para cada subproblema, sin foco en electromovilidad (2007, anterior a la masificación de buses eléctricos).
- **Método:** revisión narrativa con formulaciones ilustrativas; no reporta cómputo propio.
- **Supuestos clave:** trata vehicle scheduling y crew scheduling como problemas secuenciales/integrables pero no simultáneos por defecto; asume flota convencional.
- **Qué nos sirve:** contexto histórico y vocabulario estándar de la jerarquía de planificación (network design → timetabling → vehicle scheduling → crew scheduling), útil para ubicar dónde entra la decisión de carga en esa jerarquía.
- **Qué NO cubre:** todo lo eléctrico; es anterior al problema.
- **Pregunta que gatilla:** → Q11 (¿el proyecto asume vehicle scheduling desacoplado de crew scheduling?).

---

## Capa 1 — E-VSP: núcleo del problema

### [P-04] Perumal, Lusby & Larsen (2022) — Electric bus planning & scheduling: A review of related problems and methodologies
- **Capa:** 1 · **Prioridad de lectura:** CRÍTICA — leer primero
- **DOI/URL:** https://doi.org/10.1016/j.ejor.2021.10.058 (verificado vía Crossref) · EJOR 301(2):395-413 · 259 citas (Semantic Scholar, consultado 2026)
- **Problema:** review que sintetiza 43 artículos sobre planificación de buses eléctricos en tres niveles: estratégico (inversión en flota/infraestructura), táctico (ubicación de cargadores) y operacional (E-VSP y *charging scheduling*).
- **Formulación:** organiza el campo en 4 familias de problema: (1) fleet & infrastructure investment, (2) charging infrastructure location, (3) **E-VSP** — asignar buses a viajes programados satisfaciendo autonomía y necesidades de recarga, (4) charging scheduling — optimizar costo de carga según tarifa horaria y capacidad de estación.
- **Método:** revisión bibliométrica y metodológica; no propone algoritmo, pero mapea qué método (exacto/heurístico) se usó en cada subproblema de la literatura revisada.
- **Supuestos clave:** (1) trata E-VSP y charging scheduling como problemas frecuentemente resueltos por separado en la literatura (secuencial, no simultáneo) — brecha que el enunciado de nuestro proyecto exige cerrar; (2) identifica que la robustez/incertidumbre en scheduling eléctrico está subdesarrollada.
- **Qué nos sirve:** es el mapa de literatura completo — todas las semillas de Capas 1-3 de este documento provienen de su grafo de citas (backward y forward). Los autores señalan explícitamente robustez como vacío — confirma que Capa 3 debe incluir incertidumbre.
- **Qué NO cubre:** al ser de 2022, no cubre desarrollos posteriores (branch-and-price recientes, chance-constrained, ver Wang et al. 2025 abajo).
- **Pregunta que gatilla:** → Q12 (¿el equipo debe abordar incertidumbre o basta un enfoque determinístico con análisis de sensibilidad?).

---

### [P-05] Wang, Zhang, Liu, Gong, Lu, Wu, Gu, Li & Cao (2025) — A Review of Battery Electric Public Transport Timetabling and Scheduling: A 10 Year Retrospective and New Developments
- **Capa:** 1 · **Prioridad de lectura:** CRÍTICA — es el review más reciente encontrado, usado como segundo eje de snowballing
- **DOI/URL:** https://doi.org/10.3390/electronics14091694 (verificado vía Crossref) · Electronics 14(9):1694, publicado 2025-04-22
- **Problema:** review de una década (10 años) de investigación en BEV (Battery Electric Vehicle) timetabling y scheduling en transporte público, con foco específico en buses (no EVs particulares).
- **Formulación:** estructura la revisión en 3 ejes: (1) evolución de los modelos de electric vehicle timetabling con análisis comparativo metodológico, (2) desarrollos clave en electric vehicle scheduling, incluida la integración con crew scheduling, (3) integración BEV scheduling + timetabling.
- **Método:** revisión sistemática comparativa; identifica fortalezas/limitaciones de metodologías actuales y direcciones futuras.
- **Supuestos clave:** foco en degradación de batería y gestión del ciclo de vida como dimensión de optimización — algo que Perumal (2022) no cubría con el mismo detalle por ser 3 años más antiguo.
- **Qué nos sirve:** es el review post-Perumal que confirma qué preguntas siguen abiertas en 2025 (integración timetabling-scheduling, degradación de batería) — usarlo para justificar el estado del arte en la introducción del informe y para verificar que no nos falte literatura 2022-2025.
- **Qué NO cubre:** según el propio abstract, no es un review centrado en la restricción de **capacidad de infraestructura de carga** (número de cargadores/potencia) — ese eje se cubre mejor en Capa 2.
- **Pregunta que gatilla:** → Q12.

---

### [P-06] Pasha, Li, Elmi, Fathollahi-Fard, Lau, Roshani, Kawasaki & Dulebenets (2024) — Electric vehicle scheduling: State of the art, critical challenges, and future research opportunities
- **Capa:** 1 · **Prioridad de lectura:** MEDIA (complementario, alcance más amplio que buses)
- **DOI/URL:** https://doi.org/10.1016/j.jii.2024.100561 (verificado vía Crossref) · Journal of Industrial Information Integration, Vol. 38, art. 100561
- **Problema:** review de electric vehicle scheduling en sentido amplio (no exclusivamente buses urbanos); agrupa los estudios en 3 categorías: EVS general, EVS con consideraciones de red eléctrica (power grid), y EVS con consideraciones ambientales.
- **Formulación:** presenta modelos matemáticos representativos por categoría (no específico de un solo dominio de aplicación).
- **Método:** revisión sistemática con formulaciones ilustrativas.
- **Supuestos clave:** al cubrir EVs en general (no solo buses de transporte público), su nivel de detalle operacional (deadhead, terminales, electroterminales) es menor que en Perumal (2022) o Wang et al. (2025).
- **Qué nos sirve:** perspectiva de la interacción con la red eléctrica (power grid characteristics) — relevante para justificar por qué modelamos capacidad de potencia agregada del electroterminal, tal como pide el enunciado.
- **Qué NO cubre:** especificidad del contexto de transporte público urbano (terminales, recorridos, deadhead entre paraderos).
- **Pregunta que gatilla:** → Q07.

---

### [P-07] Wen, Linde, Ropke, Mirchandani & Larsen (2016) — An adaptive large neighborhood search heuristic for the Electric Vehicle Scheduling Problem
- **Capa:** 1 (también Capa 3 — método) · **Prioridad de lectura:** ALTA
- **DOI/URL:** https://doi.org/10.1016/j.cor.2016.06.013 (verificado vía Crossref) · Computers & Operations Research 76:73-83
- **Problema:** E-VSP con múltiples depósitos: viajes programados con horario fijo deben ser cubiertos por buses eléctricos con autonomía limitada; los vehículos pueden recargarse **total o parcialmente** en estaciones de recarga dadas.
- **Formulación:** no se limita a instancias pequeñas — el objetivo explícito del paper es resolver instancias grandes (el E-VSP es NP-hard).
- **Método:** heurístico — Adaptive Large Neighborhood Search (ALNS), metaheurística de destrucción/reparación adaptativa.
- **Supuestos clave:** (1) recarga parcial permitida (no solo full recharge); (2) estaciones de recarga con ubicación y disponibilidad dadas (no modela capacidad limitada de cargadores simultáneos, según el propio Perumal 2022 lo clasifica); (3) NP-hard → se resigna optimalidad garantizada a cambio de escalabilidad.
- **Qué nos sirve:** referencia metodológica directa si el equipo opta por metaheurística — mismo problema núcleo (E-VSP con recarga parcial) que el enunciado, pero **sin** capacidad limitada de cargadores, que es exactamente la extensión que nuestro proyecto debe agregar.
- **Qué NO cubre:** capacidad de infraestructura de carga (cargadores finitos, potencia agregada) — la restricción central del enunciado.
- **Pregunta que gatilla:** → Q07, Q13 (¿partir de ALNS extendido con capacidad de carga, o de un exacto en instancia reducida?).

---

### [P-08] van Kooten Niekerk, van den Akker & Hoogeveen (2017) — Scheduling electric vehicles
- **Capa:** 1 · **Prioridad de lectura:** ALTA
- **DOI/URL:** https://doi.org/10.1007/s12469-017-0164-0 (verificado vía Crossref y Springer Link) · Public Transport 9(1-2):155-176
- **Problema:** e-VSP mono-línea: viajes programados deben cubrirse con buses eléctricos de autonomía limitada, sin sustitución/intercambio de batería. Explícitamente comparan **modelo simplificado** (carga lineal, precio de electricidad constante, sin efecto de profundidad de descarga en vida útil de batería) contra **modelo detallado** (proceso de carga no lineal, tarifas reales por hora, costo de depreciación de batería por profundidad de descarga).
- **Formulación:** el modelo detallado discretiza el nivel de carga para mantener tratabilidad; se resuelve por programación lineal entera para instancias pequeñas/medianas.
- **Método:** exacto (ILP) para instancias pequeñas/medianas; para instancias grandes, dos métodos basados en **column generation** que dan buenas soluciones sin garantía de optimalidad. Probado en instancias reales.
- **Supuestos clave:** (1) sin intercambio de batería; (2) comparación explícita recarga lineal vs. no lineal — cita textual del abstract: *"we allow any type of charging process, work with the actual electricity prices, and take the depreciation cost of the battery into account"*; (3) no hay restricción de capacidad simultánea de cargadores (asumen disponibilidad).
- **Qué nos sirve:** es la referencia más directa para la pregunta "¿carga lineal o curva no lineal?" del enunciado — da ambos modelos y compara su costo-beneficio, con datos de tarifa horaria de electricidad análogos a los que trae `data-alumnos/electricity_prices.csv`.
- **Qué NO cubre:** capacidad limitada de cargadores/potencia agregada (el "recurso escaso" del enunciado) — no hay contención entre buses por el mismo cargador.
- **Pregunta que gatilla:** → Q08 (curva de carga: lineal vs. no lineal).

---

### [P-09] Adler & Mirchandani (2017) — The Vehicle Scheduling Problem for Fleets with Alternative-Fuel Vehicles
- **Capa:** 1 (también Capa 3 — método exacto) · **Prioridad de lectura:** ALTA
- **DOI/URL:** https://doi.org/10.1287/trsc.2015.0615 (verificado vía Crossref) · Transportation Science 51(2):441-456
- **Problema:** "alternative-fuel multiple depot vehicle scheduling problem" — generalización del MDVSP donde los vehículos solo pueden reabastecerse en un conjunto dado de estaciones de combustible/energía y tienen capacidad de tanque/batería limitada. Aplica a flotas de combustible alternativo en general (no solo eléctricas).
- **Formulación:** programa entero sobre la red MDVSP extendida con nodos de reabastecimiento y seguimiento de nivel de combustible/carga restante.
- **Método:** exacto — **branch-and-price**. Probado con datos reales del sistema de buses metropolitano de Phoenix, Arizona.
- **Supuestos clave:** (1) estaciones de reabastecimiento en ubicaciones fijas y capacidad de atención no limitante (no compiten los buses por la estación); (2) consumo determinístico por distancia recorrida.
- **Qué nos sirve:** referencia metodológica exacta (branch-and-price) para la variante de capacidad de tanque/batería — punto de comparación directo si el equipo elige un enfoque de column generation / branch-and-price para el modelo base sin capacidad de carga.
- **Qué NO cubre:** capacidad limitada de estaciones de recarga — asume disponibilidad no restringida en el punto de recarga, y no hay recarga parcial con curva de carga.
- **Pregunta que gatilla:** → Q13.

---

### [P-10] Li (2014) — Transit Bus Scheduling with Limited Energy
- **Capa:** 1 · **Prioridad de lectura:** ALTA
- **DOI/URL:** https://doi.org/10.1287/trsc.2013.0468 (verificado vía Crossref) · Transportation Science 48(4):521-539
- **Problema:** dos variantes de scheduling con energía limitada: (a) buses eléctricos con **battery swapping** o **fast charging** en una estación de batería, y (b) buses de gas natural comprimido/diésel/híbrido-diésel con restricción de distancia máxima de ruta.
- **Formulación:** modelo de vehicle scheduling con restricción de energía/distancia acoplada al nivel de combustible o carga restante; ambas variantes son NP-hard.
- **Método:** algoritmos basados en **column generation**; también explora simulated annealing (SA) para generar planes factibles rápido, priorizando velocidad de cómputo y salud de batería sobre optimalidad garantizada.
- **Supuestos clave:** (1) contempla battery swapping como alternativa a recarga in situ — opción que el enunciado de nuestro proyecto no menciona y probablemente no aplica al parque BYD K9 real de la RM; (2) restricción de distancia máxima por ruta, más simple que un balance energético continuo.
- **Qué nos sirve:** referencia de la familia "column generation + energía limitada"; útil para justificar el descarte de battery swapping como alcance (nuestros datos de vehículos no traen esa opción).
- **Qué NO cubre:** capacidad limitada de estación de carga/swapping — no hay contención por recurso compartido.
- **Pregunta que gatilla:** → Q09 (¿se descarta explícitamente battery swapping como fuera de alcance?).

---

## Capa 2 — Recarga como recurso escaso

### [P-11] He, Liu & Song (2020) — Optimal charging scheduling and management for a fast-charging battery electric bus system
- **Capa:** 2 · **Prioridad de lectura:** ALTA
- **DOI/URL:** https://doi.org/10.1016/j.tre.2020.102056 (verificado vía Crossref) · TR Part E: Logistics and Transportation Review, Vol. 142, art. 102056
- **Problema:** *on-route fast-charging* — buses eléctricos que se recargan a alta potencia durante los tiempos de espera (*layover*) en terminal, en vez de recarga nocturna lenta en depósito. Aborda cómo esto hace a un bus eléctrico "tan capaz como su equivalente diésel" en rango y horas de operación.
- **Formulación:** modelo de programación de la carga en terminal considerando la cola de buses que llegan a recargar y la potencia disponible.
- **Método:** optimización de la programación de carga con gestión de demanda pico (peak demand management).
- **Supuestos clave:** (1) recarga rápida en terminal de paso (no en electroterminal dedicado); (2) potencia de carga alta concentrada en ventanas cortas — exactamente el escenario de contención de recurso que describe el enunciado.
- **Qué nos sirve:** modela explícitamente la competencia por el recurso de carga en ventanas de tiempo cortas — aplicable directamente a la restricción de "capacidad eléctrica restringida" del electroterminal.
- **Qué NO cubre:** no resuelve el E-VSP completo (asignación de viajes), solo la sub-decisión de carga dado un patrón de llegada de buses.
- **Pregunta que gatilla:** → Q07.

---

### [P-12] de Vos, van Lieshout & Dollevoet (2024) — Electric Vehicle Scheduling in Public Transit with Capacitated Charging Stations
- **Capa:** 2 (también Capa 3 — método exacto) · **Prioridad de lectura:** CRÍTICA
- **DOI/URL:** https://doi.org/10.1287/trsc.2022.0253 (verificado vía Crossref) · Transportation Science 58(2):279-294
- **Problema:** E-VSP con **capacidad limitada de estaciones de carga** (número finito de puntos de carga simultáneos) y **recarga parcial** — la combinación exacta de restricciones que pide el enunciado del proyecto.
- **Formulación:** programa binario basado en rutas (*path-based binary program*) sobre una red que trackea SoC y ocupación de la estación de carga en el tiempo.
- **Método:** exacto — column generation con problema de pricing que genera rutas factibles respetando capacidad de estación.
- **Supuestos clave:** (1) capacidad de estación = número de puntos de carga simultáneos (no modela explícitamente límite de potencia agregada en kW/MW, solo cupos discretos); (2) recarga parcial permitida con relación tiempo-SoC dada.
- **Qué nos sirve:** es la referencia metodológica más cercana al problema exacto del enunciado — mismo objeto (cargadores finitos + recarga parcial), aunque no cubre la restricción de potencia agregada que el enunciado menciona como restricción adicional y distinta.
- **Qué NO cubre:** la restricción de potencia eléctrica agregada del electroterminal (kW/MW disponibles), que es una restricción distinta a "número de cargadores" según el propio enunciado.
- **Pregunta que gatilla:** → Q07 (cargadores discretos vs. potencia agregada — esta referencia resuelve solo la primera).

---

### [P-13] Jiang, Zhang & Zhang (2022) — Electric Bus Scheduling Considering Limited Charging Facility Capacity for Large-Scale Operation
- **Capa:** 2 · **Prioridad de lectura:** ALTA
- **DOI/URL:** https://doi.org/10.1061/jtepbs.0000706 (verificado vía Crossref) · Journal of Transportation Engineering, Part A: Systems 148(9):04022058
- **Problema:** E-VSP a **gran escala** con capacidad limitada de instalación de carga — foco explícito en escalabilidad (>500 viajes, según criterio de inclusión de este documento).
- **Formulación:** modelo de asignación con restricción de capacidad de instalación de carga como cuello de botella explícito.
- **Método:** enfoque orientado a instancias grandes (escalabilidad como objetivo de diseño del algoritmo).
- **Supuestos clave:** capacidad de instalación como restricción dura; foco en tratabilidad computacional a escala real.
- **Qué nos sirve:** referencia directa de escalabilidad — si el proyecto termina manejando miles de viajes (como sugiere el enunciado: "miles de viajes programados"), este es el punto de comparación de tamaño de instancia resuelto.
- **Qué NO cubre:** no fue posible verificar en este corte si distingue cargadores discretos de potencia agregada (requiere lectura completa del texto, no solo abstract/metadata).
- **Pregunta que gatilla:** → Q07.

---

### [P-14] Xylia, Leduc, Patrizio, Kraxner & Silveira (2017) — Locating charging infrastructure for electric buses in Stockholm
- **Capa:** 2 · **Prioridad de lectura:** MEDIA
- **DOI/URL:** https://doi.org/10.1016/j.trc.2017.03.005 (verificado vía Crossref) · TR Part C 78:183-200
- **Problema:** ubicación óptima de infraestructura de carga para buses eléctricos a nivel de red urbana (Estocolmo) — problema de **localización**, no de scheduling.
- **Formulación:** modelo de optimización de ubicación que identifica los hubs de transporte público (conexión con tren/metro) como los puntos preferentes para instalar cargadores.
- **Método:** optimización de localización (no vehicle scheduling).
- **Supuestos clave:** ubicaciones de electroterminal como variable de decisión (no dato fijo) — a diferencia de nuestro proyecto, donde `data-alumnos/depots.csv` da las ubicaciones como dato fijo.
- **Qué nos sirve:** contexto para justificar que nuestro proyecto trata la ubicación de electroterminales como dato (no decisión) — a diferencia de esta referencia. Cumple el criterio de inclusión por ser ampliamente citado en Perumal (2022), aunque es *charging station location* puro.
- **Qué NO cubre:** no resuelve scheduling ni capacidad eléctrica; es un problema de nivel táctico/estratégico, no operacional.
- **Pregunta que gatilla:** → Q06 (¿las ubicaciones de electroterminales son dato fijo o parte de la decisión?) — la respuesta ya está en `data-alumnos/depots.csv` (dato fijo), pero se incluye por si el equipo quiere evaluar sensibilidad a la ubicación.

---

### [P-15] Häll, Ceder, Ekström & Quttineh (2018) — Adjustments of public transit operations planning process for the use of electric buses
- **Capa:** 2 · **Prioridad de lectura:** ALTA
- **DOI/URL:** https://doi.org/10.1080/15472450.2018.1488131 (verificado vía Crossref) · Journal of Intelligent Transportation Systems 23(3):216-230
- **Problema:** cómo la introducción de buses eléctricos obliga a modificar el **proceso completo de planificación** de transporte público (no solo el scheduling): diseño de red de rutas, timetabling y vehicle scheduling deben ajustarse conjuntamente.
- **Formulación:** análisis conceptual + estudio de caso mostrando qué etapas de la jerarquía de planificación (ver Desaulniers & Hickman 2007) requieren rediseño.
- **Método:** estudio de caso aplicado, no propone un algoritmo de optimización nuevo.
- **Supuestos clave:** (1) el diseño de rutas y horarios no puede tratarse como fijo e independiente de la electrificación — contradice el supuesto usual de tratar el GTFS como dato inmutable; (2) trade-off explícito entre rigidez del timetable y factibilidad energética.
- **Qué nos sirve:** justifica por qué, aunque el enunciado y `data-alumnos/gtfs` dan los viajes programados como dato fijo, es válido declarar esto como un supuesto explícito de alcance (no rediseñamos rutas ni horarios) en vez de ignorarlo silenciosamente.
- **Qué NO cubre:** no da una formulación matemática reutilizable directamente.
- **Pregunta que gatilla:** → Q02 (¿los horarios/recorridos del GTFS son fijos e innegociables, o el equipo puede proponer ajustes menores de timetable?).

---

## Capa 3 — Métodos de solución

### [P-16] Wu, Lin & Li (2025) — Optimal battery-electric bus scheduling with waiting times cost: A branch-and-price approach
- **Capa:** 3 (método exacto) · **Prioridad de lectura:** ALTA
- **DOI/URL:** https://doi.org/10.1016/j.cie.2025.111209 (verificado vía Crossref) · Computers & Industrial Engineering, Vol. 206, art. 111209
- **Problema:** E-VSP con costo de tiempos de espera (*waiting time cost*) y tiempos de recarga variables — variante que penaliza explícitamente el tiempo ocioso del bus, no solo el costo de deadhead y energía.
- **Formulación:** programa lineal entero mixto (MILP), descompuesto en problema maestro + problema de *pricing*.
- **Método:** exacto — branch-and-price. Los autores reportan que su enfoque resuelve a optimalidad instancias de hasta 101 viajes, superando al mejor exacto previo (que llegaba a 91 viajes).
- **Supuestos clave:** (1) el tiempo de recarga es variable (no fijo), lo que agrega una dimensión de decisión adicional; (2) el tamaño de instancia resuelto (101 viajes) es pequeño frente a la escala de "miles de viajes" del enunciado — brecha de escalabilidad relevante.
- **Qué nos sirve:** benchmark de lo que un enfoque exacto puede resolver hoy (2025) en tiempo razonable — útil para argumentar por qué a escala RM se necesita heurística/descomposición, no solo el exacto.
- **Qué NO cubre:** capacidad limitada de electroterminal (cargadores/potencia) — no es su foco.
- **Pregunta que gatilla:** → Q13 (¿el equipo debe reportar tanto un exacto en instancia reducida como una heurística escalable, o basta una de las dos rutas?).

---

### [P-17] Legault, Cabral & Sun (2025) — Integrated Bus Fleet Electrification Planning Through Accelerated Logic-Based Benders Decomposition and Restriction Heuristics
- **Capa:** 3 (método de descomposición) · **Prioridad de lectura:** MEDIA-ALTA — **preprint, no revisión por pares**
- **DOI/URL:** https://arxiv.org/abs/2508.05863 (verificado — arXiv, versión v3 de 2026-07-27; también en Optimization Online) — **es un working paper, se cita como tal** por regla anti-alucinación §5.1.3
- **Problema:** planificación integrada multi-período: inversión anual en flota + infraestructura de carga, y operación horaria de vehicle scheduling + charging, simultáneamente (no en dos etapas separadas).
- **Formulación:** programa entero de dos etapas (inversión estratégica + operación).
- **Método:** exacto — **Logic-based Benders decomposition** acelerada con preprocesamiento, descomposición parcial y varios tipos de cortes de Benders; reporta *speedups* de hasta 3 órdenes de magnitud. Complementa con una heurística de restricción (*restriction heuristic*) con gap de optimalidad <1% para instancias grandes. Probado con datos de tránsito de Chicago.
- **Supuestos clave:** integra decisión de inversión (cuántos buses/cargadores) con la operación diaria — nuestro proyecto probablemente NO incluye la decisión de inversión (la flota de 1200 buses ya viene dada en `parameters.csv`), por lo que esta referencia es un techo metodológico más que un punto de partida directo.
- **Qué nos sirve:** técnica de descomposición (Benders lógico) aplicable si el equipo decide separar la decisión "cuántos buses asignar a cada depósito" de "cómo secuenciar sus viajes" como dos niveles del mismo problema.
- **Qué NO cubre:** al ser preprint, sin garantía de revisión por pares; no aplica directamente porque asume flota variable, mientras nuestro enunciado da flota fija.
- **Pregunta que gatilla:** → Q04 (¿la flota de 1200 buses es un dato fijo o el equipo puede proponer un tamaño de flota distinto como resultado?).

---

### [P-18] Ricard, Desaulniers, Lodi & Rousseau (2026) — Chance-constrained battery management for electric bus scheduling
- **Capa:** 3 (robustez/incertidumbre) · **Prioridad de lectura:** ALTA — responde directamente al vacío señalado por Perumal et al. (2022)
- **DOI/URL:** https://doi.org/10.1016/j.ejor.2026.05.046 (verificado vía Crossref) · European Journal of Operational Research (en prensa/2026) — versión preprint previa en arXiv:2503.19853, verificada también
- **Problema:** E-VSP bajo **incertidumbre** en consumo energético y degradación de batería — exactamente el vacío que Perumal, Lusby & Larsen (2022) identifican como subdesarrollado.
- **Formulación:** modelo *chance-constrained*: las restricciones de SoC se cumplen con una probabilidad mínima dada (no determinísticamente), permitiendo un margen de riesgo controlado en vez de un peor-caso rígido.
- **Método:** heurística de branch-and-price adaptada a *pricing* estocástico.
- **Supuestos clave:** (1) el consumo energético y la degradación de batería son variables aleatorias con distribución conocida/estimable; (2) se define un nivel de servicio (probabilidad de cumplimiento) en vez de una cota determinística fija de SoC mínimo.
- **Qué nos sirve:** es la referencia más directa para justificar (o descartar con fundamento) si el proyecto debe tratar el consumo energético como determinístico o estocástico — probablemente la pregunta que el profesor haga en la defensa, según predice el propio AGENT.md.
- **Qué NO cubre:** no aborda capacidad limitada de infraestructura de carga (cargadores/potencia) simultáneamente con la incertidumbre.
- **Pregunta que gatilla:** → Q12.

---

## Capa 4 — Contexto chileno / Santiago

### [P-19] Ministerio de Energía de Chile — Plataforma de Electromovilidad: Buses eléctricos de RED Metropolitana de Movilidad
- **Capa:** 4 · **Prioridad de lectura:** MEDIA — fuente oficial, pero con cifras desactualizadas (ver "Qué NO cubre")
- **URL:** https://energia.gob.cl/electromovilidad/transporte-de-pasajeros/buses-electricos-red (verificado, fetch directo del sitio del Ministerio de Energía)
- **Qué reporta:** despliegue inicial de 200 buses eléctricos; a la fecha de la publicación de la página, más de 650 unidades (~10% de la flota RED); flota BYD K9 (operador METBUS, 100 unidades) y Yutong E12 (operadores Vule y STP, 100 unidades); cargadores BYD de 50 kW AC y cargadores Yutong de 150 kW DC; disponibilidad de flota reportada sobre 97%; ahorro de mantención ~70% vs. diésel Euro VI.
- **Qué nos sirve:** fuente oficial (gobierno de Chile) para justificar órdenes de magnitud de potencia de carga real (50-150 kW), que se puede contrastar con `data-alumnos/vehicles.csv` (charge_power_kw = 180, no coincide exactamente con ninguna de las dos cifras oficiales encontradas).
- **Qué NO cubre / brecha detectada:** las cifras de esta página corresponden al despliegue temprano (~2020, ~650 buses); la flota actual real de RED es de miles de buses eléctricos (ver P-20 y P-21, ~2500-3500 unidades reportadas en prensa 2025). **La página no entrega el detalle de flota/infraestructura actual (2026) en formato descargable** — es contenido narrativo, no un dataset.
- **Pregunta que gatilla:** → Q03 (¿los 1200 buses y las capacidades de `data-alumnos` son un recorte deliberado del problema real, o deben tratarse como si fueran la totalidad de la RM?).

---

### [P-20] Galarza (2020) — From pilots to scale: Lessons from electric bus deployments in Santiago de Chile (ZEBRA / CMM Chile, en conjunto con IEA Global EV Outlook 2020)
- **Capa:** 4 · **Prioridad de lectura:** ALTA — la fuente más rica en parámetros reales verificables
- **URL:** https://iea.blob.core.windows.net/assets/db408b53-276c-47d6-8b05-52e53b1208e1/e-bus-case-study-Santiago-From-pilots-to-scale-Zebra-paper.pdf (verificado, PDF leído completo) · Autor: Sebastián Galarza (CMM Chile), partnership ZEBRA (ICCT + C40 Cities), publicado junto al IEA Global EV Outlook 2020
- **Qué reporta (todo con fuente primaria citada en el reporte):** RED/Transantiago en 2018 tenía 6.756 buses, 380 rutas, 690.954 pasajeros de capacidad, 2.946 km de red (Tabla 2 del reporte). Piloto Metbus-Enel-BYD (2017): 2 buses BYD K9FE, consumo real de **1,006 kWh/km**, costo operacional **US$0,10/kWh** (idéntico al período P1 de `data-alumnos/electricity_prices.csv`), disponibilidad 99,23%. Escalamiento a 100 buses BYD: cargadores BYD EVA 080KI AC de 80 kW, tiempo de carga 3-4 h, costo por electroterminal de upgrade de red ~US$3 millones. Piloto Engie-Gildemeister-Vule/STP: buses Yutong E12, terminal STP con 13 cargadores DC de 150 kW para 25 buses, terminal Vule Rinconada con 37 cargadores DC de 150 kW para 75 buses, demanda total de potencia de terminal de 6 MW + respaldo de 2,1 MW.
- **Qué nos sirve:** es la única fuente de este documento con cifras **operacionales reales y verificadas** de consumo energético (kWh/km), potencia de carga (kW) y capacidad de electroterminal (MW, N° de cargadores por N° de buses) para el caso de Santiago — permite contrastar directamente los valores sintéticos de `data-alumnos` (charge_power_kw=180, capacity=150-180) contra la realidad documentada (80-150 kW por cargador, ratios de ~2 buses por cargador en los pilotos).
- **Qué NO cubre:** es un reporte técnico de 2020 (no revisado por pares), describe pilotos de 2017-2020 con flotas de 100-285 buses, no la escala actual (miles de buses). No incluye modelo de optimización ni de scheduling.
- **Pregunta que gatilla:** → Q03, Q08 (¿usamos los parámetros de `data-alumnos` tal cual, aunque no coincidan con los valores reales documentados, o los ajustamos a estos rangos reales como validación de realismo?).

---

### [P-21] Basso, Feijoo, Pezoa, Varas & Vidal (2024) — The impact of electromobility in public transport: An estimation of energy consumption using disaggregated data in Santiago, Chile
- **Capa:** 4 · **Prioridad de lectura:** ALTA — único paper revisado por pares con datos desagregados reales de la RED
- **DOI/URL:** https://doi.org/10.1016/j.energy.2023.129550 (verificado vía Crossref) · Energy 286:129550
- **Problema:** estimación de consumo energético bus-por-bus usando datos desagregados reales de operación de RED Metropolitana (no agregados por ruta) — cuantifica el ahorro de reemplazar buses diésel por eléctricos.
- **Formulación/Método:** modelo de estimación de consumo a nivel de viaje individual, considerando ocupación de pasajeros y modo de conducción del conductor (no solo distancia).
- **Supuestos clave:** (1) el consumo energético depende de variables operacionales finas (conductor, ocupación), no solo de distancia recorrida — más rico que el supuesto lineal simple de `energy_kwh` en `data-alumnos/parametros_descripcion.csv`; (2) autores reportan ahorro de 400.000 kWh/día al reemplazar 1.000 buses diésel por eléctricos.
- **Qué nos sirve:** valida (o cuestiona) el supuesto de consumo lineal en distancia que probablemente usa el dataset sintético del curso; es la referencia académica con datos reales de RED más citable de todo este documento.
- **Qué NO cubre:** no resuelve scheduling ni capacidad de carga, es un modelo de estimación de consumo, no de asignación de viajes.
- **Pregunta que gatilla:** → Q08 (¿se acepta el supuesto de consumo lineal en distancia de `data-alumnos`, o el equipo debe justificar/probar una relación más rica?).

---

### [P-22] Oemick Jerez (2019) — Evaluación económica y social de la incorporación de buses eléctricos al transporte público urbano de Santiago (tesis, Magíster en Gestión y Dirección de Empresas, U. de Chile)
- **Capa:** 4 · **Prioridad de lectura:** MEDIA
- **URL:** https://repositorio.uchile.cl/handle/2250/171777 (verificado, repositorio institucional U. de Chile, acceso abierto)
- **Qué reporta:** evaluación de 3 escenarios (25%/50%/75% de flota eléctrica a 2030); costos de combustible caen 55% acumulado; ahorro máximo de 641.000 millones CLP en escenario 75%.
- **Qué nos sirve:** referencia de orden de magnitud para justificar costos operacionales (`cost_per_km` en `parameters.csv`) desde una perspectiva económica agregada, aunque a nivel de flota, no de scheduling.
- **Qué NO cubre:** no modela scheduling, deadhead ni capacidad de carga; es evaluación económica agregada, no operativa.
- **Pregunta que gatilla:** → Q10 (¿el análisis económico agregado sirve como validación de plausibilidad de los costos del proyecto, o se descarta por incompatibilidad de escala/método?).

---

### [P-23] Zapata Barrientos (2022) — Impacto de electrificación de buses del transporte público de Santiago sobre el sistema eléctrico nacional (memoria de título, Ing. Civil Eléctrico, U. de Chile)
- **Capa:** 4 · **Prioridad de lectura:** ALTA — cifras de potencia agregada directamente relevantes a la restricción del enunciado
- **URL:** https://repositorio.uchile.cl/handle/2250/184624 (verificado, repositorio institucional U. de Chile, acceso abierto)
- **Problema:** impacto de electrificar la flota completa de buses de Santiago sobre el sistema eléctrico nacional — no scheduling, pero sí dimensiona la restricción de potencia agregada del enunciado a escala de sistema.
- **Formulación/Método:** (1) modelo de gestión de carga que optimiza horarios de recarga para minimizar costo energético; (2) simulación de despacho hidrotérmico 2021-2030 para impacto sistémico.
- **Supuestos clave y hallazgos:** electrificar la flota completa requeriría **>130 MW** de potencia y **~1,59 GWh/día** de consumo (0,63% de la demanda punta 2020); ~80% de la demanda de los buses eléctricos sería abastecida por generación a gas y carbón; hasta 97% de la flota podría electrificarse.
- **Qué nos sirve:** da una cota real de magnitud de potencia agregada a nivel de sistema — útil para poner en perspectiva si la restricción de "capacidad eléctrica restringida" del enunciado debe modelarse a nivel de electroterminal individual (como sugiere el enunciado) o si existe también una cota a nivel de sistema completo que el proyecto podría ignorar razonablemente.
- **Qué NO cubre:** no resuelve el E-VSP; su modelo de gestión de carga es agregado a nivel de sistema eléctrico, no de vehicle scheduling por bus.
- **Pregunta que gatilla:** → Q07.

---

### Disponibilidad de datos — Capa 4 (resumen obligatorio)

| Fuente | ¿Descargable? | Formato | Cobertura verificada | Evidencia |
|---|---|---|---|---|
| **GTFS Red Metropolitana de Movilidad** | **Sí**, público, sin autenticación | `.zip` con archivos `.txt` estándar GTFS (agency, calendar, routes, trips, stop_times, shapes, frequencies, pathways, levels) | Feed vigente verificado en `dtpm.cl/index.php/noticias/gtfs-vigente`: URLs con fecha de vigencia (ej. `GTFS_20260418.zip`). El archivo entregado en `data-alumnos/gtfs/` (`feed_version V166.20260704`) **es una copia de este mismo feed público**, confirmado por coincidencia exacta de fechas y estructura. | Abierto directamente; sin página de términos de licencia explícita encontrada (la página de "GTFS vigente" no declara licencia — **brecha, ver Q14**). |
| **Datos de flota, depósitos, tarifas eléctricas y capacidad de carga** (`vehicles.csv`, `depots.csv`, `charger_capacity.csv`, `electricity_prices.csv`, `parameters.csv`) | No verificado como público — **parecen construidos para el curso** | CSV simples con valores redondos (potencias, capacidades) | Ningún valor de estos archivos coincide exactamente con cifras oficiales encontradas (Ministerio de Energía: 50-150 kW real vs. 180 kW en `vehicles.csv`; tampoco se encontró fuente pública para `fleet_size=1200`, ni para los 5 depósitos con sus capacidades exactas). | **No se abrió ninguna fuente pública que confirme estos valores** — se marcan `[SIN FUENTE — dato de curso, no público]`. |
| **Ministerio de Energía — Estrategia Nacional de Electromovilidad / plataforma de electromovilidad** | Sí, la página web es pública | HTML narrativo, **no dataset descargable** | Cifras agregadas de flota (~650 buses ~2020) y tipo de cargador, sin granularidad por electroterminal ni serie temporal descargable. | Verificado por fetch directo. |
| **Reporte ZEBRA/CMM Chile/IEA (Galarza 2020)** | Sí, PDF público | PDF narrativo con tablas, **no dataset estructurado** | Cifras operacionales reales de pilotos 2017-2020 (consumo kWh/km, kW por cargador, MW por terminal) citadas con fuente primaria en notas al pie del propio reporte. | Verificado, PDF leído completo. |
| **Basso et al. (2024), *Energy*** | Parcialmente — el **paper** es de acceso restringido (ScienceDirect, no verificado acceso abierto); los **datos desagregados de RED** que usan no se confirmó que sean públicos | Artículo científico, no dataset | Metodología y resultados agregados públicos vía abstract/resumen; no se verificó si el dataset desagregado subyacente es descargable. | **Brecha: no se pudo verificar si los datos desagregados de RED usados por los autores están disponibles para terceros — pregunta directa a hacer, no supuesto.** |
| **Tesis U. de Chile (Oemick 2019, Zapata 2022)** | Sí, texto completo público | PDF, repositorio institucional (Tesis/Memoria) | Texto completo con metodología, supuestos numéricos y fuentes citadas dentro de cada tesis. | Verificado, páginas de repositorio abiertas. |

**Conclusión de disponibilidad:** el **GTFS de la RED es el único insumo de este proyecto que es simultáneamente público, verificado y ya empaquetado en `data-alumnos/`**. Todo lo demás (flota, depósitos, tarifas, capacidad de carga) parece construido específicamente para el curso, sin fuente pública verificada que lo respalde — lo cual es razonable pedagógicamente, pero **no debe presentarse en el informe final como si fueran datos oficiales de DTPM/Ministerio de Energía sin aclararlo**.

---

## Por verificar

*(vacío — las 23 referencias de este documento fueron verificadas abriendo su DOI/URL antes de fichar. Dos de ellas, P-17 y (parcialmente) P-18, son preprints/en prensa y están declaradas como tales en su ficha, no como versión final revisada por pares.)*

---

## Ranking de prioridad de lectura (23 referencias)

| Orden | Ficha | Por qué en este orden |
|---|---|---|
| 1 | P-04 Perumal et al. (2022) | Mapa completo del campo; de aquí sale todo el snowballing |
| 2 | P-05 Wang et al. (2025) | Review más reciente encontrado; confirma vacíos vigentes a 2025 |
| 3 | P-12 de Vos, van Lieshout & Dollevoet (2024) | Formulación exacta más cercana al problema del enunciado (cargadores finitos + recarga parcial) |
| 4 | P-08 van Kooten Niekerk et al. (2017) | Resuelve la pregunta de carga lineal/no lineal con datos reales |
| 5 | P-07 Wen et al. (2016) | Método heurístico de referencia (ALNS), mismo problema núcleo |
| 6 | P-18 Ricard et al. (2026) | Cierra el vacío de robustez/incertidumbre que Perumal (2022) señala |
| 7 | P-15 Häll et al. (2018) | Advierte que la jerarquía de planificación completa puede verse afectada |
| 8 | P-20 Galarza (2020) — ZEBRA/IEA | Única fuente con parámetros reales de Santiago (kWh/km, kW, MW) para contrastar con `data-alumnos` |
| 9 | P-01 Bunte & Kliewer (2009) | Vocabulario y taxonomía de red antes de formular |
| 10 | P-02 Kliewer, Mellouli & Suhl (2006) | Técnica de time-space network agregado, base para escalar |
| 11 | P-11 He, Liu & Song (2020) | Contención real por recurso de carga en ventanas cortas |
| 12 | P-09 Adler & Mirchandani (2017) | Método exacto (branch-and-price) de referencia |
| 13 | P-16 Wu, Lin & Li (2025) | Benchmark de tamaño de instancia resoluble a optimalidad hoy |
| 14 | P-21 Basso et al. (2024) | Único paper revisado por pares con datos reales de consumo desagregado de RED |
| 15 | P-23 Zapata (2022) | Cota real de potencia agregada a nivel de sistema |
| 16 | P-10 Li (2014) | Alternativa de battery swapping a descartar/justificar |
| 17 | P-13 Jiang, Zhang & Zhang (2022) | Escalabilidad a instancias grandes |
| 18 | P-06 Pasha et al. (2024) | Complementario, perspectiva de red eléctrica |
| 19 | P-14 Xylia et al. (2017) | Contexto de localización (fuera del foco de scheduling) |
| 20 | P-19 Ministerio de Energía | Fuente oficial pero desactualizada; lectura de contexto |
| 21 | P-22 Oemick (2019) | Evaluación económica agregada, lectura de contexto |
| 22 | P-17 Legault, Cabral & Sun (2025) | Preprint; techo metodológico si se decide modelar inversión de flota |
| 23 | P-03 Desaulniers & Hickman (2007) | Contexto histórico, lectura opcional |
