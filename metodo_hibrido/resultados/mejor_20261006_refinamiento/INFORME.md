# Mejor solución factible encontrada — 6 de octubre de 2026

**3.873 buses; USD 1.374.631,70 para el día modelado.**

212 rutas y 33.220 corridas cubiertas exactamente una vez. Se conservan los parámetros y restricciones originales del híbrido.

| Resultado | Buses | Costo USD |
|---|---:|---:|
| Caso base reconstruido | 4.014 | 1.415.348,70 |
| Mejor corrida previa (B240_r3) | 3.902 | 1.383.918,03 |
| Primera búsqueda, parejas y tríos de 600 s | 3.884 | 1.378.806,94 |
| Refinamiento final, parejas y tríos de 240 s | 3.873 | 1.374.631,70 |

Respecto del caso base: **USD 40.716,99 de ahorro (2,88%) y 141 buses menos**.
Respecto de la mejor corrida previa: USD 9.286,33 menos.

## Composición del costo

| Componente | USD |
|---|---:|
| Buses | 968.250,00 |
| Kilómetros | 399.329,28 |
| Electricidad | 4.382,43 |
| Sesiones de recarga | 2.670,00 |

Kilómetros totales: 798.658,55; energía comprada: 26.432,41 kWh; sesiones: 534.

## Factibilidad y alcance

Auditoría del plan exportado aprobada y costos de los CSV conciliados. Se aprobaron 22 pruebas del constructor, protección del incumbente y modelos locales.
Se comprobaron cobertura, identidad y horarios de servicios, sector único por jornada, continuidad temporal y espacial, balance de energía, reserva de batería y capacidades compartidas de estacionamiento y carga.

Tiempo total medido de ambas búsquedas completas: 28,64 minutos. Primera búsqueda: 600 s por parejas y 600 s por tríos, 8 vecinos y 3 alternativas; refinamiento: 240 s por etapa, 12 vecinos y 5 alternativas. Hasta 30 rondas y 2 s por MILP local en ambas.
Se enviaron 60.440 modelos locales; 184 excedieron el tamaño de la licencia restringida y se descartaron.

**Es la mejor solución encontrada en estas búsquedas; no se demostró optimalidad global.** Se mantiene el supuesto de batería inicialmente llena y sin reposición final obligatoria, para un día aislado.

## Archivos

- `04_final/planes.json`: plan completo por bus.
- `04_final/jornadas.csv`: asignaciones y costos por bus.
- `04_final/actividades.csv`: actividades y energía reconstruida.
- `04_final/recargas.csv`: calendario de recargas.
- `verificacion_final.json`: auditoría, comparación completa y huellas de entregables.
- `comparacion.json` y carpetas por etapa: evolución del refinamiento.
- `../mejor_20261006_600/`: caso base reconstruido y primera búsqueda.
