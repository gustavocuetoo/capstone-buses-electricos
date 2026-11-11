"""Escribe cifras_sectores.tex: todas las cifras del informe salen de los datos, no se tipean a mano.

Uso:  python3 cifras_sectores.py
"""
from collections import defaultdict
from pathlib import Path

import datos_geo

AQUI = Path(__file__).resolve().parent
DIA = 'L'
RUTA_EJEMPLO = '101'
MARGEN_AJUSTADO = 0.05  # la segunda mejor opción queda a menos de 5 % de la primera


def miles(numero):
    return f'{numero:,.0f}'.replace(',', '.')


def decimal(numero):
    return f'{numero:.1f}'.replace('.', ',')


def sumas_por_ruta(filas_distancias):
    """route_id -> {electroterminal: km en vacío sumados}. Es la misma cuenta de fase1/preparar.py."""
    sumas = defaultdict(lambda: defaultdict(float))
    for fila in filas_distancias:
        if not fila['distancia_km']:
            raise ValueError(f"Distancia a electroterminal ausente en la ruta {fila['route_id']}")
        sumas[fila['route_id']][int(fila['depot_id'])] += float(fila['distancia_km'])
    return {ruta: dict(por_terminal) for ruta, por_terminal in sumas.items()}


def rutas_ajustadas(sumas, margen):
    """Rutas cuyo segundo mejor electroterminal queda a menos de `margen` del mejor."""
    cantidad = 0
    for por_terminal in sumas.values():
        mejor, segundo = sorted(por_terminal.values())[:2]
        if (segundo - mejor) / mejor < margen:
            cantidad += 1
    return cantidad


def comando(nombre, valor):
    return f'\\newcommand{{\\{nombre}}}{{{valor}}}'


def filas_tabla(resumen, terminales):
    total = sum(datos['corridas'] for datos in resumen.values())
    filas = []
    for terminal in terminales:
        datos = resumen[terminal['sector']]
        filas.append(f"\\cuadro{{sector{terminal['sector']}}} {terminal['sector']} & {terminal['nombre']} & "
                     f"{datos['rutas']} & {miles(datos['corridas'])} & {round(100 * datos['corridas'] / total)}\\,\\% \\\\")
    return '\n'.join(filas)


def filas_ejemplo(terminales, por_terminal):
    mejor = min(por_terminal, key=por_terminal.get)
    filas = []
    for terminal in terminales:
        km = decimal(por_terminal[terminal['sector']])
        if terminal['sector'] == mejor:
            filas.append(f"\\rowcolor{{azulclaro}}\\textbf{{{terminal['nombre']}}} & \\textbf{{{km}}} \\\\")
        else:
            filas.append(f"{terminal['nombre']} & {km} \\\\")
    return '\n'.join(filas), next(t['nombre'] for t in terminales if t['sector'] == mejor)


def macros(resumen, terminales, ejemplo, ajustadas):
    ruta, nombre_ruta, por_terminal = ejemplo
    total_rutas = sum(datos['rutas'] for datos in resumen.values())
    tabla_ejemplo, ganador = filas_ejemplo(terminales, por_terminal)
    lineas = [
        '% Archivo generado por cifras_sectores.py. No editar a mano.',
        comando('TotalRutas', miles(total_rutas)),
        comando('TotalCorridas', miles(sum(datos['corridas'] for datos in resumen.values()))),
        comando('TotalPlazas', miles(sum(t['plazas'] for t in terminales))),
        comando('RutasAjustadas', miles(ajustadas)),
        comando('PctRutasAjustadas', round(100 * ajustadas / total_rutas)),
        comando('RutaEjemplo', ruta),
        comando('NombreRutaEjemplo', nombre_ruta.replace(' - ', '--')),
        comando('GanadorEjemplo', ganador),
        comando('FilasSectores', '%\n' + filas_tabla(resumen, terminales) + '%\n'),
        comando('FilasEjemplo', '%\n' + tabla_ejemplo + '%\n'),
    ]
    return '\n'.join(lineas) + '\n'


def main():
    codigo = datos_geo.carpeta_codigo()
    corridas = datos_geo.leer_csv(codigo / 'output/fase1/corridas.csv')
    distancias = datos_geo.leer_csv(codigo / 'output/distancias_electroterminales/distancias_recorridos_electroterminales.csv')
    sectores = datos_geo.leer_sectores(codigo / 'output/fase1/sectores.csv')
    terminales = datos_geo.leer_electroterminales(datos_geo.RAIZ / '01-datos/depots.csv')
    nombres = {f['route_id']: f['route_long_name'] for f in datos_geo.leer_csv(datos_geo.RAIZ / '01-datos/gtfs/routes.txt')}
    sumas = sumas_por_ruta(distancias)
    for ruta, sector in sectores.items():
        if min(sumas[ruta], key=sumas[ruta].get) != sector:
            raise ValueError(f'La ruta {ruta} no quedó en el electroterminal de menor suma: revisar sectores.csv')
    texto = macros(datos_geo.resumen_por_sector(corridas, DIA), terminales,
                   ejemplo=(RUTA_EJEMPLO, nombres[RUTA_EJEMPLO], sumas[RUTA_EJEMPLO]),
                   ajustadas=rutas_ajustadas(sumas, MARGEN_AJUSTADO))
    (AQUI / 'cifras_sectores.tex').write_text(texto, encoding='utf-8')
    print(texto)


if __name__ == '__main__':
    main()
