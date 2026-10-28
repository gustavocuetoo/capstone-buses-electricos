"""Vecindario de tres jornadas: absorción repartida y rotación de sufijos."""
import itertools
import time
from collections import Counter
from tres_fases.intercambios import compatible,distancia_minima,evaluar_conjunto
from tres_fases.fase3 import Calendario
from tres_fases.reparar import cambiar_reservas,costo
from tres_fases.verificar import verificar

def insertar(ids,trip,lookup,d):
    for k in range(len(ids)+1):
        # Solo cambian los enlaces vecinos de la inserción.
        if k and not compatible([ids[k-1],trip],lookup,d):continue
        if k<len(ids) and not compatible([trip,ids[k]],lookup,d):continue
        yield ids[:k]+[trip]+ids[k:]

def propuestas(seqs,lookup,d,starts,finals,width=4,deadline=None):
    """Reparte la primera jornada entre las otras dos mediante un haz acotado."""
    def expired():return deadline is not None and time.perf_counter()>=deadline
    expected=Counter(t for s in seqs for t in s)
    seen={tuple(sorted(tuple(s) for s in seqs))}
    states=[[list(seqs[1]),list(seqs[2])]]
    for trip in seqs[0]:
        if expired():return
        next_states={}
        for state in states:
            for b in range(2):
                for inserted in insertar(state[b],trip,lookup,d):
                    candidate=[inserted if i==b else state[i] for i in range(2)]
                    key=tuple(sorted(tuple(s) for s in candidate))
                    empty=sum(distancia_minima(s,lookup,d,starts,finals) for s in candidate)
                    balance=sum(sum(lookup[t]['distancia_servicio_km'] for t in s)**2 for s in candidate)
                    next_states[key]=(.5*empty+.002*balance,candidate)
        states=[v[1] for v in sorted(next_states.values(),key=lambda v:(v[0],v[1]))[:width]]
        if not states:break
    for candidate in states:
        if expired():return
        key=tuple(sorted(tuple(s) for s in candidate))
        if key not in seen:
            assert Counter(t for s in candidate for t in s)==expected
            seen.add(key);yield 'absorcion_3_a_2',candidate
    # Coordinación genuina de tres buses: rotar las tres colas, sin cambiar prefijos.
    cuts=[sorted({0,len(s)//2,len(s)}) for s in seqs]
    for cut in itertools.product(*cuts):
        if expired():return
        for step in (1,2):
            candidate=[seqs[i][:cut[i]]+seqs[(i+step)%3][cut[(i+step)%3]:] for i in range(3)]
            candidate=[s for s in candidate if s]
            key=tuple(sorted(tuple(s) for s in candidate))
            if key in seen or not all(compatible(s,lookup,d) for s in candidate):continue
            assert Counter(t for s in candidate for t in s)==expected
            seen.add(key);yield 'rotacion_3',candidate

def buscar_trios(plans,lookup,d,starts,physical,plugs,tariffs,t0,horizon,budget=120.,local_limit=2.,neighbors=8,per_pair=3,max_rounds=3,coordination='conjunta'):
    if coordination!='conjunta':raise ValueError('Tres jornadas requieren coordinación conjunta')
    tick=time.perf_counter();deadline=tick+budget
    current=[dict(p) for p in plans];expected=[lookup[t] for p in current for t in p['corridas']]
    params=(d,starts,physical,plugs,tariffs,t0,horizon)
    verificar(current,expected,*params)
    calendar=Calendario(physical,plugs,t0,horizon);cambiar_reservas(calendar,current,1)
    history=[];attempts=0;rounds=0;stop='rondas';last_message=tick
    for round_no in range(max_rounds):
        rounds=round_no+1;candidates=[];seen_groups=set()
        preparation_deadline=min(deadline,time.perf_counter()+min(15.,budget*.2))
        for i in sorted(range(len(current)),key=lambda i:(len(current[i]['corridas']),current[i]['bus_id'])):
            if time.perf_counter()>=preparation_deadline:break
            donor=current[i];ranks=[]
            for j,p in enumerate(current):
                if time.perf_counter()>=preparation_deadline:break
                if i==j or p['sector_id']!=donor['sector_id']:continue
                can=[t for t in donor['corridas'] if next(insertar(p['corridas'],t,lookup,d),None) is not None]
                if can:
                    # Prioriza receptores compatibles con muchos servicios y de baja carga de trabajo.
                    ranks.append((-len(can),len(p['corridas']),j))
            nearest=[j for _,_,j in sorted(ranks)[:neighbors]]
            for j,k in itertools.combinations(nearest,2):
                if time.perf_counter()>=preparation_deadline:break
                group=tuple(sorted((i,j,k)))
                if group in seen_groups:continue
                seen_groups.add(group)
                old=[current[q] for q in (i,j,k)];old_cost=costo(old,tariffs)
                choices=[]
                for kind,seqs in propuestas([p['corridas'] for p in old],lookup,d,starts,starts+sorted(physical),deadline=preparation_deadline):
                    score=250*len(seqs)+.5*(sum(distancia_minima(s,lookup,d,starts,starts+sorted(physical)) for s in seqs)
                                           +sum(lookup[t]['distancia_servicio_km'] for s in seqs for t in s))-old_cost
                    choices.append((score,kind,seqs))
                for score,kind,seqs in sorted(choices,key=lambda v:(v[0],v[1],v[2]))[:per_pair]:
                    candidates.append((score,(i,j,k),kind,seqs))
        used=set();changed=False
        for _,indices,kind,seqs in sorted(candidates,key=lambda v:(v[0],v[1],v[2])):
            if time.perf_counter()>=deadline:stop='presupuesto';break
            if any(i in used for i in indices):continue
            old=[current[i] for i in indices];attempts+=1
            candidate,status=evaluar_conjunto(old,seqs,lookup,d,starts,calendar,tariffs,local_limit,deadline)
            record=dict(ronda=round_no+1,intento=attempts,tipo=kind,bus_a=old[0]['bus_id'],bus_b=old[1]['bus_id'],
                        bus_c=old[2]['bus_id'],sector=old[0]['sector_id'],estados=';'.join(status),aceptado=False,
                        buses_evitados=0,ahorro_usd=0.)
            if candidate:
                for k,p in enumerate(candidate):p['bus_id']=old[k]['bus_id']
                proposal=[p for q,p in enumerate(current) if p is not None and q not in indices]+candidate
                try:verificar(proposal,expected,*params)
                except (AssertionError,ValueError,KeyError) as error:record['estados']+=';rechazado_auditoria:'+str(error)
                else:
                    cambiar_reservas(calendar,old,-1);cambiar_reservas(calendar,candidate,1)
                    for k,i in enumerate(indices):current[i]=candidate[k] if k<len(candidate) else None
                    record.update(aceptado=True,buses_evitados=3-len(candidate),ahorro_usd=costo(old,tariffs)-costo(candidate,tariffs))
                    changed=True;used.update(indices)
            history.append(record)
            if time.perf_counter()-last_message>=20:
                print(f'Trios: {attempts} intentos, {sum(r["aceptado"] for r in history)} mejoras aceptadas.',flush=True)
                last_message=time.perf_counter()
        current=[p for p in current if p is not None]
        if time.perf_counter()>=deadline:stop='presupuesto';break
        if not changed:stop='sin_mejoras_en_vecindario';break
    verificar(current,expected,*params)
    return current,history,dict(tiempo_busqueda_s=time.perf_counter()-tick,intentos=attempts,rondas=rounds,
                               motivo_fin=stop,mejoras=sum(r['aceptado'] for r in history))
