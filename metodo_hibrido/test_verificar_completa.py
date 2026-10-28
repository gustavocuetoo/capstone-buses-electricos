"""La validación cruzada contra los datos y el auditor originales, para cualquier tipo de día.

Tarda cerca de un minuto: corre solo con PRUEBAS_LENTAS=1.
"""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from metodo_hibrido.verificar_completa import verificar_resultado

HERE = Path(__file__).resolve().parent
LABORAL = HERE / 'resultados/completa_417_20261006'


@unittest.skipUnless(os.environ.get('PRUEBAS_LENTAS'), 'prueba lenta: usar PRUEBAS_LENTAS=1')
class ValidacionCruzada(unittest.TestCase):
    def test_laboral_reproduce_la_verificacion_del_6_de_octubre(self):
        guardada = json.loads((LABORAL / 'verificacion_final.json').read_text(encoding='utf8'))
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp)
            (copia / '04_final').mkdir()
            for archivo in (LABORAL / '04_final').iterdir():
                (copia / '04_final' / archivo.name).symlink_to(archivo)
            nueva = verificar_resultado(copia, HERE / 'instancia_417')
            testigo = (copia / 'testigo_simultaneidad.csv').read_bytes()
        # La autorización de flota se agregó a mano al archivo del 6-oct; el código no la produce.
        self.assertEqual(set(guardada) - set(nueva), {'flota_ajustable_autorizada_por_usuario'})
        self.assertEqual({k: nueva[k] for k in guardada if k in nueva},
                         {k: v for k, v in guardada.items() if k in nueva})
        self.assertEqual(nueva['servicio'], 'L')
        self.assertEqual(testigo, (LABORAL / 'testigo_simultaneidad.csv').read_bytes())


class TipoDeDiaDeLaInstancia(unittest.TestCase):
    def test_instancia_de_sabado_rotulada_laboral_se_rechaza(self):
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / 'instancia'
            shutil.copytree(HERE / 'instancia_417_S', copia)
            spec = json.loads((copia / 'escenario.json').read_text(encoding='utf8'))
            spec['service_id'] = 'L'
            (copia / 'escenario.json').write_text(json.dumps(spec, ensure_ascii=False), encoding='utf8')
            with self.assertRaisesRegex(AssertionError, 'tipo de día'):
                verificar_resultado(Path(tmp) / 'sin_resultado', copia)


if __name__ == '__main__':
    unittest.main()
