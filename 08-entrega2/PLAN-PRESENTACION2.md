# Presentación 2: plan de láminas

Primera versión: 5 de octubre de 2026. Fuentes: `00-enunciado/Lineamientos Entrega 2 2026-2.docx`,
el feedback del ayudante a la Presentación 1 y el informe 1 anotado (`g29 anotado.pdf`).

**Límite:** 10:00 duros (+60 s y nos cortan). El guion apunta a **9:35**.
**Máximo 3 expositores.** Todos los integrantes tienen que haber presentado en alguna de las tres entregas.

---

## 1. Puntaje de la rúbrica (60 pts) → tiempo

| Ítem | Pts | Tiempo asignado |
|---|---|---|
| Descripción del problema (con objetivo y entregable) | 10 | 80 s |
| Datos | 5 | 70 s |
| KPIs | 4 | 35 s |
| Caso base | 7 | 50 s |
| Metodología | 9 | 115 s |
| Implementación | 5 | 45 s |
| **Resultados** | **15** | **125 s** |
| Cierre (conclusiones + pasos siguientes) | 5 | 50 s |

Resultados es el ítem que más pesa y en la Entrega 1 no existía. Ahí va el tiempo.
Las láminas siguen el orden de la rúbrica, que es la lista que los profesores tienen al lado mientras corrigen.

---

## 2. Láminas

Todas llevan **número `n / 14`** abajo a la derecha (feedback general).

| # | Lámina | Ítem | s | Exp. |
|---|---|---|---|---|
| 1 | Portada | — | 5 | A |
| 2 | El problema: qué es una corrida y qué decidimos | Problema | 45 | A |
| 3 | Objetivo: qué costos minimizamos y qué entregamos | Problema | 35 | A |
| 4 | Datos: de 417 recorridos a 64.502 corridas, y cómo se reparten en el día | Datos | 45 | A |
| 5 | Lo que los datos no traen y qué suponemos | Datos · Supuestos | 25 | A |
| 6 | Con qué medimos (KPIs) | KPIs | 35 | A |
| 7 | Caso base: cómo lo haría alguien sin optimizar | Caso base | 50 | B |
| 8 | Formulación: red tiempo-espacio | Metodología | 60 | B |
| 9 | Por qué tres fases y qué perdemos con eso | Metodología | 55 | B |
| 10 | Prototipo: instancia, herramientas y tamaño | Implementación | 45 | B |
| 11 | Resultados: caso base vs. modelo vs. cota | Resultados | 65 | C |
| 12 | Resultados: de dónde sale la diferencia | Resultados | 60 | C |
| 13 | Carta Gantt: lo planificado y lo hecho | Cierre | 25 | C |
| 14 | Conclusiones y pasos siguientes | Cierre | 25 | C |

Bloques: A = 190 s, B = 210 s, C = 175 s. Total 575 s = 9:35.
**Anexos** (fuera del tiempo): formulación completa, glosario, tabla de supuestos, la cota inferior por tipo de día.

---

## 3. Qué dice cada lámina

### 2 · El problema
- **Definir "corrida" en la primera frase**, porque en el informe la anotaron dos veces: *una corrida es una salida de un recorrido a una hora dada*. Ejemplo: el 506 que sale a las 07:15. Un recorrido tiene decenas de corridas al día.
- Usar **una sola palabra** en todo el deck: "corrida". No mezclar con "viaje" (el informe usa las dos y el ayudante preguntó si eran lo mismo).
- Qué decidimos: cuántos buses, qué corridas hace cada bus y en qué orden, y cuándo y dónde recarga.
- La cantidad de buses **la determina el modelo**. No mencionar los 1.200 de `parameters.csv` (anotación del informe).

### 3 · Objetivo
- Una frase con **todo** lo que contempla (anotación del informe: antes se mencionaban solo los costos): cubrir las 64.502 corridas de un día laboral al menor costo diario, respetando la batería y la capacidad de los 5 electroterminales.
- **Decir de dónde salen los costos antes de mostrar cifras** (feedback presentación): "son los parámetros entregados en `parameters.csv` y `electricity_prices.csv`":
  - 250 USD por bus utilizado
  - 0,5 USD por km recorrido (con y sin pasajeros)
  - 0,10 a 0,22 USD/kWh según la hora de carga
  - 0,03 USD por minuto de espera
  - 5 USD por cada carga
- Si se muestra el "66 % es flota", decir que es la cota de flota × 250 USD sobre la suma de esos componentes. **Recalcular con 6.601**: la cifra de 2.512.204 se hizo con 6.603 buses.
- Entregable: herramienta en Python, reproducible, que entrega asignación bus-corrida + calendario de recargas + flota + costos.

### 4 · Datos
- Escalera con cifras del informe final: 427 → **417 recorridos** RED (filtro `agency_id=RM`, `route_type=3`) → 6.620 patrones laborales → **64.502 corridas** (expandiendo frecuencias).
- **Gráfico de corridas activas a lo largo del día** (lo pidió el ayudante en el informe). Pico de 6.601 a las 08:00.
- Nombrar las siglas completas la primera vez: GTFS (*General Transit Feed Specification*, el formato de horarios), SOC (*state of charge*, % de batería).

### 5 · Lo que los datos no traen
Feedback general: "hagan supuestos y expliquen que no los consideran". Tabla de dos columnas, *no está en los datos* → *qué suponemos*:
- Tráfico, accidentes, fallas, mantenciones → duraciones nominales, sin perturbaciones
- SOC inicial de cada bus → todos parten al 100 %
- Consumo energético → 1,4 kWh/km lineal (350 kWh / 250 km)
- Traslados sin pasajeros → reconstruidos por distancia (25 km/h, factor de rodeo 1,35)
- Potencia real de los electroterminales → capacidad de carga suficiente; solo limitan los cupos
- Curva de carga → **lineal**; aclarar que **es un supuesto nuestro**, no una limitación de la metodología (anotación del informe)

### 6 · KPIs
Feedback: un KPI es una métrica que se mide en la solución y **se compara con el caso base**. Sacar las columnas "valor de referencia" e "importancia".

| KPI | Fórmula | Unidad |
|---|---|---|
| Flota | buses utilizados | buses |
| **Costo total** (antes "costo operacional") | suma de los 5 componentes de la lámina 3 | USD/día |
| **Costo energético** (antes "energía") | Σ precio(hora) × kWh cargados | USD/día |
| Kilómetros en vacío | km sin pasajeros / km totales | % |
| Ocupación de carga | máximo de buses cargando a la vez / cupos, por electroterminal | % |
| Buses agregados por batería | flota final − flota de la Fase 1 | buses |

- El ayudante preguntó por qué medir solo el costo energético y no los demás: **mostrar el costo total desglosado** en sus 5 componentes, no solo la energía.
- **Ningún porcentaje sin fórmula.** El 90 % de ocupación y el < 20 % de eficiencia de la Presentación 1 eran metas que nadie podía rastrear; no vuelven.
- La cobertura no es KPI: si no es 100 %, el plan no sirve. Se dice como condición.

### 7 · Caso base
Rúbrica: "forma intuitiva, no analítica de hacer las cosas, una política miope". Tiene que correr **sobre la misma instancia** que el modelo.
Propuesta (por decidir con el grupo, ver preguntas abiertas):
- **Cada recorrido con sus propios buses.** No se comparten buses entre recorridos; dentro del recorrido, cada corrida la toma el primer bus libre que alcance a llegar.
- **Recarga miope:** cuando el SOC baja de un umbral, el bus va al electroterminal más cercano y carga al 100 %, a la hora que sea.
- Por qué es defendible: es como se planifica a mano (por línea), siempre es factible, y la diferencia con el modelo mide exactamente las dos palancas que el modelo agrega: compartir buses entre recorridos y elegir cuándo cargar.

### 8 · Formulación
Lo que exigen los lineamientos: conjuntos, parámetros, variables, restricciones, en lenguaje matemático. En la lámina, solo la estructura; el detalle va en anexo.
- Conjuntos: corridas, nodos de la red (eventos de llegada y salida por punto y hora), arcos (servicio, vacío, espera, entrada y salida de electroterminal), electroterminales.
- Variables: flujo de buses en cada arco.
- Función objetivo: los 5 componentes de costo.
- Restricciones: conservación de flujo, cada corrida cubierta una vez, capacidad del electroterminal.
- Mostrar un **dibujo pequeño de la red tiempo-espacio** (ejes tiempo × lugar) en vez de diez ecuaciones.

### 9 · Por qué tres fases
- Fase 1: flujo de costo mínimo, sin batería → cuántos buses y por dónde pasan.
- Fase 2: descomponer ese flujo en jornadas de bus concretas.
- Fase 3: recorrer cada jornada actualizando el SOC e insertar recargas; si no alcanza, cortar la jornada y agregar un bus.
- Sectorizar por electroterminal: 5 subproblemas de ~12.000 corridas, cerca de la escala probada por Olsen et al. (10.710).
- Fortalezas: escala; siempre entrega un plan factible; la Fase 1 da una cota.
- Debilidades: pierde optimalidad global; la solución depende de la sectorización; la batería entra tarde.
- **Corrección del informe:** el informe hablaba de "terminales convencionales" en la Fase 2, que no existen en nuestros datos. Adaptarlo a lo que sí hay: electroterminales y puntos de término de recorrido.

### 10 · Prototipo
Lineamientos: instancia simplificada **con justificación**, herramientas, supuestos y qué aprendimos para la versión final.
- Instancia: [por confirmar: ¿un sector?]. Si es un sector, la justificación sale sola: la sectorización ya es parte del método, así que es un subproblema real, no un recorte arbitrario.
- Herramientas: Python, [solver], [librerías].
- Tamaño: nodos, arcos, tiempo de cómputo.

### 11 · Resultados: tabla principal
Columnas **caso base | modelo | cota inferior**, filas = KPIs de la lámina 6.
- La gráfica que más explica: buses en ruta y buses cargando, por hora, caso base vs. modelo.

### 12 · Resultados: de dónde sale la diferencia
- Costo total desglosado (barras apiladas): cuánto ahorra el modelo en flota, cuánto en km, cuánto en energía.
- **Brecha contra la cota**, con la justificación que pidió el ayudante (ver sección 4).
- Si hay variabilidad o sensibilidad (umbral de SOC, consumo ±, día sábado), va aquí.
- Validación de los KPIs: ¿alguno no discriminó entre caso base y modelo? Los lineamientos piden decir si sirven o hay que cambiarlos.

### 13 · Carta Gantt
La del informe 1 (14 sep → 11 oct) marcando qué se cumplió y qué no, y por qué. Lo piden explícitamente los lineamientos.

### 14 · Conclusiones y pasos siguientes
Conclusiones accionables (qué decide un operador con esto), cómo se pasa del sector a la red completa y a sábado/domingo, y análisis de sensibilidad pendientes.

---

## 4. La cota inferior: cómo responder las tres preguntas del ayudante

> ¿Cómo se aseguran de que su solución esté cerca de la cota? ¿Por qué comparar así? Si la cota no es factible, ¿cómo sirve?

1. **No hace falta que la cota sea factible.** Ningún plan factible usa menos buses que la cota. Entonces `(flota_sol − cota) / cota` es un **máximo** de cuánto nos alejamos del óptimo: si da 5 %, estamos a lo más 5 % del mejor plan posible. La cota es un piso, no un rival.
2. **Hay dos pisos, y uno es mucho mejor:**
   - Simultaneidad (6.601): débil, porque ignora los traslados en vacío y las recargas.
   - **El óptimo de la Fase 1** (flujo sin batería): más ajustado, porque ya incluye los traslados en vacío. Es una relajación del problema completo, así que también es un piso válido.
3. **Lo que se reporta:** la brecha contra la Fase 1. Esa brecha *es* el costo de la batería: los buses que hubo que agregar porque la energía no alcanzaba.
4. **Advertencia honesta:** el piso de la Fase 1 vale para el problema *sectorizado* (cada recorrido asignado a un electroterminal fijo), no para la red sin sectorizar.

---

## 5. Cifras que no vuelven a aparecer

| Cifra (Presentación 1) | Problema | Qué hacer |
|---|---|---|
| "23 % geográficamente factible", "3,1 % es barato" | no se explicó de dónde salían | sacarlas; la dificultad ya queda clara con 64.502 corridas y la batería |
| 90 % (630) de ocupación, < 20 % de eficiencia | metas sin cálculo detrás | sacarlas; los KPIs se miden, no se fijan |
| "Importancia 3/5" | sin criterio | sacar la columna |
| 64.603 corridas (lámina objetivo) | cifra de un procesamiento anterior | usar **64.502** |
| 2.545.946 y 2.512.204 USD/día | dos pisos distintos; el segundo usa 6.603 buses | recalcular uno solo, con 6.601, desde el código |
| 816 viajes "en 28 h" (de Vos) | el informe dice 7 h | revisar en el paper antes de usarla |

---

## 6. Preguntas abiertas

- [ ] ¿Dónde está el código de las Fases 1-3 y del caso base? No está en `02-codigo/`.
- [ ] ¿Sobre qué instancia corrió el prototipo (un sector, una ventana horaria, la red completa)?
- [ ] ¿Qué caso base usamos? (Propuesta en la lámina 7.)
- [ ] Fecha de la presentación y quiénes exponen.
- [ ] ¿Se arma otra vez en claude.ai/design con el estilo rojo de la Presentación 1?
