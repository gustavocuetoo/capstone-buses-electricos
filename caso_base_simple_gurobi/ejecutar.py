"""Partición óptima de cadenas sin recargas: red acíclica por cadena."""
import argparse
import math
import time
from pathlib import Path
from datos_y_auditoria import load, terminals, plans_from_selection, params, verificar, save_json, save_csv

ROOT=Path(__file__).resolve().parent

def segments(ids,lookup,d,term):
    """Todos los fragmentos consecutivos factibles, sin poda por retorno intermedio."""
    arcs=[]
    for a in range(len(ids)):
        first=lookup[ids[a]]
        km=d[term[ids[a]][0],'S:'+first['inicio_stop_id']][0]
        for b in range(a,len(ids)):
            t=lookup[ids[b]]
            if b>a:
                prev=lookup[ids[b-1]]
                km+=d['S:'+prev['fin_stop_id'],'S:'+t['inicio_stop_id']][0]
            km+=t['distancia_servicio_km']
            # El consumo acumulado no disminuye. El retorno sí puede disminuir.
            if 1.4*km>315+1e-8:break
            total=km+d['S:'+t['fin_stop_id'],term[ids[b]][1]][0]
            if 1.4*total<=315+1e-8:
                arcs.append((a,b+1,250+.5*total))
    return arcs

def shortest(n,arcs):
    outgoing=[[] for _ in range(n+1)]
    for a,b,c in arcs:outgoing[a].append((b,c))
    cost=[math.inf]*(n+1);parent=[None]*(n+1);cost[0]=0
    for a in range(n):
        for b,c in outgoing[a]:
            if cost[a]+c<cost[b]-1e-9:cost[b]=cost[a]+c;parent[b]=a
    if not math.isfinite(cost[n]):raise ValueError('Cadena sin partición factible')
    chosen=[];b=n
    while b: a=parent[b];chosen.append((a,b));b=a
    return cost[n],list(reversed(chosen))

def solve_gurobi(n,arcs,env,limit,threads):
    import gurobipy as gp
    model=gp.Model('particion_sin_recarga',env=env)
    try:
        model.Params.OutputFlag=0;model.Params.TimeLimit=limit
        model.Params.Threads=threads;model.Params.MIPGap=0
        outgoing=[[] for _ in range(n+1)];incoming=[[] for _ in range(n+1)]
        x=[]
        for a,b,c in arcs:
            v=model.addVar(vtype=gp.GRB.BINARY,obj=c);x.append(v)
            outgoing[a].append(v);incoming[b].append(v)
        for v in range(n+1):
            model.addConstr(gp.quicksum(outgoing[v])-gp.quicksum(incoming[v])==(1 if v==0 else -1 if v==n else 0))
        model.optimize()
        if model.Status!=gp.GRB.OPTIMAL:
            raise RuntimeError(f'Cadena no resuelta a optimalidad: estado {model.Status}; ampliar --tiempo-cadena. No se sustituye por otra solución.')
        chosen=[(a,b) for (a,b,c),v in zip(arcs,x) if v.X>.5]
        return model.ObjVal,sorted(chosen),dict(estado=int(model.Status),gap=model.MIPGap,cota=model.ObjBound,tiempo_s=model.Runtime)
    finally:model.dispose()

def run(args):
    started=time.perf_counter();out=args.salida
    if out.exists():raise ValueError('Elegir una carpeta de salida nueva')
    out.mkdir(parents=True)
    save_json(out/'configuracion.json',{k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()})
    env=None
    try:
        cfg,trips,lookup,d,chains=load(args.instancia)
        term={i:terminals(t,d,cfg,False) for i,t in lookup.items()}
        if args.motor=='gurobi':
            import gurobipy as gp
            env=gp.Env(empty=True);env.setParam('LogFile',str(out/'gurobi.log'));env.setParam('OutputFlag',0);env.start()
        links=set();ends={i:term[i][1] for i in lookup};details=[];total=0.
        for index,chain in enumerate(chains):
            ids=chain['corridas'];arcs=segments(ids,lookup,d,term)
            exact,chosen=shortest(len(ids),arcs)
            stats={}
            if env is not None:
                cost,chosen,stats=solve_gurobi(len(ids),arcs,env,args.tiempo_cadena,args.hilos)
                if abs(cost-exact)>max(.001,1e-8*abs(exact)):raise AssertionError('Gurobi y programación dinámica no coinciden')
            else:cost=exact
            for a,b in chosen:links.update(zip(ids[a:b],ids[a+1:b]))
            total+=cost
            details.append(dict(cadena=chain['id'],corridas=len(ids),variables=len(arcs),restricciones=len(ids)+1,buses=len(chosen),costo=cost,**stats))
            if (index+1)%500==0:print(f'{index+1}/{len(chains)} cadenas resueltas',flush=True)
        plans=plans_from_selection(chains,lookup,d,cfg,term,links,{},ends)
        summary,journeys,activities=verificar(plans,*params(cfg,trips,d))
        if abs(summary['costo_total_usd']-total)>max(.01,1e-8*abs(total)):raise AssertionError('Costo auditado distinto al optimizado')
        summary.update(motor=args.motor,optimo_cadenas_fijas_sin_recarga=True,optimo_problema_original=False,
                       rutas=len({t['route_id'] for t in trips}),corridas=len(trips),cadenas=len(chains),
                       variables_totales=sum(v['variables'] for v in details),max_variables_por_modelo=max(v['variables'] for v in details),
                       max_restricciones_por_modelo=max(v['restricciones'] for v in details),tiempo_total_s=time.perf_counter()-started)
        save_json(out/'resumen.json',summary);save_json(out/'planes.json',plans)
        save_csv(out/'jornadas.csv',journeys);save_csv(out/'actividades.csv',activities);save_csv(out/'modelos.csv',details)
        print(summary,flush=True)
    except Exception as exc:
        save_json(out/'fallo.json',dict(error=str(exc),tipo=type(exc).__name__,ejecucion_completa=False));raise
    finally:
        if env is not None:env.dispose()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--instancia',type=Path,default=ROOT/'instancia_212')
    p.add_argument('--salida',type=Path,default=ROOT/'resultados_gurobi')
    p.add_argument('--motor',choices=['gurobi','dinamica'],default='gurobi')
    p.add_argument('--tiempo-cadena',type=float,default=60)
    p.add_argument('--hilos',type=int,default=1)
    a=p.parse_args()
    if a.tiempo_cadena<=0 or a.hilos<1:p.error('Límites inválidos')
    run(a)
