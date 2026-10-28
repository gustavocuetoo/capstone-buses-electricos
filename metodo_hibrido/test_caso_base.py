"""Pruebas sintéticas de factibilidad, calendario y reglas de decisión."""
import copy
import unittest

from metodo_hibrido.caso_base import Calendar, InputError, solve, tariff
from metodo_hibrido.verificar import verificar


def instance(gap=2400, second_sector=False):
    ids = ['T01', 'E1', 'S:A', 'S:B']
    distances = {(a,b): ((0.0, 0) if a == b else (1.0, 200)) for a in ids for b in ids}
    trips = [dict(corrida_id='a', inicio_s=600, fin_s=4200, inicio_stop_id='A', fin_stop_id='B',
                  sector_id='1', distancia_servicio_km=150.0),
             dict(corrida_id='b', inicio_s=4200+gap, fin_s=7800+gap, inicio_stop_id='B', fin_stop_id='A',
                  sector_id='1', distancia_servicio_km=120.0)]
    if second_sector:
        trips += [dict(t, corrida_id=t['corrida_id']+'2', sector_id='2') for t in trips[:]]
    return [trips, distances, ['T01'], {'E1':1}, {'E1':1}, [(0,24,.1)], 0, 16000]


class Tests(unittest.TestCase):
    def test_recharge_avoids_bus_and_is_minimal(self):
        summary, journeys, activities, _, _ = solve(*instance())
        self.assertEqual(summary['buses'], 1)
        self.assertEqual(summary['sesiones'], 1)
        # 150+120 servicio, salida+retorno 2 km, desvío 2 km.
        self.assertAlmostEqual(summary['carga_kwh'], 1.4*274-315)
        self.assertAlmostEqual(journeys[0]['energia_final_kwh'], 35)

    def test_no_time_to_charge_adds_bus(self):
        summary, _, _, _, buses = solve(*instance(gap=0))
        self.assertEqual(summary['buses'], 2)
        self.assertEqual(summary['carga_kwh'], 0)
        self.assertTrue(all(b['actividades'][0]['inicio_s'] == 0 for b in buses))

    def test_shared_capacity_between_sectors(self):
        summary, _, _, _, _ = solve(*instance(second_sector=True))
        self.assertEqual(summary['corridas'], 4)
        self.assertLessEqual(summary['capacidades']['E1']['ocupacion_maxima'], 1)
        self.assertLessEqual(summary['capacidades']['E1']['cargas_simultaneas_maximas'], 1)

    def test_no_midnight_reset(self):
        data = instance()
        for t in data[0]:
            t['inicio_s'] += 81000
            t['fin_s'] += 81000
        data[-1] = 100000
        summary, _, activities, _, _ = solve(*data)
        self.assertEqual(summary['buses'], 1)
        self.assertGreater(summary['carga_kwh'], 0)
        self.assertTrue(any(a['tipo']=='carga' and a['inicio_s'] > 86400 for a in activities))
        self.assertEqual(tariff(-300, [(0,8,.1),(8,24,.2)]), .2)

    def test_unknown_distance_reports_input_error(self):
        data = instance()
        del data[1]['S:A', 'E1']
        with self.assertRaisesRegex(InputError, 'Faltan'):
            solve(*data)

    def test_explicit_unreachable_optional_terminal_is_allowed(self):
        data = instance()
        data[1]['S:A', 'E1'] = None
        summary, _, _, _, buses = solve(*data)
        self.assertTrue(summary['verificado'])
        self.assertEqual(buses[0]['terminal_final'], 'T01')

    def test_duplicate_input_ids_rejected(self):
        data = instance()
        data[0].append(dict(data[0][0]))
        with self.assertRaisesRegex(InputError, 'duplicados'):
            solve(*data)

    def test_unreachable_service_is_heuristic_failure(self):
        data = instance()
        data[0][0]['distancia_servicio_km'] = 300
        with self.assertRaisesRegex(RuntimeError, 'no prueba infactibilidad'):
            solve(*data)

    def test_half_open_intervals_and_physical_parking(self):
        cal = Calendar({'E1':1}, {'E1':1}, -300, 1200)
        cal.reserve('E1', -300, 0, True)
        self.assertTrue(cal.free('E1', 0, 300, True))
        cal.reserve('E1', 600, 1200)
        self.assertFalse(cal.free('E1', 600, 900, True))

    def test_parking_does_not_displace_a_reserved_charge(self):
        data = instance()
        early = dict(corrida_id='early', inicio_s=300, fin_s=400, inicio_stop_id='A', fin_stop_id='B',
                     sector_id='other', distancia_servicio_km=1.)
        data[0].append(early)
        data[1]['S:B','E1'] = (.1, 20)
        data[1]['S:A','E1'] = (.1, 20)
        summary, _, _, _, buses = solve(*data)
        self.assertEqual(summary['buses'], 2)
        self.assertEqual(next(b for b in buses if b['sector_id']=='other')['terminal_final'], 'T01')
        self.assertEqual(summary['sesiones'], 1)

    def test_tampered_charge_is_rejected_by_group_validator(self):
        data = instance()
        *_, buses = solve(*data)
        bad = copy.deepcopy(buses)
        next(a for b in bad for a in b['actividades'] if a['tipo']=='carga')['carga_kwh'] = 100
        with self.assertRaises(AssertionError):
            verificar(bad, *data)

    def test_smaller_deadhead_wins(self):
        data = instance(gap=0)
        data[0] = [dict(corrida_id='a',inicio_s=600,fin_s=1000,inicio_stop_id='A',fin_stop_id='A',sector_id='1',distancia_servicio_km=1.),
                   dict(corrida_id='b',inicio_s=600,fin_s=1000,inicio_stop_id='B',fin_stop_id='B',sector_id='1',distancia_servicio_km=1.),
                   dict(corrida_id='c',inicio_s=1600,fin_s=2000,inicio_stop_id='B',fin_stop_id='A',sector_id='1',distancia_servicio_km=1.)]
        _, _, _, decisions, _ = solve(*data)
        self.assertEqual(decisions[2]['bus_id'], decisions[1]['bus_id'])

    def test_deterministic_with_shuffled_trips(self):
        data = instance(second_sector=True)
        first = solve(*data)
        data[0].reverse()
        self.assertEqual(first, solve(*data))

    def test_invalid_tariff_gap_rejected(self):
        data = instance()
        data[5] = [(0,8,.1),(9,24,.2)]
        with self.assertRaisesRegex(InputError, 'Tarifas'):
            solve(*data)


if __name__ == '__main__':
    unittest.main()
