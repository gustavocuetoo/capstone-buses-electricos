"""Vecindario de k jornadas: la generalización de los tríos a grupos de 3, 4, 5 u 8 buses.

Con k=3 y selección «parecidos» reproduce exactamente buscar_trios (lo comprueba test_grupos.py).
Dos movimientos, como en los tríos:
  - absorción: la jornada del bus donante se reparte entre las otras k-1 (haz acotado);
  - rotación: las k colas giran entre los buses, sin tocar los comienzos.
"""
import itertools
import math
import random
import time
from collections import Counter
from metodo_hibrido.calendario import Calendario
from metodo_hibrido.conjunta import MAX_SECUENCIAS
from metodo_hibrido.intercambios import compatible, distancia_minima, evaluar_conjunto
from metodo_hibrido.recarga import cambiar_reservas, costo
from metodo_hibrido.trios import insertar
from metodo_hibrido.verificar import verificar

SELECCIONES = ('parecidos', 'azar')
# Tope de sorteos sin repetir antes de rendirse al elegir grupos al azar.
INTENTOS_SORTEO = 50


def _clave(seqs):
    return tuple(sorted(tuple(s) for s in seqs))


def propuestas(seqs, lookup, d, starts, finals, width=4, deadline=None):
    """Repartos alternativos de los servicios de k jornadas; seqs[0] es el donante."""
    def expired():
        return deadline is not None and time.perf_counter() >= deadline
    k = len(seqs)
    expected = Counter(t for s in seqs for t in s)
    seen = {_clave(seqs)}
    states = [[list(s) for s in seqs[1:]]]
    for trip in seqs[0]:
        if expired():
            return
        next_states = {}
        for state in states:
            for b in range(k - 1):
                for inserted in insertar(state[b], trip, lookup, d):
                    candidate = [inserted if i == b else state[i] for i in range(k - 1)]
                    empty = sum(distancia_minima(s, lookup, d, starts, finals) for s in candidate)
                    balance = sum(sum(lookup[t]['distancia_servicio_km'] for t in s) ** 2 for s in candidate)
                    next_states[_clave(candidate)] = (.5 * empty + .002 * balance, candidate)
        states = [v[1] for v in sorted(next_states.values(), key=lambda v: (v[0], v[1]))[:width]]
        if not states:
            break
    for candidate in states:
        if expired():
            return
        key = _clave(candidate)
        if key not in seen:
            assert Counter(t for s in candidate for t in s) == expected
            seen.add(key)
            yield f'absorcion_{k}_a_{k - 1}', candidate
    cuts = [sorted({0, len(s) // 2, len(s)}) for s in seqs]
    for cut in itertools.product(*cuts):
        if expired():
            return
        for step in range(1, k):
            candidate = [seqs[i][:cut[i]] + seqs[(i + step) % k][cut[(i + step) % k]:] for i in range(k)]
            candidate = [s for s in candidate if s]
            key = _clave(candidate)
            if key in seen or not all(compatible(s, lookup, d) for s in candidate):
                continue
            assert Counter(t for s in candidate for t in s) == expected
            seen.add(key)
            yield f'rotacion_{k}', candidate


def _companeros(ranks, k, neighbors, seleccion, rng):
    """Combinaciones de k-1 receptores para un donante.

    «parecidos» toma los receptores mejor clasificados; «azar» sortea la misma cantidad de grupos
    entre todos los receptores posibles del sector.
    """
    nearest = [j for _, _, j in sorted(ranks)[:neighbors]]
    if seleccion == 'parecidos':
        return list(itertools.combinations(nearest, k - 1))
    cuantos = math.comb(len(nearest), k - 1)
    pool = sorted(j for _, _, j in ranks)
    if cuantos == 0:
        return []
    if math.comb(len(pool), k - 1) <= cuantos:
        return list(itertools.combinations(pool, k - 1))
    elegidos, intentos = set(), 0
    while len(elegidos) < cuantos and intentos < cuantos * INTENTOS_SORTEO:
        elegidos.add(tuple(sorted(rng.sample(pool, k - 1))))
        intentos += 1
    return sorted(elegidos)


def _receptores(current, i, lookup, d, deadline):
    donor = current[i]
    ranks = []
    for j, p in enumerate(current):
        if time.perf_counter() >= deadline:
            break
        if i == j or p['sector_id'] != donor['sector_id']:
            continue
        can = [t for t in donor['corridas'] if next(insertar(p['corridas'], t, lookup, d), None) is not None]
        if can:
            # Prioriza receptores compatibles con muchos servicios y de baja carga de trabajo.
            ranks.append((-len(can), len(p['corridas']), j))
    return ranks


def _candidatos(current, lookup, d, starts, physical, tariffs, k, neighbors, per_pair, seleccion, rng, deadline):
    candidates, seen_groups = [], set()
    finals = starts + sorted(physical)
    for i in sorted(range(len(current)), key=lambda i: (len(current[i]['corridas']), current[i]['bus_id'])):
        if time.perf_counter() >= deadline:
            break
        ranks = _receptores(current, i, lookup, d, deadline)
        for combo in _companeros(ranks, k, neighbors, seleccion, rng):
            if time.perf_counter() >= deadline:
                break
            indices = (i,) + tuple(combo)
            group = tuple(sorted(indices))
            if group in seen_groups:
                continue
            seen_groups.add(group)
            old = [current[q] for q in indices]
            old_cost = costo(old, tariffs)
            choices = []
            for kind, seqs in propuestas([p['corridas'] for p in old], lookup, d, starts, finals, deadline=deadline):
                score = (250 * len(seqs) + .5 * (sum(distancia_minima(s, lookup, d, starts, finals) for s in seqs)
                         + sum(lookup[t]['distancia_servicio_km'] for s in seqs for t in s)) - old_cost)
                choices.append((score, kind, seqs))
            for score, kind, seqs in sorted(choices, key=lambda v: (v[0], v[1], v[2]))[:per_pair]:
                candidates.append((score, indices, kind, seqs))
    return candidates


def buscar_grupos(plans, lookup, d, starts, physical, plugs, tariffs, t0, horizon, budget=120., local_limit=2.,
                  neighbors=8, per_pair=3, max_rounds=3, coordination='conjunta', k=3, seleccion='parecidos', semilla=0):
    if coordination != 'conjunta':
        raise ValueError('Los grupos de jornadas requieren coordinación conjunta')
    if not 3 <= k <= MAX_SECUENCIAS:
        raise ValueError(f'El tamaño de grupo debe estar entre 3 y {MAX_SECUENCIAS}; los pares usan intercambios.buscar')
    if seleccion not in SELECCIONES:
        raise ValueError(f'Selección desconocida: {seleccion}')
    tick = time.perf_counter()
    deadline = tick + budget
    rng = random.Random(semilla)
    current = [dict(p) for p in plans]
    expected = [lookup[t] for p in current for t in p['corridas']]
    params = (d, starts, physical, plugs, tariffs, t0, horizon)
    verificar(current, expected, *params)
    calendar = Calendario(physical, plugs, t0, horizon)
    cambiar_reservas(calendar, current, 1)
    history, attempts, rounds, stop, last_message = [], 0, 0, 'rondas', tick
    for round_no in range(max_rounds):
        rounds = round_no + 1
        preparation_deadline = min(deadline, time.perf_counter() + min(15., budget * .2))
        candidates = _candidatos(current, lookup, d, starts, physical, tariffs, k, neighbors, per_pair,
                                 seleccion, rng, preparation_deadline)
        used, changed = set(), False
        for _, indices, kind, seqs in sorted(candidates, key=lambda v: (v[0], v[1], v[2])):
            if time.perf_counter() >= deadline:
                stop = 'presupuesto'
                break
            if any(i in used for i in indices):
                continue
            old = [current[i] for i in indices]
            attempts += 1
            candidate, status = evaluar_conjunto(old, seqs, lookup, d, starts, calendar, tariffs, local_limit, deadline)
            record = dict(ronda=round_no + 1, intento=attempts, tamano=k, seleccion=seleccion, tipo=kind,
                          buses='|'.join(p['bus_id'] for p in old), sector=old[0]['sector_id'],
                          estados=';'.join(status), aceptado=False, buses_evitados=0, ahorro_usd=0.)
            if candidate:
                for q, p in enumerate(candidate):
                    p['bus_id'] = old[q]['bus_id']
                proposal = [p for q, p in enumerate(current) if p is not None and q not in indices] + candidate
                try:
                    verificar(proposal, expected, *params)
                except (AssertionError, ValueError, KeyError) as error:
                    record['estados'] += ';rechazado_auditoria:' + str(error)
                else:
                    cambiar_reservas(calendar, old, -1)
                    cambiar_reservas(calendar, candidate, 1)
                    for q, i in enumerate(indices):
                        current[i] = candidate[q] if q < len(candidate) else None
                    record.update(aceptado=True, buses_evitados=k - len(candidate),
                                  ahorro_usd=costo(old, tariffs) - costo(candidate, tariffs))
                    changed = True
                    used.update(indices)
            history.append(record)
            if time.perf_counter() - last_message >= 20:
                print(f'Grupos de {k}: {attempts} intentos, {sum(r["aceptado"] for r in history)} mejoras aceptadas.',
                      flush=True)
                last_message = time.perf_counter()
        current = [p for p in current if p is not None]
        if time.perf_counter() >= deadline:
            stop = 'presupuesto'
            break
        if not changed:
            stop = 'sin_mejoras_en_vecindario'
            break
    verificar(current, expected, *params)
    return current, history, dict(tiempo_busqueda_s=time.perf_counter() - tick, intentos=attempts, rondas=rounds,
                                  motivo_fin=stop, mejoras=sum(r['aceptado'] for r in history), tamano=k,
                                  seleccion=seleccion)
