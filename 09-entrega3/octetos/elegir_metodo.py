"""Elige, con la tabla del día laboral, el método que se corre en sábado y domingo.

Regla (decidida el 11-nov): gana el mejor de todos, el más barato. Un método reemplaza a pares+tríos
si es más barato que pares+tríos con el mismo tiempo en la mayoría de los tiempos probados; si hay
varios así, gana el de mayor ahorro promedio. Con selección al azar cuenta el promedio de las
semillas; las corridas con error no cuentan.

Imprime en una línea los argumentos para correr_metodos.py (por ejemplo «--metodos solo_base pares_trios»)
y en stderr el motivo, para que quede en el registro.

Uso: .venv-optimizacion/bin/python 09-entrega3/octetos/elegir_metodo.py <tabla_dia_laboral.csv>
"""
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from metodo_hibrido.caso_base import read_csv  # noqa: E402

NUESTRO = ('pares_trios', '')
UMBRAL = 0.0  # basta con ser más barato (antes se exigía más de 1 %)


def _agrupar(filas):
    """Costos válidos por (método, selección) y por tiempo, y las semillas usadas por cada uno."""
    costos = defaultdict(lambda: defaultdict(list))
    semillas = defaultdict(set)
    for f in filas:
        if f['error'].strip() or f['metodo'] == 'solo_base':
            continue
        clave = (f['metodo'], f['seleccion'])
        costos[clave][float(f['presupuesto_s'])].append(float(f['costo_total_usd']))
        semillas[clave].add(int(f['semilla']))
    return costos, semillas


def _ahorros(por_tiempo, referencia):
    """Ahorro relativo frente a pares+tríos en cada tiempo que ambos tienen."""
    return [1 - mean(costos) / referencia[t] for t, costos in por_tiempo.items() if t in referencia]


def elegir(filas):
    casos = {f.get('instancia') for f in filas}
    if len(casos) > 1:
        raise ValueError(f'La tabla mezcla {len(casos)} casos; la decisión se toma con uno solo')
    costos, semillas = _agrupar(filas)
    referencia = {t: mean(c) for t, c in costos.get(NUESTRO, {}).items()}
    if not referencia:
        raise ValueError('La tabla no tiene corridas válidas de pares_trios: no se puede decidir')
    ganador, mejor_ahorro = NUESTRO, 0.0
    for clave, por_tiempo in costos.items():
        ahorros = _ahorros(por_tiempo, referencia) if clave != NUESTRO else []
        gana_la_mayoria = 2 * sum(a > UMBRAL for a in ahorros) > len(referencia)
        if gana_la_mayoria and mean(ahorros) > mejor_ahorro:
            ganador, mejor_ahorro = clave, mean(ahorros)
    metodo, seleccion = ganador
    return dict(metodo=metodo, seleccion=seleccion, semillas=sorted(semillas[ganador]))


def argumentos(eleccion):
    """Argumentos de correr_metodos.py para el método elegido, con el plan inicial como referencia."""
    args = ['--metodos', 'solo_base', eleccion['metodo']]
    if eleccion['seleccion']:
        args += ['--selecciones', eleccion['seleccion']]
    if eleccion['seleccion'] == 'azar':
        args += ['--semillas', *map(str, eleccion['semillas'])]
    return args


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    eleccion = elegir(read_csv(Path(sys.argv[1])))
    print(f"Método elegido con el día laboral: {eleccion}", file=sys.stderr)
    print(' '.join(argumentos(eleccion)))


if __name__ == '__main__':
    main()
