"""Revisión de la solución completa desde GTFS y archivos fuente.

No importa código del optimizador ni de sus verificadores. No modifica entradas
ni planes. La potencia agregada se cuantifica, sin inventar una capacidad de red.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EPS = 1e-6
DIA = {'L': 'laboral', 'S': 'de sábado', 'D': 'de domingo o festivo'}
CORRIDAS_ESPERADAS = {'L': 64502, 'S': 43619, 'D': 37377}
PATRONES_ESPERADOS = {'L': 6620, 'S': 4215, 'D': 3629}


class AuditFailure(AssertionError):
    pass


def require(condition, message):
    if not condition:
        raise AuditFailure(message)


def rows(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        yield from csv.DictReader(stream)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def seconds(value):
    hour, minute, second = map(int, value.split(':'))
    require(hour >= 0 and 0 <= minute < 60 and 0 <= second < 60,
            f'Hora GTFS inválida: {value}')
    return hour * 3600 + minute * 60 + second


def reconstruct_trips(servicio='L'):
    raw = ROOT / '01-datos'
    routes = {r['route_id'] for r in rows(raw / 'gtfs/routes.txt')
              if r['agency_id'] == 'RM' and r['route_type'] == '3'}
    patterns = {r['trip_id']: r for r in rows(raw / 'gtfs/trips.txt')
                if r['route_id'] in routes and r['service_id'] == servicio}
    timing = {}
    for r in rows(raw / 'gtfs/stop_times.txt'):
        trip = r['trip_id']
        if trip not in patterns:
            continue
        seq = int(r['stop_sequence'])
        if trip not in timing:
            timing[trip] = [seq, r, seq, r]
        else:
            t = timing[trip]
            if seq < t[0]:
                t[:2] = [seq, r]
            if seq > t[2]:
                t[2:] = [seq, r]
    lengths = {r['shape_id']: float(r['distance_km'])
               for r in rows(raw / 'shape_distances.csv')}
    expected, frequency_patterns = {}, set()
    exact_times = Counter()
    for index, f in enumerate(rows(raw / 'gtfs/frequencies.txt')):
        trip = f['trip_id']
        if trip not in patterns:
            continue
        p = patterns[trip]
        first, last = timing[trip][1], timing[trip][3]
        duration = seconds(last['arrival_time']) - seconds(first['departure_time'])
        headway = int(f['headway_secs'])
        require(duration > 0 and headway > 0, f'Patrón inválido: {trip}')
        frequency_patterns.add(trip)
        exact_times[f.get('exact_times', '')] += 1
        for n, start in enumerate(range(seconds(f['start_time']), seconds(f['end_time']), headway)):
            key = f'{trip}__f{index}__n{n}'
            require(key not in expected, f'Corrida GTFS duplicada: {key}')
            expected[key] = dict(corrida_id=key, trip_id=trip, service_id=servicio,
                route_id=p['route_id'], direction_id=p['direction_id'], shape_id=p['shape_id'],
                inicio_stop_id=first['stop_id'], fin_stop_id=last['stop_id'],
                inicio_s=start, fin_s=start + duration,
                distancia_servicio_km=lengths[p['shape_id']])
    require(frequency_patterns == set(patterns), f'Patrones del día {servicio} sin frecuencias')
    require(len(routes) == 417 and len(expected) == CORRIDAS_ESPERADAS[servicio]
            and len(patterns) == PATRONES_ESPERADOS[servicio],
            'Tamaño inesperado del universo reconstruido')
    return expected, dict(rutas=len(routes), patrones=len(patterns), corridas=len(expected),
                          exact_times=dict(exact_times))


def source_contract(expected, servicio='L', instancia=ROOT / 'metodo_hibrido/instancia_417'):
    source = ROOT / 'CODIGO apstone'
    raw = ROOT / '01-datos'
    source_trips = {r['corrida_id']: r for r in rows(source / 'output/fase1/corridas.csv')
                    if r['service_id'] == servicio}
    instance_trips = {r['corrida_id']: r for r in rows(instancia / 'corridas.csv')}
    require(set(source_trips) == set(expected) == set(instance_trips), 'Universos de corridas distintos')
    for key, e in expected.items():
        r = source_trips[key]
        require(r == instance_trips[key], f'Instancia alterada: {key}')
        for field, value in e.items():
            actual = r[field]
            if isinstance(value, int):
                require(int(actual) == value, f'GTFS discrepante: {key}/{field}')
            elif isinstance(value, float):
                require(abs(float(actual) - value) <= 1e-9, f'Distancia GTFS discrepante: {key}')
            else:
                require(actual == value, f'GTFS discrepante: {key}/{field}')
        e['sector_id'] = r['sector_id']
    distances, metadata = {}, {}
    for r in rows(source / 'output/fase1/traslados.csv'):
        pair = r['origen_id'], r['destino_id']
        if not r['distancia_km']:
            distances[pair] = None
            continue
        km = float(r['distancia_km'])
        require(math.isfinite(km) and km >= 0, f'Distancia inválida: {pair}')
        distances[pair] = km
        metadata[pair] = r
    for r in rows(source / 'output/distancias_electroterminales/distancias_recorridos_electroterminales.csv'):
        stop, depot = 'S:' + r['extremo_stop_id'], 'E' + r['depot_id']
        pair = (depot, stop) if r['movimiento'] == 'electroterminal_a_inicio' else (stop, depot)
        km = float(r['distancia_km']) if r['distancia_km'] else None
        if pair in distances:
            require(km is not None and distances[pair] is not None
                    and abs(distances[pair] - km) <= 1e-5, f'Distancia contradictoria: {pair}')
        distances[pair] = km
        metadata[pair] = r
    for trip in expected.values():
        for field in ['inicio_stop_id', 'fin_stop_id']:
            stop = 'S:' + trip[field]
            distances[stop, stop] = 0.
    instance_distances = {}
    for r in rows(instancia / 'distancias.csv'):
        pair = r['origen_id'], r['destino_id']
        require(pair not in instance_distances, f'Par de distancias duplicado: {pair}')
        instance_distances[pair] = float(r['distancia_km']) if r['distancia_km'] else None
    require(instance_distances == distances, 'Matriz copiada distinta de fuentes originales')
    params = {r['parameter']: float(r['value']) for r in rows(raw / 'parameters.csv')}
    for filename in ['parameters.csv', 'vehicles.csv', 'depots.csv', 'charger_capacity.csv',
                     'electricity_prices.csv', 'shape_distances.csv']:
        require(digest(raw / filename) == digest(source / filename), f'Datos base distintos: {filename}')
    physical = {'E' + r['depot_id']: int(r['capacity']) for r in rows(raw / 'depots.csv')}
    plugs = {'E' + r['depot_id']: int(r['max_simultaneous_charging'])
             for r in rows(raw / 'charger_capacity.csv')}
    windows = defaultdict(list)
    for r in rows(raw / 'charging_activities.csv'):
        windows['E' + r['depot_id']].append((int(r['start_hour']) * 3600,
                                            int(r['end_hour']) * 3600, int(r['capacity'])))
    for e, values in windows.items():
        values.sort()
        require(values[0][0] == 0 and values[-1][1] == 86400,
                f'Calendario de carga incompleto: {e}')
        require(all(a[1] == b[0] for a, b in zip(values, values[1:])), f'Hueco de carga: {e}')
    tariffs = [(seconds(r['start_hour'] + ':00:00'), seconds(r['end_hour'] + ':00:00'),
                float(r['price_usd_kwh'])) for r in rows(raw / 'electricity_prices.csv')]
    terminal_rows = json.loads((source / 'fase1/terminales_espera.json').read_text())
    starts = {r['terminal_id'] for r in terminal_rows if r['terminal_id'] in {'T01','T02','T03','T04'}}
    required_stops = {'S:' + t[field] for t in expected.values()
                      for field in ['inicio_stop_id','fin_stop_id']}
    positions = {'S:' + r['stop_id']: (float(r['stop_lat']), float(r['stop_lon']))
                 for r in rows(raw / 'gtfs/stops.txt') if 'S:' + r['stop_id'] in required_stops}
    require(set(positions) == required_stops, 'Extremos de servicio sin coordenadas')
    positions.update({'E' + r['depot_id']: (float(r['lat']), float(r['lon']))
                      for r in rows(raw / 'depots.csv')})
    positions.update({r['terminal_id']: (r['lat'], r['lon']) for r in terminal_rows
                      if r['terminal_id'] in starts})
    spec = json.loads((instancia / 'escenario.json').read_text())
    require(set(spec['terminales_espera']) == starts and spec['capacidad_fisica'] == physical
            and spec['conexiones'] == plugs, 'Recursos distintos de los originales')
    t0 = min(t['inicio_s'] - math.ceil(distances[s, 'S:' + t['inicio_stop_id']] * 3600 / 18)
             for t in expected.values() for s in starts)
    horizon = max(t['fin_s'] + math.ceil(distances['S:' + t['fin_stop_id'], s] * 3600 / 18)
                  for t in expected.values() for s in starts | set(physical))
    require(t0 == spec['inicio_horizonte_s'] and horizon == spec['fin_horizonte_s'], 'Horizonte discrepante')
    return dict(expected=expected, distances=distances, metadata=metadata, params=params,
                physical=physical, plugs=plugs, windows=windows, tariffs=tariffs,
                starts=starts, positions=positions, t0=t0, horizon=horizon)


def great_circle(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 6371.0088 * 2 * math.asin(min(1., math.sqrt(h)))


def audit_plans(plans, c):
    seen = Counter()
    resource_events = defaultdict(lambda: defaultdict(lambda: [0, 0, 0.]))
    used_pairs = set()
    metrics = Counter()
    journey_values, activity_values = {}, {}
    minimum, maximum = math.inf, -math.inf
    endpoints, spans = [], []
    require(len({p['bus_id'] for p in plans}) == len(plans), 'Bus duplicado')
    p = c['params']
    battery = p['battery_kwh']
    lower, upper = p['min_soc'] * battery, p['max_soc'] * battery
    consumption = battery / p['range_km']
    for bus in plans:
        bus_id = bus['bus_id']
        require(bus['terminal_inicial'] in c['starts'], f'Salida no permitida: {bus_id}')
        time, loc, energy = c['t0'], bus['terminal_inicial'], battery
        covered, local = [], Counter()
        previous = None
        first_movement = last_movement = None
        for index, a in enumerate(bus['actividades'], 1):
            label = f'{bus_id}/{index}'
            s, f, km, q = a['inicio_s'], a['fin_s'], a['distancia_km'], a['carga_kwh']
            require(type(s) is int and type(f) is int and s < f, f'Tiempo inválido: {label}')
            require(s == time and a['origen'] == loc, f'Discontinuidad: {label}')
            require(c['t0'] <= s < f <= c['horizon'], f'Fuera de horizonte: {label}')
            require(math.isfinite(km) and math.isfinite(q) and km >= 0 and q >= 0,
                    f'Magnitud inválida: {label}')
            before = energy
            kind = a['tipo']
            if kind == 'servicio':
                key = a['corrida_id']
                require(key in c['expected'], f'Corrida desconocida: {label}')
                t = c['expected'][key]
                require((s, f, a['origen'], a['destino']) ==
                        (t['inicio_s'], t['fin_s'], 'S:' + t['inicio_stop_id'], 'S:' + t['fin_stop_id']),
                        f'Corrida modificada: {label}')
                require(abs(km - t['distancia_servicio_km']) <= 1e-9 and q == 0,
                        f'Kilómetros de servicio alterados: {label}')
                require(t['sector_id'] == bus['sector_id'], f'Sector alterado: {label}')
                seen[key] += 1
                covered.append(key)
                local['km_servicio'] += km
                energy -= consumption * km
            elif kind == 'vacio':
                pair = a['origen'], a['destino']
                require(pair in c['distances'] and c['distances'][pair] is not None,
                        f'Traslado inexistente: {label}')
                original_km = c['distances'][pair]
                require(abs(original_km-km) <= 1e-9 and f-s == math.ceil(original_km*3600/18)
                        and q == 0, f'Traslado alterado: {label}')
                straight = great_circle(c['positions'][pair[0]], c['positions'][pair[1]])
                require(km + .002 >= straight, f'Traslado menor que distancia directa: {label}')
                used_pairs.add(pair)
                local['km_vacio'] += km
                energy -= consumption * km
            elif kind in {'carga', 'espera'}:
                require(a['origen'] == a['destino'] and km == 0, f'Estacionario inválido: {label}')
                if kind == 'carga':
                    require(loc in c['physical'] and s % 300 == 0 and f-s == 300,
                            f'Lugar o bloque de carga inválido: {label}')
                    require(q * 3600/(f-s) <= p['charge_power_kw'] + EPS,
                            f'Potencia individual excedida: {label}')
                    price = next(price for start, end, price in c['tariffs'] if start <= s % 86400 < end)
                    require(s//3600 == (f-1)//3600, f'Bloque cruza tarifa/capacidad: {label}')
                    local['costo_energia'] += q*price
                    local['carga_kwh'] += q
                    if previous is None or previous['tipo'] != 'carga' or previous['destino'] != loc:
                        local['sesiones'] += 1
                    energy += q
                else:
                    require(q == 0, f'Energía creada en espera: {label}')
                    local['espera_s'] += f-s
                if loc in c['physical']:
                    charged = int(kind == 'carga')
                    power = q*3600/(f-s) if charged else 0.
                    for second, sign in [(s,1),(f,-1)]:
                        event = resource_events[loc][second]
                        event[0] += sign
                        event[1] += sign*charged
                        event[2] += sign*power
            else:
                raise AuditFailure(f'Actividad desconocida: {label}')
            require(lower-EPS <= energy <= upper+EPS, f'Batería fuera de rango: {label}: {energy}')
            minimum, maximum = min(minimum, energy), max(maximum, energy)
            activity_values[bus_id, index] = (before, energy, a)
            metrics['actividades'] += 1
            metrics[kind] += 1
            if kind in {'vacio', 'servicio'}:
                if first_movement is None:
                    first_movement = s
                last_movement = f
            time, loc, previous = f, a['destino'], a
        require(covered and covered == bus['corridas'], f'Lista de servicios inconsistente: {bus_id}')
        require(time == c['horizon'] and loc == bus['terminal_final']
                and loc in c['starts'] | set(c['physical']), f'Final inválido: {bus_id}')
        require(abs(battery+local['carga_kwh']-consumption*(local['km_servicio']+local['km_vacio'])-energy)
                <= EPS, f'Balance energético incorrecto: {bus_id}')
        local['energia_final_kwh'] = energy
        local['costo_usd'] = (p['vehicle_fixed_cost'] + p['cost_per_km']*(local['km_servicio']+local['km_vacio'])
                             + local['costo_energia'] + p['fixed_charge_cost']*local['sesiones'])
        journey_values[bus_id] = dict(local)
        metrics.update(local)
        endpoints.append((bus['terminal_inicial'], bus['terminal_final']))
        spans.append(last_movement-first_movement)
    require(set(seen) == set(c['expected']) and all(count == 1 for count in seen.values()),
            'Cobertura incompleta o duplicada')
    peaks = {}
    for e in c['physical']:
        occupation = charging = 0
        power = 0.
        peak_o = peak_c = 0
        peak_power, peak_time = 0., None
        for second, changes in sorted(resource_events[e].items()):
            occupation += changes[0]
            charging += changes[1]
            power += changes[2]
            require(0 <= charging <= occupation <= c['physical'][e], f'Estacionamiento excedido: {e}/{second}')
            limit = next(cap for start,end,cap in c['windows'][e] if start <= second % 86400 < end)
            require(charging <= min(c['plugs'][e],limit), f'Cupos horarios excedidos: {e}/{second}')
            require(power >= -EPS and power <= charging*p['charge_power_kw']+EPS,
                    f'Potencia individual acumulada inválida: {e}/{second}')
            peak_o, peak_c = max(peak_o,occupation), max(peak_c,charging)
            if power > peak_power:
                peak_power, peak_time = power, second
        require(occupation == charging == 0 and abs(power) <= EPS, f'Recursos sin cierre: {e}')
        peaks[e] = dict(ocupacion_maxima=peak_o, cargas_simultaneas_maximas=peak_c,
                        capacidad_fisica=c['physical'][e], conexiones=c['plugs'][e],
                        potencia_maxima_kw=peak_power, segundo_potencia_maxima=peak_time)
    report = dict(aprobado=True, buses=len(plans), corridas=len(seen), actividades=metrics['actividades'],
                  tipos_actividad={k:metrics[k] for k in ['servicio','vacio','espera','carga']},
                  km_servicio=metrics['km_servicio'], km_vacio=metrics['km_vacio'],
                  carga_kwh=metrics['carga_kwh'], sesiones=metrics['sesiones'],
                  energia_minima_kwh=minimum, energia_maxima_kwh=maximum,
                  energia_final_total_kwh=metrics['energia_final_kwh'],
                  costo_modelado_usd=metrics['costo_usd'], recursos=peaks,
                  pares_de_traslado_utilizados=len(used_pairs),
                  amplitud_maxima_s=max(spans), tolerancia_bateria_kwh=EPS,
                  salidas_por_terminal=dict(Counter(a for a,b in endpoints)),
                  finales_por_terminal=dict(Counter(b for a,b in endpoints)))
    return report, journey_values, activity_values, used_pairs


def salida_por_defecto(servicio, resultado):
    """La evidencia laboral del 6-oct vive en esta carpeta; sábado y domingo escriben junto a su resultado."""
    return Path(__file__).resolve().parent if servicio == 'L' else Path(resultado) / 'revision_independiente'


def auditar_resultado(resultado, instancia, salida=None):
    """Audita los planes de resultado/04_final contra el GTFS y las fuentes del tipo de día de la instancia."""
    resultado, instancia = Path(resultado).resolve(), Path(instancia).resolve()
    servicio = json.loads((instancia / 'escenario.json').read_text())['service_id']
    salida = Path(salida) if salida is not None else salida_por_defecto(servicio, resultado)
    folder = resultado / '04_final'
    protected = [*folder.iterdir(), *(ROOT / 'metodo_hibrido').glob('*.py')]
    before = {str(p.relative_to(ROOT)):digest(p) for p in protected if p.is_file()}
    expected, reconstruction = reconstruct_trips(servicio)
    contract = source_contract(expected, servicio, instancia)
    plans = json.loads((folder / 'planes.json').read_text())
    report, journeys, activities, pairs = audit_plans(plans, contract)
    saved = json.loads((folder / 'resumen.json').read_text())
    require(saved['buses'] == report['buses'] and saved['corridas'] == report['corridas'], 'Resumen distinto')
    require(math.isclose(saved['costo_total_usd'], report['costo_modelado_usd'], abs_tol=1e-6), 'Costo discrepante')
    csv_activity_keys = set()
    charge_rows = []
    for r in rows(folder / 'actividades.csv'):
        key = r['bus_id'],int(r['orden'])
        require(key not in csv_activity_keys and key in activities, 'Actividad exportada duplicada o desconocida')
        csv_activity_keys.add(key)
        before_energy, after_energy, original = activities[key]
        for field, value in original.items():
            if isinstance(value, (int, float)):
                require(abs(float(r[field])-value) <= EPS, f'Actividad exportada discrepante: {key}/{field}')
            else:
                require(r[field] == value, f'Actividad exportada discrepante: {key}/{field}')
        require(abs(float(r['energia_inicial_kwh'])-before_energy) <= EPS
                and abs(float(r['energia_final_kwh'])-after_energy) <= EPS, 'SOC exportado discrepante')
        if r['tipo'] == 'carga':
            charge_rows.append(r)
    require(csv_activity_keys == set(activities), 'Cantidad de actividades exportadas distinta')
    require(charge_rows == list(rows(folder / 'recargas.csv')), 'Recargas exportadas distintas')
    csv_bus_ids = []
    for r in rows(folder / 'jornadas.csv'):
        require(r['bus_id'] in journeys, 'Bus exportado desconocido')
        csv_bus_ids.append(r['bus_id'])
        for field in ['km_servicio','km_vacio','carga_kwh','sesiones','energia_final_kwh','costo_usd']:
            require(abs(float(r[field])-journeys[r['bus_id']].get(field,0)) <= EPS,
                    f'Jornada exportada discrepante: {r["bus_id"]}/{field}')
    require(len(csv_bus_ids) == len(set(csv_bus_ids)) == len(journeys), 'Jornadas exportadas duplicadas o incompletas')
    # Demostrar rechazo de corrupciones concretas de un plan que sí fue aprobado.
    def rejected(label, candidate, expected_error, c=contract):
        try:
            audit_plans(candidate,c)
        except AuditFailure as error:
            require(expected_error in str(error), f'Prueba rechazó por otro motivo: {label}: {error}')
            return dict(prueba=label, rechazada=True, motivo=str(error))
        raise AuditFailure(f'Corrupción no detectada: {label}')
    bad = copy.deepcopy(plans[0])
    bad['actividades'][1]['origen'] = 'T99'
    negative = [rejected('teletransporte', [bad], 'Discontinuidad')]
    bad = copy.deepcopy(plans[0])
    next(a for a in bad['actividades'] if a['tipo']=='servicio')['inicio_s'] += 1
    negative.append(rejected('horario modificado', [bad], 'Discontinuidad'))
    bad = copy.deepcopy(plans[0])
    next(a for a in bad['actividades'] if a['tipo']=='vacio')['distancia_km'] += 1
    negative.append(rejected('distancia modificada', [bad], 'Traslado alterado'))
    bad = copy.deepcopy(next(b for b in plans if any(a['tipo']=='carga' for a in b['actividades'])))
    next(a for a in bad['actividades'] if a['tipo']=='carga')['carga_kwh'] = 15.001
    negative.append(rejected('potencia individual excedida', [bad], 'Potencia individual excedida'))
    negative.append(rejected('corridas omitidas', plans[1:], 'Cobertura incompleta'))
    negative.append(rejected('bus duplicado', [plans[0],plans[0]], 'Bus duplicado'))
    duplicate = copy.deepcopy(plans[0])
    duplicate['bus_id'] = 'B_CORRUPTO_DUPLICADO'
    negative.append(rejected('corridas duplicadas entre buses distintos', plans+[duplicate], 'Cobertura incompleta o duplicada'))
    undersized = dict(contract, physical={e:0 for e in contract['physical']})
    negative.append(rejected('ocupación sobre capacidad', plans, 'Estacionamiento excedido', undersized))
    no_plugs = dict(contract, plugs={e:0 for e in contract['plugs']})
    negative.append(rejected('cargadores sobre capacidad', plans, 'Cupos horarios excedidos', no_plugs))
    high_reserve = dict(contract, params=dict(contract['params'],min_soc=.999))
    negative.append(rejected('reserva de batería violada', plans, 'Batería fuera de rango', high_reserve))
    change_events = defaultdict(int)
    for t in expected.values():
        change_events[t['inicio_s']] += 1
        change_events[t['fin_s']] -= 1
    running = peak = 0
    peak_time = None
    for second, delta in sorted(change_events.items()):
        running += delta
        if running > peak:
            peak,peak_time = running,second
    require(running == 0, 'Simultaneidad sin cierre')
    reviewed_accesses = Counter(contract['metadata'].get(pair,{}).get('estado','') for pair in pairs)
    after = {str(p.relative_to(ROOT)):digest(p) for p in protected if p.is_file()}
    require(before == after, 'La auditoría alteró código o entregables')
    report.update(fecha_utc=datetime.now(timezone.utc).isoformat(), reconstruccion_gtfs=reconstruction,
                  cota_flota_simultaneidad=peak, segundo_pico=peak_time,
                  pruebas_de_corrupcion=negative, estados_accesos_pares_utilizados=dict(reviewed_accesses),
                  codigo_y_entregables_sin_cambios=True, sha256_protegidos=after,
                  capacidad_electrica_acordada_verificada=True,
                  definicion_capacidad_electrica='Cupos originales por electroterminal y 180 kW por bus; acuerdo confirmado por el usuario en esta revisión.',
                  transformer_mw_entregado=False,
                  servicio=servicio,
                  alcance=f'Día {DIA[servicio]} representativo aislado; flota dimensionada; SOC inicial 100%; T ilimitados; espera sin costo; sin límite de jornada.')
    salida.mkdir(parents=True,exist_ok=True)
    (salida / 'auditoria_independiente.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (salida / 'pares_traslado_utilizados.json').write_text(json.dumps(sorted(pairs),ensure_ascii=False))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resultado', type=Path, default=ROOT / 'metodo_hibrido/resultados/completa_417_20261006')
    parser.add_argument('--instancia', type=Path, default=ROOT / 'metodo_hibrido/instancia_417')
    parser.add_argument('--salida', type=Path,
                        help='Por defecto: esta carpeta para L; RESULTADO/revision_independiente para S y D')
    args = parser.parse_args()
    report = auditar_resultado(args.resultado, args.instancia, args.salida)
    print(json.dumps({k:v for k,v in report.items() if k not in {'sha256_protegidos','pruebas_de_corrupcion'}},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
