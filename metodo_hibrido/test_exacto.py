"""La respuesta perfecta pasa el revisor, cuesta lo que dice el modelo y no la supera ninguna heurística."""
import copy
import unittest
from metodo_hibrido.caso_base import solve
from metodo_hibrido.exacto import resolver_exacto
from metodo_hibrido.grupos import buscar_grupos
from metodo_hibrido.intercambios import buscar
from metodo_hibrido.test_caso_base import instance
from metodo_hibrido.test_grupos import OPCIONES, escenario
from metodo_hibrido.trios import buscar_trios
from metodo_hibrido.verificar import verificar


class RespuestaPerfecta(unittest.TestCase):
    def comprobar(self, trips, params):
        plans, info = resolver_exacto(trips, *params, limit=60)
        self.assertTrue(info['optimo'], info)
        reporte = verificar(plans, trips, *params)[0]
        self.assertAlmostEqual(reporte['costo_total_usd'], info['objetivo_usd'], places=4)
        return plans, reporte

    def test_ninguna_heuristica_es_mas_barata(self):
        trips, params, plans = escenario()
        lookup = {t['corrida_id']: t for t in trips}
        _, perfecta = self.comprobar(trips, params)
        busquedas = [lambda p: buscar(p, lookup, *params, **OPCIONES),
                     lambda p: buscar_trios(p, lookup, *params, **OPCIONES),
                     lambda p: buscar_grupos(p, lookup, *params, k=4, **OPCIONES)]
        for busqueda in busquedas:
            resultado = busqueda(copy.deepcopy(plans))[0]
            costo = verificar(resultado, trips, *params)[0]['costo_total_usd']
            self.assertLessEqual(perfecta['costo_total_usd'], costo + 1e-6)

    def test_recarga_cuando_evita_un_bus(self):
        trips, *params = instance()
        _, perfecta = self.comprobar(trips, params)
        construido = solve(trips, *params)[0]
        self.assertEqual(perfecta['buses'], 1)
        self.assertEqual(perfecta['sesiones'], 1)
        self.assertLessEqual(perfecta['costo_total_usd'], construido['costo_total_usd'] + 1e-6)

    def test_sin_tiempo_para_recargar_usa_dos_buses(self):
        trips, *params = instance(gap=0)
        _, perfecta = self.comprobar(trips, params)
        self.assertEqual(perfecta['buses'], 2)
        self.assertEqual(perfecta['sesiones'], 0)


if __name__ == '__main__':
    unittest.main()
