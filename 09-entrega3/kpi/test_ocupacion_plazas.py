"""Pruebas de ocupacion_plazas.py.

    python3 -m pytest -q 09-entrega3/kpi/test_ocupacion_plazas.py
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ocupacion_plazas as op  # noqa: E402
import planes as pl  # noqa: E402

RAIZ = pl.RAIZ


def _act(filas):
    return pd.DataFrame(filas, columns=['bus_id', 'orden', 'tipo', 'origen', 'destino', 'inicio_s', 'fin_s'])


def test_separa_carga_operacion_y_cierre():
    act = _act([
        ('A', 1, 'servicio', 'S:1', 'S:2', 0, 600),
        ('A', 2, 'espera', 'E1', 'E1', 600, 900),     # espera durante la operación
        ('A', 3, 'carga', 'E1', 'E1', 900, 1200),
        ('A', 4, 'servicio', 'S:2', 'S:1', 1200, 1800),
        ('A', 5, 'espera', 'T01', 'T01', 1800, 3000),  # termina en un T: no ocupa plazas
        ('B', 1, 'servicio', 'S:3', 'S:4', 0, 1500),
        ('B', 2, 'espera', 'E1', 'E1', 1500, 3000),    # estacionado al cierre
    ])
    est = op.estancias(act)
    assert sorted(est['categoria']) == ['cargando', 'cierre', 'operacion']
    prof = op.perfil(est, 0, 3000)
    e1 = prof[prof['electroterminal'] == 'E1'].set_index('bloque_s')
    assert e1.at[600, 'operacion'] == 1 and e1.at[900, 'cargando'] == 1
    assert e1.at[1500, 'presentes'] == 1 and e1.at[1500, 'cierre'] == 1 and e1.at[1500, 'sin_cierre'] == 0
    assert e1['presentes'].max() == 1


def test_maximo_dentro_del_bloque():
    # Dos buses se cruzan 60 s dentro del mismo bloque: el máximo del bloque es 2.
    puntos = op._barrido([(0, 400), (340, 900)])
    m = op._maximo_por_bloque(puntos, 0, 900)
    assert m[0] == 1 and m[300] == 2 and m[600] == 1


@pytest.mark.skipif(not (RAIZ / '09-entrega3/octetos/casos/mediano_200_sector_1_2_rutas').exists(),
                    reason='faltan los casos del repositorio')
def test_coincide_con_el_auditor_en_un_caso_real(tmp_path):
    """Construye el plan inicial de un caso mediano, lo exporta y compara el pico con el del auditor."""
    sys.path.insert(0, str(RAIZ))
    from metodo_hibrido.caso_base import load_instance, solve
    from metodo_hibrido.ejecutar import export
    trips, *params = load_instance(RAIZ / '09-entrega3/octetos/casos/mediano_200_sector_1_2_rutas')
    plan = tmp_path / 'plan'
    export(plan, solve(trips, *params)[-1], trips, params)
    _, res = op.analizar(plan, 'prueba', tmp_path / 'salida')  # falla si no coincide con el auditor
    assert res['presentes_max'].sum() > 0
