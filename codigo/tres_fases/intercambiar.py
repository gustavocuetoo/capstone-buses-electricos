"""Reasignar servicios entre dos jornadas del mismo sector sobre una solución guardada."""
import sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'.deps'));sys.path.insert(0,str(BASE))
import argparse
import json
import time
import hashlib
from collections import defaultdict
from tres_fases.datos import cargar,leer,guardar
from tres_fases.intercambios import buscar
from tres_fases.verificar import verificar

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=BASE/'output/tres_fases/muestra_20_reparada')
    parser.add_argument('--salida',type=Path)
    parser.add_argument('--presupuesto',type=float,default=120.)
    parser.add_argument('--limite-local',type=float,default=2.)
    parser.add_argument('--vecinos',type=int,default=8)
    parser.add_argument('--alternativas',type=int,default=3)
    parser.add_argument('--rondas',type=int,default=3)
    parser.add_argument('--coordinacion',choices=('secuencial','conjunta'),default='secuencial')
    parser.add_argument('--grupo',type=int,choices=(2,3),default=2)
    args=parser.parse_args()
    if args.grupo==3 and args.coordinacion!='conjunta':parser.error('--grupo 3 requiere --coordinacion conjunta')
    if min(args.presupuesto,args.limite_local,args.vecinos,args.alternativas,args.rondas)<=0:
        parser.error('Los límites deben ser positivos')
    tick=time.perf_counter()
    suffix='_trios' if args.grupo==3 else ('_conjunta' if args.coordinacion=='conjunta' else '_intercambios')
    out=args.salida or args.base.with_name(args.base.name+suffix)
    if out.resolve()==args.base.resolve():raise ValueError('Se debe conservar la carpeta original')
    summary=json.loads((args.base/'comparacion.json').read_text(encoding='utf-8'))
    if 'horizonte' in summary:bounds=summary['horizonte']
    else:
        parent=json.loads((Path(summary['base'])/'resumen.json').read_text(encoding='utf-8'))
        bounds=parent['horizonte']
    trips,d,starts,physical,plugs,tariffs=cargar(summary['rutas'])
    grouped=defaultdict(list)
    for a in leer(args.base/'actividades.csv'):
        row={k:a[k] for k in ('tipo','origen','destino','corrida_id')}
        row.update({k:int(a[k]) for k in ('inicio_s','fin_s')})
        row.update({k:float(a[k]) for k in ('distancia_km','carga_kwh')})
        grouped[a['bus_id']].append(row)
    plans=[]
    for p in leer(args.base/'jornadas.csv'):
        acts=grouped[p['bus_id']]
        plans.append({**{k:p[k] for k in ('bus_id','cadena_fase2','sector_id','terminal_inicial','terminal_final')},
                      'actividades':acts,'corridas':[a['corrida_id'] for a in acts if a['tipo']=='servicio']})
    params=(d,starts,physical,plugs,tariffs,int(bounds['inicio_horizonte_s']),int(bounds['fin_horizonte_s']))
    before,_,_=verificar(plans,trips,*params)
    print(f"Inicio: {before['buses']} buses, {len(trips)} corridas; presupuesto {args.presupuesto:g} s.",flush=True)
    search=buscar
    if args.grupo==3:
        from tres_fases.trios import buscar_trios
        search=buscar_trios
    result,history,stats=search(plans,{t['corrida_id']:t for t in trips},*params,
                              budget=args.presupuesto,local_limit=args.limite_local,neighbors=args.vecinos,
                              per_pair=args.alternativas,max_rounds=args.rondas,coordination=args.coordinacion)
    after,journeys,activities=verificar(result,trips,*params)
    out.mkdir(parents=True,exist_ok=True)
    guardar(out/'jornadas.csv',journeys);guardar(out/'actividades.csv',activities)
    guardar(out/'intercambios.csv',history);guardar(out/'recargas.csv',[a for a in activities if a['tipo']=='carga'])
    report=dict(base=str(args.base.resolve()),rutas=summary['rutas'],horizonte=bounds,
                antes=before,despues=after,buses_evitados=before['buses']-after['buses'],
                ahorro_usd=before['costo_total_usd']-after['costo_total_usd'],busqueda=stats,
                parametros=dict(presupuesto_s=args.presupuesto,limite_local_s=args.limite_local,
                                vecinos=args.vecinos,alternativas_por_grupo=args.alternativas,rondas=args.rondas,coordinacion=args.coordinacion,grupo=args.grupo),
                sha256_entrada={f:hashlib.sha256((args.base/f).read_bytes()).hexdigest() for f in ('jornadas.csv','actividades.csv')},
                tiempo_total_s=time.perf_counter()-tick,optimalidad_global_demostrada=False)
    (out/'comparacion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k in ('buses_evitados','ahorro_usd','busqueda','tiempo_total_s')},indent=2))

if __name__=='__main__':main()
