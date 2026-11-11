"""Lee los datos del mapa de sectores: comunas, autopistas, trazados y sectores.

No usa geopandas ni shapely: el GeoPackage se lee con sqlite3 y el WKB se
decodifica a mano, igual que en `construir_distancias_electroterminales.py`.
"""
import csv
import sqlite3
import struct
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CARPETAS_CODIGO = ('CODIGO apstone', 'codigo')
LARGO_CAJA_GPKG = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}
WKB_LINEA, WKB_POLIGONO, WKB_MULTILINEA, WKB_MULTIPOLIGONO = 2, 3, 5, 6
CODIFICACION = 'utf-8-sig'


def carpeta_codigo(raiz=RAIZ):
    """Devuelve la carpeta del código, que en el repositorio tiene dos nombres posibles."""
    for nombre in CARPETAS_CODIGO:
        if (raiz / nombre / 'output').is_dir():
            return raiz / nombre
    raise FileNotFoundError(f'No se encontró ninguna de las carpetas {CARPETAS_CODIGO} en {raiz}')


def leer_csv(ruta):
    if not Path(ruta).is_file():
        raise FileNotFoundError(f'Falta el archivo de datos: {ruta}')
    with open(ruta, encoding=CODIFICACION, newline='') as archivo:
        return list(csv.DictReader(archivo))


def _leer_puntos(blob, pos, orden):
    cantidad = struct.unpack_from(orden + 'I', blob, pos)[0]
    plano = struct.unpack_from(f'{orden}{2 * cantidad}d', blob, pos + 4)
    return list(zip(plano[0::2], plano[1::2])), pos + 4 + 16 * cantidad


def _leer_wkb(blob, pos):
    """Devuelve (partes, posición siguiente). Una línea es una lista de puntos; un polígono, una lista de anillos."""
    orden = '<' if blob[pos] == 1 else '>'
    tipo = struct.unpack_from(orden + 'I', blob, pos + 1)[0] % 1000
    pos += 5
    if tipo == WKB_LINEA:
        puntos, pos = _leer_puntos(blob, pos, orden)
        return [puntos], pos
    if tipo == WKB_POLIGONO:
        cantidad = struct.unpack_from(orden + 'I', blob, pos)[0]
        pos += 4
        anillos = []
        for _ in range(cantidad):
            anillo, pos = _leer_puntos(blob, pos, orden)
            anillos.append(anillo)
        return [anillos], pos
    if tipo in (WKB_MULTILINEA, WKB_MULTIPOLIGONO):
        cantidad = struct.unpack_from(orden + 'I', blob, pos)[0]
        pos += 4
        partes = []
        for _ in range(cantidad):
            nuevas, pos = _leer_wkb(blob, pos)
            partes.extend(nuevas)
        return partes, pos
    raise ValueError(f'Tipo de geometría WKB no admitido: {tipo}')


def geometria_gpkg(blob):
    """Decodifica una geometría de GeoPackage en una lista de líneas o de polígonos."""
    tipo_caja = (blob[3] >> 1) & 7
    partes, _ = _leer_wkb(blob, 8 + LARGO_CAJA_GPKG[tipo_caja])
    return partes


def toca_caja(puntos, caja):
    xmin, xmax, ymin, ymax = caja
    xs = [p[0] for p in puntos]
    ys = [p[1] for p in puntos]
    return not (max(xs) < xmin or min(xs) > xmax or max(ys) < ymin or min(ys) > ymax)


def _abrir_gpkg(ruta):
    if not Path(ruta).exists():
        raise FileNotFoundError(f'Falta el GeoPackage: {ruta}')
    return sqlite3.connect(Path(ruta).resolve().as_uri() + '?mode=ro', uri=True)


def leer_comunas(ruta_gpkg, caja):
    """Lista de (nombre, polígonos) de las comunas que tocan la caja."""
    consulta = "SELECT name, geom FROM gis_osm_adminareas_a_free WHERE fclass='admin_level8'"
    comunas = []
    with _abrir_gpkg(ruta_gpkg) as conexion:
        for nombre, blob in conexion.execute(consulta):
            poligonos = geometria_gpkg(blob)
            if any(toca_caja(poligono[0], caja) for poligono in poligonos):
                comunas.append((nombre, poligonos))
    return comunas


def leer_trazados(ruta_shapes):
    """Diccionario shape_id -> lista ordenada de (lon, lat)."""
    puntos = defaultdict(list)
    for fila in leer_csv(ruta_shapes):
        puntos[fila['shape_id']].append(
            (int(fila['shape_pt_sequence']), float(fila['shape_pt_lon']), float(fila['shape_pt_lat'])))
    return {forma: [(lon, lat) for _, lon, lat in sorted(lista)] for forma, lista in puntos.items()}


def leer_sectores(ruta_sectores):
    """Diccionario route_id -> número de sector."""
    return {fila['route_id']: int(fila['sector_id']) for fila in leer_csv(ruta_sectores)}


def trazados_por_ruta(corridas):
    """Diccionario route_id -> conjunto de shape_id que usa esa ruta."""
    formas = defaultdict(set)
    for fila in corridas:
        formas[fila['route_id']].add(fila['shape_id'])
    return dict(formas)


def resumen_por_sector(corridas, dia):
    """Rutas distintas y corridas de cada sector en un tipo de día (L, S o D)."""
    rutas = defaultdict(set)
    cantidad = defaultdict(int)
    for fila in corridas:
        if fila['service_id'] != dia:
            continue
        sector = int(fila['sector_id'])
        rutas[sector].add(fila['route_id'])
        cantidad[sector] += 1
    return {sector: dict(rutas=len(rutas[sector]), corridas=cantidad[sector]) for sector in sorted(cantidad)}


def leer_electroterminales(ruta_depots):
    return [dict(sector=int(f['depot_id']), nombre=f['nombre'], lon=float(f['lon']), lat=float(f['lat']),
                 plazas=int(f['capacity'])) for f in leer_csv(ruta_depots)]
