"""Carga explícita del escenario acordado, sin modificar los datos originales."""
import csv
import math
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CONFIG = dict(velocidad_vacio_kmh=18., costo_bus_usd=250., costo_km_usd=.5,
              costo_espera_min_usd=0., regulacion_min=0., bateria_kwh=350.,
              minimo_kwh=35., consumo_kwh_km=1.4, potencia_kw=180., bloque_s=300)

def leer(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def guardar(path, rows):
    if not rows:
        Path(path).write_text('', encoding='utf-8')
        return
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def corridas(servicio='L'):
    """Corridas de un tipo de día: L laboral, S sábado, D domingo o festivo."""
    rows = [r for r in leer(BASE/'output/fase1/corridas.csv') if r['service_id'] == servicio]
    for r in rows:
        for k in ('inicio_s', 'fin_s'):
            r[k] = int(r[k])
        r['distancia_servicio_km'] = float(r['distancia_servicio_km'])
    return sorted(rows, key=lambda r: (r['inicio_s'], r['corrida_id']))

def seleccionar(rows, cantidad, obligatorias=()):
    """Muestra reproducible: cuantiles de longitud media dentro de los cinco sectores."""
    groups = defaultdict(list)
    for r in rows:
        groups[r['route_id']].append(r)
    required=set(obligatorias)
    if required-set(groups):raise ValueError('Hay rutas obligatorias sin servicios laborales')
    if len(required)>cantidad:raise ValueError('La muestra nueva no puede ser menor que las rutas obligatorias')
    sectors = defaultdict(list)
    for route, ts in groups.items():
        sectors[ts[0]['sector_id']].append((sum(t['distancia_servicio_km'] for t in ts)/len(ts), route))
    selected = []
    keys = sorted(sectors)
    for i, sector in enumerate(keys):
        candidates = sorted(sectors[sector])
        n = cantidad//len(keys) + (i < cantidad % len(keys))
        if n > len(candidates):
            raise ValueError('No hay suficientes rutas en un sector')
        fixed=[r for _,r in candidates if r in required]
        if len(fixed)>n:raise ValueError('Las rutas obligatorias exceden la cuota de un sector')
        if fixed:
            selected.extend(fixed)
            candidates=[c for c in candidates if c[1] not in required]
            n-=len(fixed)
        # Cuantiles interiores: incluye rutas cortas, medias y largas sin escoger por resultado.
        for j in range(n):
            selected.append(candidates[int((j+.5)*len(candidates)/n)][1])
    return selected

def cargar(routes, all_rows=None):
    rows = all_rows if all_rows is not None else corridas()
    trips = [r for r in rows if r['route_id'] in set(routes)]
    if set(routes) != {r['route_id'] for r in trips}:
        raise ValueError('Alguna ruta solicitada no tiene corridas laborales')
    d = {}
    for r in leer(BASE/'output/fase1/traslados.csv'):
        if r['distancia_km']:
            km = float(r['distancia_km'])
            d[r['origen_id'], r['destino_id']] = (km, math.ceil(km*3600/18))
    for r in leer(BASE/'output/distancias_electroterminales/distancias_recorridos_electroterminales.csv'):
        if not r['distancia_km']:
            continue
        s, e = 'S:'+r['extremo_stop_id'], 'E'+r['depot_id']
        pair = (s, e) if r['movimiento'] == 'fin_a_electroterminal' else (e, s)
        km = float(r['distancia_km'])
        value = (km, math.ceil(km*3600/18))
        if pair in d and abs(d[pair][0]-km) > 1e-5:
            raise ValueError(f'Distancia contradictoria: {pair}')
        d[pair] = value
    stops = {'S:'+r[k] for r in trips for k in ('inicio_stop_id', 'fin_stop_id')}
    for s in stops:
        d[s, s] = (0., 0)
    starts = ['T01', 'T02', 'T03', 'T04']
    physical = {'E'+r['depot_id']: int(r['capacity']) for r in leer(BASE/'depots.csv')}
    plugs = {'E'+r['depot_id']: int(r['max_simultaneous_charging']) for r in leer(BASE/'charger_capacity.csv')}
    if physical.keys() != plugs.keys():
        raise ValueError('Capacidades de carga incompletas')
    tariffs = [(int(r['start_hour']), int(r['end_hour']), float(r['price_usd_kwh']))
               for r in leer(BASE/'electricity_prices.csv')]
    return trips, d, starts, physical, plugs, tariffs
