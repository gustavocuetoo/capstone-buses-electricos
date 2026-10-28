"""Barrido del presupuesto de búsqueda del método híbrido (lámina 32 de la Entrega 2).

Corre el ejecutor oficial (metodo_hibrido/ejecutar.py) sin modificarlo: el mismo presupuesto
para parejas y tríos, varias repeticiones por presupuesto y una corrida a la vez. La búsqueda
se corta por reloj, así que correr en paralelo cambiaría lo que cada corrida alcanza a revisar.

El orden de los presupuestos se baraja dentro de cada repetición (semilla fija) para que el
calentamiento del equipo o la carga de fondo no favorezcan siempre al mismo presupuesto.
Si se interrumpe, al volver a correrlo salta las corridas que ya tienen comparacion.json.

Uso (con el Python que tiene gurobipy 12 y una licencia vigente):
    python barrido.py --plan            # muestra el plan y el tiempo estimado, no corre nada
    python barrido.py                   # corre lo que falte
    python barrido.py --hibrido RUTA    # si metodo_hibrido/ no está en la carpeta del proyecto
    python barrido.py --licencia-gratuita   # sin licencia vigente: ver licencia_gratuita.py
"""
import argparse
import csv
import platform
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROYECTO = HERE.parents[1]
PRESUPUESTOS_S = (30, 60, 120, 240)
REPETICIONES = 3
SEMILLA_ORDEN = 2026
# Carga, construcción, auditorías y exportación medidas en el ensayo original (463,6 s en total
# con 120 + 120 s de búsqueda). Solo sirve para estimar la duración del barrido.
SOBRECOSTO_POR_CORRIDA_S = 220


def nombre_corrida(presupuesto: int, repeticion: int) -> str:
    return f"B{presupuesto:03d}_r{repeticion}"


def plan_de_corridas(presupuestos, repeticiones, semilla=SEMILLA_ORDEN):
    """Lista (presupuesto, repetición) en bloques por repetición, barajados con semilla fija."""
    plan = []
    for repeticion in range(1, repeticiones + 1):
        orden = list(presupuestos)
        random.Random(semilla + repeticion).shuffle(orden)
        plan.extend((presupuesto, repeticion) for presupuesto in orden)
    return plan


def estado_corrida(carpeta: Path) -> str:
    if (carpeta / "comparacion.json").exists():
        return "lista"
    if carpeta.exists():
        return "incompleta"
    return "pendiente"


def comprobar_gurobi(hibrido: Path, variables: int) -> None:
    """Falla antes de empezar si gurobipy no carga o la licencia no sirve."""
    sys.path.insert(0, str(hibrido.parent / ".deps"))  # igual que ejecutar.py
    try:
        import gurobipy as gp
        modelo = gp.Model()
        modelo.Params.OutputFlag = 0
        x = modelo.addVars(variables, ub=1)
        modelo.setObjective(x.sum(), gp.GRB.MAXIMIZE)
        modelo.optimize()
    except Exception as error:  # ImportError o GurobiError: el mensaje original basta
        sys.exit(f"Gurobi no está listo en este Python ({sys.executable}): {error}")


def correr(ejecutor: Path, salida: Path, presupuesto: int, repeticion: int, registro: Path) -> int:
    carpeta = salida / nombre_corrida(presupuesto, repeticion)
    log = salida / "logs" / f"{carpeta.name}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    comando = [sys.executable, "-u", str(ejecutor), "--salida", str(carpeta),
               "--presupuesto-pares", str(presupuesto), "--presupuesto-trios", str(presupuesto)]
    inicio = datetime.now()
    tick = time.perf_counter()
    with log.open("w", encoding="utf8") as salida_log:
        codigo = subprocess.run(comando, stdout=salida_log, stderr=subprocess.STDOUT).returncode
    duracion = time.perf_counter() - tick
    nuevo = not registro.exists()
    with registro.open("a", newline="", encoding="utf8") as archivo:
        escritor = csv.writer(archivo)
        if nuevo:
            escritor.writerow(["corrida", "presupuesto_s", "repeticion", "inicio", "duracion_s",
                               "codigo_salida", "ejecutor", "sistema", "procesador", "python"])
        escritor.writerow([carpeta.name, presupuesto, repeticion, inicio.isoformat(timespec="seconds"),
                           f"{duracion:.1f}", codigo, ejecutor.name, platform.platform(), platform.machine(),
                           platform.python_version()])
    return codigo


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hibrido", type=Path, default=PROYECTO / "metodo_hibrido")
    parser.add_argument("--presupuestos", type=int, nargs="+", default=list(PRESUPUESTOS_S))
    parser.add_argument("--repeticiones", type=int, default=REPETICIONES)
    parser.add_argument("--plan", action="store_true", help="solo mostrar el plan")
    parser.add_argument("--licencia-gratuita", action="store_true",
                        help="correr con la licencia restringida de pip (ver licencia_gratuita.py)")
    args = parser.parse_args()
    hibrido = args.hibrido.resolve()
    if not (hibrido / "ejecutar.py").exists():
        parser.error(f"No encuentro ejecutar.py en {hibrido}")
    if args.licencia_gratuita and hibrido != (PROYECTO / "metodo_hibrido").resolve():
        parser.error("--licencia-gratuita usa el metodo_hibrido/ de la carpeta del proyecto")
    if min(args.presupuestos) <= 0 or args.repeticiones <= 0:
        parser.error("Presupuestos y repeticiones deben ser positivos")
    salida = hibrido / "resultados" / "presupuesto"
    plan = plan_de_corridas(args.presupuestos, args.repeticiones)
    estados = {p: estado_corrida(salida / nombre_corrida(*p)) for p in plan}
    pendientes = [p for p in plan if estados[p] == "pendiente"]
    estimado = sum(2 * b + SOBRECOSTO_POR_CORRIDA_S for b, _ in pendientes)
    for presupuesto, repeticion in plan:
        print(f"  {nombre_corrida(presupuesto, repeticion)}  {estados[(presupuesto, repeticion)]}")
    print(f"{len(pendientes)} corridas pendientes; unos {estimado / 60:.0f} min en total.")
    incompletas = [nombre_corrida(*p) for p in plan if estados[p] == "incompleta"]
    if incompletas:
        print("Ojo: estas carpetas existen sin comparacion.json (revisar fallo.json y el log); "
              "no se tocan: " + ", ".join(incompletas))
    if args.plan or not pendientes:
        return
    if args.licencia_gratuita:
        from licencia_gratuita import usar_licencia_gratuita
        usar_licencia_gratuita()  # los procesos hijos heredan el mismo HOME
        comprobar_gurobi(hibrido, variables=100)
        ejecutor = HERE / "licencia_gratuita.py"
    else:
        comprobar_gurobi(hibrido, variables=2500)  # sobre el tope de la licencia restringida
        ejecutor = hibrido / "ejecutar.py"
    for numero, (presupuesto, repeticion) in enumerate(pendientes, start=1):
        print(f"[{datetime.now():%H:%M}] {numero}/{len(pendientes)}: {nombre_corrida(presupuesto, repeticion)}",
              flush=True)
        codigo = correr(ejecutor, salida, presupuesto, repeticion, salida / "registro.csv")
        if codigo != 0:
            print(f"   terminó con código {codigo}; ver logs/{nombre_corrida(presupuesto, repeticion)}.log",
                  flush=True)
    print("Barrido terminado. Siguiente paso: python grafico.py")


if __name__ == "__main__":
    main()
