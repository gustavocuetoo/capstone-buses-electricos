"""Flujo de costo mínimo en red tiempo-espacio, sin batería (fase 1)."""
import sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'.deps'))
sys.path.insert(0,str(BASE))
import argparse
import bisect
import csv
import json
import math
from collections import defaultdict,Counter,namedtuple
import numpy as np
from scipy.sparse import coo_matrix
import gurobipy as gp
from gurobipy import GRB
from construir_distancias_electroterminales import read_csv,write_csv

class Arco(namedtuple('_Arco','u v tipo km espera_min inicio_s fin_s corrida_id terminal_id costo lb ub')):
    """Registro inmutable compacto; conserva acceso por nombre e items para las fases existentes."""
    __slots__=()
    def __getitem__(self,key):
        if isinstance(key,str):return getattr(self,key)
        return super().__getitem__(key)
    def items(self):return zip(self._fields,self)


def crear_red(trips,distances,starts,final_caps,cfg):
    """All feasible end-to-start pairs are represented by earliest-arrival links plus waits."""
    nodes={}; node_keys=[]; arcs=[]
    def node(key):
        if key not in nodes: nodes[key]=len(nodes);node_keys.append(key)
        return nodes[key]
    source,sink=node(('source',)),node(('sink',))
    def arc(u,v,kind,km=0,wait=0,start=None,end=None,trip='',terminal='',lb=0,ub=None):
        if u==v: return
        cost=cfg['costo_km_usd']*km+cfg['costo_espera_min_usd']*wait
        if kind=='flota':cost=cfg['costo_bus_usd']
        arcs.append(Arco(u=u,v=v,tipo=kind,km=km,espera_min=wait,inicio_s=start,fin_s=end,
                         corrida_id=trip,terminal_id=terminal,costo=cost,lb=lb,ub=len(trips) if ub is None else ub))
    departure_times=defaultdict(set); events=defaultdict(set); arrivals=set()
    for t in trips:
        sec=t['sector_id'];s=t['inicio_s'];f=t['fin_s'];o='S:'+t['inicio_stop_id'];d='S:'+t['fin_stop_id']
        if f<=s:raise ValueError('Corrida de duración no positiva')
        events[sec,o].add(s);events[sec,d].add(f)
        departure_times[sec,o].add(s);arrivals.add((sec,d,f))
    for (sec,loc),times in events.items():
        ordered=sorted(times)
        for time in ordered:node((sec,loc,time))
        for left,right in zip(ordered,ordered[1:]):
            arc(node((sec,loc,left)),node((sec,loc,right)),'espera',wait=(right-left)/60,start=left,end=right)
    for t in trips:
        arc(node((t['sector_id'],'S:'+t['inicio_stop_id'],t['inicio_s'])),
            node((t['sector_id'],'S:'+t['fin_stop_id'],t['fin_s'])),
            'servicio',km=t['distancia_servicio_km'],start=t['inicio_s'],end=t['fin_s'],trip=t['corrida_id'],lb=1,ub=1)
    regulation=math.ceil(cfg['regulacion_min']*60)
    if regulation:
        raise ValueError('Esta red usa regulación mínima cero. Para un valor positivo hay que separar eventos de llegada/disponibilidad.')
    by_sector=defaultdict(list)
    for (sec,loc),times in departure_times.items():by_sector[sec].append((loc,sorted(times)))
    # Waiting at any endpoint is uncapacitated. No nearest-k or max-gap truncation.
    for sec,origin,finish in sorted(arrivals):
        for target,times in by_sector[sec]:
            if target==origin:continue
            pair=distances.get((origin,target))
            if pair is None:raise ValueError(f'Falta parámetro {origin}->{target}')
            km,seconds=pair
            if not math.isfinite(km):continue
            j=bisect.bisect_left(times,finish+seconds)
            if j<len(times):
                arrival=times[j]
                arc(node((sec,origin,finish)),node((sec,target,arrival)),'traslado',
                    km=km,wait=(arrival-finish-seconds)/60,start=finish,end=arrival)
    earliest=math.inf;latest=-math.inf
    for (sec,loc),times in departure_times.items():
        for time in sorted(times):
            for terminal in starts:
                if (terminal,loc) not in distances:raise ValueError(f'Falta salida {terminal}->{loc}')
                km,seconds=distances[terminal,loc]
                if math.isfinite(km):
                    earliest=min(earliest,time-seconds)
                    arc(source,node((sec,loc,time)),'salida_terminal',km=km,start=time-seconds,end=time,terminal=terminal)
    for sec,origin,finish in sorted(arrivals):
        for terminal in final_caps:
            if (origin,terminal) not in distances:raise ValueError(f'Falta retorno {origin}->{terminal}')
            km,seconds=distances[origin,terminal]
            if math.isfinite(km):
                latest=max(latest,finish+seconds)
                arc(node((sec,origin,finish)),node(('terminal_final',terminal)),'retorno_terminal',
                    km=km,start=finish,end=finish+seconds,terminal=terminal)
    for terminal,capacity in final_caps.items():
        arc(node(('terminal_final',terminal)),sink,'estacionamiento_final',terminal=terminal,
            ub=len(trips) if capacity is None else capacity)
    arc(sink,source,'flota')
    return node_keys,arcs,source,sink,dict(inicio_horizonte_s=earliest,fin_horizonte_s=latest)


def resolver_red(nodes,arcs,out,time_limit=120):
    model=gp.Model('RED_fase1')
    model.Params.Threads=4
    model.Params.TimeLimit=time_limit
    model.Params.Method=1  # Basic LP solution; network integrality is checked before use.
    model.Params.LogFile=str(out/'gurobi.log')
    variables=model.addMVar(len(arcs),lb=np.fromiter((a['lb'] for a in arcs),dtype=float,count=len(arcs)),
                           ub=np.fromiter((a['ub'] for a in arcs),dtype=float,count=len(arcs)),
                           obj=np.fromiter((a['costo'] for a in arcs),dtype=float,count=len(arcs)),name='flujo')
    rows=np.fromiter((node for a in arcs for node in (a['u'],a['v'])),dtype=np.int32,count=2*len(arcs))
    columns=np.repeat(np.arange(len(arcs),dtype=np.int32),2)
    values=np.tile(np.array([-1.,1.]),len(arcs))
    incidence=coo_matrix((values,(rows,columns)),shape=(len(nodes),len(arcs))).tocsr()
    del rows,columns,values
    model.addMConstr(incidence,variables,'=',np.zeros(len(nodes)),name='balance')
    model.write(str(out/'modelo.mps'))
    model.optimize()
    if model.Status==GRB.INFEASIBLE:
        model.computeIIS();model.write(str(out/'conflicto.ilp'))
        raise RuntimeError('Modelo infactible. Véase conflicto.ilp.')
    if model.SolCount==0:raise RuntimeError(f'No se obtuvo solución. Estado Gurobi {model.Status}')
    solution=variables.X
    if np.max(np.abs(solution-np.rint(solution)))>1e-5:
        raise RuntimeError('Flujo fraccionario: no se convierte en buses mediante redondeo arbitrario.')
    flow=np.rint(solution).astype(int)
    residual=incidence@flow
    assert np.max(np.abs(residual))<1e-8
    assert all(a['lb']<=int(x)<=a['ub'] for a,x in zip(arcs,flow))
    model.write(str(out/'solucion.sol'))
    summary=dict(estado_gurobi=int(model.Status),optimo_demostrado=model.Status==GRB.OPTIMAL,
                 objetivo_usd=model.ObjVal,tiempo_solver_s=model.Runtime,nodos=len(nodes),arcos=len(arcs))
    model.dispose()
    return flow,summary


def descomponer(nodes,arcs,flow,source,sink):
    remaining=flow.copy();adj=defaultdict(list)
    fleet=0
    for i,a in enumerate(arcs):
        if a['tipo']=='flota':fleet+=int(remaining[i]);remaining[i]=0
        elif remaining[i]:adj[a['u']].append(i)
    paths=[]
    for bus in range(fleet):
        current=source;path=[];seen=set()
        while current!=sink:
            if current in seen:raise RuntimeError('Ciclo inesperado en una jornada')
            seen.add(current)
            choices=adj[current]
            while choices and remaining[choices[-1]]==0:choices.pop()
            if not choices:raise RuntimeError('Flujo incompleto al descomponer')
            index=choices[-1];remaining[index]-=1;path.append(index);current=arcs[index]['v']
        paths.append(path)
    if np.any(remaining):raise RuntimeError('Quedó flujo sin asignar a jornadas')
    return paths


def verificar_y_exportar(trips,nodes,arcs,paths,distances,final_caps,cfg,out):
    lookup={t['corrida_id']:t for t in trips};coverage=Counter();end_counts=Counter();start_counts=Counter()
    records=[];journeys=[];fixed=cfg['costo_bus_usd'];total=0
    for index,path in enumerate(paths,1):
        bus=f'B{index:05d}';used=[arcs[i] for i in path]
        services=[a for a in used if a['tipo']=='servicio']
        if not services:raise AssertionError('Jornada sin servicios')
        first,last=used[0],next(a for a in reversed(used) if a['tipo']=='retorno_terminal')
        start_counts[first['terminal_id']]+=1;end_counts[last['terminal_id']]+=1
        first_trip,last_trip=lookup[services[0]['corrida_id']],lookup[services[-1]['corrida_id']]
        pull=distances[first['terminal_id'],'S:'+first_trip['inicio_stop_id']]
        assert first['inicio_s']+pull[1]<=first_trip['inicio_s']
        for previous,current in zip(services,services[1:]):
            a,b=lookup[previous['corrida_id']],lookup[current['corrida_id']]
            assert a['sector_id']==b['sector_id']
            travel=distances['S:'+a['fin_stop_id'],'S:'+b['inicio_stop_id']][1]
            assert a['fin_s']+travel<=b['inicio_s']
        for activity in services:coverage[activity['corrida_id']]+=1
        cost=fixed+sum(a['costo'] for a in used);total+=cost
        journeys.append(dict(bus_id=bus,sector_id=first_trip['sector_id'],terminal_inicial=first['terminal_id'],
                             terminal_final=last['terminal_id'],inicio_s=first['inicio_s'],fin_s=last['fin_s'],
                             corridas=len(services),km_servicio=sum(a['km'] for a in services),
                             km_vacio=sum(a['km'] for a in used if a['tipo']!='servicio'),
                             espera_min=sum(a['espera_min'] for a in used),costo_usd=cost))
        for order,a in enumerate(used,1):
            if a['tipo']=='estacionamiento_final':continue
            records.append(dict(bus_id=bus,orden=order,**{k:v for k,v in a.items() if k not in {'u','v','lb','ub'}},
                                nodo_origen=str(nodes[a['u']]),nodo_destino=str(nodes[a['v']])))
    assert set(coverage)==set(lookup) and all(x==1 for x in coverage.values())
    for terminal,cap in final_caps.items():assert cap is None or end_counts[terminal]<=cap
    write_csv(out/'jornadas.csv',journeys);write_csv(out/'actividades.csv',records)
    return dict(corridas_cubiertas=len(coverage),flota=len(paths),
                buses_iniciales=dict(start_counts),buses_finales=dict(end_counts),
                km_vacio=sum(j['km_vacio'] for j in journeys),km_servicio=sum(j['km_servicio'] for j in journeys),
                espera_min=sum(j['espera_min'] for j in journeys),costo_verificado_usd=total,
                verificacion='cobertura, balances, integralidad, horarios, terminales y costos; no incluye energía')


def cargar_instancia(args):
    data=BASE/'output/fase1'
    cfg=json.loads((BASE/'fase1/configuracion.json').read_text(encoding='utf-8'))
    meta=json.loads((data/'metadatos.json').read_text(encoding='utf-8'))
    if meta['terminales_pendientes'] and not args.permitir_pendientes:
        raise ValueError('Hay terminales pendientes; usar --permitir-pendientes solo para un prototipo explícito.')
    assert cfg['velocidad_vacio_kmh']==meta['velocidad_kmh'],'Recalcular traslados al cambiar velocidad'
    trips=[]
    selected=set(args.rutas.split(','))
    for r in read_csv(data/'corridas.csv'):
        if r['service_id']!=args.dia:continue
        if not args.todas and r['route_id'] not in selected:continue
        if args.sector and r['sector_id']!=args.sector:continue
        for k in ['inicio_s','fin_s']:r[k]=int(r[k])
        r['distancia_servicio_km']=float(r['distancia_servicio_km'])
        trips.append(r)
    trips.sort(key=lambda r:(r['inicio_s'],r['corrida_id']))
    if args.limite:trips=trips[:args.limite]
    if not trips:raise ValueError('Instancia vacía')
    distances={}
    for r in read_csv(data/'traslados.csv'):
        distances[r['origen_id'],r['destino_id']]=(float(r['distancia_km']),int(r['tiempo_s'])) if r['distancia_km'] else (math.inf,math.inf)
    starts=meta['terminales_activos']
    final_caps={t:None for t in starts}
    # Preserve the original five electroterminals and their finite physical capacity.
    for d in read_csv(BASE/'depots.csv'):final_caps['E'+d['depot_id']]=int(d['capacity'])
    for r in read_csv(BASE/'output/distancias_electroterminales/distancias_recorridos_electroterminales.csv'):
        if r['movimiento']!='fin_a_electroterminal':continue
        km=float(r['distancia_km']) if r['distancia_km'] else math.inf
        distances['S:'+r['fin_stop_id'],'E'+r['depot_id']]=(km,math.ceil(km/cfg['velocidad_vacio_kmh']*3600) if math.isfinite(km) else math.inf)
    return cfg,meta,trips,distances,starts,final_caps


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dia',choices=['L','S','D'],default='L')
    parser.add_argument('--rutas',default='101',help='Rutas separadas por coma; ejemplo inicial 101')
    parser.add_argument('--todas',action='store_true')
    parser.add_argument('--sector',choices=['1','2','3','4','5'])
    parser.add_argument('--limite',type=int,default=0,help='0 conserva todas las corridas seleccionadas')
    parser.add_argument('--tiempo-limite',type=float,default=120)
    parser.add_argument('--permitir-pendientes',action='store_true')
    parser.add_argument('--salida',default='output/fase1/prueba_101')
    args=parser.parse_args()
    cfg,meta,trips,distances,starts,final_caps=cargar_instancia(args)
    out=BASE/args.salida;out.mkdir(parents=True,exist_ok=True)
    nodes,arcs,source,sink,bounds=crear_red(trips,distances,starts,final_caps,cfg)
    print(f'Instancia: {len(trips)} corridas; {len(nodes)} nodos; {len(arcs)} arcos',flush=True)
    flow,summary=resolver_red(nodes,arcs,out,args.tiempo_limite)
    paths=descomponer(nodes,arcs,flow,source,sink)
    verified=verificar_y_exportar(trips,nodes,arcs,paths,distances,final_caps,cfg,out)
    assert abs(summary['objetivo_usd']-verified['costo_verificado_usd'])<.01
    timeline=sorted([(t['inicio_s'],1) for t in trips]+[(t['fin_s'],-1) for t in trips])
    live=peak=0
    for _,change in timeline:live+=change;peak=max(peak,live)
    assert verified['flota']>=peak
    report={**summary,**verified,**bounds,'dia':args.dia,'rutas':sorted({t['route_id'] for t in trips}),
            'corridas_instancia':len(trips),'cota_simultaneidad':peak,'terminales_pendientes':meta['terminales_pendientes'],
            'velocidad_vacio_kmh':cfg['velocidad_vacio_kmh'],'factibilidad_energetica_verificada':False,
            'alcance':'Día aislado de fase 1. No es operación semanal ni solución eléctrica factible.'}
    (out/'resultado.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
