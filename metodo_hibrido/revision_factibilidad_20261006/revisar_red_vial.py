"""Recalcula los traslados usados en la red vial dirigida almacenada.

El caché de fase 1 incluye extremos de servicio y terminales T. Las conexiones
a E provienen de una matriz distinta y se verifican en la auditoría principal.
"""
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.sparse import load_npz
from scipy.sparse.csgraph import dijkstra

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def main():
    started = perf_counter()
    graph_file = ROOT / 'CODIGO apstone/output/fase1/red_vial_cache.npz'
    points_file = ROOT / 'CODIGO apstone/output/fase1/puntos_red_cache.json'
    graph = load_npz(graph_file)
    snaps = json.loads(points_file.read_text())['snaps']
    pairs = json.loads((HERE / 'pares_traslado_utilizados.json').read_text())
    with (ROOT / 'CODIGO apstone/output/fase1/traslados.csv').open(encoding='utf-8-sig',newline='') as stream:
        exported = {(r['origen_id'],r['destino_id']):float(r['distancia_km'])
                    for r in csv.DictReader(stream) if r['distancia_km']}
    assert np.all(np.isfinite(graph.data)) and np.all(graph.data >= 0)
    by_source, outside = defaultdict(list), []
    for a,b in pairs:
        if a in snaps and b in snaps:
            by_source[a].append(b)
        else:
            outside.append([a,b])
    verified, max_difference, witness = 0, 0., None
    for index,(a,targets) in enumerate(sorted(by_source.items()),1):
        distances = dijkstra(graph,directed=True,indices=snaps[a]['node'])
        for b in targets:
            actual = float(distances[snaps[b]['node']])
            assert math.isfinite(actual), f'Sin camino: {a},{b}'
            difference = abs(actual-exported[a,b])
            assert difference <= .00000051, f'Distancia discrepante: {a},{b}: {actual}, {exported[a,b]}'
            if difference > max_difference:
                max_difference,witness = difference,[a,b]
            verified += 1
        if index % 60 == 0:
            print(json.dumps(dict(origenes_revisados=index,origenes_total=len(by_source),pares_verificados=verified)),flush=True)
    result = dict(aprobado=True,origenes_recalculados=len(by_source),pares_recalculados=verified,
                  conexiones_e_de_matriz_separada=len(outside),
                  diferencia_maxima_km=max_difference,testigo_diferencia=witness,
                  grafo_nodos=graph.shape[0],grafo_arcos=graph.nnz,
                  metodo='Caminos mínimos dirigidos de SciPy, sobre el caché de red vial fuente; sin importar código del optimizador.',
                  segundos=perf_counter()-started,
                  sha256_grafo=hashlib.sha256(graph_file.read_bytes()).hexdigest(),
                  sha256_puntos=hashlib.sha256(points_file.read_bytes()).hexdigest())
    (HERE / 'verificacion_red_vial.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
