"""Cálculos sobre los planes exportados que el informe necesita y no vienen en los resúmenes."""
import math
from collections import defaultdict

SEGUNDOS_DIA = 86_400
TOLERANCIA_USD = 1e-6
NOMBRES_ETAPAS = ('construccion', 'parejas', 'trios', 'refinamiento')


def simultaneidad_maxima(intervalos):
    eventos = defaultdict(int)
    for inicio, fin in intervalos:
        eventos[inicio] += 1
        eventos[fin] -= 1
    actual = pico = 0
    segundo = None
    for instante, cambio in sorted(eventos.items()):
        actual += cambio
        if actual > pico:
            pico, segundo = actual, instante
    return pico, segundo


def _etapa(filas, nombre):
    for f in filas:
        if f['etapa'] == nombre:
            return int(f['buses']), float(f['costo_total_usd'])
    raise ValueError(f'Falta la etapa {nombre}')


def etapas(filas_600, filas_refinado):
    construccion, parejas, trios = (_etapa(filas_600, n) for n in ('inicial', '01_pares', '01_trios'))
    inicio_refinado = _etapa(filas_refinado, 'inicial')
    if inicio_refinado[0] != trios[0] or abs(inicio_refinado[1] - trios[1]) > TOLERANCIA_USD:
        raise ValueError('Las corridas no encadenan: el refinamiento no parte del final de la búsqueda de 600 s')
    refinamiento = _etapa(filas_refinado, '01_trios')
    return [dict(etapa=n, buses=b, costo=c)
            for n, (b, c) in zip(NOMBRES_ETAPAS, (construccion, parejas, trios, refinamiento))]


def energia_por_hora(recargas):
    horas = [0.0] * 24
    for fila in recargas:
        hora = (int(float(fila['inicio_s'])) % SEGUNDOS_DIA) // 3600
        horas[hora] += float(fila['carga_kwh'])
    return horas


def tarifa_en_hora(tarifas, hora):
    for desde, hasta, precio in tarifas:
        if desde <= hora < hasta:
            return precio
    raise ValueError(f'Ninguna tarifa cubre la hora {hora}')


def estimacion_nocturna(jornadas, bateria_kwh, potencia_kw, conexiones_totales):
    deficits = [bateria_kwh - float(j['energia_final_kwh']) for j in jornadas]
    con_deficit = [d for d in deficits if d > 1e-9]
    total = sum(con_deficit)
    return dict(deficit_kwh=total, buses_con_deficit=len(con_deficit),
                horas_si_todas_las_conexiones=total / (potencia_kw * conexiones_totales),
                horas_bus_mas_vacio=max(con_deficit, default=0.0) / potencia_kw,
                rondas_de_carga=math.ceil(len(con_deficit) / conexiones_totales))


def minutos_espera_en_servicio(actividades):
    por_bus = defaultdict(list)
    for fila in actividades:
        por_bus[fila['bus_id']].append(fila)
    segundos = 0
    for filas in por_bus.values():
        servicios = [f for f in filas if f['tipo'] == 'servicio']
        if not servicios:
            continue
        primero = min(int(float(f['inicio_s'])) for f in servicios)
        ultimo = max(int(float(f['fin_s'])) for f in servicios)
        for f in filas:
            if f['tipo'] == 'espera':
                desde = max(int(float(f['inicio_s'])), primero)
                hasta = min(int(float(f['fin_s'])), ultimo)
                segundos += max(0, hasta - desde)
    return segundos / 60
