"""Uso de los cargadores de cada electroterminal durante el día, para caso base y método.

Uso, desde la raíz del repositorio:
    python3 09-entrega3/kpi/uso_electroterminales.py

Lee recargas.csv de cada plan de planes.PLANES y escribe en 09-entrega3/kpi/resultados/:
  - uso_e_perfil.csv: por plan, electroterminal y bloque de 5 min: buses cargando, kWh y MW;
  - uso_e_resumen.csv: por plan y electroterminal: pico de buses cargando, % de conexiones, hora del
    pico, MW pico, energía, horas con carga y energía por tramo de tarifa;
  - uso_e_sector_x_electroterminal.csv: dónde carga cada sector (% de su energía en cada E);
  - uso_e_mapa_calor_L.png: % de conexiones en uso por hora, caso base y método (día laboral);
  - uso_e_perfil_L.png: buses cargando a lo largo del día, un panel por electroterminal.

Alcance: mide conexiones (buses cargando). La ocupación de plazas también cuenta buses estacionados
sin cargar; eso necesita actividades.csv, que no está en el repositorio.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import planes as pl  # noqa: E402

SALIDA = Path(__file__).resolve().parent / 'resultados'
TERMINALES = ['E1', 'E2', 'E3', 'E4', 'E5']

# Paleta de referencia validada (skill dataviz): rampa azul secuencial y dos primeros colores categóricos.
AZUL = ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b']
METODO, BASE = '#2a78d6', '#eb6834'
TEXTO, TEXTO_2, GRILLA, FONDO = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'


def perfil(plan):
    """Buses cargando, kWh y MW por electroterminal y bloque de 5 min (con ceros donde no hay carga)."""
    b = pl.bloques(plan.recargas)
    g = b.groupby(['electroterminal', 'bloque_s']).agg(buses_cargando=('bus_id', 'nunique'),
                                                       carga_kwh=('carga_kwh', 'sum'))
    inicio = min(0, int(b['bloque_s'].min())) if len(b) else 0
    fin = max(86400 - pl.BLOQUE_S, int(b['bloque_s'].max())) if len(b) else 86400 - pl.BLOQUE_S
    rejilla = pd.MultiIndex.from_product([TERMINALES, range(inicio, fin + 1, pl.BLOQUE_S)],
                                         names=['electroterminal', 'bloque_s'])
    g = g.reindex(rejilla, fill_value=0).reset_index()
    g['mw'] = g['carga_kwh'] / (pl.BLOQUE_S / 3600) / 1000
    g['hora'] = g['bloque_s'] // 3600
    g.insert(0, 'plan', plan.etiqueta)
    return g


def resumen(plan, prof, par):
    filas = []
    caps = par['capacidades']
    for e in TERMINALES:
        p = prof[prof['electroterminal'] == e]
        r = plan.recargas[plan.recargas['origen'] == e]
        pico = int(p['buses_cargando'].max())
        bloque_pico = int(p.loc[p['buses_cargando'].idxmax(), 'bloque_s']) if pico else None
        por_tarifa = {}
        for ini, fin, precio in par['tarifas']:
            h = (p['bloque_s'] / 3600) % 24
            por_tarifa[f'kwh_{int(ini):02d}_{int(fin):02d}h'] = p.loc[(h >= ini) & (h < fin), 'carga_kwh'].sum()
        filas.append(dict(
            plan=plan.etiqueta, electroterminal=e, nombre=pl.NOMBRES_E[e],
            plazas=caps[e]['plazas'], conexiones=caps[e]['conexiones'],
            buses_cargando_max=pico,
            pct_conexiones_max=100 * pico / caps[e]['conexiones'],
            hora_pico=(f'{bloque_pico // 3600 % 24:02d}:{bloque_pico % 3600 // 60:02d}' if pico else ''),
            bloques_en_el_pico=int((p['buses_cargando'] == pico).sum()) if pico else 0,
            mw_max=p['mw'].max(),
            mw_si_todas_las_conexiones=caps[e]['conexiones'] * par['potencia_kw'] / 1000,
            carga_kwh=r['carga_kwh'].sum(),
            buses_distintos=r['bus_id'].nunique(),
            horas_con_carga=(p['buses_cargando'] > 0).sum() * pl.BLOQUE_S / 3600,
            buses_cargando_medio_si_hay_carga=p.loc[p['buses_cargando'] > 0, 'buses_cargando'].mean(),
            **por_tarifa,
        ))
    t = pd.DataFrame(filas)
    t['pct_carga_total'] = 100 * t['carga_kwh'] / t['carga_kwh'].sum()
    return t


def validar_con_auditor(plan, res):
    """El pico de cargas simultáneas debe coincidir con el que reportó el auditor en resumen.json."""
    caps = plan.resumen.get('capacidades', {})
    for fila in res.itertuples():
        esperado = caps.get(fila.electroterminal, {}).get('cargas_simultaneas_maximas')
        if esperado is not None and esperado != fila.buses_cargando_max:
            raise ValueError(f'{plan.etiqueta} {fila.electroterminal}: pico {fila.buses_cargando_max} '
                             f'contra {esperado} del auditor')


def sector_x_electroterminal(plan):
    m = plan.recargas.merge(plan.jornadas[['bus_id', 'sector_id']], on='bus_id')
    t = m.pivot_table(index='sector_id', columns='origen', values='carga_kwh', aggfunc='sum', fill_value=0)
    t = t.reindex(columns=TERMINALES, fill_value=0)
    pct = 100 * t.div(t.sum(axis=1), axis=0)
    pct.columns = [f'pct_en_{c}' for c in pct.columns]
    pct.insert(0, 'carga_kwh', t.sum(axis=1))
    pct = pct.reset_index().rename(columns={'sector_id': 'sector'})
    pct.insert(0, 'plan', plan.etiqueta)
    return pct


def _ejes(ax):
    ax.set_facecolor(FONDO)
    for lado in ('top', 'right'):
        ax.spines[lado].set_visible(False)
    for lado in ('left', 'bottom'):
        ax.spines[lado].set_color(GRILLA)
    ax.tick_params(colors=TEXTO_2, labelsize=8)


def mapa_calor(perfiles, par, dia, ruta):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    cmap = LinearSegmentedColormap.from_list('azul', ['#f4f8fd'] + AZUL)
    titulos = [('caso_base', 'Caso base'), ('metodo', 'Método')]
    fig, ejes = plt.subplots(2, 1, figsize=(9, 4.6), sharex=True, facecolor=FONDO)
    for ax, (nombre, titulo) in zip(ejes, titulos):
        p = perfiles[f'{nombre}_{dia}']
        p = p[(p['bloque_s'] >= 0) & (p['bloque_s'] < 86400)]
        m = p.groupby(['electroterminal', 'hora'])['buses_cargando'].max().unstack(fill_value=0)
        m = m.reindex(index=TERMINALES, columns=range(24), fill_value=0)
        conex = pd.Series({e: par['capacidades'][e]['conexiones'] for e in TERMINALES})
        pct = 100 * m.div(conex, axis=0)
        im = ax.imshow(pct.values, aspect='auto', cmap=cmap, vmin=0, vmax=100, interpolation='nearest')
        ax.set_yticks(range(5))
        ax.set_yticklabels([f'{e} {pl.NOMBRES_E[e]}' for e in TERMINALES])
        ax.set_title(titulo, loc='left', fontsize=10, color=TEXTO)
        _ejes(ax)
        for s in ax.spines.values():
            s.set_visible(False)
    ejes[-1].set_xticks(range(0, 24, 2))
    ejes[-1].set_xticklabels([f'{h:02d}' for h in range(0, 24, 2)])
    ejes[-1].set_xlabel('Hora del día', color=TEXTO_2, fontsize=9)
    barra = fig.colorbar(im, ax=ejes, fraction=0.025, pad=0.02)
    barra.set_label('% de conexiones en uso (máximo de la hora)', color=TEXTO_2, fontsize=8)
    barra.ax.tick_params(labelsize=8, colors=TEXTO_2)
    barra.outline.set_visible(False)
    fig.suptitle(f'Conexiones de carga en uso por electroterminal, día {pl.DIAS[dia]}',
                 x=0.06, ha='left', fontsize=11, color=TEXTO)
    fig.savefig(ruta, dpi=200, bbox_inches='tight', facecolor=FONDO)
    plt.close(fig)


def perfil_diario(perfiles, par, dia, ruta):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, ejes = plt.subplots(5, 1, figsize=(8, 8.5), sharex=True, facecolor=FONDO)
    for ax, e in zip(ejes, TERMINALES):
        for nombre, color, etiqueta in (('caso_base', BASE, 'Caso base'), ('metodo', METODO, 'Método')):
            p = perfiles[f'{nombre}_{dia}']
            p = p[(p['electroterminal'] == e) & (p['bloque_s'] >= 0) & (p['bloque_s'] < 86400)]
            ax.plot(p['bloque_s'] / 3600, p['buses_cargando'], color=color, lw=1.6, label=etiqueta)
        conex = par['capacidades'][e]['conexiones']
        ax.axhline(conex, color=TEXTO_2, lw=1, ls=(0, (4, 3)))
        ax.text(24, conex, f' {conex} conexiones', va='center', fontsize=7.5, color=TEXTO_2)
        ax.set_ylim(0, conex * 1.12)
        ax.set_ylabel(f'{e}\n{pl.NOMBRES_E[e]}', fontsize=8, color=TEXTO_2, rotation=0, ha='right', va='center')
        ax.grid(axis='y', color=GRILLA, lw=0.6)
        _ejes(ax)
    manijas, etiquetas = ejes[0].get_legend_handles_labels()
    fig.legend(manijas, etiquetas, loc='upper right', bbox_to_anchor=(0.98, 1.0), fontsize=8.5, frameon=False, ncol=2)
    ejes[-1].set_xlim(0, 24)
    ejes[-1].set_xticks(range(0, 25, 2))
    ejes[-1].set_xticklabels([f'{h:02d}' for h in range(0, 25, 2)])
    ejes[-1].set_xlabel('Hora del día', color=TEXTO_2, fontsize=9)
    fig.suptitle(f'Buses cargando a la vez (bloques de 5 min), día {pl.DIAS[dia]}',
                 x=0.02, ha='left', fontsize=11, color=TEXTO)
    fig.tight_layout()
    fig.savefig(ruta, dpi=200, bbox_inches='tight', facecolor=FONDO)
    plt.close(fig)


def main():
    par = pl.leer_parametros()
    planes = pl.leer_planes()
    SALIDA.mkdir(exist_ok=True)
    perfiles, resumenes, matrices = {}, [], []
    for plan in planes:
        prof = perfil(plan)
        res = resumen(plan, prof, par)
        validar_con_auditor(plan, res)
        perfiles[plan.etiqueta] = prof
        resumenes.append(res)
        matrices.append(sector_x_electroterminal(plan))
    pd.concat(perfiles.values()).to_csv(SALIDA / 'uso_e_perfil.csv', index=False)
    resumen_total = pd.concat(resumenes)
    resumen_total.to_csv(SALIDA / 'uso_e_resumen.csv', index=False)
    pd.concat(matrices).to_csv(SALIDA / 'uso_e_sector_x_electroterminal.csv', index=False)
    for dia in pl.DIAS:
        if f'caso_base_{dia}' in perfiles and f'metodo_{dia}' in perfiles:
            mapa_calor(perfiles, par, dia, SALIDA / f'uso_e_mapa_calor_{dia}.png')
            perfil_diario(perfiles, par, dia, SALIDA / f'uso_e_perfil_{dia}.png')
    cols = ['plan', 'electroterminal', 'conexiones', 'buses_cargando_max', 'pct_conexiones_max', 'hora_pico',
            'mw_max', 'carga_kwh', 'pct_carga_total', 'horas_con_carga']
    with pd.option_context('display.float_format', '{:,.1f}'.format, 'display.width', 200):
        print(resumen_total[cols].to_string(index=False))


if __name__ == '__main__':
    main()
