"""Convierte los trazados de las rutas en zonas: qué sector predomina en cada punto del mapa."""
import math
from typing import NamedTuple

import numpy as np
from scipy.ndimage import gaussian_filter

LON_ORIGEN, LAT_ORIGEN = -70.65, -33.47  # centro aproximado de la red
KM_POR_GRADO_LAT = 110.57
KM_POR_GRADO_LON = 111.32 * math.cos(math.radians(LAT_ORIGEN))
SIN_SECTOR = 0


class Zonas(NamedTuple):
    dominante: np.ndarray      # sector que predomina en cada celda; SIN_SECTOR donde no pasan rutas
    participacion: np.ndarray  # fracción de los kilómetros de ruta de la celda que son de ese sector
    caja_km: tuple             # (xmin, xmax, ymin, ymax) de la grilla


def a_km(puntos):
    """Proyecta (lon, lat) a kilómetros respecto del origen. Suficiente para una ciudad."""
    arreglo = np.asarray(puntos, dtype=float)
    return np.column_stack(((arreglo[:, 0] - LON_ORIGEN) * KM_POR_GRADO_LON,
                            (arreglo[:, 1] - LAT_ORIGEN) * KM_POR_GRADO_LAT))


def densificar(linea, paso_km):
    """Puntos cada `paso_km` a lo largo de la línea: cada punto representa ese tramo de ruta."""
    tramos = np.hypot(*np.diff(linea, axis=0).T)
    acumulado = np.concatenate(([0.0], np.cumsum(tramos)))
    if acumulado[-1] == 0:
        return linea[:1].copy()
    posiciones = np.arange(0, acumulado[-1], paso_km)
    return np.column_stack((np.interp(posiciones, acumulado, linea[:, 0]),
                            np.interp(posiciones, acumulado, linea[:, 1])))


def zonas_dominantes(puntos_por_sector, caja_km, celda_km, sigma_km, umbral):
    """Suaviza los kilómetros de ruta de cada sector y elige el sector que predomina en cada celda.

    `umbral` es la densidad suavizada mínima (puntos de ruta por celda) para pintar la celda.
    """
    xmin, xmax, ymin, ymax = caja_km
    bordes_x = np.arange(xmin, xmax + celda_km, celda_km)
    bordes_y = np.arange(ymin, ymax + celda_km, celda_km)
    sectores = sorted(puntos_por_sector)
    capas = []
    for sector in sectores:
        puntos = puntos_por_sector[sector]
        conteo, _, _ = np.histogram2d(puntos[:, 1], puntos[:, 0], bins=(bordes_y, bordes_x))
        capas.append(gaussian_filter(conteo, sigma=sigma_km / celda_km, mode='constant'))
    pila = np.stack(capas)
    total = pila.sum(axis=0)
    con_rutas = total > umbral
    dominante = np.where(con_rutas, np.array(sectores)[pila.argmax(axis=0)], SIN_SECTOR)
    participacion = np.where(con_rutas, pila.max(axis=0) / np.where(con_rutas, total, 1.0), 0.0)
    return Zonas(dominante, participacion, (bordes_x[0], bordes_x[-1], bordes_y[0], bordes_y[-1]))
