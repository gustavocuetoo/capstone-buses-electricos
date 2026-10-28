#!/usr/bin/env bash
# Compila los documentos LaTeX de 04-documentos/ y deja los PDF en 04-documentos/pdf/.
# Uso:  ./compilar.sh              -> compila todos
#       ./compilar.sh analisis_datos -> compila solo uno
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p pdf

docs=("${@:-}")
if [[ -z "${1:-}" ]]; then
  docs=(analisis_datos bibliografia discusion_metodologica mapa_supuestos preguntas_profesor)
fi

for doc in "${docs[@]}"; do
  echo "==> $doc"
  pdflatex -interaction=nonstopmode -halt-on-error "$doc.tex" >/dev/null
  bibtex "$doc" >/dev/null || true
  pdflatex -interaction=nonstopmode -halt-on-error "$doc.tex" >/dev/null
  pdflatex -interaction=nonstopmode -halt-on-error "$doc.tex" >/dev/null
  mv "$doc.pdf" pdf/
done

rm -f ./*.aux ./*.log ./*.bbl ./*.blg ./*.toc ./*.out ./*.nav ./*.snm
echo "Listo. PDFs en 04-documentos/pdf/"
