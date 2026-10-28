"""El auditor independiente, parametrizado por tipo de día, repite la revisión laboral del 6 de octubre.

Tarda varios minutos: corre solo con PRUEBAS_LENTAS=1, desde esta carpeta.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

from auditoria_independiente import ROOT, auditar_resultado, salida_por_defecto

AQUI = Path(__file__).resolve().parent
# La fecha cambia en cada corrida y las huellas cubren el código de metodo_hibrido, que cambió el 27-oct.
VARIABLES = {'fecha_utc', 'sha256_protegidos'}


@unittest.skipUnless(os.environ.get('PRUEBAS_LENTAS'), 'prueba lenta: usar PRUEBAS_LENTAS=1')
class AuditoriaIndependiente(unittest.TestCase):
    def test_laboral_repite_la_revision_del_6_de_octubre(self):
        guardada = json.loads((AQUI / 'auditoria_independiente.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            auditar_resultado(ROOT / 'metodo_hibrido/resultados/completa_417_20261006',
                              ROOT / 'metodo_hibrido/instancia_417', Path(tmp))
            nueva = json.loads((Path(tmp) / 'auditoria_independiente.json').read_text())
        for clave in sorted(set(guardada) - VARIABLES):
            with self.subTest(clave=clave):
                self.assertEqual(nueva[clave], guardada[clave])
        self.assertEqual(nueva['servicio'], 'L')

    def test_acepta_rutas_relativas_a_la_carpeta_actual(self):
        resultado = os.path.relpath(ROOT / 'metodo_hibrido/resultados/completa_417_20261006')
        instancia = os.path.relpath(ROOT / 'metodo_hibrido/instancia_417')
        with tempfile.TemporaryDirectory() as tmp:
            reporte = auditar_resultado(resultado, instancia, Path(tmp))
        self.assertEqual((reporte['servicio'], reporte['buses']), ('L', 7427))


class SalidaPorDefecto(unittest.TestCase):
    def test_laboral_escribe_junto_a_la_evidencia_del_6_de_octubre(self):
        self.assertEqual(salida_por_defecto('L', Path('/resultado')), AQUI)

    def test_fin_de_semana_no_sobrescribe_la_evidencia_laboral(self):
        for servicio in ('S', 'D'):
            with self.subTest(servicio=servicio):
                self.assertEqual(salida_por_defecto(servicio, Path('/resultado')),
                                 Path('/resultado/revision_independiente'))


if __name__ == '__main__':
    unittest.main()
