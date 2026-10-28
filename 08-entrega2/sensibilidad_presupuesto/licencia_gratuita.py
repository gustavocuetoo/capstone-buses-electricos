"""Corre metodo_hibrido/ejecutar.py con la licencia gratuita que trae gurobipy (pip).

Esa licencia resuelve modelos de hasta 2.000 variables y 2.000 restricciones (lineales más
indicadores). En una búsqueda de 120 + 120 s en este Mac, 7 de 5.232 modelos de tríos (0,13 %)
pasaron el tope: aquí se tratan como «sin solución» (el candidato se descarta) en vez de botar la
corrida. Es la única diferencia con el ejecutor oficial, que no se modifica. Cada corrida deja
licencia_gratuita.json con cuántos modelos se enviaron a Gurobi y cuántos se descartaron.

Uso: los mismos argumentos de ejecutar.py, por ejemplo
    python licencia_gratuita.py --salida RUTA --presupuesto-pares 60 --presupuesto-trios 60
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROYECTO = HERE.parents[1]
# Sin un gurobi.lic a la vista, gurobipy usa su licencia restringida (la de este Mac está vencida).
HOME_SIN_LICENCIA = HERE / ".home_sin_licencia"
ERROR_TAMANO_LICENCIA = 10010


def usar_licencia_gratuita() -> None:
    HOME_SIN_LICENCIA.mkdir(exist_ok=True)
    os.environ["HOME"] = str(HOME_SIN_LICENCIA)


def parchar_gurobi(conteo: dict) -> None:
    """Cuenta los modelos y descarta, sin resolver, los que superan el tope de la licencia."""
    import gurobipy as gp

    class ModeloConTope(gp.Model):
        def optimize(self, *args, **kwargs):
            conteo["modelos"] += 1
            try:
                return super().optimize(*args, **kwargs)
            except gp.GurobiError as error:
                if error.errno != ERROR_TAMANO_LICENCIA:
                    raise
                self.update()
                conteo["descartados"].append(dict(variables=self.NumVars, restricciones=self.NumConstrs,
                                                  indicadores=self.NumGenConstrs))

    gp.Model = ModeloConTope


def salida_de(argumentos: list):
    """Carpeta de salida indicada con --salida, o None si no viene."""
    if "--salida" in argumentos and argumentos.index("--salida") + 1 < len(argumentos):
        return Path(argumentos[argumentos.index("--salida") + 1])
    return None


def main() -> None:
    usar_licencia_gratuita()
    conteo = dict(modelos=0, descartados=[])
    parchar_gurobi(conteo)
    sys.path.insert(0, str(PROYECTO))
    from metodo_hibrido import ejecutar
    salida = salida_de(sys.argv[1:])
    sys.argv = [str(PROYECTO / "metodo_hibrido" / "ejecutar.py")] + sys.argv[1:]
    try:
        ejecutar.main()
    finally:
        if salida is not None and salida.exists():
            (salida / "licencia_gratuita.json").write_text(json.dumps(dict(
                licencia="restringida de gurobipy (pip): hasta 2.000 variables y 2.000 restricciones",
                modelos_totales=conteo["modelos"], modelos_descartados=len(conteo["descartados"]),
                descartados=conteo["descartados"]), ensure_ascii=False, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
