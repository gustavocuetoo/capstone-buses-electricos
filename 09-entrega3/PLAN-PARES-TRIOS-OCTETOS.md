# Plan corto · Pares y tríos contra grupos más grandes (hasta octetos)

Grupo 29 · **reprogramado el lunes 9 de noviembre:** del lunes 9 al **jueves 12**, para tener resultados antes de congelar cifras el domingo 15. La fecha de la presentación (jueves 19) sigue sin confirmar.

> **Estado al 9-nov.** Del calendario original (4 al 8 de noviembre) no se alcanzó a hacer nada. La licencia académica de Gurobi venció el 24-sep-2025 y **se renueva el miércoles 11**. Todo el estudio se hace con Gurobi. **HiGHS 1.15.1** quedó instalado en `.venv-optimizacion` solo como respaldo.
>
> **Cómo funciona hoy la mejora por grupos** (`metodo_hibrido/intercambios.py` y `trios.py`): primero se proponen repartos de viajes con reglas fijas (absorber un bus en los otros, rotar las colas) y después un solo modelo decide las recargas del grupo (`conjunta.py`). Ese modelo acepta como máximo 3 buses y está escrito solo para Gurobi. Generalizarlo a 4, 5 y 8 buses es el trabajo más grande del plan.

## La idea, en simple

Nuestro programa hace primero un plan rápido y después lo mejora por grupos: toma 2 buses (pares) o 3 buses (tríos), les reparte de nuevo los viajes y deja el cambio si el costo baja.

La pregunta natural es **¿por qué grupos de 2 y 3, y no de 4, 5 u 8?**

- **Un grupo más grande** ve más combinaciones, así que en cada intento puede encontrar ahorros que un par no ve.
- **Pero cada intento es mucho más lento,** así que en el mismo tiempo se alcanzan a revisar muchos menos grupos.

La comparación responde cuál de las dos cosas pesa más. Si en el mismo tiempo los grupos grandes no ganan, queda demostrado que pares y tríos son la mejor elección. Si ganan, lo sabremos a tiempo para cambiar.

## Contra qué nos comparamos

| Método | Qué hace |
|---|---|
| Solo el plan rápido | Sin mejorar nada: el piso |
| Solo pares | Grupos de 2 |
| **Pares y tríos (el nuestro)** | Grupos de 2 y luego de 3 |
| **Cuartetos** | Grupos de 4 buses |
| **Quintetos** | Grupos de 5 buses |
| **Octetos** | Grupos de 8 buses |
| Mezcla creciente | Parte con pares y sube a 3, 4, 5 y 8 solo cuando el grupo anterior ya no encuentra ahorros |
| La respuesta perfecta | Resuelve todo sin atajos. Solo funciona en casos chicos y sirve de regla para medir a todos |

**Cómo se arma cada grupo:** con buses que se pueden cambiar viajes entre sí, es decir, del mismo sector y con horarios que se toquen. Se prueban dos formas de elegirlos: los buses más parecidos y al azar.

**Para que sea justo:** los mismos casos, el mismo tiempo, el mismo computador, el mismo cálculo de costo y el mismo revisor automático para todos.

**Ojo con la licencia:** la gratuita de Gurobi solo acepta problemas pequeños, y un octeto probablemente se pasa del límite. Hay dos salidas: un programa gratuito sin límite, o pedir la licencia académica de la universidad.

## Checklist

### Lunes 9 · Investigar y preparar
- [~] **Investigar** quién más mejora planes de buses por grupos (de 2, 3 o más), qué tamaño de grupo usan y por qué. Primera pasada en `octetos/INVESTIGACION.md`; falta leer completo Limmer et al. (2023)
- [ ] Averiguar cómo se demuestra en los estudios que un método es bueno: contra qué se compara y qué se mide
- [ ] Revisar cada fuente (autores, año, revista) antes de citarla
- [x] Resolver la licencia. **Decisión del 9-nov: todo con Gurobi.** La licencia académica se renueva el miércoles 11. Hasta entonces los programas se prueban en los casos muy chicos, que caben en la licencia gratuita. HiGHS quedó instalado solo como respaldo si la licencia no llega
- [x] Crear los **casos muy chicos** (1 ruta, unos 6), donde se puede encontrar la respuesta perfecta. Hay 6, de 24 a 26 corridas, en `octetos/casos/` (script `octetos/crear_casos.py`, 5 pruebas). **Ojo:** en estos casos ningún bus necesita recargar. En el 264N el caso base ya usa el mínimo de buses, pero en el J22 los tríos bajan de 4 a 3 buses (−17 %). Con 4 a 10 buses no alcanzan a formarse grupos de 5 u 8 (0 intentos): sirven para comparar contra la respuesta perfecta, no para probar octetos
- [x] Crear los **casos chicos** (2 a 4 rutas, unos 6). Hay 6, de 84 a 157 corridas. **Prueba del 9-nov:** en el caso de 152 corridas, los tríos ya se pasan del límite de la licencia gratuita de Gurobi. Llevar el modelo de recargas a HiGHS es obligatorio, incluso para comparar pares y tríos

### Martes 10 · Programas
- [x] Generalizar la mejora para que acepte grupos de cualquier tamaño (2, 3, 4, 5 y 8), usando la misma pieza que hoy resuelve pares y tríos. Hecho el 9-nov en `metodo_hibrido/grupos.py`; `conjunta.py` acepta hasta 8 buses. Las 27 pruebas pasan, incluida la que comprueba que con k=3 el resultado es idéntico al de los tríos
- [x] Las dos formas de elegir grupos: los buses más parecidos y al azar (con semilla fija, para repetir el resultado)
- [x] La mezcla creciente (2 → 3 → 4 → 5 → 8): `metodo_hibrido/creciente.py`, con 3 pruebas. Vuelve a pares cada vez que un tamaño mejora
- [x] La respuesta perfecta para los casos chicos: `metodo_hibrido/exacto.py`, con 3 pruebas. Usa el mismo costo y el mismo catálogo de recargas que los grupos. **Solo es viable en los casos muy chicos** (4 mil a 37 mil enlaces con recarga); en los chicos hay de 400 mil a 1,5 millones. Con la licencia gratuita no cabe ni en los muy chicos
- [x] Un programa que corra todos los métodos en todos los casos y junte los resultados en una tabla: `octetos/correr_metodos.py`, con 2 pruebas. Escribe fila por fila, retoma con `--continuar` y anota los errores sin detenerse
- [x] Pruebas automáticas, y confirmar que pares y tríos siguen dando exactamente lo mismo que antes. Son 40 pruebas en total, y con k=3 el resultado es idéntico a los tríos

### Miércoles 11 · Correr

Comandos, desde la raíz del proyecto y con la licencia académica cargada:

```bash
.venv-optimizacion/bin/python 09-entrega3/octetos/correr_metodos.py --presupuestos 60 120 --presupuesto-exacta 1800 --salida 09-entrega3/octetos/resultados/casos_chicos.csv
```

```bash
.venv-optimizacion/bin/python 09-entrega3/octetos/correr_metodos.py --instancias metodo_hibrido/instancia_212 --metodos solo_base pares pares_trios cuartetos quintetos octetos mezcla --presupuestos 300 600 1200 --salida 09-entrega3/octetos/resultados/muestra_212.csv
```

Si una corrida se corta, se repite el mismo comando con `--continuar`. **Ensayo del 9-nov con la licencia gratuita (J22, 20 s):** solo pares llega a 3 buses y USD 1.044,58; tríos o cuartetos solos, a 3 buses y USD 1.088,46; los quintetos y octetos no alcanzan a formar grupos.
- [x] **Antes de correr:** renovar la licencia académica (hecho el 10-nov; todo corre con `octetos/correr_todo.sh`). Prueba del 9-nov: con la gratuita, hasta los tríos fallan en un caso muy chico y todos los tamaños fallan en el caso chico de 84 corridas. La licencia restringida del entorno vence el 23-nov
- [ ] Casos muy chicos y chicos: todos los métodos, incluida la respuesta perfecta
- [ ] **Red completa (417 rutas):** el día laboral con todos los métodos (incluidos los tríos solos, agregados el 10-nov por lo de chico_02) y 10, 20 y 40 minutos decide el método (regla en `octetos/elegir_metodo.py`: gana el más barato con el mismo tiempo en la mayoría de los tiempos; el 11-nov se quitó el umbral del 1 %). Sábado y domingo se corren solo con el elegido. Se guardan los planes (`resultados/planes_417_{L,S,D}/`). Termina ~mié 11 en la noche
- [ ] **Ojo (chico_02, 10-nov):** pares+tríos se queda en 30 buses y tríos solos llegan a 29 (−2,6 %): los pares dejan un óptimo local del que los tríos no salen. Revisar si pasa en la red completa
- [ ] Pasar cada resultado por el revisor automático. Lo que no pasa no se usa
- [ ] *Si alcanza, de noche:* la red completa con el mejor grupo grande, para compararla con la nuestra

### Jueves 12 · Conclusión
- [ ] Una tabla por caso y método: costo, buses, tiempo y distancia a la respuesta perfecta
- [ ] Un gráfico: el ahorro según el tamaño del grupo, con el mismo tiempo
- [ ] Un gráfico: cuánto demora un intento según el tamaño del grupo
- [ ] Comprobar si las diferencias son reales o casualidad
- [ ] Una página con la conclusión y lo que dice la investigación, lista para el informe y para una lámina

## Qué tiene que mostrar el jueves 12 para decir «pares y tríos es la mejor elección»
- Con el mismo tiempo, ni los cuartetos, ni los quintetos, ni los octetos, ni la mezcla creciente son más de 1 % más baratos.
- En los casos chicos, quedamos cerca de la respuesta perfecta (idealmente a menos de 2 %).
- Los tríos mejoran lo que dejan los pares.

Si algo de esto no se cumple, el jueves 12 decidimos con los datos en la mano si cambiamos el método.
