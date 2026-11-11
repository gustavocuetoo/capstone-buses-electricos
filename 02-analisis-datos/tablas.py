#!/usr/bin/env python3
"""Escritura de tablas LaTeX generadas desde datos.

Mantiene el estilo definido en `04-documentos/estilo.tex` (encabezado
`headrow` + `\\thead`, filas alternas `softrow`, reglas de booktabs) para que
ninguna cifra del informe se escriba a mano.

Este módulo es una biblioteca: no se ejecuta solo.
"""

from __future__ import annotations

from pathlib import Path

ENCABEZADO_GENERADO = (
    "% Generado automáticamente -- NO editar a mano.\n"
    "% Volver a generar con:  python3 02-analisis-datos/entrega1_kpis.py\n"
)

SIMBOLO_ESTADO = {
    "ok": "\\textcolor{ink}{\\textbf{OK}}",
    "alerta": "\\textcolor{amber}{\\textbf{ALERTA}}",
    "falla": "\\textcolor{critred}{\\textbf{FALLA}}",
}


def escapar(texto: str) -> str:
    """Escapa los caracteres que LaTeX interpreta, salvo los ya marcados."""
    if "\\" in texto:
        return texto  # ya viene con macros LaTeX intencionales
    for crudo, seguro in (("&", "\\&"), ("%", "\\%"), ("_", "\\_"), ("#", "\\#")):
        texto = texto.replace(crudo, seguro)
    return texto


def escribir_tabla(
    destino: Path,
    columnas: str,
    cabeceras: list[str],
    filas: list[list[str]],
    entorno: str = "tabular",
) -> None:
    """Escribe un fragmento LaTeX con una tabla lista para \\input.

    No incluye `table` ni `caption`: eso lo decide el documento que la usa,
    para que la misma tabla sirva en el informe y en la presentación.
    """
    lineas = [ENCABEZADO_GENERADO.rstrip(), ""]
    apertura = f"\\begin{{{entorno}}}{{{columnas}}}"
    lineas.append(apertura)
    lineas.append("\\rowcolor{headrow}")
    lineas.append(" & ".join(f"\\thead{{{c}}}" for c in cabeceras) + " \\\\")
    lineas.append("\\midrule")

    for indice, fila in enumerate(filas):
        if indice % 2 == 1:
            lineas.append("\\rowcolor{softrow}")
        lineas.append(" & ".join(escapar(celda) for celda in fila) + " \\\\")

    lineas.append("\\bottomrule")
    lineas.append(f"\\end{{{entorno}}}")
    destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def escribir_macros(destino: Path, macros: dict[str, str]) -> None:
    """Escribe un archivo de \\newcommand para que el texto no lleve números."""
    lineas = [ENCABEZADO_GENERADO.rstrip(), ""]
    lineas += [f"\\newcommand{{\\{nombre}}}{{{valor}}}" for nombre, valor in macros.items()]
    destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")
