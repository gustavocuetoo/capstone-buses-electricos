#!/usr/bin/env python3
"""Análisis descriptivo y verificación de consistencia de los datos del capstone.

Lee `01-datos/` (solo lectura) y produce en `03-resultados/`:
  - metricas.tex          macros LaTeX con todas las cifras, para que el
                          documento no tenga ningún número escrito a mano
  - fig_duracion.pdf      histograma de duración de viaje
  - fig_distancia.pdf     histograma de distancia de viaje
  - fig_concurrencia.pdf  perfil horario de viajes simultáneos

Uso (desde la raiz del proyecto):  python3 02-codigo/analisis_datos.py
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# --------------------------------------------------------------------------
# Configuración
# --------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parent.parent
DIR_DATOS = RAIZ / "01-datos"
DIR_GTFS = DIR_DATOS / "gtfs"
DIR_SALIDA = RAIZ / "03-resultados"

SERVICIO_DIA_LABORAL = "L"

# El GTFS de la Red incluye Metro (route_type 1) y Metrotren (route_type 0)
# además de los buses (route_type 3). Programar esos servicios con la flota de
# buses eléctricos no tiene sentido, así que se filtran explícitamente.
TIPO_RUTA_BUS = "3"
SEGUNDOS_POR_MINUTO = 60
SEGUNDOS_POR_HORA = 3600
MINUTOS_POR_HORA = 60
HORAS_POR_DIA = 24
KWH_POR_GWH = 1_000_000

# Consumo medido en el piloto Metbus-Enel-BYD (Galarza 2020, reporte ZEBRA/IEA).
CONSUMO_REAL_KWH_KM = 1.006

# Flota real de RED en 2018 según el mismo reporte, usada como validación cruzada.
FLOTA_RED_REAL_2018 = 6756

BINS_HISTOGRAMA = 40
COLOR_TINTA = "#003E5C"
COLOR_AMBAR = "#B06210"
COLOR_ROJO = "#9E2620"
COLOR_SUAVE = "#CDD6DB"
FONDO_ETIQUETA = {"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 1.5}
TAMANO_FIGURA = (7.0, 3.2)


# --------------------------------------------------------------------------
# Lectura de archivos
# --------------------------------------------------------------------------


def leer_csv(ruta: Path) -> list[dict[str, str]]:
    """Lee un CSV delimitado por comas. Falla con mensaje claro si no existe."""
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró {ruta}. Verifica que 01-datos/ esté completo."
        )
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        return list(csv.DictReader(archivo))


def segundos_desde_medianoche(marca: str) -> int:
    """Convierte HH:MM:SS a segundos. GTFS admite horas >= 24 para trasnoche."""
    partes = marca.split(":")
    if len(partes) != 3:
        raise ValueError(f"Marca de tiempo GTFS inválida: {marca!r}")
    horas, minutos, segundos = (int(p) for p in partes)
    return horas * SEGUNDOS_POR_HORA + minutos * SEGUNDOS_POR_MINUTO + segundos


def cargar_parametros() -> dict[str, float]:
    """parameters.csv viene como pares parameter,value en vez de columnas."""
    filas = leer_csv(DIR_DATOS / "parameters.csv")
    return {fila["parameter"]: float(fila["value"]) for fila in filas}


def cargar_rutas() -> dict[str, dict[str, str]]:
    """route_id -> fila de routes.txt."""
    return {f["route_id"]: f for f in leer_csv(DIR_GTFS / "routes.txt")}


def cargar_viajes(servicio: str) -> dict[str, dict[str, str]]:
    """Viajes de bus del día de servicio pedido.

    Filtra dos veces: por día de operación y por modo. Sin el segundo filtro se
    cuelan las líneas de Metro y el Metrotren Rancagua, que inflan el tamaño del
    problema y contaminan toda la estadística descriptiva.
    """
    rutas = cargar_rutas()
    filas = leer_csv(DIR_GTFS / "trips.txt")
    del_dia = [f for f in filas if f["service_id"] == servicio]
    viajes = {
        f["trip_id"]: f
        for f in del_dia
        if rutas.get(f["route_id"], {}).get("route_type") == TIPO_RUTA_BUS
    }
    if not viajes:
        raise ValueError(f"Ningún viaje de bus con service_id={servicio!r} en trips.txt")
    return viajes


def contar_viajes_descartados(servicio: str) -> tuple[int, int]:
    """(viajes no-bus descartados, total de viajes del día) para documentar el filtro."""
    rutas = cargar_rutas()
    del_dia = [
        f for f in leer_csv(DIR_GTFS / "trips.txt") if f["service_id"] == servicio
    ]
    no_bus = sum(
        1
        for f in del_dia
        if rutas.get(f["route_id"], {}).get("route_type") != TIPO_RUTA_BUS
    )
    return no_bus, len(del_dia)


def cargar_ventanas(ids_viaje: frozenset[str]) -> dict[str, tuple[int, int]]:
    """Primera salida y última llegada de cada viaje, desde stop_times.txt."""
    inicio: dict[str, int] = {}
    fin: dict[str, int] = {}
    ruta = DIR_GTFS / "stop_times.txt"
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró {ruta}")
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        for fila in csv.DictReader(archivo):
            id_viaje = fila["trip_id"]
            if id_viaje not in ids_viaje:
                continue
            for campo in ("departure_time", "arrival_time"):
                marca = (fila.get(campo) or "").strip()
                if not marca:
                    continue
                instante = segundos_desde_medianoche(marca)
                if id_viaje not in inicio or instante < inicio[id_viaje]:
                    inicio[id_viaje] = instante
                if id_viaje not in fin or instante > fin[id_viaje]:
                    fin[id_viaje] = instante
    return {v: (inicio[v], fin[v]) for v in inicio if fin[v] > inicio[v]}


def cargar_frecuencias(ids_viaje: frozenset[str]) -> dict[str, list[dict[str, str]]]:
    ventanas: dict[str, list[dict[str, str]]] = {}
    for fila in leer_csv(DIR_GTFS / "frequencies.txt"):
        id_viaje = fila["trip_id"]
        if id_viaje in ids_viaje:
            ventanas.setdefault(id_viaje, []).append(fila)
    return ventanas


def cargar_distancias_shape() -> dict[str, float]:
    filas = leer_csv(DIR_DATOS / "shape_distances.csv")
    return {f["shape_id"]: float(f["distance_km"]) for f in filas}


# --------------------------------------------------------------------------
# Expansión de corridas
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Corrida:
    """Una ejecución concreta de un viaje, ya expandida desde frequencies.txt."""

    inicio_s: int
    fin_s: int
    distancia_km: float

    @property
    def duracion_min(self) -> float:
        return (self.fin_s - self.inicio_s) / SEGUNDOS_POR_MINUTO


def expandir_corridas(
    viajes: dict[str, dict[str, str]],
    ventanas: dict[str, tuple[int, int]],
    frecuencias: dict[str, list[dict[str, str]]],
    distancias: dict[str, float],
) -> tuple[Corrida, ...]:
    """Convierte plantillas de viaje en corridas reales.

    Un viaje listado en frequencies.txt no es una corrida: es un patrón que se
    repite cada `headway_secs` dentro de su ventana. Ignorarlo subestima el
    tamaño real del problema por un factor cercano a ocho.
    """
    corridas: list[Corrida] = []
    for id_viaje, viaje in viajes.items():
        if id_viaje not in ventanas:
            continue
        inicio_base, fin_base = ventanas[id_viaje]
        duracion = fin_base - inicio_base
        distancia = distancias.get(viaje.get("shape_id", ""), 0.0)

        if id_viaje not in frecuencias:
            corridas.append(Corrida(inicio_base, fin_base, distancia))
            continue

        for ventana in frecuencias[id_viaje]:
            desde = segundos_desde_medianoche(ventana["start_time"])
            hasta = segundos_desde_medianoche(ventana["end_time"])
            intervalo = int(ventana["headway_secs"])
            if intervalo <= 0:
                raise ValueError(f"headway_secs inválido en el viaje {id_viaje}")
            salida = desde
            while salida < hasta:
                corridas.append(Corrida(salida, salida + duracion, distancia))
                salida += intervalo
    return tuple(corridas)


def pico_concurrencia(corridas: tuple[Corrida, ...]) -> tuple[int, int]:
    """Máximo de viajes simultáneos y el instante en que ocurre.

    Es la cota inferior clásica de flota para un VSP: ningún plan puede usar
    menos vehículos que viajes solapados haya en el peor instante.
    """
    eventos = sorted(
        [(c.inicio_s, 1) for c in corridas] + [(c.fin_s, -1) for c in corridas]
    )
    activos = pico = instante_pico = 0
    for instante, delta in eventos:
        activos += delta
        if activos > pico:
            pico, instante_pico = activos, instante
    return pico, instante_pico


def perfil_por_hora(corridas: tuple[Corrida, ...]) -> tuple[float, ...]:
    """Cantidad de viajes activos a la mitad de cada hora del día."""
    activos_por_hora = []
    for hora in range(HORAS_POR_DIA):
        centro = hora * SEGUNDOS_POR_HORA + SEGUNDOS_POR_HORA // 2
        activos_por_hora.append(
            sum(1 for c in corridas if c.inicio_s <= centro < c.fin_s)
        )
    return tuple(float(v) for v in activos_por_hora)


# --------------------------------------------------------------------------
# Verificación de consistencia
# --------------------------------------------------------------------------


def campos_ausentes() -> tuple[tuple[str, ...], int]:
    """Campos documentados en el diccionario que no existen en ningún archivo."""
    documentados = [
        fila["parametro"].strip()
        for fila in leer_csv(DIR_DATOS / "parametros_descripcion.csv")
    ]

    presentes: set[str] = set()
    fuentes = list(DIR_DATOS.glob("*.csv")) + list(DIR_GTFS.glob("*.txt"))
    for ruta in fuentes:
        if "descripcion" in ruta.name:
            continue
        with ruta.open(encoding="utf-8-sig", newline="") as archivo:
            cabecera = archivo.readline().strip().split(",")
        presentes.update(c.strip() for c in cabecera)

    # parameters.csv guarda los nombres como filas, no como columnas
    presentes.update(cargar_parametros().keys())

    ausentes = tuple(c for c in documentados if c not in presentes)
    return ausentes, len(documentados)


# --------------------------------------------------------------------------
# Figuras
# --------------------------------------------------------------------------


def _estilo_ejes(ejes) -> None:
    for lado in ("top", "right"):
        ejes.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ejes.spines[lado].set_color(COLOR_SUAVE)
    ejes.tick_params(colors="#555555", labelsize=8)
    ejes.grid(axis="y", color=COLOR_SUAVE, linewidth=0.6, alpha=0.7)
    ejes.set_axisbelow(True)


def graficar_histograma(
    valores: list[float], etiqueta_x: str, destino: Path, mediana: float
) -> None:
    figura, ejes = plt.subplots(figsize=TAMANO_FIGURA)
    ejes.hist(valores, bins=BINS_HISTOGRAMA, color=COLOR_TINTA, alpha=0.85)
    ejes.axvline(mediana, color=COLOR_AMBAR, linewidth=1.6, linestyle="--")
    ejes.annotate(
        f"mediana {mediana:.1f}",
        xy=(mediana, ejes.get_ylim()[1] * 0.88),
        xytext=(6, 0),
        textcoords="offset points",
        color=COLOR_AMBAR,
        fontsize=8,
        fontweight="bold",
        bbox=FONDO_ETIQUETA,
    )
    ejes.set_xlabel(etiqueta_x, fontsize=9, color="#333333")
    ejes.set_ylabel("viajes", fontsize=9, color="#333333")
    _estilo_ejes(ejes)
    figura.tight_layout()
    figura.savefig(destino, format="pdf")
    plt.close(figura)


def graficar_concurrencia(
    perfil: tuple[float, ...], flota: int, cupos: int, destino: Path
) -> None:
    figura, ejes = plt.subplots(figsize=(7.0, 3.6))
    horas = list(range(HORAS_POR_DIA))
    ejes.fill_between(horas, perfil, color=COLOR_TINTA, alpha=0.85, step="mid")
    ejes.axhline(flota, color=COLOR_AMBAR, linewidth=1.6)
    ejes.annotate(
        f"flota declarada: {flota:,}".replace(",", "."),
        xy=(0.4, flota),
        xytext=(0, 7),
        textcoords="offset points",
        color=COLOR_AMBAR,
        fontsize=8,
        fontweight="bold",
        bbox=FONDO_ETIQUETA,
    )
    ejes.axhline(cupos, color=COLOR_ROJO, linewidth=1.4, linestyle=":")
    ejes.annotate(
        f"cupos en electroterminales: {cupos}",
        xy=(0.4, cupos),
        xytext=(0, -13),
        textcoords="offset points",
        color=COLOR_ROJO,
        fontsize=8,
        fontweight="bold",
        bbox=FONDO_ETIQUETA,
    )
    ejes.set_xlabel("hora del día", fontsize=9, color="#333333")
    ejes.set_ylabel("viajes simultáneos", fontsize=9, color="#333333")
    ejes.set_xticks(range(0, HORAS_POR_DIA, 2))
    ejes.set_xlim(0, HORAS_POR_DIA - 1)
    _estilo_ejes(ejes)
    figura.tight_layout()
    figura.savefig(destino, format="pdf")
    plt.close(figura)


# --------------------------------------------------------------------------
# Salida de macros
# --------------------------------------------------------------------------


def miles(valor: float) -> str:
    """Formato chileno: separador de miles con punto."""
    return f"{round(valor):,}".replace(",", ".")


def decimal(valor: float, cifras: int = 1) -> str:
    """Formato chileno: coma decimal, protegida para LaTeX."""
    return f"{valor:.{cifras}f}".replace(".", "{,}")


def escribir_macros(macros: dict[str, str], destino: Path) -> None:
    lineas = [
        "% Generado por analisis_datos.py -- NO editar a mano.",
        "% Volver a generar con:  python3 analisis_datos.py",
        "",
    ]
    lineas += [
        f"\\newcommand{{\\{nombre}}}{{{valor}}}" for nombre, valor in macros.items()
    ]
    destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def construir_macros(contexto: dict) -> dict[str, str]:
    """Arma el diccionario de macros a partir de las métricas ya calculadas."""
    c = contexto
    return {
        "servicioDia": SERVICIO_DIA_LABORAL,
        "registrosViaje": miles(c["n_viajes"]),
        "viajesDelDia": miles(c["n_viajes_dia"]),
        "viajesNoBus": miles(c["n_no_bus"]),
        "pctNoBus": decimal(100 * c["n_no_bus"] / c["n_viajes_dia"]),
        "corridasReales": miles(c["n_corridas"]),
        "factorFrecuencia": decimal(c["n_corridas"] / c["n_viajes"]),
        "pctFrecuencia": decimal(100 * c["n_con_frecuencia"] / c["n_viajes"]),
        "duracionMedia": decimal(mean(c["duraciones"])),
        "duracionMediana": decimal(median(c["duraciones"])),
        "duracionMin": miles(min(c["duraciones"])),
        "duracionMax": miles(max(c["duraciones"])),
        "distanciaMedia": decimal(mean(c["distancias"])),
        "distanciaMediana": decimal(median(c["distancias"])),
        "distanciaMin": decimal(min(c["distancias"])),
        "distanciaMax": decimal(max(c["distancias"])),
        "kmTotales": miles(c["km_totales"]),
        "horasBus": miles(c["horas_bus"]),
        "consumoImplicito": decimal(c["consumo_implicito"], 2),
        "consumoReal": decimal(CONSUMO_REAL_KWH_KM, 3),
        "energiaImplicita": decimal(c["km_totales"] * c["consumo_implicito"] / KWH_POR_GWH, 2),
        "energiaReal": decimal(c["km_totales"] * CONSUMO_REAL_KWH_KM / KWH_POR_GWH, 2),
        "autonomiaUtil": miles(c["autonomia_util"]),
        "picoSimultaneo": miles(c["pico"]),
        "horaPico": c["hora_pico"],
        "flotaDeclarada": miles(c["flota"]),
        "cuposTotales": miles(c["cupos"]),
        "numElectroterminales": str(c["n_depots"]),
        "ratioFlota": decimal(c["pico"] / c["flota"]),
        "ratioCupos": decimal(c["pico"] / c["cupos"]),
        "flotaRealRED": miles(FLOTA_RED_REAL_2018),
        "desvioValidacion": decimal(
            abs(c["pico"] - FLOTA_RED_REAL_2018) / FLOTA_RED_REAL_2018 * 100
        ),
        "camposDocumentados": str(c["total_campos"]),
        "camposAusentes": str(len(c["ausentes"])),
        "listaCamposAusentes": ", ".join(
            "\\texttt{" + campo.replace("_", "\\_") + "}" for campo in c["ausentes"]
        ),
    }


# --------------------------------------------------------------------------
# Orquestación
# --------------------------------------------------------------------------


def main() -> int:
    DIR_SALIDA.mkdir(exist_ok=True)

    parametros = cargar_parametros()
    viajes = cargar_viajes(SERVICIO_DIA_LABORAL)
    ids = frozenset(viajes)
    ventanas = cargar_ventanas(ids)
    frecuencias = cargar_frecuencias(ids)
    distancias = cargar_distancias_shape()
    corridas = expandir_corridas(viajes, ventanas, frecuencias, distancias)

    if not corridas:
        print("ERROR: no se pudo expandir ninguna corrida.", file=sys.stderr)
        return 1

    duraciones = [(f - i) / SEGUNDOS_POR_MINUTO for i, f in ventanas.values()]
    distancias_viaje = [
        distancias[v["shape_id"]]
        for v in viajes.values()
        if v.get("shape_id") in distancias
    ]
    if not duraciones or not distancias_viaje:
        print("ERROR: faltan duraciones o distancias para el servicio.", file=sys.stderr)
        return 1

    pico, instante_pico = pico_concurrencia(corridas)
    depots = leer_csv(DIR_DATOS / "depots.csv")
    ausentes, total_campos = campos_ausentes()

    n_no_bus, n_viajes_dia = contar_viajes_descartados(SERVICIO_DIA_LABORAL)

    contexto = {
        "n_viajes": len(viajes),
        "n_no_bus": n_no_bus,
        "n_viajes_dia": n_viajes_dia,
        "n_corridas": len(corridas),
        "n_con_frecuencia": len(frecuencias),
        "duraciones": duraciones,
        "distancias": distancias_viaje,
        "km_totales": sum(c.distancia_km for c in corridas),
        "horas_bus": sum(c.duracion_min for c in corridas) / MINUTOS_POR_HORA,
        "consumo_implicito": parametros["battery_kwh"] / parametros["range_km"],
        "autonomia_util": parametros["range_km"]
        * (parametros["max_soc"] - parametros["min_soc"]),
        "pico": pico,
        "hora_pico": f"{instante_pico // SEGUNDOS_POR_HORA:02d}:"
        f"{(instante_pico % SEGUNDOS_POR_HORA) // SEGUNDOS_POR_MINUTO:02d}",
        "flota": int(parametros["fleet_size"]),
        "cupos": sum(int(d["capacity"]) for d in depots),
        "n_depots": len(depots),
        "ausentes": ausentes,
        "total_campos": total_campos,
    }

    graficar_histograma(
        duraciones, "duración del viaje (min)",
        DIR_SALIDA / "fig_duracion.pdf", median(duraciones),
    )
    graficar_histograma(
        distancias_viaje, "distancia del viaje (km)",
        DIR_SALIDA / "fig_distancia.pdf", median(distancias_viaje),
    )
    graficar_concurrencia(
        perfil_por_hora(corridas), contexto["flota"], contexto["cupos"],
        DIR_SALIDA / "fig_concurrencia.pdf",
    )

    escribir_macros(construir_macros(contexto), DIR_SALIDA / "metricas.tex")

    print(f"Servicio analizado           : {SERVICIO_DIA_LABORAL}")
    print(f"Viajes del dia L (todo modo) : {n_viajes_dia:,}")
    print(f"  descartados por no ser bus : {n_no_bus:,}")
    print(f"Viajes de bus analizados     : {contexto['n_viajes']:,}")
    print(f"Corridas reales expandidas   : {contexto['n_corridas']:,}")
    print(f"Pico simultáneo              : {pico:,} a las {contexto['hora_pico']}")
    print(f"Flota declarada              : {contexto['flota']:,}"
          f"  -> faltan {pico - contexto['flota']:,}")
    print(f"Cupos en electroterminales   : {contexto['cupos']:,}")
    print(f"Campos documentados ausentes : {len(ausentes)} de {total_campos}")
    print(f"\nSalida escrita en {DIR_SALIDA}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
