import unittest

import auditar_miope

ACTIVIDADES = [
    {'bus_id': 'C1', 'orden': '2', 'tipo': 'servicio', 'origen': 'S:A', 'destino': 'S:B',
     'inicio_s': '0', 'fin_s': '600', 'distancia_km': '5.0', 'carga_kwh': '0.0', 'corrida_id': 'R1'},
    {'bus_id': 'C1', 'orden': '1', 'tipo': 'vacio', 'origen': 'T01', 'destino': 'S:A',
     'inicio_s': '-300', 'fin_s': '0', 'distancia_km': '1.5', 'carga_kwh': '0.0', 'corrida_id': ''},
    {'bus_id': 'C2', 'orden': '1', 'tipo': 'carga', 'origen': 'E1', 'destino': 'E1',
     'inicio_s': '100', 'fin_s': '400', 'distancia_km': '0.0', 'carga_kwh': '15.0', 'corrida_id': ''},
]
JORNADAS = [
    {'bus_id': 'C1', 'cadena_fase2': 'ruta:102', 'sector_id': '3', 'terminal_inicial': 'T01', 'terminal_final': 'T02'},
    {'bus_id': 'C2', 'cadena_fase2': 'ruta:103', 'sector_id': '1', 'terminal_inicial': 'T03', 'terminal_final': 'T03'},
]


class TestAdaptador(unittest.TestCase):
    def test_ordena_por_orden_y_convierte_tipos(self):
        planes = auditar_miope.planes_desde_csv(ACTIVIDADES, JORNADAS)
        c1 = planes[0]
        self.assertEqual([a['tipo'] for a in c1['actividades']], ['vacio', 'servicio'])
        self.assertEqual(c1['actividades'][0]['inicio_s'], -300)
        self.assertIsInstance(c1['actividades'][0]['distancia_km'], float)
        self.assertEqual(c1['corridas'], ['R1'])
        self.assertEqual(c1['sector_id'], '3')

    def test_bus_sin_actividades_es_error(self):
        with self.assertRaisesRegex(ValueError, 'C9'):
            auditar_miope.planes_desde_csv(ACTIVIDADES, JORNADAS + [dict(JORNADAS[0], bus_id='C9')])


if __name__ == '__main__':
    unittest.main()
