#!/usr/bin/env bash
# Compila la presentación. Requiere que 03-resultados/ esté generado:
#   python3 02-analisis-datos/analisis_datos.py && python3 02-analisis-datos/entrega1_kpis.py
set -euo pipefail
cd "$(dirname "$0")"
pdflatex -interaction=nonstopmode -halt-on-error presentacion1.tex >/dev/null
pdflatex -interaction=nonstopmode -halt-on-error presentacion1.tex >/dev/null
rm -f ./*.aux ./*.log ./*.nav ./*.snm ./*.out ./*.toc
echo "Listo: $(pwd)/presentacion1.pdf"
