"""El programa de corridas escribe una fila auditada por corrida, retoma lo hecho y no pisa tablas."""
import tempfile
import unittest
from pathlib import Path

from correr_metodos import CASOS, correr
from metodo_hibrido.caso_base import read_csv

CASO = CASOS / 'muy_chico_03_ruta_I10N'
METODOS = ['solo_base', 'pares', 'cuartetos']


class Corridas(unittest.TestCase):
    def test_una_fila_por_corrida_y_ninguna_peor_que_el_plan_inicial(self):
        with tempfile.TemporaryDirectory() as tmp:
            salida = Path(tmp) / 'tabla.csv'
            correr([CASO], METODOS, [5], selecciones=['parecidos', 'azar'], semillas=[1], salida=salida)
            filas = read_csv(salida)
            # solo_base y pares, más cuartetos con «parecidos» y con «azar» (semilla 1).
            self.assertEqual([(f['metodo'], f['seleccion']) for f in filas],
                             [('solo_base', ''), ('pares', ''), ('cuartetos', 'parecidos'), ('cuartetos', 'azar')])
            self.assertTrue(all(f['error'] == '' for f in filas))
            inicial = float(filas[0]['costo_total_usd'])
            self.assertTrue(all(float(f['costo_total_usd']) <= inicial + 1e-6 for f in filas))

    def test_continuar_salta_lo_hecho_y_no_se_pisa_una_tabla(self):
        with tempfile.TemporaryDirectory() as tmp:
            salida = Path(tmp) / 'tabla.csv'
            correr([CASO], ['solo_base'], [5], salida=salida)
            with self.assertRaises(FileExistsError):
                correr([CASO], ['solo_base'], [5], salida=salida)
            nuevas = correr([CASO], ['solo_base', 'pares'], [5], salida=salida, continuar=True)
            self.assertEqual([f['metodo'] for f in nuevas], ['pares'])
            self.assertEqual(len(read_csv(salida)), 2)


if __name__ == '__main__':
    unittest.main()
