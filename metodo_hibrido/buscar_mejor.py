"""Búsqueda prolongada con los motores híbridos originales y etapas auditadas.

Permite continuar planes exportados con --desde. No modifica datos ni motores.
"""
import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instancia', type=Path, default=HERE / 'instancia_212')
    parser.add_argument('--desde', type=Path)
    parser.add_argument('--salida', type=Path, required=True)
    parser.add_argument('--presupuesto', type=float, default=600)
    parser.add_argument('--ciclos', type=int, default=1)
    parser.add_argument('--vecinos', type=int, default=8)
    parser.add_argument('--alternativas', type=int, default=3)
    parser.add_argument('--rondas', type=int, default=30)
    parser.add_argument('--limite-local', type=float, default=2)
    parser.add_argument('--licencia-restringida', action='store_true')
    args = parser.parse_args()
    if not args.salida.resolve().is_relative_to(HERE):
        parser.error('La salida debe estar dentro de metodo_hibrido')
    if args.salida.exists():
        parser.error('La salida ya existe')
    if min(args.presupuesto, args.ciclos, args.vecinos, args.alternativas,
           args.rondas, args.limite_local) <= 0:
        parser.error('Los límites deben ser positivos')

    import importlib.util
    if args.licencia_restringida:
        # Seleccionar explícitamente la licencia incluida en pip, sin alterar HOME.
        spec = importlib.util.find_spec('gurobipy')
        if spec is None:
            parser.error('gurobipy no está instalado en este Python')
        license_path = Path(spec.origin).parent / '.libs' / 'gurobi.lic'
        if not license_path.is_file():
            parser.error('No se encontró la licencia incluida en gurobipy')
        os.environ['GRB_LICENSE_FILE'] = str(license_path)
    import gurobipy as gp
    import numpy as np
    license_stats = dict(modelos_totales=0, modelos_descartados=0, descartados=[])
    original_model = gp.Model
    if args.licencia_restringida:
        class BoundedModel(original_model):
            def optimize(self, *a, **kw):
                license_stats['modelos_totales'] += 1
                try:
                    return super().optimize(*a, **kw)
                except gp.GurobiError as error:
                    if error.errno != 10010:
                        raise
                    self.update()
                    license_stats['modelos_descartados'] += 1
                    license_stats['descartados'].append(dict(
                        variables=self.NumVars, restricciones=self.NumConstrs,
                        indicadores=self.NumGenConstrs))
        gp.Model = BoundedModel

    from metodo_hibrido.caso_base import load_instance, solve, write_csv
    from metodo_hibrido.ejecutar import etapa, export, json_file
    from metodo_hibrido.intercambios import buscar
    from metodo_hibrido.trios import buscar_trios
    from metodo_hibrido.verificar import verificar

    tick = time.perf_counter()
    trips, *params = load_instance(args.instancia)
    args.salida.mkdir(parents=True)
    metadata = dict(
        inicio=datetime.now(ZoneInfo('America/Santiago')).isoformat(),
        parametros={k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        python=sys.version, gurobi=gp.gurobi.version(), numpy=np.__version__,
        sha256_entradas={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in args.instancia.iterdir() if p.is_file()},
        sha256_codigo={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in HERE.glob('*.py')},
        optimalidad_global_demostrada=False)
    json_file(args.salida / 'ejecucion.json', metadata)
    rows = []
    try:
        if args.desde:
            plans = json.loads(args.desde.read_text(encoding='utf8'))
            metadata['sha256_planes_iniciales'] = hashlib.sha256(args.desde.read_bytes()).hexdigest()
            json_file(args.salida / 'ejecucion.json', metadata)
        else:
            _, _, _, decisions, plans = solve(trips, *params, progress=lambda n, total, b:
                print(f'Construcción: {n}/{total}; {b} buses', flush=True))
        initial = export(args.salida / '00_inicial', plans, trips, params)
        if not args.desde:
            write_csv(args.salida / '00_inicial' / 'decisiones.csv', decisions)
        print(f"Inicial auditado: {initial['buses']} buses; USD {initial['costo_total_usd']:.2f}", flush=True)
        stages = []
        for cycle in range(1, args.ciclos + 1):
            cycle_start = verificar(plans, trips, *params)[0]['costo_total_usd']
            for name, search in [('pares', buscar), ('trios', buscar_trios)]:
                label = f'{cycle:02d}_{name}'
                print(f'{label}: presupuesto {args.presupuesto:g} s', flush=True)
                plans, history, stats = etapa(plans, trips, params, search,
                    budget=args.presupuesto, local_limit=args.limite_local,
                    neighbors=args.vecinos, per_pair=args.alternativas,
                    max_rounds=args.rondas, coordination='conjunta')
                report = export(args.salida / label, plans, trips, params)
                write_csv(args.salida / label / 'intentos.csv', history)
                json_file(args.salida / label / 'busqueda.json', stats)
                stages.append(dict(etapa=label, **stats))
                rows.append(dict(etapa=label, **report))
                print(f"{label}: {report['buses']} buses; USD {report['costo_total_usd']:.2f}; {stats['motivo_fin']}", flush=True)
            if verificar(plans, trips, *params)[0]['costo_total_usd'] >= cycle_start - 1e-5:
                break
        final = export(args.salida / '04_final', plans, trips, params)
        assert final['costo_total_usd'] <= initial['costo_total_usd'] + 1e-5
        result = dict(inicial=initial, final=final, busquedas=stages,
            corridas=len(trips), rutas=len({t['route_id'] for t in trips}),
            buses_evitados=initial['buses']-final['buses'],
            ahorro_usd=initial['costo_total_usd']-final['costo_total_usd'],
            mejora_porcentual=100*(initial['costo_total_usd']-final['costo_total_usd'])/initial['costo_total_usd'],
            tiempo_total_s=time.perf_counter()-tick, optimalidad_global_demostrada=False)
        json_file(args.salida / 'comparacion.json', result)
        fields = ['etapa', 'buses', 'corridas', 'km', 'carga_kwh', 'sesiones', 'costo_total_usd']
        write_csv(args.salida / 'comparacion_etapas.csv',
                  [{k: r[k] for k in fields} for r in [dict(etapa='inicial', **initial)] + rows])
        print(json.dumps({k: v for k, v in result.items() if k not in ('inicial', 'final', 'busquedas')}, indent=2), flush=True)
    except Exception as error:
        json_file(args.salida / 'fallo.json', dict(error=type(error).__name__, detalle=str(error)))
        raise
    finally:
        json_file(args.salida / 'licencia.json', license_stats)


if __name__ == '__main__':
    main()
