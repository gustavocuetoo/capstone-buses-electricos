#!/usr/bin/env python3
"""Métricas operativas, instancias y KPIs para la Entrega 1.

Responde a lo pedido en la reunión de coordinación:

  1. Tabla de instancias (chica -> grande) con su tamaño combinatorio, para
     decidir qué problema es realmente abordable.
  2. KPIs preliminares del problema, con su valor de referencia calculado
     sobre los datos entregados.
  3. Entendimiento de los datos: cuántos viajes hace un bus, cada cuánto
     recarga, qué campos faltan y cuáles son reconstruibles.
  4. Verificación de que los datos vengan bien (batería de chequeos).

Lee `01-datos/` (solo lectura) y escribe en `03-resultados/`.
Uso (desde la raíz del proyecto):  python3 02-codigo/entrega1_kpis.py
"""

from __future__ import annotations

import bisect
import math
import random
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

sys.path.insert(0, str(Path(__file__).resolve().parent))

import analisis_datos as base  # noqa: E402
import geografia as geo  # noqa: E402
import tablas  # noqa: E402

# --------------------------------------------------------------------------
# Supuestos explícitos (todos son candidatos a pregunta para el profesor)
# --------------------------------------------------------------------------

SEMILLA = 20260826
MUESTRA_PARES = 200_000

# Tiempo mínimo entre el fin de un viaje y el inicio del siguiente para el
# mismo bus, aun cuando terminen y empiecen en el mismo punto (recuperación).
CONEXION_MINIMA_MIN = 5

# Holgura máxima entre dos viajes para considerarlos una conexión "ajustada":
# por encima de esto el bus simplemente espera y el par no informa nada.
HOLGURA_AJUSTADA_MIN = 60

# Un traslado en vacío de hasta esta distancia se considera barato.
DEADHEAD_BARATO_KM = 3.0

# Tamaños de instancia, expresados como número de rutas muestreadas.
TAMANOS_INSTANCIA = (1, 10, 50, 200)

SEGUNDOS_POR_MINUTO = 60
MINUTOS_POR_HORA = 60
HORAS_POR_DIA = 24
KW_POR_MW = 1000
KWH_POR_GWH = 1_000_000
PERCENTIL_ALTO = 0.90

# Caja envolvente aproximada de la Región Metropolitana. Cualquier parada fuera
# de ella es un servicio que no corresponde a la red de buses urbanos.
CAJA_RM = (-33.90, -33.15, -71.05, -70.35)


# --------------------------------------------------------------------------
# Carga
# --------------------------------------------------------------------------


def cargar_todo() -> dict:
    """Deja en un solo diccionario todo lo que necesitan los cálculos."""
    parametros = base.cargar_parametros()
    viajes = base.cargar_viajes(base.SERVICIO_DIA_LABORAL)
    ids = frozenset(viajes)
    ventanas = base.cargar_ventanas(ids)
    frecuencias = base.cargar_frecuencias(ids)
    distancias = base.cargar_distancias_shape()

    coordenadas = geo.cargar_coordenadas_paradas(base.DIR_GTFS / "stops.txt")
    terminales = geo.cargar_terminales_de_viaje(base.DIR_GTFS / "stop_times.txt", ids)
    geo_viaje = geo.coordenadas_de_viaje(terminales, coordenadas)

    electroterminales = [
        (float(d["lat"]), float(d["lon"]))
        for d in base.leer_csv(base.DIR_DATOS / "charger_capacity.csv")
    ]

    return {
        "parametros": parametros,
        "viajes": viajes,
        "ventanas": ventanas,
        "frecuencias": frecuencias,
        "distancias": distancias,
        "geo_viaje": geo_viaje,
        "electroterminales": electroterminales,
        "precios": base.leer_csv(base.DIR_DATOS / "electricity_prices.csv"),
    }


def agrupar_por_ruta(viajes: dict) -> dict[str, dict]:
    """route_id -> {trip_id: viaje}. La ruta es la unidad natural de recorte."""
    por_ruta: dict[str, dict] = defaultdict(dict)
    for id_viaje, viaje in viajes.items():
        por_ruta[viaje["route_id"]][id_viaje] = viaje
    return dict(por_ruta)


def muestrear_rutas(rutas: list[str], cantidad: int) -> list[str]:
    """Muestra sistemática y reproducible: toma una ruta cada k, sin azar."""
    if cantidad >= len(rutas):
        return rutas
    paso = len(rutas) / cantidad
    return [rutas[int(i * paso)] for i in range(cantidad)]


# --------------------------------------------------------------------------
# Complejidad combinatoria
# --------------------------------------------------------------------------


def contar_arcos_temporales(corridas: tuple, conexion_s: int) -> int:
    """Pares (i, j) donde j puede seguir a i solo por compatibilidad horaria.

    Es la cota superior del número de variables de arco de una formulación
    connection-based: cada par factible es una variable binaria potencial.
    """
    inicios = sorted(c.inicio_s for c in corridas)
    return sum(
        len(inicios) - bisect.bisect_left(inicios, c.fin_s + conexion_s)
        for c in corridas
    )


def corridas_georreferenciadas(datos: dict) -> list[tuple]:
    """Corridas expandidas con las coordenadas de sus terminales.

    Se expande viaje por viaje para reutilizar exactamente la misma lógica de
    `analisis_datos.expandir_corridas` sin duplicarla.
    """
    registros = []
    for id_viaje, viaje in datos["viajes"].items():
        if id_viaje not in datos["geo_viaje"]:
            continue
        corridas = base.expandir_corridas(
            {id_viaje: viaje},
            datos["ventanas"],
            datos["frecuencias"],
            datos["distancias"],
        )
        origen, destino = datos["geo_viaje"][id_viaje]
        registros.extend(
            (c.inicio_s, c.fin_s, origen, destino) for c in corridas
        )
    return registros


def muestrear_conexiones(registros: list[tuple], conexion_s: int) -> dict:
    """Caracteriza los arcos del problema muestreando pares con semilla fija.

    Enumerar los ~10^9 pares del caso completo es inviable. Interesan dos cosas
    distintas y hay que medirlas por separado:

    - Sobre los pares *ajustados* (poca holgura entre viajes), cuántos sobreviven
      a la geografía. Es la poda real que introduce el deadhead.
    - Sobre todos los pares horarios, cuántos son *baratos* (deadhead corto).
      Ese porcentaje mide lo difícil que es encontrar un buen encadenamiento:
      la mayoría de las conexiones legales son pésimas.
    """
    azar = random.Random(SEMILLA)
    total = len(registros)
    resumen = {"pares_tiempo": 0, "ajustados": 0, "ajustados_geo": 0, "baratos": 0}
    deadheads: list[float] = []

    for _ in range(MUESTRA_PARES):
        origen = registros[azar.randrange(total)]
        siguiente = registros[azar.randrange(total)]
        if siguiente[0] < origen[1] + conexion_s:
            continue
        resumen["pares_tiempo"] += 1

        distancia = geo.distancia_calle_km(origen[3], siguiente[2])
        deadheads.append(distancia)
        if distancia <= DEADHEAD_BARATO_KM:
            resumen["baratos"] += 1

        holgura_min = (siguiente[0] - origen[1]) / SEGUNDOS_POR_MINUTO
        if holgura_min > HOLGURA_AJUSTADA_MIN:
            continue
        resumen["ajustados"] += 1
        if geo.tiempo_deadhead_min(distancia) + CONEXION_MINIMA_MIN <= holgura_min:
            resumen["ajustados_geo"] += 1

    resumen["fraccion_geo"] = (
        resumen["ajustados_geo"] / resumen["ajustados"] if resumen["ajustados"] else 0.0
    )
    resumen["fraccion_barata"] = (
        resumen["baratos"] / resumen["pares_tiempo"] if resumen["pares_tiempo"] else 0.0
    )
    resumen["deadheads"] = deadheads
    return resumen


# --------------------------------------------------------------------------
# Instancias
# --------------------------------------------------------------------------


def describir_instancia(nombre: str, rutas: list[str], datos: dict, por_ruta: dict) -> dict:
    """Calcula el tamaño operativo y combinatorio de un subconjunto de rutas."""
    viajes = {}
    for ruta in rutas:
        viajes.update(por_ruta[ruta])

    corridas = base.expandir_corridas(
        viajes, datos["ventanas"], datos["frecuencias"], datos["distancias"]
    )
    pico, _ = base.pico_concurrencia(corridas)
    conexion_s = CONEXION_MINIMA_MIN * SEGUNDOS_POR_MINUTO

    return {
        "nombre": nombre,
        "n_rutas": len(rutas),
        "n_viajes": len(viajes),
        "n_corridas": len(corridas),
        "km": sum(c.distancia_km for c in corridas),
        "horas_bus": sum(c.duracion_min for c in corridas) / MINUTOS_POR_HORA,
        "pico": pico,
        "arcos": contar_arcos_temporales(corridas, conexion_s),
    }


def construir_instancias(datos: dict, por_ruta: dict) -> list[dict]:
    """Familia de instancias de menor a mayor, todas del mismo día laboral."""
    rutas = sorted(por_ruta)
    instancias = [
        describir_instancia(
            f"I-{tamano:03d}", muestrear_rutas(rutas, tamano), datos, por_ruta
        )
        for tamano in TAMANOS_INSTANCIA
    ]
    instancias.append(describir_instancia("I-FULL", rutas, datos, por_ruta))
    return instancias


# --------------------------------------------------------------------------
# KPIs operativos
# --------------------------------------------------------------------------


def perfil_de_bus(km_totales: float, n_corridas: int, flota: int, parametros: dict) -> dict:
    """Qué le toca a un bus típico: viajes, kilómetros y recargas por día."""
    if flota <= 0:
        raise ValueError("El tamaño de flota debe ser positivo")

    consumo = parametros["battery_kwh"] / parametros["range_km"]
    util_kwh = parametros["battery_kwh"] * (parametros["max_soc"] - parametros["min_soc"])
    energia_bus = km_totales / flota * consumo

    return {
        "viajes_por_bus": n_corridas / flota,
        "km_por_bus": km_totales / flota,
        "energia_por_bus": energia_bus,
        "recargas_por_bus": energia_bus / util_kwh,
        "tiempo_recarga_min": util_kwh / parametros["charge_power_kw"] * MINUTOS_POR_HORA,
    }


def balance_de_carga(km_totales: float, cupos: int, parametros: dict) -> dict:
    """Contrasta la energía que el día exige con la que la red puede entregar."""
    consumo = parametros["battery_kwh"] / parametros["range_km"]
    energia_dia = km_totales * consumo
    capacidad_dia = cupos * parametros["charge_power_kw"] * HORAS_POR_DIA

    return {
        "energia_dia_gwh": energia_dia / KWH_POR_GWH,
        "potencia_instalada_mw": cupos * parametros["charge_power_kw"] / KW_POR_MW,
        "capacidad_dia_gwh": capacidad_dia / KWH_POR_GWH,
        "uso_capacidad_pct": 100 * energia_dia / capacidad_dia,
    }


def costos_de_referencia(
    km_totales: float, flota: int, energia_kwh: float, precios: list[dict]
) -> dict:
    """Cota inferior del costo diario y rango tarifario de la energía.

    Es cota inferior porque ignora deadhead, esperas y cargas fijas: sirve para
    dimensionar el orden de magnitud, no para comparar soluciones.
    """
    parametros = base.cargar_parametros()
    tarifas = [float(p["price_usd_kwh"]) for p in precios]
    costo_fijo = flota * parametros["vehicle_fixed_cost"]
    costo_km = km_totales * parametros["cost_per_km"]

    return {
        "precio_min": min(tarifas),
        "precio_max": max(tarifas),
        "brecha_tarifaria_pct": 100 * (max(tarifas) - min(tarifas)) / min(tarifas),
        "costo_fijo": costo_fijo,
        "costo_km": costo_km,
        "costo_energia_min": energia_kwh * min(tarifas),
        "costo_energia_max": energia_kwh * max(tarifas),
        "costo_total_min": costo_fijo + costo_km + energia_kwh * min(tarifas),
    }


# --------------------------------------------------------------------------
# Geografía de la operación
# --------------------------------------------------------------------------


def percentil(valores: list[float], fraccion: float) -> float:
    """Percentil por posición sobre la muestra ordenada."""
    if not valores:
        raise ValueError("No hay valores para calcular el percentil")
    ordenados = sorted(valores)
    indice = min(int(fraccion * len(ordenados)), len(ordenados) - 1)
    return ordenados[indice]


def distancias_a_electroterminal(datos: dict) -> dict:
    """Cuán lejos quedan los extremos de los viajes de un punto de recarga."""
    depots = datos["electroterminales"]
    salidas = [
        geo.distancia_al_electroterminal_mas_cercano(origen, depots)
        for origen, _ in datos["geo_viaje"].values()
    ]
    llegadas = [
        geo.distancia_al_electroterminal_mas_cercano(destino, depots)
        for _, destino in datos["geo_viaje"].values()
    ]
    return {
        "pullout_medio": mean(salidas),
        "pullout_p90": percentil(salidas, PERCENTIL_ALTO),
        "pullin_medio": mean(llegadas),
        "pullin_max": max(llegadas),
        "salidas": salidas,
    }


# --------------------------------------------------------------------------
# Verificación de los datos
# --------------------------------------------------------------------------


def notacion_cientifica(valor: float) -> str:
    """Formato $m \\times 10^{e}$: la única forma de que cinco órdenes de
    magnitud quepan en la misma columna sin volverse ilegibles."""
    if valor <= 0:
        return "0"
    exponente = int(math.floor(math.log10(valor)))
    mantisa = valor / 10 ** exponente
    return f"${base.decimal(mantisa, 1)}\\times 10^{{{exponente}}}$"


def _chequeo(clave: str, descripcion: str, valor: str, estado: str) -> dict:
    return {"clave": clave, "descripcion": descripcion, "valor": valor, "estado": estado}


def verificar_cobertura(datos: dict) -> list[dict]:
    """Chequeos de completitud: ¿tenemos un dato por cada viaje que hay que cubrir?"""
    viajes = datos["viajes"]
    con_shape = sum(1 for v in viajes.values() if v.get("shape_id") in datos["distancias"])
    con_ventana = sum(1 for v in viajes if v in datos["ventanas"])
    con_geo = len(datos["geo_viaje"])
    total = len(viajes)

    return [
        _chequeo(
            "C1", "Viajes con distancia conocida (shape\\_distances)",
            f"{100 * con_shape / total:.1f}\\%".replace(".", "{,}"),
            "ok" if con_shape == total else "alerta",
        ),
        _chequeo(
            "C2", "Viajes con ventana horaria válida (stop\\_times)",
            f"{100 * con_ventana / total:.1f}\\%".replace(".", "{,}"),
            "ok" if con_ventana == total else "alerta",
        ),
        _chequeo(
            "C3", "Terminales de origen/destino reconstruibles",
            f"{100 * con_geo / total:.1f}\\%".replace(".", "{,}"),
            "ok" if con_geo / total > 0.99 else "alerta",
        ),
    ]


def verificar_rangos(datos: dict) -> list[dict]:
    """Chequeos de plausibilidad: ¿los valores están en rangos operativos creíbles?"""
    duraciones = [
        (f - i) / SEGUNDOS_POR_MINUTO for i, f in datos["ventanas"].values()
    ]
    distancias = [
        datos["distancias"][v["shape_id"]]
        for v in datos["viajes"].values()
        if v.get("shape_id") in datos["distancias"]
    ]
    cortos = sum(1 for d in duraciones if d < 10)
    breves = sum(1 for d in distancias if d < 5)
    headways = [
        int(w["headway_secs"])
        for ventanas in datos["frecuencias"].values()
        for w in ventanas
    ]

    return [
        _chequeo(
            "C4", "Viajes de menos de 10 min (posible artefacto)",
            f"{base.miles(cortos)} de {base.miles(len(duraciones))}", "ok" if cortos == 0 else "alerta",
        ),
        _chequeo(
            "C5", "Viajes de menos de 5 km (posible artefacto)",
            f"{base.miles(breves)} de {base.miles(len(distancias))}", "ok" if breves == 0 else "alerta",
        ),
        _chequeo(
            "C6", "Frecuencias con headway positivo",
            f"{base.miles(sum(1 for h in headways if h > 0))} de {base.miles(len(headways))}",
            "ok" if all(h > 0 for h in headways) else "falla",
        ),
    ]


def verificar_consistencia(datos: dict) -> list[dict]:
    """Chequeos cruzados: ¿los archivos se contradicen entre sí?"""
    parametros = datos["parametros"]
    depots = base.leer_csv(base.DIR_DATOS / "depots.csv")
    cargadores = base.leer_csv(base.DIR_DATOS / "charger_capacity.csv")
    coinciden = all(
        d["capacity"] == c["capacity"]
        for d, c in zip(depots, cargadores, strict=True)
    )

    horas_l = sorted(
        (int(p["start_hour"]), int(p["end_hour"])) for p in datos["precios"]
    )
    tarifa_continua = horas_l[0][0] == 0 and horas_l[-1][1] == HORAS_POR_DIA and all(
        anterior[1] == siguiente[0] for anterior, siguiente in zip(horas_l, horas_l[1:])
    )

    consumo = parametros["battery_kwh"] / parametros["range_km"]
    desvio = 100 * (consumo - base.CONSUMO_REAL_KWH_KM) / base.CONSUMO_REAL_KWH_KM

    return [
        _chequeo(
            "C7", "depots.csv y charger\\_capacity.csv concuerdan",
            "idénticos" if coinciden else "discrepan", "ok" if coinciden else "falla",
        ),
        _chequeo(
            "C8", "Tarifa eléctrica cubre 24 h sin huecos ni solapes",
            f"{len(horas_l)} tramos", "ok" if tarifa_continua else "falla",
        ),
        _chequeo(
            "C9", "Consumo implícito vs. piloto real (1{,}006 kWh/km)",
            f"+{desvio:.0f}\\%", "alerta",
        ),
    ]


def verificar_filtros() -> list[dict]:
    """Los filtros preliminares que hubo que aplicar y lo que dejaron fuera."""
    no_bus, total_dia = base.contar_viajes_descartados(base.SERVICIO_DIA_LABORAL)
    coordenadas = geo.cargar_coordenadas_paradas(base.DIR_GTFS / "stops.txt")
    lat_min, lat_max, lon_min, lon_max = CAJA_RM
    fuera = [
        parada
        for parada, (lat, lon) in coordenadas.items()
        if not (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max)
    ]
    return [
        _chequeo(
            "C12", "Viajes no-bus (Metro y Metrotren) en el día de servicio",
            f"{base.miles(no_bus)} de {base.miles(total_dia)} descartados", "alerta",
        ),
        _chequeo(
            "C13", "Paradas fuera de la Región Metropolitana",
            f"{base.miles(len(fuera))} de {base.miles(len(coordenadas))}", "alerta" if fuera else "ok",
        ),
    ]


def verificar_diccionario() -> list[dict]:
    """El diccionario de datos promete campos que no existen en ningún archivo."""
    ausentes, total = base.campos_ausentes()
    return [
        _chequeo(
            "C11", "Campos del diccionario presentes en los archivos",
            f"{total - len(ausentes)} de {total}", "falla",
        )
    ]


# --------------------------------------------------------------------------
# Catálogo de KPIs
# --------------------------------------------------------------------------

# Cada KPI declara si ya es medible con los datos entregados o si solo se podrá
# evaluar una vez que exista un plan de operación. Distinguirlo evita prometer
# indicadores que hoy no tienen valor de referencia.
USO_INSTANCIA = {
    "I-001": "Depuración del modelo; óptimo exacto verificable a mano",
    "I-010": "Prototipo MILP exacto; referencia de calidad",
    "I-050": "Comparar exacto vs. heurística; calibración",
    "I-200": "Escala de trabajo; ajuste de parámetros",
    "I-FULL": "Caso real objetivo; solo heurística/descomposición",
}


def catalogo_kpis(metricas: dict) -> list[list[str]]:
    """Los KPIs con los que se evaluará cualquier plan de operación."""
    d = base.decimal
    m = base.miles
    return [
        ["K1", "Buses en operación", "Vehículos distintos usados en el día",
         m(metricas["pico"]) + " (cota inf.)", "Medible hoy"],
        ["K2", "Viajes por bus-día", "Corridas cubiertas / buses usados",
         d(metricas["perfil"]["viajes_por_bus"]), "Medible hoy"],
        ["K3", "Kilómetros por bus-día", "km recorridos / buses usados",
         d(metricas["perfil"]["km_por_bus"]), "Medible hoy"],
        ["K4", "Recargas por bus-día", "Energía consumida / energía útil de batería",
         d(metricas["perfil"]["recargas_por_bus"], 2), "Medible hoy"],
        ["K5", "Uso de la capacidad de carga", "Energía del día / energía máxima entregable",
         d(metricas["carga"]["uso_capacidad_pct"]) + "\\%", "Medible hoy"],
        ["K6", "Potencia instalada", "Cupos $\\times$ potencia por cargador",
         d(metricas["carga"]["potencia_instalada_mw"]) + " MW", "Medible hoy"],
        ["K7", "Costo total de operación", "Fijo + km + energía + espera (USD/día)",
         m(metricas["costos"]["costo_total_min"]) + " (cota inf.)", "Medible hoy"],
        ["K8", "Brecha tarifaria intradiaria", "(precio máx. $-$ mín.) / mín.",
         d(metricas["costos"]["brecha_tarifaria_pct"], 0) + "\\%", "Medible hoy"],
        ["K9", "Kilómetros en vacío", "km de deadhead / km totales",
         "---", "Requiere el plan"],
        ["K10", "Cobertura de viajes", "Corridas asignadas / corridas exigidas",
         "100\\% (restricción dura)", "Requiere el plan"],
        ["K11", "Holgura mínima de SoC", "Mínimo estado de carga alcanzado en el día",
         "---", "Requiere el plan"],
        ["K12", "Pico de carga simultánea", "Máx. buses cargando a la vez por terminal",
         "---", "Requiere el plan"],
    ]


# --------------------------------------------------------------------------
# Salida
# --------------------------------------------------------------------------


def filas_instancias(instancias: list[dict]) -> list[list[str]]:
    return [
        [
            i["nombre"],
            base.miles(i["n_rutas"]),
            base.miles(i["n_viajes"]),
            base.miles(i["n_corridas"]),
            base.miles(i["km"]),
            base.miles(i["horas_bus"]),
            base.miles(i["pico"]),
            notacion_cientifica(i["arcos"]),
            USO_INSTANCIA[i["nombre"]],
        ]
        for i in instancias
    ]


def armar_macros(metricas: dict) -> dict[str, str]:
    """Macros LaTeX. Los nombres no deben chocar con los de metricas.tex."""
    d, m = base.decimal, base.miles
    perfil, declarado = metricas["perfil"], metricas["perfil_declarado"]
    carga, costos, deadhead = metricas["carga"], metricas["costos"], metricas["deadhead"]

    return {
        "viajesPorBus": d(perfil["viajes_por_bus"]),
        "kmPorBus": d(perfil["km_por_bus"]),
        "energiaPorBus": m(perfil["energia_por_bus"]),
        "recargasPorBus": d(perfil["recargas_por_bus"], 2),
        "tiempoRecarga": m(perfil["tiempo_recarga_min"]),
        "viajesPorBusDecl": d(declarado["viajes_por_bus"]),
        "kmPorBusDecl": m(declarado["km_por_bus"]),
        "recargasPorBusDecl": d(declarado["recargas_por_bus"], 1),
        "potenciaInstalada": d(carga["potencia_instalada_mw"]),
        "capacidadCargaDia": d(carga["capacidad_dia_gwh"], 2),
        "usoCapacidadCarga": d(carga["uso_capacidad_pct"]),
        "precioMin": d(costos["precio_min"], 2),
        "precioMax": d(costos["precio_max"], 2),
        "brechaTarifaria": d(costos["brecha_tarifaria_pct"], 0),
        "costoFijoDia": m(costos["costo_fijo"]),
        "costoKmDia": m(costos["costo_km"]),
        "costoEnergiaMin": m(costos["costo_energia_min"]),
        "costoEnergiaMax": m(costos["costo_energia_max"]),
        "costoTotalMin": m(costos["costo_total_min"]),
        "desvioConsumo": d(metricas["desvio_consumo"], 0),
        "arcosFull": d(metricas["arcos_full"] / 1e6, 0),
        "arcosPorCorrida": m(metricas["arcos_full"] / metricas["n_corridas"]),
        "fraccionGeoFactible": d(100 * metricas["conexiones"]["fraccion_geo"], 0),
        "fraccionBarata": d(100 * metricas["conexiones"]["fraccion_barata"], 1),
        "holguraAjustada": m(HOLGURA_AJUSTADA_MIN),
        "deadheadBarato": m(DEADHEAD_BARATO_KM),
        "deadheadMedio": d(mean(deadhead)),
        "deadheadMediana": d(median(deadhead)),
        "deadheadPnoventa": d(percentil(deadhead, PERCENTIL_ALTO)),
        "pullOutMedio": d(metricas["depots"]["pullout_medio"]),
        "pullOutPnoventa": d(metricas["depots"]["pullout_p90"]),
        "pullInMax": d(metricas["depots"]["pullin_max"]),
        "pctGeoReconstruido": d(metricas["pct_geo"]),
        "numRutas": m(metricas["n_rutas"]),
        "conexionMinima": m(CONEXION_MINIMA_MIN),
        "velocidadComercial": d(metricas["velocidad_comercial"]),
        "velocidadDeadhead": m(geo.VELOCIDAD_DEADHEAD_KMH),
        "factorRodeo": d(geo.FACTOR_RODEO, 2),
        "chequeosTotal": str(metricas["n_chequeos"]),
        "chequeosOk": str(metricas["n_ok"]),
        "chequeosAlerta": str(metricas["n_alerta"]),
        "chequeosFalla": str(metricas["n_falla"]),
    }


def escribir_salidas(metricas: dict, instancias: list[dict], chequeos: list[dict]) -> None:
    salida = base.DIR_SALIDA
    tablas.escribir_macros(salida / "metricas_entrega1.tex", armar_macros(metricas))

    tablas.escribir_tabla(
        salida / "tabla_instancias.tex",
        "l r r r r r r r L{3.4cm}",
        ["Inst.", "Rutas", "Viajes", "Corridas", "km/día", "h-bus",
         "Cota flota", "Arcos", "Uso previsto"],
        filas_instancias(instancias),
    )

    tablas.escribir_tabla(
        salida / "tabla_kpis.tex",
        "l L{3.2cm} L{5.0cm} r l",
        ["", "KPI", "Definición", "Referencia", "Estado"],
        catalogo_kpis(metricas),
    )

    tablas.escribir_tabla(
        salida / "tabla_calidad.tex",
        "l L{8.2cm} r l",
        ["", "Verificación", "Resultado", "Estado"],
        [
            [c["clave"], c["descripcion"], c["valor"], tablas.SIMBOLO_ESTADO[c["estado"]]]
            for c in chequeos
        ],
    )

    escribir_tablas_deck(metricas, instancias, chequeos)

    base.graficar_histograma(
        metricas["conexiones"]["deadheads"],
        "distancia de traslado en vacío entre viajes encadenables (km)",
        salida / "fig_deadhead.pdf",
        median(metricas["conexiones"]["deadheads"]),
    )
    base.graficar_histograma(
        metricas["depots"]["salidas"],
        "distancia del inicio de viaje al electroterminal más cercano (km)",
        salida / "fig_pullout.pdf",
        median(metricas["depots"]["salidas"]),
    )


def escribir_tablas_deck(metricas: dict, instancias: list[dict], chequeos: list[dict]) -> None:
    """Variantes compactas de las mismas tablas, legibles proyectadas.

    Son recortes de columnas, no cifras distintas: la versión completa vive en
    el informe y esta en la presentación, pero ambas salen del mismo cálculo.
    """
    salida = base.DIR_SALIDA

    tablas.escribir_tabla(
        salida / "tabla_instancias_deck.tex",
        "l r r r r L{3.6cm}",
        ["Inst.", "Corridas", "km/día", "Cota flota", "Arcos", "Para qué sirve"],
        [
            [
                i["nombre"], base.miles(i["n_corridas"]), base.miles(i["km"]),
                base.miles(i["pico"]), notacion_cientifica(i["arcos"]),
                USO_INSTANCIA[i["nombre"]],
            ]
            for i in instancias
        ],
    )

    tablas.escribir_tabla(
        salida / "tabla_kpis_deck.tex",
        "l L{5.2cm} r l",
        ["", "KPI", "Referencia", "¿Medible hoy?"],
        [[fila[0], fila[1], fila[3], fila[4]] for fila in catalogo_kpis(metricas)],
    )

    problematicos = [c for c in chequeos if c["estado"] != "ok"]
    tablas.escribir_tabla(
        salida / "tabla_calidad_deck.tex",
        "l L{6.8cm} r l",
        ["", "Lo que no cuadra", "Resultado", ""],
        [
            [c["clave"], c["descripcion"], c["valor"], tablas.SIMBOLO_ESTADO[c["estado"]]]
            for c in problematicos
        ],
    )

# --------------------------------------------------------------------------
# Orquestación
# --------------------------------------------------------------------------


def main() -> int:
    base.DIR_SALIDA.mkdir(exist_ok=True)
    datos = cargar_todo()
    parametros = datos["parametros"]
    por_ruta = agrupar_por_ruta(datos["viajes"])

    print("Construyendo instancias...")
    instancias = construir_instancias(datos, por_ruta)
    completa = instancias[-1]

    print("Muestreando conexiones factibles...")
    registros = corridas_georreferenciadas(datos)
    conexiones = muestrear_conexiones(registros, CONEXION_MINIMA_MIN * SEGUNDOS_POR_MINUTO)

    cupos = sum(
        int(d["capacity"]) for d in base.leer_csv(base.DIR_DATOS / "charger_capacity.csv")
    )
    flota_declarada = int(parametros["fleet_size"])
    energia_dia = completa["km"] * parametros["battery_kwh"] / parametros["range_km"]

    metricas = {
        "pico": completa["pico"],
        "n_corridas": completa["n_corridas"],
        "n_rutas": completa["n_rutas"],
        "arcos_full": completa["arcos"],
        "conexiones": conexiones,
        "perfil": perfil_de_bus(
            completa["km"], completa["n_corridas"], completa["pico"], parametros
        ),
        "perfil_declarado": perfil_de_bus(
            completa["km"], completa["n_corridas"], flota_declarada, parametros
        ),
        "carga": balance_de_carga(completa["km"], cupos, parametros),
        "costos": costos_de_referencia(
            completa["km"], completa["pico"], energia_dia, datos["precios"]
        ),
        "deadhead": conexiones["deadheads"],
        "depots": distancias_a_electroterminal(datos),
        "pct_geo": 100 * len(datos["geo_viaje"]) / len(datos["viajes"]),
        "velocidad_comercial": completa["km"] / completa["horas_bus"],
        "desvio_consumo": 100
        * (parametros["battery_kwh"] / parametros["range_km"] - base.CONSUMO_REAL_KWH_KM)
        / base.CONSUMO_REAL_KWH_KM,
    }

    chequeos = (
        verificar_cobertura(datos)
        + verificar_rangos(datos)
        + verificar_consistencia(datos)
        + verificar_diccionario()
        + verificar_filtros()
    )
    metricas["n_chequeos"] = len(chequeos)
    metricas["n_ok"] = sum(1 for c in chequeos if c["estado"] == "ok")
    metricas["n_alerta"] = sum(1 for c in chequeos if c["estado"] == "alerta")
    metricas["n_falla"] = sum(1 for c in chequeos if c["estado"] == "falla")

    escribir_salidas(metricas, instancias, chequeos)

    print(f"\nRutas del servicio {base.SERVICIO_DIA_LABORAL}   : {metricas['n_rutas']:,}")
    print(f"Viajes por bus-día        : {metricas['perfil']['viajes_por_bus']:.1f}")
    print(f"km por bus-día            : {metricas['perfil']['km_por_bus']:.1f}")
    print(f"Recargas por bus-día      : {metricas['perfil']['recargas_por_bus']:.2f}")
    print(f"Arcos del caso completo   : {metricas['arcos_full']:,}")
    print(f"Conexiones ajustadas OK   : {100 * conexiones['fraccion_geo']:.0f}%")
    print(f"Arcos baratos (<= 3 km)   : {100 * conexiones['fraccion_barata']:.1f}%")
    print(f"Deadhead mediano          : {median(conexiones['deadheads']):.1f} km")
    print(f"Chequeos ok/alerta/falla  : "
          f"{metricas['n_ok']}/{metricas['n_alerta']}/{metricas['n_falla']}")
    print(f"\nSalida escrita en {base.DIR_SALIDA}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
