#!/usr/bin/env python3
"""Figuras y macros del informe de la Entrega 1.

Reconstruye las corridas del GTFS con exactamente la misma metodología que
declara el informe (filtro `agency_id=RM` + `route_type=3`, expansión
`t_n = start_time + n * headway` con `t_n < end_time`) y produce:

  NOMBRE_PROYECTO_GRUPO_XX/figures/fig_concurrencia.pdf
  NOMBRE_PROYECTO_GRUPO_XX/figures/fig_distribuciones.pdf
  NOMBRE_PROYECTO_GRUPO_XX/chapters/metricas_datos.tex

Además verifica contra las cifras publicadas en el informe: si alguna deja de
cuadrar, el script falla en vez de generar figuras inconsistentes con el texto.

Uso:  python3 02-analisis-datos/figuras_informe.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

# --------------------------------------------------------------------------
# Configuración
# --------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parent.parent
DIR_DATOS = RAIZ / "01-datos"
DIR_GTFS = DIR_DATOS / "gtfs"
DIR_INFORME = RAIZ.parent / "NOMBRE_PROYECTO_GRUPO_XX"
DIR_FIGURAS = DIR_INFORME / "figures"
DIR_CAPITULOS = DIR_INFORME / "chapters"

# Filtro que aísla los buses RED del resto del GTFS (Metro, Metrotren, aeropuerto).
AGENCIA_RED = "RM"
TIPO_RUTA_BUS = "3"

# Tipos de día que se estudian por separado.
SERVICIOS = ("L", "S", "D")
NOMBRE_SERVICIO = {"L": "Laboral", "S": "Sábado", "D": "Domingo/festivo"}

# Parámetros del vehículo de referencia (vehicles.csv) y consumo derivado.
BATERIA_KWH = 350.0
AUTONOMIA_KM = 250.0
SOC_MINIMO = 0.10
CONSUMO_KWH_KM = BATERIA_KWH / AUTONOMIA_KM  # 1,4 kWh/km
ENERGIA_UTIL_KWH = BATERIA_KWH * (1 - SOC_MINIMO)

SEGUNDOS_POR_MINUTO = 60
SEGUNDOS_POR_HORA = 3600
HORAS_POR_DIA = 24

# Umbrales usados para caracterizar la cola de las distribuciones. No son
# filtros: ninguna corrida se elimina, solo se cuentan para reportarlas.
DURACION_CORTA_MIN = 10
DURACION_LARGA_MIN = 180
DISTANCIA_CORTA_KM = 5
DISTANCIA_LARGA_KM = 50
VELOCIDAD_IMPLAUSIBLE_KMH = 40

# Tiempo mínimo entre el fin de una corrida y el inicio de la siguiente del mismo bus.
CONEXION_MINIMA_MIN = 5

# Cifras publicadas en el informe. El script se detiene si deja de reproducirlas.
CIFRAS_ESPERADAS = {
    "rutas_red": 417,
    "patrones_totales": 14464,
    "corridas": {"L": 64502, "S": 43619, "D": 37377},
    "pico": {"L": 6601, "S": 3860, "D": 2900},
}

COLOR_LABORAL = "#003E5C"
COLOR_SABADO = "#B06210"
COLOR_DOMINGO = "#6B7B83"
COLOR_REFERENCIA = "#9E2620"
COLOR_SERVICIO = {"L": COLOR_LABORAL, "S": COLOR_SABADO, "D": COLOR_DOMINGO}
COLOR_GRILLA = "#DDE3E6"

# Desplazamiento de la etiqueta del pico, para que no se monte sobre otra curva.
DESPLAZAMIENTO_ETIQUETA = {"L": (5, 5), "S": (6, -11), "D": (6, -11)}
# Las curvas se cruzan cerca de los picos: la etiqueta va sobre un fondo opaco.
FONDO_ETIQUETA = {"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 1.0}

BINS_HISTOGRAMA = 45


# --------------------------------------------------------------------------
# Lectura y reconstrucción de corridas
# --------------------------------------------------------------------------


def a_segundos(marca: str) -> int:
    """Convierte HH:MM:SS a segundos. GTFS admite horas >= 24 (trasnoche)."""
    horas, minutos, segundos = (int(parte) for parte in marca.split(":"))
    return horas * SEGUNDOS_POR_HORA + minutos * SEGUNDOS_POR_MINUTO + segundos


def leer(nombre: str, **kwargs) -> pd.DataFrame:
    """Lee un archivo de 01-datos/, con mensaje claro si no está."""
    ruta = DIR_GTFS / nombre if nombre.endswith(".txt") else DIR_DATOS / nombre
    if not ruta.exists():
        raise FileNotFoundError(f"Falta {ruta}. Verifica que 01-datos/ esté completo.")
    return pd.read_csv(ruta, **kwargs)


def rutas_red() -> set[str]:
    """Recorridos operados por buses RED, descartando Metro y Metrotren."""
    routes = leer("routes.txt", dtype=str)
    es_red = (routes.agency_id == AGENCIA_RED) & (routes.route_type == TIPO_RUTA_BUS)
    return set(routes.loc[es_red, "route_id"])


def patrones(ids_ruta: set[str]) -> pd.DataFrame:
    """Patrones de viaje RED con su duración nominal y su distancia."""
    trips = leer("trips.txt", dtype=str)
    trips = trips[trips.route_id.isin(ids_ruta)][["trip_id", "service_id", "shape_id"]]

    tiempos = leer(
        "stop_times.txt",
        dtype=str,
        usecols=["trip_id", "arrival_time", "departure_time", "stop_sequence"],
    )
    tiempos = tiempos[tiempos.trip_id.isin(set(trips.trip_id))].copy()
    tiempos["orden"] = tiempos.stop_sequence.astype(int)
    tiempos = tiempos.sort_values(["trip_id", "orden"])

    por_patron = tiempos.groupby("trip_id")
    duracion = (
        por_patron.arrival_time.last().map(a_segundos)
        - por_patron.departure_time.first().map(a_segundos)
    ).rename("duracion_s")

    distancias = leer("shape_distances.csv")
    return trips.merge(duracion, on="trip_id").merge(distancias, on="shape_id")


def expandir_frecuencias(patrones_red: pd.DataFrame) -> pd.DataFrame:
    """Genera una corrida por cada salida t_n = start + n*headway, con t_n < end."""
    ventanas = leer("frequencies.txt", dtype=str)
    ventanas = ventanas[ventanas.trip_id.isin(set(patrones_red.trip_id))].copy()
    ventanas["inicio"] = ventanas.start_time.map(a_segundos)
    ventanas["fin"] = ventanas.end_time.map(a_segundos)
    ventanas["headway"] = ventanas.headway_secs.astype(int)

    salidas = [
        (trip_id, inicio + n * headway)
        for trip_id, inicio, fin, headway in ventanas[
            ["trip_id", "inicio", "fin", "headway"]
        ].itertuples(index=False)
        for n in range(((fin - inicio - 1) // headway) + 1 if fin > inicio else 0)
    ]

    corridas = pd.DataFrame(salidas, columns=["trip_id", "salida_s"]).merge(
        patrones_red, on="trip_id"
    )
    corridas["llegada_s"] = corridas.salida_s + corridas.duracion_s
    corridas["duracion_min"] = corridas.duracion_s / SEGUNDOS_POR_MINUTO
    corridas["energia_kwh"] = corridas.distance_km * CONSUMO_KWH_KM
    corridas["velocidad_kmh"] = corridas.distance_km / (
        corridas.duracion_s / SEGUNDOS_POR_HORA
    )
    return corridas


# --------------------------------------------------------------------------
# Concurrencia
# --------------------------------------------------------------------------


def _barrido_de_eventos(corridas: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Corridas activas tras cada evento, con el intervalo semiabierto [salida, llegada).

    En un empate la llegada se procesa antes que la salida, de modo que una
    corrida que termina justo cuando otra parte no se cuenta dos veces.
    """
    instantes = np.concatenate([corridas.salida_s.values, corridas.llegada_s.values])
    signos = np.concatenate(
        [np.ones(len(corridas), dtype=int), -np.ones(len(corridas), dtype=int)]
    )
    orden = np.lexsort((signos, instantes))
    return instantes[orden], np.cumsum(signos[orden])


def perfil_concurrencia(corridas: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Máximo de corridas activas dentro de cada minuto del día.

    Se resuelve al segundo y recién después se agrega por minuto, para que el
    máximo de la curva coincida exactamente con la cota inferior que reporta el
    texto y no quede desfasado por el redondeo de la malla.
    """
    instantes, activas = _barrido_de_eventos(corridas)
    minutos = (instantes // SEGUNDOS_POR_MINUTO).astype(int)
    total_minutos = int(minutos.max()) + 2

    # Valor al comienzo de cada minuto: la curva es constante entre eventos, así
    # que los minutos sin eventos heredan el último valor conocido.
    inicio_minuto = np.arange(total_minutos) * SEGUNDOS_POR_MINUTO
    indice_previo = np.searchsorted(instantes, inicio_minuto, side="right") - 1
    perfil = np.where(indice_previo >= 0, activas[indice_previo], 0)

    # Y además el máximo alcanzado dentro del minuto, por los eventos que caen en él.
    np.maximum.at(perfil, minutos, activas)

    horas = np.arange(total_minutos) / SEGUNDOS_POR_MINUTO
    return horas, perfil


def pico_simultaneo(corridas: pd.DataFrame) -> int:
    """Máximo de corridas simultáneas, resuelto al segundo sobre [salida, llegada)."""
    return int(_barrido_de_eventos(corridas)[1].max())


# --------------------------------------------------------------------------
# Figuras
# --------------------------------------------------------------------------


def _limpiar_ejes(eje) -> None:
    eje.grid(axis="y", color=COLOR_GRILLA, linewidth=0.6)
    eje.set_axisbelow(True)
    for lado in ("top", "right"):
        eje.spines[lado].set_visible(False)


def _miles(valor: float) -> str:
    """Formatea con punto de miles, como se usa en el informe."""
    return f"{valor:,.0f}".replace(",", ".")


def figura_concurrencia(corridas: pd.DataFrame, destino: Path) -> None:
    """Perfil horario de corridas simultáneas, una curva por tipo de día."""
    figura, eje = plt.subplots(figsize=(6.6, 2.9))

    for servicio in SERVICIOS:
        del_dia = corridas[corridas.service_id == servicio]
        horas, activas = perfil_concurrencia(del_dia)
        eje.plot(
            horas,
            activas,
            color=COLOR_SERVICIO[servicio],
            linewidth=1.4,
            label=NOMBRE_SERVICIO[servicio],
        )
        pico = int(activas.max())
        hora_pico = float(horas[int(activas.argmax())])
        eje.plot([hora_pico], [pico], marker="o", ms=4, color=COLOR_SERVICIO[servicio])
        eje.annotate(
            _miles(pico),
            xy=(hora_pico, pico),
            xytext=DESPLAZAMIENTO_ETIQUETA[servicio],
            textcoords="offset points",
            fontsize=8,
            color=COLOR_SERVICIO[servicio],
            bbox=FONDO_ETIQUETA,
        )

    eje.set_xlabel("Hora del día")
    eje.set_ylabel("Corridas simultáneas")
    eje.set_xlim(0, 26)
    eje.set_xticks(range(0, 27, 2))
    eje.set_ylim(bottom=0)
    _limpiar_ejes(eje)
    eje.legend(frameon=False, fontsize=8, loc="upper right")

    figura.tight_layout()
    figura.savefig(destino, bbox_inches="tight")
    plt.close(figura)


def _panel_histograma(eje, valores, etiqueta_x: str) -> None:
    eje.hist(
        valores, bins=BINS_HISTOGRAMA, color=COLOR_LABORAL, edgecolor="white", linewidth=0.3
    )
    mediana = float(np.median(valores))
    eje.axvline(
        mediana,
        color=COLOR_REFERENCIA,
        linewidth=1.1,
        linestyle="--",
        label=f"mediana = {mediana:.1f}".replace(".", ","),
    )
    eje.set_xlabel(etiqueta_x)
    _limpiar_ejes(eje)
    eje.legend(frameon=False, fontsize=7.5)


def figura_distribuciones(corridas: pd.DataFrame, destino: Path) -> None:
    """Distribuciones preliminares de las corridas del día laboral."""
    laboral = corridas[corridas.service_id == "L"]
    figura, ejes = plt.subplots(1, 3, figsize=(7.4, 2.4))

    _panel_histograma(ejes[0], laboral.distance_km, "Distancia (km)")
    _panel_histograma(ejes[1], laboral.duracion_min, "Duración (min)")
    _panel_histograma(ejes[2], laboral.velocidad_kmh, "Velocidad comercial (km/h)")

    ejes[0].set_ylabel("Corridas")
    for eje, titulo in zip(ejes, ("(a)", "(b)", "(c)")):
        eje.set_title(titulo, fontsize=8.5, loc="left", color="#44555C")

    figura.tight_layout()
    figura.savefig(destino, bbox_inches="tight")
    plt.close(figura)


# --------------------------------------------------------------------------
# Complejidad combinatoria
# --------------------------------------------------------------------------


def arcos_de_encadenamiento(corridas: pd.DataFrame) -> int:
    """Pares (i, j) que un mismo bus podría encadenar respetando el tiempo.

    Se cuenta j tal que su salida ocurre al menos CONEXION_MINIMA_MIN después de
    la llegada de i. Es una cota superior optimista del tamaño de la red: ignora
    la distancia entre el fin de i y el inicio de j, de modo que el número real
    de arcos operacionalmente válidos es menor, nunca mayor.
    """
    salidas = np.sort(corridas.salida_s.values)
    disponible_desde = corridas.llegada_s.values + CONEXION_MINIMA_MIN * SEGUNDOS_POR_MINUTO
    posteriores = len(salidas) - np.searchsorted(salidas, disponible_desde, side="left")
    return int(posteriores.sum())


# --------------------------------------------------------------------------
# Macros LaTeX
# --------------------------------------------------------------------------


def _es(valor: float, decimales: int = 0) -> str:
    """Formatea a la chilena: punto de miles y coma decimal."""
    marcador = ""
    return (
        f"{valor:,.{decimales}f}".replace(",", marcador).replace(".", ",").replace(marcador, ".")
    )


def _hora_hhmm(segundos: float) -> str:
    return "{:02d}:{:02d}".format(
        int(segundos // SEGUNDOS_POR_HORA),
        int((segundos % SEGUNDOS_POR_HORA) // SEGUNDOS_POR_MINUTO),
    )


def escribir_macros(corridas: pd.DataFrame, destino: Path) -> None:
    """Escribe las cifras del análisis de colas para que el texto no las repita a mano."""
    laboral = corridas[corridas.service_id == "L"]
    headways = leer("frequencies.txt", dtype=str)
    headways = headways[headways.trip_id.isin(set(laboral.trip_id))].headway_secs.astype(int)

    arcos = arcos_de_encadenamiento(laboral)
    macros = {
        "arcosEncadenamiento": _es(arcos / 1e6),
        "arcosMilesDeMillones": _es(arcos / 1e9, 2),
        "paresTotales": _es(len(laboral) * (len(laboral) - 1) / 1e9, 2),
        "conexionMinima": _es(CONEXION_MINIMA_MIN),
        "corridasCortas": _es((laboral.duracion_min < DURACION_CORTA_MIN).sum()),
        "corridasLargas": _es((laboral.duracion_min > DURACION_LARGA_MIN).sum()),
        "corridasBreves": _es((laboral.distance_km < DISTANCIA_CORTA_KM).sum()),
        "corridasExtensas": _es((laboral.distance_km > DISTANCIA_LARGA_KM).sum()),
        "corridasRapidas": _es((laboral.velocidad_kmh > VELOCIDAD_IMPLAUSIBLE_KMH).sum()),
        "corridasTrasnoche": _es(
            (laboral.llegada_s >= HORAS_POR_DIA * SEGUNDOS_POR_HORA).sum()
        ),
        "ultimaLlegada": _hora_hhmm(laboral.llegada_s.max()),
        "velocidadMedia": _es(laboral.velocidad_kmh.mean(), 2),
        "velocidadMediana": _es(laboral.velocidad_kmh.median(), 2),
        "velocidadMaxima": _es(laboral.velocidad_kmh.max(), 2),
        "distanciaMinima": _es(laboral.distance_km.min(), 2),
        "distanciaMaxima": _es(laboral.distance_km.max(), 2),
        "duracionMinima": _es(laboral.duracion_min.min(), 1),
        "duracionMaxima": _es(laboral.duracion_min.max(), 1),
        "energiaMaxCorrida": _es(laboral.energia_kwh.max(), 1),
        "energiaUtil": _es(ENERGIA_UTIL_KWH),
        "headwayMediano": _es(headways.median() / SEGUNDOS_POR_MINUTO),
        "headwayMinimo": _es(headways.min() / SEGUNDOS_POR_MINUTO, 1),
        "headwayMaximo": _es(headways.max() / SEGUNDOS_POR_MINUTO),
    }

    lineas = [
        "% Generado por 02-analisis-datos/figuras_informe.py -- NO editar a mano.",
        "% Regenerar con:  python3 02-analisis-datos/figuras_informe.py",
        "",
    ]
    lineas += [f"\\newcommand{{\\{nombre}}}{{{valor}}}" for nombre, valor in macros.items()]
    destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
# Verificación
# --------------------------------------------------------------------------


def verificar(ids_ruta: set[str], patrones_red: pd.DataFrame, corridas: pd.DataFrame) -> None:
    """Falla si el pipeline deja de reproducir alguna cifra publicada en el informe."""
    errores: list[str] = []

    def comparar(etiqueta: str, obtenido: int, esperado: int) -> None:
        marca = "ok" if obtenido == esperado else "DISCREPANCIA"
        print(f"  {etiqueta:<26} {obtenido:>7,}  (informe {esperado:>7,})  {marca}")
        if obtenido != esperado:
            errores.append(f"{etiqueta}: {obtenido} != {esperado}")

    print("Verificación contra las cifras del informe:")
    comparar("rutas RED", len(ids_ruta), CIFRAS_ESPERADAS["rutas_red"])
    comparar("patrones RED", len(patrones_red), CIFRAS_ESPERADAS["patrones_totales"])
    for servicio in SERVICIOS:
        del_dia = corridas[corridas.service_id == servicio]
        comparar(
            f"corridas {servicio}", len(del_dia), CIFRAS_ESPERADAS["corridas"][servicio]
        )
        comparar(
            f"pico simultaneo {servicio}",
            pico_simultaneo(del_dia),
            CIFRAS_ESPERADAS["pico"][servicio],
        )

    if errores:
        raise SystemExit(
            "Los datos ya no reproducen el informe:\n  - " + "\n  - ".join(errores)
        )


# --------------------------------------------------------------------------


def main() -> None:
    ids_ruta = rutas_red()
    patrones_red = patrones(ids_ruta)
    corridas = expandir_frecuencias(patrones_red)

    verificar(ids_ruta, patrones_red, corridas)

    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    figura_concurrencia(corridas, DIR_FIGURAS / "fig_concurrencia.pdf")
    figura_distribuciones(corridas, DIR_FIGURAS / "fig_distribuciones.pdf")
    escribir_macros(corridas, DIR_CAPITULOS / "metricas_datos.tex")

    print("\nGenerado:")
    for archivo in ("fig_concurrencia.pdf", "fig_distribuciones.pdf"):
        print(f"  {DIR_FIGURAS / archivo}")
    print(f"  {DIR_CAPITULOS / 'metricas_datos.tex'}")


if __name__ == "__main__":
    main()
