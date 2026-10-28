"""Búsqueda acotada entre dos jornadas, preservando la mejor solución verificada."""
import time
from collections import Counter
from metodo_hibrido.calendario import Calendario
from metodo_hibrido.recarga import cambiar_reservas, costo, resolver_jornada
from metodo_hibrido.verificar import verificar

def compatible(ids, lookup, d):
    return all(lookup[a]['fin_s']+d['S:'+lookup[a]['fin_stop_id'], 'S:'+lookup[b]['inicio_stop_id']][1]
               <= lookup[b]['inicio_s'] for a,b in zip(ids,ids[1:]))

def distancia_minima(ids, lookup, d, starts, finals):
    """Costo de enlaces directos como criterio de orden; no certifica cota global."""
    if not ids:return 0.
    return (min(d[t,'S:'+lookup[ids[0]]['inicio_stop_id']][0] for t in starts)
            +min(d['S:'+lookup[ids[-1]]['fin_stop_id'],t][0] for t in finals)
            +sum(d['S:'+lookup[a]['fin_stop_id'],'S:'+lookup[b]['inicio_stop_id']][0] for a,b in zip(ids,ids[1:])))

def alternativas(a,b,lookup,d):
    """Fusión, intercambio de sufijos y traslado individual; conservación exacta de servicios."""
    seen={tuple(sorted((tuple(a),tuple(b))))}
    def candidate(kind,left,right):
        seqs=[s for s in (left,right) if s]
        key=tuple(sorted(tuple(s) for s in seqs))
        if key in seen or not all(compatible(s,lookup,d) for s in seqs):return None
        seen.add(key)
        assert Counter(t for s in seqs for t in s)==Counter(a+b)
        return kind,seqs
    merged=sorted(a+b,key=lambda t:(lookup[t]['inicio_s'],t))
    c=candidate('fusion',merged,[])
    if c:yield c
    for i in range(len(a)+1):
        for j in range(len(b)+1):
            c=candidate('sufijos',a[:i]+b[j:],b[:j]+a[i:])
            if c:yield c
    for left,right in ((a,b),(b,a)):
        for i,t in enumerate(left):
            shortened=left[:i]+left[i+1:]
            for j in range(len(right)+1):
                c=candidate('servicio',shortened,right[:j]+[t]+right[j:])
                if c:yield c

def evaluar(old,seqs,lookup,d,starts,calendar,tariffs,limit,deadline):
    """Prueba los dos órdenes de reserva; siempre devuelve intacto el calendario original."""
    cambiar_reservas(calendar,old,-1)
    statuses=[]
    try:
        for order in ([0],) if len(seqs)==1 else ([0,1],[1,0]):
            built=[]
            try:
                for k in order:
                    remaining=deadline-time.perf_counter()
                    if remaining<=0:return None,statuses+['presupuesto']
                    plan,info=resolver_jornada([lookup[t] for t in seqs[k]],'intercambio',d,starts,calendar,tariffs,
                                               limit=min(limit,remaining),conservative=False,deadline=deadline)
                    statuses.append(str(info['estado']))
                    if plan is None:break
                    plan['cadena_fase2']='|'.join(sorted({c for p in old for c in p['cadena_fase2'].split('|')}))
                    cambiar_reservas(calendar,[plan],1)
                    built.append(plan)
                if len(built)==len(seqs) and costo(built,tariffs)<costo(old,tariffs)-1e-5:
                    return built,statuses
            finally:
                cambiar_reservas(calendar,built,-1)
    finally:
        cambiar_reservas(calendar,old,1)
    return None,statuses

def evaluar_conjunto(old,seqs,lookup,d,starts,calendar,tariffs,limit,deadline):
    from metodo_hibrido.conjunta import resolver_conjunto
    cambiar_reservas(calendar,old,-1)
    try:
        if time.perf_counter()>=deadline:return None,['presupuesto']
        chain='|'.join(sorted({c for p in old for c in p['cadena_fase2'].split('|')}))
        plans,info=resolver_conjunto([[lookup[t] for t in seq] for seq in seqs],chain,d,starts,calendar,tariffs,
                                    limit=min(limit,deadline-time.perf_counter()),deadline=deadline)
        status=[str(info['estado']),f"fisicas={info.get('restricciones_fisicas',0)}",f"conexiones={info.get('restricciones_conexiones',0)}"]
        if plans and costo(plans,tariffs)<costo(old,tariffs)-1e-5:return plans,status
        return None,status
    finally:cambiar_reservas(calendar,old,1)

def buscar(plans,lookup,d,starts,physical,plugs,tariffs,t0,horizon,budget=120.,local_limit=2.,neighbors=8,per_pair=3,max_rounds=3,coordination='secuencial'):
    if coordination not in ('secuencial','conjunta'):raise ValueError('Coordinación desconocida')
    tick=time.perf_counter();deadline=tick+budget
    current=[dict(p) for p in plans]
    expected=[lookup[t] for p in current for t in p['corridas']]
    params=(d,starts,physical,plugs,tariffs,t0,horizon)
    verificar(current,expected,*params)
    calendar=Calendario(physical,plugs,t0,horizon);cambiar_reservas(calendar,current,1)
    history=[];attempts=0;last_message=tick;stop='rondas';rounds=0
    for round_no in range(max_rounds):
        rounds=round_no+1
        candidates=[];seen_pairs=set()
        preparation_deadline=min(deadline,time.perf_counter()+min(15.,budget*.2))
        # Jornadas cortas primero: son candidatas a ser absorbidas por otras.
        for i in sorted(range(len(current)),key=lambda i:(len(current[i]['corridas']),current[i]['bus_id'])):
            if time.perf_counter()>=preparation_deadline:break
            a=current[i]
            neighbors_rank=[]
            for j,b in enumerate(current):
                if i==j or a['sector_id']!=b['sector_id']:continue
                if tuple(sorted((i,j))) in seen_pairs:continue
                # Cercanía espacio-temporal entre enlaces posibles de ambos buses.
                links=[(d['S:'+lookup[x]['fin_stop_id'],'S:'+lookup[y]['inicio_stop_id']][0],
                        lookup[y]['inicio_s']-lookup[x]['fin_s'])
                       for left,right in ((a,b),(b,a)) for x in left['corridas'] for y in right['corridas']
                       if lookup[x]['fin_s']+d['S:'+lookup[x]['fin_stop_id'],'S:'+lookup[y]['inicio_stop_id']][1]<=lookup[y]['inicio_s']]
                if links:neighbors_rank.append((min(km+seconds/3600 for km,seconds in links),j))
            for _,j in sorted(neighbors_rank)[:neighbors]:
                if time.perf_counter()>=preparation_deadline:break
                seen_pairs.add(tuple(sorted((i,j))))
                b=current[j];old_cost=costo([a,b],tariffs)
                alternatives=[]
                for kind,seqs in alternativas(a['corridas'],b['corridas'],lookup,d):
                    if time.perf_counter()>=preparation_deadline:break
                    score=250*len(seqs)+.5*sum(distancia_minima(s,lookup,d,starts,starts+sorted(physical)) for s in seqs)
                    alternatives.append((score,kind,seqs))
                for score,kind,seqs in sorted(alternatives,key=lambda v:(v[0],v[1],v[2]))[:per_pair]:
                    # Servicio constante: solo se usa el costo aproximado para ordenar intentos.
                    service_cost=.5*sum(lookup[t]['distancia_servicio_km'] for s in seqs for t in s)
                    candidates.append((score+service_cost-old_cost,i,j,kind,seqs))
        changed=False;used=set()
        for _,i,j,kind,seqs in sorted(candidates,key=lambda v:(v[0],v[1],v[2],v[3])):
            if time.perf_counter()>=deadline:stop='presupuesto';break
            if i in used or j in used:continue
            old=[current[i],current[j]];attempts+=1
            evaluator=evaluar_conjunto if coordination=='conjunta' else evaluar
            candidate,statuses=evaluator(old,seqs,lookup,d,starts,calendar,tariffs,local_limit,deadline)
            record=dict(ronda=round_no+1,intento=attempts,tipo=kind,bus_a=old[0]['bus_id'],bus_b=old[1]['bus_id'],
                        sector=old[0]['sector_id'],estados=';'.join(statuses),aceptado=False,buses_evitados=0,ahorro_usd=0.)
            if candidate:
                for k,p in enumerate(candidate):p['bus_id']=old[k]['bus_id']
                proposal=[p for index,p in enumerate(current) if index not in (i,j) and p is not None]+candidate
                # expected es fijo: un servicio omitido no desaparece de la auditoría.
                try:
                    verificar(proposal,expected,*params)
                except (AssertionError,KeyError,ValueError) as error:
                    record['estados']+=';rechazado_auditoria:'+str(error)
                else:
                    cambiar_reservas(calendar,old,-1);cambiar_reservas(calendar,candidate,1)
                    record.update(aceptado=True,buses_evitados=2-len(candidate),ahorro_usd=costo(old,tariffs)-costo(candidate,tariffs))
                    current[i]=candidate[0];current[j]=candidate[1] if len(candidate)==2 else None
                    used.update((i,j));changed=True
            history.append(record)
            if time.perf_counter()-last_message>=20:
                print(f'Intercambios: {attempts} intentos, {sum(r["aceptado"] for r in history)} mejoras aceptadas.',flush=True)
                last_message=time.perf_counter()
        current=[p for p in current if p is not None]
        if time.perf_counter()>=deadline:stop='presupuesto';break
        if not changed:stop='sin_mejoras_en_vecindario';break
    verificar(current,expected,*params)
    return current,history,dict(tiempo_busqueda_s=time.perf_counter()-tick,intentos=attempts,rondas=rounds,
                               motivo_fin=stop,mejoras=sum(r['aceptado'] for r in history))
