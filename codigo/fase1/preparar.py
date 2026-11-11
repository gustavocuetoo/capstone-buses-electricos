"""Genera corridas, sectores y matriz de traslados viales para la fase 1."""
import sys
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'.deps'))
sys.path.insert(0,str(BASE))
import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
import numpy as np
from scipy.sparse import csr_matrix, save_npz
from scipy.sparse.csgraph import dijkstra as sparse_dijkstra
from construir_distancias_electroterminales import read_csv,write_csv,load_gtfs,build_graph,attach_locations,haversine
from calcular_peak_buses import a_segundos

OUT=BASE/'output/fase1'

def preparar_corridas(config):
    OUT.mkdir(parents=True,exist_ok=True)
    routes,variants,mapping,stops=load_gtfs(BASE)
    variant_by_id={v['variante_id']:v for v in variants}
    trip_variant={r['trip_id']:r['variante_id'] for r in mapping}
    trips={r['trip_id']:r for r in read_csv(BASE/'gtfs/trips.txt') if r['trip_id'] in trip_variant}
    timing={}
    for r in read_csv(BASE/'gtfs/stop_times.txt'):
        key=r['trip_id']
        if key not in trips: continue
        seq=int(r['stop_sequence'])
        if key not in timing: timing[key]=[seq,a_segundos(r['departure_time']),seq,a_segundos(r['arrival_time'])]
        else:
            v=timing[key]
            if seq<v[0]: v[:2]=[seq,a_segundos(r['departure_time'])]
            if seq>v[2]: v[2:]=[seq,a_segundos(r['arrival_time'])]
    lengths={r['shape_id']:float(r['distance_km']) for r in read_csv(BASE/'shape_distances.csv')}
    # Both directions and all variants of a route stay in the same sector.
    score=defaultdict(float)
    for r in read_csv(BASE/'output/distancias_electroterminales/distancias_recorridos_electroterminales.csv'):
        if not r['distancia_km']: raise ValueError('Distancia a electroterminal ausente')
        score[r['route_id'],r['depot_id']]+=float(r['distancia_km'])
    sectors={route:min((str(i) for i in range(1,6)),key=lambda dep:score[route,dep]) for route in routes}
    write_csv(OUT/'sectores.csv',[{'route_id':r,'sector_id':sectors[r]} for r in sorted(routes)])
    rows=[]
    for freq_index,r in enumerate(read_csv(BASE/'gtfs/frequencies.txt')):
        trip=r['trip_id']
        if trip not in trips: continue
        v=variant_by_id[trip_variant[trip]]
        t=timing[trip]
        duration=t[3]-t[1]
        if duration<=0: raise ValueError(f'Duración no positiva: {trip}')
        headway=int(r['headway_secs'])
        if headway<=0: raise ValueError('Headway no positivo')
        for k,start in enumerate(range(a_segundos(r['start_time']),a_segundos(r['end_time']),headway)):
            rows.append(dict(corrida_id=f'{trip}__f{freq_index}__n{k}',trip_id=trip,
                             service_id=trips[trip]['service_id'],**v,
                             sector_id=sectors[v['route_id']],inicio_s=start,fin_s=start+duration,
                             distancia_servicio_km=lengths[v['shape_id']]))
    rows.sort(key=lambda r:(r['service_id'],r['inicio_s'],r['corrida_id']))
    assert len({r['corrida_id'] for r in rows})==len(rows)
    write_csv(OUT/'corridas.csv',rows)
    counts={d:sum(r['service_id']==d for r in rows) for d in ['L','S','D']}
    print('Corridas reconstruidas',counts,flush=True)
    return variants,stops,counts

def preparar_distancias(config,variants,stops,allow_pending):
    terminals=json.loads((BASE/'fase1/terminales_espera.json').read_text(encoding='utf-8'))
    pending=[t['terminal_id'] for t in terminals if t['lat'] is None or t['lon'] is None]
    if pending and not allow_pending:
        raise ValueError(f'Terminales pendientes: {pending}. Confirmar coordenadas o usar --permitir-pendientes para un prototipo explícito.')
    active=[t for t in terminals if t['terminal_id'] not in pending]
    if not active: raise ValueError('Sin terminales activos')
    locations={f'S:{k}':(float(v['stop_lon']),float(v['stop_lat'])) for k,v in stops.items()}
    locations.update({t['terminal_id']:(t['lon'],t['lat']) for t in active})
    fingerprint=hashlib.sha256(json.dumps(locations,sort_keys=True).encode()).hexdigest()
    xs,ys=zip(*locations.values())
    graph,reverse,coords,segments,add_edge,roads=build_graph(BASE,[min(xs)-.4,max(xs)+.4,min(ys)-.4,max(ys)+.4])
    snaps=attach_locations(locations,graph,reverse,coords,segments,add_edge)
    # CSR without summed parallel edges: each ordered pair keeps its minimum length.
    indices=[]; data=[]; indptr=[0]
    for neighbors in graph:
        unique={}
        for target,weight in neighbors:
            unique[target]=min(weight,unique.get(target,math.inf))
        for target,weight in sorted(unique.items()): indices.append(target);data.append(weight)
        indptr.append(len(indices))
    matrix=csr_matrix((np.array(data),np.array(indices,dtype=np.int32),np.array(indptr,dtype=np.int32)),shape=(len(graph),len(graph)))
    save_npz(OUT/'red_vial_cache.npz',matrix)
    (OUT/'puntos_red_cache.json').write_text(json.dumps({'fingerprint':fingerprint,'locations':locations,'snaps':snaps},ensure_ascii=False),encoding='utf-8')
    del graph,reverse,coords,segments,indices,data,indptr,add_edge
    starts=sorted({'S:'+v['inicio_stop_id'] for v in variants})
    ends=sorted({'S:'+v['fin_stop_id'] for v in variants})
    tids=[t['terminal_id'] for t in active]
    sources=ends+tids
    # A source may also be a start. Only requested direction pairs are exported.
    count=missing=0
    with (OUT/'traslados.csv').open('w',encoding='utf-8-sig',newline='') as file:
        fields=['origen_id','destino_id','distancia_km','tiempo_s','acceso_origen_m','acceso_destino_m','estado']
        writer=csv.DictWriter(file,fieldnames=fields);writer.writeheader()
        for index,source in enumerate(sources):
            distances=sparse_dijkstra(matrix,directed=True,indices=snaps[source]['node'])
            targets=starts+tids if source.startswith('S:') else starts
            for target in targets:
                if source==target: distance=0.0
                else: distance=float(distances[snaps[target]['node']])
                state='calculada'
                if not math.isfinite(distance): state='sin_camino_en_red';missing+=1
                elif max(snaps[source]['acceso_km'],snaps[target]['acceso_km'])>.1: state='revisar_acceso'
                if math.isfinite(distance):
                    assert distance+.001>=haversine(locations[source],locations[target])
                # Ceil avoids claiming a connection feasible by rounding down.
                seconds=(0 if source==target else max(1,math.ceil(distance/config['velocidad_vacio_kmh']*3600))) if math.isfinite(distance) else ''
                writer.writerow(dict(origen_id=source,destino_id=target,distancia_km=round(distance,6) if math.isfinite(distance) else '',
                                     tiempo_s=seconds,acceso_origen_m=round(snaps[source]['acceso_km']*1000,2),
                                     acceso_destino_m=round(snaps[target]['acceso_km']*1000,2),estado=state))
                count+=1
            if index%25==0 or index==len(sources)-1: print(f'Rutas viales: {index+1}/{len(sources)} orígenes',flush=True)
    meta={'terminales_activos':tids,'terminales_pendientes':pending,'velocidad_kmh':config['velocidad_vacio_kmh'],
          'conexiones':count,'sin_camino':missing,'fingerprint':fingerprint,
          'accesos_terminales_m':{t:round(snaps[t]['acceso_km']*1000,2) for t in tids}}
    (OUT/'metadatos.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(meta,ensure_ascii=False,indent=2),flush=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--permitir-pendientes',action='store_true')
    parser.add_argument('--solo-corridas',action='store_true')
    args=parser.parse_args()
    config=json.loads((BASE/'fase1/configuracion.json').read_text(encoding='utf-8'))
    if config['velocidad_vacio_kmh']<=0: raise ValueError('Velocidad debe ser positiva')
    variants,stops,_=preparar_corridas(config)
    if not args.solo_corridas: preparar_distancias(config,variants,stops,args.permitir_pendientes)

if __name__=='__main__':main()
