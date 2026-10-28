"""El auditor del híbrido aprueba el caso base miope solo si el plan cumple todas sus reglas."""
import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from auditar_caso_base import auditar

RAIZ = Path(__file__).resolve().parents[2]
INSTANCIA_212 = RAIZ / 'metodo_hibrido/instancia_212'
MIOPE_212 = RAIZ / 'CODIGO apstone/output/tres_fases/muestra_212_caso_base'


class AuditoriaCasoBase(unittest.TestCase):
    def test_caso_base_de_212_rutas_se_aprueba(self):
        # El 13-oct este mismo plan pasó el auditor del híbrido sin diferencias.
        resultado = auditar(INSTANCIA_212, MIOPE_212)
        self.assertTrue(resultado['aprobado'])
        self.assertEqual(resultado['diferencias'], [])

    def test_plan_al_que_le_falta_una_corrida_se_rechaza(self):
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp)
            for nombre in ('jornadas.csv', 'resumen.json'):
                shutil.copy(MIOPE_212 / nombre, copia / nombre)
            with open(MIOPE_212 / 'actividades.csv', encoding='utf-8-sig', newline='') as f:
                filas = list(csv.DictReader(f))
            primera = next(i for i, f in enumerate(filas) if f['tipo'] == 'servicio')
            with open(copia / 'actividades.csv', 'w', encoding='utf-8-sig', newline='') as f:
                escritor = csv.DictWriter(f, fieldnames=list(filas[0]))
                escritor.writeheader()
                escritor.writerows(filas[:primera] + filas[primera + 1:])
            resultado = auditar(INSTANCIA_212, copia)
        self.assertFalse(resultado['aprobado'])
        self.assertIn('Discontinuidad', resultado['error'])


if __name__ == '__main__':
    unittest.main()
