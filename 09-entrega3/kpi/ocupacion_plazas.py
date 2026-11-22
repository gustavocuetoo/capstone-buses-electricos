"""Ocupación de plazas de cada electroterminal durante el día, desde actividades.csv.

Una plaza está ocupada por un bus que carga o espera en el electroterminal (como en
metodo_hibrido/verificar.py). Este script separa los buses que ya terminaron su jornada y quedan
estacionados hasta el final del horizonte de los que están ahí durante la operación, para ver si las
plazas se llenan de día o solo al cierre.

actividades.csv no está en GitHub por su tamaño: está en cada carpeta 04_final del computador donde se
corrió el método (la escribe export() de metodo_hibrido/ejecutar.py).

Uso, desde la raíz del repositorio:
    python3 09-entrega3/kpi/ocupacion_plazas.py --plan metodo_hibrido/resultados/completa_417_20261006/04_final \\
        --nombre metodo_L

Escribe en 09-entrega3/kpi/resultados/:
  - plazas_<nombre>_perfil.csv: por electroterminal y bloque de 5 min, máximo de buses presentes, de ellos
    cargando y de ellos estacionados al cierre;
  - plazas_<nombre>_resumen.csv: por electroterminal, pico total, pico sin contar el estacionamiento final,
    hora de cada pico y minutos al 100 %;
  - plazas_<nombre>.png: ocupación a lo largo del día, un panel por electroterminal.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import planes as pl  # noqa: E402
from uso_electroterminales import FONDO, GRILLA, TERMINALES, TEXTO, TEXTO_2, _ejes  # noqa: E402

SALIDA = Path(__file__).resolve().parent / 'resultados'
CATEGORIAS = ('cargando', 'operacion', 'cierre')
COLORES = {'cargando': '#2a78d6', 'operacion': '#1baf7a', 'cierre': '#c3c2b7'}
ETIQUETAS = {'cargando': 'Cargando', 'operacion': 'Esperando durante la operación',
             'cierre': 'Estacionados al cierre de la jornada'}


def estancias(actividades):
    """Intervalos [inicio, fin) de cada bus en un electroterminal, con su categoría."""
    a = actividades[actividades['tipo'].isin(['carga', 'espera'])
                    & actividades['origen'].astype(str).str.startswith('E')].copy()
    fin_bus = actividades.groupby('bus_id')['fin_s'].max()
    ultima = a['fin_s'].values == fin_bus.reindex(a['bus_id']).values
    a['categoria'] = 'operacion'
    a.loc[a['tipo'] == 'carga', 'categoria'] = 'cargando'
    a.loc[(a['tipo'] == 'espera') & ultima, 'categoria'] = 'cierre'
    return a[['bus_id', 'origen', 'inicio_s', 'fin_s', 'categoria']].rename(columns={'origen': 'electroterminal'})


def _barrido(intervalos):
    """Función escalonada (instante, buses presentes) a partir de intervalos [inicio, fin)."""
    cambios = defaultdict(int)
    for ini, fin in intervalos:
        cambios[ini] += 1
        cambios[fin] -= 1
    valor, puntos = 0, []
    for t in sorted(cambios):
        valor += cambios[t]
        puntos.append((t, valor))
    if valor != 0:
        raise ValueError('Ocupación sin cierre')
    return puntos


def _maximo_por_bloque(puntos, inicio, fin, bloque=pl.BLOQUE_S):
    """Máximo de la función escalonada dentro de cada bloque [b, b+bloque)."""
    bloques = list(range(inicio, fin, bloque))
    maximos = dict.fromkeys(bloques, 0)
    valor, k = 0, 0
    for b in bloques:
        while k < len(puntos) and puntos[k][0] <= b:
            valor = puntos[k][1]
            k += 1
        m = valor
        j = k
        while j < len(puntos) and puntos[j][0] < b + bloque:
            m = max(m, puntos[j][1])
            j += 1
        maximos[b] = m
    return maximos


def perfil(est, inicio, fin):
    filas = []
    for e in TERMINALES:
        x = est[est['electroterminal'] == e]
        total = _maximo_por_bloque(_barrido(zip(x['inicio_s'], x['fin_s'])), inicio, fin)
        por_cat = {c: _maximo_por_bloque(_barrido(zip(x.loc[x['categoria'] == c, 'inicio_s'],
                                                        x.loc[x['categoria'] == c, 'fin_s'])), inicio, fin)
                   for c in CATEGORIAS}
        sin_cierre = _maximo_por_bloque(_barrido(zip(x.loc[x['categoria'] != 'cierre', 'inicio_s'],
                                                      x.loc[x['categoria'] != 'cierre', 'fin_s'])), inicio, fin)
        for b in total:
            filas.append(dict(electroterminal=e, bloque_s=b, presentes=total[b], sin_cierre=sin_cierre[b],
                              **{c: por_cat[c][b] for c in CATEGORIAS}))
    return pd.DataFrame(filas)


def _hora(s):
    return f'{int(s) // 3600 % 24:02d}:{int(s) % 3600 // 60:02d}' + (' (+1)' if s >= 86400 else '')


def resumen(prof, par):
    filas = []
    for e in TERMINALES:
        p = prof[prof['electroterminal'] == e]
        plazas = par['capacidades'][e]['plazas']
        pico, pico_op = int(p['presentes'].max()), int(p['sin_cierre'].max())
        filas.append(dict(
            electroterminal=e, nombre=pl.NOMBRES_E[e], plazas=plazas,
            presentes_max=pico, pct_plazas_max=100 * pico / plazas,
            hora_pico=_hora(p.loc[p['presentes'].idxmax(), 'bloque_s']) if pico else '',
            presentes_max_sin_cierre=pico_op, pct_plazas_max_sin_cierre=100 * pico_op / plazas,
            hora_pico_sin_cierre=_hora(p.loc[p['sin_cierre'].idxmax(), 'bloque_s']) if pico_op else '',
            minutos_al_100=int((p['presentes'] >= plazas).sum()) * pl.BLOQUE_S // 60,
            minutos_al_100_sin_cierre=int((p['sin_cierre'] >= plazas).sum()) * pl.BLOQUE_S // 60,
            estacionados_al_cierre=int(p['cierre'].max()),
        ))
    return pd.DataFrame(filas)


def figura(prof, par, titulo, ruta):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, ejes = plt.subplots(5, 1, figsize=(8, 8.5), sharex=True, facecolor=FONDO)
    for ax, e in zip(ejes, TERMINALES):
        p = prof[prof['electroterminal'] == e]
        x = p['bloque_s'] / 3600
        ax.stackplot(x, [p[c] for c in CATEGORIAS], colors=[COLORES[c] for c in CATEGORIAS],
                     labels=[ETIQUETAS[c] for c in CATEGORIAS], edgecolor=FONDO, linewidth=0.3)
        plazas = par['capacidades'][e]['plazas']
        ax.set_xlim(x.min(), x.max())
        ax.axhline(plazas, color=TEXTO_2, lw=1, ls=(0, (4, 3)))
        ax.text(x.max(), plazas, f' {plazas} plazas', va='center', fontsize=7.5, color=TEXTO_2)
        ax.set_ylim(0, plazas * 1.15)
        ax.set_ylabel(f'{e}\n{pl.NOMBRES_E[e]}', fontsize=8, color=TEXTO_2, rotation=0, ha='right', va='center')
        ax.grid(axis='y', color=GRILLA, lw=0.6)
        _ejes(ax)
    manijas, etiquetas = ejes[0].get_legend_handles_labels()
    fig.legend(manijas, etiquetas, loc='upper right', bbox_to_anchor=(0.98, 1.0), fontsize=8, frameon=False, ncol=1)
    marcas = [h for h in range(-3, 30, 3) if prof['bloque_s'].min() <= h * 3600 <= prof['bloque_s'].max()]
    ejes[-1].set_xticks(marcas)
    ejes[-1].set_xticklabels([f'{h % 24:02d}' + ('+1' if h >= 24 else '') for h in marcas])
    ejes[-1].set_xlabel('Hora del día (+1 = día siguiente)', color=TEXTO_2, fontsize=9)
    fig.suptitle(titulo, x=0.02, ha='left', fontsize=11, color=TEXTO)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(ruta, dpi=200, bbox_inches='tight', facecolor=FONDO)
    plt.close(fig)


def analizar(carpeta, nombre, salida=SALIDA, par=None):
    par = par or pl.leer_parametros()
    carpeta = Path(carpeta)
    act = pd.read_csv(carpeta / 'actividades.csv', encoding='utf-8-sig')
    est = estancias(act)
    inicio = int(act['inicio_s'].min()) // pl.BLOQUE_S * pl.BLOQUE_S
    fin = int(act['fin_s'].max())
    prof = perfil(est, inicio, fin)
    res = resumen(prof, par)
    resumen_json = carpeta / 'resumen.json'
    if resumen_json.exists():
        caps = json.loads(resumen_json.read_text(encoding='utf-8'))
        caps = caps.get('caso_base', caps).get('capacidades', {})
        for fila in res.itertuples():
            esperado = caps.get(fila.electroterminal, {}).get('ocupacion_maxima')
            if esperado is not None and esperado != fila.presentes_max:
                raise ValueError(f'{fila.electroterminal}: pico {fila.presentes_max} contra {esperado} del auditor')
    salida = Path(salida)
    salida.mkdir(exist_ok=True)
    prof.to_csv(salida / f'plazas_{nombre}_perfil.csv', index=False)
    res.to_csv(salida / f'plazas_{nombre}_resumen.csv', index=False)
    figura(prof, par, f'Ocupación de plazas por electroterminal ({nombre})', salida / f'plazas_{nombre}.png')
    return prof, res


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--plan', type=Path, required=True, help='Carpeta con actividades.csv (por ejemplo 04_final)')
    parser.add_argument('--nombre', required=True, help='Etiqueta para los archivos de salida, por ejemplo metodo_L')
    parser.add_argument('--salida', type=Path, default=SALIDA)
    args = parser.parse_args()
    _, res = analizar(args.plan, args.nombre, args.salida)
    with pd.option_context('display.float_format', '{:,.1f}'.format, 'display.width', 200):
        print(res.to_string(index=False))


if __name__ == '__main__':
    main()
