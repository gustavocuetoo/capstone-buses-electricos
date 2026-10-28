#!/usr/bin/env python3
"""Reconstrucción geográfica de los viajes a partir del GTFS.

El diccionario de datos documenta campos `start_stop`, `end_stop`,
`origin_lat/lon` y `dest_lat/lon` que NO existen en ningún archivo entregado.
Este módulo demuestra que son derivables: la primera y última parada de cada
viaje están en `stop_times.txt` y sus coordenadas en `stops.txt`.

Sobre esa reconstrucción se calculan las distancias de traslado en vacío
(deadhead) entre terminales y hacia los electroterminales, que son el insumo
que el modelo de scheduling necesita y que hoy falta.

Este módulo es una biblioteca: no se ejecuta solo.
"""

from __future__ import annotations

import csv
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

RADIO_TIERRA_KM = 6371.0

# Supuesto explícito: los traslados en vacío no hacen paradas de pasajeros, por
# lo que circulan más rápido que la velocidad comercial observada (~16 km/h).
# Valor a validar con el profesor; ver preguntas_profesor.tex.
VELOCIDAD_DEADHEAD_KMH = 25.0

# Factor de rodeo: la distancia por calle es mayor que la línea recta.
# 1,35 es el valor habitual reportado para redes urbanas en grilla deformada.
FACTOR_RODEO = 1.35

PRIMERA_SECUENCIA = "1"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia de círculo máximo en kilómetros."""
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    return 2 * RADIO_TIERRA_KM * asin(sqrt(a))


def distancia_calle_km(origen: tuple[float, float], destino: tuple[float, float]) -> float:
    """Distancia estimada por calle: haversine corregida por factor de rodeo."""
    return FACTOR_RODEO * haversine_km(origen[0], origen[1], destino[0], destino[1])


def tiempo_deadhead_min(distancia_km: float) -> float:
    """Minutos de traslado en vacío para una distancia dada."""
    return 60.0 * distancia_km / VELOCIDAD_DEADHEAD_KMH


def cargar_coordenadas_paradas(ruta_stops: Path) -> dict[str, tuple[float, float]]:
    """stop_id -> (lat, lon). Descarta filas sin coordenadas utilizables."""
    coordenadas: dict[str, tuple[float, float]] = {}
    with ruta_stops.open(encoding="utf-8-sig", newline="") as archivo:
        for fila in csv.DictReader(archivo):
            lat, lon = fila.get("stop_lat"), fila.get("stop_lon")
            if not lat or not lon:
                continue
            coordenadas[fila["stop_id"]] = (float(lat), float(lon))
    return coordenadas


def cargar_terminales_de_viaje(
    ruta_stop_times: Path, ids_viaje: frozenset[str]
) -> dict[str, tuple[str, str]]:
    """trip_id -> (parada de inicio, parada de término).

    Recorre `stop_times.txt` una sola vez quedándose con la parada de menor y
    de mayor `stop_sequence` por viaje. El archivo tiene ~1,3 M de filas, así
    que evitamos cargarlo completo en memoria.
    """
    extremos: dict[str, tuple[int, str, int, str]] = {}
    with ruta_stop_times.open(encoding="utf-8-sig", newline="") as archivo:
        for fila in csv.DictReader(archivo):
            id_viaje = fila["trip_id"]
            if id_viaje not in ids_viaje:
                continue
            secuencia = int(fila["stop_sequence"])
            parada = fila["stop_id"]
            actual = extremos.get(id_viaje)
            if actual is None:
                extremos[id_viaje] = (secuencia, parada, secuencia, parada)
                continue
            min_seq, min_stop, max_seq, max_stop = actual
            if secuencia < min_seq:
                min_seq, min_stop = secuencia, parada
            if secuencia > max_seq:
                max_seq, max_stop = secuencia, parada
            extremos[id_viaje] = (min_seq, min_stop, max_seq, max_stop)

    return {v: (datos[1], datos[3]) for v, datos in extremos.items()}


def coordenadas_de_viaje(
    terminales: dict[str, tuple[str, str]],
    coordenadas: dict[str, tuple[float, float]],
) -> dict[str, tuple[tuple[float, float], tuple[float, float]]]:
    """trip_id -> (coord de inicio, coord de término). Omite viajes sin geo."""
    reconstruidos = {}
    for id_viaje, (parada_ini, parada_fin) in terminales.items():
        origen = coordenadas.get(parada_ini)
        destino = coordenadas.get(parada_fin)
        if origen is None or destino is None:
            continue
        reconstruidos[id_viaje] = (origen, destino)
    return reconstruidos


def distancia_al_electroterminal_mas_cercano(
    punto: tuple[float, float], electroterminales: list[tuple[float, float]]
) -> float:
    """Kilómetros hasta el electroterminal más cercano (pull-in / pull-out)."""
    return min(distancia_calle_km(punto, depot) for depot in electroterminales)
