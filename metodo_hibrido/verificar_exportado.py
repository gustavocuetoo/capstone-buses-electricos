"""Reaudita operación y CSV exportados; identidades originales auditadas en ejecución."""
import csv
import hashlib
import importlib.machinery
import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
FOLDER = HERE / 'resultados/completa_417_20261006'


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def main():
    cache = HERE / '__pycache__/verificar.cpython-312.pyc'
    loader = importlib.machinery.SourcelessFileLoader('auditor_cache', str(cache))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    audit = importlib.util.module_from_spec(spec)
    loader.exec_module(audit)
    final = json.loads((FOLDER / '04_final/planes.json').read_text())
    trips = []
    for bus in final:
        for a in bus['actividades']:
            if a['tipo'] == 'servicio':
                trips.append(dict(corrida_id=a['corrida_id'], inicio_s=a['inicio_s'], fin_s=a['fin_s'],
                    inicio_stop_id=a['origen'][2:], fin_stop_id=a['destino'][2:],
                    distancia_servicio_km=a['distancia_km'], sector_id=bus['sector_id']))
    assert len(trips) == len({t['corrida_id'] for t in trips}) == 64502
    distances = {}
    for r in read(HERE / 'instancia_417/distancias.csv'):
        km = float(r['distancia_km']) if r['distancia_km'] else None
        distances[r['origen_id'], r['destino_id']] = None if km is None else (km, math.ceil(km * 3600 / 18))
    params = (distances, ['T01', 'T02', 'T03', 'T04'],
        {'E1':150, 'E2':180, 'E3':120, 'E4':100, 'E5':150},
        {'E1':150, 'E2':180, 'E3':120, 'E4':100, 'E5':150},
        [(0,8,.1),(8,14,.15),(14,17,.22),(17,19,.15),(19,22,.22),(22,24,.11)], -7145, 99119)
    report, journeys, activities = audit.verificar(final, trips, *params)
    assert report == json.loads((FOLDER / '04_final/resumen.json').read_text())
    actual_journeys = read(FOLDER / '04_final/jornadas.csv')
    actual_activities = read(FOLDER / '04_final/actividades.csv')
    charges = read(FOLDER / '04_final/recargas.csv')
    for actual, expected in [(actual_journeys, journeys), (actual_activities, activities)]:
        assert len(actual) == len(expected)
        for a, b in zip(actual, expected):
            assert set(a) == set(b)
            for k, v in b.items():
                assert math.isclose(float(a[k]), v, rel_tol=1e-12, abs_tol=1e-7) if isinstance(v, (int,float)) else a[k] == str(v)
    assert charges == [a for a in actual_activities if a['tipo'] == 'carga']
    assert math.isclose(sum(float(j['costo_usd']) for j in actual_journeys), report['costo_total_usd'], abs_tol=1e-5)
    events = defaultdict(int)
    for t in trips:
        events[t['inicio_s']] += 1
        events[t['fin_s']] -= 1
    value = peak = 0
    when = None
    for second, delta in sorted(events.items()):
        value += delta
        if value > peak:
            peak, when = value, second
    witness = [t for t in trips if t['inicio_s'] <= when < t['fin_s']]
    assert len(witness) == peak == 6601 and when == 28800
    with (FOLDER / 'testigo_simultaneidad.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(witness[0])); w.writeheader(); w.writerows(witness)
    result = dict(auditoria_operacion_exportada_aprobada=True,
        cobertura_e_identidades_originales='Auditadas contra las entradas en cada aceptación y en la exportación final durante la búsqueda',
        validacion_cruzada_base_con_originales='Aprobada durante la ejecución; 64502 viajes',
        relectura_directa_originales_final='Pendiente: archivos dataless en iCloud bloquean lectura',
        csv_conciliados=True, rutas=417, corridas=64502, resumen=report,
        cota_flota_por_simultaneidad=peak, segundo_maxima_simultaneidad=when,
        flota_archivo_original=1200, factible_con_flota_archivo_original=False,
        alcance='Modelo híbrido: flota dimensionada; espera sin costo; batería inicial llena y sin reposición final',
        sha256_entregables={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in (FOLDER / '04_final').iterdir() if p.is_file()})
    (FOLDER / 'verificacion_final.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(dict(auditoria_exportados_aprobada=True, corridas=64502, rutas=417,
        buses=report['buses'], costo_usd=report['costo_total_usd'])))


if __name__ == '__main__':
    main()
