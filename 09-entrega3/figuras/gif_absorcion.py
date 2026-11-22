"""Animación de la jugada de absorción: un bus donante reparte sus viajes entre los otros del grupo.

Es un ejemplo ilustrativo (horarios inventados) para la presentación y el informe. Muestra un grupo de
4 buses (1 donante y 3 receptores), pero la jugada es la misma para cualquier tamaño de grupo k: el
donante reparte todos sus viajes entre los otros k − 1 y, si el plan sigue siendo factible y más
barato, el grupo queda con un bus menos (metodo_hibrido/grupos.py, movimiento «absorcion_k_a_k-1»).

Uso, desde la raíz del repositorio:
    python3 09-entrega3/figuras/gif_absorcion.py

Escribe en 09-entrega3/figuras/:
  - absorcion.gif: la animación;
  - absorcion_pasos.png: los cuatro pasos en una sola figura, para el informe.
"""
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.animation import FuncAnimation, PillowWriter  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

SALIDA = Path(__file__).resolve().parent

# Paleta de referencia validada (skill dataviz).
FONDO, TEXTO, TEXTO_2, GRILLA = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
RECEPTOR, DONANTE, CARGA = '#9ec5f4', '#eb6834', '#1baf7a'

BUSES = ['Bus 1', 'Bus 2', 'Bus 3', 'Bus 4 (donante)']
FILA = {0: 3, 1: 2, 2: 1, 3: 0}  # fila en el gráfico: el donante va abajo
VIAJES = {
    0: [(6.0, 7.5), (9.6, 11.2), (15.0, 16.5), (19.0, 20.5)],
    1: [(6.5, 8.0), (12.5, 14.0), (17.0, 18.6), (20.3, 21.6)],
    2: [(7.0, 9.0), (11.0, 12.5), (14.5, 16.0), (20.1, 21.5)],
}
DONADOS = [((7.8, 9.3), 0), ((10.2, 11.8), 1), ((16.4, 18.0), 2)]  # (horario, bus que lo recibe)
RECARGA = (2, (18.2, 19.6))  # bus 3 queda corto de batería: recarga antes de su último viaje
ALTO = 0.56
CUADROS_MOVER, CUADROS_PAUSA = 10, 14


def _viaje(ax, ini, fin, fila, color, alfa=1.0, borde=None):
    caja = FancyBboxPatch((ini, fila - ALTO / 2), fin - ini, ALTO, boxstyle='round,pad=0,rounding_size=0.08',
                          facecolor=color, edgecolor=borde or FONDO, linewidth=1.5 if borde else 1, alpha=alfa)
    ax.add_patch(caja)


def _base(ax, titulo, subtitulo):
    ax.clear()
    ax.set_facecolor(FONDO)
    ax.set_xlim(5.5, 22.2)
    ax.set_ylim(-0.75, 3.75)
    ax.set_yticks([FILA[i] for i in range(4)])
    ax.set_yticklabels(BUSES, fontsize=10, color=TEXTO_2)
    ax.set_xticks(range(6, 23, 2))
    ax.set_xticklabels([f'{h:02d}:00' for h in range(6, 23, 2)], fontsize=8.5, color=TEXTO_2)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    for i in range(4):
        ax.axhline(FILA[i], color=GRILLA, lw=1, zorder=0)
    ax.set_title(titulo, loc='left', fontsize=13, color=TEXTO, pad=26)
    ax.text(0, 1.035, subtitulo, transform=ax.transAxes, fontsize=9.5, color=TEXTO_2)


def estado(paso, avance=1.0):
    """Qué dibujar en cada paso: 0 plan actual, 1..3 se mueven los viajes, 4 recarga, 5 bus eliminado."""
    movidos = min(paso, 3)
    viajes = []
    for b, lista in VIAJES.items():
        viajes += [(ini, fin, FILA[b], RECEPTOR, 1.0, None) for ini, fin in lista]
    for k, ((ini, fin), destino) in enumerate(DONADOS):
        if k < movidos - 1 or (k == movidos - 1 and paso > movidos):
            fila = FILA[destino]
        elif k == movidos - 1:
            fila = FILA[3] + (FILA[destino] - FILA[3]) * avance
        else:
            fila = FILA[3]
        viajes.append((ini, fin, fila, DONANTE, 1.0, TEXTO if k == movidos - 1 and paso <= 3 else None))
    return viajes


TEXTOS = [
    ('Plan actual: 4 buses', 'El bus 4 tiene pocos viajes. ¿Pueden hacerlos los otros 3 en sus huecos libres?'),
    ('Paso 1: el primer viaje va al bus 1', 'Cabe en el hueco libre del bus 1, con tiempo para llegar al inicio.'),
    ('Paso 2: el segundo viaje va al bus 2', 'Cada viaje del donante se inserta en algún receptor del grupo.'),
    ('Paso 3: el tercer viaje va al bus 3', 'Todos los viajes del bus 4 quedaron cubiertos por los otros buses.'),
    ('Paso 4: se agenda una recarga', 'El bus 3 ya no alcanza con su batería: un modelo entero pequeño decide dónde y cuánto cargar.'),
    ('Resultado: 3 buses, uno menos', 'Se acepta solo si el plan es factible y más barato: −USD 250 al día por el bus eliminado.'),
]


def dibujar(ax, paso, avance=1.0):
    titulo, sub = TEXTOS[paso]
    _base(ax, titulo, sub)
    for ini, fin, fila, color, alfa, borde in estado(paso, avance):
        _viaje(ax, ini, fin, fila, color, alfa, borde)
    if paso >= 4:
        b, (ini, fin) = RECARGA
        _viaje(ax, ini, fin, FILA[b], CARGA)
        ax.text((ini + fin) / 2, FILA[b] + ALTO / 2 + 0.12, 'carga', ha='center', fontsize=8.5, color=TEXTO_2)
    if paso >= 5:
        ax.plot([5.6, 22.1], [FILA[3], FILA[3]], color=DONANTE, lw=2)
        ax.text(13.8, FILA[3], '  bus eliminado  ', ha='center', va='center', fontsize=10, color=DONANTE,
                bbox=dict(facecolor=FONDO, edgecolor=DONANTE, boxstyle='round,pad=0.3'))
    ax.legend(handles=[FancyBboxPatch((0, 0), 1, 1, facecolor=c, edgecolor=FONDO, label=l)
                       for c, l in ((RECEPTOR, 'Viaje de un receptor'), (DONANTE, 'Viaje del bus donante'),
                                    (CARGA, 'Recarga en electroterminal'))],
              loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False, fontsize=8.5)


def cuadros():
    lista = [(0, 1.0)] * CUADROS_PAUSA
    for paso in (1, 2, 3):
        lista += [(paso, i / CUADROS_MOVER) for i in range(1, CUADROS_MOVER + 1)] + [(paso, 1.0)] * CUADROS_PAUSA
    lista += [(4, 1.0)] * CUADROS_PAUSA + [(5, 1.0)] * (2 * CUADROS_PAUSA)
    return lista


def main():
    fig, ax = plt.subplots(figsize=(9, 4.3), facecolor=FONDO)
    fig.subplots_adjust(left=0.15, right=0.98, top=0.82, bottom=0.2)
    lista = cuadros()
    anim = FuncAnimation(fig, lambda i: dibujar(ax, *lista[i]), frames=len(lista))
    anim.save(SALIDA / 'absorcion.gif', writer=PillowWriter(fps=12), dpi=110)
    plt.close(fig)

    fig, ejes = plt.subplots(4, 1, figsize=(9, 14), facecolor=FONDO)
    for ax, paso in zip(ejes, (0, 3, 4, 5)):
        dibujar(ax, paso)
    fig.tight_layout(h_pad=3)
    fig.savefig(SALIDA / 'absorcion_pasos.png', dpi=170, facecolor=FONDO)
    plt.close(fig)


if __name__ == '__main__':
    main()
