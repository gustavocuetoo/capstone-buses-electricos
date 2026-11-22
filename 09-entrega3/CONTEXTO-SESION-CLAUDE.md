# Contexto para continuar con Claude Code (22-nov-2026)

Resumen de una sesión larga con Claude (informe 2, comentarios, reunión con el profesor y revisión del código).
Sirve para que una sesión nueva de Claude Code parta con el mismo contexto. Lee primero este archivo y
`09-entrega3/PLAN-ENTREGA3.md`.

## Estado de los resultados (día laboral, red completa: 417 rutas, 64.502 corridas)

| Plan | Buses | Costo (USD/día) | Fuente |
|---|---|---|---|
| Caso base miope por ruta | 8.684 | 3.062.717 | `codigo/output/tres_fases/red_417_L_caso_base/` |
| Plan inicial (construcción) | 7.570 | 2.677.608 | `09-entrega3/octetos/resultados/red_completa_417_L.csv` |
| Híbrido, corrida del 6-oct | 7.427 | 2.638.494 | `metodo_hibrido/resultados/completa_417_20261006/04_final/` |
| Cuartetos al azar, 40 min (media 3 semillas) | 7.351 | 2.617.469 | `red_completa_417_L.csv` (solo resumen, sin jornadas ni recargas) |

- Contra el caso base, los cuartetos ahorran 15,4 % de buses y 14,5 % de costo. El −2,25 % del PDF de
  metodología es solo la búsqueda sobre el plan inicial.
- Cota de simultaneidad: 6.601 buses (11,96 % por debajo de la corrida del 6-oct). La relajación de flujo
  (Fase 1) en la red completa sigue pendiente: necesita la licencia académica de Gurobi (la de pip rechaza
  modelos de más de 2.000 variables).
- Costo del 6-oct: buses 70,4 %, km 28,9 %, energía 0,4 % (USD 11.605), sesiones 0,3 %.
- Ocupación (verificación del 6-oct): las plazas llegan al 100 % en los 5 electroterminales; las cargas
  simultáneas nunca pasan de 21 a 45 conexiones. El recurso escaso son las plazas, no los cargadores.

## Casos chicos contra el óptimo exacto

- 5 casos (84 a 157 corridas): los cuartetos quedan a 0,13 % del óptimo en promedio y con los mismos buses.
- Ni el óptimo ni la heurística recargan (0 sesiones, 0 kWh en `casos_chicos*.csv`). La diferencia de costo
  es solo km en vacío. Las notas de Gemini de la reunión dicen «mayores costos por recarga»: es incorrecto.
- Casos medianos (200 a 405 corridas) ya creados en `09-entrega3/octetos/casos/`; necesitan ≥16 GB de RAM.

## Por qué pierden los octetos (respuesta al profesor)

En `red_completa_417_L.csv` los octetos terminan solos en 7 a 9 min con `sin_mejoras_en_vecindario`, con
~2.000 intentos tanto con 10 como con 40 min. No es falta de tiempo: el vecindario implementado se agota.
Causas en el código (`metodo_hibrido/grupos.py`, `09-entrega3/octetos/correr_metodos.py`):

1. `local_limit=2.`: el MILP de recargas de cada grupo tiene 2 s, sea de 4 o de 8 buses.
2. `width=4` en `propuestas`: el haz de reparto guarda 4 estados sin importar cuántos receptores haya, y los
   ordena por km y balance, sin mirar batería.
3. `neighbors=8` en `_companeros`: cada donante prueba C(8, k−1) grupos: 56 en cuartetos, 8 en octetos.

Cada jugada elimina como máximo un bus (absorción de k a k−1). Los receptores nunca sueltan sus propios
viajes, por eso un octeto implementado no contiene en la práctica a un cuarteto.
Experimento propuesto: escalar `local_limit`, `width` y el número de grupos por donante con k.

## Lo que pidió el profesor (reunión del 17-nov)

1. Escalar el MILP exacto (hasta ~10 rutas) y ubicar caso base, pares, tríos y cuartetos contra el óptimo.
2. Casos más difíciles: batería reducida (`bateria_kwh` en `escenario.json`) o más demanda por bus.
3. Ocupación de cada electroterminal durante el día y desbalance entre sectores (65 a 117 rutas).
4. Explicar si la pérdida de los octetos es de tiempo o algorítmica (ver arriba).
5. Calcular todos los KPI definidos y una sensibilidad con perspectiva de gestión, no obviedades.
6. Diagrama y GIF de la metodología; contar la metodología actual sin los pivotes intermedios.

## Tareas que no dependen de la elección de cuartetos u octetos

Pueden hacerse con los datos del repositorio, sin Gurobi:

1. Script de KPI para cualquier carpeta de plan (`jornadas.csv`, `recargas.csv`, `resumen.json`), para
   caso base y método en L, S y D.
2. Uso de cargadores por electroterminal y bloque de 5 min desde `recargas.csv`: buses cargando, MW y kWh;
   mapa de calor hora × terminal; comparación entre sectores. La ocupación de plazas necesita
   `actividades.csv` (no está en GitHub; se regenera con `01-datos/`).
3. Generador de casos con recarga forzada (copiar casos y bajar `bateria_kwh`).
4. Generador de escenarios de sensibilidad (tabla 6.1 de `PLAN-ENTREGA3.md`).

Necesitan Gurobi con licencia o los datos completos: cota por relajación de flujo, casos medianos exactos,
Monte Carlo de atrasos y ocupación de plazas.

## Pendientes del informe

- El informe 2 enlaza `nfariasl/capstone-grupo29` (privado); el repositorio público es
  `nfariasl/capstone-buses-electricos`.
- Este fork (`gustavocuetoo/capstone-buses-electricos`) debe volver al repositorio del grupo mediante
  pull request, para que el informe enlace un solo repositorio.
