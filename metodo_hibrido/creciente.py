"""Mezcla creciente: parte con pares y agranda el grupo solo cuando el tamaño actual deja de mejorar.

Es la búsqueda de vecindario variable (Mladenović y Hansen, 1997): si un tamaño encuentra una mejora,
se vuelve al más chico; si no, se pasa al siguiente. Termina cuando el último tamaño no mejora o se
acaba el presupuesto, que es uno solo para toda la mezcla.
"""
import time
from metodo_hibrido.grupos import buscar_grupos
from metodo_hibrido.intercambios import buscar

TAMANOS = (2, 3, 4, 5, 8)


def buscar_creciente(plans, lookup, d, starts, physical, plugs, tariffs, t0, horizon, budget=120., local_limit=2.,
                     neighbors=8, per_pair=3, max_rounds=3, coordination='conjunta', tamanos=TAMANOS,
                     seleccion='parecidos', semilla=0):
    if coordination != 'conjunta':
        raise ValueError('La mezcla creciente requiere coordinación conjunta')
    if not tamanos or list(tamanos) != sorted(set(tamanos)) or tamanos[0] < 2:
        raise ValueError('Los tamaños deben ser crecientes, sin repetir y desde 2')
    tick = time.perf_counter()
    deadline = tick + budget
    params = (d, starts, physical, plugs, tariffs, t0, horizon)
    comunes = dict(local_limit=local_limit, neighbors=neighbors, per_pair=per_pair, max_rounds=max_rounds,
                   coordination='conjunta')
    current, history, pasos, nivel, stop = plans, [], [], 0, 'ultimo_tamano_sin_mejoras'
    while nivel < len(tamanos):
        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            stop = 'presupuesto'
            break
        k = tamanos[nivel]
        if k == 2:
            current, hist, stats = buscar(current, lookup, *params, budget=remaining, **comunes)
        else:
            current, hist, stats = buscar_grupos(current, lookup, *params, budget=remaining, k=k,
                                                 seleccion=seleccion, semilla=semilla + len(pasos), **comunes)
        paso = len(pasos) + 1
        history += [dict(r, paso=paso, tamano=k) for r in hist]
        pasos.append(dict(paso=paso, tamano=k, intentos=stats['intentos'], mejoras=stats['mejoras'],
                          motivo_fin=stats['motivo_fin']))
        nivel = 0 if stats['mejoras'] else nivel + 1
    return current, history, dict(tiempo_busqueda_s=time.perf_counter() - tick,
                                  intentos=sum(p['intentos'] for p in pasos), mejoras=sum(p['mejoras'] for p in pasos),
                                  rondas=len(pasos), motivo_fin=stop, pasos=pasos, seleccion=seleccion)
