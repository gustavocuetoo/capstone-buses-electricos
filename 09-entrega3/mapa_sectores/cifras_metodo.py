"""Escribe cifras_metodo.tex con los resultados de la red completa (día laboral).

Uso:  python3 cifras_metodo.py
Lee 09-entrega3/octetos/resultados/red_completa_417_L.csv. Los métodos al azar se
promedian sobre sus semillas; los demás tienen una sola corrida.
"""
from pathlib import Path

import datos_geo
from cifras_sectores import comando, miles

AQUI = Path(__file__).resolve().parent
RESULTADOS = datos_geo.RAIZ / '09-entrega3/octetos/resultados/red_completa_417_L.csv'
PRESUPUESTO_S = 2400.0
# (método, selección, nombre en la tabla, prefijo de las macros)
FILAS = [('pares_trios', '', 'Pares y tríos por ranking (Entrega 2)', 'EntregaDos'),
         ('trios', 'parecidos', 'Tríos por ranking', 'TriosRanking'),
         ('trios', 'azar', 'Tríos al azar', 'TriosAzar'),
         ('cuartetos', 'azar', 'Cuartetos al azar', 'Cuartetos'),
         ('quintetos', 'azar', 'Quintetos al azar', 'Quintetos'),
         ('octetos', 'azar', 'Octetos al azar', 'Octetos')]
GANADOR = 'Cuartetos'


def promedio(filas, metodo, seleccion, presupuesto_s):
    """Promedio de buses y costo de las corridas de un método (una por semilla)."""
    elegidas = [f for f in filas if f['metodo'] == metodo and f['seleccion'] == seleccion
                and float(f['presupuesto_s']) == presupuesto_s]
    if not elegidas:
        raise ValueError(f'Sin corridas de {metodo} {seleccion} con {presupuesto_s} s')
    if any(f.get('error') for f in elegidas):
        raise ValueError(f'Hay corridas con error en {metodo} {seleccion}')
    return dict(buses=sum(int(f['buses']) for f in elegidas) / len(elegidas),
                costo=sum(float(f['costo_total_usd']) for f in elegidas) / len(elegidas),
                corridas=len(elegidas))


def ahorro_pct(base, metodo):
    return 100 * (base['costo'] - metodo['costo']) / base['costo']


def pct(numero):
    return f'{numero:.2f}'.replace('.', ',')


def macros(filas):
    base = promedio(filas, 'solo_base', '', 0.0)
    lineas = ['% Archivo generado por cifras_metodo.py. No editar a mano.',
              comando('BusesBase', miles(base['buses'])), comando('CostoBase', miles(base['costo']))]
    tabla = [f"Primer plan rápido (paso 1) & {miles(base['buses'])} & {miles(base['costo'])} & -- \\\\"]
    for metodo, seleccion, nombre, prefijo in FILAS:
        dato = promedio(filas, metodo, seleccion, PRESUPUESTO_S)
        lineas += [comando('Buses' + prefijo, miles(dato['buses'])),
                   comando('Ahorro' + prefijo, pct(ahorro_pct(base, dato))),
                   comando('MenosBuses' + prefijo, miles(base['buses'] - dato['buses'])),
                   comando('AhorroUsd' + prefijo, miles(base['costo'] - dato['costo']))]
        fila = f"{nombre} & {miles(dato['buses'])} & {miles(dato['costo'])} & $-${pct(ahorro_pct(base, dato))}\\,\\%"
        if prefijo == GANADOR:
            campos = [f'\\textbf{{{campo.strip()}}}' for campo in fila.split('&')]
            fila = '\\rowcolor{verdeclaro}' + ' & '.join(campos)
        tabla.append(fila + ' \\\\')
    entrega_dos = promedio(filas, 'pares_trios', '', PRESUPUESTO_S)
    ganador = promedio(filas, 'cuartetos', 'azar', PRESUPUESTO_S)
    lineas.append(comando('MenosQueEntregaDos', miles(entrega_dos['buses'] - ganador['buses'])))
    lineas.append(comando('FilasMetodos', '%\n' + '\n'.join(tabla) + '%\n'))
    return '\n'.join(lineas) + '\n'


def main():
    texto = macros(datos_geo.leer_csv(RESULTADOS))
    (AQUI / 'cifras_metodo.tex').write_text(texto, encoding='utf-8')
    print(texto)


if __name__ == '__main__':
    main()
