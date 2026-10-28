"""Utilidades de lectura, reconstrucción y auditoría del caso base sin recargas."""
import argparse
import csv
import hashlib
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path
from validador_grupo import verificar

RATE, BATTERY, RESERVE = 1.4, 350., 35.
ROOT = Path(__file__).resolve().parent


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')


def save_csv(path, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def load(folder):
    cfg = json.loads((folder/'escenario.json').read_text(encoding='utf-8-sig'))
    fixed = dict(bateria_kwh=350,reserva_kwh=35,consumo_kwh_km=1.4,velocidad_vacio_kmh=18,
                 potencia_kw=180,bloque_s=300,costo_bus=250,costo_km=.5,costo_sesion=5)
    for k,v in fixed.items():
        if cfg.get('parametros',{}).get(k,v) != v: raise ValueError('Parámetro no compatible: '+k)
    trips = read_csv(folder/'corridas.csv')
    for t in trips:
        for k in ('inicio_s','fin_s'): t[k]=int(t[k])
        t['distancia_servicio_km']=float(t['distancia_servicio_km'])
        if t['service_id']!='L' or t['fin_s']<=t['inicio_s']: raise ValueError('Servicio inválido')
    lookup={t['corrida_id']:t for t in trips}
    if len(lookup)!=len(trips): raise ValueError('Corridas duplicadas')
    distances={}
    for row in read_csv(folder/'distancias.csv'):
        key=(row['origen_id'],row['destino_id'])
        if key in distances: raise ValueError('Distancia duplicada')
        if row.get('estado')=='sin_camino': continue
        km=float(row['distancia_km'])
        if not math.isfinite(km) or km<0: raise ValueError('Distancia inválida')
        distances[key]=(km,math.ceil(km*200))
    chains=json.loads((folder/'cadenas.json').read_text(encoding='utf8'))['cadenas']
    covered=Counter(i for c in chains for i in c['corridas'])
    if covered!=Counter(lookup.keys()): raise ValueError('Las cadenas deben cubrir todos los servicios una vez')
    for c in chains:
        if not c['corridas']: raise ValueError('Cadena vacía')
        for i,j in zip(c['corridas'],c['corridas'][1:]):
            a,b=lookup[i],lookup[j]
            km,dt=distances['S:'+a['fin_stop_id'],'S:'+b['inicio_stop_id']]
            if a['sector_id']!=b['sector_id'] or a['fin_s']+dt>b['inicio_s']:
                raise ValueError('Cadena incompatible: '+c['id'])
    return cfg,trips,lookup,distances,chains


def tariff(s,cfg):
    hour=(s%86400)/3600
    return next(p for a,b,p in cfg['tarifas'] if a<=hour<b)


def terminals(t,d,cfg,include_e=True):
    """Un T inicial y un T final por corrida; E finales opcionales. Restricción explícita."""
    o,e='S:'+t['inicio_stop_id'],'S:'+t['fin_stop_id']
    starts=[a for a in cfg['terminales_espera'] if (a,o) in d
            and cfg['inicio_horizonte_s']+d[a,o][1]<=t['inicio_s']]
    ends=[a for a in cfg['terminales_espera'] if (e,a) in d
          and t['fin_s']+d[e,a][1]<=cfg['fin_horizonte_s']]
    if not starts or not ends: raise ValueError('Sin terminal común: '+t['corrida_id'])
    begin=min(starts,key=lambda a:(d[a,o][0],a))
    end=min(ends,key=lambda a:(d[e,a][0],a))
    if RATE*(d[begin,o][0]+t['distancia_servicio_km']+d[e,end][0])>BATTERY-RESERVE+1e-7:
        raise ValueError('No se obtiene respaldo individual sin recarga: '+t['corrida_id'])
    finals=[end]
    if include_e:
        finals += [a for a in sorted(cfg['capacidad_fisica']) if (e,a) in d
                   and t['fin_s']+d[e,a][1]<=cfg['fin_horizonte_s']
                   and RATE*(t['distancia_servicio_km']+d[e,a][0])<=BATTERY-RESERVE+1e-7]
    return begin,end,finals


def act(kind,o,e,s,f,km=0.,q=0.,trip=''):
    return dict(tipo=kind,origen=o,destino=e,inicio_s=int(s),fin_s=int(f),
                distancia_km=float(km),carga_kwh=float(q),corrida_id=trip)


def plans_from_selection(chains,lookup,d,cfg,term,links,charges,ends):
    plans=[]
    for chain in chains:
        segments=[];cur=[]
        for i in chain['corridas']:
            if cur and (cur[-1],i) not in links:segments.append(cur);cur=[]
            cur.append(i)
        if cur:segments.append(cur)
        for segment in segments:
            acts=[];now=cfg['inicio_horizonte_s'];loc=term[segment[0]][0]
            begin=loc
            def wait(end):
                nonlocal now
                if end<now:raise ValueError('Espera negativa')
                if end>now:acts.append(act('espera',loc,loc,now,end));now=end
            def move(target):
                nonlocal now,loc
                km,dt=d[loc,target]
                if dt:acts.append(act('vacio',loc,target,now,now+dt,km));now+=dt
                elif loc!=target:raise ValueError('IDs distintos con tiempo cero')
                loc=target
            for k,i in enumerate(segment):
                t=lookup[i];target='S:'+t['inicio_stop_id']
                c=charges.get((segment[k-1],i)) if k else None
                if c:
                    w,q=c;wait(w['start']-w['dt1']);move(w['e'])
                    for start in range(w['start'],w['end'],300):
                        acts.append(act('carga',loc,loc,start,start+300,q=max(0.,q)/w['n']))
                    now=w['end'];move(target)
                else:
                    wait(t['inicio_s']-d[loc,target][1]);move(target)
                wait(t['inicio_s'])
                loc='S:'+t['fin_stop_id'];now=t['fin_s']
                acts.append(act('servicio',target,loc,t['inicio_s'],now,t['distancia_servicio_km'],trip=i))
            final=ends[segment[-1]];move(final);wait(cfg['fin_horizonte_s'])
            plans.append(dict(bus_id=f'M{len(plans)+1:05d}',cadena_fase2=chain['id'],
                              sector_id=lookup[segment[0]]['sector_id'],terminal_inicial=begin,
                              terminal_final=final,corridas=segment,actividades=acts))
    return plans


def params(cfg,trips,d):
    return (trips,d,cfg['terminales_espera'],cfg['capacidad_fisica'],cfg['conexiones'],
            cfg['tarifas'],cfg['inicio_horizonte_s'],cfg['fin_horizonte_s'])


def initial_plan(chains,lookup,d,cfg,term):
    links=set();energy={};ends={i:term[i][1] for i in lookup}
    for c in chains:
        previous=None
        for i in c['corridas']:
            t=lookup[i];o,e='S:'+t['inicio_stop_id'],'S:'+t['fin_stop_id']
            new=350-RATE*(d[term[i][0],o][0]+t['distancia_servicio_km'])
            if previous:
                last=lookup[previous]
                continued=energy[previous]-RATE*(d['S:'+last['fin_stop_id'],o][0]+t['distancia_servicio_km'])
                if continued>=35+RATE*d[e,term[i][1]][0]-1e-7:
                    new=continued;links.add((previous,i))
            energy[i]=new;previous=i
    return plans_from_selection(chains,lookup,d,cfg,term,links,{},ends),links,energy


