"""La mezcla creciente parte igual que los pares y nunca termina peor que ellos."""
import copy
import unittest
from collections import Counter
from metodo_hibrido.creciente import buscar_creciente
from metodo_hibrido.intercambios import buscar
from metodo_hibrido.recarga import costo
from metodo_hibrido.test_grupos import OPCIONES, escenario
from metodo_hibrido.verificar import verificar


class MezclaCreciente(unittest.TestCase):
    def setUp(self):
        self.trips, self.params, self.plans = escenario()
        self.lookup = {t['corrida_id']: t for t in self.trips}

    def test_no_termina_peor_que_los_pares_y_cubre_todo(self):
        tariffs = self.params[4]
        pares = buscar(copy.deepcopy(self.plans), self.lookup, *self.params, **OPCIONES)[0]
        mezcla, _, stats = buscar_creciente(copy.deepcopy(self.plans), self.lookup, *self.params,
                                            tamanos=(2, 3, 4), **OPCIONES)
        verificar(mezcla, self.trips, *self.params)
        self.assertLessEqual(costo(mezcla, tariffs), costo(pares, tariffs) + 1e-6)
        self.assertEqual(Counter(t for p in mezcla for t in p['corridas']), Counter(list(self.lookup)))
        self.assertEqual(stats['pasos'][0]['tamano'], 2)

    def test_termina_cuando_el_tamano_mas_grande_no_mejora(self):
        _, _, stats = buscar_creciente(copy.deepcopy(self.plans), self.lookup, *self.params,
                                       tamanos=(2, 3, 4), **OPCIONES)
        self.assertEqual(stats['motivo_fin'], 'ultimo_tamano_sin_mejoras')
        self.assertEqual(stats['pasos'][-1]['tamano'], 4)
        self.assertEqual(stats['pasos'][-1]['mejoras'], 0)
        # Después de cada mejora se vuelve a los pares.
        for antes, despues in zip(stats['pasos'], stats['pasos'][1:]):
            if antes['mejoras']:
                self.assertEqual(despues['tamano'], 2)

    def test_rechaza_tamanos_desordenados(self):
        for tamanos in ((), (3, 2), (2, 2, 3), (1, 2)):
            with self.subTest(tamanos=tamanos), self.assertRaises(ValueError):
                buscar_creciente(self.plans, self.lookup, *self.params, tamanos=tamanos, **OPCIONES)


if __name__ == '__main__':
    unittest.main()
