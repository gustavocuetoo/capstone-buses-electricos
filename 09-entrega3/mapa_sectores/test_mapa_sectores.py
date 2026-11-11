"""Pruebas de las funciones puras del mapa de sectores."""
import struct
import unittest

import numpy as np

import cifras_metodo
import cifras_sectores
import datos_geo
import mapa_sectores
import zonas


def blob_gpkg(wkb, con_caja=False):
    """Arma un blob de GeoPackage mínimo: cabecera, caja opcional y WKB."""
    banderas = 0b00000011 if con_caja else 0b00000001
    cabecera = b'GP' + bytes([0, banderas]) + struct.pack('<i', 4326)
    caja = struct.pack('<dddd', 0, 1, 0, 1) if con_caja else b''
    return cabecera + caja + wkb


def wkb_linea(puntos):
    plano = [c for p in puntos for c in p]
    return struct.pack('<BII', 1, 2, len(puntos)) + struct.pack(f'<{len(plano)}d', *plano)


def wkb_poligono(anillo):
    plano = [c for p in anillo for c in p]
    return struct.pack('<BIII', 1, 3, 1, len(anillo)) + struct.pack(f'<{len(plano)}d', *plano)


class GeometriaGpkgTest(unittest.TestCase):
    def test_lee_una_linea_sin_caja(self):
        partes = datos_geo.geometria_gpkg(blob_gpkg(wkb_linea([(0, 0), (1, 2)])))
        self.assertEqual(partes, [[(0.0, 0.0), (1.0, 2.0)]])

    def test_lee_un_multipoligono_con_caja(self):
        anillo = [(0, 0), (1, 0), (1, 1), (0, 0)]
        multi = struct.pack('<BII', 1, 6, 2) + wkb_poligono(anillo) * 2
        partes = datos_geo.geometria_gpkg(blob_gpkg(multi, con_caja=True))
        self.assertEqual(len(partes), 2)
        self.assertEqual(partes[0][0], [(float(x), float(y)) for x, y in anillo])

    def test_rechaza_un_tipo_de_geometria_desconocido(self):
        with self.assertRaises(ValueError):
            datos_geo.geometria_gpkg(blob_gpkg(struct.pack('<BI', 1, 17)))

    def test_toca_caja_detecta_puntos_dentro_y_fuera(self):
        caja = (0, 10, 0, 10)
        self.assertTrue(datos_geo.toca_caja([(5, 5), (20, 20)], caja))
        self.assertFalse(datos_geo.toca_caja([(11, 11), (20, 20)], caja))


class ZonasTest(unittest.TestCase):
    def test_a_km_deja_el_origen_en_cero_y_mide_un_grado_de_latitud(self):
        puntos = zonas.a_km([(zonas.LON_ORIGEN, zonas.LAT_ORIGEN), (zonas.LON_ORIGEN, zonas.LAT_ORIGEN + 1)])
        np.testing.assert_allclose(puntos[0], [0, 0], atol=1e-9)
        self.assertAlmostEqual(puntos[1][1], zonas.KM_POR_GRADO_LAT)

    def test_densificar_pone_un_punto_por_paso(self):
        linea = np.array([[0.0, 0.0], [1.0, 0.0]])
        puntos = zonas.densificar(linea, paso_km=0.1)
        self.assertEqual(len(puntos), 10)
        np.testing.assert_allclose(puntos[3], [0.3, 0.0])

    def test_densificar_una_linea_sin_largo_devuelve_su_punto(self):
        linea = np.array([[2.0, 3.0], [2.0, 3.0]])
        np.testing.assert_allclose(zonas.densificar(linea, paso_km=0.1), [[2.0, 3.0]])

    def test_cada_lado_del_mapa_queda_para_el_sector_que_pasa_por_ahi(self):
        y = np.arange(0, 10, 0.1)
        puntos = {1: np.column_stack((np.full_like(y, 2.0), y)),
                  2: np.column_stack((np.full_like(y, 8.0), y))}
        resultado = zonas.zonas_dominantes(puntos, caja_km=(0, 10, 0, 10), celda_km=0.5, sigma_km=0.5, umbral=0.01)
        fila = resultado.dominante[10]
        self.assertEqual(fila[4], 1)
        self.assertEqual(fila[16], 2)
        self.assertGreater(resultado.participacion[10][4], 0.99)

    def test_donde_no_pasan_rutas_no_hay_sector(self):
        puntos = {1: np.array([[1.0, 1.0]] * 50)}
        resultado = zonas.zonas_dominantes(puntos, caja_km=(0, 20, 0, 20), celda_km=0.5, sigma_km=0.5, umbral=0.01)
        self.assertEqual(resultado.dominante[-1][-1], zonas.SIN_SECTOR)
        self.assertEqual(resultado.dominante[2][2], 1)

    def test_zona_compartida_tiene_participacion_cercana_a_la_mitad(self):
        y = np.arange(0, 10, 0.1)
        linea = np.column_stack((np.full_like(y, 5.0), y))
        resultado = zonas.zonas_dominantes({1: linea, 2: linea.copy()}, caja_km=(0, 10, 0, 10),
                                           celda_km=0.5, sigma_km=0.5, umbral=0.01)
        self.assertAlmostEqual(float(resultado.participacion[10][10]), 0.5, places=6)


class ConteoTest(unittest.TestCase):
    def test_resumen_cuenta_rutas_y_corridas_del_dia_pedido(self):
        corridas = [
            dict(service_id='L', sector_id='1', route_id='101'),
            dict(service_id='L', sector_id='1', route_id='101'),
            dict(service_id='L', sector_id='2', route_id='102'),
            dict(service_id='S', sector_id='2', route_id='103'),
        ]
        resumen = datos_geo.resumen_por_sector(corridas, dia='L')
        self.assertEqual(resumen, {1: dict(rutas=1, corridas=2), 2: dict(rutas=1, corridas=1)})


class ImagenTest(unittest.TestCase):
    def test_la_caja_del_mapa_rodea_todos_los_puntos_con_margen(self):
        puntos = {1: np.array([[0.0, 0.0]]), 2: np.array([[10.0, 4.0]])}
        margen = mapa_sectores.MARGEN_KM
        self.assertEqual(mapa_sectores.caja_del_mapa(puntos), (-margen, 10 + margen, -margen, 4 + margen))

    def test_la_imagen_pinta_fuerte_la_mayoria_palida_la_mezcla_y_nada_sin_rutas(self):
        resultado = zonas.Zonas(dominante=np.array([[1, 2, zonas.SIN_SECTOR]]),
                                participacion=np.array([[0.9, 0.4, 0.0]]), caja_km=(0, 3, 0, 1))
        imagen = mapa_sectores.imagen_zonas(resultado)
        self.assertEqual(imagen[0, 0, 3], mapa_sectores.ALFA_CLARO)
        self.assertEqual(imagen[0, 1, 3], mapa_sectores.ALFA_MEZCLA)
        self.assertEqual(imagen[0, 2, 3], 0.0)


class CifrasTest(unittest.TestCase):
    FILAS = [
        dict(route_id='101', depot_id='1', distancia_km='10.0'),
        dict(route_id='101', depot_id='1', distancia_km='5.5'),
        dict(route_id='101', depot_id='2', distancia_km='15.0'),
        dict(route_id='102', depot_id='1', distancia_km='20.0'),
        dict(route_id='102', depot_id='2', distancia_km='20.5'),
    ]

    def test_suma_los_kilometros_de_cada_ruta_a_cada_electroterminal(self):
        sumas = cifras_sectores.sumas_por_ruta(self.FILAS)
        self.assertEqual(sumas['101'], {1: 15.5, 2: 15.0})

    def test_una_distancia_vacia_es_un_error_y_no_un_cero(self):
        with self.assertRaises(ValueError):
            cifras_sectores.sumas_por_ruta([dict(route_id='101', depot_id='1', distancia_km='')])

    def test_cuenta_las_rutas_cuya_decision_es_ajustada(self):
        sumas = cifras_sectores.sumas_por_ruta(self.FILAS)
        self.assertEqual(cifras_sectores.rutas_ajustadas(sumas, margen=0.03), 1)
        self.assertEqual(cifras_sectores.rutas_ajustadas(sumas, margen=0.05), 2)

    def test_formatea_numeros_como_se_escriben_en_chile(self):
        self.assertEqual(cifras_sectores.miles(64502), '64.502')
        self.assertEqual(cifras_sectores.decimal(44.56), '44,6')

    def test_las_macros_incluyen_totales_y_una_fila_por_sector(self):
        resumen = {1: dict(rutas=2, corridas=1500), 2: dict(rutas=1, corridas=500)}
        terminales = [dict(sector=1, nombre='Norte', plazas=150), dict(sector=2, nombre='Sur', plazas=100)]
        texto = cifras_sectores.macros(resumen, terminales, ejemplo=('101', 'A - B', {1: 15.5, 2: 15.0}), ajustadas=1)
        self.assertIn(r'\newcommand{\TotalRutas}{3}', texto)
        self.assertIn(r'\newcommand{\TotalCorridas}{2.000}', texto)
        self.assertIn('Norte & 2 & 1.500 & 75', texto)
        self.assertIn(r'\textbf{15,0}', texto)


class CifrasMetodoTest(unittest.TestCase):
    FILAS = [
        dict(metodo='solo_base', seleccion='', presupuesto_s='0.0', buses='100', costo_total_usd='1000', error=''),
        dict(metodo='trios', seleccion='azar', presupuesto_s='2400.0', buses='90', costo_total_usd='900', error=''),
        dict(metodo='trios', seleccion='azar', presupuesto_s='2400.0', buses='92', costo_total_usd='920', error=''),
        dict(metodo='trios', seleccion='azar', presupuesto_s='600.0', buses='99', costo_total_usd='990', error=''),
    ]

    def test_promedia_las_semillas_del_mismo_presupuesto(self):
        dato = cifras_metodo.promedio(self.FILAS, 'trios', 'azar', 2400.0)
        self.assertEqual(dato, dict(buses=91.0, costo=910.0, corridas=2))

    def test_el_ahorro_se_mide_contra_el_primer_plan(self):
        base = cifras_metodo.promedio(self.FILAS, 'solo_base', '', 0.0)
        dato = cifras_metodo.promedio(self.FILAS, 'trios', 'azar', 2400.0)
        self.assertAlmostEqual(cifras_metodo.ahorro_pct(base, dato), 9.0)

    def test_un_metodo_sin_corridas_es_un_error(self):
        with self.assertRaises(ValueError):
            cifras_metodo.promedio(self.FILAS, 'octetos', 'azar', 2400.0)

    def test_una_corrida_con_error_no_se_promedia(self):
        filas = [dict(self.FILAS[1], error='se cortó')]
        with self.assertRaises(ValueError):
            cifras_metodo.promedio(filas, 'trios', 'azar', 2400.0)


if __name__ == '__main__':
    unittest.main()
