"""KPI de cada plan (caso base y método) y su comparación, por tipo de día.

Uso, desde la raíz del repositorio:
    python3 09-entrega3/kpi/kpi_planes.py

Escribe en 09-entrega3/kpi/resultados/:
  - kpi_planes.csv: una fila por KPI y una columna por plan;
  - kpi_ahorro.csv: diferencia del método contra el caso base, por día;
  - kpi_por_sector.csv: buses, corridas, km y carga por sector y plan;
  - kpi_planes.md: las mismas tablas, para pegar o revisar.

Para agregar un plan (por ejemplo, el de cuartetos), sumar su carpeta en planes.PLANES.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import planes as pl  # noqa: E402

SALIDA = Path(__file__).resolve().parent / 'resultados'

# Nombre, unidad y descripción de cada KPI, en el orden en que se reportan.
DEFINICIONES = [
    ('buses', 'buses', 'Buses utilizados (jornadas)'),
    ('corridas', 'corridas', 'Corridas cubiertas'),
    ('corridas_por_bus', 'corridas/bus', 'Corridas por bus, promedio'),
    ('km_servicio', 'km', 'Kilómetros con pasajeros'),
    ('km_vacio', 'km', 'Kilómetros en vacío (traslados, ida y vuelta a cargar)'),
    ('pct_km_vacio', '%', 'Km en vacío sobre km totales'),
    ('costo_total_usd', 'USD/día', 'Costo total'),
    ('costo_buses_usd', 'USD/día', 'Costo fijo de buses'),
    ('costo_km_usd', 'USD/día', 'Costo por kilómetro'),
    ('costo_energia_usd', 'USD/día', 'Costo de electricidad'),
    ('costo_sesiones_usd', 'USD/día', 'Costo fijo por sesión de carga'),
    ('pct_costo_buses', '%', 'Participación de buses en el costo'),
    ('pct_costo_km', '%', 'Participación de km en el costo'),
    ('pct_costo_energia', '%', 'Participación de electricidad en el costo'),
    ('pct_costo_sesiones', '%', 'Participación de sesiones en el costo'),
    ('costo_por_corrida_usd', 'USD/corrida', 'Costo total por corrida'),
    ('costo_por_km_servicio_usd', 'USD/km', 'Costo total por km con pasajeros'),
    ('energia_consumida_kwh', 'kWh', 'Energía consumida (consumo por km totales)'),
    ('energia_cargada_kwh', 'kWh', 'Energía cargada durante el día'),
    ('pct_energia_cargada', '%', 'Energía cargada sobre consumida'),
    ('precio_medio_energia_usd_kwh', 'USD/kWh', 'Costo de electricidad por kWh cargado'),
    ('sesiones', 'sesiones', 'Sesiones de carga'),
    ('buses_que_cargan', 'buses', 'Buses con al menos una sesión'),
    ('pct_buses_que_cargan', '%', 'Buses con al menos una sesión sobre el total'),
    ('kwh_por_sesion', 'kWh/sesión', 'Energía media por sesión'),
    ('energia_minima_kwh', 'kWh', 'Mínimo estado de carga alcanzado por algún bus'),
    ('energia_final_media_kwh', 'kWh', 'Estado de carga promedio al terminar el día'),
    ('energia_a_reponer_kwh', 'kWh', 'Energía para dejar todos los buses llenos al día siguiente'),
    ('buses_terminan_en_E', 'buses', 'Buses que terminan el día en un electroterminal'),
    ('cargas_simultaneas_max', 'buses', 'Máximo de buses cargando a la vez, suma de los 5 E'),
]


def kpi(plan, par):
    j, s = plan.jornadas, plan.resumen
    km = j['km_servicio'].sum() + j['km_vacio'].sum()
    consumida = par['consumo_kwh_km'] * km
    con_carga = j['sesiones'] > 0
    total = s['costo_total_usd']
    carga = s['carga_kwh']
    por_bloque = pl.bloques(plan.recargas)
    simultaneas = por_bloque.groupby(['electroterminal', 'bloque_s'])['bus_id'].nunique()
    pico = simultaneas.groupby(level='bloque_s').sum().max() if len(simultaneas) else 0
    valores = dict(
        buses=s['buses'],
        corridas=s['corridas'],
        corridas_por_bus=s['corridas'] / s['buses'],
        km_servicio=j['km_servicio'].sum(),
        km_vacio=j['km_vacio'].sum(),
        pct_km_vacio=100 * j['km_vacio'].sum() / km,
        costo_total_usd=total,
        costo_buses_usd=s['costo_buses_usd'],
        costo_km_usd=s['costo_km_usd'],
        costo_energia_usd=s['costo_energia_usd'],
        costo_sesiones_usd=s['costo_sesiones_usd'],
        pct_costo_buses=100 * s['costo_buses_usd'] / total,
        pct_costo_km=100 * s['costo_km_usd'] / total,
        pct_costo_energia=100 * s['costo_energia_usd'] / total,
        pct_costo_sesiones=100 * s['costo_sesiones_usd'] / total,
        costo_por_corrida_usd=total / s['corridas'],
        costo_por_km_servicio_usd=total / j['km_servicio'].sum(),
        energia_consumida_kwh=consumida,
        energia_cargada_kwh=carga,
        pct_energia_cargada=100 * carga / consumida,
        precio_medio_energia_usd_kwh=s['costo_energia_usd'] / carga if carga else float('nan'),
        sesiones=s['sesiones'],
        buses_que_cargan=int(con_carga.sum()),
        pct_buses_que_cargan=100 * con_carga.mean(),
        kwh_por_sesion=carga / s['sesiones'] if s['sesiones'] else float('nan'),
        energia_minima_kwh=j['energia_minima_kwh'].min(),
        energia_final_media_kwh=j['energia_final_kwh'].mean(),
        energia_a_reponer_kwh=(par['bateria_kwh'] - j['energia_final_kwh']).clip(lower=0).sum(),
        buses_terminan_en_E=int(j['terminal_final'].str.startswith('E').sum()),
        cargas_simultaneas_max=int(pico),
    )
    return valores


def tabla_kpi(planes, par):
    columnas = {p.etiqueta: kpi(p, par) for p in planes}
    filas = []
    for clave, unidad, descripcion in DEFINICIONES:
        fila = dict(kpi=clave, unidad=unidad, descripcion=descripcion)
        fila.update({etiqueta: valores[clave] for etiqueta, valores in columnas.items()})
        filas.append(fila)
    return pd.DataFrame(filas)


def tabla_ahorro(tabla):
    """Método contra caso base en los KPI de cantidad y costo, por día."""
    claves = ['buses', 'km_vacio', 'costo_total_usd', 'costo_buses_usd', 'costo_km_usd',
              'costo_energia_usd', 'costo_sesiones_usd', 'energia_cargada_kwh', 'sesiones']
    t = tabla.set_index('kpi')
    filas = []
    for dia in pl.DIAS:
        base, metodo = f'caso_base_{dia}', f'metodo_{dia}'
        if base not in t or metodo not in t:
            continue
        for clave in claves:
            if clave not in t.index:
                continue
            b, m = float(t.at[clave, base]), float(t.at[clave, metodo])
            filas.append(dict(dia=dia, kpi=clave, caso_base=b, metodo=m, diferencia=m - b,
                              pct=100 * (m - b) / b if b else float('nan')))
    return pd.DataFrame(filas)


def tabla_sectores(planes):
    filas = []
    for p in planes:
        j = p.jornadas
        carga_en = p.recargas.merge(j[['bus_id', 'sector_id']], on='bus_id')
        propio = (carga_en['origen'] == 'E' + carga_en['sector_id'].astype(str))
        for sector, g in j.groupby('sector_id'):
            c = carga_en[carga_en['sector_id'] == sector]
            kwh = c['carga_kwh'].sum()
            filas.append(dict(
                plan=p.etiqueta, sector=int(sector), electroterminal=pl.NOMBRES_E[f'E{int(sector)}'],
                buses=len(g), corridas=int(g['corridas'].sum()),
                km_servicio=g['km_servicio'].sum(), km_vacio=g['km_vacio'].sum(),
                carga_kwh=kwh, sesiones=int(g['sesiones'].sum()),
                pct_carga_en_su_electroterminal=100 * c.loc[propio[c.index], 'carga_kwh'].sum() / kwh if kwh else float('nan'),
                costo_usd=g['costo_usd'].sum()))
    return pd.DataFrame(filas)


def _markdown(df, decimales=1):
    def fmt(v):
        if isinstance(v, float):
            return f'{v:,.{decimales}f}'.replace(',', ' ')
        return str(v)
    cab = '| ' + ' | '.join(df.columns) + ' |'
    sep = '|' + '|'.join('---' for _ in df.columns) + '|'
    return '\n'.join([cab, sep] + ['| ' + ' | '.join(fmt(v) for v in fila) + ' |' for fila in df.itertuples(index=False)])


def main():
    par = pl.leer_parametros()
    planes = pl.leer_planes()
    SALIDA.mkdir(exist_ok=True)
    tabla = tabla_kpi(planes, par)
    ahorro = tabla_ahorro(tabla)
    sectores = tabla_sectores(planes)
    tabla.to_csv(SALIDA / 'kpi_planes.csv', index=False)
    ahorro.to_csv(SALIDA / 'kpi_ahorro.csv', index=False)
    sectores.to_csv(SALIDA / 'kpi_por_sector.csv', index=False)
    texto = ['# KPI de los planes (red completa, 417 rutas)', '',
             'Generado por `kpi_planes.py`. No editar a mano.', '',
             '## KPI por plan', '', _markdown(tabla.drop(columns='descripcion')), '',
             '## Método contra caso base', '', _markdown(ahorro), '',
             '## Por sector', '', _markdown(sectores), '']
    (SALIDA / 'kpi_planes.md').write_text('\n'.join(texto), encoding='utf-8')
    with pd.option_context('display.float_format', '{:,.1f}'.format, 'display.width', 200):
        print(tabla.drop(columns='descripcion').to_string(index=False))
        print()
        print(ahorro[ahorro['kpi'].isin(['buses', 'costo_total_usd'])].to_string(index=False))


if __name__ == '__main__':
    main()
