"""Una instancia tiene un solo tipo de día: laboral (L), sábado (S) o domingo y festivo (D)."""
import unittest

from metodo_hibrido.caso_base import InputError, solve
from metodo_hibrido.test_caso_base import instance


def con_servicio(data, servicios):
    trips = [dict(t, service_id=s) for t, s in zip(data[0], servicios)]
    return [trips, *data[1:]]


class TiposDeDia(unittest.TestCase):
    def test_sabado_completo_se_acepta(self):
        summary, *_ = solve(*con_servicio(instance(), ['S', 'S']))
        self.assertEqual(summary['corridas'], 2)

    def test_domingo_completo_se_acepta(self):
        summary, *_ = solve(*con_servicio(instance(), ['D', 'D']))
        self.assertEqual(summary['corridas'], 2)

    def test_mezclar_tipos_de_dia_se_rechaza(self):
        with self.assertRaisesRegex(InputError, 'tipo de día'):
            solve(*con_servicio(instance(), ['L', 'S']))

    def test_tipo_de_dia_desconocido_se_rechaza(self):
        with self.assertRaises(InputError):
            solve(*con_servicio(instance(), ['X', 'X']))


if __name__ == '__main__':
    unittest.main()
