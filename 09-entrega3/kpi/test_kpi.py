"""Pruebas de los scripts de KPI y uso de electroterminales.

    python3 -m pytest -q 09-entrega3/kpi/test_kpi.py
"""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kpi_planes as kp  # noqa: E402
import planes as pl  # noqa: E402
import uso_electroterminales as ue  # noqa: E402

PAR = dict(bateria_kwh=350., reserva_kwh=35., consumo_kwh_km=1.4, potencia_kw=180.,
           capacidades={e: dict(plazas=10, conexiones=4) for e in ue.TERMINALES},
           tarifas=[(0, 8, .1), (8, 14, .15), (14, 17, .22), (17, 19, .15), (19, 22, .22), (22, 24, .11)])


def _plan_chico(tmp_path, **cambios):
    """Dos buses: B1 carga dos bloques en E2, B2 no carga."""
    jornadas = pd.DataFrame([
        dict(bus_id='B1', cadena_fase2='x', sector_id=2, terminal_inicial='T01', terminal_final='E2', corridas=3,
             km_servicio=100., km_vacio=20., carga_kwh=25., sesiones=1, energia_minima_kwh=40.,
             energia_final_kwh=200., costo_usd=250 + 60 + 4 + 5),
        dict(bus_id='B2', cadena_fase2='x', sector_id=3, terminal_inicial='T02', terminal_final='T02', corridas=2,
             km_servicio=50., km_vacio=10., carga_kwh=0., sesiones=0, energia_minima_kwh=266.,
             energia_final_kwh=266., costo_usd=250 + 30),
    ])
    recargas = pd.DataFrame([
        dict(bus_id='B1', orden=1, tipo='carga', origen='E2', destino='E2', inicio_s=61200, fin_s=61500,
             distancia_km=0., carga_kwh=15., corrida_id='', energia_inicial_kwh=40., energia_final_kwh=55.),
        dict(bus_id='B1', orden=2, tipo='carga', origen='E2', destino='E2', inicio_s=61500, fin_s=61800,
             distancia_km=0., carga_kwh=10., corrida_id='', energia_inicial_kwh=55., energia_final_kwh=65.),
    ])
    resumen = dict(verificado=True, corridas=5, buses=2, km=180., carga_kwh=25., sesiones=1, costo_buses_usd=500,
                   costo_km_usd=90., costo_energia_usd=4., costo_sesiones_usd=5, costo_total_usd=599.,
                   energia_minima_kwh=40., capacidades={'E2': dict(cargas_simultaneas_maximas=1)})
    resumen.update(cambios)
    jornadas.to_csv(tmp_path / 'jornadas.csv', index=False)
    recargas.to_csv(tmp_path / 'recargas.csv', index=False)
    (tmp_path / 'resumen.json').write_text(json.dumps(resumen))
    return pl.leer_plan('metodo', 'L', tmp_path)


def test_kpi_de_un_plan_chico(tmp_path):
    k = kp.kpi(_plan_chico(tmp_path), PAR)
    assert k['buses'] == 2 and k['corridas'] == 5
    assert k['pct_km_vacio'] == pytest.approx(100 * 30 / 180)
    assert k['energia_consumida_kwh'] == pytest.approx(1.4 * 180)
    assert k['buses_que_cargan'] == 1 and k['pct_buses_que_cargan'] == pytest.approx(50)
    assert k['energia_a_reponer_kwh'] == pytest.approx(150 + 84)
    assert k['buses_terminan_en_E'] == 1
    assert k['cargas_simultaneas_max'] == 1


def test_detecta_planes_inconsistentes(tmp_path):
    with pytest.raises(ValueError, match='buses'):
        _plan_chico(tmp_path, buses=3)


def test_bloques_reparte_la_energia(tmp_path):
    r = pd.DataFrame([dict(origen='E1', bus_id='B', inicio_s=150, fin_s=750, carga_kwh=30.)])
    b = pl.bloques(r)
    assert list(b['bloque_s']) == [0, 300, 600]
    assert list(b['carga_kwh']) == pytest.approx([7.5, 15, 7.5])


def test_perfil_y_resumen(tmp_path):
    plan = _plan_chico(tmp_path)
    prof = ue.perfil(plan)
    e2 = prof[prof['electroterminal'] == 'E2']
    assert e2['buses_cargando'].max() == 1
    assert e2['carga_kwh'].sum() == pytest.approx(25)
    assert e2.loc[e2['bloque_s'] == 61200, 'mw'].iloc[0] == pytest.approx(15 / (300 / 3600) / 1000)
    res = ue.resumen(plan, prof, PAR).set_index('electroterminal')
    assert res.at['E2', 'buses_cargando_max'] == 1
    assert res.at['E2', 'hora_pico'] == '17:00'
    assert res.at['E2', 'kwh_17_19h'] == pytest.approx(25)
    ue.validar_con_auditor(plan, res.reset_index())


def test_ahorro_contra_caso_base():
    t = pd.DataFrame([dict(kpi='buses', caso_base_L=100., metodo_L=90.)])
    a = kp.tabla_ahorro(t)
    fila = a[a['kpi'] == 'buses'].iloc[0]
    assert fila['diferencia'] == -10 and fila['pct'] == pytest.approx(-10)


@pytest.mark.skipif(not (pl.RAIZ / pl.PLANES[0][2]).exists(), reason='faltan los planes del repositorio')
def test_planes_del_repositorio_cuadran_con_el_auditor():
    par = pl.leer_parametros()
    for plan in pl.leer_planes():
        ue.validar_con_auditor(plan, ue.resumen(plan, ue.perfil(plan), par))
