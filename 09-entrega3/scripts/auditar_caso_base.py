"""Pasa un plan del caso base miope por el auditor del método híbrido, sin modificarlo.

Uso, desde la raíz del proyecto:
  .venv-optimizacion/bin/python 09-entrega3/scripts/auditar_caso_base.py \\
      --instancia metodo_hibrido/instancia_417_S \\
      --caso-base "codigo/output/tres_fases/red_417_S_caso_base"
Escribe auditoria_hibrido.json en la carpeta del caso base y termina con código 1 si no aprueba.
"""
import argparse
import json
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / '08-entrega2/informe2/scripts'))
from auditar_miope import CLAVES_COMPARADAS, planes_desde_csv  # noqa: E402
from metodo_hibrido.caso_base import load_instance, read_csv  # noqa: E402
from metodo_hibrido.verificar import verificar  # noqa: E402


def auditar(instancia, carpeta):
    """Reconstruye los planes desde los CSV del caso base y los audita con las reglas del híbrido."""
    carpeta = Path(carpeta)
    trips, *params = load_instance(instancia)
    planes = planes_desde_csv(read_csv(carpeta / 'actividades.csv'), read_csv(carpeta / 'jornadas.csv'))
    esperado = json.loads((carpeta / 'resumen.json').read_text(encoding='utf-8'))['caso_base']
    try:
        reporte, _, _ = verificar(planes, trips, *params)
    except Exception as error:  # el auditor señala la primera regla que no se cumple
        return dict(aprobado=False, error=f'{type(error).__name__}: {error}', diferencias=[])
    diferencias = [dict(clave=k, auditor=reporte[k], caso_base=esperado[k]) for k in CLAVES_COMPARADAS
                   if not math.isclose(reporte[k], esperado[k], rel_tol=1e-9, abs_tol=1e-6)]
    return dict(aprobado=reporte.get('verificado') is True and not diferencias,
                reporte=reporte, diferencias=diferencias)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instancia', type=Path, required=True)
    parser.add_argument('--caso-base', type=Path, required=True)
    args = parser.parse_args()
    resultado = auditar(args.instancia, args.caso_base)
    (args.caso_base / 'auditoria_hibrido.json').write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in resultado.items() if k != 'reporte'}, ensure_ascii=False))
    return 0 if resultado['aprobado'] else 1


if __name__ == '__main__':
    sys.exit(main())
