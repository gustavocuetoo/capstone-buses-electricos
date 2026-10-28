"""Genera las figuras del informe 2 desde los resultados (PDF vectorial, tipografía tipo Times)."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

import analisis  # noqa: E402
import cifras  # noqa: E402
import fuentes  # noqa: E402

AQUI = Path(__file__).resolve().parents[1]
SERIE_1, SERIE_2 = '#2a78d6', '#eb6834'       # paleta categórica validada (skill dataviz)
TINTA, TINTA_SECUNDARIA, GRILLA = '#0b0b0b', '#52514e', '#e4e3df'
RAMPA_TARIFA = ('#9ec5f4', '#6da7ec', '#3987e5', '#184f95')  # rampa secuencial azul, claro → oscuro
ANCHO = 6.3
ALTO = 2.6
HORAS = range(-2, 28)
plt.rcParams.update({
    'font.family': 'serif', 'font.serif': ['STIXGeneral'], 'mathtext.fontset': 'stix', 'font.size': 9,
    'text.color': TINTA, 'axes.labelcolor': TINTA, 'xtick.color': TINTA_SECUNDARIA,
    'ytick.color': TINTA_SECUNDARIA, 'axes.edgecolor': TINTA_SECUNDARIA,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'axes.grid.axis': 'y',
    'grid.color': GRILLA, 'grid.linewidth': 0.6, 'axes.axisbelow': True, 'lines.linewidth': 1.5,
})


def miles(valor, _posicion=None):
    return f'{valor:,.0f}'.replace(',', '.')


def en_curso_por_hora(corridas):
    intervalos = [(int(c['inicio_s']), int(c['fin_s'])) for c in corridas]
    return [sum(1 for i, f in intervalos if i <= h * 3600 < f) for h in HORAS]


def figura_corridas_por_hora():
    red = en_curso_por_hora(fuentes.leer_csv(fuentes.INSTANCIA_RED / 'corridas.csv'))
    muestra = en_curso_por_hora(fuentes.leer_csv(fuentes.INSTANCIA / 'corridas.csv'))
    fig, ax = plt.subplots(figsize=(ANCHO, ALTO))
    ax.plot(list(HORAS), red, color=SERIE_1, label='Red completa (417 rutas)')
    ax.plot(list(HORAS), muestra, color=SERIE_2, label='Muestra (212 rutas)')
    ax.set_xticks(list(HORAS)[::2], [f'{h % 24:02d}' for h in list(HORAS)[::2]])
    ax.yaxis.set_major_formatter(miles)
    ax.set_xlabel('Hora del día (las horas 00–03 de la derecha son del día siguiente)')
    ax.set_ylabel('Corridas en curso')
    ax.legend(frameon=False, loc='upper left')
    fig.tight_layout()
    fig.savefig(AQUI / 'figures/corridas_por_hora.pdf')
    plt.close(fig)


def figura_energia_por_hora():
    escenario = fuentes.leer_json(fuentes.INSTANCIA / 'escenario.json')
    tarifas = [analisis.tarifa_en_hora(escenario['tarifas'], h) for h in range(24)]
    niveles = sorted(set(tarifas))
    if len(niveles) > len(RAMPA_TARIFA):
        raise ValueError(f'Hay {len(niveles)} tramos de tarifa y la rampa tiene {len(RAMPA_TARIFA)} tonos')
    color_de = dict(zip(niveles, RAMPA_TARIFA))
    paneles = (('Caso base miope', fuentes.MIOPE / 'recargas.csv'),
               ('Modelo híbrido (refinado)', fuentes.REFINADO / '04_final/recargas.csv'))
    fig, ejes = plt.subplots(1, 2, figsize=(ANCHO, ALTO + 0.3))
    for ax, (titulo, ruta) in zip(ejes, paneles):
        energia = analisis.energia_por_hora(fuentes.leer_csv(ruta))
        ax.bar(range(24), [e / 1000 for e in energia], width=0.8, color=[color_de[t] for t in tarifas])
        ax.set_title(titulo, fontsize=9)
        ax.set_xticks(range(0, 24, 4), [f'{h:02d}' for h in range(0, 24, 4)])
        ax.set_xlabel('Hora de inicio de la carga')
        ax.set_ylabel('Energía cargada (MWh)')
    leyenda = [Patch(color=color_de[n], label=f'{n:.2f}'.replace('.', ',') + ' USD/kWh') for n in niveles]
    fig.legend(handles=leyenda, loc='lower center', ncol=len(niveles), frameon=False,
               title='Tarifa de la hora', title_fontsize=9)
    fig.tight_layout(rect=(0, 0.16, 1, 1))
    fig.savefig(AQUI / 'figures/energia_por_hora.pdf')
    plt.close(fig)


def figura_barrido():
    filas = cifras.corridas_barrido()
    presupuestos = sorted({f['presupuesto'] for f in filas})
    medianas = [sorted(f['ahorro'] for f in filas if f['presupuesto'] == b)[1] / 1000 for b in presupuestos]
    fig, ax = plt.subplots(figsize=(ANCHO, ALTO))
    ax.plot(presupuestos, medianas, color=SERIE_1, label='Mediana de 3 repeticiones', zorder=2)
    ax.scatter([f['presupuesto'] for f in filas], [f['ahorro'] / 1000 for f in filas], s=36,
               facecolor=SERIE_1, edgecolor='white', linewidth=1, alpha=0.55, label='Cada repetición', zorder=3)
    ax.set_xscale('log')
    ax.set_xticks(presupuestos, [str(b) for b in presupuestos])
    ax.minorticks_off()
    ax.set_xlabel('Presupuesto por etapa de búsqueda (s, escala logarítmica)')
    ax.set_ylabel('Ahorro sobre la construcción\n(miles de USD/día)')
    ax.legend(frameon=False, loc='upper left')
    fig.tight_layout()
    fig.savefig(AQUI / 'figures/barrido.pdf')
    plt.close(fig)


def main():
    figura_corridas_por_hora()
    figura_energia_por_hora()
    figura_barrido()
    print('3 figuras en figures/')
    return 0


if __name__ == '__main__':
    sys.exit(main())
