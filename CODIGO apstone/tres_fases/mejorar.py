"""Reparar una ejecución existente sin cambiar rutas ni volver a resolver fases 1 y 2."""
import sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'.deps'));sys.path.insert(0,str(BASE))
import argparse
import json
import time
from collections import defaultdict
from tres_fases.datos import cargar,leer,guardar
from tres_fases.reparar import reparar
from tres_fases.verificar import verificar

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=BASE/'output/tres_fases/muestra_20')
    parser.add_argument('--salida',type=Path)
    parser.add_argument('--limite-local',type=float,default=2.)
    args=parser.parse_args()
    out=args.salida or args.base.with_name(args.base.name+'_reparada')
    if out.resolve()==args.base.resolve():raise ValueError('La comparación debe preservar la carpeta original')
    out.mkdir(parents=True,exist_ok=True)
    original=json.loads((args.base/'resumen.json').read_text(encoding='utf-8'))
    trips,d,starts,physical,plugs,tariffs=cargar(original['rutas'])
    t0=int(original['horizonte']['inicio_horizonte_s']);h=int(original['horizonte']['fin_horizonte_s'])
    grouped=defaultdict(list)
    for a in leer(args.base/'fase3/actividades.csv'):
        row={k:a[k] for k in ('tipo','origen','destino','corrida_id')}
        row.update({k:int(a[k]) for k in ('inicio_s','fin_s')})
        row.update({k:float(a[k]) for k in ('distancia_km','carga_kwh')})
        grouped[a['bus_id']].append(row)
    plans=[]
    for p in leer(args.base/'fase3/jornadas.csv'):
        acts=grouped[p['bus_id']]
        plans.append({**{k:p[k] for k in ('bus_id','cadena_fase2','sector_id','terminal_inicial','terminal_final')},
                      'actividades':acts,'corridas':[a['corrida_id'] for a in acts if a['tipo']=='servicio']})
    params=(d,starts,physical,plugs,tariffs,t0,h)
    before,_,_=verificar(plans,trips,*params)
    tick=time.perf_counter()
    improved,diagnostics=reparar(plans,{t['corrida_id']:t for t in trips},*params,limit=args.limite_local)
    elapsed=time.perf_counter()-tick
    after,journeys,activities=verificar(improved,trips,*params)
    guardar(out/'jornadas.csv',journeys);guardar(out/'actividades.csv',activities)
    guardar(out/'diagnostico_reparaciones.csv',diagnostics)
    guardar(out/'recargas.csv',[a for a in activities if a['tipo']=='carga'])
    report=dict(base=str(args.base.resolve()),rutas=original['rutas'],corridas=len(trips),
                antes=before,despues=after,buses_evitados=before['buses']-after['buses'],
                ahorro_usd=before['costo_total_usd']-after['costo_total_usd'],tiempo_reparacion_s=elapsed,
                intentos=len(diagnostics),fusiones_con_reserva=sum(r['aceptada'] and not r['requiere_relajar_reserva_T'] for r in diagnostics),
                fusiones_sin_reserva=sum(r['aceptada'] and r['requiere_relajar_reserva_T'] for r in diagnostics),
                limite_local_s=args.limite_local,optimalidad_global_demostrada=False)
    (out/'comparacion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('antes','despues','rutas')},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
