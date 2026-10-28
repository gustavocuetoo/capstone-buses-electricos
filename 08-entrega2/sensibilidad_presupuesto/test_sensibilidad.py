"""Pruebas del barrido y del gráfico de la lámina 32. Correr desde esta carpeta:
    python -m unittest test_sensibilidad
"""
import csv
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from barrido import nombre_corrida, plan_de_corridas
from grafico import ENSAYO_ORIGINAL, dibujar, leer_barrido, leer_corrida, miles, resumir
from licencia_gratuita import salida_de

CAMPOS_ETAPAS = ["etapa", "buses", "corridas", "km", "carga_kwh", "sesiones", "costo_total_usd", "tiempo_algoritmo_s"]


def corrida_falsa(raiz: Path, nombre: str, presupuesto: float, costos: tuple, buses: tuple) -> Path:
    """Carpeta con la forma de una salida de ejecutar.py y valores inventados."""
    carpeta = raiz / nombre
    for sub in ("02_pares", "03_trios"):
        (carpeta / sub).mkdir(parents=True)
        (carpeta / sub / "busqueda.json").write_text(json.dumps(dict(
            tiempo_busqueda_s=presupuesto + 0.4, intentos=10, rondas=1, motivo_fin="presupuesto", mejoras=3,
            etapa_aceptada=True, rechazo="", tiempo_etapa_s=presupuesto + 2)), encoding="utf8")
    (carpeta / "ejecucion.json").write_text(json.dumps(dict(parametros=dict(
        presupuesto_pares=presupuesto, presupuesto_trios=presupuesto))), encoding="utf8")
    (carpeta / "comparacion.json").write_text("{}", encoding="utf8")
    with (carpeta / "comparacion_etapas.csv").open("w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(CAMPOS_ETAPAS)
        for etapa, costo, n in zip(("caso_base", "02_pares", "03_trios"), costos, buses):
            escritor.writerow([etapa, n, 33220, 0, 0, 0, costo, 1.0])
    return carpeta


class PlanDeCorridas(unittest.TestCase):
    def test_cada_repeticion_tiene_cada_presupuesto_una_vez(self):
        plan = plan_de_corridas((30, 60, 120, 240), 3)
        self.assertEqual(len(plan), 12)
        for repeticion in (1, 2, 3):
            bloque = [b for b, r in plan if r == repeticion]
            self.assertEqual(Counter(bloque), Counter((30, 60, 120, 240)))

    def test_el_orden_es_reproducible(self):
        self.assertEqual(plan_de_corridas((30, 60, 120), 2), plan_de_corridas((30, 60, 120), 2))

    def test_nombre_de_carpeta(self):
        self.assertEqual(nombre_corrida(30, 1), "B030_r1")

    def test_el_lanzador_encuentra_la_carpeta_de_salida(self):
        self.assertEqual(salida_de(["--salida", "x/B030_r1", "--presupuesto-pares", "30"]), Path("x/B030_r1"))
        self.assertIsNone(salida_de(["--presupuesto-pares", "30"]))
        self.assertIsNone(salida_de(["--salida"]))


class LecturaDeCorridas(unittest.TestCase):
    def test_reproduce_las_cifras_del_ensayo_original(self):
        corrida = leer_corrida(ENSAYO_ORIGINAL)
        self.assertAlmostEqual(corrida["parejas_y_trios"]["ahorro_usd"], 10738.45, places=2)
        self.assertEqual(corrida["parejas_y_trios"]["buses_evitados"], 41)
        self.assertAlmostEqual(corrida["parejas"]["ahorro_usd"], 1415348.70 - 1410013.06, places=1)
        self.assertEqual(corrida["parejas"]["buses_evitados"], 18)
        self.assertEqual((corrida["parejas"]["intentos"], corrida["parejas"]["mejoras"]), (169, 60))

    def test_calcula_el_ahorro_contra_la_construccion(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = corrida_falsa(Path(tmp), "B030_r1", 30, (1_000_000, 996_000, 990_000), (100, 98, 95))
            corrida = leer_corrida(carpeta)
        self.assertEqual(corrida["presupuesto_s"], 30)
        self.assertAlmostEqual(corrida["parejas"]["ahorro_usd"], 4_000)
        self.assertAlmostEqual(corrida["parejas_y_trios"]["ahorro_usd"], 10_000)
        self.assertEqual(corrida["parejas_y_trios"]["buses_evitados"], 5)

    def test_rechaza_corridas_con_distinta_construccion(self):
        with tempfile.TemporaryDirectory() as tmp:
            corrida_falsa(Path(tmp), "B030_r1", 30, (1_000_000, 996_000, 990_000), (100, 98, 95))
            corrida_falsa(Path(tmp), "B060_r1", 60, (1_000_500, 996_000, 990_000), (100, 98, 95))
            with self.assertRaises(ValueError):
                leer_barrido(Path(tmp))

    def test_ignora_carpetas_sin_comparacion(self):
        with tempfile.TemporaryDirectory() as tmp:
            corrida_falsa(Path(tmp), "B030_r1", 30, (1_000_000, 996_000, 990_000), (100, 98, 95))
            (Path(tmp) / "B060_r1").mkdir()
            self.assertEqual([c["corrida"] for c in leer_barrido(Path(tmp))], ["B030_r1"])


class ResumenYGrafico(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        raiz = Path(self.tmp.name)
        for r, final in enumerate((990_000, 992_000, 989_000), start=1):
            corrida_falsa(raiz, f"B060_r{r}", 60, (1_000_000, 996_000, final), (100, 98, 96))
            corrida_falsa(raiz, f"B120_r{r}", 120, (1_000_000, 995_000, final - 1_000), (100, 97, 95))
        self.corridas = leer_barrido(raiz)

    def tearDown(self):
        self.tmp.cleanup()

    def test_mediana_minimo_y_maximo(self):
        r = resumir(self.corridas)[("parejas_y_trios", 60)]
        self.assertEqual((r["n"], r["mediana"], r["minimo"], r["maximo"]), (3, 10_000, 8_000, 11_000))

    def test_dibuja_un_png_del_tamano_del_recuadro(self):
        destino = Path(self.tmp.name) / "g.png"
        dibujar(self.corridas, destino)
        with destino.open("rb") as archivo:
            cabecera = archivo.read(24)
        ancho, alto = int.from_bytes(cabecera[16:20], "big"), int.from_bytes(cabecera[20:24], "big")
        self.assertEqual((ancho, alto), (2805, 1206))

    def test_formato_chileno(self):
        self.assertEqual(miles(10738.45), "10.738")


if __name__ == "__main__":
    unittest.main()
