"""Los casos chicos son subconjuntos válidos e intactos de la instancia de 212 rutas."""
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from crear_casos import (INSTANCIA_212, MEDIANOS, crear_casos, crear_medianos, elegir_casos,
                         elegir_medianos)
from metodo_hibrido.caso_base import load_instance, read_csv, validate_inputs


class EleccionDeCasos(unittest.TestCase):
    def setUp(self):
        self.corridas = read_csv(INSTANCIA_212 / 'corridas.csv')
        self.casos = elegir_casos(self.corridas)

    def test_hay_seis_muy_chicos_de_una_ruta_y_cinco_chicos_de_dos_a_cuatro(self):
        tamanos = Counter(c['tipo'] for c in self.casos)
        self.assertEqual(tamanos, {'muy_chico': 6, 'chico': 5})
        for caso in self.casos:
            esperado = {1} if caso['tipo'] == 'muy_chico' else {2, 3, 4}
            self.assertIn(len(caso['rutas']), esperado, caso['nombre'])

    def test_cada_caso_es_de_un_solo_sector_y_ninguna_ruta_se_repite(self):
        sector = {r['route_id']: r['sector_id'] for r in self.corridas}
        usadas = [ruta for caso in self.casos for ruta in caso['rutas']]
        self.assertEqual(len(usadas), len(set(usadas)))
        for caso in self.casos:
            self.assertEqual({sector[r] for r in caso['rutas']}, {caso['sector']}, caso['nombre'])

    def test_la_eleccion_no_depende_del_orden_de_las_corridas(self):
        self.assertEqual(elegir_casos(list(reversed(self.corridas))), self.casos)


class CasosEscritos(unittest.TestCase):
    def test_cada_caso_se_valida_y_copia_las_corridas_sin_cambios(self):
        originales = {r['corrida_id']: r for r in read_csv(INSTANCIA_212 / 'corridas.csv')}
        with tempfile.TemporaryDirectory() as tmp:
            indice = crear_casos(Path(tmp))
            self.assertEqual(len(indice), 11)
            for fila in indice:
                carpeta = Path(tmp) / fila['nombre']
                validate_inputs(*load_instance(carpeta))
                corridas = read_csv(carpeta / 'corridas.csv')
                self.assertEqual(len(corridas), fila['corridas'])
                self.assertEqual({r['route_id'] for r in corridas}, set(fila['rutas'].split('|')))
                for r in corridas:
                    self.assertEqual(r, originales[r['corrida_id']])

    def test_no_sobrescribe_una_carpeta_existente(self):
        with tempfile.TemporaryDirectory() as tmp:
            crear_casos(Path(tmp))
            with self.assertRaises(FileExistsError):
                crear_casos(Path(tmp))


class CasosMedianos(unittest.TestCase):
    def setUp(self):
        self.corridas = read_csv(INSTANCIA_212 / 'corridas.csv')
        self.usadas = {r for c in elegir_casos(self.corridas) for r in c['rutas']}
        self.casos = elegir_medianos(self.corridas, self.usadas)

    def test_hay_una_escalera_de_un_solo_sector_que_crece(self):
        conteo = Counter(r['route_id'] for r in self.corridas)
        sector = {r['route_id']: r['sector_id'] for r in self.corridas}
        self.assertEqual([c['objetivo'] for c in self.casos], list(MEDIANOS))
        self.assertEqual(len({c['sector'] for c in self.casos}), 1)
        for anterior, caso in zip(self.casos, self.casos[1:]):
            self.assertLess(set(anterior['rutas']), set(caso['rutas']))
        for caso in self.casos:
            total = sum(conteo[r] for r in caso['rutas'])
            self.assertLessEqual(abs(total - caso['objetivo']), 0.1 * caso['objetivo'], caso['nombre'])
            self.assertEqual({sector[r] for r in caso['rutas']}, {caso['sector']}, caso['nombre'])

    def test_no_repite_rutas_de_los_casos_chicos(self):
        self.assertFalse(set(self.casos[-1]['rutas']) & self.usadas)

    def test_la_eleccion_no_depende_del_orden_de_las_corridas(self):
        self.assertEqual(elegir_medianos(list(reversed(self.corridas)), self.usadas), self.casos)

    def test_cada_caso_mediano_se_valida_y_copia_las_corridas_sin_cambios(self):
        originales = {r['corrida_id']: r for r in self.corridas}
        with tempfile.TemporaryDirectory() as tmp:
            indice = crear_medianos(Path(tmp))
            self.assertEqual(len(indice), len(MEDIANOS))
            for fila in indice:
                carpeta = Path(tmp) / fila['nombre']
                validate_inputs(*load_instance(carpeta))
                corridas = read_csv(carpeta / 'corridas.csv')
                self.assertEqual(len(corridas), fila['corridas'])
                for r in corridas:
                    self.assertEqual(r, originales[r['corrida_id']])
            with self.assertRaises(FileExistsError):
                crear_medianos(Path(tmp))


if __name__ == '__main__':
    unittest.main()
