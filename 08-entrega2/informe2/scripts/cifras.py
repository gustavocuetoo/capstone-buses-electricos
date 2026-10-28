"""Genera cifras.tex (una macro por cifra) y tablas/barrido.tex desde los resultados auditados."""
import statistics
import sys
from pathlib import Path

import analisis
import fuentes
from formato import con_signo, delta, macro, numero

AQUI = Path(__file__).resolve().parents[1]
NUMERALES = {'1': 'Uno', '2': 'Dos', '3': 'Tres', '4': 'Cuatro', '5': 'Cinco'}
UMBRALES = {20: 'Veinte', 30: 'Treinta', 50: 'Cincuenta'}
PRESUPUESTOS = {15: 'Quince', 30: 'Treinta', 60: 'Sesenta', 120: 'CientoVeinte', 240: 'DosCuarenta'}
COMPONENTES = {'Flota': 'costo_buses_usd', 'Km': 'costo_km_usd',
               'Energia': 'costo_energia_usd', 'Sesiones': 'costo_sesiones_usd'}
HORA_TARIFA_NOCTURNA = 3
CORRIDAS_BARRIDO = 15


def kpis(resumen, jornadas):
    km_vacio = sum(float(j['km_vacio']) for j in jornadas)
    return dict(Buses=resumen['buses'], Costo=resumen['costo_total_usd'],
                CostoFlota=resumen['costo_buses_usd'], CostoKm=resumen['costo_km_usd'],
                CostoEnergia=resumen['costo_energia_usd'], CostoSesiones=resumen['costo_sesiones_usd'],
                Km=resumen['km'], KmVacio=km_vacio, PctVacio=100 * km_vacio / resumen['km'],
                Energia=resumen['carga_kwh'], Sesiones=resumen['sesiones'])


def macros_de_plan(m, sufijo, k, resumen):
    for clave in ('Buses', 'Costo', 'CostoFlota', 'CostoKm', 'CostoEnergia', 'CostoSesiones',
                  'Km', 'KmVacio', 'Energia', 'Sesiones'):
        m[clave + sufijo] = numero(k[clave])
    m['PctVacio' + sufijo] = numero(k['PctVacio'], 1)
    for nombre, campo in COMPONENTES.items():
        m[f'Pct{nombre}{sufijo}'] = numero(100 * resumen[campo] / resumen['costo_total_usd'], 1)
    for e, cap in resumen['capacidades'].items():
        letra = 'E' + NUMERALES[e[1:]]
        m[f'Plazas{letra}{sufijo}'] = numero(cap['ocupacion_maxima'])
        m[f'Conexiones{letra}{sufijo}'] = numero(cap['cargas_simultaneas_maximas'])
        m[f'Capacidad{letra}'] = numero(cap['capacidad_fisica'])


def calcular():
    m = {}
    escenario = fuentes.leer_json(fuentes.INSTANCIA / 'escenario.json')
    p = escenario['parametros']
    auditoria = fuentes.leer_json(fuentes.SALIDAS / 'auditoria_miope.json')
    if not auditoria.get('aprobado'):
        raise ValueError('La auditoría del miope no está aprobada (Tarea 4)')
    base = fuentes.resumen_verificado(auditoria['reporte'], 'auditoria_miope.json')
    modelo = fuentes.resumen_verificado(fuentes.leer_json(fuentes.REFINADO / '04_final/resumen.json'), 'refinado')
    jornadas_base = fuentes.leer_csv(fuentes.MIOPE / 'jornadas.csv')
    jornadas_modelo = fuentes.leer_csv(fuentes.REFINADO / '04_final/jornadas.csv')
    k_base, k_modelo = kpis(base, jornadas_base), kpis(modelo, jornadas_modelo)
    macros_de_plan(m, 'Base', k_base, base)
    macros_de_plan(m, 'Modelo', k_modelo, modelo)
    for clave in ('Buses', 'Costo', 'CostoFlota', 'CostoKm', 'CostoEnergia', 'CostoSesiones',
                  'KmVacio', 'Energia', 'Sesiones'):
        diferencia, pct = delta(k_base[clave], k_modelo[clave])
        m['Delta' + clave], m['DeltaPct' + clave] = con_signo(diferencia), con_signo(pct, 1)
    m['DeltaPpVacio'] = con_signo(k_modelo['PctVacio'] - k_base['PctVacio'], 1)
    m['PlazasTotales'] = numero(sum(escenario['capacidad_fisica'].values()))

    sin_recargas = fuentes.resumen_verificado(fuentes.leer_json(fuentes.SIN_RECARGAS / 'resumen.json'), 'sin recargas')
    m['BusesSinRecargas'], m['CostoSinRecargas'] = numero(sin_recargas['buses']), numero(sin_recargas['costo_total_usd'])
    for umbral, nombre in UMBRALES.items():
        carpeta = fuentes.MIOPE_UMBRAL[umbral]
        r = fuentes.resumen_verificado(fuentes.leer_json(carpeta / 'resumen.json')['caso_base'], f'umbral {umbral}')
        k = kpis(r, fuentes.leer_csv(carpeta / 'jornadas.csv'))
        m[f'BusesUmbral{nombre}'], m[f'CostoUmbral{nombre}'] = numero(k['Buses']), numero(k['Costo'])
        m[f'PctVacioUmbral{nombre}'] = numero(k['PctVacio'], 1)

    etapas = analisis.etapas(fuentes.leer_csv(fuentes.BUSQUEDA_600 / 'comparacion_etapas.csv'),
                             fuentes.leer_csv(fuentes.REFINADO / 'comparacion_etapas.csv'))
    por_nombre = {e['etapa']: e for e in etapas}
    if por_nombre['refinamiento']['buses'] != modelo['buses']:
        raise ValueError('La última etapa no coincide con el resumen del refinado')
    for etiqueta, nombre in (('Construccion', 'construccion'), ('Parejas', 'parejas'), ('Trios', 'trios')):
        etapa = por_nombre[nombre]
        m['Buses' + etiqueta], m['Costo' + etiqueta] = numero(etapa['buses']), numero(etapa['costo'])
        diferencia, pct = delta(base['buses'], etapa['buses'])
        m['DeltaBuses' + etiqueta], m['DeltaPctBuses' + etiqueta] = con_signo(diferencia), con_signo(pct, 1)
        m['DeltaPctCosto' + etiqueta] = con_signo(delta(base['costo_total_usd'], etapa['costo'])[1], 1)
    ahorro_total = base['buses'] - modelo['buses']
    ahorro_construccion = base['buses'] - por_nombre['construccion']['buses']
    m['AhorroBusesConstruccion'] = numero(ahorro_construccion)
    m['AhorroBusesBusqueda'] = numero(por_nombre['construccion']['buses'] - modelo['buses'])
    m['PctAhorroConstruccion'] = numero(100 * ahorro_construccion / ahorro_total, 1)

    corridas = fuentes.leer_csv(fuentes.INSTANCIA / 'corridas.csv')
    pico, segundo = analisis.simultaneidad_maxima([(int(c['inicio_s']), int(c['fin_s'])) for c in corridas])
    prototipo = fuentes.leer_json(fuentes.PROTOTIPO / 'resumen.json')
    fase1, fase2 = prototipo['fase1'], prototipo['fase2']
    if not fase1['optimo_demostrado']:
        raise ValueError('La Fase 1 del prototipo no tiene óptimo demostrado: no sirve como cota')
    m['CotaSimultaneidad'] = numero(pico)
    m['HoraCotaSimultaneidad'] = f'{(segundo // 3600) % 24:02d}:{(segundo % 3600) // 60:02d}'
    m['PisoFaseUno'], m['FlotaFaseUno'] = numero(fase1['objetivo_usd']), numero(fase2['flota'])
    m['BrechaCostoPiso'] = numero(100 * (modelo['costo_total_usd'] / fase1['objetivo_usd'] - 1), 1)
    m['BrechaBusesFaseUno'] = numero(100 * (modelo['buses'] / fase2['flota'] - 1), 1)
    m['BrechaBusesSimultaneidad'] = numero(100 * (modelo['buses'] / pico - 1), 1)
    m['NodosFaseUno'], m['ArcosFaseUno'] = numero(fase1['nodos']), numero(fase1['arcos'])
    m['BusesPrototipoSinMejora'] = numero(prototipo['fase3']['buses'])
    m['BusesExtraSinRecargas'] = numero(sin_recargas['buses'] - fase2['flota'])  # cadenas que piden un 2.º bus
    mejorado = fuentes.leer_json(fuentes.PROTOTIPO_MEJORADO / 'comparacion.json')
    m['BusesPrototipo'] = numero(fuentes.resumen_verificado(mejorado['despues'], 'prototipo mejorado')['buses'])

    km_servicio = [sum(float(j['km_servicio']) for j in js) for js in (jornadas_base, jornadas_modelo)]
    if abs(km_servicio[0] - km_servicio[1]) > 1e-6 * km_servicio[0]:
        raise ValueError('Los km de servicio del caso base y del modelo difieren: no cubren las mismas corridas')
    m['KmServicio'] = numero(km_servicio[1])

    punta = max(precio for _, _, precio in escenario['tarifas'])
    m['TarifaPunta'] = numero(punta, 2)
    for sufijo, carpeta, resumen in (('Base', fuentes.MIOPE, base), ('Modelo', fuentes.REFINADO / '04_final', modelo)):
        horas = analisis.energia_por_hora(fuentes.leer_csv(carpeta / 'recargas.csv'))
        if abs(sum(horas) - resumen['carga_kwh']) > 1e-6 * resumen['carga_kwh']:
            raise ValueError(f'La energía de recargas.csv ({sum(horas)}) no calza con el resumen del plan {sufijo}')
        en_punta = sum(e for h, e in enumerate(horas) if analisis.tarifa_en_hora(escenario['tarifas'], h) == punta)
        m['PctEnergiaPunta' + sufijo] = numero(100 * en_punta / sum(horas), 1)
        m['PrecioMedioKwh' + sufijo] = numero(resumen['costo_energia_usd'] / resumen['carga_kwh'], 3)

    tarifa = analisis.tarifa_en_hora(escenario['tarifas'], HORA_TARIFA_NOCTURNA)
    m['TarifaNocturna'] = numero(tarifa, 2)
    ajustado = {}
    for sufijo, jornadas, k in (('Base', jornadas_base, k_base), ('Modelo', jornadas_modelo, k_modelo)):
        noche = analisis.estimacion_nocturna(jornadas, p['bateria_kwh'], p['potencia_kw'],
                                             sum(escenario['conexiones'].values()))
        ajustado[sufijo] = k['Costo'] + noche['deficit_kwh'] * tarifa
        m['Deficit' + sufijo], m['CostoAjustado' + sufijo] = numero(noche['deficit_kwh']), numero(ajustado[sufijo])
        if sufijo == 'Modelo':
            m['BusesConDeficit'] = numero(noche['buses_con_deficit'])
            m['HorasCargaParalelo'] = numero(noche['horas_si_todas_las_conexiones'], 1)
            m['HorasBusMasVacio'] = numero(noche['horas_bus_mas_vacio'], 1)
            m['RondasCarga'] = numero(noche['rondas_de_carga'])
    diferencia, pct = delta(ajustado['Base'], ajustado['Modelo'])
    m['DeltaCostoAjustado'], m['DeltaPctCostoAjustado'] = con_signo(diferencia), con_signo(pct, 1)

    costo_minuto = float({r['parameter']: r['value'] for r in fuentes.leer_csv(fuentes.PARAMETROS)}['waiting_cost_per_min'])
    m['CostoEsperaMinuto'] = numero(costo_minuto, 2)
    con_espera = {}
    for sufijo, carpeta, k in (('Base', fuentes.MIOPE, k_base), ('Modelo', fuentes.REFINADO / '04_final', k_modelo)):
        minutos = analisis.minutos_espera_en_servicio(fuentes.leer_csv(carpeta / 'actividades.csv'))
        con_espera[sufijo] = k['Costo'] + minutos * costo_minuto
        m['MinutosEspera' + sufijo] = numero(minutos)
        m['CostoEspera' + sufijo] = numero(minutos * costo_minuto)
        m['CostoConEspera' + sufijo] = numero(con_espera[sufijo])
    m['DeltaPctCostoConEspera'] = con_signo(delta(con_espera['Base'], con_espera['Modelo'])[1], 1)

    red = fuentes.leer_csv(fuentes.INSTANCIA_RED / 'corridas.csv')
    rutas_muestra, rutas_red = len({c['route_id'] for c in corridas}), len({c['route_id'] for c in red})
    m['RutasMuestra'], m['CorridasMuestra'] = numero(rutas_muestra), numero(len(corridas))
    m['RutasRed'], m['CorridasRed'] = numero(rutas_red), numero(len(red))
    m['PctRutasMuestra'] = numero(100 * rutas_muestra / rutas_red, 1)
    m['PctCorridasMuestra'] = numero(100 * len(corridas) / len(red), 1)

    m['Bateria'], m['Reserva'] = numero(p['bateria_kwh']), numero(p['reserva_kwh'])
    m['Consumo'], m['Potencia'] = numero(p['consumo_kwh_km'], 1), numero(p['potencia_kw'])
    m['EnergiaBloque'] = numero(p['potencia_kw'] * p['bloque_s'] / 3600)
    m['Autonomia'] = numero((p['bateria_kwh'] - p['reserva_kwh']) / p['consumo_kwh_km'])
    m['CostoBus'], m['CostoKmUnit'] = numero(p['costo_bus']), numero(p['costo_km'], 1)
    m['CostoSesion'], m['VelocidadVacio'] = numero(p['costo_sesion']), numero(p['velocidad_vacio_kmh'])

    carpetas = (fuentes.BUSQUEDA_600, fuentes.REFINADO)
    segundos = sum(fuentes.leer_json(c / 'comparacion.json')['tiempo_total_s'] for c in carpetas)
    licencias = [fuentes.leer_json(c / 'licencia.json') for c in carpetas]
    m['MinutosRefinado'] = numero(segundos / 60, 1)
    m['ModelosLocales'] = numero(sum(x['modelos_totales'] for x in licencias))
    m['ModelosDescartados'] = numero(sum(x['modelos_descartados'] for x in licencias))

    m.update(macros_barrido())
    return m


def corridas_barrido():
    filas = []
    for carpeta in sorted(fuentes.BARRIDO.glob('B[0-9][0-9][0-9]_r[0-9]')):
        c = fuentes.leer_json(carpeta / 'comparacion.json')
        fuentes.resumen_verificado(c['final'], carpeta.name)
        filas.append(dict(corrida=carpeta.name, presupuesto=int(carpeta.name[1:4]),
                          buses=c['buses_evitados'], ahorro=c['ahorro_usd']))
    if len(filas) != CORRIDAS_BARRIDO:
        raise ValueError(f'Se esperaban {CORRIDAS_BARRIDO} corridas del barrido y hay {len(filas)}')
    return filas


def macros_barrido():
    filas, m = corridas_barrido(), {}
    for presupuesto, nombre in PRESUPUESTOS.items():
        grupo = [f for f in filas if f['presupuesto'] == presupuesto]
        m['MedianaAhorro' + nombre] = numero(statistics.median(f['ahorro'] for f in grupo))
        m['MedianaBusesEvitados' + nombre] = numero(statistics.median(f['buses'] for f in grupo))
    return m


def tabla_barrido():
    lineas = [f"{f['presupuesto']} & {f['corrida'][-1]} & {numero(f['buses'])} & {numero(f['ahorro'])} \\\\"
              for f in corridas_barrido()]
    return '\n'.join(lineas) + '\n'


def main():
    m = calcular()
    texto = '% Generado por scripts/cifras.py. No editar a mano.\n' + '\n'.join(
        macro(n, v) for n, v in sorted(m.items())) + '\n'
    (AQUI / 'cifras.tex').write_text(texto, encoding='utf-8')
    (AQUI / 'tablas').mkdir(exist_ok=True)
    (AQUI / 'tablas/barrido.tex').write_text(tabla_barrido(), encoding='utf-8')
    print(f'{len(m)} macros escritas en cifras.tex')
    return 0


if __name__ == '__main__':
    sys.exit(main())
