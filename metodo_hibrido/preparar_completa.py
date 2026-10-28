"""Exporta todas las corridas de un tipo de día al formato independiente del híbrido.

Laboral (L) queda en instancia_417; sábado (S) y domingo o festivo (D), en instancia_417_S e instancia_417_D.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from metodo_hibrido.caso_base import DAY_TYPES, read_csv, write_csv, load_instance, validate_inputs

HERE = Path(__file__).resolve().parent


def carpeta_codigo(raiz):
    """En el proyecto se llama «CODIGO apstone»; en el repositorio del grupo, «codigo»."""
    for nombre in ('CODIGO apstone', 'codigo'):
        if (raiz / nombre).is_dir():
            return raiz / nombre
    raise FileNotFoundError(f'No está la carpeta del código en {raiz}')


SOURCE = carpeta_codigo(HERE.parent)
# Corridas y rutas de cada tipo de día en los datos originales; si no calzan, no se arma la instancia.
ESPERADO = {'L': (64502, 417), 'S': (43619, 343), 'D': (37377, 339)}
DIA = {'L': 'laboral', 'S': 'de sábado', 'D': 'de domingo o festivo'}


def destino_por_defecto(servicio):
    return HERE / ('instancia_417' if servicio == 'L' else f'instancia_417_{servicio}')


def preparar(servicio='L', destino=None):
    if servicio not in DAY_TYPES:
        raise ValueError(f'Tipo de día desconocido: {servicio}')
    target = Path(destino) if destino is not None else destino_por_defecto(servicio)
    if target.exists():
        raise FileExistsError(target)
    files = {
        'corridas': SOURCE / 'output/fase1/corridas.csv',
        'traslados': SOURCE / 'output/fase1/traslados.csv',
        'electroterminales': SOURCE / 'output/distancias_electroterminales/distancias_recorridos_electroterminales.csv',
        'depots': SOURCE / 'depots.csv',
        'cargadores': SOURCE / 'charger_capacity.csv',
        'tarifas': SOURCE / 'electricity_prices.csv',
    }
    trips = [r for r in read_csv(files['corridas']) if r['service_id'] == servicio]
    assert (len(trips), len({r['route_id'] for r in trips})) == ESPERADO[servicio]
    by_id = {r['corrida_id']: r for r in trips}
    assert len(by_id) == len(trips)
    if servicio == 'L':
        # Verifica que la instancia anterior está incluida sin alterar ningún servicio.
        for r in read_csv(HERE / 'instancia_212/corridas.csv'):
            assert r == by_id[r['corrida_id']], r['corrida_id']
    distances = {}
    for r in read_csv(files['traslados']):
        pair = r['origen_id'], r['destino_id']
        value = float(r['distancia_km']) if r['distancia_km'] else None
        if value is None:
            assert r['estado'] == 'sin_camino'
        assert pair not in distances
        distances[pair] = value
    for r in read_csv(files['electroterminales']):
        s, e = 'S:' + r['extremo_stop_id'], 'E' + r['depot_id']
        pair = (s, e) if r['movimiento'] == 'fin_a_electroterminal' else (e, s)
        value = float(r['distancia_km']) if r['distancia_km'] else None
        if pair in distances:
            assert distances[pair] is not None and value is not None and abs(distances[pair] - value) < 1e-5
        distances[pair] = value
    for t in trips:
        for key in ('inicio_stop_id', 'fin_stop_id'):
            s = 'S:' + t[key]
            distances[s, s] = 0.
    spec = json.loads((HERE / 'instancia_212/escenario.json').read_text(encoding='utf-8-sig'))
    spec['service_id'] = servicio
    spec['rutas'] = sorted({r['route_id'] for r in trips})
    starts = spec['terminales_espera']
    # Misma regla de horizonte: salidas desde T y retornos a T o E.
    duration = lambda pair: math.ceil(distances[pair] * 3600 / 18)
    spec['inicio_horizonte_s'] = min(int(t['inicio_s']) - duration((s, 'S:' + t['inicio_stop_id']))
        for t in trips for s in starts if distances.get((s, 'S:' + t['inicio_stop_id'])) is not None)
    spec['fin_horizonte_s'] = max(int(t['fin_s']) + duration(('S:' + t['fin_stop_id'], s))
        for t in trips for s in starts + sorted(spec['capacidad_fisica'])
        if distances.get(('S:' + t['fin_stop_id'], s)) is not None)
    spec['origen'] = f'Universo {DIA[servicio]} completo; sin selección de rutas; horizonte por salidas y retornos'
    spec['fuentes_sha256'] = {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in files.items()}
    target.mkdir()
    write_csv(target / 'corridas.csv', sorted(trips, key=lambda r: (int(r['inicio_s']), r['corrida_id'])))
    write_csv(target / 'distancias.csv', [dict(origen_id=a, destino_id=b,
        distancia_km='' if km is None else km, estado='sin_camino' if km is None else 'calculada')
        for (a, b), km in sorted(distances.items())])
    (target / 'escenario.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding='utf8')
    validate_inputs(*load_instance(target))
    return dict(servicio=servicio, corridas=len(trips), rutas=len(spec['rutas']), pares_distancia=len(distances),
                inicio=spec['inicio_horizonte_s'], fin=spec['fin_horizonte_s'], validada=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--servicio', choices=DAY_TYPES, default='L',
                        help='L laboral, S sábado, D domingo o festivo')
    args = parser.parse_args()
    print(json.dumps(preparar(args.servicio)))


if __name__ == '__main__':
    main()
