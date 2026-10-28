import sys
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]
if sys.platform == 'win32':  # .deps trae binarios de Windows; en otros sistemas se usa el entorno local
    sys.path.insert(0, str(BASE/'.deps'))
sys.path.insert(0, str(BASE))
import unittest
from tres_fases.caso_base import construir_caso_base
from tres_fases.verificar import verificar

def corrida(cid, ruta, inicio, fin, desde, hasta, km):
    return dict(corrida_id=cid, route_id=ruta, inicio_s=inicio, fin_s=fin, inicio_stop_id=desde,
                fin_stop_id=hasta, sector_id='1', distancia_servicio_km=km)

def distancias():
    ids = ['T01', 'E1', 'E2', 'S:A', 'S:B']
    d = {(a, b): ((0., 0) if a == b else (1., 200)) for a in ids for b in ids}
    d['S:B', 'E2'] = d['E2', 'S:A'] = (5., 1000)
    return d

def resolver(trips, plugs=None, horizon=40000, umbral=.3):
    params = (distancias(), ['T01'], {'E1': 5, 'E2': 5}, plugs or {'E1': 5, 'E2': 5}, [(0, 24, .1)], 0, horizon)
    plans = construir_caso_base(trips, *params, umbral=umbral)
    result, _, acts = verificar(plans, trips, *params)
    return plans, result, acts

class CasoBaseTests(unittest.TestCase):
    def test_routes_do_not_share_buses(self):
        trips = [corrida('a', 'r1', 600, 4200, 'A', 'B', 10.), corrida('c', 'r2', 5000, 8000, 'B', 'A', 10.)]
        plans, result, _ = resolver(trips)
        self.assertEqual(result['buses'], 2)
        self.assertEqual({p['cadena_fase2'] for p in plans}, {'ruta:r1', 'ruta:r2'})

    def test_same_route_reuses_first_free_bus(self):
        trips = [corrida('a', 'r1', 600, 4200, 'A', 'B', 10.), corrida('b', 'r1', 5000, 8000, 'B', 'A', 10.)]
        _, result, _ = resolver(trips)
        self.assertEqual(result['buses'], 1)
        self.assertEqual(result['carga_kwh'], 0)

    def test_low_battery_charges_to_full_at_nearest_terminal(self):
        trips = [corrida('a', 'r1', 600, 4200, 'A', 'B', 150.), corrida('b', 'r1', 4200+6000, 7800+6000, 'B', 'A', 120.)]
        _, result, acts = resolver(trips)
        self.assertEqual(result['buses'], 1)
        self.assertEqual(result['sesiones'], 1)
        cargas = [a for a in acts if a['tipo'] == 'carga']
        self.assertTrue(all(a['origen'] == 'E1' for a in cargas))
        self.assertAlmostEqual(cargas[-1]['energia_final_kwh'], 350.)

    def test_full_charge_that_does_not_fit_adds_bus(self):
        trips = [corrida('a', 'r1', 600, 4200, 'A', 'B', 150.), corrida('b', 'r1', 4200+2400, 7800+2400, 'B', 'A', 120.)]
        _, result, _ = resolver(trips)
        self.assertEqual(result['buses'], 2)
        self.assertEqual(result['carga_kwh'], 0)

    def test_falls_back_to_next_terminal_when_nearest_has_no_plug(self):
        trips = [corrida('a', 'r1', 600, 4200, 'A', 'B', 150.), corrida('b', 'r1', 4200+6000, 7800+6000, 'B', 'A', 120.),
                 corrida('x', 'r2', 600, 4200, 'A', 'B', 150.), corrida('y', 'r2', 4200+6000, 7800+6000, 'B', 'A', 120.)]
        _, result, acts = resolver(trips, plugs={'E1': 1, 'E2': 1})
        self.assertEqual(result['buses'], 2)
        self.assertEqual({a['origen'] for a in acts if a['tipo'] == 'carga'}, {'E1', 'E2'})

    def test_threshold_triggers_charge_even_when_energy_is_enough(self):
        trips = [corrida('a', 'r1', 600, 4200, 'A', 'B', 150.), corrida('b', 'r1', 4200+6000, 7800+6000, 'B', 'A', 10.)]
        _, sin_umbral, _ = resolver(trips, umbral=0.)
        _, con_umbral, _ = resolver(trips, umbral=.5)
        self.assertEqual(sin_umbral['carga_kwh'], 0)
        self.assertGreater(con_umbral['carga_kwh'], 0)

if __name__ == '__main__':
    unittest.main()
