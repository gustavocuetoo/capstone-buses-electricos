import tempfile
import unittest
from pathlib import Path

import formato
import fuentes


class TestFormato(unittest.TestCase):
    def test_formato_chileno(self):
        self.assertEqual(formato.numero(1374631.7037), '1.374.632')
        self.assertEqual(formato.numero(14.1048, 1), '14,1')
        self.assertEqual(formato.numero(0.75873, 2), '0,76')
        self.assertEqual(formato.numero(950), '950')

    def test_cero_negativo_se_escribe_cero(self):
        self.assertEqual(formato.numero(-0.0001), '0')
        self.assertEqual(formato.con_signo(-0.04, 1), '0,0')

    def test_signo_explicito(self):
        self.assertEqual(formato.con_signo(-636), '\\ensuremath{-}636')
        self.assertEqual(formato.con_signo(3462.4), '+3.462')

    def test_no_finito_falla(self):
        with self.assertRaises(ValueError):
            formato.numero(float('nan'))

    def test_delta(self):
        diferencia, porcentaje = formato.delta(4509, 3873)
        self.assertEqual(diferencia, -636)
        self.assertAlmostEqual(porcentaje, -14.1051, places=3)
        with self.assertRaises(ValueError):
            formato.delta(0, 5)

    def test_macro(self):
        self.assertEqual(formato.macro('BusesModelo', '3.873'), '\\newcommand{\\BusesModelo}{3.873}')
        with self.assertRaises(ValueError):
            formato.macro('Buses2', '1')


class TestFuentes(unittest.TestCase):
    def test_solo_nube_detecta_bandera(self):
        self.assertTrue(fuentes.es_solo_nube(0x40000000 | 0x20))
        self.assertFalse(fuentes.es_solo_nube(0x20))

    def test_archivo_faltante_falla_con_ruta(self):
        with self.assertRaisesRegex(FileNotFoundError, 'no_existe.json'):
            fuentes.leer_json(Path('/tmp/no_existe.json'))

    def test_resumen_no_verificado_falla(self):
        with self.assertRaisesRegex(ValueError, 'verificado'):
            fuentes.resumen_verificado({'buses': 3, 'verificado': False}, 'x.json')
        self.assertEqual(fuentes.resumen_verificado({'verificado': True, 'buses': 3}, 'x')['buses'], 3)

    def test_carpeta_codigo_acepta_ambos_nombres(self):
        with tempfile.TemporaryDirectory() as carpeta:
            raiz = Path(carpeta)
            (raiz / 'CODIGO apstone').mkdir()
            self.assertEqual(fuentes.carpeta_codigo(raiz), raiz / 'CODIGO apstone')
            (raiz / 'codigo').mkdir()
            self.assertEqual(fuentes.carpeta_codigo(raiz), raiz / 'codigo')

    def test_csv_con_bom(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'a.csv'
            ruta.write_text('﻿bus_id,km\nB1,2.5\n', encoding='utf-8')
            self.assertEqual(fuentes.leer_csv(ruta), [{'bus_id': 'B1', 'km': '2.5'}])


if __name__ == '__main__':
    unittest.main()
