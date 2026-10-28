"""Gráfico de la lámina 32: ahorro adicional del híbrido según el presupuesto de búsqueda.

Lee las corridas que deja barrido.py en metodo_hibrido/resultados/presupuesto/B*_r*, escribe
resumen_barrido.csv y dibuja grafico_presupuesto.png con el tamaño del recuadro de la lámina
(935 × 402 px de una lámina de 1920 × 1080) y fondo transparente, para pegarlo en Canva.

Ahorro adicional = costo de la construcción cronológica − costo después de cada búsqueda
(USD por día). Es el mismo criterio de la guía: USD 10.738,45 con 120 + 120 s en el ensayo original.

Uso:
    python grafico.py                         # con las corridas del barrido
    python grafico.py --con-ensayo-original   # agrega el ensayo de 120 s (otro equipo) como rombo
"""
import argparse
import csv
import json
import statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.ticker import NullLocator

HERE = Path(__file__).resolve().parent
PROYECTO = HERE.parents[1]
BARRIDO = PROYECTO / "metodo_hibrido" / "resultados" / "presupuesto"
ENSAYO_ORIGINAL = PROYECTO / "metodo_hibrido" / "resultados" / "ensayo_212"

# Recuadro del gráfico en la lámina 32, en px de una lámina de 1920 × 1080.
ANCHO_PX, ALTO_PX = 935, 402
MARGEN_PX = dict(izquierda=74, derecha=128, arriba=58, abajo=86)
PX_POR_PULGADA = 100
DPI_SALIDA = 300            # 3× para que se vea nítido en Canva
PT = 72 / PX_POR_PULGADA    # puntos por px de lámina

ROJO = "#d42a1e"            # rojo del deck: resultado final del híbrido
GRIS = "#8a8a8a"            # gris de énfasis: etapa intermedia
TINTA = "#232323"
TINTA_2 = "#5e5e5e"
GRILLA = "#e4e4e4"
SUPERFICIE = "#fefdfc"      # fondo de la lámina: anillo de los puntos
# (clave, etiqueta, color, opacidad de la banda); la primera es la que importa.
ETAPAS = (("parejas_y_trios", "Parejas + tríos", ROJO, 0.12),
          ("parejas", "Solo parejas", GRIS, 0.16))
TOLERANCIA_USD = 0.01
SEPARACION_ETIQUETAS_PX = 50
PRESUPUESTO_USADO_S = 120


def miles(valor: float) -> str:
    """Formato chileno: 10738.45 -> '10.738'."""
    return f"{valor:,.0f}".replace(",", ".")


def _leer_json(ruta: Path) -> dict:
    return json.loads(ruta.read_text(encoding="utf8"))


def leer_corrida(carpeta: Path) -> dict:
    """Ahorro y esfuerzo de cada búsqueda de una corrida de ejecutar.py."""
    parametros = _leer_json(carpeta / "ejecucion.json")["parametros"]
    if parametros["presupuesto_pares"] != parametros["presupuesto_trios"]:
        raise ValueError(f"{carpeta.name}: presupuestos distintos para parejas y tríos")
    with (carpeta / "comparacion_etapas.csv").open(encoding="utf-8-sig", newline="") as archivo:
        etapas = {fila["etapa"]: fila for fila in csv.DictReader(archivo)}
    base = etapas["caso_base"]
    corrida = dict(corrida=carpeta.name, presupuesto_s=float(parametros["presupuesto_pares"]),
                   costo_construccion=float(base["costo_total_usd"]), buses_construccion=int(base["buses"]))
    licencia = carpeta / "licencia_gratuita.json"  # solo existe si se corrió con licencia_gratuita.py
    if licencia.exists():
        datos = _leer_json(licencia)
        corrida.update(modelos_totales=datos["modelos_totales"], modelos_descartados=datos["modelos_descartados"])
    for clave, etapa in (("parejas", "02_pares"), ("parejas_y_trios", "03_trios")):
        busqueda = _leer_json(carpeta / etapa / "busqueda.json")
        corrida[clave] = dict(
            ahorro_usd=corrida["costo_construccion"] - float(etapas[etapa]["costo_total_usd"]),
            buses_evitados=corrida["buses_construccion"] - int(etapas[etapa]["buses"]),
            intentos=busqueda["intentos"], mejoras=busqueda["mejoras"],
            tiempo_busqueda_s=busqueda["tiempo_busqueda_s"], motivo_fin=busqueda["motivo_fin"])
    return corrida


def leer_barrido(carpeta: Path) -> list:
    """Corridas terminadas; exige que todas partan de la misma construcción."""
    corridas = [leer_corrida(c) for c in sorted(carpeta.glob("B*_r*")) if (c / "comparacion.json").exists()]
    if not corridas:
        raise FileNotFoundError(f"No hay corridas terminadas en {carpeta}")
    primera = corridas[0]
    for corrida in corridas[1:]:
        if (abs(corrida["costo_construccion"] - primera["costo_construccion"]) > TOLERANCIA_USD
                or corrida["buses_construccion"] != primera["buses_construccion"]):
            raise ValueError(f"La construcción de {corrida['corrida']} no coincide con la de "
                             f"{primera['corrida']}: las corridas no parten del mismo punto")
    return corridas


def resumir(corridas: list) -> dict:
    """{(etapa, presupuesto): n, mediana, mínimo y máximo del ahorro, y mediana de buses}."""
    grupos = {}
    for corrida in corridas:
        for clave, *_ in ETAPAS:
            grupos.setdefault((clave, corrida["presupuesto_s"]), []).append(corrida[clave])
    resumen = {}
    for llave, filas in grupos.items():
        ahorros = [f["ahorro_usd"] for f in filas]
        resumen[llave] = dict(n=len(filas), mediana=statistics.median(ahorros), minimo=min(ahorros),
                              maximo=max(ahorros),
                              buses_mediana=statistics.median(f["buses_evitados"] for f in filas))
    return resumen


def escribir_csv(corridas: list, ruta: Path) -> None:
    campos = ["corrida", "presupuesto_s", "etapa", "ahorro_usd", "buses_evitados", "intentos", "mejoras",
              "tiempo_busqueda_s", "motivo_fin", "costo_construccion"]
    with ruta.open("w", newline="", encoding="utf8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        for corrida in corridas:
            for clave, *_ in ETAPAS:
                escritor.writerow(dict(corrida=corrida["corrida"], presupuesto_s=corrida["presupuesto_s"],
                                       etapa=clave, costo_construccion=corrida["costo_construccion"],
                                       **corrida[clave]))


def _figura():
    for nombre in ("PT_Sans.ttf", "PT_Sans_Bold.ttf"):
        font_manager.fontManager.addfont(str(HERE / "fonts" / nombre))
    plt.rcParams["font.family"] = "PT Sans"
    # El épsilon evita que 4,02 pulgadas × 300 dpi se trunque a 1205 px en vez de 1206.
    fig = plt.figure(figsize=(ANCHO_PX / PX_POR_PULGADA + 1e-6, ALTO_PX / PX_POR_PULGADA + 1e-6),
                     dpi=PX_POR_PULGADA)
    m = MARGEN_PX
    ax = fig.add_axes([m["izquierda"] / ANCHO_PX, m["abajo"] / ALTO_PX,
                       (ANCHO_PX - m["izquierda"] - m["derecha"]) / ANCHO_PX,
                       (ALTO_PX - m["arriba"] - m["abajo"]) / ALTO_PX])
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    return fig, ax


def _ejes(ax, presupuestos: list, techo: float, paso: int, usado) -> None:
    """usado: presupuesto que se destaca como el del ensayo, o None si se corrió en otro equipo."""
    ax.set_xscale("log", base=2)
    ax.set_xlim(presupuestos[0] / 1.3, presupuestos[-1] * 1.3)
    ax.set_xticks(presupuestos)
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xticklabels([f"{b:g} s (usado)" if b == usado else f"{b:g} s" for b in presupuestos],
                       fontsize=21 * PT, color=TINTA_2)
    for etiqueta, b in zip(ax.get_xticklabels(), presupuestos):
        if b == usado:
            etiqueta.set_color(TINTA)
            etiqueta.set_fontweight("bold")
    ax.set_ylim(0, techo)
    marcas = range(0, int(techo) + 1, paso)
    ax.set_yticks(list(marcas))
    ax.set_yticklabels([miles(v) for v in marcas], fontsize=20 * PT, color=TINTA_2)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color("#c9c9c9")
    ax.spines["bottom"].set_linewidth(1 * PT)
    ax.tick_params(axis="both", length=0, pad=8 * PT)
    ax.yaxis.grid(True, color=GRILLA, linewidth=1 * PT)
    ax.set_axisbelow(True)
    if usado in presupuestos:
        ax.axvline(usado, color=GRILLA, linewidth=1.5 * PT, zorder=0)


def _series(ax, corridas: list, resumen: dict, presupuestos: list, repeticiones: int) -> None:
    for orden, (clave, etiqueta, color, opacidad) in enumerate(reversed(ETAPAS)):
        z = 2 + 2 * orden
        medianas = [resumen[(clave, b)]["mediana"] for b in presupuestos]
        if repeticiones > 1:  # con una sola corrida no hay banda ni puntos aparte que mostrar
            mins = [resumen[(clave, b)]["minimo"] for b in presupuestos]
            maxs = [resumen[(clave, b)]["maximo"] for b in presupuestos]
            ax.fill_between(presupuestos, mins, maxs, color=color, alpha=opacidad, linewidth=0, zorder=z)
            ax.scatter([c["presupuesto_s"] for c in corridas], [c[clave]["ahorro_usd"] for c in corridas],
                       s=(7 * PT) ** 2, color=color, alpha=0.55, edgecolors=SUPERFICIE, linewidths=1.5 * PT,
                       zorder=z + 1)
        ax.plot(presupuestos, medianas, color=color, linewidth=2.5 * PT, solid_capstyle="round",
                solid_joinstyle="round", marker="o", markersize=11 * PT, markeredgecolor=SUPERFICIE,
                markeredgewidth=2 * PT, zorder=z + 1, label=etiqueta)


def _etiquetas_finales(ax, resumen: dict, ultimo: float) -> None:
    """Valor de la mediana al final de cada serie, con línea guía si hubo que separarlas."""
    puntos = [(clave, resumen[(clave, ultimo)]) for clave, *_ in ETAPAS]
    alturas = [ax.transData.transform((ultimo, r["mediana"]))[1] for _, r in puntos]
    destino = list(alturas)
    if abs(alturas[0] - alturas[1]) < SEPARACION_ETIQUETAS_PX:
        centro = sum(alturas) / 2
        signo = 1 if alturas[0] >= alturas[1] else -1
        destino = [centro + signo * SEPARACION_ETIQUETAS_PX / 2, centro - signo * SEPARACION_ETIQUETAS_PX / 2]
    for (clave, r), y_px, y_dest in zip(puntos, alturas, destino):
        buses = r["buses_mediana"]
        texto_buses = "1 bus menos" if buses == 1 else f"{buses:g} buses menos"
        guia = dict(arrowstyle="-", color=GRIS, linewidth=1 * PT, shrinkA=0, shrinkB=6) if y_dest != y_px else None
        ax.annotate(f"USD {miles(r['mediana'])}", xy=(ultimo, r["mediana"]), xycoords="data",
                    xytext=(16 * PT, (y_dest - y_px) * PT + 6 * PT), textcoords="offset points",
                    fontsize=21 * PT, fontweight="bold", color=TINTA, va="bottom", ha="left",
                    arrowprops=guia, annotation_clip=False)
        ax.annotate(texto_buses, xy=(ultimo, r["mediana"]), xycoords="data",
                    xytext=(16 * PT, (y_dest - y_px) * PT - 2 * PT), textcoords="offset points",
                    fontsize=19 * PT, color=TINTA_2, va="top", ha="left", annotation_clip=False)


def _textos(fig, repeticiones: int, original, equipo: str) -> None:
    izquierda = MARGEN_PX["izquierda"] / ANCHO_PX - 0.005
    fig.text(izquierda, 1 - 14 / ALTO_PX, "Ahorro sobre la construcción cronológica (USD/día)",
             fontsize=21 * PT, color=TINTA, fontweight="bold", ha="left", va="top")
    # Sin anillo: en la leyenda el anillo corta la línea y la hace ver punteada.
    asas = [Line2D([], [], color=c, linewidth=2.5 * PT, marker="o", markersize=10 * PT,
                   markeredgewidth=0) for _, _, c, _ in ETAPAS]
    nombres = [e for _, e, _, _ in ETAPAS]
    if original is not None:
        asas.append(Line2D([], [], linestyle="none", marker="D", markersize=9 * PT, markerfacecolor="none",
                           markeredgecolor=TINTA, markeredgewidth=1.5 * PT))
        nombres.append("Ensayo original")
    fig.legend(asas, nombres, loc="upper right", bbox_to_anchor=(1 - 4 / ANCHO_PX, 1 - 2 / ALTO_PX),
               ncol=len(asas), frameon=False, fontsize=20 * PT, handlelength=1.6, columnspacing=1.2,
               labelcolor=TINTA)
    eje = "Presupuesto de cada búsqueda (el mismo para parejas y para tríos)"
    fig.text(izquierda, 34 / ALTO_PX, f"{eje}, en {equipo}" if equipo else eje,
             fontsize=19 * PT, color=TINTA_2, ha="left", va="bottom")
    nota = (f"Línea: mediana de {repeticiones} corridas · banda: mínimo a máximo · puntos claros: cada corrida"
            if repeticiones > 1 else "Una corrida por presupuesto")
    fig.text(izquierda, 6 / ALTO_PX, nota, fontsize=17 * PT, color=TINTA_2, ha="left", va="bottom")


def dibujar(corridas: list, destino: Path, original=None, marca_agua: str = "", equipo: str = "") -> Path:
    resumen = resumir(corridas)
    presupuestos = sorted({c["presupuesto_s"] for c in corridas})
    repeticiones = max(r["n"] for r in resumen.values())
    tope = max(r["maximo"] for r in resumen.values())
    if original is not None:
        tope = max(tope, original["parejas_y_trios"]["ahorro_usd"])
    paso = 2000 if tope * 1.12 <= 12000 else 4000
    techo = paso * (int(tope * 1.12 // paso) + 1)
    fig, ax = _figura()
    # En otro equipo, 120 s no equivalen a la búsqueda del ensayo: no se destaca como «usado».
    _ejes(ax, presupuestos, techo, paso, None if equipo else PRESUPUESTO_USADO_S)
    _series(ax, corridas, resumen, presupuestos, repeticiones)
    if original is not None:
        ax.scatter([PRESUPUESTO_USADO_S], [original["parejas_y_trios"]["ahorro_usd"]], marker="D",
                   s=(9 * PT) ** 2, facecolors="none", edgecolors=TINTA, linewidths=1.5 * PT, zorder=9)
    _etiquetas_finales(ax, resumen, presupuestos[-1])
    _textos(fig, repeticiones, original, equipo)
    if marca_agua:
        fig.text(0.5, 0.5, marca_agua, fontsize=54 * PT, color=ROJO, alpha=0.22, rotation=12,
                 ha="center", va="center", fontweight="bold")
    fig.savefig(destino, dpi=DPI_SALIDA, transparent=True)
    plt.close(fig)
    return destino


def imprimir_resumen(corridas: list) -> None:
    resumen = resumir(corridas)
    base = corridas[0]
    print(f"Construcción: {base['buses_construccion']} buses, USD {miles(base['costo_construccion'])}")
    for b in sorted({c["presupuesto_s"] for c in corridas}):
        partes = []
        for clave, etiqueta, *_ in ETAPAS:
            r = resumen[(clave, b)]
            partes.append(f"{etiqueta}: USD {miles(r['mediana'])} [{miles(r['minimo'])}–{miles(r['maximo'])}], "
                          f"{r['buses_mediana']:g} buses")
        motivos = sorted({c[k]["motivo_fin"] for c in corridas if c["presupuesto_s"] == b
                          for k in ("parejas", "parejas_y_trios")})
        print(f"{b:g} s (n={resumen[('parejas', b)]['n']}): " + " | ".join(partes) + f" | fin: {', '.join(motivos)}")
    con_licencia = [c for c in corridas if "modelos_totales" in c]
    if con_licencia:
        totales = sum(c["modelos_totales"] for c in con_licencia)
        descartados = sum(c["modelos_descartados"] for c in con_licencia)
        print(f"Licencia gratuita: {descartados} de {totales} modelos descartados por tamaño "
              f"({100 * descartados / totales:.2f} %) en {len(con_licencia)} corridas")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--barrido", type=Path, default=BARRIDO)
    parser.add_argument("--png", type=Path, default=HERE / "grafico_presupuesto.png")
    parser.add_argument("--csv", type=Path, default=HERE / "resumen_barrido.csv")
    parser.add_argument("--con-ensayo-original", action="store_true")
    parser.add_argument("--marca-agua", default="", help="texto en diagonal, para vistas previas")
    parser.add_argument("--equipo", default="", help="dónde se corrió, para la nota (p. ej. «un Mac M1»)")
    args = parser.parse_args()
    corridas = leer_barrido(args.barrido)
    original = leer_corrida(ENSAYO_ORIGINAL) if args.con_ensayo_original else None
    escribir_csv(corridas, args.csv)
    imprimir_resumen(corridas)
    print(dibujar(corridas, args.png, original, args.marca_agua, args.equipo))


if __name__ == "__main__":
    main()
