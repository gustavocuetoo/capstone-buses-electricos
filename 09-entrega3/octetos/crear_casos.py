"""Crea los casos muy chicos y chicos para comparar pares y tríos contra grupos más grandes.

Cada caso es un subconjunto de rutas completas de la instancia de 212 rutas, de un solo sector:
  - 6 muy chicos: 1 ruta de 15 a 40 corridas, donde se puede buscar la respuesta perfecta;
  - 6 chicos: 2, 3 o 4 rutas de 25 a 80 corridas cada una.
Las corridas se copian sin cambios y el horizonte es el de la instancia de origen.

Uso, desde la raíz del proyecto:
  .venv-optimizacion/bin/python 09-entrega3/octetos/crear_casos.py
"""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from metodo_hibrido.caso_base import load_instance, read_csv, validate_inputs, write_csv  # noqa: E402

INSTANCIA_212 = RAIZ / 'metodo_hibrido/instancia_212'
DESTINO = Path(__file__).resolve().parent / 'casos'

MUY_CHICO_CORRIDAS = (15, 40)
MUY_CHICO_IDEAL = 25
MUY_CHICOS = 6
CHICO_CORRIDAS = (25, 80)
# (posición del sector en orden, número de rutas) de cada caso chico. El sector 4 es el que
# tiene más rutas en el rango, por eso recibe dos casos.
CHICOS = ((0, 2), (1, 2), (2, 3), (3, 3), (4, 4), (3, 4))


def _rutas(corridas):
    conteo = Counter(r['route_id'] for r in corridas)
    sectores = {}
    for r in corridas:
        if sectores.setdefault(r['route_id'], r['sector_id']) != r['sector_id']:
            raise ValueError(f"La ruta {r['route_id']} aparece en más de un sector")
    return conteo, sectores


def _muy_chicos(conteo, sectores):
    bajo, alto = MUY_CHICO_CORRIDAS
    candidatas = sorted((abs(n - MUY_CHICO_IDEAL), ruta) for ruta, n in conteo.items() if bajo <= n <= alto)
    elegidas = []
    for sector in sorted(set(sectores.values())):
        mejor = next((ruta for _, ruta in candidatas if sectores[ruta] == sector), None)
        if mejor is not None:
            elegidas.append(mejor)
    elegidas += [ruta for _, ruta in candidatas if ruta not in elegidas][:MUY_CHICOS - len(elegidas)]
    if len(elegidas) != MUY_CHICOS:
        raise ValueError(f'Solo hay {len(elegidas)} rutas de {bajo} a {alto} corridas')
    return [dict(tipo='muy_chico', nombre=f'muy_chico_{i:02d}_ruta_{ruta}', sector=sectores[ruta], rutas=[ruta])
            for i, ruta in enumerate(elegidas, 1)]


def _chicos(conteo, sectores, usadas):
    bajo, alto = CHICO_CORRIDAS
    orden = sorted(set(sectores.values()))
    usadas = set(usadas)
    casos = []
    for i, (posicion, cuantas) in enumerate(CHICOS, 1):
        sector = orden[posicion]
        libres = sorted(r for r, n in conteo.items()
                        if sectores[r] == sector and bajo <= n <= alto and r not in usadas)
        if len(libres) < cuantas:
            raise ValueError(f'El sector {sector} no tiene {cuantas} rutas libres de {bajo} a {alto} corridas')
        rutas = libres[:cuantas]
        usadas |= set(rutas)
        casos.append(dict(tipo='chico', nombre=f'chico_{i:02d}_sector_{sector}_{cuantas}_rutas',
                          sector=sector, rutas=rutas))
    return casos


def elegir_casos(corridas):
    """Regla fija y reproducible; no depende del orden de las corridas."""
    conteo, sectores = _rutas(corridas)
    muy_chicos = _muy_chicos(conteo, sectores)
    return muy_chicos + _chicos(conteo, sectores, [c['rutas'][0] for c in muy_chicos])


def _distancias_del_caso(distancias, paradas):
    """Conserva los pares cuyos extremos de parada pertenecen al caso; terminales y electroterminales, todos."""
    def sirve(extremo):
        return not extremo.startswith('S:') or extremo in paradas
    return [r for r in distancias if sirve(r['origen_id']) and sirve(r['destino_id'])]


def _escribir(carpeta, corridas, distancias, escenario):
    carpeta.mkdir()
    write_csv(carpeta / 'corridas.csv', corridas)
    write_csv(carpeta / 'distancias.csv', distancias)
    (carpeta / 'escenario.json').write_text(json.dumps(escenario, ensure_ascii=False, indent=2), encoding='utf8')
    validate_inputs(*load_instance(carpeta))


def crear_casos(destino=DESTINO, origen=INSTANCIA_212):
    destino, origen = Path(destino), Path(origen)
    corridas = read_csv(origen / 'corridas.csv')
    casos = elegir_casos(corridas)
    existentes = [c['nombre'] for c in casos if (destino / c['nombre']).exists()]
    if existentes or (destino / 'indice.csv').exists():
        raise FileExistsError(f'Ya existen casos en {destino}: {existentes[:3]}')
    distancias = read_csv(origen / 'distancias.csv')
    base = json.loads((origen / 'escenario.json').read_text(encoding='utf-8-sig'))
    huella = hashlib.sha256((origen / 'corridas.csv').read_bytes()).hexdigest()
    destino.mkdir(parents=True, exist_ok=True)
    indice = []
    for caso in casos:
        rutas = set(caso['rutas'])
        propias = [r for r in corridas if r['route_id'] in rutas]
        paradas = {'S:' + r[k] for r in propias for k in ('inicio_stop_id', 'fin_stop_id')}
        escenario = {**base, 'rutas': sorted(rutas),
                     'origen': f"Caso {caso['tipo'].replace('_', ' ')} de la instancia de 212 rutas; rutas completas",
                     'corridas_origen_sha256': huella}
        _escribir(destino / caso['nombre'], propias, _distancias_del_caso(distancias, paradas), escenario)
        indice.append(dict(nombre=caso['nombre'], tipo=caso['tipo'], sector=caso['sector'],
                           rutas='|'.join(caso['rutas']), corridas=len(propias)))
    write_csv(destino / 'indice.csv', indice)
    return indice


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--destino', type=Path, default=DESTINO)
    args = parser.parse_args()
    for fila in crear_casos(args.destino):
        print(f"{fila['nombre']:<34} sector {fila['sector']}  {fila['corridas']:>4} corridas  {fila['rutas']}")


if __name__ == '__main__':
    main()
