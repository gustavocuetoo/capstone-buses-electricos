import unittest

import analisis


def fila(etapa, buses, costo):
    return {'etapa': etapa, 'buses': str(buses), 'costo_total_usd': str(costo)}


class TestAnalisis(unittest.TestCase):
    def test_simultaneidad_intervalos_semiabiertos(self):
        self.assertEqual(analisis.simultaneidad_maxima([(0, 10), (5, 15), (10, 20)]), (2, 5))
        self.assertEqual(analisis.simultaneidad_maxima([(0, 10), (10, 20)]), (1, 0))
        self.assertEqual(analisis.simultaneidad_maxima([]), (0, None))

    def test_etapas_encadenadas(self):
        a = [fila('inicial', 4014, 1415348.7), fila('01_pares', 3989, 1403067.6), fila('01_trios', 3884, 1378806.9)]
        b = [fila('inicial', 3884, 1378806.9), fila('01_pares', 3884, 1377062.9), fila('01_trios', 3873, 1374631.7)]
        resultado = analisis.etapas(a, b)
        self.assertEqual([e['etapa'] for e in resultado], ['construccion', 'parejas', 'trios', 'refinamiento'])
        self.assertEqual([e['buses'] for e in resultado], [4014, 3989, 3884, 3873])

    def test_etapas_que_no_encadenan_fallan(self):
        a = [fila('inicial', 4014, 1.0), fila('01_pares', 3989, 1.0), fila('01_trios', 3884, 1.0)]
        b = [fila('inicial', 3900, 1.0), fila('01_pares', 3890, 1.0), fila('01_trios', 3873, 1.0)]
        with self.assertRaisesRegex(ValueError, 'no encadenan'):
            analisis.etapas(a, b)

    def test_energia_por_hora_envuelve_el_dia(self):
        recargas = [{'inicio_s': '-600', 'carga_kwh': '15'}, {'inicio_s': '90000', 'carga_kwh': '5'},
                    {'inicio_s': '3600', 'carga_kwh': '2.5'}]
        horas = analisis.energia_por_hora(recargas)
        self.assertEqual(len(horas), 24)
        self.assertEqual(horas[23], 15.0)
        self.assertEqual(horas[1], 7.5)

    def test_tarifa_en_hora(self):
        tarifas = [[0, 8, 0.1], [8, 14, 0.15], [22, 24, 0.11]]
        self.assertEqual(analisis.tarifa_en_hora(tarifas, 3), 0.1)
        self.assertEqual(analisis.tarifa_en_hora(tarifas, 23), 0.11)
        with self.assertRaises(ValueError):
            analisis.tarifa_en_hora(tarifas, 15)

    def test_estimacion_nocturna(self):
        jornadas = [{'energia_final_kwh': '350'}, {'energia_final_kwh': '35'}, {'energia_final_kwh': '170'}]
        r = analisis.estimacion_nocturna(jornadas, bateria_kwh=350, potencia_kw=180, conexiones_totales=1)
        self.assertEqual(r['buses_con_deficit'], 2)
        self.assertAlmostEqual(r['deficit_kwh'], 495.0)
        self.assertAlmostEqual(r['horas_si_todas_las_conexiones'], 2.75)
        self.assertAlmostEqual(r['horas_bus_mas_vacio'], 1.75)
        self.assertEqual(r['rondas_de_carga'], 2)

    def test_espera_solo_entre_primera_y_ultima_corrida(self):
        actividades = [
            {'bus_id': 'B', 'tipo': 'espera', 'inicio_s': '-100', 'fin_s': '0'},
            {'bus_id': 'B', 'tipo': 'servicio', 'inicio_s': '0', 'fin_s': '600'},
            {'bus_id': 'B', 'tipo': 'espera', 'inicio_s': '600', 'fin_s': '1200'},
            {'bus_id': 'B', 'tipo': 'servicio', 'inicio_s': '1200', 'fin_s': '1800'},
            {'bus_id': 'B', 'tipo': 'espera', 'inicio_s': '1800', 'fin_s': '9000'},
        ]
        self.assertEqual(analisis.minutos_espera_en_servicio(actividades), 10.0)


if __name__ == '__main__':
    unittest.main()
