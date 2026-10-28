"""Ejecutar: python tres_fases/ejecutar.py --cantidad 15 (o --rutas 101)."""
import sys
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE/'.deps'))
sys.path.insert(0, str(BASE))
import argparse
import json
import time
from collections import defaultdict
from fase1.modelo import crear_red, resolver_red, verificar_y_exportar
from tres_fases.datos import CONFIG, corridas, seleccionar, cargar, guardar, leer
from tres_fases.fase2 import descomponer_energia
from tres_fases.fase3 import construir
from tres_fases.verificar import verificar

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--rutas', default=None, help='IDs separados por comas; todas sus corridas L')
    mode.add_argument('--cantidad', type=int, choices=range(10, 213), metavar='10..212')
    parser.add_argument('--incluir-rutas-desde',type=Path,help='CSV seleccion_rutas.csv de una muestra que se debe conservar')
    parser.add_argument('--limite-segundos', type=int, default=120)
    parser.add_argument('--salida', type=Path)
    args = parser.parse_args()
    start = time.perf_counter()
    rows = corridas()
    if args.incluir_rutas_desde and not args.cantidad:parser.error('--incluir-rutas-desde requiere --cantidad')
    required=[r['route_id'] for r in leer(args.incluir_rutas_desde)] if args.incluir_rutas_desde else []
    routes = seleccionar(rows, args.cantidad,required) if args.cantidad else (args.rutas or '101').split(',')
    out = args.salida or BASE/'output/tres_fases'/('muestra_'+str(args.cantidad) if args.cantidad else 'rutas_'+'_'.join(routes))
    out.mkdir(parents=True, exist_ok=True)
    trips, distances, starts, physical, plugs, tariffs = cargar(routes, rows)
    groups = defaultdict(list)
    for t in trips:
        groups[t['route_id']].append(t)
    guardar(out/'seleccion_rutas.csv', [dict(route_id=r, sector_id=groups[r][0]['sector_id'], corridas=len(groups[r]),
            km_promedio=sum(t['distancia_servicio_km'] for t in groups[r])/len(groups[r])) for r in routes])
    scenario = dict(configuracion=CONFIG, rutas=routes, dia='L', terminales_comunes=starts,
                    terminal_excluido='T05 Los Acacios', capacidad_fisica=physical, cargadores=plugs,
                    criterio_seleccion=('Muestra anidada: rutas obligatorias y cuantiles entre restantes por sector' if required else 'Cuantiles de longitud media por sector') if args.cantidad else 'Rutas explícitas',
                    rutas_obligatorias=required,
                    disponibilidad_electroterminales='24 horas, supuesto pendiente de validación')
    (out/'escenario.json').write_text(json.dumps(scenario, ensure_ascii=False, indent=2), encoding='utf-8')
    phase1 = out/'fase1'
    phase1.mkdir(exist_ok=True)
    nodes, arcs, source, sink, bounds = crear_red(trips, distances, starts, {**dict.fromkeys(starts), **physical}, CONFIG)
    flow, summary1 = resolver_red(nodes, arcs, phase1, args.limite_segundos)
    tick = time.perf_counter()
    paths = descomponer_energia(nodes, arcs, flow, source, sink)
    phase2 = out/'fase2'
    phase2.mkdir(exist_ok=True)
    summary2 = verificar_y_exportar(trips, nodes, arcs, paths, distances, {**dict.fromkeys(starts), **physical}, CONFIG, phase2)
    summary2['tiempo_s'] = time.perf_counter()-tick
    chains = [dict(id=f'J{i:05d}', corridas=[arcs[j]['corrida_id'] for j in p if arcs[j]['tipo']=='servicio']) for i, p in enumerate(paths, 1)]
    del nodes,arcs,flow,paths
    lookup = {t['corrida_id']: t for t in trips}
    tick = time.perf_counter()
    schedules, splits = construir(chains, lookup, distances, starts, physical, plugs, tariffs,
                                 int(bounds['inicio_horizonte_s']), int(bounds['fin_horizonte_s']))
    construction_time = time.perf_counter()-tick
    summary3, journeys, activities = verificar(schedules, trips, distances, starts, physical, plugs, tariffs,
                                              int(bounds['inicio_horizonte_s']), int(bounds['fin_horizonte_s']))
    summary3.update(tiempo_construccion_s=construction_time, particiones=len(splits), optimalidad_demostrada=False)
    phase3 = out/'fase3'
    phase3.mkdir(exist_ok=True)
    guardar(phase3/'jornadas.csv', journeys)
    guardar(phase3/'actividades.csv', activities)
    guardar(phase3/'particiones.csv', splits)
    guardar(phase3/'recargas.csv', [a for a in activities if a['tipo']=='carga'])
    result = dict(rutas=routes, corridas=len(trips), horizonte=bounds, fase1=summary1, fase2=summary2,
                  fase3=summary3, tiempo_total_s=time.perf_counter()-start)
    (out/'resumen.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
