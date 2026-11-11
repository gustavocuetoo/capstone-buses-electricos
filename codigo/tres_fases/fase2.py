"""Descomposición del flujo entero mediante emparejamiento local de energía."""
import heapq
from collections import defaultdict, Counter

def descomponer_energia(nodes, arcs, flow, source, sink):
    outgoing = defaultdict(list)
    indegree = Counter()
    active = {source, sink}
    fleet = 0
    for i, (a, x) in enumerate(zip(arcs, flow)):
        if a['tipo'] == 'flota':
            fleet += int(x)
        elif x:
            outgoing[a['u']].append(i)
            indegree[a['v']] += 1
            active.update((a['u'], a['v']))
    ready = [n for n in active if indegree[n] == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        u = heapq.heappop(ready)
        order.append(u)
        for i in outgoing[u]:
            v = arcs[i]['v']
            indegree[v] -= 1
            if indegree[v] == 0:
                heapq.heappush(ready, v)
    if len(order) != len(active):
        raise ValueError('El flujo operacional contiene un ciclo')
    # Energía hasta el próximo servicio; se usa solo para ordenar, no como garantía de SOC.
    lookahead = defaultdict(float)
    scores = {}
    for u in reversed(order):
        for i in outgoing[u]:
            a = arcs[i]
            scores[i] = 1.4*a['km'] + (0 if a['tipo'] == 'servicio' else lookahead[a['v']])
        if outgoing[u]:
            lookahead[u] = min(scores[i] for i in outgoing[u])
    tokens = defaultdict(list)
    tokens[source] = [(0., b, []) for b in range(fleet)]
    for u in order:
        if u == sink:
            continue
        choices = [i for i in outgoing[u] for _ in range(int(flow[i]))]
        incoming = sorted(tokens.pop(u, []), key=lambda t: (-t[0], t[1]))
        choices.sort(key=lambda i: (scores[i], i))
        if len(incoming) != len(choices):
            raise AssertionError('Desbalance al construir jornadas')
        for (energy, bus, path), i in zip(incoming, choices):
            path.append(i)
            tokens[arcs[i]['v']].append((energy+1.4*arcs[i]['km'], bus, path))
    paths = [p for _, _, p in sorted(tokens[sink], key=lambda t: t[1])]
    used = Counter(i for p in paths for i in p)
    assert len(paths) == fleet
    assert all(used[i] == int(x) for i, (a, x) in enumerate(zip(arcs, flow)) if a['tipo'] != 'flota')
    return paths
