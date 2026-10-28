import json, re, csv, statistics, html
from pathlib import Path

ROOT=Path('/Users/anitasepulveda/Desktop/Universidad/SEMESTRES/SEMESTRE 8/Capstone/Proyecto')
OUT=ROOT/'08-entrega2/actualizacion_canva_20261006'
original=json.loads((OUT/'original.json').read_text())
groups={n:[r for r in original['richtexts'] if r['page_index']==n] for n in range(1,29)}
ops={}
def change(n,i,new):
 r=groups[n][i]; old=''.join(z.get('text','') for z in r['regions'])
 if new!=old:
  ops.setdefault(n,[]).append(dict(type='find_and_replace_text',element_id=r['element_id'],find_text=old,replace_text=new))
def sub(n,i,a,b):
 old=''.join(z.get('text','') for z in groups[n][i]['regions'])
 assert a in old,(n,i,a)
 change(n,i,old.replace(a,b))

change(4,6,'≈ 70 %')
change(4,7,'del costo diario de la solución final es flota (USD 968.250 de 1.374.632):')
change(4,8,'Flota: USD 250 por bus utilizado — 968.250\nKilómetros: USD 0,5 por km — 399.329\nElectricidad: según tarifa horaria — 4.382\nSesiones de carga: USD 5 cada una — 2.670')
change(11,17,'Absorbe o rota tramos entre tres jornadas; repite parejas y tríos para refinar el plan')
change(16,6,'Comprueba horario, batería y retorno en cada asignación: no hay que reparar después.\n\nMejora con MILP pequeños: Gurobi decide recargas y terminales de 2 a 3 jornadas.\n\nSolo acepta cambios factibles y más baratos: nunca empeora la solución.\n\nAuditoría del plan exportado: 33.220 corridas exactas, 22 pruebas y costos conciliados.')
change(16,8,'Conserva lo útil del Ciclo 1: modelos locales de recarga y auditoría. En esta instancia produjo una solución factible auditada.\n\nCon las mismas corridas: −302 buses (−7,23 %) y −USD 84.941 (−5,82 %) frente al prototipo anterior.\n\nLa construcción es el despacho secuencial clásico (Bodin et al., 1978), adaptado a baterías.\n\n')
change(17,6,'buscar_mejor.py')
change(17,7,'Coordina búsqueda, refinamiento y auditorías')
change(17,25,'Verificación: 22 pruebas del híbrido (14 del constructor, 8 de integración), auditoría del plan exportado y conciliación de costos con los CSV. Caso base intacto.')
sub(17,27,'220 rutas.','212 rutas.')
change(17,31,'Se toman 2 jornadas en un mismo sector y se prueba fusionar e intercambiar.\n\nSe obtienen mejoras: 3.989 buses y 1.403.068 USD')
change(17,32,'4 · Tríos y refinamiento')
change(17,33,'Tríos y otra pasada de parejas y tríos, con capacidad compartida.\n\nPropuesta final: 3.873 buses y 1.374.632 USD')
change(19,1,'302 buses menos con las mismas corridas')
for i,new in {9:'3.873',10:'−302 (−7,23 %)',13:'1.374.631,70',14:'−84.941,10 (−5,82 %)',17:'94.244',18:'−4.606 km (−4,66 %)',21:'26.432',22:'−53,7 %',25:'534',26:'−52,7 %'}.items():change(19,i,new)
change(19,28,'La construcción cronológica aporta −161 buses y −USD 44.224 (52 % del ahorro); la mejora local y el refinamiento suman −141 buses y −USD 40.717 (2,88 % del costo inicial). Los km en vacío pasan de 12,31 % a 11,80 % del kilometraje total. Menor compra de energía no equivale a menor consumo: las baterías iniciales aportan y los estados finales pueden diferir.')
for i,new in {3:'89 %',5:'52 % / 48 %',13:'12 / 150',15:'180 / 180',16:'14 / 180',19:'8 / 120',22:'16 / 100',25:'16 / 150'}.items():change(20,i,new)
change(20,27,'Tiempo total: 1.718,4 s (28 min 38 s). Dos pasadas de 600 + 240 s por búsqueda. Parejas: 22.672 alternativas, 859 mejoras, 841 s; tríos: 37.769 alternativas, 172 mejoras, 841 s. Terminaron por presupuesto.')
change(20,28,'Costo final (USD): buses 968.250 · km 399.329 · electricidad 4.382 · sesiones 2.670. El tiempo no es comparable con la fase 1 anterior.')
change(21,2,'Misma instancia y parámetros físicos. Fuente: resultados/mejor_20261006_600 y mejor_20261006_refinamiento.')
for i,new in {20:'3.989',21:'1.403.068',22:'−25',23:'Tríos + refinamiento',24:'Tríos y segunda pasada de parejas y tríos',25:'3.873',26:'1.374.632',27:'−116'}.items():change(21,i,new)
change(21,29,'La construcción explica 161 de los 302 buses (53 %). La mejora local y el refinamiento suman 141 buses y USD 40.717, un 2,88 % del costo inicial. Las etapas corrieron en secuencia: no aíslan la causa de cada decisión del algoritmo.')
for i,new in {3:'DOS PASADAS: 600 + 240 s',10:'22.672',11:'859',12:'841 s',15:'37.769',16:'172',17:'841 s'}.items():change(22,i,new)
change(22,21,'Sí: flota −7,23 %, costo −5,82 %, sesiones −53 %, energía comprada −54 %. Los km en vacío bajan 4,66 %.')
change(22,23,'Km de servicio es idéntico (704.414 km): es dato, no KPI. Energía y sesiones pesan 0,5 % del costo: informan, pero no deciden.')
change(22,25,'Ampliar repeticiones y medir vecindarios y escala con igual presupuesto; mantener plazas y conexiones separadas.')
for i,new in {5:'53 %',7:'70 %',9:'100 %',11:'−53 %',13:'−302',15:'600+240 s'}.items():change(23,i,new)
change(23,10,'de plazas ocupadas: los cargadores tienen holgura')
change(23,12,'sesiones de carga: menos recargas en electroterminales')
change(23,14,'buses menos con construcción y mejora local auditada')
change(23,16,'por búsqueda en dos pasadas: 2,88 % de ahorro local')
change(24,5,'La flota explica ~70% del costo: cada bus evitado pesa más que cualquier ahorro de energía.\n\nLos cinco electroterminales alcanzan el 100% de plazas ocupadas; los cargadores tienen holgura (máx. 16 conexiones simultáneas).')
change(24,7,'Adoptamos la construcción con energía y conservamos la mejora local auditada.\n\nPara la entrega final: ampliar repeticiones, medir el aporte de cada movimiento y la escalabilidad a más rutas.')
change(25,12,'Solución, KPIs y barrido de presupuestos cumplidos')
change(26,9,'Ampliar análisis de sensibilidad')
sub(26,12,'−202 buses y −3,8 %','−302 buses y −5,8 %')
change(27,4,'La flota domina el costo: 70,4 % del costo final (USD 968.250 de 1.374.632) y 89 % del ahorro viene de usar menos buses.')
change(27,6,'La construcción con energía y la mejora local redujeron 302 buses (−7,23 %) y USD 84.941 (−5,82 %) frente al Ciclo 1, con las mismas 33.220 corridas.')
change(27,8,'La mejora local aporta 2,88 %. Más tiempo y una segunda pasada mejoraron el plan; falta ampliar repeticiones y separar el efecto de los vecindarios.')
change(27,10,'Sin garantía de optimalidad: tiempo y licencia acotados, sectores fijos y día aislado. El aporte de cada cambio no está aislado.')
# Correct existing footers only, retaining their style and coordinates.
for n,rows in groups.items():
 for i,r in enumerate(rows):
  t=''.join(z.get('text','') for z in r['regions'])
  if re.fullmatch(r'\d+ / 23',t):change(n,i,f'{n} / 28')
(OUT/'operaciones_texto.json').write_text(json.dumps(ops,ensure_ascii=False,indent=2))
print('Changes',sum(map(len,ops.values())),'pages',list(ops))
