"""Pasa el plan del caso base miope por el auditor del método híbrido, sin modificarlo."""
import json
import math
import sys
from collections import defaultdict

import fuentes

sys.path.insert(0, str(fuentes.RAIZ))
from metodo_hibrido.verificar import verificar  # noqa: E402

CLAVES_COMPARADAS = ('buses', 'corridas', 'km', 'carga_kwh', 'sesiones', 'costo_total_usd')
VELOCIDAD_VACIO_KMH = 18


def planes_desde_csv(actividades, jornadas):
    por_bus = defaultdict(list)
    for fila in actividades:
        por_bus[fila['bus_id']].append(fila)
    planes = []
    for jornada in jornadas:
        filas = sorted(por_bus.get(jornada['bus_id'], []), key=lambda f: int(f['orden']))
        if not filas:
            raise ValueError(f'El bus {jornada["bus_id"]} no tiene actividades')
        acts = [dict(tipo=f['tipo'], origen=f['origen'], destino=f['destino'],
                     inicio_s=int(float(f['inicio_s'])), fin_s=int(float(f['fin_s'])),
                     distancia_km=float(f['distancia_km']), carga_kwh=float(f['carga_kwh']),
                     corrida_id=f['corrida_id']) for f in filas]
        planes.append(dict(bus_id=jornada['bus_id'], cadena_fase2=jornada['cadena_fase2'],
                           sector_id=jornada['sector_id'], terminal_inicial=jornada['terminal_inicial'],
                           terminal_final=jornada['terminal_final'],
                           corridas=[a['corrida_id'] for a in acts if a['tipo'] == 'servicio'],
                           actividades=acts))
    return planes


def corridas_de_instancia():
    return [dict(corrida_id=r['corrida_id'], inicio_s=int(r['inicio_s']), fin_s=int(r['fin_s']),
                 inicio_stop_id=r['inicio_stop_id'], fin_stop_id=r['fin_stop_id'],
                 distancia_servicio_km=float(r['distancia_servicio_km']), sector_id=r['sector_id'])
            for r in fuentes.leer_csv(fuentes.INSTANCIA / 'corridas.csv')]


def distancias_de_instancia():
    distancias = {}
    for r in fuentes.leer_csv(fuentes.INSTANCIA / 'distancias.csv'):
        km = float(r['distancia_km']) if r['distancia_km'] else None
        distancias[r['origen_id'], r['destino_id']] = (
            None if km is None else (km, math.ceil(km * 3600 / VELOCIDAD_VACIO_KMH)))
    return distancias


def main():
    escenario = fuentes.leer_json(fuentes.INSTANCIA / 'escenario.json')
    planes = planes_desde_csv(fuentes.leer_csv(fuentes.MIOPE / 'actividades.csv'),
                              fuentes.leer_csv(fuentes.MIOPE / 'jornadas.csv'))
    esperado = fuentes.resumen_verificado(
        fuentes.leer_json(fuentes.MIOPE / 'resumen.json')['caso_base'], 'resumen del miope')
    try:
        reporte, _, _ = verificar(planes, corridas_de_instancia(), distancias_de_instancia(),
                                  escenario['terminales_espera'], escenario['capacidad_fisica'],
                                  escenario['conexiones'], [tuple(t) for t in escenario['tarifas']],
                                  escenario['inicio_horizonte_s'], escenario['fin_horizonte_s'])
    except Exception as error:  # el auditor señala la primera regla que no se cumple
        resultado = dict(aprobado=False, error=f'{type(error).__name__}: {error}')
    else:
        diferencias = [dict(clave=k, auditor=reporte[k], miope=esperado[k]) for k in CLAVES_COMPARADAS
                       if not math.isclose(reporte[k], esperado[k], rel_tol=1e-9, abs_tol=1e-6)]
        resultado = dict(aprobado=reporte.get('verificado') is True and not diferencias,
                         reporte=reporte, diferencias=diferencias)
    fuentes.SALIDAS.mkdir(exist_ok=True)
    (fuentes.SALIDAS / 'auditoria_miope.json').write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in resultado.items() if k != 'reporte'}, ensure_ascii=False))
    return 0 if resultado['aprobado'] else 1


if __name__ == '__main__':
    sys.exit(main())
