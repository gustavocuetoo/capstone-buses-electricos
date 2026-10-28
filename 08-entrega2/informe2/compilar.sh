#!/bin/bash
# Compila el informe 2: cifras → figuras → LaTeX → revisor.
set -euo pipefail
cd "$(dirname "$0")"
python3 scripts/cifras.py
python3 scripts/figuras.py
latexmk -pdf -interaction=nonstopmode -halt-on-error informe2.tex
python3 scripts/revisar.py
