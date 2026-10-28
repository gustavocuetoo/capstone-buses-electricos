"""Audita un resultado de la red completa contra datos y auditor originales, para cualquier tipo de día.

Uso: python -m metodo_hibrido.verificar_completa RESULTADO [--instancia metodo_hibrido/instancia_417_S]
"""
import argparse
import hashlib
import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path

from metodo_hibrido.caso_base import load_instance, read_csv, write_csv
from metodo_hibrido.preparar_completa import ESPERADO, SOURCE

HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def verificar_resultado(folder, instancia=HERE / 'instancia_417'):
    folder, instancia = Path(folder), Path(instancia)
    scenario = json.loads((instancia / 'escenario.json').read_text(encoding='utf-8-sig'))
    servicio = scenario['service_id']
    trips, *params = load_instance(instancia)
    data = module('datos_originales', SOURCE / 'tres_fases/datos.py')
    audit = module('auditor_original', SOURCE / 'tres_fases/verificar.py')
    all_rows = data.corridas(servicio)
    routes = sorted({t['route_id'] for t in all_rows})
    original_trips, d, starts, physical, plugs, prices = data.cargar(routes, all_rows)
    assert routes == sorted(scenario['rutas']), 'La instancia no cubre todas las rutas de su tipo de día'
    assert (len(original_trips), len(routes)) == ESPERADO[servicio], 'Universo distinto del esperado para su tipo de día'
    assert {t['corrida_id']: t for t in trips} == {t['corrida_id']: t for t in original_trips}
    assert params[1:4] == [starts, physical, plugs]
    assert [tuple(p) for p in params[4]] == prices
    t0, horizon = params[-2:]
    assert t0 == min(t['inicio_s'] - d[s, 'S:' + t['inicio_stop_id']][1] for t in trips for s in starts)
    assert horizon == max(t['fin_s'] + d['S:' + t['fin_stop_id'], s][1]
                         for t in trips for s in starts + sorted(physical))
    plans = json.loads((folder / '04_final/planes.json').read_text(encoding='utf8'))
    report, journeys, activities = audit.verificar(plans, original_trips, d, starts,
        physical, plugs, prices, t0, horizon)
    saved = json.loads((folder / '04_final/resumen.json').read_text(encoding='utf8'))
    assert report == saved
    csv_journeys = read_csv(folder / '04_final/jornadas.csv')
    csv_activities = read_csv(folder / '04_final/actividades.csv')
    csv_charges = read_csv(folder / '04_final/recargas.csv')
    assert len(csv_journeys) == len(journeys) and len(csv_activities) == len(activities)
    assert len(csv_charges) == sum(a['tipo'] == 'carga' for a in activities)
    assert csv_charges == [a for a in csv_activities if a['tipo'] == 'carga']
    for actual, expected in ((csv_journeys, journeys), (csv_activities, activities)):
        for a, b in zip(actual, expected):
            assert set(a) == set(b)
            for k, v in b.items():
                if isinstance(v, (int, float)):
                    assert math.isclose(float(a[k]), v, rel_tol=1e-12, abs_tol=1e-7), k
                else:
                    assert a[k] == str(v), k
    assert math.isclose(sum(float(j['costo_usd']) for j in csv_journeys), report['costo_total_usd'], abs_tol=1e-5)
    paths = dict(corridas=SOURCE / 'output/fase1/corridas.csv', traslados=SOURCE / 'output/fase1/traslados.csv',
        electroterminales=SOURCE / 'output/distancias_electroterminales/distancias_recorridos_electroterminales.csv',
        depots=SOURCE / 'depots.csv', cargadores=SOURCE / 'charger_capacity.csv', tarifas=SOURCE / 'electricity_prices.csv')
    assert all(hashlib.sha256(paths[k].read_bytes()).hexdigest() == value
               for k, value in scenario['fuentes_sha256'].items())
    events = defaultdict(int)
    for t in original_trips:
        events[t['inicio_s']] += 1
        events[t['fin_s']] -= 1
    occupation = peak = 0
    peak_time = None
    for second, delta in sorted(events.items()):
        occupation += delta
        if occupation > peak:
            peak, peak_time = occupation, second
    original_parameters = {r['parameter']: float(r['value']) for r in read_csv(SOURCE / 'parameters.csv')}
    witness = [t for t in original_trips if t['inicio_s'] <= peak_time < t['fin_s']]
    assert len(witness) == peak
    write_csv(folder / 'testigo_simultaneidad.csv', witness)
    result = dict(validacion_cruzada_aprobada=True, datos_originales_sin_cambios=True,
        csv_conciliados=True, servicio=servicio, corridas=len(original_trips), rutas=len(routes), resumen=report,
        alcance='Modelo híbrido: flota dimensionada, espera sin costo, día aislado con batería inicial llena',
        cota_flota_por_simultaneidad=peak, segundo_maxima_simultaneidad=peak_time,
        flota_archivo_original=original_parameters['fleet_size'],
        factible_con_flota_archivo_original=peak <= original_parameters['fleet_size'],
        sha256_entregables={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in (folder / '04_final').iterdir() if p.is_file()})
    (folder / 'verificacion_final.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('resultado', type=Path)
    parser.add_argument('--instancia', type=Path, default=HERE / 'instancia_417')
    args = parser.parse_args()
    result = verificar_resultado(args.resultado, args.instancia)
    print(json.dumps(dict(servicio=result['servicio'], corridas=result['corridas'], rutas=result['rutas'],
        buses=result['resumen']['buses'], costo_total_usd=result['resumen']['costo_total_usd'],
        validacion_cruzada_aprobada=True)))


if __name__ == '__main__':
    main()
