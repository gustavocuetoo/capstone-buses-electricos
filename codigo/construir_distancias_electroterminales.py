"""Construye parámetros de traslados RED a partir de GTFS y chile.gpkg.

Solo usa la biblioteca estándar y numpy. No modifica fuentes.
Las distancias son aproximaciones sobre la red disponible, no rutas autorizadas.
"""
from __future__ import annotations

import argparse
import csv
import heapq
import json
import math
import sqlite3
import struct
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

EARTH_KM = 6371.0088
ROAD_CLASSES = {
    'motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary',
    'primary_link', 'secondary', 'secondary_link', 'tertiary',
    'tertiary_link', 'unclassified', 'residential', 'living_street',
    'service', 'busway',
}


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as file:
        yield from csv.DictReader(file)


def write_csv(path, rows):
    assert rows
    with path.open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def haversine(a, b):
    lon1, lat1, lon2, lat2 = map(math.radians, (*a, *b))
    value = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 2 * EARTH_KM * math.asin(min(1, math.sqrt(value)))


def gpkg_line(blob):
    """Lee LineString 2D WKB con encabezado binario GeoPackage."""
    assert blob[:2] == b'GP'
    envelope = (blob[3] >> 1) & 7
    offset = 8 + {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[envelope]
    endian = '<' if blob[offset] == 1 else '>'
    kind, count = struct.unpack_from(endian+'II', blob, offset+1)
    if kind != 2:
        raise ValueError(f'Geometría no soportada: {kind}')
    values = struct.unpack_from(endian+'d'*(count*2), blob, offset+9)
    return list(zip(values[::2], values[1::2]))


def dijkstra(graph, source):
    dist = [math.inf] * len(graph)
    dist[source] = 0.0
    queue = [(0.0, source)]
    while queue:
        current, node = heapq.heappop(queue)
        if current != dist[node]:
            continue
        for target, length in graph[node]:
            value = current + length
            if value < dist[target]:
                dist[target] = value
                heapq.heappush(queue, (value, target))
    return dist


def load_gtfs(base):
    routes = {r['route_id']: r for r in read_csv(base/'gtfs/routes.txt')
              if r['agency_id'] == 'RM' and r['route_type'] == '3'}
    trips = {r['trip_id']: r for r in read_csv(base/'gtfs/trips.txt')
             if r['route_id'] in routes and r['service_id'] in {'L', 'S', 'D'}}
    ends = {}
    for row in read_csv(base/'gtfs/stop_times.txt'):
        trip = row['trip_id']
        if trip not in trips:
            continue
        sequence = int(row['stop_sequence'])
        if trip not in ends:
            ends[trip] = [sequence, row['stop_id'], sequence, row['stop_id']]
        else:
            v = ends[trip]
            if sequence < v[0]:
                v[0:2] = [sequence, row['stop_id']]
            if sequence > v[2]:
                v[2:4] = [sequence, row['stop_id']]
    assert set(ends) == set(trips), 'Patrones sin paradas'
    groups = defaultdict(list)
    for trip, row in trips.items():
        start, end = ends[trip][1], ends[trip][3]
        key = (row['route_id'], row['direction_id'], row['shape_id'], start, end)
        groups[key].append(trip)
    variants, mapping = [], []
    for i, key in enumerate(sorted(groups), 1):
        route, direction, shape, start, end = key
        variant = f'V{i:04d}'
        variants.append(dict(variante_id=variant, route_id=route,
                             direction_id=direction, shape_id=shape,
                             inicio_stop_id=start, fin_stop_id=end))
        for trip in sorted(groups[key]):
            mapping.append(dict(trip_id=trip, service_id=trips[trip]['service_id'],
                                variante_id=variant))
    required = {v[k] for v in variants for k in ('inicio_stop_id', 'fin_stop_id')}
    stops = {r['stop_id']: r for r in read_csv(base/'gtfs/stops.txt') if r['stop_id'] in required}
    assert set(stops) == required, 'Extremos sin coordenadas'
    return routes, variants, mapping, stops


def build_graph(base, bbox):
    conn = sqlite3.connect((base/'chile.gpkg').resolve().as_uri()+'?mode=ro', uri=True)
    placeholders = ','.join('?' for _ in ROAD_CLASSES)
    sql = f'''SELECT fid,geom,oneway,fclass,name,layer,bridge,tunnel
              FROM gis_osm_roads_free WHERE fclass IN ({placeholders}) ORDER BY fid'''
    xmin, xmax, ymin, ymax = bbox
    graph, reverse, coords, lookup, segments = [], [], [], {}, []

    def add_node(point):
        # Only existing geometry vertices are joined; geometrical crossings are not noded.
        if point not in lookup:
            lookup[point] = len(graph)
            coords.append(point)
            graph.append([])
            reverse.append([])
        return lookup[point]

    def add_edge(u, v, length):
        graph[u].append((v, length))
        reverse[v].append((u, length))

    roads = 0
    for fid, blob, one, road_class, name, layer, bridge, tunnel in conn.execute(sql, sorted(ROAD_CLASSES)):
        envelope = (blob[3] >> 1) & 7
        if envelope:
            endian = '<' if blob[3] & 1 else '>'
            x0,x1,y0,y1 = struct.unpack_from(endian+'dddd',blob,8)
            if x1<xmin or x0>xmax or y1<ymin or y0>ymax:
                continue
        else:
            check_points = gpkg_line(blob)
            xx,yy = zip(*check_points)
            if max(xx)<xmin or min(xx)>xmax or max(yy)<ymin or min(yy)>ymax:
                continue
        assert one in {'F','T','B'}, f'oneway inesperado {one}'
        points = gpkg_line(blob)
        roads += 1
        for a, b in zip(points, points[1:]):
            if a == b:
                continue
            u, v = add_node(a), add_node(b)
            length = haversine(a, b)
            forward, backward = one in {'F','B'}, one in {'T','B'}
            if forward:
                add_edge(u, v, length)
            if backward:
                add_edge(v, u, length)
            segments.append((u,v,length,forward,backward,fid,road_class,name or '',layer,bridge,tunnel))
    conn.close()
    print(f'Red: {roads} vías, {len(graph)} vértices, {len(segments)} segmentos', flush=True)
    return graph, reverse, coords, segments, add_edge, roads


def attach_locations(locations, graph, reverse, coords, segments, add_edge):
    # Project each point to the closest ground-level non-motorway segment.
    # Access connectors are an explicit geometric approximation, not measured driveways.
    ids = [i for i,s in enumerate(segments) if s[6] not in {'motorway','motorway_link'}
           and s[8] in (0,None) and s[9] != 'T' and s[10] != 'T']
    lat0 = math.radians(sum(p[1] for p in locations.values())/len(locations))
    scale = np.array([111.1950802335329*math.cos(lat0), 111.1950802335329])
    a = np.array([coords[segments[i][0]] for i in ids])*scale
    b = np.array([coords[segments[i][1]] for i in ids])*scale
    delta = b-a
    norm = np.sum(delta*delta, axis=1)
    minimum,maximum = np.minimum(a,b),np.maximum(a,b)
    additions, snaps = defaultdict(list), {}

    def virtual(point):
        index = len(graph)
        graph.append([])
        reverse.append([])
        coords.append(point)
        return index

    for count,(key, point) in enumerate(sorted(locations.items()),1):
        p = np.array(point)*scale
        radius = 0.25
        while True:
            candidates = np.flatnonzero((maximum[:,0]>=p[0]-radius)&(minimum[:,0]<=p[0]+radius)
                                       &(maximum[:,1]>=p[1]-radius)&(minimum[:,1]<=p[1]+radius))
            if len(candidates):
                t = np.clip(np.sum((p-a[candidates])*delta[candidates],axis=1)/norm[candidates],0,1)
                projected = a[candidates]+t[:,None]*delta[candidates]
                squared = np.sum((projected-p)**2,axis=1)
                local = int(np.argmin(squared))
                # Certifies that a segment excluded by the square cannot be closer.
                if squared[local] <= radius*radius:
                    break
            radius *= 2
        position = int(candidates[local])
        segment_id = ids[position]
        segment = segments[segment_id]
        fraction = float(t[local])
        snap_point = tuple(projected[local]/scale)
        access = haversine(point,snap_point)
        snap_node = virtual(snap_point)
        point_node = virtual(point)
        add_edge(point_node,snap_node,access)
        add_edge(snap_node,point_node,access)
        additions[segment_id].append((fraction,snap_node))
        snaps[key] = dict(node=point_node, acceso_km=access,
                          lon_red=snap_point[0],lat_red=snap_point[1],
                          via_fid=segment[5],via_clase=segment[6],via_nombre=segment[7])
        if count % 100 == 0:
            print(f'Accesos calculados: {count}/{len(locations)}',flush=True)
    for segment_id, cuts in additions.items():
        u,v,length,forward,backward,*_ = segments[segment_id]
        ordered = [(0,u),*sorted(cuts),(1,v)]
        for (left,x),(right,y) in zip(ordered,ordered[1:]):
            weight = (right-left)*length
            if forward:
                add_edge(x,y,weight)
            if backward:
                add_edge(y,x,weight)
    return snaps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--output', type=Path, default=Path('output/distancias_electroterminales'))
    parser.add_argument('--margen-grados', type=float, default=0.4)
    parser.add_argument('--revision-acceso-m', type=float, default=100)
    args = parser.parse_args()
    base = args.base.resolve()
    output = args.output if args.output.is_absolute() else base/args.output
    output.mkdir(parents=True,exist_ok=True)
    routes, variants, mapping, stops = load_gtfs(base)
    depots = list(read_csv(base/'depots.csv'))
    locations = {f'S:{k}':(float(v['stop_lon']),float(v['stop_lat'])) for k,v in stops.items()}
    locations.update({f'D:{d["depot_id"]}':(float(d['lon']),float(d['lat'])) for d in depots})
    print(f'GTFS: {len(routes)} rutas, {len(mapping)} patrones, {len(variants)} variantes, {len(stops)} extremos únicos',flush=True)
    xs,ys = zip(*locations.values())
    margin = args.margen_grados
    bbox = [min(xs)-margin,max(xs)+margin,min(ys)-margin,max(ys)+margin]
    graph,reverse,coords,segments,add_edge,roads = build_graph(base,bbox)
    snaps = attach_locations(locations,graph,reverse,coords,segments,add_edge)
    result, samples = [], []
    candidates = list(sorted(stops))
    test_stops = (candidates[0],candidates[len(candidates)//2],candidates[-1])
    references = {}
    for depot in depots:
        key = 'D:'+depot['depot_id']
        depot_node = snaps[key]['node']
        outward = dijkstra(graph,depot_node)
        inward = dijkstra(reverse,depot_node)
        print(f'Distancias calculadas: {depot["nombre"]}',flush=True)
        for variant in variants:
            start_key,end_key = 'S:'+variant['inicio_stop_id'],'S:'+variant['fin_stop_id']
            start,end = snaps[start_key],snaps[end_key]
            for movement,stop_key,snap,value in (
                ('fin_a_electroterminal',end_key,end,inward[end['node']]),
                ('electroterminal_a_inicio',start_key,start,outward[start['node']]),
            ):
                access = snap['acceso_km']+snaps[key]['acceso_km']
                connected = math.isfinite(value)
                straight = haversine(locations[stop_key],locations[key])
                if connected:
                    assert value+0.001 >= straight, 'Distancia vial menor que distancia directa'
                    assert value+1e-8 >= access
                status = 'sin_camino_en_red' if not connected else (
                    'revisar_acceso' if max(snap['acceso_km'],snaps[key]['acceso_km'])*1000 > args.revision_acceso_m
                    else 'calculada')
                result.append({
                    **variant, 'depot_id':depot['depot_id'],'electroterminal':depot['nombre'],
                    'movimiento':movement,'extremo_stop_id':stop_key[2:],
                    'distancia_km':round(value,4) if connected else '',
                    'distancia_red_km':round(max(0,value-access),4) if connected else '',
                    'acceso_extremo_m':round(snap['acceso_km']*1000,2),
                    'acceso_electroterminal_m':round(snaps[key]['acceso_km']*1000,2),
                    'distancia_directa_km':round(straight,4),
                    'estado':status,
                })
        for stop in test_stops:
            references[stop,depot['depot_id']] = inward[snaps['S:'+stop]['node']]
    # Three independent forward searches check fifteen reverse results.
    for stop in test_stops:
        check = dijkstra(graph,snaps['S:'+stop]['node'])
        for depot in depots:
            test = check[snaps['D:'+depot['depot_id']]['node']]
            reference = references[stop,depot['depot_id']]
            assert (math.isinf(test) and math.isinf(reference)) or abs(test-reference)<1e-7
            samples.append({'stop_id':stop,'depot_id':depot['depot_id'],'coincide':True})
    result.sort(key=lambda r:(r['variante_id'],int(r['depot_id']),r['movimiento']))
    assert len(result)==len(variants)*len(depots)*2
    keys={(r['variante_id'],r['depot_id'],r['movimiento']) for r in result}
    assert len(keys)==len(result)
    summary = dict(rutas=len(routes),patrones=len(mapping),variantes=len(variants),
                   extremos_unicos=len(stops),electroterminales=len(depots),filas=len(result),
                   estados=dict(Counter(r['estado'] for r in result)),
                   bbox=bbox,margen_grados=margin,vias=roads,nodos=len(graph),segmentos=len(segments),
                   umbral_revision_acceso_m=args.revision_acceso_m,
                   pruebas_busqueda_inversa=len(samples),
                   accesos_electroterminales_m={d['nombre']:round(snaps['D:'+d['depot_id']]['acceso_km']*1000,2) for d in depots})
    write_csv(output/'distancias_recorridos_electroterminales.csv',result)
    write_csv(output/'patrones_variantes.csv',mapping)
    access_rows=[]
    for key,snap in sorted(snaps.items()):
        lon,lat=locations[key]
        access_rows.append(dict(tipo='electroterminal' if key.startswith('D:') else 'parada',
                               id=key[2:],lon=lon,lat=lat,
                               **{k:v for k,v in snap.items() if k!='node'}))
    # QA details are supplementary; the two CSVs above are the model interface.
    (output/'accesos_revision.json').write_text(json.dumps(access_rows,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'validacion.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)


if __name__ == '__main__':
    main()
