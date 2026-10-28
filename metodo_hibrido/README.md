# Método híbrido: construcción cronológica y optimización local

**Ensayo completado:** 212 rutas, 33.220 corridas, **3.973 buses y USD 1.404.610,25**. Respecto del caso base: 41 buses menos y USD 10.738,45 de ahorro (0,76%). Se aprobaron 22 pruebas y la validación cruzada con los datos y auditor originales. Véase [RESULTADOS.md](RESULTADOS.md) para comparación, tiempos y límites.

Esta carpeta contiene una metodología separada del prototipo de tres fases. No importa código de `tres_fases` ni de `fase1`; no ejecuta flujo agregado ni descomposición. Mantiene copias propias de los datos de las 212 rutas y exporta exclusivamente dentro de esta carpeta. Comparte únicamente el entorno de dependencias del proyecto (`.deps`).

## Qué se implementó

1. Construcción cronológica independiente, adaptada del paquete del compañero. Revisa buses del mismo sector, comprueba horarios y energía, considera carga mínima y reutiliza el bus factible de menor distancia vacía. Solo incorpora otro cuando no encuentra candidato. Asigna estacionamiento final después de reservar las cargas.
2. Mejora por parejas: fusión, intercambio de tramos finales y traslado de servicios individuales.
3. Mejora por tríos: reparto de una jornada entre otras dos y rotación de tramos finales.
4. Para las secuencias propuestas, un MILP local decide conjuntamente recargas y terminales; mantiene fijas las demás jornadas. Los servicios se reasignan por la búsqueda, no mediante variables globales bus-servicio.
5. Auditoría independiente de cobertura, horarios, continuidad espacial, SOC, recursos compartidos y costos. Solo se aceptan reducciones estrictas del costo. Cada etapa trabaja sobre una copia y se conserva la anterior si no mejora o si su resultado falla la auditoría.

El resultado del caso base se conserva siempre en `01_caso_base`. Un error de ejecución detiene el ensayo y genera `fallo.json`; no se confunde un fallo con una solución final. Las etapas ya exportadas permanecen disponibles. La comparación completa solo existe después de auditar la salida final.

## Decisiones para controlar el esfuerzo

Se priorizan jornadas cortas y vecinos compatibles, con ocho vecinos, tres alternativas por grupo, hasta tres rondas y dos segundos por MILP. Parejas y tríos reciben 120 segundos cada uno por defecto. Se mantiene un catálogo acotado de ventanas de carga y una sola visita a E por hueco. La generación de candidatos y auditoría pueden exceder ligeramente el presupuesto; este no es un límite estricto del proceso completo.

Esta primera implementación mantiene los motores locales de la versión comprobada del proyecto. El experimento mide el cambio de solución inicial; no cambia simultáneamente las capacidades, los sectores o las reglas de energía. No garantiza una mejora estricta ni óptimo global; la aceptación garantiza que una salida final completada no cueste más que su caso base auditado.

## Supuestos conservados

- 212 rutas y sus 33.220 corridas laborales, mismas distancias dirigidas y horarios.
- Horizonte de -7.086 a 98.901 segundos respecto de medianoche; SOC inicial 100% en el inicio común, sin reinicio a medianoche.
- Batería 350 kWh, reserva 35 kWh, consumo 1,4 kWh/km; 18 km/h exclusivamente en vacío.
- Carga hasta 180 kW, bloques de cinco minutos, carga parcial. Sin condición final adicional al mínimo.
- USD 250/bus, USD 0,5/km, tarifas originales y USD 5/sesión. Esperas y estacionamiento sin costo.
- Cinco E originales: plazas físicas y conexiones de 150, 180, 120, 100 y 150, como en los archivos. Recursos separados y compartidos entre sectores.
- T01 Pajaritos/Las Araucarias, T02 Miguel Mujica, T03 El Salto y T04 El Roble: estacionamiento ilimitado y sin carga. Los Acacios excluido.
- Servicios de un solo sector por jornada. Cualquier sector puede utilizar cualquiera de los cinco E.
- Día aislado con energía inicial dada y sin recuperación final obligatoria. Sin nuevos supuestos de realismo energético o temporal.

## Archivos

| Archivo | Función |
|---|---|
| `ejecutar.py` | Entrada única; construye, mejora, audita, protege resultados y exporta la comparación. |
| `caso_base.py` | Construcción cronológica del compañero y carga de la instancia normalizada. |
| `calendario.py` | Calendario numérico de ocupación y funciones para crear actividades. No construye cadenas de fase 2. |
| `recarga.py` | Catálogo de cargas, reservas reversibles, cálculo de costo y modelo de una jornada. |
| `conjunta.py` | MILP de recarga y terminales de una a tres secuencias. |
| `intercambios.py` | Búsqueda de mejoras entre dos jornadas. |
| `trios.py` | Búsqueda entre tres jornadas. |
| `verificar.py` | Auditoría de planes completos. |
| `test_caso_base.py`, `test_hibrido.py` | Pruebas del constructor, protección del incumbente y mejoras locales. |
| `instancia_212/` | Datos autocontenidos: escenario, corridas y distancias. |
| `procedencia.json` | Fuentes y huellas de los módulos adaptados; no son dependencias de ejecución. |

El campo histórico `cadena_fase2` permanece por compatibilidad del formato; su valor inicial es `CASO_BASE`. No indica que esta metodología haya ejecutado la fase 2.

## Ejecución

Desde la raíz de Capstone, con Python y Gurobi 12 disponibles:

```powershell
python metodo_hibrido/ejecutar.py
```

La salida predeterminada es `metodo_hibrido/resultados/ensayo_212`. No se sobrescribe una carpeta existente. Para repetir:

```powershell
python metodo_hibrido/ejecutar.py --salida metodo_hibrido/resultados/ensayo_212_repetido
```

Opciones: `--presupuesto-pares`, `--presupuesto-trios`, `--limite-local`, `--vecinos`, `--alternativas`, `--rondas` y `--instancia`. Un presupuesto cero omite esa búsqueda. La interfaz no permite modificar los coeficientes físicos sin adaptar coherentemente el código y su auditoría.

```powershell
python -m unittest metodo_hibrido.test_hibrido metodo_hibrido.test_caso_base
```

Cada ejecución guarda configuración y huellas de entradas y código, la base, las etapas aceptadas y el resultado final. `comparacion.json` informa costo, flota y tiempos; `comparacion_etapas.csv` permite comparar etapas. Cada etapa contiene jornadas, actividades con energía reconstruida, recargas y planes completos. Las búsquedas también guardan todos sus intentos evaluados.

## Interpretación

La referencia de calidad es el caso base de 4.014 buses y USD 1.415.348,70. El prototipo previo de tres fases obtuvo 4.175 buses y USD 1.459.572,80. El ahorro atribuible a esta búsqueda híbrida debe medirse respecto del primero. Los resultados medidos se documentan en `RESULTADOS.md` al completar el ensayo. Más costo ahorrado no implica necesariamente menos buses, ni menos compra de electricidad implica igual reducción del consumo.
