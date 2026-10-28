"""Calcula la maxima cantidad de recorridos de buses simultaneos.

Usa los archivos GTFS routes.txt, trips.txt, stop_times.txt y frequencies.txt.
La reconstruccion es deterministica: para cada ventana de frecuencia genera
salidas en start_time + n * headway_secs, siempre que sean menores que end_time.
"""

import argparse
import csv
from pathlib import Path


def leer_csv(ruta):
    with ruta.open("r", encoding="utf-8-sig", newline="") as archivo:
        yield from csv.DictReader(archivo)


def a_segundos(hora):
    """Convierte HH:MM:SS a segundos; admite horas GTFS mayores que 24."""
    horas, minutos, segundos = map(int, hora.split(":"))
    return horas * 3600 + minutos * 60 + segundos


def mostrar_hora(segundos):
    horas, resto = divmod(segundos, 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"


def calcular_peak(carpeta_gtfs, tipo_dia="L"):
    # 1. Seleccionar las rutas de buses de la agencia RM.
    rutas_rm = {
        fila["route_id"]
        for fila in leer_csv(carpeta_gtfs / "routes.txt")
        if fila["agency_id"] == "RM" and fila["route_type"] == "3"
    }

    # 2. Seleccionar los trip_id del tipo de dia solicitado.
    viajes = {
        fila["trip_id"]
        for fila in leer_csv(carpeta_gtfs / "trips.txt")
        if fila["route_id"] in rutas_rm and fila["service_id"] == tipo_dia
    }

    # 3. Obtener primera salida y ultima llegada de cada trip_id.
    # timing[trip_id] = [primera_secuencia, primera_salida,
    #                    ultima_secuencia, ultima_llegada]
    timing = {}
    for fila in leer_csv(carpeta_gtfs / "stop_times.txt"):
        trip_id = fila["trip_id"]
        if trip_id not in viajes:
            continue

        secuencia = int(fila["stop_sequence"])
        llegada = a_segundos(fila["arrival_time"])
        salida = a_segundos(fila["departure_time"])

        if trip_id not in timing:
            timing[trip_id] = [secuencia, salida, secuencia, llegada]
        else:
            datos = timing[trip_id]
            if secuencia < datos[0]:
                datos[0], datos[1] = secuencia, salida
            if secuencia > datos[2]:
                datos[2], datos[3] = secuencia, llegada

    # 4. Reconstruir cada corrida y crear sus eventos de inicio y termino.
    # Un inicio suma 1 bus activo; un termino resta 1.
    eventos = []
    corridas = 0

    for fila in leer_csv(carpeta_gtfs / "frequencies.txt"):
        trip_id = fila["trip_id"]
        if trip_id not in viajes or trip_id not in timing:
            continue

        inicio = a_segundos(fila["start_time"])
        fin_ventana = a_segundos(fila["end_time"])
        frecuencia = int(fila["headway_secs"])
        duracion = timing[trip_id][3] - timing[trip_id][1]

        salida = inicio
        while salida < fin_ventana:
            termino = salida + duracion
            eventos.append((salida, 1))
            eventos.append((termino, -1))
            corridas += 1
            salida += frecuencia

    # 5. Barrido cronologico. En un empate se procesa primero -1 y luego +1:
    # el intervalo es [inicio, termino), por lo que al terminar deja de estar activo.
    eventos.sort(key=lambda evento: (evento[0], evento[1]))

    activos = 0
    peak = 0
    hora_peak = None

    for instante, cambio in eventos:
        activos += cambio
        if activos > peak:
            peak = activos
            hora_peak = instante

    return corridas, peak, hora_peak


def main():
    parser = argparse.ArgumentParser(
        description="Calcula el peak de buses simultaneamente activos."
    )
    parser.add_argument(
        "--gtfs",
        type=Path,
        default=Path(__file__).resolve().parent / "gtfs",
        help="Carpeta que contiene los archivos GTFS (por defecto: ./gtfs).",
    )
    parser.add_argument(
        "--dia",
        choices=("L", "S", "D"),
        default="L",
        help="Tipo de dia: L=laboral, S=sabado, D=domingo/festivo.",
    )
    argumentos = parser.parse_args()

    corridas, peak, hora_peak = calcular_peak(argumentos.gtfs, argumentos.dia)

    nombres = {"L": "laboral", "S": "sabado", "D": "domingo/festivo"}
    print(f"Tipo de dia: {nombres[argumentos.dia]}")
    print(f"Corridas reconstruidas: {corridas:,}".replace(",", "."))
    print(f"Peak de buses simultaneos: {peak:,}".replace(",", "."))
    print(f"Primer instante del peak: {mostrar_hora(hora_peak)}")


if __name__ == "__main__":
    main()
