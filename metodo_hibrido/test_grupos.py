"""Los grupos de k jornadas: con k=3 repiten exactamente los tríos; con k mayor siguen siendo válidos."""
import copy
import unittest
from collections import Counter
from metodo_hibrido.caso_base import solve
from metodo_hibrido.grupos import buscar_grupos, propuestas
from metodo_hibrido.test_caso_base import instance
from metodo_hibrido.trios import buscar_trios, propuestas as propuestas_trios
from metodo_hibrido.verificar import verificar

# Seis servicios cortos que se pueden encadenar; cada uno parte en su propio bus.
HORARIOS = [('a', 600, 2400, 'A', 'B'), ('b', 3000, 4800, 'B', 'A'), ('c', 5400, 7200, 'A', 'B'),
            ('d', 7800, 9600, 'B', 'A'), ('e', 10200, 12000, 'A', 'B'), ('f', 12600, 14400, 'B', 'A')]
OPCIONES = dict(budget=60, local_limit=5, neighbors=8, per_pair=3, max_rounds=3, coordination='conjunta')


def escenario():
    _, d, starts, physical, plugs, tariffs, t0, _ = instance()
    physical, plugs = {'E1': 6}, {'E1': 6}
    trips = [dict(corrida_id=c, inicio_s=s, fin_s=f, inicio_stop_id=a, fin_stop_id=b, sector_id='1',
                  distancia_servicio_km=20.) for c, s, f, a, b in HORARIOS]
    params = (d, starts, physical, plugs, tariffs, t0, 16000)
    plans = []
    for i, t in enumerate(trips):
        p = solve([t], *params)[-1][0]
        p['bus_id'] = str(i)
        plans.append(p)
    return trips, params, plans


def sin_tiempos(stats):
    return {k: v for k, v in stats.items() if k != 'tiempo_busqueda_s'}


class TamanoTres(unittest.TestCase):
    def test_las_propuestas_son_las_mismas_que_las_de_los_trios(self):
        trips, params, _ = escenario()
        lookup = {t['corrida_id']: t for t in trips}
        seqs = [['a', 'd'], ['b', 'e'], ['c', 'f']]
        args = (lookup, params[0], ['T01'], ['T01', 'E1'])
        self.assertEqual(list(propuestas(seqs, *args)), list(propuestas_trios(seqs, *args)))

    def test_la_busqueda_da_el_mismo_plan_que_los_trios(self):
        trips, params, plans = escenario()
        lookup = {t['corrida_id']: t for t in trips}
        trio, hist_trio, stats_trio = buscar_trios(copy.deepcopy(plans), lookup, *params, **OPCIONES)
        grupo, hist_grupo, stats_grupo = buscar_grupos(copy.deepcopy(plans), lookup, *params, k=3, **OPCIONES)
        self.assertGreater(stats_trio['mejoras'], 0)
        self.assertEqual(grupo, trio)
        self.assertEqual([(r['tipo'], r['aceptado']) for r in hist_grupo], [(r['tipo'], r['aceptado']) for r in hist_trio])
        esperado = {k: v for k, v in sin_tiempos(stats_grupo).items() if k not in ('tamano', 'seleccion')}
        self.assertEqual(esperado, sin_tiempos(stats_trio))


class TamanosMayores(unittest.TestCase):
    def test_grupos_de_cuatro_y_cinco_mejoran_y_cubren_todo(self):
        trips, params, plans = escenario()
        lookup = {t['corrida_id']: t for t in trips}
        antes = verificar(plans, trips, *params)[0]
        for k in (4, 5):
            with self.subTest(k=k):
                result, history, stats = buscar_grupos(copy.deepcopy(plans), lookup, *params, k=k, **OPCIONES)
                despues = verificar(result, trips, *params)[0]
                self.assertLess(despues['costo_total_usd'], antes['costo_total_usd'])
                self.assertEqual(Counter(t for p in result for t in p['corridas']), Counter(list(lookup)))
                self.assertTrue(all(r['tamano'] == k for r in history))

    def test_el_azar_con_la_misma_semilla_repite_el_resultado(self):
        trips, params, plans = escenario()
        lookup = {t['corrida_id']: t for t in trips}
        corridas = [buscar_grupos(copy.deepcopy(plans), lookup, *params, k=4, seleccion='azar', semilla=7, **OPCIONES)
                    for _ in range(2)]
        self.assertEqual(corridas[0][0], corridas[1][0])
        self.assertEqual(sin_tiempos(corridas[0][2]), sin_tiempos(corridas[1][2]))

    def test_rechaza_tamanos_y_selecciones_invalidas(self):
        trips, params, plans = escenario()
        lookup = {t['corrida_id']: t for t in trips}
        for k, seleccion in ((2, 'parecidos'), (9, 'parecidos'), (4, 'cercanos')):
            with self.subTest(k=k, seleccion=seleccion), self.assertRaises(ValueError):
                buscar_grupos(plans, lookup, *params, k=k, seleccion=seleccion, **OPCIONES)


if __name__ == '__main__':
    unittest.main()
