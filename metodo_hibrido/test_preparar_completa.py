"""Instancias de la red completa por tipo de día, generadas desde los datos originales.

Lee los archivos reales de `CODIGO apstone/output`, así que tarda algunos segundos.
"""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from metodo_hibrido.preparar_completa import carpeta_codigo, preparar

HERE = Path(__file__).resolve().parent


def leer(ruta):
    with open(ruta, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


class InstanciasCompletas(unittest.TestCase):
    def test_laboral_reproduce_byte_a_byte_la_instancia_417(self):
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / 'instancia'
            preparar('L', destino)
            for nombre in ('corridas.csv', 'distancias.csv', 'escenario.json'):
                with self.subTest(archivo=nombre):
                    self.assertEqual((destino / nombre).read_bytes(),
                                     (HERE / 'instancia_417' / nombre).read_bytes())

    def test_fin_de_semana_trae_solo_sus_corridas(self):
        # Conteos hechos aparte, directamente sobre output/fase1/corridas.csv.
        esperado = {'S': (43619, 343), 'D': (37377, 339)}
        for servicio, (corridas, rutas) in esperado.items():
            with self.subTest(servicio=servicio), tempfile.TemporaryDirectory() as tmp:
                destino = Path(tmp) / 'instancia'
                preparar(servicio, destino)
                filas = leer(destino / 'corridas.csv')
                escenario = json.loads((destino / 'escenario.json').read_text(encoding='utf8'))
                self.assertEqual(len(filas), corridas)
                self.assertEqual({f['service_id'] for f in filas}, {servicio})
                self.assertEqual(len({f['route_id'] for f in filas}), rutas)
                self.assertEqual(escenario['service_id'], servicio)
                self.assertEqual(len(escenario['rutas']), rutas)

    def test_carpeta_del_codigo_con_cualquiera_de_sus_nombres(self):
        # En el proyecto se llama «CODIGO apstone»; en el repositorio del grupo, «codigo».
        for nombre in ('CODIGO apstone', 'codigo'):
            with self.subTest(nombre=nombre), tempfile.TemporaryDirectory() as tmp:
                (Path(tmp) / nombre).mkdir()
                self.assertEqual(carpeta_codigo(Path(tmp)), Path(tmp) / nombre)
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(FileNotFoundError):
            carpeta_codigo(Path(tmp))

    def test_no_sobrescribe_una_instancia_existente(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileExistsError):
                preparar('S', Path(tmp))


if __name__ == '__main__':
    unittest.main()
