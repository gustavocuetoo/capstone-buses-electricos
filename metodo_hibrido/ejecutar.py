"""Construcción cronológica y optimización local, independiente de las tres fases."""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'.deps'))
sys.path.insert(0,str(ROOT))
import argparse
import copy
import hashlib
import json
import time
from metodo_hibrido.caso_base import load_instance,solve,write_csv
from metodo_hibrido.verificar import verificar


def json_file(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')


def export(folder,plans,trips,params):
    report,journeys,activities=verificar(plans,trips,*params)
    folder.mkdir(parents=True,exist_ok=False)
    for name,rows in [('jornadas',journeys),('actividades',activities),
                      ('recargas',[a for a in activities if a['tipo']=='carga'])]:
        write_csv(folder/(name+'.csv'),rows)
    json_file(folder/'planes.json',plans)
    json_file(folder/'resumen.json',report)
    return report


def etapa(plans,trips,params,search,**kwargs):
    """Aislar mutaciones y conservar el incumbente ante rechazo o fallo de auditoría."""
    before,_,_=verificar(plans,trips,*params)
    tick=time.perf_counter()
    candidate,history,stats=search(copy.deepcopy(plans),{t['corrida_id']:t for t in trips},*params,**kwargs)
    try:
        after,_,_=verificar(candidate,trips,*params)
    except (AssertionError,KeyError,ValueError) as error:
        return plans,history,dict(**stats,etapa_aceptada=False,rechazo='auditoria: '+str(error),tiempo_etapa_s=time.perf_counter()-tick)
    accepted=after['costo_total_usd']<before['costo_total_usd']-1e-5
    return candidate if accepted else plans,history,dict(**stats,etapa_aceptada=accepted,
            rechazo='' if accepted else 'sin_mejora_estricta',tiempo_etapa_s=time.perf_counter()-tick)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instancia',type=Path,default=HERE/'instancia_212')
    parser.add_argument('--salida',type=Path,default=HERE/'resultados'/'ensayo_212')
    parser.add_argument('--presupuesto-pares',type=float,default=120)
    parser.add_argument('--presupuesto-trios',type=float,default=120)
    parser.add_argument('--limite-local',type=float,default=2)
    parser.add_argument('--vecinos',type=int,default=8)
    parser.add_argument('--alternativas',type=int,default=3)
    parser.add_argument('--rondas',type=int,default=3)
    args=parser.parse_args()
    if min(args.presupuesto_pares,args.presupuesto_trios)<0 or min(args.limite_local,args.vecinos,args.alternativas,args.rondas)<=0:
        parser.error('Presupuestos no negativos y otros límites positivos requeridos')
    if not args.salida.resolve().is_relative_to(HERE.resolve()):
        parser.error('La salida debe permanecer dentro de metodo_hibrido para separar las metodologías')
    if args.salida.exists():parser.error('La carpeta de salida ya existe; elige otra para conservar los resultados')
    # Cargar dependencias antes de comenzar el ensayo para detectar instalaciones incompletas.
    from metodo_hibrido.intercambios import buscar
    from metodo_hibrido.trios import buscar_trios
    tick=time.perf_counter()
    trips,*params=load_instance(args.instancia)
    args.salida.mkdir(parents=True)
    configuration=dict(metodologia='Construcción cronológica + mejora local conjunta',
        parametros={k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()},
        sha256_entradas={n:hashlib.sha256((args.instancia/n).read_bytes()).hexdigest()
                       for n in ('escenario.json','corridas.csv','distancias.csv')},
        sha256_codigo={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')},
        sectores='Servicios de cada jornada en un solo sector; cinco E compartidos')
    json_file(args.salida/'ejecucion.json',configuration)
    try:
        start=time.perf_counter()
        initial,_,_,decisions,plans=solve(trips,*params,
            progress=lambda n,total,b:print(f'Construcción: {n}/{total}; {b} buses',flush=True))
        construction=time.perf_counter()-start
        baseline=export(args.salida/'01_caso_base',plans,trips,params)
        write_csv(args.salida/'01_caso_base'/'decisiones.csv',decisions)
        rows=[dict(etapa='caso_base',**baseline,tiempo_algoritmo_s=construction)]
        history_stats=[]
        for label,search,budget in [('02_pares',buscar,args.presupuesto_pares),('03_trios',buscar_trios,args.presupuesto_trios)]:
            if budget==0:continue
            print(f'{label}: inicio {len(plans)} buses; presupuesto {budget:g} s',flush=True)
            plans,history,stats=etapa(plans,trips,params,search,budget=budget,local_limit=args.limite_local,
                neighbors=args.vecinos,per_pair=args.alternativas,max_rounds=args.rondas,coordination='conjunta')
            report=export(args.salida/label,plans,trips,params)
            write_csv(args.salida/label/'intentos.csv',history)
            json_file(args.salida/label/'busqueda.json',stats)
            history_stats.append(dict(etapa=label,**stats))
            rows.append(dict(etapa=label,**report,tiempo_algoritmo_s=stats['tiempo_etapa_s']))
            print(f"{label}: {report['buses']} buses; USD {report['costo_total_usd']:.2f}",flush=True)
        final=export(args.salida/'04_final',plans,trips,params)
        assert final['costo_total_usd']<=baseline['costo_total_usd']+1e-5
        result=dict(metodologia=configuration['metodologia'],corridas=len(trips),rutas=len({t['route_id'] for t in trips}),
            inicial=baseline,final=final,buses_evitados=baseline['buses']-final['buses'],
            ahorro_usd=baseline['costo_total_usd']-final['costo_total_usd'],
            mejora_porcentual=100*(baseline['costo_total_usd']-final['costo_total_usd'])/baseline['costo_total_usd'],
            tiempo_construccion_s=construction,busquedas=history_stats,tiempo_total_s=time.perf_counter()-tick,
            optimalidad_global_demostrada=False)
        json_file(args.salida/'comparacion.json',result)
        fields=['etapa','buses','corridas','km','carga_kwh','sesiones','costo_total_usd','tiempo_algoritmo_s']
        write_csv(args.salida/'comparacion_etapas.csv',[{k:r[k] for k in fields} for r in rows])
        print(json.dumps({k:result[k] for k in ['buses_evitados','ahorro_usd','mejora_porcentual','tiempo_total_s']},indent=2))
    except Exception as error:
        json_file(args.salida/'fallo.json',dict(error=type(error).__name__,detalle=str(error),
                  indicacion='Las etapas ya exportadas permanecen disponibles; no considerar el ensayo completo.'))
        raise


if __name__=='__main__':main()
