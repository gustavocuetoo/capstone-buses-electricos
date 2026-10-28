# Plan de trabajo · Entrega 3 (final)

Grupo 29 · ICS2122 · Planificación de la operación de buses eléctricos en la RM
Armado el 27-oct-2026 a partir de `00-enunciado/Lineamientos Entrega 3 2026-2.docx` y del estado del proyecto a esa fecha.

> **Fechas por confirmar.** Los lineamientos no las traen. Este plan supone la **presentación el jueves 19-nov** (mismo día de la semana que la del 8-oct) y el **informe el viernes 27-nov** (último día de clases UC; las evaluaciones finales van del 30-nov al 16-dic). La sección 10 dice qué mover si son otras.

## Resumen

- El informe final vale 200 puntos, tiene 45 páginas como máximo y es reprobatorio. La presentación vale 60 puntos y dura 15 minutos estrictos.
- Ya existe una solución factible y auditada para la red completa en día laboral: **7.427 buses y USD 2.638.494 al día**. No entró al informe 2.
- **Actualización 27-oct (noche):** sábado, domingo y el caso base en la red completa ya están corridos y auditados (sección 2). En la semana, el híbrido cuesta 13,8 % menos que el caso base.
- Para decir «problema resuelto» faltan cuatro cosas: evidencia de optimalidad, repetibilidad energética, sensibilidad con incertidumbre, e implementación con piloto.
- Esta semana se cierran las decisiones de modelación con el ayudante.
- Las cifras se congelan el **domingo 15-nov**. Desde ahí solo se escribe, se ensaya y se revisa.

## 1. Qué pide la Entrega 3

| | Entrega 2 | Entrega 3 |
|---|---|---|
| Informe | 135 pts · 30 págs | **200 pts · 45 págs** sin portada, anexos ni bibliografía. LaTeX, Times New Roman 11, índice, documento base del curso sin modificar |
| Presentación | 10 min | **15 min + 5 de preguntas**, 60 pts. Pasados 15:00 hay descuento; a los 16:00 la interrumpen |
| Expositores | máx. 3 | máx. 3, y **todos los integrantes deben haber presentado en alguna de las tres entregas** |
| Código | repositorio | GitHub (enlace en el informe) o .zip; autocontenido, ordenado y con instrucciones de uso |
| Además | — | abstract en inglés, resumen ejecutivo, declaración de IA firmada por los 7, evaluación de pares (a quien no la responde se le multiplica la nota por 0,75) |

Contenido nuevo respecto de la Entrega 2:
- decir si la solución es **óptima o aproximada, con evidencia computacional**;
- un análisis a posteriori: qué pasa si los supuestos no se cumplen y **cómo se comporta la solución con incertidumbre**;
- un **análisis crítico** propio: limitaciones y qué se pudo hacer mejor;
- una **propuesta de implementación**, por etapas o con un piloto controlado, y cómo se evaluaría el éxito del piloto antes de un despliegue total.

**Rúbrica del informe (200 pts):**
- abstract 5 · resumen e introducción 5 · problema 15;
- **modelo, estrategia y metodología 60:** datos 5, bibliografía 5, modelo 10, estrategia 15, supuestos 5, KPIs 5, caso base 10, implementación 5;
- **resultados 50:** presentación 15, análisis 15, relación con los objetivos 10, conclusiones interpretativas 10;
- **sensibilidad y extensiones 40:** justificación de parámetros 5, evaluación 20, implicancias 10, extensiones 5;
- conclusiones 25.

Hay descuentos por correcciones no hechas de informes anteriores, falta de coherencia, citas y bibliografía, y lenguaje y formato.

**Rúbrica de la presentación (60 pts):** problema 10 · datos 5 · KPIs 4 · caso base 5 · metodología 8 · implementación 5 · **resultados 18** · cierre 5. Hay descuentos por comentarios del ciclo 2 no atendidos, figuras sin leyenda o con errores, estructura, dinámica y manejo del tiempo.

## 2. Dónde estamos (27-oct)

**Hecho y auditado:**
- **Red completa, día laboral** (corrida del 6-oct): las 64.502 corridas de las 417 rutas con 7.427 buses y USD 2.638.494,33 al día, en 21,4 min. Pasó el auditor original y uno independiente (`metodo_hibrido/revision_factibilidad_20261006/`).
- **Cota básica de la red completa:** 6.601 buses simultáneos a las 08:00, más los km de servicio, dan USD 2.322.956. El óptimo está entre esa cota y la solución, con una separación de 11,96 %.
- **Muestra de 212 rutas** (informe 2): el refinado (3.873 buses, USD 1.374.632) ahorra 14,2 % frente al caso base miope (4.509 buses, USD 1.601.775), o 12,4 % con el ajuste por energía final.
- **Infraestructura de trabajo:** barrido de presupuesto (15 corridas), cifras generadas por script (`08-entrega2/informe2/compilar.sh`), pruebas automáticas y el repositorio privado `nfariasl/capstone-grupo29`.
- **Sábado, domingo y caso base en la red completa** (27-oct), con los mismos parámetros que el día laboral:
  - los tres planes del híbrido pasaron los tres auditores: el del híbrido, la validación cruzada contra los datos originales y el independiente desde el GTFS, que rechazó 10 de 10 corrupciones;
  - el caso base pasó dos auditores: el de tres fases y el del híbrido.

  | Día | Corridas | Híbrido | Caso base | Diferencia |
  |---|---|---|---|---|
  | Laboral | 64.502 | 7.427 buses · USD 2.638.494 | 8.684 buses · USD 3.062.717 | −14,5 % buses · −13,9 % costo |
  | Sábado | 43.619 | 4.692 buses · USD 1.739.778 | 5.492 buses · USD 2.040.216 | −14,6 % buses · −14,7 % costo |
  | Domingo | 37.377 | 4.201 buses · USD 1.540.099 | 4.669 buses · USD 1.765.184 | −10,0 % buses · −12,8 % costo |

  En la semana (5 días laborales, sábado y domingo), el híbrido cuesta USD 16,47 millones contra 19,12 millones del caso base (−13,8 %). La flota necesaria es la del día laboral: 7.427 buses.
  - Resultados: `metodo_hibrido/resultados/completa_417_{S,D}_20261027/` y `CODIGO apstone/output/tres_fases/red_417_{L,S,D}_caso_base/`.

**Lo que falta para decir «problema resuelto»:**
1. **Sábado y domingo:** hecho el 27-oct (arriba).
2. **Caso base en la red completa:** hecho el 27-oct (arriba).
3. **Calidad de la solución:** las separaciones son contra una cota débil, y no hay validación exacta en instancias chicas ni réplicas en la red completa. Contra la cota básica, la separación crece en fin de semana: 12,0 % el día laboral, 18,0 % el sábado y 27,1 % el domingo (cotas por simultaneidad de 6.601, 3.860 y 2.900 buses).
4. **Repetibilidad energética.** Los buses parten llenos y durante el día solo se compra el 3,0 % de la energía que consumen (64.534 de 2.136.272 kWh). Los buses terminan con 71 kWh en promedio. Reponer lo que falta (2,07 GWh) tomaría 16,4 h usando a la vez las 700 conexiones a 180 kW. Además, 6.727 de los 7.427 buses terminan el día en terminales sin cargadores; los otros 700 ocupan todas las plazas de los electroterminales. Todo esto está verificado en `04_final/jornadas.csv`. Sábado y domingo tampoco se repiten: reponer su energía tomaría 10,8 h y 9,3 h. El equipo docente lo preguntó el 8-oct: «¿cómo se cubre el día siguiente?».
5. **Sensibilidad:** vale 40 pts, y solo hay presupuesto de búsqueda, umbral del caso base y costo de espera.
6. **Incertidumbre, implementación y piloto:** no hay nada hecho.
7. **Datos del enunciado sin usar:**
   - el costo de espera (0,03 USD/min) no se cobra;
   - `transformer_mw` aparece en el diccionario de datos, pero no viene en ningún archivo. El límite eléctrico se modeló como conexiones × 180 kW, y la punta programada en El Conquistador llega a 7,1 MW.
8. **Pendientes de forma:**
   - agregar al ayudante y al profesor como colaboradores del repositorio;
   - el anexo de correcciones;
   - un solo término por concepto («ruta» o «recorrido», «terminal de espera» o «terminal común»);
   - revisar si la versión entregada en Overleaf quedó sin sección de KPIs en el capítulo 2.

**Comentarios que hay que atender (descuentan si no):**
- la corrección anotada del informe 1 (13 comentarios);
- el feedback de la presentación del 8-oct;
- la corrección del informe 2, cuando llegue;
- la retroalimentación que otro grupo le hizo al G29. No está en el computador ni en el correo: `~/Downloads/Feedback Proyectos Capstone_G28.docx` es la que el G29 le dio al G28.

## 3. Cuándo está resuelto

La entrega está lista cuando se cumplen estas siete condiciones:
1. Hay un plan factible y auditado para día laboral, sábado y domingo en la red completa, cada uno con su caso base auditado.
2. Cada plan tiene su brecha contra una cota inferior válida, y una validación exacta en instancias chicas mide cuánto se aleja la heurística del óptimo.
3. La variabilidad de la heurística está medida con réplicas.
4. La sensibilidad cubre los supuestos que más pesan y compara el modelo con el caso base en cada escenario.
5. La repetibilidad energética está cuantificada y hay una recomendación de infraestructura.
6. Hay una propuesta de implementación con piloto y criterios de éxito medibles.
7. Cada cifra del informe y del deck sale de un script que lee resultados auditados.

## 4. Decisiones de esta semana (cerrar el viernes 30-oct)

| # | Decisión | Recomendación | Con quién |
|---|---|---|---|
| D1 | Escenario energético principal | Mantener el día aislado con batería llena como escenario principal, por continuidad con la Entrega 2. Agregar el análisis de repetibilidad con recomendación de infraestructura (T7) y la sensibilidad al estado de carga inicial y final | Grupo + ayudante |
| D2 | Costo de espera de 0,03 USD/min | Sumarlo al costo informado de todos los planes. Si el código lo permite sin rehacer todo, agregar un escenario con la espera dentro del objetivo | Grupo + ayudante |
| D3 | Un sector por bus | Mantenerlo como decisión del método, decirlo así en el informe y calcular también la cota sin sectores | Grupo |
| D4 | Límite eléctrico (`transformer_mw` sin dato) | Declarar el vacío. Usar conexiones × 180 kW en el escenario principal y un tope en MW como sensibilidad | Grupo + ayudante |
| D5 | Alcance | Día laboral, sábado y domingo en las 417 rutas, como promete el objetivo del informe 2. Costo semanal = 5 × laboral + sábado + domingo; flota = la mayor de las tres | Grupo |
| D6 | Caso base | La política miope por ruta con recarga del informe 2, corrida en la red completa | Grupo |
| D7 | Expositores | Quienes aún no han presentado, hasta 3 | Grupo |
| D8 | Fuente única | Un solo proyecto de Overleaf y un solo deck. Las cifras de ambos salen del mismo `cifras.tex` | Grupo |

**Reunión con el ayudante (Max Burr) el jueves 29 o el viernes 30-oct, 15 minutos.** Preguntas:
1. D1, D2 y D4.
2. ¿El índice, el abstract y el resumen ejecutivo cuentan en las 45 páginas?
3. Fecha de la presentación, fecha del informe y documento base de la Entrega 3.
4. ¿Se puede usar otra licencia o solver para las cotas?

## 5. Frentes de trabajo

Siete personas en cinco frentes. Los nombres los pone el grupo.

| Frente | Personas | Entrega |
|---|---|---|
| A. Cómputo | 2 | T0–T10: instancias, corridas, auditorías, cotas, sensibilidad y simulación |
| B. Cifras y figuras | 1 | T11: `cifras.tex` y las figuras de la Entrega 3, desde resultados auditados |
| C. Informe | 2 | Capítulos, investigación (R1–R8), anexo de correcciones y revisión de coherencia |
| D. Presentación | 2, incluidos los expositores | Deck, guion, tiempos, ensayos y banco de preguntas |
| E. Coordinación y calidad | 1 (puede ser alguien de C) | Calendario, decisiones, checklist final, repositorio, declaración de IA y firmas |

## 6. Trabajo técnico

Cada resultado se audita antes de usarlo. Las corridas largas van de noche.

- **T0 · Licencia de Gurobi** (medio día). La académica de `~/gurobi.lic` venció el 24-sep-2025. La restringida de pip descarta los modelos de más de 2.000 variables o restricciones: en la red completa se descartaron 48 de 40.070 modelos locales, y no alcanza para las cotas. Pedir una licencia académica nueva (gratis, desde la red UC o con VPN). Plan B: OR-Tools para el flujo de costo mínimo y HiGHS para los modelos enteros, ambos gratis.
- **T1 · Sábado y domingo** (hecha el 27-oct). Parametrizar `service_id` en `preparar_completa.py` y en `auditoria_independiente.py`. Generar `instancia_417_S` e `instancia_417_D`, correr `buscar_mejor.py` con el mismo presupuesto que el día laboral y auditar ambos.
- **T2 · Caso base en la red completa** (hecha el 27-oct). Correr `CODIGO apstone/tres_fases/caso_base.py` (umbral 0 %) para día laboral, sábado y domingo, y pasarlo por el auditor del híbrido, como se hizo con 212 rutas.
- **T3 · Costo completo** (medio día; depende de D2). Un script que suma la espera a todos los planes (caso base, modelo y escenarios) con una misma definición de espera.
- **T4 · Cotas inferiores** (2 días; depende de T0). Calcular dos cotas:
  - simultaneidad más km de servicio, para cada tipo de día;
  - circulación de costo mínimo sin batería (la Fase 1) sobre la red completa, con y sin sectores.

  Con ellas se arma la tabla de brechas. La Fase 1 es una relajación válida solo si admite al menos todas las conexiones que admite el modelo completo: hay que comprobarlo y decirlo en el informe.
- **T5 · Validación exacta** (4 días; depende de T0). Es la tarea más pesada. Escribir en gurobipy el modelo completo: cobertura exacta, continuidad, estado de carga por actividad, carga en bloques de 5 min, plazas y conexiones compartidas, y costo con espera. Resolverlo al óptimo (o con brecha ≤ 1 %) en 10 a 20 subinstancias de 1 a 4 rutas (100 a 400 corridas), repartidas entre los 5 electroterminales. Correr el híbrido en las mismas e informar la brecha media y máxima, con los tiempos. El mismo modelo es el del capítulo 5 (10 pts). Plan B: achicar a 1 o 2 rutas.
- **T6 · Variabilidad** (1 noche de máquina; depende de T1).
  - 5 réplicas del día laboral con el presupuesto oficial (600 + 600 s);
  - una curva de costo contra presupuesto (300, 600, 1.200 y 2.400 s);
  - informar media, desviación e intervalo de confianza del 95 %.

  La búsqueda se corta por reloj: todas las réplicas van en el mismo equipo y sin otros programas pesados abiertos.
- **T7 · Repetibilidad e infraestructura** (2 días; depende de T1).
  - Calcular la energía final de cada bus, dónde termina y su ventana nocturna.
  - Calcular cuánto puede entregar cada electroterminal de noche (plazas, conexiones, 180 kW) y cuántos MW faltarían, por terminal, para repetir el día.
  - Si el código lo permite, correr un escenario con estado de carga final mínimo.

  Es probable que el resultado sea que los 5 electroterminales no sostienen la red completa día tras día. Se presenta como hallazgo, con su recomendación.
- **T8 · Sensibilidad** (2 noches de máquina; depende de T2 y T3). Usa los escenarios de la tabla 6.1. Cada escenario se corre con el modelo y con el caso base, para mostrar si el ahorro se mantiene.
- **T9 · Incertidumbre** (3 días; depende de T1).
  - Un script nuevo de Monte Carlo lee `04_final/actividades.csv` y simula el plan fijo con duraciones de corrida variables (variación de 10 a 20 %) y consumo variable.
  - Mide el porcentaje de salidas atrasadas, el atraso medio y máximo, y los buses que bajan de la reserva de 35 kWh.
  - Después, reoptimizar con una holgura mínima entre corridas de 0, 3 y 5 min y graficar costo contra puntualidad.
- **T10 · Mejorar la solución** (opcional, solo si sobra tiempo). Opciones: más presupuesto partiendo del plan actual (`--desde`), intercambios entre sectores, o una construcción a partir de la Fase 1.
- **T11 · Cifras y figuras** (continuo). Copiar el pipeline de `08-entrega2/informe2/` (`compilar.sh`, `cifras.py`, `figuras.py`, `revisar.py` y sus pruebas) a `09-entrega3/informe3/`. Ampliarlo a los tres tipos de día, las cotas, la sensibilidad y la simulación.
- **T12 · Repositorio final** (1 día, al final).
  - Agregar como colaboradores al ayudante y al profesor.
  - Un README con la instalación y una orden por resultado.
  - Las pruebas pasando.
  - Una etiqueta `entrega-3` que calce con el informe.

### 6.1 Escenarios de sensibilidad

La rúbrica pide justificar cada parámetro (5 pts). Prioridad 1 es obligatoria; 2 y 3 van si hay tiempo.

| Parámetro | Valores | Por qué | Prioridad |
|---|---|---|---|
| Consumo (kWh/km) | 1,4 ± 10 % y ± 20 % | Clima, aire acondicionado, carga y pendiente; fija la autonomía | 1 |
| Plazas por electroterminal | −20 %, +20 %, +50 % | Es el recurso que se satura en los 5 electroterminales | 1 |
| Estado de carga inicial y final | Inicial 100, 90 y 80 %; final mínimo 0, 30 y 50 % | Condición de borde del día aislado (D1) | 1 |
| Tope eléctrico por electroterminal | 80 % y 60 % de la punta actual de cada uno (hoy entre 3,0 y 7,1 MW) | El enunciado habla de capacidad eléctrica restringida, y el dato no viene | 1 |
| Velocidad en vacío | 12, 15, 18 y 22 km/h | Congestión; hoy es constante | 1 |
| Costo de espera | 0 y 0,03 USD/min | Está en los datos y no se cobra (D2) | 1 |
| Presupuesto de búsqueda | 300 a 2.400 s | Calidad contra tiempo de la heurística (T6) | 1 |
| Potencia de carga | 120, 150 y 250 kW | Tecnología de cargadores | 2 |
| Costo fijo por bus | 150 y 350 USD/día | Es el 70 % del costo: cambia el equilibrio entre flota y km | 2 |
| Tarifa en punta | +50 % | Mueve el horario de carga | 2 |
| Cierre de un electroterminal | Uno a la vez | Resiliencia | 2 |
| Demanda | +10 % de corridas | Escalabilidad | 3 |

Para las implicancias (10 pts) hay que mostrar dos cosas: si el ahorro frente al caso base se mantiene en todos los escenarios, y qué parámetros mueven más el costo (gráfico de tornado).

## 7. Investigación

Cada referencia se verifica (autores, año, revista y DOI) antes de citarla, como en la Entrega 2. Los autores de esta tabla son candidatos, no citas confirmadas.

| # | Pregunta | Capítulo | Por dónde partir |
|---|---|---|---|
| R1 | Cómo resuelve la literatura el problema de programación de buses eléctricos con carga parcial e infraestructura compartida, y qué fortalezas, debilidades y supuestos tiene cada método frente a nuestro caso | Bibliografía (5) y estrategia (15) | Perumal, Lusby y Larsen (2022, revisión); Wen et al. (2016); van Kooten Niekerk et al. (2017); Li (2014); Kliewer, Mellouli y Suhl (2006, red tiempo-espacio); Bunte y Kliewer (2009); Adler y Mirchandani (2017) |
| R2 | Cómo se acota el óptimo y se certifica la calidad de una solución en este tipo de problemas | Resultados: optimalidad | Relajación lineal de la red tiempo-espacio; generación de columnas (Desrosiers y Lübbecke, 2005) |
| R3 | Si es razonable suponer carga lineal y sin degradación | Supuestos (5) y rangos de T8 | Olsen y Kliewer (2020) |
| R4 | Cómo se propagan los atrasos y cuánta holgura conviene dejar | T9 | Naumann, Suhl y Kramkowski (2011); Tang, Lin y He (2019) |
| R5 | Contexto real: flota eléctrica de la Red, electroterminales, carga nocturna en depósitos, velocidad comercial | Problema (15) y rangos | DTPM, Ministerio de Transportes, memorias de operadores |
| R6 | Cómo se pilotea y se evalúa un cambio de programación en transporte público | Implementación y piloto | Modo sombra, piloto por sector, comparación con sectores de control (diferencias en diferencias) |
| R7 | Consumo real de buses de 12 m en Santiago y tarifas eléctricas | Rangos de T8 | Estudios de electromovilidad en Chile |
| R8 | Estructura lógica de la clase de escritura técnica y reglas APA de apéndices | Todo el informe | Material del curso; apastyle.apa.org |

## 8. Informe: 45 páginas contra la rúbrica

| Cap. | Contenido | Pts | Págs | Cifras desde |
|---|---|---|---|---|
| — | Abstract (inglés) y resumen ejecutivo | 5 + 5 | 1,5 | todo |
| 1 | Introducción | (en los 5 de arriba) | 1,5 | — |
| 2 | Problema: contexto de la Red, impacto, objetivo, alcance y KPIs | 15 + 5 | 3,5 | R5 |
| 3 | Datos: fuentes, preparación, figuras por tipo de día, riesgos de sesgo y cómo condicionan el modelo | 5 | 3,5 | T1 |
| 4 | Revisión bibliográfica crítica y evolución metodológica (Entrega 1 → 2 → 3) | 5 + parte de 15 | 4 | R1–R4 |
| 5 | Modelo formal completo y supuestos (tabla: supuesto, justificación y cómo se prueba) | 10 + 5 | 4 | T5 |
| 6 | Estrategia (construcción, búsqueda local con modelos enteros, auditoría, cotas y validación exacta), implementación y herramientas | resto de 15 + 5 | 4,5 | T4, T5, T12 |
| 7 | Caso base en la red completa | 10 | 2 | T2 |
| 8 | Resultados: los tres tipos de día frente al caso base y las cotas, de dónde sale el ahorro, uso de los electroterminales, calidad de la solución, variabilidad y relación con los objetivos | 50 | 8 | T1–T6 |
| 9 | Sensibilidad, incertidumbre y repetibilidad | 35 | 6 | T7–T9 |
| 10 | Implementación, piloto y extensiones | 5 | 2,5 | R6, T7 |
| 11 | Conclusiones: hallazgos, fortalezas, limitaciones y pasos siguientes | 25 | 2 | — |
| | **Cuerpo** | **200** | **43** (2 de margen) | |

**Anexos** (formato APA, solo material complementario):
- A. Notación.
- B. Correcciones: cada comentario del informe 1, la presentación 2, el informe 2 y los pares, con el lugar donde se atendió.
- C. Parámetros de cada escenario.
- D. Tablas completas de sensibilidad.
- E. Cómo reproducir los resultados.
- Declaración de IA firmada.

**Orden de redacción:**
1. Primero lo que ya tiene material: capítulos 2, 3, 4 y 7, a partir del informe 2 y de la versión de Overleaf.
2. Después los capítulos 5 y 6.
3. Los capítulos 8, 9 y 10 a medida que llegan las cifras.
4. Al final, la introducción, las conclusiones, el abstract y el resumen ejecutivo.

## 9. Presentación: 15 minutos

| Bloque | Pts | Tiempo | Láminas |
|---|---|---|---|
| Problema y objetivo | 10 | 2:00 | 2–3 |
| Datos | 5 | 1:00 | 4 |
| KPIs | 4 | 0:40 | 5 |
| Caso base | 5 | 1:00 | 6 |
| Metodología: evolución, por qué el híbrido, el modelo | 8 | 2:00 | 7–8 |
| Implementación y auditoría | 5 | 1:00 | 9 |
| Resultados: tres tipos de día, de dónde sale el ahorro, optimalidad, sensibilidad, incertidumbre y repetibilidad | 18 | 5:00 | 10–15 |
| Cierre: conclusiones, piloto y pasos siguientes | 5 | 1:30 | 16–17 |
| **Total** | **60** | **14:10** | 17 + anexos |

**Reglas que vienen del feedback del 8-oct:**
- número en todas las láminas;
- supuestos explícitos sobre lo que no está en los datos;
- ningún porcentaje sin decir de dónde sale;
- decir de dónde salen los costos antes de mostrarlos;
- KPIs comparados contra el caso base;
- justificar la comparación contra la cota.

**Además:** leyenda y unidades en cada gráfico, poco texto por lámina y el detalle en las notas del orador.

**Ensayos:** tres, con cronómetro, y al menos uno con el grupo completo. La meta es entre 14:00 y 14:30. Si un ensayo se pasa del tiempo, se corta contenido; no se habla más rápido.

**Banco de preguntas.** Cada una con una respuesta de 30 s y, si hace falta, una lámina de anexo:
- ¿La solución es óptima?
- ¿Cómo se repite el día siguiente?
- ¿Por qué no respetan los 1.200 buses?
- ¿Por qué los sectores son fijos?
- ¿Qué pasa con los atrasos?
- ¿Por qué 18 km/h en vacío?
- ¿Y el límite del transformador?
- ¿Por qué no cobran la espera?
- ¿Qué tan sensibles son al consumo?
- ¿Cuánto demora y en qué equipo?
- ¿Cómo lo implementaría la Red?

## 10. Calendario

Supone la presentación el jueves 19-nov y el informe el viernes 27-nov.

**Semana 1 · 27-oct al 1-nov**
- Cómputo: T0 (licencia), T1 (sábado y domingo), T2 (caso base), T3 (costo con espera).
- Informe y cifras:
  - reunir los cuatro comentarios y el documento base;
  - armar el esqueleto de 45 páginas en Overleaf;
  - empezar el anexo de correcciones;
  - partir con R1 y R5.
- Presentación: definir los expositores (D7).
- **Hitos:** el viernes 30, decisiones D1–D8 cerradas; el domingo 1, los tres tipos de día y el caso base auditados.

**Semana 2 · 2 al 8-nov**
- Cómputo: T4 (cotas), T5 (validación exacta), T6 (réplicas, de noche), T7 (repetibilidad).
- Informe y cifras: capítulos 2, 3, 4 y 7 en borrador; T11 con los tres tipos de día.
- Presentación: el hilo de la historia en una página.
- **Hito:** el domingo 8, cotas, brechas y diagnóstico energético listos.

**Semana 3 · 9 al 15-nov**
- Cómputo: T8 (sensibilidad, de noche) y T9 (simulación).
- Informe y cifras: capítulos 5 y 6; los capítulos 8 y 9 a medida que llegan las cifras.
- Presentación: deck en borrador, aún sin cifras finales.
- **Hito:** el domingo 15, **congelación de cifras**. Desde ahí no se corre nada que cambie el informe.

**Semana 4 · 16 al 22-nov**
- Cómputo: solo correcciones.
- Informe: capítulos 10 y 11.
- Presentación:
  - lunes 16, deck completo;
  - martes 17, ensayo 1;
  - miércoles 18, ensayo 2 con preguntas;
  - **jueves 19, presentación**.
- **Hito:** el domingo 22, borrador completo del informe.

**Semana 5 · 23 al 27-nov**
- Cómputo: T12 (repositorio final).
- Informe:
  - lunes y martes, revisión cruzada (dos lectores por capítulo) con el checklist de la sección 11;
  - abstract y resumen ejecutivo;
  - firmas de la declaración de IA.
- Evaluación de pares: la responden todos.
- **Hito:** el viernes 27, **entrega**.

**Si la presentación cae en otra fecha:**
- **Jueves 12-nov:** la congelación pasa al domingo 8-nov. La sensibilidad se reduce a la prioridad 1, la simulación queda sin reoptimizar y el deck se arma la semana del 2-nov.
- **Jueves 26-nov:** la semana extra va a T10 (mejorar la solución) y a un tercer ensayo. La congelación pasa al domingo 22-nov.

## 11. Control de calidad antes de entregar

**Informe**
- [ ] Ninguna cifra escrita a mano: todas salen de `cifras.tex`, y `compilar.sh` termina sin errores.
- [ ] Cada resultado usado pasó el auditor.
- [ ] El cuerpo tiene 45 páginas o menos, con el documento base sin tocar, índice e índices de figuras y tablas.
- [ ] El abstract en inglés y el resumen ejecutivo tienen las cifras clave.
- [ ] Un solo término por concepto en todo el informe y el deck; siglas definidas la primera vez que aparecen.
- [ ] Cada figura es legible, tiene leyenda, unidades y título, y se cita en el texto.
- [ ] Cada referencia está verificada; citas y apéndices en formato APA; los apéndices son solo complementarios.
- [ ] El anexo B muestra dónde se atendió cada comentario recibido.
- [ ] Se dice explícitamente si la solución es óptima o aproximada, con su brecha y su cota.
- [ ] La declaración de IA está marcada SÍ, con el detalle de los usos y las firmas de los 7.
- [ ] El enlace al repositorio abre para el ayudante y el profesor.

**Presentación**
- [ ] El último ensayo dura entre 14:00 y 14:30, con cronómetro.
- [ ] Todas las láminas tienen número; los gráficos tienen leyenda; no hay sintaxis LaTeX cruda ni restos de plantilla.
- [ ] Las cifras son las mismas del informe.
- [ ] Hay 3 expositores como máximo, incluidos quienes aún no han presentado.
- [ ] Hay láminas de anexo para el banco de preguntas.

**Código**
- [ ] El README explica la instalación y tiene una orden por resultado; las pruebas pasan; la etiqueta `entrega-3` existe.

## 12. Riesgos

| Riesgo | Cómo se detecta | Plan B |
|---|---|---|
| La fecha es antes de lo supuesto | Canvas o el ayudante | Seguir la sección 10 |
| No hay licencia académica | Error 10009 o modelos descartados por tamaño | OR-Tools y HiGHS para las cotas y la validación exacta |
| Sábado o domingo no corren o no pasan el auditor | Falla T1 | Revisar la preparación de datos antes que el método; avisar al grupo el mismo día |
| La red completa no se sostiene día a día con los 5 electroterminales | T7 | Presentarlo como hallazgo con recomendación de infraestructura; no esconderlo |
| El deck y el informe muestran cifras distintas | Ensayo 1 | Ambos leen el mismo `cifras.tex` |
| iCloud deja archivos solo en la nube y las lecturas se cuelgan | `ls -lO` muestra `dataless` | Marcar `Proyecto` como «Mantener descargado» y correr en `~/capstone-grupo29` |
| Hay dos versiones del deck o del informe | Ediciones cruzadas | D8: una sola fuente, con un responsable por archivo |
| El informe pasa de 45 páginas | Conteo cada domingo | Respetar el presupuesto de páginas por capítulo; pasar detalle a anexos sin esconder resultados |

## 13. Qué hay que conseguir fuera del proyecto

Guardar todo en `09-entrega3/comentarios/`:
- la fecha de la presentación, la del informe y el documento base (Canvas);
- la corrección del informe 2;
- la retroalimentación de pares que recibió el G29;
- el feedback escrito de la presentación del 8-oct y la corrección anotada del informe 1;
- la licencia académica de Gurobi (T0).
