"""Caso base miope por tipo de día, sobre la misma instancia que usa el método híbrido.

Lee los datos reales, así que tarda algunos segundos.
"""
import sys
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]
if sys.platform == 'win32':  # .deps trae binarios de Windows; en otros sistemas se usa el entorno local
    sys.path.insert(0, str(BASE/'.deps'))
sys.path.insert(0, str(BASE))
import json
import tempfile
import unittest
from tres_fases.caso_base import ejecutar, rutas_horizonte_servicio
from tres_fases.datos import corridas

HIBRIDO = BASE.parent/'metodo_hibrido'


class TiposDeDia(unittest.TestCase):
    def test_corridas_de_sabado(self):
        filas = corridas('S')
        self.assertEqual(len(filas), 43619)
        self.assertEqual({f['service_id'] for f in filas}, {'S'})
        self.assertIsInstance(filas[0]['inicio_s'], int)
        self.assertEqual(filas, sorted(filas, key=lambda r: (r['inicio_s'], r['corrida_id'])))

    def test_instancia_212_reproduce_el_caso_base_del_informe_2(self):
        # Corrida del 5-oct con --base output/tres_fases/muestra_212: 4.509 buses y USD 1.601.774,92.
        rutas, horizonte, servicio = rutas_horizonte_servicio(instancia=HIBRIDO/'instancia_212')
        with tempfile.TemporaryDirectory() as tmp:
            resultado = ejecutar(rutas, horizonte, servicio, 0., Path(tmp))
        self.assertEqual(resultado['caso_base']['buses'], 4509)
        self.assertAlmostEqual(resultado['caso_base']['costo_total_usd'], 1601774.92, delta=.01)

    def test_instancia_sin_tipo_de_dia_no_se_asume_laboral(self):
        spec = json.loads((HIBRIDO/'instancia_212'/'escenario.json').read_text(encoding='utf-8-sig'))
        del spec['service_id']
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'escenario.json').write_text(json.dumps(spec), encoding='utf-8')
            with self.assertRaises(KeyError):
                rutas_horizonte_servicio(instancia=Path(tmp))

    def test_instancia_de_sabado_usa_solo_corridas_de_sabado(self):
        rutas, horizonte, servicio = rutas_horizonte_servicio(instancia=HIBRIDO/'instancia_417_S')
        self.assertEqual((len(rutas), servicio), (343, 'S'))
        with tempfile.TemporaryDirectory() as tmp:
            resultado = ejecutar(rutas, horizonte, servicio, 0., Path(tmp))
        self.assertEqual(resultado['caso_base']['corridas'], 43619)
        self.assertTrue(resultado['caso_base']['verificado'])


if __name__ == '__main__':
    unittest.main()
