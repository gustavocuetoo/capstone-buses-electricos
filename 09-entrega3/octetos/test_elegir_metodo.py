"""La regla elige el método más barato con el mismo tiempo (pares+tríos si nadie le gana)."""
import unittest

from elegir_metodo import elegir

PRESUPUESTOS = (600, 1200, 2400)


def fila(metodo, costo, presupuesto, seleccion='', semilla=0, error=''):
    return dict(metodo=metodo, seleccion=seleccion, semilla=str(semilla), presupuesto_s=str(float(presupuesto)),
                costo_total_usd='' if error else str(costo), error=error)


def tabla(retador=None):
    """pares_trios cuesta 100 en todos los tiempos; `retador` agrega filas de otro método."""
    filas = [fila('solo_base', 110, 0)] + [fila('pares_trios', 100, p) for p in PRESUPUESTOS]
    filas += [fila('octetos', 100.5, p, 'parecidos') for p in PRESUPUESTOS]
    return filas + (retador or [])


class Regla(unittest.TestCase):
    def test_sin_retador_mas_barato_se_queda_pares_trios(self):
        self.assertEqual(elegir(tabla()), dict(metodo='pares_trios', seleccion='', semillas=[0]))

    def test_basta_ser_algo_mas_barato_para_ganar(self):
        retador = [fila('trios', 99.5, p, 'parecidos') for p in PRESUPUESTOS]
        self.assertEqual(elegir(tabla(retador))['metodo'], 'trios')

    def test_gana_el_retador_mas_barato_en_la_mayoria_de_los_tiempos(self):
        retador = [fila('cuartetos', 98, 600, 'parecidos'), fila('cuartetos', 98, 1200, 'parecidos'),
                   fila('cuartetos', 100, 2400, 'parecidos')]
        self.assertEqual(elegir(tabla(retador)), dict(metodo='cuartetos', seleccion='parecidos', semillas=[0]))

    def test_ganar_en_un_solo_tiempo_no_basta(self):
        retador = [fila('cuartetos', 95, 2400, 'parecidos')] + [fila('cuartetos', 100, p, 'parecidos')
                                                                for p in (600, 1200)]
        self.assertEqual(elegir(tabla(retador))['metodo'], 'pares_trios')

    def test_al_azar_cuenta_el_promedio_de_las_semillas_y_se_ignoran_los_errores(self):
        # Semillas 1 y 2: 99 y 102 → promedio 100,5 (peor, aunque una semilla sea mejor). La semilla 3 falló.
        retador = [fila('quintetos', c, p, 'azar', s) for p in PRESUPUESTOS for s, c in ((1, 99), (2, 102))]
        retador += [fila('quintetos', 0, p, 'azar', 3, error='RuntimeError') for p in PRESUPUESTOS]
        self.assertEqual(elegir(tabla(retador))['metodo'], 'pares_trios')
        ganador = [fila('quintetos', 97, p, 'azar', s) for p in PRESUPUESTOS for s in (1, 2)]
        self.assertEqual(elegir(tabla(ganador)), dict(metodo='quintetos', seleccion='azar', semillas=[1, 2]))

    def test_entre_dos_retadores_gana_el_de_mayor_ahorro_promedio(self):
        retador = [fila('cuartetos', 98, p, 'parecidos') for p in PRESUPUESTOS]
        retador += [fila('mezcla', 96, p, 'parecidos') for p in PRESUPUESTOS]
        self.assertEqual(elegir(tabla(retador))['metodo'], 'mezcla')

    def test_una_tabla_con_varios_casos_no_se_mezcla(self):
        filas = tabla()
        filas[1] = dict(filas[1], instancia='otro_caso')
        with self.assertRaises(ValueError):
            elegir(filas)

    def test_sin_pares_trios_valido_no_se_puede_decidir(self):
        filas = [fila('pares_trios', 0, p, error='RuntimeError') for p in PRESUPUESTOS]
        with self.assertRaises(ValueError):
            elegir(filas)


if __name__ == '__main__':
    unittest.main()
