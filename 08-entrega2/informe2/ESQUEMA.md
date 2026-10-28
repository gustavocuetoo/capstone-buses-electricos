# Esquema del informe de la Entrega 2 — Grupo 29

Acordado el 13-oct-2026. **Entrega: viernes 16-oct-2026.** El grupo revisa el borrador completo el 15-oct.

Este documento fija qué va en cada capítulo, de dónde sale cada cifra y qué comentario de la corrección atiende cada parte. Si algo de aquí cambia, se cambia aquí primero y después en el `.tex`.

---

## 1. Reglas de forma (lineamientos de la Entrega 2)

- LaTeX con el documento base del curso: `pucthesis.cls`, copiado de `CODIGO apstone/informe/`. **No se toca su configuración** (márgenes, interlineado, letra): los lineamientos lo castigan.
  - **Tamaño de letra: 11 pt** (decidido el 13-oct). La plantilla original del curso (`Plantilla_Informe.zip`) carga la clase en 12 pt, y el grupo la cambió a 11 pt en `pucthesis.cls` (línea 4) para el informe 1. Se mantiene 11 pt porque es lo que piden los lineamientos («Times New Roman de 11 puntos») y la corrección del informe 1 no lo objetó. Se copia la versión del grupo; los demás cambios de esa versión son de idioma y de capítulos.
- Times New Roman 11, índice obligatorio, índices de figuras y tablas.
- **Máximo 30 páginas** sin contar portada, índice, resumen, anexos ni bibliografía.
- Anexos según APA: solo material complementario y citado en el cuerpo. No sirven para esquivar el límite de páginas.
- Citas con `apacite`. Figuras legibles, con leyenda, y numeradas y citadas en el texto.
- Enlace al repositorio del código dentro del informe.
- **Declaración de uso de IA al final del informe**, como piden los lineamientos (el informe 1 la puso al principio). Marca **SÍ** y detalla los usos. La firman los 7 integrantes.
- Rótulos de la plantilla en español: «ANEXOS», «Figura» y «Tabla». No se dejan restos de la plantilla como «First Appendix» o «An Interesting Short Story».
- Voz impersonal («se construyó», «se observa»), igual que el informe 1.
- Números en formato chileno: 1.374.632 y 14,1 %.

## 2. Decisiones de fondo

| Tema | Decisión |
|---|---|
| Caso base oficial | **Política miope por ruta con recarga** (`CODIGO apstone/tres_fases/caso_base.py`, umbral 0 %): 4.509 buses, USD 1.601.775 |
| Por qué ese caso base | El profesor y el ayudante pidieron que el caso base incluya carga «aunque sea de manera bien básica» |
| Caso base presentado el 8-oct (sin recargas, 5.150 buses) | Solo un párrafo en el capítulo 4 que explica el cambio |
| Otros casos base (prototipo 4.175, cronológica 4.014) | Fuera como líneas de comparación, hasta hablarlo con el grupo. El prototipo aparece en el capítulo 3 como prueba de concepto, no como caso base |
| Resultado principal | **Refinado del 6-oct**: 3.873 buses, USD 1.374.632 (`metodo_hibrido/resultados/mejor_20261006_refinamiento/`) |
| Red completa (417 rutas) | Fuera del informe. Escalar a la red completa es un paso futuro |
| Variabilidad | Barrido de presupuesto: 15 corridas, rotuladas «otro equipo» |
| Formulación | Modelo completo basado en conexiones entre corridas. El MILP local del híbrido es ese mismo modelo restringido a 1–3 jornadas |
| Cifras | Ninguna se escribe a mano: salen de `cifras.tex`, que genera un script (sección 5) |

## 3. Preliminares (no cuentan en las 30 páginas)

- **Portada:** los 7 integrantes, profesor guía Agustín Chiu, ayudante tutor Max Burr, «Santiago de Chile, octubre 2026».
- Índice, índice de figuras e índice de tablas.
- **Resumen (1 página como máximo).** Entra en el ítem «Resumen del caso de estudio» (15 pts) junto con la introducción. Debe incluir:
  - el problema y su alcance;
  - la motivación;
  - el objetivo, de forma que se pueda evaluar;
  - **el entregable esperado**;
  - qué se hizo en esta entrega;
  - el resultado principal frente al caso base;
  - la conclusión central.

  Sin siglas sin definir.

## 4. Capítulos

Cada capítulo indica: páginas · ítems de la rúbrica · contenido · figuras y tablas · fuentes · comentarios que atiende. En los comentarios, **[A-pN]** es una anotación del informe 1 en la página N del PDF corregido, y **[F]** es el feedback de la presentación del 8-oct.

### Capítulo 1. Introducción — 1,5 págs.

**Rúbrica:** Resumen del caso de estudio (15).

**Contenido**
1. Contexto: la Red Metropolitana de Movilidad y su flota eléctrica. Se escribe separado de lo que se resuelve.
2. Cómo nace el problema y qué parte se resuelve (una simplificación del problema real).
3. **Objetivo del semestre:** una herramienta reproducible que entregue, para las 417 rutas y cada tipo de día (laboral, sábado y domingo o festivo), un plan diario factible de menor costo total. El plan indica qué bus cubre cada corrida, en qué orden, y cuándo, dónde y cuánto recarga. Respeta horarios, autonomía y las plazas y conexiones de los 5 electroterminales.
4. Entregable final.
5. Qué se hizo en esta entrega: un prototipo en 212 rutas, en día laboral.
6. Qué cambió desde el informe 1: el método y el caso base.
7. Estructura del informe.

**Reglas:** el objetivo no lleva porcentajes de costo sacados de los resultados. El tamaño de la flota se presenta como una decisión del modelo, sin discutir el valor de 1.200.

**Atiende:** [F] distinguir contexto de problema; [F] el objetivo es lo de fin de semestre; [F] porcentajes de costo en el objetivo; [A-p9] objetivo incompleto (faltaban los 5 E y los horarios); [A-p8] cifra de 1.200 buses.

### Capítulo 2. Descripción detallada del problema y datos — 4,5 págs.

**Rúbrica:** Análisis de datos (5), KPI (10).

**2.1 Glosario.** Una tabla breve con los siguientes términos:
- **ruta** (o recorrido);
- **corrida:** una salida de una ruta a una hora dada. Se usa siempre en ese sentido, nunca «viaje» como sinónimo;
- **traslado en vacío:** el bus se mueve sin pasajeros entre el fin de una corrida y el inicio de otra, o hacia un terminal;
- **cadena;**
- **jornada:** lo que hace un bus durante el día;
- **sector;**
- **electroterminal (E):** tiene cargadores;
- **terminal de espera (T):** sin carga;
- **estado de carga (SOC).**

Toda sigla se define la primera vez que aparece.

**2.2 Problema.** En palabras: qué se decide, qué restringe y qué se minimiza. Las corridas son una oferta fija: no se eliminan ni se mueven.

**2.3 Datos y su preparación**
- Del GTFS completo a buses RED: tabla 427 → 417 rutas (lámina 5 del deck).
- Corridas reconstruidas desde frecuencias (`exact_times = 0`): son una instancia determinística representativa, no salidas observadas. Cifras: 64.502 corridas laborales.
- Distancias viales dirigidas.
- Archivos del curso: vehículos, 5 electroterminales (`depots.csv`), capacidad de carga, tarifas y parámetros.
- **Figura: corridas en curso por hora del día** [A-p11].

**2.4 Decisiones de preparación que condicionan el modelo**
- **Sectores:** cada ruta va al E con menor suma de distancias. Tabla de rutas y corridas por sector.
- **Terminales T01–T04:** de dónde salen y por qué hacen falta. Pendiente de verificar (sección 7).
- **Muestra de 212 rutas:** reproducible, unas 42 por sector, por cuantiles de longitud media. Incluye rutas cortas, medias y largas y no se eligió mirando resultados. Tabla que compara muestra y red (km medio por corrida, corridas por hora y distribución por sector) para discutir **sesgos**.
- **Horizonte:** de −7.086 a 98.901 s respecto de la medianoche.

**2.5 KPIs.** Se definen aquí y se miden en el capítulo 7. Se comparan **siempre contra el caso base**, con Δ y Δ%, nunca contra metas fijas [A-p13].
1. **Costo total** (USD/día) = flota + km + electricidad + sesiones, con el peso porcentual de cada componente [A-p14: nombre y desglose].
2. **Buses utilizados.**
3. **Km en vacío**, como % de los km totales.
4. **Uso de electroterminales:** máximo de plazas y de conexiones ocupadas, sobre la capacidad de cada E.

De apoyo: energía comprada, sesiones de carga y tiempo de cómputo. Cada KPI con su fórmula en palabras y sus símbolos definidos.

**Fuentes:** `04-documentos/analisis_datos.tex`; `CODIGO apstone/informe/Informe_P7_integrado.zip` (`descripcion_problema.tex`); `01-datos/`; `metodo_hibrido/instancia_212/`; `CODIGO apstone/output/tres_fases/muestra_212/seleccion_rutas.csv`; `CODIGO apstone/tres_fases/datos.py` (función `seleccionar`).

**Atiende:** [F] definir corridas, cadenas, traslados en vacío y jornadas; [F] mostrar el análisis de datos y justificar sectores y rutas; [F] qué rutas se eligieron y si eso afecta los resultados; [F] KPIs dispersos y letras sin explicar; [A-p7] «corrida»; [A-p8] y [A-p9] siglas; [A-p10] «distancia de qué»; [A-p11] qué significa «energía MWh»; [A-p16] corridas vs. viajes.

### Capítulo 3. Evolución y discusión metodológica — 3 págs.

**Rúbrica:** Revisión bibliográfica (5) y parte de Metodología (20).

**Contenido**
- **3.1** Las alternativas del informe 1 en un párrafo (MILP, generación de columnas, red tiempo-espacio) y por qué se eligió tres fases.
- **3.2 Prueba de concepto:** el prototipo de tres fases en 212 rutas.
  - Fase 1: LP de 63.298 nodos y 2.092.978 variables; 3.561 buses sin batería.
  - Con batería y reparación: 4.322 → 4.175 buses.

  **Se presenta como prueba de concepto, no como caso base.**
- **3.3 Diagnóstico:** al cortar cadenas por batería se agregan buses, y la energía queda desacoplada de la asignación. Eso es lo que da los lineamientos para el método final.
- **3.4 Por qué el híbrido.** Discusión crítica con referencias: fortalezas, debilidades y supuestos de cada una en relación con este caso. Referencias:
  - despacho secuencial (verificar autor y año exactos: el deck dice «Bodin et al., 1978»);
  - una revisión de programación de buses eléctricos;
  - métodos que combinan heurísticas con MILP local (matheurísticas);
  - de Vos et al. (2024) y Alvo et al. (2021), si siguen siendo pertinentes.
- Aclarar que la carga lineal es **un supuesto de este trabajo**, no una limitación del método [A-p20].

**Atiende:** [A-p19] «terminales convencionales» (en los datos solo hay E; se explica qué son los T); [A-p20] baterías lineales.

### Capítulo 4. Caso base — 2 págs.

**Rúbrica:** Caso base (10).

**Contenido**

**4.1 Política miope por ruta con recarga**, en pasos:
1. Las corridas se recorren en orden de hora de salida.
2. Cada ruta tiene sus propios buses.
3. Cada corrida se asigna al bus de su ruta que lleva más tiempo libre y alcanza a llegar a tiempo.
4. Si la batería no alcanza para la corrida y la reserva de regreso, el bus va antes al E más cercano con cupo y carga al 100 %. Si ahí no cabe a tiempo, prueba el siguiente.
5. Si ningún bus de la ruta puede, se agrega uno con batería llena desde el T más cercano.
6. Después de su última corrida, cada bus vuelve al T más cercano.

**4.2 Por qué es defendible:** es intuitiva y no usa optimización, imita la operación por ruta e incluye carga básica.

**4.3 Mismo terreno de comparación:** mismas 212 rutas y 33.220 corridas [F], mismo horizonte, mismas constantes y **mismo auditor que el híbrido** (sección 7, verificación 1). Tiene 6 pruebas automáticas.

**4.4 Resultado:** tabla de KPIs.

**4.5 Sensibilidad al umbral de carga:** 0, 20, 30 y 50 %. Se usa 0 %, el más favorable para el caso base, para no inflar la ganancia del modelo.

**4.6 Párrafo sobre el caso base presentado el 8-oct:** era sin recargas, con 5.150 buses. Se cambió por el comentario del profesor y del ayudante. Lo que mostraba: sin recargas, 1.589 cadenas necesitan un segundo bus.

**Fuentes:** `CODIGO apstone/tres_fases/CASO_BASE.md`; `CODIGO apstone/output/tres_fases/muestra_212_caso_base*/resumen.json`; `caso_base_simple_gurobi/corrida_gurobi/resumen.json`.

**Atiende:** [F] incluir carga en el caso base; [F] decir que se usaron las mismas corridas reducidas; [F] cómo se cubre el día siguiente (remite al capítulo 8).

### Capítulo 5. Metodología híbrida propuesta — 5 págs.

**Rúbrica:** Metodología (20).

**5.1 Modelo matemático del problema completo** (basado en conexiones entre corridas):
- **Conjuntos:** corridas, electroterminales, terminales de espera, bloques de 5 min y sectores.
- **Parámetros:** horarios, distancias, consumo (1,4 kWh/km), batería (350 kWh), reserva (35 kWh), potencia (180 kW, 15 kWh por bloque), tarifa por bloque, plazas y conexiones por E, y costos (USD 250 por bus, 0,5 por km, 5 por sesión).
- **Variables:**
  - binaria «el mismo bus hace la corrida *j* después de la *i*»;
  - inicio y fin de jornada en un T;
  - energía al llegar a cada corrida;
  - carga por E y bloque entre dos corridas;
  - sesiones de carga.
- **Objetivo:** 250 × buses + 0,5 × km + Σ tarifa × kWh + 5 × sesiones.
- **Restricciones:**
  - cada corrida tiene exactamente un antecesor y un sucesor (otra corrida o un T);
  - solo se permiten conexiones factibles en tiempo y espacio;
  - una jornada no cruza sectores;
  - propagación de la energía;
  - reserva mínima;
  - carga máxima por bloque;
  - plazas físicas y conexiones por E y por bloque;
  - dominios de las variables.
- **Tamaño de la instancia y por qué no se resuelve directo.** Se cuentan las conexiones factibles (sección 7, verificación 7).

**5.2 El método híbrido**
- Construcción cronológica (7 pasos).
- Mejora por parejas: fusión, traslado de una corrida e intercambio de tramos finales.
- Mejora por tríos: absorción y rotación.
- **MILP local = el modelo de 5.1 restringido a 1–3 jornadas, con el resto fijo.** Decide los terminales de inicio y fin y las ventanas y kWh de carga.
- Regla de aceptación: solo cambios factibles que bajan el costo, así que nunca empeora la solución.

**5.3 Fortalezas, debilidades y propuestas de mejora** para la etapa final.

**Reglas:** cada símbolo se define la primera vez que aparece, en la misma frase. La tabla de notación completa va en el Anexo A.

**Fuentes:** `metodo_hibrido/README.md`, `conjunta.py`, `recarga.py`, `caso_base.py`, `intercambios.py`, `trios.py`; láminas 10–12 del deck; `08-entrega2/guia_preparacion_entrega_2.pdf`.

**Atiende:** [F] letras sin explicar en las restricciones y en la lámina 10 («E»); [A-p8] y [A-p9] siglas.

### Capítulo 6. Implementación computacional y trazabilidad — 2,5 págs.

**Rúbrica:** Implementación y herramientas (10).

**Contenido**
- **Diagrama de flujo de los módulos** [F]: instancia → construcción → parejas → tríos → auditoría → exportación, indicando qué archivo hace cada paso.
- Herramientas: Python, NumPy, Gurobi 12 (gurobipy) con la licencia restringida de pip. Se dice cuántos modelos locales se descartaron por tamaño: 184 de 60.440.
- **Auditor independiente:** cobertura exacta, identidad y horario de cada corrida, continuidad en tiempo y espacio, sector único, balance de energía, reserva y capacidades compartidas.
- 22 pruebas automáticas y protección de la mejor solución anterior.
- **Trazabilidad:** huellas sha256 de los datos y del código en cada corrida (`ejecucion.json`, `verificacion_final.json`).
- **Cómo se reproduce el refinado:** construcción → búsqueda de 600 s por etapa (8 vecinos, 3 alternativas) → refinamiento de 240 s (12 vecinos, 5 alternativas). En total 28,6 min. Como el presupuesto se mide en segundos, el número exacto depende del equipo.
- Enlace al repositorio de GitHub.

**Fuentes:** `metodo_hibrido/README.md`, `RESULTADOS.md`; `metodo_hibrido/resultados/mejor_20261006_refinamiento/INFORME.md`, `ejecucion.json`, `licencia.json`.

### Capítulo 7. Resultados y análisis de KPIs — 6 págs.

**Rúbrica:** Resultados y análisis (20), KPI (10).

**Reglas:** toda tabla lleva el valor, el Δ y el Δ% contra el caso base [F].

**7.1 KPIs: caso base contra refinado.** Tabla principal.

**7.2 Composición del costo:** el % de cada componente en el caso base y en el refinado [F], y qué significa.

**7.3 De dónde sale la diferencia, por etapas** [F: «¿es tema del caso base o del modelo?»]:

| Etapa | Buses |
|---|---:|
| Caso base miope | 4.509 |
| Construcción cronológica | 4.014 |
| Parejas | por confirmar |
| Tríos y refinamiento | 3.873 |

La construcción aparece como **etapa del método**, no como otro caso base. Se explica qué cambia entre el miope y la construcción: los buses se comparten entre rutas del mismo sector, la carga es parcial en vez de al 100 % y se elige el traslado en vacío más corto.

**7.4 Energía**
- **Figura:** energía cargada por hora del día, con la tarifa horaria encima [F].
- Cómo se reparte la carga entre tramos de tarifa y cuánto pesa en el costo.
- **Costo ajustado por la energía final:** lo que le falta a cada bus para volver a quedar lleno, valorizado a la tarifa nocturna. Así los dos planes se comparan como si terminaran con la batería llena. Es necesario porque **el miope compra 252.529 kWh y el refinado 26.432 kWh**: el miope carga al 100 % cada vez y termina con mucha más energía.

**7.5 Electroterminales:** las plazas se saturan y las conexiones tienen holgura. Tabla por E.

**7.6 Variabilidad:** barrido de presupuesto (15, 30, 60, 120 y 240 s × 3 repeticiones), con medianas y rangos. Va rotulado «otro equipo», porque el presupuesto se mide en segundos de reloj.

**7.7 Cotas inferiores y brecha**
- Simultaneidad: 3.398 buses en 212 rutas.
- Piso de la Fase 1 del prototipo: 3.561 buses, USD 1.278.245.
- Brecha del refinado contra cada cota. Una cota no necesita ser factible: la brecha acota por arriba la distancia al óptimo.

**7.8 Validez de los KPIs:** cuáles distinguen entre caso base y modelo y cuál sobra. Por ejemplo, los km de servicio son un dato, no un KPI.

**7.9 Limitaciones y mejoras posibles.**

**Fuentes:** `metodo_hibrido/resultados/mejor_20261006_refinamiento/` (`04_final/resumen.json`, `recargas.csv`, `jornadas.csv`, `comparacion_etapas.csv`); `metodo_hibrido/resultados/mejor_20261006_600/` (etapas previas); `CODIGO apstone/output/tres_fases/muestra_212_caso_base/`; `metodo_hibrido/resultados/presupuesto/registro.csv` y `08-entrega2/sensibilidad_presupuesto/`; `CODIGO apstone/output/tres_fases/muestra_212/` (Fase 1).

**Atiende:** [F] mostrar cambios porcentuales; [F] interpretar a fondo; [F] «si el caso base carga, ¿sería tan grande la diferencia?»; [F] peso de cada costo; [F] en qué horarios cargan los buses.

### Capítulo 8. Supuestos, riesgos y plan de sensibilidad — 2,5 págs.

**Rúbrica:** Supuestos (5).

**8.1 Tabla de supuestos**, con su fundamento y su riesgo:
- SOC inicial 100 % y día aislado sin reponer la batería al final;
- consumo lineal de 1,4 kWh/km;
- carga lineal hasta 180 kW en bloques de 5 min;
- flota irrestricta (autorizado por el equipo docente);
- T01–T04 sin carga y con estacionamiento ilimitado;
- esperas sin costo, aunque `parameters.csv` trae 0,03 USD/min;
- 18 km/h en los traslados en vacío;
- un sector por jornada;
- horarios reconstruidos desde frecuencias.

**8.2 Recarga nocturna** («¿cómo se cubre el día siguiente?» [F]). Estimación:
- energía que le falta a cada bus al terminar el día, desde `jornadas.csv`;
- comparada con lo que pueden entregar las conexiones de cada E en la ventana nocturna;
- más la restricción física: los T no tienen cargadores y los E suman 700 plazas para 3.873 buses.

Conclusión: queda como riesgo y como paso futuro (exigir un estado de carga al final del día).

**8.3 Sensibilidad ya hecha**
- presupuesto de búsqueda;
- umbral del caso base;
- costo de espera de 0,03 USD/min, **recalculado para el refinado y el miope**. El cálculo que existe es del ensayo oficial, no del refinado.

**8.4 Plan de sensibilidad.** Tabla con supuesto, rango, KPI que se mira y semana en que se corre:
- consumo ±10 %;
- potencia de carga;
- conexiones por E;
- SOC final exigido;
- tarifa.

**No se corre nada nuevo antes del 16-oct.**

### Capítulo 9. Conclusiones — 1,5 págs.

**Rúbrica:** Conclusiones (20).

Críticas y accionables:
- los aprendizajes clave;
- qué tan robustos son los resultados bajo distintos supuestos (con lo de los capítulos 7 y 8);
- las fortalezas del enfoque;
- las limitaciones que hay que resolver;
- las implicancias prácticas para RED;
- líneas concretas de mejora hacia la entrega final.

Cada conclusión se apoya en una cifra del capítulo 7 u 8.

### Capítulo 10. Pasos futuros — 1,5 págs.

**Rúbrica:** Pasos futuros (15).

**10.1 Avance contra la Carta Gantt del informe 1:** qué se cumplió, qué se reemplazó y qué quedó pendiente, con las dificultades encontradas. Sale de la lámina 21.

**10.2 Carta Gantt nueva** hasta la entrega final, con **hitos, dependencias y responsables**:

| Actividad | Fecha |
|---|---|
| Escalar a la red completa | 19 al 25-oct |
| Extender a sábado y domingo o festivo | 26-oct al 1-nov |
| Ampliar el análisis de sensibilidad | 9 al 15-nov |
| Caso base para la red completa | por fijar |
| Exigir estado de carga al final del día | por fijar |

- La columna de responsables la llena el grupo.
- Las fechas de la Entrega 3 y del informe final están por confirmar.
- La semana del 2 al 8-nov no tiene nada asignado en la lámina 22: hay que decidir qué va ahí.

### Referencias

APA con `apacite`. Antes de citar cada referencia nueva, se verifica que exista y que sus datos estén bien.

### Anexos (no cuentan en las 30 páginas)

- **A. Notación:** tabla completa de conjuntos, parámetros y variables del capítulo 5.
- **B. Correcciones respecto del informe 1 y de la presentación:** tabla «comentario → dónde se atendió» (sección 6 de este esquema).
- **C. Barrido de presupuesto:** las 15 corridas.
- **D. Parámetros del escenario:** sale de `metodo_hibrido/instancia_212/escenario.json`.
- **Declaración de uso de IA:** al final, con las firmas.

## 5. Cifras y figuras: de dónde sale cada una

Scripts en `08-entrega2/informe2/scripts/`:
- `cifras.py` genera `cifras.tex`, con una macro por cifra (por ejemplo `\BusesCasoBase`).
- `figuras.py` genera los PDF de `figures/`.

Los dos leen solo los archivos de esta tabla y fallan con un error claro si falta alguno o si un resumen no viene marcado como verificado.

| Cifra o figura | Archivo fuente |
|---|---|
| KPIs del refinado | `metodo_hibrido/resultados/mejor_20261006_refinamiento/04_final/resumen.json` |
| Etapas del refinado | `.../mejor_20261006_refinamiento/comparacion_etapas.csv` y `.../mejor_20261006_600/comparacion_etapas.csv` |
| Energía por hora y tarifa | `.../04_final/recargas.csv` y `metodo_hibrido/instancia_212/escenario.json` (`tarifas`) |
| Energía al final del día | `.../04_final/jornadas.csv` y el `jornadas.csv` del miope |
| KPIs del caso base miope | `CODIGO apstone/output/tres_fases/muestra_212_caso_base/resumen.json` (después de la verificación 1) |
| Sensibilidad al umbral | `CODIGO apstone/output/tres_fases/muestra_212_caso_base_{0.2,0.3,0.5}/resumen.json` |
| Caso base sin recargas (párrafo) | `caso_base_simple_gurobi/corrida_gurobi/resumen.json` |
| Barrido de presupuesto | `metodo_hibrido/resultados/presupuesto/registro.csv` |
| Corridas por hora y comparación muestra vs. red | `metodo_hibrido/instancia_212/corridas.csv` y las corridas de la red completa (ubicar la fuente) |
| Cotas (simultaneidad y Fase 1) | `metodo_hibrido/instancia_212/corridas.csv` y `CODIGO apstone/output/tres_fases/muestra_212/` (verificación 3) |

## 6. Correcciones y dónde se atienden (base del Anexo B)

**Corrección del informe 1** (PDF anotado; pN = página del PDF)

| Comentario | Dónde se atiende |
|---|---|
| p7: «corrida» es una palabra extraña; definirla antes de usarla | Glosario 2.1 |
| p8: no hace falta discutir los 1.200 buses | Cap. 1 y 2.2: la flota es una decisión del modelo |
| p8: explicar las siglas | Regla global y glosario |
| p9: de nuevo las siglas | Regla global |
| p9: objetivo incompleto (los 5 E, los horarios) | Cap. 1, objetivo completo |
| p10: «distancia de qué» | 2.3 |
| p11: «energía MWh», ¿de todas las corridas del día? | 2.3, unidad y alcance explícitos |
| p11: mostrar el gráfico de corridas a lo largo del día | Figura de 2.3 |
| p13: los KPIs se comparan, no son valores fijos | 2.5 y cap. 7 |
| p14: «costo total» y «costo energético» como nombres | 2.5 |
| p14: ¿por qué solo comparan el costo energético? | 2.5 y 7.2, desglose completo |
| p16: ¿corridas y viajes son lo mismo? | Glosario: solo «corrida» |
| p19: ¿qué son los «terminales convencionales»? | 2.4 y 3.4: se explica qué son los T |
| p20: ¿baterías lineales por supuesto o por el método? | 3.4 y 8.1 |
| p22: erratas («una», «existen») | El texto se escribe nuevo; se revisa la ortografía |
| Restos de la plantilla («First Appendix», «An Interesting Short Story») | Regla de forma 1 |
| Gantt sin responsables, hitos ni dependencias | 10.2 |
| Declaración de IA marcada «NO» | Al final, marcada SÍ con el detalle |

**Feedback de la presentación del 8-oct:** cada comentario está ligado a su capítulo en la sección 4, en las líneas «Atiende».

## 7. Verificaciones antes de usar las cifras

1. **Pasar el caso base miope por el auditor del híbrido** (`metodo_hibrido/verificar.py`). El auditor recibe `schedules`, pero el miope no tiene `planes.json`: hay que reconstruir los planes desde su `actividades.csv`. Si aparece una diferencia, se informa antes de seguir. Si no se puede, se declara que se auditó con `tres_fases/verificar.py`.
2. **Origen de T01–T04 y por qué se excluye Los Acacios.** No están en `depots.csv`, que solo trae los 5 E. Hay que rastrearlos en la preparación de datos de la fase 1 (`CODIGO apstone/fase1/`, hoy solo en iCloud).
3. **Fuente de las cotas.** Recalcular la de simultaneidad (3.398) desde `corridas.csv` y ubicar el piso de la Fase 1 (3.561 buses, USD 1.278.245) en `output/tres_fases/muestra_212/fase1/`.
4. **Etapas intermedias del refinado.** Leer `mejor_20261006_600/comparacion_etapas.csv` para la fila de parejas.
5. **Costo de espera a 0,03 USD/min** para el refinado y para el miope.
6. **Referencias nuevas:** confirmar autor, año y publicación de cada una.
7. **Conexiones factibles** de la instancia de 212 rutas, para dar el tamaño del modelo completo en 5.1.
8. **Archivos solo en iCloud** (`compressed,dataless`): la guía de la Entrega 2, `CODIGO apstone/tres_fases/README.md` y `CODIGO apstone/fase1/MODELO_MATEMATICO.md`. Hay que marcar `Proyecto` como «Mantener descargado».

## 8. Riesgos

- **Plazo:** quedan tres días. Se redacta primero lo que tiene más puntos y más material.
- **El caso base cambia respecto de la presentación.** El grupo tiene que estar de acuerdo, y las cifras del informe no van a calzar con el deck. Se explica en el Anexo B.
- **Energía no comparable** entre el miope y el refinado (252.529 contra 26.432 kWh). Se resuelve con el costo ajustado de 7.4. Si el ajuste cambia el orden de los planes, se informa.
- **iCloud** puede colgar lecturas o compilaciones. Se revisa con `ls -lO` antes de leer.

## 9. Orden de trabajo

| Cuándo | Qué |
|---|---|
| 13-oct (noche) | Este esquema; copiar la plantilla a `informe2/`; scripts de cifras; verificaciones 1, 3 y 4 |
| 14-oct | Capítulos 4, 7 y 6 |
| 15-oct (mañana) | Capítulos 2, 8, 5 y 3 |
| 15-oct (tarde) | Capítulos 1, 9 y 10; resumen; anexos. **Borrador completo al grupo** |
| 16-oct | Correcciones del grupo, firmas y entrega |

## 10. Pendientes del grupo

- Acordar el cambio de caso base (sección 2).
- Llenar los responsables de la Carta Gantt y fijar las fechas de la Entrega 3 y del informe final.
- Crear el repositorio privado de GitHub y compartirlo con el ayudante y el profesor (yo preparo la carpeta y el README).
- Revisar y firmar la declaración de uso de IA.
- Subir el informe al Overleaf del grupo, si se va a compilar ahí.
