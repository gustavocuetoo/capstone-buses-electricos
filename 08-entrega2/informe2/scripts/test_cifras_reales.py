import re
import unittest

import cifras


class TestCifrasReales(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.macros = cifras.calcular()

    def test_cifras_conocidas(self):
        self.assertEqual(self.macros['BusesModelo'], '3.873')
        self.assertEqual(self.macros['CostoModelo'], '1.374.632')
        self.assertEqual(self.macros['BusesBase'], '4.509')
        self.assertEqual(self.macros['BusesSinRecargas'], '5.150')
        self.assertEqual(self.macros['BusesExtraSinRecargas'], '1.589')
        self.assertEqual(self.macros['BusesConstruccion'], '4.014')
        self.assertEqual(self.macros['BusesPrototipo'], '4.175')
        self.assertEqual(self.macros['PisoFaseUno'], '1.278.245')
        self.assertEqual(self.macros['MinutosRefinado'], '28,6')

    def test_cifras_del_capitulo_siete(self):
        self.assertEqual(self.macros['DeltaBusesConstruccion'], '\\ensuremath{-}495')
        self.assertEqual(self.macros['KmServicio'], '704.414')
        for plan in ('Base', 'Modelo'):
            precio = float(self.macros['PrecioMedioKwh' + plan].replace(',', '.'))
            self.assertTrue(0.10 <= precio <= 0.22, f'precio medio {plan} fuera de las tarifas: {precio}')
            punta = float(self.macros['PctEnergiaPunta' + plan].replace(',', '.'))
            self.assertTrue(0 <= punta <= 100)

    def test_todas_las_macros_son_validas(self):
        for nombre, valor in self.macros.items():
            self.assertRegex(nombre, r'^[A-Za-z]+$')
            self.assertNotIn('nan', valor)
            self.assertFalse(re.search(r'\d\.\d{1,2}$', valor), f'{nombre}={valor} parece punto decimal')


if __name__ == '__main__':
    unittest.main()
