# Investigación · ¿De qué tamaño conviene que sean los grupos?

Primera pasada, lunes 9 de noviembre de 2026. Las fichas (autores, año, revista, DOI) se revisaron en los registros bibliográficos; los textos completos todavía no.

## Lo que dice la literatura, en simple

1. **El dilema ya tiene nombre.** En la búsqueda local, un vecindario más grande da mejores soluciones en cada intento, pero cada intento cuesta más. Un vecindario grande solo conviene si se puede revisar rápido. Es la tesis central de Ahuja et al. (2002), y es exactamente nuestra pregunta: pares y tríos contra cuartetos, quintetos y octetos.
2. **La «mezcla creciente» es una idea conocida.** Pasar a un vecindario más grande solo cuando el actual deja de encontrar mejoras es la búsqueda de vecindario variable (VNS) de Mladenović y Hansen (1997). Si la usamos, la citamos así.
3. **Lo más parecido a nuestro método en buses eléctricos** es Limmer, Varga y Raidl (2023): sacan una parte del plan y la reparan con un modelo entero (MILP), igual que nuestro modelo conjunto de recargas. Prueban tres formas de elegir qué sacar. **Falta leer el texto completo** para saber cuántos vehículos sacan por intento.
4. **En los trabajos de destruir y reparar, el tamaño del grupo se ajusta, no se deduce.** Se suele fijar como fracción de la solución y se calibra con experimentos: grupos chicos refinan y grupos grandes exploran. No encontramos ningún estudio que fije «2 o 3 buses» como regla. Por eso nuestra comparación aporta algo propio.

## Fuentes revisadas

| Fuente | Qué aporta | Estado |
|---|---|---|
| Ahuja, R. K., Ergun, Ö., Orlin, J. B. y Punnen, A. P. (2002). A survey of very large-scale neighborhood search techniques. *Discrete Applied Mathematics*, 123(1–3), 75–102. | El dilema entre tamaño del vecindario y tiempo por intento | Ficha revisada ([dblp](https://dblp.uni-trier.de/rec/journals/dam/AhujaEOP02.html)) |
| Mladenović, N. y Hansen, P. (1997). Variable neighborhood search. *Computers & Operations Research*, 24(11), 1097–1100. doi:10.1016/S0305-0548(97)00031-2 | Agrandar el vecindario solo cuando el actual se agota (nuestra mezcla creciente) | Ficha revisada ([dblp](https://dblp.org/rec/journals/cor/MladenovicH97)) |
| Limmer, S., Varga, J. y Raidl, G. R. (2023). Large Neighborhood Search for Electric Vehicle Fleet Scheduling. *Energies*, 16(12), 4576. doi:10.3390/en16124576 | Destruir y reparar con un MILP en flotas eléctricas; tres formas de destruir | Ficha revisada ([MDPI](https://mdpi.com/1996-1073/16/12/4576)); **falta el texto completo** |
| Varga, J. et al. (2022). *IEEE Access*. Flota eléctrica compartida con Benders y una búsqueda de vecindario variable general (GVNS) | VNS aplicada a recargas y asignación | Encontrado ([TU Wien](https://repositum.tuwien.at/bitstream/20.500.12708/142164/1/Varga-2022-IEEE%20Access-vor.pdf)); falta la ficha completa |

## Pendiente

- Leer Limmer et al. (2023), que es de acceso abierto: cuántos vehículos sacan por intento, cómo los eligen y contra qué comparan.
- Buscar un trabajo de programación de buses (no de ruteo) que compare tamaños de grupo con el mismo tiempo de cómputo.
- Cómo se demuestra que un método es bueno: contra la cota o la respuesta exacta en casos chicos, con el mismo tiempo y varias semillas. Ese es el diseño de nuestro plan; falta una cita que lo respalde.
