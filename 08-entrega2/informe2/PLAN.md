# Informe de la Entrega 2 — Plan de trabajo

> **Para agentes:** SUB-SKILL REQUERIDO: usar superpowers:subagent-driven-development (recomendado) o superpowers:executing-plans para ejecutar este plan tarea por tarea. Los pasos usan casillas (`- [ ]`) para seguir el avance.

**Objetivo:** dejar el informe de la Entrega 2 compilado en PDF el 15-oct-2026 en la tarde, con todas sus cifras generadas por script desde los resultados auditados, para que el grupo lo revise y se entregue el 16-oct.

**Arquitectura:** el informe es un proyecto LaTeX en `08-entrega2/informe2/`, con la plantilla `pucthesis` del grupo (11 pt). Unos scripts de Python en `scripts/` leen los resultados (JSON/CSV) del método híbrido y del caso base. Con eso generan `cifras.tex` (una macro por cifra), las tablas de `tablas/` y las figuras de `figures/`. `revisar.py` comprueba las reglas del esquema sobre el `.tex` y el PDF. Primero se construyen y prueban los scripts (TDD); después se redacta capítulo por capítulo en el orden del esquema.

**Herramientas:** Python 3.12 (`python3`, con numpy 2.4 y matplotlib 3.10; `unittest` de la biblioteca estándar), pdfLaTeX + latexmk + BibTeX con apacite, pdftotext y pdftoppm (poppler).

**Spec:** [`ESQUEMA.md`](ESQUEMA.md), en esta misma carpeta. Leerlo entero antes de empezar: cada tarea de redacción remite a una sección suya.

## Restricciones globales

Copiadas del esquema; valen para todas las tareas.

- **Páginas:** máximo 30, sin contar portada, índice, resumen, anexos ni bibliografía.
- **Plantilla:** `pucthesis.cls` en **11 pt**, en la versión del grupo, y sin otros cambios de configuración. Sí se permiten paquetes y rótulos.
- **Cifras:** ninguna se escribe a mano en `chapters/*.tex`. Todas salen de una macro de `cifras.tex` o de un archivo de `tablas/`.
- **Formato de números:** chileno (1.374.632; 14,1 %). Los negativos se escriben `\ensuremath{-}`.
- **Voz y términos:** voz impersonal. «Corrida» y nunca «viaje». Toda sigla y todo símbolo se definen la primera vez que aparecen.
- **Caso base oficial:** la política miope por ruta con recarga, usando **el reporte del auditor del híbrido** (Tarea 4).
- **Resultado principal:** el refinado, `metodo_hibrido/resultados/mejor_20261006_refinamiento/`. La red de 417 rutas queda fuera de los resultados; solo se usa en el capítulo 2 para comparar datos.
- **No se escribe nada dentro de `metodo_hibrido/`:** `ejecutar.py` registra la huella de cada `*.py` de esa carpeta. Tampoco se modifica `CODIGO apstone/output/`. Todo lo generado va a `08-entrega2/informe2/`.
- **Declaración de IA:** al final, como último anexo, marcada SÍ.
- **iCloud:** antes de leer un archivo, comprobar que no esté solo en la nube (`compressed,dataless`).
- **Git:** no se hace commit. El repositorio no tiene commits y no se pidió.

### Presupuesto de páginas físicas

En `pucthesis`, cada capítulo empieza en página nueva, así que el reparto del esquema (en medias páginas) se traduce a páginas físicas:

| Capítulo | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Páginas | 2 | 4 | 3 | 2 | 5 | 2 | 6 | 2 | 2 | 2 | 30 |

El total de 30 es un límite estricto. El de cada capítulo es una alerta.

## Pendientes de la autorrevisión (13-oct, corregir antes de ejecutar la tarea afectada)

- **Tarea 11, paso 3:** la tabla del GTFS a RED (427 → 417 rutas, 26.137 → 14.464 viajes del GTFS, etc.) no debe copiarse del deck. Las cifras aparecen en `02-codigo/figuras_informe.py`, y `03-resultados/` tiene las tablas que generó la Entrega 1 (`tabla_instancias.tex`, `tabla_calidad.tex`, `metricas_entrega1.tex`). Usar esas fuentes por `\input` o generar las macros desde `02-codigo/`.
- **Tarea 11, paso 4:** falta el código de la comparación entre muestra y red. Agregar en `cifras.py` una función `macros_muestra_vs_red(corridas, red)`: corridas por sector y km medio por corrida (`distancia_servicio_km`) en la muestra y en la red, con su prueba.
- **Tarea 13, paso 2:** falta el código que arma `tiempos` desde `distancias.csv` y escribe la macro `ConexionesFactibles`.
- **Tarea 15, paso 3:** la Carta Gantt va como tabla `tabularx`, con una columna por semana; no en TikZ.
- **Tarea 6:** confirmar que `muestra_212_trios/comparacion.json` tiene la clave `final` con `verificado`, y que los resúmenes de los umbrales tienen la clave `caso_base`.

## Focos de revisión

Fallas que ninguna prueba de una tarea en particular cubriría por sí sola, ordenadas por probabilidad. Cada una tiene su prueba en la tarea indicada.

1. **Un archivo fuente quedó solo en iCloud.** El script debe fallar al tiro con «archivo solo en iCloud: <ruta>», en vez de quedarse colgado leyendo. Prueba en la Tarea 3: `test_solo_nube_detecta_bandera`.
2. **Un resumen falta o no viene `"verificado": true`.** `cifras.py` debe abortar sin escribir `cifras.tex`, en vez de dejar cifras viejas. Prueba en la Tarea 3: `test_resumen_no_verificado_falla`.
3. **Las dos corridas del refinado no encadenan** (la etapa inicial del refinamiento ≠ la etapa final de la búsqueda de 600 s). Debe dar error, no una tabla de etapas inventada. Prueba en la Tarea 5: `test_etapas_que_no_encadenan_fallan`.
4. **Redondeos que producen «−0» o «-0,0 %», o separadores al revés.** Prueba en la Tarea 3: `test_cero_negativo_se_escribe_cero` y `test_formato_chileno`.
5. **Recargas con hora negativa (antes de medianoche) o mayor a 24 h** que caen en la hora equivocada del gráfico. Prueba en la Tarea 5: `test_energia_por_hora_envuelve_el_dia`.

---

### Tarea 1: Proyecto LaTeX que compila

**Archivos**
- Crear `08-entrega2/informe2/informe2.tex`, `compilar.sh`, `referencias.bib` y `chapters/*.tex` (16 archivos).
- Copiar `CODIGO apstone/informe/pucthesis.cls`, `apacite.sty`, `apacite.bst` y `figures/LogoUC.pdf`.

**Interfaces**
- Produce: el nombre de cada archivo de capítulo (las Tareas 8–16 escriben en ellos) y `compilar.sh` (las Tareas 2, 6 y 7 lo amplían).

- [ ] **Paso 1: copiar la plantilla del grupo y comprobar que es la de 11 pt.**

```bash
cd "08-entrega2/informe2" && mkdir -p chapters figures tablas salidas scripts
cp "../../CODIGO apstone/informe/pucthesis.cls" "../../CODIGO apstone/informe/apacite.sty" "../../CODIGO apstone/informe/apacite.bst" .
cp "../../CODIGO apstone/informe/figures/LogoUC.pdf" figures/
cp "../../04-documentos/referencias.bib" referencias.bib
sed -n '4p' pucthesis.cls
```

Esperado: `\LoadClass[oneside,reqno,11pt]{amsbook}`.

- [ ] **Paso 2: crear `informe2.tex`.** Se copian las líneas 1–66 de `CODIGO apstone/informe/Thesis.tex` (el preámbulo, hasta antes de `\begin{document}`) y se agregan `\usepackage{tikz}`, `\usetikzlibrary{positioning,arrows.meta}` y `\input{cifras.tex}` al final del preámbulo. Después va el cuerpo:

```latex
\begin{document}

\mdate{Octubre 2026}
\version{2}

\title[PLANIFICACIÓN DE LA OPERACIÓN DE BUSES ELÉCTRICOS EN LA REGIÓN METROPOLITANA\\ GRUPO 29]
   {\bf PLANIFICACIÓN DE LA OPERACIÓN DE BUSES ELÉCTRICOS EN LA REGIÓN METROPOLITANA\\ GRUPO 29}
\author[Integrantes:]{Integrantes:\\
\textnormal{\small{
Gonzalo Anguita\\
Diego Barrios\\
Gustavo Cueto\\
Nicolás Farías\\
Fernando González\\
Ricardo Palma\\
Cristóbal Rehbein}
}
}

\address{Escuela de Ingenier\'ia\\
                   Pontificia Universidad Cat\'olica de Chile\\
                   Vicu\~na Mackenna 4860\\
                  Santiago, Chile\\
                  {\it Tel.\/} : 56 (2) 354-2000}

\advisor                    {\textbf{Profesor Guía:} Agustín Chiu}
\ogrsmember                 {\textbf{Ayudante Tutor:} Max Burr}
\date                       {Octubre 2026}
\copyrightname              {Grupo 29}
\copyrightyear              {2026}

\NoChapterPageNumber
\pagenumbering{roman}
\maketitle

\pdfbookmark{\contentsname}{toc}
\tableofcontents
\phantomsection \label{listoffigures}
\listoffigures
\phantomsection \label{listoftables}
\listoftables
\cleardoublepage

\phantomsection \label{resumen}
\chapter*{RESUMEN}
\input{./chapters/resumen.tex}
\cleardoublepage

\pagenumbering{arabic}

\chapter[INTRODUCCIÓN]{Introducción} \label{ch:introduccion}
\input{./chapters/cap01_introduccion.tex}

\chapter[DESCRIPCIÓN DETALLADA DEL PROBLEMA Y DATOS]{Descripción detallada del problema y datos} \label{ch:problema}
\input{./chapters/cap02_problema_datos.tex}

\chapter[EVOLUCIÓN Y DISCUSIÓN METODOLÓGICA]{Evolución y discusión metodológica} \label{ch:evolucion}
\input{./chapters/cap03_evolucion.tex}

\chapter[CASO BASE]{Caso base} \label{ch:caso-base}
\input{./chapters/cap04_caso_base.tex}

\chapter[METODOLOGÍA HÍBRIDA PROPUESTA]{Metodología híbrida propuesta} \label{ch:metodologia}
\input{./chapters/cap05_metodologia.tex}

\chapter[IMPLEMENTACIÓN COMPUTACIONAL Y TRAZABILIDAD]{Implementación computacional y trazabilidad} \label{ch:implementacion}
\input{./chapters/cap06_implementacion.tex}

\chapter[RESULTADOS Y ANÁLISIS DE KPIS]{Resultados y análisis de KPIs} \label{ch:resultados}
\input{./chapters/cap07_resultados.tex}

\chapter[SUPUESTOS, RIESGOS Y PLAN DE SENSIBILIDAD]{Supuestos, riesgos y plan de sensibilidad} \label{ch:supuestos}
\input{./chapters/cap08_supuestos.tex}

\chapter[CONCLUSIONES]{Conclusiones} \label{ch:conclusiones}
\input{./chapters/cap09_conclusiones.tex}

\chapter[PASOS FUTUROS]{Pasos futuros} \label{ch:pasos-futuros}
\input{./chapters/cap10_pasos_futuros.tex}

\cleardoublepage
\phantomsection \label{references}
\bibliographystyle{apacite}
\renewcommand{\bibname}{REFERENCIAS}
\bibliography{referencias}

\appendix

\newpage
\section[Notación]{Notación} \label{an:notacion}
\input{./chapters/anexo_a_notacion.tex}

\newpage
\section[Correcciones respecto del informe 1 y la presentación]{Correcciones respecto del informe 1 y la presentación} \label{an:correcciones}
\input{./chapters/anexo_b_correcciones.tex}

\newpage
\section[Barrido de presupuesto de búsqueda]{Barrido de presupuesto de búsqueda} \label{an:barrido}
\input{./chapters/anexo_c_barrido.tex}

\newpage
\section[Parámetros del escenario]{Parámetros del escenario} \label{an:parametros}
\input{./chapters/anexo_d_parametros.tex}

\newpage
\section[Declaración de uso de IA]{Declaración de uso de IA en este informe y presentación asociada} \label{an:ia}
\input{./chapters/anexo_e_declaracion_ia.tex}

\end{document}
```

- [ ] **Paso 3: crear los 16 archivos de capítulo con un comentario que remite al esquema, y un `cifras.tex` mínimo.**

```bash
cd "08-entrega2/informe2"
for f in resumen cap01_introduccion cap02_problema_datos cap03_evolucion cap04_caso_base cap05_metodologia cap06_implementacion cap07_resultados cap08_supuestos cap09_conclusiones cap10_pasos_futuros anexo_a_notacion anexo_b_correcciones anexo_c_barrido anexo_d_parametros anexo_e_declaracion_ia; do
  printf '%% Se redacta según ESQUEMA.md. Archivo: %s\n' "$f" > "chapters/$f.tex"
done
printf '\\nocite{*}\n' >> chapters/cap03_evolucion.tex
printf '%% Lo genera scripts/cifras.py (Tarea 6). No editar a mano.\n' > cifras.tex
```

El `\nocite{*}` es temporal: evita que BibTeX falle sin citas. Se saca en la Tarea 14 y `revisar.py --final` lo rechaza.

- [ ] **Paso 4: crear `compilar.sh`.**

```bash
#!/bin/bash
# Compila el informe 2. Las Tareas 2, 6 y 7 agregan pasos antes y después de latexmk.
set -euo pipefail
cd "$(dirname "$0")"
latexmk -pdf -interaction=nonstopmode -halt-on-error informe2.tex
```

`chmod +x compilar.sh`.

- [ ] **Paso 5: compilar y revisar.**

Correr `./compilar.sh`. Esperado: termina con código 0 y deja `informe2.pdf`.

Después: `pdftotext informe2.pdf - | grep -nE "APPENDIX|Figure |Table |TABLE OF CONTENTS|LIST OF"`.
Esperado: ninguna línea.

Si aparecen rótulos en inglés, agregar justo después de `\begin{document}`: `\renewcommand{\appendixname}{ANEXOS}`, `\renewcommand{\figurename}{Figura}` y `\renewcommand{\tablename}{Tabla}`. Compilar de nuevo.

- [ ] **Paso 6: mirar la portada y el índice.** `pdftoppm -f 1 -l 3 -r 60 -png informe2.pdf salidas/vista` y abrir las imágenes. Esperado: título, 7 integrantes, Agustín Chiu, Max Burr, «Octubre 2026», 10 capítulos y 5 anexos en el índice.

### Tarea 2: Revisor de reglas (`revisar.py`)

**Archivos**
- Crear `scripts/revisar.py` y `scripts/test_revisar.py`.
- Modificar `compilar.sh`.

**Interfaces**
- Produce: `problemas_en_tex(nombre: str, texto: str) -> tuple[list[str], list[str]]` (errores, pendientes); `problemas_en_pdf(texto: str) -> list[str]`; `paginas_por_capitulo(toc: str) -> dict`; la línea de comando `python3 scripts/revisar.py [--final]`.

- [ ] **Paso 1: escribir las pruebas que fallan.**

```python
# scripts/test_revisar.py
import unittest

import revisar


class TestTex(unittest.TestCase):
    def test_numero_con_separador_de_miles_es_error(self):
        errores, _ = revisar.problemas_en_tex('cap', 'Se cubren 33.220 corridas.')
        self.assertEqual(len(errores), 1)

    def test_decimal_con_coma_es_error(self):
        errores, _ = revisar.problemas_en_tex('cap', 'El vacío es 16,6 por ciento.')
        self.assertEqual(len(errores), 1)

    def test_macros_y_enteros_simples_pasan(self):
        errores, _ = revisar.problemas_en_tex('cap', 'Usa \\BusesModelo{} buses en 5 sectores y 212 rutas.')
        self.assertEqual(errores, [])

    def test_comentarios_y_marca_literal_no_se_revisan(self):
        texto = '% 33.220 en comentario\nEl año 2.026 %literal\nPorcentaje 10\\% de 3 casos.'
        errores, _ = revisar.problemas_en_tex('cap', texto)
        self.assertEqual(errores, [])

    def test_coordenadas_tikz_no_son_cifras(self):
        texto = '\\begin{tikzpicture}\n\\node at (0,1.5) {A};\n\\end{tikzpicture}'
        errores, _ = revisar.problemas_en_tex('cap', texto)
        self.assertEqual(errores, [])

    def test_viaje_esta_prohibido(self):
        errores, _ = revisar.problemas_en_tex('cap', 'Cada viaje se cubre una vez.')
        self.assertEqual(len(errores), 1)

    def test_restos_de_plantilla_son_error(self):
        errores, _ = revisar.problemas_en_tex('main', '\\section{First Appendix}')
        self.assertEqual(len(errores), 1)

    def test_pendientes_se_informan_aparte(self):
        errores, pendientes = revisar.problemas_en_tex('cap', '\\nocite{*} y [POR COMPLETAR: responsables]')
        self.assertEqual(errores, [])
        self.assertEqual(len(pendientes), 2)


class TestPdf(unittest.TestCase):
    def test_referencias_rotas_y_rotulos_en_ingles(self):
        problemas = revisar.problemas_en_pdf('Ver Tabla ?? y la Figure 2.\nAPPENDIX')
        self.assertEqual(len(problemas), 3)

    def test_pdf_limpio(self):
        self.assertEqual(revisar.problemas_en_pdf('Ver la Tabla 7.1 y la Figura 2.1.'), [])


class TestPaginas(unittest.TestCase):
    TOC = (
        '\\contentsline {chapter}{RESUMEN}{vii}{chapter*.3}%\n'
        '\\contentsline {chapter}{\\numberline {1.}INTRODUCCI\\IeC {\\\'O}N}{1}{chapter.1}%\n'
        '\\contentsline {section}{\\numberline {1.1.}Contexto}{1}{section.1.1}%\n'
        '\\contentsline {chapter}{\\numberline {2.}DESCRIPCI\\IeC {\\\'O}N}{3}{chapter.2}%\n'
        '\\contentsline {chapter}{REFERENCIAS}{8}{chapter*.9}%\n'
    )

    def test_paginas_por_capitulo_hasta_referencias(self):
        paginas = revisar.paginas_por_capitulo(self.TOC)
        self.assertEqual(paginas, {'capitulos': {1: 2, 2: 5}, 'total': 7})

    def test_sin_referencias_es_error(self):
        with self.assertRaises(ValueError):
            revisar.paginas_por_capitulo('\\contentsline {chapter}{\\numberline {1.}A}{1}{chapter.1}%\n')


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Paso 2: correr las pruebas y ver que fallan.**

Correr `cd 08-entrega2/informe2 && python3 -m unittest discover -s scripts -p 'test_revisar.py' -v`.
Esperado: `ModuleNotFoundError: No module named 'revisar'`.

- [ ] **Paso 3: escribir `revisar.py`.**

```python
"""Revisa el .tex y el PDF del informe 2 contra las reglas de ESQUEMA.md."""
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parents[1]
LIMITE_PAGINAS = 30
PRESUPUESTO = {1: 2, 2: 4, 3: 3, 4: 2, 5: 5, 6: 2, 7: 6, 8: 2, 9: 2, 10: 2}
RESTOS_PLANTILLA = ('First Appendix', 'Short Story', 'selfie_monkey', 'Miembro 1',
                    'NOMBRE PROYECTO', 'GRUPO XX', 'Chapter 1', 'Lorem')
NUMERO_A_MANO = re.compile(r'(?<![\w\\.,])(?:\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+,\d+)(?![\w])')
PALABRA_PROHIBIDA = re.compile(r'\bviajes?\b', re.IGNORECASE)
COMENTARIO = re.compile(r'(?<!\\)%.*$')
MARCA_LITERAL = '%literal'
PENDIENTE = re.compile(r'\\nocite\{\*\}|\[POR COMPLETAR[^\]]*\]')
ENTRADA_TOC = re.compile(r'^\\contentsline\s*\{chapter\}\{(?P<titulo>.*)\}'
                         r'\{(?P<pagina>[^{}]*)\}\{[^{}]*\}%?\s*$')
CAPITULO = re.compile(r'\\numberline\s*\{(?P<n>\d+)\.?\}')
ROTULOS_INGLES = (re.compile(r'\bAPPENDIX\b'), re.compile(r'\bFigure \d'),
                  re.compile(r'\bTable \d'), re.compile(r'TABLE OF CONTENTS|LIST OF'))


def problemas_en_tex(nombre, texto):
    errores, pendientes = [], []
    en_tikz = False
    for numero, linea in enumerate(texto.splitlines(), start=1):
        lugar = f'{nombre}:{numero}'
        if '\\begin{tikzpicture}' in linea:
            en_tikz = True
        if PENDIENTE.search(linea):
            pendientes.append(f'{lugar}: pendiente «{PENDIENTE.search(linea).group(0)}»')
        codigo = '' if linea.rstrip().endswith(MARCA_LITERAL) else COMENTARIO.sub('', linea)
        if not en_tikz:
            for cifra in NUMERO_A_MANO.findall(codigo):
                errores.append(f'{lugar}: cifra escrita a mano «{cifra}»; usar una macro de cifras.tex')
        if PALABRA_PROHIBIDA.search(codigo):
            errores.append(f'{lugar}: usar «corrida», no «viaje»')
        for resto in RESTOS_PLANTILLA:
            if resto in codigo:
                errores.append(f'{lugar}: resto de la plantilla «{resto}»')
        if '\\end{tikzpicture}' in linea:
            en_tikz = False
    return errores, pendientes


def problemas_en_pdf(texto):
    problemas = []
    if '??' in texto:
        problemas.append('PDF: hay referencias o citas sin resolver («??»)')
    for patron in ROTULOS_INGLES:
        if patron.search(texto):
            problemas.append(f'PDF: rótulo en inglés «{patron.search(texto).group(0)}»')
    return problemas


def paginas_por_capitulo(toc):
    inicios, referencias = [], None
    for linea in toc.splitlines():
        entrada = ENTRADA_TOC.match(linea.strip())
        if not entrada or not entrada['pagina'].isdigit():
            continue
        capitulo = CAPITULO.search(entrada['titulo'])
        if capitulo:
            inicios.append((int(capitulo['n']), int(entrada['pagina'])))
        elif 'REFERENCIAS' in entrada['titulo']:
            referencias = int(entrada['pagina'])
    if referencias is None or not inicios:
        raise ValueError('El índice no tiene capítulos numerados o falta REFERENCIAS')
    finales = [inicio for _, inicio in inicios[1:]] + [referencias]
    capitulos = {n: fin - inicio for (n, inicio), fin in zip(inicios, finales)}
    return {'capitulos': capitulos, 'total': referencias - inicios[0][1]}


def main(final=False):
    errores, pendientes, alertas = [], [], []
    archivos = [AQUI / 'informe2.tex'] + sorted((AQUI / 'chapters').glob('*.tex'))
    for archivo in archivos:
        e, p = problemas_en_tex(archivo.name, archivo.read_text(encoding='utf-8'))
        errores += e
        pendientes += p
    texto_pdf = subprocess.run(['pdftotext', str(AQUI / 'informe2.pdf'), '-'],
                               capture_output=True, text=True, check=True).stdout
    errores += problemas_en_pdf(texto_pdf)
    paginas = paginas_por_capitulo((AQUI / 'informe2.toc').read_text(encoding='utf-8', errors='replace'))
    if paginas['total'] > LIMITE_PAGINAS:
        errores.append(f'Páginas: {paginas["total"]} > {LIMITE_PAGINAS}')
    for n, usadas in paginas['capitulos'].items():
        if usadas > PRESUPUESTO[n]:
            alertas.append(f'Capítulo {n}: {usadas} págs. (presupuesto {PRESUPUESTO[n]})')
    print(f'Páginas del cuerpo: {paginas["total"]} / {LIMITE_PAGINAS} · por capítulo: {paginas["capitulos"]}')
    for grupo, lineas in (('ERROR', errores), ('PENDIENTE', pendientes), ('ALERTA', alertas)):
        for linea in lineas:
            print(f'{grupo} {linea}')
    return 1 if errores or (final and pendientes) else 0


if __name__ == '__main__':
    sys.exit(main(final='--final' in sys.argv))
```

- [ ] **Paso 4: correr las pruebas y ver que pasan.** El mismo comando del Paso 2. Esperado: `OK`, 12 pruebas.

- [ ] **Paso 5: conectar el revisor a la compilación.** Agregar `python3 scripts/revisar.py` como última línea de `compilar.sh`. Correr `./compilar.sh`.

Esperado: «Páginas del cuerpo: 10 / 30» (un capítulo vacío por página) y `PENDIENTE cap03_evolucion.tex:2: pendiente «\nocite{*}»`. Código 0.

Si `paginas_por_capitulo` falla con el `informe2.toc` real, mirar su formato (`grep chapter informe2.toc`), agregar esa línea como caso de prueba y ajustar `ENTRADA_TOC` hasta que pase.

### Tarea 3: Formato de números y lectura segura de fuentes

**Archivos**
- Crear `scripts/formato.py`, `scripts/fuentes.py` y `scripts/test_formato_fuentes.py`.

**Interfaces**
- Produce:
  - `formato.numero(valor: float, decimales: int = 0) -> str`;
  - `formato.con_signo(valor: float, decimales: int = 0) -> str`;
  - `formato.delta(base: float, nuevo: float) -> tuple[float, float]` (diferencia y %);
  - `formato.macro(nombre: str, valor: str) -> str`;
  - `fuentes.es_solo_nube(banderas: int) -> bool`;
  - `fuentes.leer_json(ruta) -> dict`;
  - `fuentes.leer_csv(ruta) -> list[dict]`;
  - `fuentes.resumen_verificado(datos: dict, origen: str) -> dict`;
  - las constantes de rutas `fuentes.REFINADO`, `BUSQUEDA_600`, `MIOPE`, `MIOPE_UMBRAL`, `SIN_RECARGAS`, `PROTOTIPO`, `PROTOTIPO_MEJORADO`, `INSTANCIA`, `INSTANCIA_RED`, `BARRIDO`, `PARAMETROS` y `SALIDAS`.

- [ ] **Paso 1: escribir las pruebas que fallan.**

```python
# scripts/test_formato_fuentes.py
import tempfile
import unittest
from pathlib import Path

import formato
import fuentes


class TestFormato(unittest.TestCase):
    def test_formato_chileno(self):
        self.assertEqual(formato.numero(1374631.7037), '1.374.632')
        self.assertEqual(formato.numero(14.1048, 1), '14,1')
        self.assertEqual(formato.numero(0.75873, 2), '0,76')
        self.assertEqual(formato.numero(950), '950')

    def test_cero_negativo_se_escribe_cero(self):
        self.assertEqual(formato.numero(-0.0001), '0')
        self.assertEqual(formato.con_signo(-0.04, 1), '0,0')

    def test_signo_explicito(self):
        self.assertEqual(formato.con_signo(-636), '\\ensuremath{-}636')
        self.assertEqual(formato.con_signo(3462.4), '+3.462')

    def test_no_finito_falla(self):
        with self.assertRaises(ValueError):
            formato.numero(float('nan'))

    def test_delta(self):
        diferencia, porcentaje = formato.delta(4509, 3873)
        self.assertEqual(diferencia, -636)
        self.assertAlmostEqual(porcentaje, -14.1051, places=3)
        with self.assertRaises(ValueError):
            formato.delta(0, 5)

    def test_macro(self):
        self.assertEqual(formato.macro('BusesModelo', '3.873'), '\\newcommand{\\BusesModelo}{3.873}')
        with self.assertRaises(ValueError):
            formato.macro('Buses2', '1')


class TestFuentes(unittest.TestCase):
    def test_solo_nube_detecta_bandera(self):
        self.assertTrue(fuentes.es_solo_nube(0x40000000 | 0x20))
        self.assertFalse(fuentes.es_solo_nube(0x20))

    def test_archivo_faltante_falla_con_ruta(self):
        with self.assertRaisesRegex(FileNotFoundError, 'no_existe.json'):
            fuentes.leer_json(Path('/tmp/no_existe.json'))

    def test_resumen_no_verificado_falla(self):
        with self.assertRaisesRegex(ValueError, 'verificado'):
            fuentes.resumen_verificado({'buses': 3, 'verificado': False}, 'x.json')
        self.assertEqual(fuentes.resumen_verificado({'verificado': True, 'buses': 3}, 'x')['buses'], 3)

    def test_csv_con_bom(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'a.csv'
            ruta.write_text('\ufeffbus_id,km\nB1,2.5\n', encoding='utf-8')
            self.assertEqual(fuentes.leer_csv(ruta), [{'bus_id': 'B1', 'km': '2.5'}])


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Paso 2: correr y ver que fallan.** Correr `python3 -m unittest discover -s scripts -p 'test_formato_fuentes.py' -v`. Esperado: `ModuleNotFoundError: No module named 'formato'`.

- [ ] **Paso 3: escribir `formato.py`.**

```python
"""Números en formato chileno y macros LaTeX para cifras.tex."""
import math
import re

NOMBRE_MACRO = re.compile(r'^[A-Za-z]+$')


def numero(valor, decimales=0):
    if not math.isfinite(valor):
        raise ValueError(f'Cifra no finita: {valor}')
    redondeado = round(valor, decimales)
    if redondeado == 0:
        redondeado = 0.0
    texto = f'{redondeado:,.{decimales}f}'
    return texto.replace(',', '_').replace('.', ',').replace('_', '.')


def con_signo(valor, decimales=0):
    texto = numero(abs(valor), decimales)
    if round(valor, decimales) == 0:
        return texto
    return ('+' if valor > 0 else '\\ensuremath{-}') + texto


def delta(base, nuevo):
    if base == 0:
        raise ValueError('No se puede calcular un cambio porcentual con base cero')
    diferencia = nuevo - base
    return diferencia, 100 * diferencia / base


def macro(nombre, valor):
    if not NOMBRE_MACRO.match(nombre):
        raise ValueError(f'Nombre de macro inválido (solo letras): {nombre}')
    return f'\\newcommand{{\\{nombre}}}{{{valor}}}'
```

- [ ] **Paso 4: escribir `fuentes.py`.**

```python
"""Rutas de los resultados que usa el informe y lectura con validación."""
import csv
import json
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
REFINADO = RAIZ / 'metodo_hibrido/resultados/mejor_20261006_refinamiento'
BUSQUEDA_600 = RAIZ / 'metodo_hibrido/resultados/mejor_20261006_600'
MIOPE = RAIZ / 'CODIGO apstone/output/tres_fases/muestra_212_caso_base'
MIOPE_UMBRAL = {20: RAIZ / 'CODIGO apstone/output/tres_fases/muestra_212_caso_base_0.2',
                30: RAIZ / 'CODIGO apstone/output/tres_fases/muestra_212_caso_base_0.3',
                50: RAIZ / 'CODIGO apstone/output/tres_fases/muestra_212_caso_base_0.5'}
SIN_RECARGAS = RAIZ / 'caso_base_simple_gurobi/corrida_gurobi'
PROTOTIPO = RAIZ / 'CODIGO apstone/output/tres_fases/muestra_212'
PROTOTIPO_MEJORADO = RAIZ / 'CODIGO apstone/output/tres_fases/muestra_212_trios'
INSTANCIA = RAIZ / 'metodo_hibrido/instancia_212'
INSTANCIA_RED = RAIZ / 'metodo_hibrido/instancia_417'
BARRIDO = RAIZ / 'metodo_hibrido/resultados/presupuesto'
PARAMETROS = RAIZ / '01-datos/parameters.csv'
SALIDAS = Path(__file__).resolve().parents[1] / 'salidas'

BANDERA_SOLO_NUBE = 0x40000000  # SF_DATALESS de macOS: el contenido está solo en iCloud


def es_solo_nube(banderas):
    return bool(banderas & BANDERA_SOLO_NUBE)


def _comprobar(ruta):
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f'Falta el archivo fuente: {ruta}')
    if es_solo_nube(getattr(os.stat(ruta), 'st_flags', 0)):
        raise OSError(f'Archivo solo en iCloud (marcar «Mantener descargado»): {ruta}')
    return ruta


def leer_json(ruta):
    return json.loads(_comprobar(ruta).read_text(encoding='utf-8'))


def leer_csv(ruta):
    with _comprobar(ruta).open(encoding='utf-8-sig', newline='') as archivo:
        return list(csv.DictReader(archivo))


def resumen_verificado(datos, origen):
    if datos.get('verificado') is not True:
        raise ValueError(f'{origen} no viene marcado como verificado')
    return datos
```

- [ ] **Paso 5: correr y ver que pasan.** El comando del Paso 2. Esperado: `OK`, 10 pruebas.

### Tarea 4: Revisar el caso base miope con el auditor del híbrido (verificación 1)

**Archivos**
- Crear `scripts/auditar_miope.py` y `scripts/test_auditar_miope.py`.
- Produce `salidas/auditoria_miope.json`.

**Interfaces**
- Consume: `fuentes.leer_csv`, `fuentes.leer_json`, `fuentes.MIOPE`, `fuentes.INSTANCIA`, `fuentes.SALIDAS`; y `metodo_hibrido.verificar.verificar(schedules, trips, distances, starts, physical, plugs, tariffs, t0, horizon) -> (report, journeys, activities)`, sin modificarlo.
- Produce: `planes_desde_csv(actividades: list[dict], jornadas: list[dict]) -> list[dict]` en el formato de `planes.json`; y `salidas/auditoria_miope.json` con `{"aprobado": bool, "reporte": {...}, "diferencias": [...]}`. La Tarea 6 lee `reporte`.

- [ ] **Paso 1: escribir la prueba del adaptador, que falla.**

```python
# scripts/test_auditar_miope.py
import unittest

import auditar_miope

ACTIVIDADES = [
    {'bus_id': 'C1', 'orden': '2', 'tipo': 'servicio', 'origen': 'S:A', 'destino': 'S:B',
     'inicio_s': '0', 'fin_s': '600', 'distancia_km': '5.0', 'carga_kwh': '0.0', 'corrida_id': 'R1'},
    {'bus_id': 'C1', 'orden': '1', 'tipo': 'vacio', 'origen': 'T01', 'destino': 'S:A',
     'inicio_s': '-300', 'fin_s': '0', 'distancia_km': '1.5', 'carga_kwh': '0.0', 'corrida_id': ''},
    {'bus_id': 'C2', 'orden': '1', 'tipo': 'carga', 'origen': 'E1', 'destino': 'E1',
     'inicio_s': '100', 'fin_s': '400', 'distancia_km': '0.0', 'carga_kwh': '15.0', 'corrida_id': ''},
]
JORNADAS = [
    {'bus_id': 'C1', 'cadena_fase2': 'ruta:102', 'sector_id': '3', 'terminal_inicial': 'T01', 'terminal_final': 'T02'},
    {'bus_id': 'C2', 'cadena_fase2': 'ruta:103', 'sector_id': '1', 'terminal_inicial': 'T03', 'terminal_final': 'T03'},
]


class TestAdaptador(unittest.TestCase):
    def test_ordena_por_orden_y_convierte_tipos(self):
        planes = auditar_miope.planes_desde_csv(ACTIVIDADES, JORNADAS)
        c1 = planes[0]
        self.assertEqual([a['tipo'] for a in c1['actividades']], ['vacio', 'servicio'])
        self.assertEqual(c1['actividades'][0]['inicio_s'], -300)
        self.assertIsInstance(c1['actividades'][0]['distancia_km'], float)
        self.assertEqual(c1['corridas'], ['R1'])
        self.assertEqual(c1['sector_id'], '3')

    def test_bus_sin_actividades_es_error(self):
        with self.assertRaisesRegex(ValueError, 'C9'):
            auditar_miope.planes_desde_csv(ACTIVIDADES, JORNADAS + [dict(JORNADAS[0], bus_id='C9')])


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Paso 2: correr y ver que falla.** Correr `python3 -m unittest discover -s scripts -p 'test_auditar_miope.py' -v`. Esperado: `ModuleNotFoundError: No module named 'auditar_miope'`.

- [ ] **Paso 3: escribir `auditar_miope.py`.**

```python
"""Pasa el plan del caso base miope por el auditor del método híbrido, sin modificarlo."""
import json
import math
import sys
from collections import defaultdict

import fuentes

sys.path.insert(0, str(fuentes.RAIZ))
from metodo_hibrido.verificar import verificar  # noqa: E402

CLAVES_COMPARADAS = ('buses', 'corridas', 'km', 'carga_kwh', 'sesiones', 'costo_total_usd')
VELOCIDAD_VACIO_KMH = 18


def planes_desde_csv(actividades, jornadas):
    por_bus = defaultdict(list)
    for fila in actividades:
        por_bus[fila['bus_id']].append(fila)
    planes = []
    for jornada in jornadas:
        filas = sorted(por_bus.get(jornada['bus_id'], []), key=lambda f: int(f['orden']))
        if not filas:
            raise ValueError(f'El bus {jornada["bus_id"]} no tiene actividades')
        acts = [dict(tipo=f['tipo'], origen=f['origen'], destino=f['destino'],
                     inicio_s=int(float(f['inicio_s'])), fin_s=int(float(f['fin_s'])),
                     distancia_km=float(f['distancia_km']), carga_kwh=float(f['carga_kwh']),
                     corrida_id=f['corrida_id']) for f in filas]
        planes.append(dict(bus_id=jornada['bus_id'], cadena_fase2=jornada['cadena_fase2'],
                           sector_id=jornada['sector_id'], terminal_inicial=jornada['terminal_inicial'],
                           terminal_final=jornada['terminal_final'],
                           corridas=[a['corrida_id'] for a in acts if a['tipo'] == 'servicio'],
                           actividades=acts))
    return planes


def corridas_de_instancia():
    return [dict(corrida_id=r['corrida_id'], inicio_s=int(r['inicio_s']), fin_s=int(r['fin_s']),
                 inicio_stop_id=r['inicio_stop_id'], fin_stop_id=r['fin_stop_id'],
                 distancia_servicio_km=float(r['distancia_servicio_km']), sector_id=r['sector_id'])
            for r in fuentes.leer_csv(fuentes.INSTANCIA / 'corridas.csv')]


def distancias_de_instancia():
    distancias = {}
    for r in fuentes.leer_csv(fuentes.INSTANCIA / 'distancias.csv'):
        km = float(r['distancia_km']) if r['distancia_km'] else None
        distancias[r['origen_id'], r['destino_id']] = (
            None if km is None else (km, math.ceil(km * 3600 / VELOCIDAD_VACIO_KMH)))
    return distancias


def main():
    escenario = fuentes.leer_json(fuentes.INSTANCIA / 'escenario.json')
    planes = planes_desde_csv(fuentes.leer_csv(fuentes.MIOPE / 'actividades.csv'),
                              fuentes.leer_csv(fuentes.MIOPE / 'jornadas.csv'))
    esperado = fuentes.resumen_verificado(
        fuentes.leer_json(fuentes.MIOPE / 'resumen.json')['caso_base'], 'resumen del miope')
    try:
        reporte, _, _ = verificar(planes, corridas_de_instancia(), distancias_de_instancia(),
                                  escenario['terminales_espera'], escenario['capacidad_fisica'],
                                  escenario['conexiones'], [tuple(t) for t in escenario['tarifas']],
                                  escenario['inicio_horizonte_s'], escenario['fin_horizonte_s'])
    except Exception as error:  # el auditor señala la primera regla que no se cumple
        resultado = dict(aprobado=False, error=f'{type(error).__name__}: {error}')
    else:
        diferencias = [dict(clave=k, auditor=reporte[k], miope=esperado[k]) for k in CLAVES_COMPARADAS
                       if not math.isclose(reporte[k], esperado[k], rel_tol=1e-9, abs_tol=1e-6)]
        resultado = dict(aprobado=reporte.get('verificado') is True and not diferencias,
                         reporte=reporte, diferencias=diferencias)
    fuentes.SALIDAS.mkdir(exist_ok=True)
    (fuentes.SALIDAS / 'auditoria_miope.json').write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in resultado.items() if k != 'reporte'}, ensure_ascii=False))
    return 0 if resultado['aprobado'] else 1


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Paso 4: correr las pruebas y ver que pasan.** El comando del Paso 2. Esperado: `OK`, 2 pruebas.

- [ ] **Paso 5: auditar el miope de verdad.** Correr `python3 scripts/auditar_miope.py`.

Esperado: `{"aprobado": true, "diferencias": []}` y código 0.

**Si sale `aprobado: false`, DETENERSE.** Mostrarle a la usuaria el error o las diferencias, y no seguir con las Tareas 6–8 hasta que decida. Las opciones son:
- (a) usar las cifras del auditor del híbrido y explicar la diferencia;
- (b) declarar que el miope se auditó con `tres_fases/verificar.py`.

### Tarea 5: Análisis — cotas, etapas, energía, espera y recarga nocturna

**Archivos**
- Crear `scripts/analisis.py` y `scripts/test_analisis.py`.

**Interfaces**
- Produce:
  - `simultaneidad_maxima(intervalos: list[tuple[int, int]]) -> tuple[int, int | None]`;
  - `etapas(filas_600: list[dict], filas_refinado: list[dict]) -> list[dict]` (claves `etapa`, `buses`, `costo`);
  - `energia_por_hora(recargas: list[dict]) -> list[float]` (24 valores);
  - `tarifa_en_hora(tarifas: list, hora: int) -> float`;
  - `estimacion_nocturna(jornadas, bateria_kwh, potencia_kw, conexiones_totales) -> dict`;
  - `minutos_espera_en_servicio(actividades: list[dict]) -> float`.

- [ ] **Paso 1: escribir las pruebas que fallan.**

```python
# scripts/test_analisis.py
import unittest

import analisis


def fila(etapa, buses, costo):
    return {'etapa': etapa, 'buses': str(buses), 'costo_total_usd': str(costo)}


class TestAnalisis(unittest.TestCase):
    def test_simultaneidad_intervalos_semiabiertos(self):
        self.assertEqual(analisis.simultaneidad_maxima([(0, 10), (5, 15), (10, 20)]), (2, 5))
        self.assertEqual(analisis.simultaneidad_maxima([(0, 10), (10, 20)]), (1, 0))
        self.assertEqual(analisis.simultaneidad_maxima([]), (0, None))

    def test_etapas_encadenadas(self):
        a = [fila('inicial', 4014, 1415348.7), fila('01_pares', 3989, 1403067.6), fila('01_trios', 3884, 1378806.9)]
        b = [fila('inicial', 3884, 1378806.9), fila('01_pares', 3884, 1377062.9), fila('01_trios', 3873, 1374631.7)]
        resultado = analisis.etapas(a, b)
        self.assertEqual([e['etapa'] for e in resultado], ['construccion', 'parejas', 'trios', 'refinamiento'])
        self.assertEqual([e['buses'] for e in resultado], [4014, 3989, 3884, 3873])

    def test_etapas_que_no_encadenan_fallan(self):
        a = [fila('inicial', 4014, 1.0), fila('01_pares', 3989, 1.0), fila('01_trios', 3884, 1.0)]
        b = [fila('inicial', 3900, 1.0), fila('01_pares', 3890, 1.0), fila('01_trios', 3873, 1.0)]
        with self.assertRaisesRegex(ValueError, 'no encadenan'):
            analisis.etapas(a, b)

    def test_energia_por_hora_envuelve_el_dia(self):
        recargas = [{'inicio_s': '-600', 'carga_kwh': '15'}, {'inicio_s': '90000', 'carga_kwh': '5'},
                    {'inicio_s': '3600', 'carga_kwh': '2.5'}]
        horas = analisis.energia_por_hora(recargas)
        self.assertEqual(len(horas), 24)
        self.assertEqual(horas[23], 15.0)
        self.assertEqual(horas[1], 7.5)

    def test_tarifa_en_hora(self):
        tarifas = [[0, 8, 0.1], [8, 14, 0.15], [22, 24, 0.11]]
        self.assertEqual(analisis.tarifa_en_hora(tarifas, 3), 0.1)
        self.assertEqual(analisis.tarifa_en_hora(tarifas, 23), 0.11)
        with self.assertRaises(ValueError):
            analisis.tarifa_en_hora(tarifas, 15)

    def test_estimacion_nocturna(self):
        jornadas = [{'energia_final_kwh': '350'}, {'energia_final_kwh': '35'}, {'energia_final_kwh': '170'}]
        r = analisis.estimacion_nocturna(jornadas, bateria_kwh=350, potencia_kw=180, conexiones_totales=1)
        self.assertEqual(r['buses_con_deficit'], 2)
        self.assertAlmostEqual(r['deficit_kwh'], 495.0)
        self.assertAlmostEqual(r['horas_si_todas_las_conexiones'], 2.75)
        self.assertAlmostEqual(r['horas_bus_mas_vacio'], 1.75)
        self.assertEqual(r['rondas_de_carga'], 2)

    def test_espera_solo_entre_primera_y_ultima_corrida(self):
        actividades = [
            {'bus_id': 'B', 'tipo': 'espera', 'inicio_s': '-100', 'fin_s': '0'},
            {'bus_id': 'B', 'tipo': 'servicio', 'inicio_s': '0', 'fin_s': '600'},
            {'bus_id': 'B', 'tipo': 'espera', 'inicio_s': '600', 'fin_s': '1200'},
            {'bus_id': 'B', 'tipo': 'servicio', 'inicio_s': '1200', 'fin_s': '1800'},
            {'bus_id': 'B', 'tipo': 'espera', 'inicio_s': '1800', 'fin_s': '9000'},
        ]
        self.assertEqual(analisis.minutos_espera_en_servicio(actividades), 10.0)


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Paso 2: correr y ver que fallan.** Correr `python3 -m unittest discover -s scripts -p 'test_analisis.py' -v`. Esperado: `ModuleNotFoundError: No module named 'analisis'`.

- [ ] **Paso 3: escribir `analisis.py`.**

```python
"""Cálculos sobre los planes exportados que el informe necesita y no vienen en los resúmenes."""
import math
from collections import defaultdict

SEGUNDOS_DIA = 86_400
TOLERANCIA_USD = 1e-6
NOMBRES_ETAPAS = ('construccion', 'parejas', 'trios', 'refinamiento')


def simultaneidad_maxima(intervalos):
    eventos = defaultdict(int)
    for inicio, fin in intervalos:
        eventos[inicio] += 1
        eventos[fin] -= 1
    actual = pico = 0
    segundo = None
    for instante, cambio in sorted(eventos.items()):
        actual += cambio
        if actual > pico:
            pico, segundo = actual, instante
    return pico, segundo


def _etapa(filas, nombre):
    for f in filas:
        if f['etapa'] == nombre:
            return int(f['buses']), float(f['costo_total_usd'])
    raise ValueError(f'Falta la etapa {nombre}')


def etapas(filas_600, filas_refinado):
    construccion, parejas, trios = (_etapa(filas_600, n) for n in ('inicial', '01_pares', '01_trios'))
    inicio_refinado = _etapa(filas_refinado, 'inicial')
    if inicio_refinado[0] != trios[0] or abs(inicio_refinado[1] - trios[1]) > TOLERANCIA_USD:
        raise ValueError('Las corridas no encadenan: el refinamiento no parte del final de la búsqueda de 600 s')
    refinamiento = _etapa(filas_refinado, '01_trios')
    return [dict(etapa=n, buses=b, costo=c)
            for n, (b, c) in zip(NOMBRES_ETAPAS, (construccion, parejas, trios, refinamiento))]


def energia_por_hora(recargas):
    horas = [0.0] * 24
    for fila in recargas:
        hora = (int(float(fila['inicio_s'])) % SEGUNDOS_DIA) // 3600
        horas[hora] += float(fila['carga_kwh'])
    return horas


def tarifa_en_hora(tarifas, hora):
    for desde, hasta, precio in tarifas:
        if desde <= hora < hasta:
            return precio
    raise ValueError(f'Ninguna tarifa cubre la hora {hora}')


def estimacion_nocturna(jornadas, bateria_kwh, potencia_kw, conexiones_totales):
    deficits = [bateria_kwh - float(j['energia_final_kwh']) for j in jornadas]
    con_deficit = [d for d in deficits if d > 1e-9]
    total = sum(con_deficit)
    return dict(deficit_kwh=total, buses_con_deficit=len(con_deficit),
                horas_si_todas_las_conexiones=total / (potencia_kw * conexiones_totales),
                horas_bus_mas_vacio=max(con_deficit, default=0.0) / potencia_kw,
                rondas_de_carga=math.ceil(len(con_deficit) / conexiones_totales))


def minutos_espera_en_servicio(actividades):
    por_bus = defaultdict(list)
    for fila in actividades:
        por_bus[fila['bus_id']].append(fila)
    segundos = 0
    for filas in por_bus.values():
        servicios = [f for f in filas if f['tipo'] == 'servicio']
        if not servicios:
            continue
        primero = min(int(float(f['inicio_s'])) for f in servicios)
        ultimo = max(int(float(f['fin_s'])) for f in servicios)
        for f in filas:
            if f['tipo'] == 'espera':
                desde = max(int(float(f['inicio_s'])), primero)
                hasta = min(int(float(f['fin_s'])), ultimo)
                segundos += max(0, hasta - desde)
    return segundos / 60
```

- [ ] **Paso 4: correr y ver que pasan.** El comando del Paso 2. Esperado: `OK`, 8 pruebas.

### Tarea 6: `cifras.py` — todas las cifras del informe como macros

**Archivos**
- Crear `scripts/cifras.py` y `scripts/test_cifras_reales.py`.
- Modificar `compilar.sh`.
- Genera `cifras.tex` y `tablas/barrido.tex`.

**Interfaces**
- Consume: `formato.*`, `fuentes.*`, `analisis.*` y `salidas/auditoria_miope.json` (de la Tarea 4).
- Produce: estas macros, que usan las Tareas 8–16. Los nombres solo llevan letras; `{P}` es `Base` (miope) o `Modelo` (refinado).

| Grupo | Macros |
|---|---|
| KPIs por plan | `Buses{P}`, `Costo{P}`, `CostoFlota{P}`, `CostoKm{P}`, `CostoEnergia{P}`, `CostoSesiones{P}`, `PctFlota{P}`, `PctKm{P}`, `PctEnergia{P}`, `PctSesiones{P}`, `Km{P}`, `KmVacio{P}`, `PctVacio{P}`, `Energia{P}`, `Sesiones{P}` |
| Cambios | `Delta{X}` y `DeltaPct{X}`, con X en `Buses`, `Costo`, `CostoFlota`, `CostoKm`, `CostoEnergia`, `CostoSesiones`, `KmVacio`, `Energia`, `Sesiones`; y `DeltaPpVacio` |
| Electroterminales | `Plazas{E}{P}`, `Conexiones{E}{P}` y `Capacidad{E}`, con E en `EUno`…`ECinco`; `PlazasTotales` |
| Caso base sin recargas | `BusesSinRecargas`, `CostoSinRecargas` |
| Umbral del miope | `BusesUmbral{U}`, `CostoUmbral{U}` y `PctVacioUmbral{U}`, con U en `Veinte`, `Treinta`, `Cincuenta` |
| Etapas | `BusesConstruccion`, `CostoConstruccion`, `BusesParejas`, `CostoParejas`, `BusesTrios`, `CostoTrios`, `AhorroBusesConstruccion`, `AhorroBusesBusqueda`, `PctAhorroConstruccion` |
| Cotas | `CotaSimultaneidad`, `HoraCotaSimultaneidad`, `PisoFaseUno`, `FlotaFaseUno`, `BrechaCostoPiso`, `BrechaBusesFaseUno`, `BrechaBusesSimultaneidad` |
| Prototipo (cap. 3) | `NodosFaseUno`, `ArcosFaseUno`, `BusesPrototipoSinMejora`, `BusesPrototipo` |
| Energía final | `TarifaNocturna`, `Deficit{P}`, `CostoAjustado{P}`, `DeltaCostoAjustado`, `DeltaPctCostoAjustado` |
| Recarga nocturna | `BusesConDeficit`, `HorasCargaParalelo`, `HorasBusMasVacio`, `RondasCarga` |
| Espera | `CostoEsperaMinuto`, `MinutosEspera{P}`, `CostoEspera{P}`, `CostoConEspera{P}`, `DeltaPctCostoConEspera` |
| Instancia | `RutasMuestra`, `CorridasMuestra`, `RutasRed`, `CorridasRed`, `PctRutasMuestra`, `PctCorridasMuestra` |
| Parámetros | `Bateria`, `Reserva`, `Consumo`, `Potencia`, `EnergiaBloque`, `Autonomia`, `CostoBus`, `CostoKmUnit`, `CostoSesion`, `VelocidadVacio` |
| Cómputo | `MinutosRefinado`, `ModelosLocales`, `ModelosDescartados` |
| Barrido | `MedianaAhorro{B}` y `MedianaBusesEvitados{B}`, con B en `Quince`, `Treinta`, `Sesenta`, `CientoVeinte`, `DosCuarenta` |

- [ ] **Paso 1: escribir la prueba con cifras conocidas, que falla.** Esta prueba ata el script a los datos reales: si alguien apunta a otra carpeta, falla.

```python
# scripts/test_cifras_reales.py
import re
import unittest

import cifras


class TestCifrasReales(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.macros = cifras.calcular()

    def test_cifras_conocidas(self):
        self.assertEqual(self.macros['BusesModelo'], '3.873')
        self.assertEqual(self.macros['CostoModelo'], '1.374.632')
        self.assertEqual(self.macros['BusesSinRecargas'], '5.150')
        self.assertEqual(self.macros['BusesConstruccion'], '4.014')
        self.assertEqual(self.macros['BusesPrototipo'], '4.175')
        self.assertEqual(self.macros['PisoFaseUno'], '1.278.245')
        self.assertEqual(self.macros['MinutosRefinado'], '28,6')

    def test_todas_las_macros_son_validas(self):
        for nombre, valor in self.macros.items():
            self.assertRegex(nombre, r'^[A-Za-z]+$')
            self.assertNotIn('nan', valor)
            self.assertFalse(re.search(r'\d\.\d{1,2}$', valor), f'{nombre}={valor} parece punto decimal')


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Paso 2: correr y ver que falla.** Correr `python3 -m unittest discover -s scripts -p 'test_cifras_reales.py' -v`. Esperado: `ModuleNotFoundError: No module named 'cifras'`.

- [ ] **Paso 3: escribir `cifras.py`.**

```python
"""Genera cifras.tex (una macro por cifra) y tablas/barrido.tex desde los resultados auditados."""
import statistics
import sys
from pathlib import Path

import analisis
import fuentes
from formato import con_signo, delta, macro, numero

AQUI = Path(__file__).resolve().parents[1]
NUMERALES = {'1': 'Uno', '2': 'Dos', '3': 'Tres', '4': 'Cuatro', '5': 'Cinco'}
UMBRALES = {20: 'Veinte', 30: 'Treinta', 50: 'Cincuenta'}
PRESUPUESTOS = {15: 'Quince', 30: 'Treinta', 60: 'Sesenta', 120: 'CientoVeinte', 240: 'DosCuarenta'}
COMPONENTES = {'Flota': 'costo_buses_usd', 'Km': 'costo_km_usd',
               'Energia': 'costo_energia_usd', 'Sesiones': 'costo_sesiones_usd'}
HORA_TARIFA_NOCTURNA = 3


def kpis(resumen, jornadas):
    km_vacio = sum(float(j['km_vacio']) for j in jornadas)
    return dict(Buses=resumen['buses'], Costo=resumen['costo_total_usd'],
                CostoFlota=resumen['costo_buses_usd'], CostoKm=resumen['costo_km_usd'],
                CostoEnergia=resumen['costo_energia_usd'], CostoSesiones=resumen['costo_sesiones_usd'],
                Km=resumen['km'], KmVacio=km_vacio, PctVacio=100 * km_vacio / resumen['km'],
                Energia=resumen['carga_kwh'], Sesiones=resumen['sesiones'])


def macros_de_plan(m, sufijo, k, resumen):
    for clave in ('Buses', 'Costo', 'CostoFlota', 'CostoKm', 'CostoEnergia', 'CostoSesiones',
                  'Km', 'KmVacio', 'Energia', 'Sesiones'):
        m[clave + sufijo] = numero(k[clave])
    m['PctVacio' + sufijo] = numero(k['PctVacio'], 1)
    for nombre, campo in COMPONENTES.items():
        m[f'Pct{nombre}{sufijo}'] = numero(100 * resumen[campo] / resumen['costo_total_usd'], 1)
    for e, cap in resumen['capacidades'].items():
        letra = 'E' + NUMERALES[e[1:]]
        m[f'Plazas{letra}{sufijo}'] = numero(cap['ocupacion_maxima'])
        m[f'Conexiones{letra}{sufijo}'] = numero(cap['cargas_simultaneas_maximas'])
        m[f'Capacidad{letra}'] = numero(cap['capacidad_fisica'])


def calcular():
    m = {}
    escenario = fuentes.leer_json(fuentes.INSTANCIA / 'escenario.json')
    p = escenario['parametros']
    auditoria = fuentes.leer_json(fuentes.SALIDAS / 'auditoria_miope.json')
    if not auditoria.get('aprobado'):
        raise ValueError('La auditoría del miope no está aprobada (Tarea 4)')
    base = fuentes.resumen_verificado(auditoria['reporte'], 'auditoria_miope.json')
    modelo = fuentes.resumen_verificado(fuentes.leer_json(fuentes.REFINADO / '04_final/resumen.json'), 'refinado')
    jornadas_base = fuentes.leer_csv(fuentes.MIOPE / 'jornadas.csv')
    jornadas_modelo = fuentes.leer_csv(fuentes.REFINADO / '04_final/jornadas.csv')
    k_base, k_modelo = kpis(base, jornadas_base), kpis(modelo, jornadas_modelo)
    macros_de_plan(m, 'Base', k_base, base)
    macros_de_plan(m, 'Modelo', k_modelo, modelo)
    for clave in ('Buses', 'Costo', 'CostoFlota', 'CostoKm', 'CostoEnergia', 'CostoSesiones',
                  'KmVacio', 'Energia', 'Sesiones'):
        diferencia, pct = delta(k_base[clave], k_modelo[clave])
        m['Delta' + clave], m['DeltaPct' + clave] = con_signo(diferencia), con_signo(pct, 1)
    m['DeltaPpVacio'] = con_signo(k_modelo['PctVacio'] - k_base['PctVacio'], 1)
    m['PlazasTotales'] = numero(sum(escenario['capacidad_fisica'].values()))

    sin_recargas = fuentes.resumen_verificado(fuentes.leer_json(fuentes.SIN_RECARGAS / 'resumen.json'), 'sin recargas')
    m['BusesSinRecargas'], m['CostoSinRecargas'] = numero(sin_recargas['buses']), numero(sin_recargas['costo_total_usd'])
    for umbral, nombre in UMBRALES.items():
        carpeta = fuentes.MIOPE_UMBRAL[umbral]
        r = fuentes.resumen_verificado(fuentes.leer_json(carpeta / 'resumen.json')['caso_base'], f'umbral {umbral}')
        k = kpis(r, fuentes.leer_csv(carpeta / 'jornadas.csv'))
        m[f'BusesUmbral{nombre}'], m[f'CostoUmbral{nombre}'] = numero(k['Buses']), numero(k['Costo'])
        m[f'PctVacioUmbral{nombre}'] = numero(k['PctVacio'], 1)

    etapas = analisis.etapas(fuentes.leer_csv(fuentes.BUSQUEDA_600 / 'comparacion_etapas.csv'),
                             fuentes.leer_csv(fuentes.REFINADO / 'comparacion_etapas.csv'))
    por_nombre = {e['etapa']: e for e in etapas}
    if por_nombre['refinamiento']['buses'] != modelo['buses']:
        raise ValueError('La última etapa no coincide con el resumen del refinado')
    for etiqueta, nombre in (('Construccion', 'construccion'), ('Parejas', 'parejas'), ('Trios', 'trios')):
        m['Buses' + etiqueta] = numero(por_nombre[nombre]['buses'])
        m['Costo' + etiqueta] = numero(por_nombre[nombre]['costo'])
    ahorro_total = base['buses'] - modelo['buses']
    ahorro_construccion = base['buses'] - por_nombre['construccion']['buses']
    m['AhorroBusesConstruccion'] = numero(ahorro_construccion)
    m['AhorroBusesBusqueda'] = numero(por_nombre['construccion']['buses'] - modelo['buses'])
    m['PctAhorroConstruccion'] = numero(100 * ahorro_construccion / ahorro_total, 1)

    corridas = fuentes.leer_csv(fuentes.INSTANCIA / 'corridas.csv')
    pico, segundo = analisis.simultaneidad_maxima([(int(c['inicio_s']), int(c['fin_s'])) for c in corridas])
    prototipo = fuentes.leer_json(fuentes.PROTOTIPO / 'resumen.json')
    fase1, fase2 = prototipo['fase1'], prototipo['fase2']
    if not fase1['optimo_demostrado']:
        raise ValueError('La Fase 1 del prototipo no tiene óptimo demostrado: no sirve como cota')
    m['CotaSimultaneidad'] = numero(pico)
    m['HoraCotaSimultaneidad'] = f'{(segundo // 3600) % 24:02d}:{(segundo % 3600) // 60:02d}'
    m['PisoFaseUno'], m['FlotaFaseUno'] = numero(fase1['objetivo_usd']), numero(fase2['flota'])
    m['BrechaCostoPiso'] = numero(100 * (modelo['costo_total_usd'] / fase1['objetivo_usd'] - 1), 1)
    m['BrechaBusesFaseUno'] = numero(100 * (modelo['buses'] / fase2['flota'] - 1), 1)
    m['BrechaBusesSimultaneidad'] = numero(100 * (modelo['buses'] / pico - 1), 1)
    m['NodosFaseUno'], m['ArcosFaseUno'] = numero(fase1['nodos']), numero(fase1['arcos'])
    m['BusesPrototipoSinMejora'] = numero(prototipo['fase3']['buses'])
    mejorado = fuentes.leer_json(fuentes.PROTOTIPO_MEJORADO / 'comparacion.json')
    m['BusesPrototipo'] = numero(fuentes.resumen_verificado(mejorado['final'], 'prototipo mejorado')['buses'])

    tarifa = analisis.tarifa_en_hora(escenario['tarifas'], HORA_TARIFA_NOCTURNA)
    m['TarifaNocturna'] = numero(tarifa, 2)
    ajustado = {}
    for sufijo, jornadas, k in (('Base', jornadas_base, k_base), ('Modelo', jornadas_modelo, k_modelo)):
        noche = analisis.estimacion_nocturna(jornadas, p['bateria_kwh'], p['potencia_kw'],
                                             sum(escenario['conexiones'].values()))
        ajustado[sufijo] = k['Costo'] + noche['deficit_kwh'] * tarifa
        m['Deficit' + sufijo], m['CostoAjustado' + sufijo] = numero(noche['deficit_kwh']), numero(ajustado[sufijo])
        if sufijo == 'Modelo':
            m['BusesConDeficit'] = numero(noche['buses_con_deficit'])
            m['HorasCargaParalelo'] = numero(noche['horas_si_todas_las_conexiones'], 1)
            m['HorasBusMasVacio'] = numero(noche['horas_bus_mas_vacio'], 1)
            m['RondasCarga'] = numero(noche['rondas_de_carga'])
    diferencia, pct = delta(ajustado['Base'], ajustado['Modelo'])
    m['DeltaCostoAjustado'], m['DeltaPctCostoAjustado'] = con_signo(diferencia), con_signo(pct, 1)

    costo_minuto = float({r['parameter']: r['value'] for r in fuentes.leer_csv(fuentes.PARAMETROS)}['waiting_cost_per_min'])
    m['CostoEsperaMinuto'] = numero(costo_minuto, 2)
    con_espera = {}
    for sufijo, carpeta, k in (('Base', fuentes.MIOPE, k_base), ('Modelo', fuentes.REFINADO / '04_final', k_modelo)):
        minutos = analisis.minutos_espera_en_servicio(fuentes.leer_csv(carpeta / 'actividades.csv'))
        con_espera[sufijo] = k['Costo'] + minutos * costo_minuto
        m['MinutosEspera' + sufijo] = numero(minutos)
        m['CostoEspera' + sufijo] = numero(minutos * costo_minuto)
        m['CostoConEspera' + sufijo] = numero(con_espera[sufijo])
    m['DeltaPctCostoConEspera'] = con_signo(delta(con_espera['Base'], con_espera['Modelo'])[1], 1)

    red = fuentes.leer_csv(fuentes.INSTANCIA_RED / 'corridas.csv')
    rutas_muestra, rutas_red = len({c['route_id'] for c in corridas}), len({c['route_id'] for c in red})
    m['RutasMuestra'], m['CorridasMuestra'] = numero(rutas_muestra), numero(len(corridas))
    m['RutasRed'], m['CorridasRed'] = numero(rutas_red), numero(len(red))
    m['PctRutasMuestra'] = numero(100 * rutas_muestra / rutas_red, 1)
    m['PctCorridasMuestra'] = numero(100 * len(corridas) / len(red), 1)

    m['Bateria'], m['Reserva'] = numero(p['bateria_kwh']), numero(p['reserva_kwh'])
    m['Consumo'], m['Potencia'] = numero(p['consumo_kwh_km'], 1), numero(p['potencia_kw'])
    m['EnergiaBloque'] = numero(p['potencia_kw'] * p['bloque_s'] / 3600)
    m['Autonomia'] = numero((p['bateria_kwh'] - p['reserva_kwh']) / p['consumo_kwh_km'])
    m['CostoBus'], m['CostoKmUnit'] = numero(p['costo_bus']), numero(p['costo_km'], 1)
    m['CostoSesion'], m['VelocidadVacio'] = numero(p['costo_sesion']), numero(p['velocidad_vacio_kmh'])

    segundos = sum(fuentes.leer_json(c / 'comparacion.json')['tiempo_total_s'] for c in (fuentes.BUSQUEDA_600, fuentes.REFINADO))
    licencias = [fuentes.leer_json(c / 'licencia.json') for c in (fuentes.BUSQUEDA_600, fuentes.REFINADO)]
    m['MinutosRefinado'] = numero(segundos / 60, 1)
    m['ModelosLocales'] = numero(sum(x['modelos_totales'] for x in licencias))
    m['ModelosDescartados'] = numero(sum(x['modelos_descartados'] for x in licencias))

    m.update(macros_barrido())
    return m


def corridas_barrido():
    filas = []
    for carpeta in sorted(fuentes.BARRIDO.glob('B[0-9][0-9][0-9]_r[0-9]')):
        c = fuentes.leer_json(carpeta / 'comparacion.json')
        fuentes.resumen_verificado(c['final'], carpeta.name)
        filas.append(dict(corrida=carpeta.name, presupuesto=int(carpeta.name[1:4]),
                          buses=c['buses_evitados'], ahorro=c['ahorro_usd']))
    if len(filas) != 15:
        raise ValueError(f'Se esperaban 15 corridas del barrido y hay {len(filas)}')
    return filas


def macros_barrido():
    filas, m = corridas_barrido(), {}
    for presupuesto, nombre in PRESUPUESTOS.items():
        grupo = [f for f in filas if f['presupuesto'] == presupuesto]
        m['MedianaAhorro' + nombre] = numero(statistics.median(f['ahorro'] for f in grupo))
        m['MedianaBusesEvitados' + nombre] = numero(statistics.median(f['buses'] for f in grupo))
    return m


def tabla_barrido():
    lineas = [f"{f['presupuesto']} & {f['corrida'][-1]} & {numero(f['buses'])} & {numero(f['ahorro'])} \\\\"
              for f in corridas_barrido()]
    return '\n'.join(lineas) + '\n'


def main():
    m = calcular()
    texto = '% Generado por scripts/cifras.py. No editar a mano.\n' + '\n'.join(
        macro(n, v) for n, v in sorted(m.items())) + '\n'
    (AQUI / 'cifras.tex').write_text(texto, encoding='utf-8')
    (AQUI / 'tablas').mkdir(exist_ok=True)
    (AQUI / 'tablas/barrido.tex').write_text(tabla_barrido(), encoding='utf-8')
    print(f'{len(m)} macros escritas en cifras.tex')
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Paso 4: correr y ver que pasa.** El comando del Paso 2. Esperado: `OK`, 2 pruebas.

Si falla `MinutosRefinado`, comparar con los 28,64 min del `INFORME.md` del refinado; ese valor manda.

- [ ] **Paso 5: revisar las cifras clave a mano** contra los informes de origen. Correr:

```bash
grep -E 'BusesBase|CostoBase\}|DeltaPctBuses|DeltaPctCosto\}|CotaSimultaneidad|BrechaCostoPiso|DeficitBase|DeficitModelo|DeltaPctCostoAjustado|CostoEsperaModelo' cifras.tex
```

Esperado:
- `BusesBase` = 4.509;
- `DeltaPctBuses` ≈ −14,1;
- `DeltaPctCosto` ≈ −14,2;
- `CotaSimultaneidad` = 3.398.

Si `DeltaPctCostoAjustado` cambia de signo respecto de `DeltaPctCosto`, **avisar a la usuaria** antes de redactar el capítulo 7 (riesgo de la sección 8 del esquema).

- [ ] **Paso 6: agregar `python3 scripts/cifras.py` a `compilar.sh`**, antes de `latexmk`. Correr `./compilar.sh`. Esperado: compila y el revisor sigue con código 0.

### Tarea 7: Figuras

**Archivos**
- Crear `scripts/figuras.py`.
- Modificar `compilar.sh`.
- Genera `figures/corridas_por_hora.pdf`, `figures/energia_por_hora.pdf` y `figures/barrido.pdf`.

**Interfaces**
- Consume: `fuentes.*`, `analisis.energia_por_hora`, `analisis.tarifa_en_hora` y `cifras.corridas_barrido`.
- Produce: los tres PDF, que incluyen los capítulos 2 y 7.

- [ ] **Paso 1: cargar el skill `dataviz`** antes de escribir el código del gráfico, y ajustar colores y marcas a lo que pide. Deben quedar fijos: tipografía serif tipo Times (`STIXGeneral`), rojo `#d42a1e` para destacar (el mismo del deck) y grises para lo demás. Ancho de 6,3 pulgadas y textos de 9 pt como mínimo.

- [ ] **Paso 2: escribir `figuras.py`.**

```python
"""Genera las figuras del informe 2 desde los resultados (PDF vectorial, tipografía tipo Times)."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

import analisis  # noqa: E402
import cifras  # noqa: E402
import fuentes  # noqa: E402

AQUI = Path(__file__).resolve().parents[1]
ROJO, GRIS, GRIS_CLARO = '#d42a1e', '#4d4d4d', '#b3b3b3'
ANCHO = 6.3
HORAS = range(-2, 28)
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['STIXGeneral'], 'mathtext.fontset': 'stix',
                     'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False})


def en_curso_por_hora(corridas):
    intervalos = [(int(c['inicio_s']), int(c['fin_s'])) for c in corridas]
    return [sum(1 for i, f in intervalos if i <= h * 3600 < f) for h in HORAS]


def figura_corridas_por_hora():
    red = en_curso_por_hora(fuentes.leer_csv(fuentes.INSTANCIA_RED / 'corridas.csv'))
    muestra = en_curso_por_hora(fuentes.leer_csv(fuentes.INSTANCIA / 'corridas.csv'))
    fig, ax = plt.subplots(figsize=(ANCHO, 2.6))
    ax.plot(list(HORAS), red, color=GRIS, label='Red completa (417 rutas)')
    ax.plot(list(HORAS), muestra, color=ROJO, label='Muestra (212 rutas)')
    ax.set_xticks(list(HORAS)[::2], [f'{h % 24:02d}' for h in list(HORAS)[::2]])
    ax.set_xlabel('Hora del día (las horas 00–03 del final son del día siguiente)')
    ax.set_ylabel('Corridas en curso')
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(AQUI / 'figures/corridas_por_hora.pdf')


def figura_energia_por_hora():
    escenario = fuentes.leer_json(fuentes.INSTANCIA / 'escenario.json')
    tarifas = [analisis.tarifa_en_hora(escenario['tarifas'], h) for h in range(24)]
    paneles = (('Caso base miope', fuentes.MIOPE / 'recargas.csv'),
               ('Modelo híbrido (refinado)', fuentes.REFINADO / '04_final/recargas.csv'))
    fig, ejes = plt.subplots(1, 2, figsize=(ANCHO, 2.6), sharex=True)
    for ax, (titulo, ruta) in zip(ejes, paneles):
        energia = analisis.energia_por_hora(fuentes.leer_csv(ruta))
        ax.bar(range(24), [e / 1000 for e in energia], color=GRIS_CLARO, width=0.85)
        ax.set_title(titulo, fontsize=9)
        ax.set_xlabel('Hora de inicio de la carga')
        ax.set_ylabel('Energía cargada (MWh)')
        tarifa = ax.twinx()
        tarifa.step(range(24), tarifas, where='mid', color=ROJO)
        tarifa.set_ylabel('Tarifa (USD/kWh)', color=ROJO)
        tarifa.set_ylim(0, max(tarifas) * 1.2)
        tarifa.spines['right'].set_visible(True)
    fig.tight_layout()
    fig.savefig(AQUI / 'figures/energia_por_hora.pdf')


def figura_barrido():
    filas = cifras.corridas_barrido()
    presupuestos = sorted({f['presupuesto'] for f in filas})
    fig, ax = plt.subplots(figsize=(ANCHO, 2.6))
    ax.scatter([f['presupuesto'] for f in filas], [f['ahorro'] / 1000 for f in filas], color=GRIS, s=14,
               label='Cada repetición')
    medianas = [sorted(f['ahorro'] for f in filas if f['presupuesto'] == b)[1] / 1000 for b in presupuestos]
    ax.plot(presupuestos, medianas, color=ROJO, marker='o', label='Mediana de 3 repeticiones')
    ax.set_xscale('log')
    ax.set_xticks(presupuestos, [str(b) for b in presupuestos])
    ax.set_xlabel('Presupuesto por etapa de búsqueda (s, escala logarítmica)')
    ax.set_ylabel('Ahorro sobre la construcción\n(miles de USD/día)')
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(AQUI / 'figures/barrido.pdf')


def main():
    figura_corridas_por_hora()
    figura_energia_por_hora()
    figura_barrido()
    print('3 figuras en figures/')
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Paso 3: generar y mirar las figuras.**

Correr `python3 scripts/figuras.py && pdftoppm -r 80 -png figures/energia_por_hora.pdf salidas/fig_energia` y abrir la imagen. Hacer lo mismo con las otras dos.

Esperado:
- el texto se lee;
- las leyendas no tapan los datos;
- en la figura de corridas el pico de la red cae cerca de las 08:00;
- en el barrido las medianas suben con el presupuesto.

- [ ] **Paso 4: agregar `python3 scripts/figuras.py` a `compilar.sh`**, después de `cifras.py`.

### Tareas 8 a 16: redacción

Reglas comunes a todas las tareas de redacción:
- Se escribe lo que pide la sección del esquema indicada, en voz impersonal.
- Toda cifra es una macro de la Tarea 6.
- Cada tabla y figura tiene `\caption`, `\label` y una referencia en el texto (`\ref`).
- Al terminar se corre `./compilar.sh`. Debe dar código 0, sin `ERROR` del revisor ni alerta de páginas en ese capítulo.
- Después se miran sus páginas con `pdftoppm -f <inicio> -l <fin> -r 70 -png informe2.pdf salidas/capN` (las páginas salen de `informe2.toc`), para comprobar cortes de tabla, figuras flotantes y espacios en blanco.

Plantilla de tabla de KPIs (columnas de caso base, modelo, Δ y Δ%), para reusar en los capítulos 4 y 7:

```latex
\begin{table}[htbp]
\centering
\caption{KPIs del caso base y del modelo híbrido (212 rutas, día laboral).}
\label{tab:kpis}
\begin{tabular}{lrrrr}
\toprule
Indicador & Caso base & Modelo & $\Delta$ & $\Delta\%$ \\
\midrule
Buses utilizados & \BusesBase & \BusesModelo & \DeltaBuses & \DeltaPctBuses\,\% \\
Costo total (USD/día) & \CostoBase & \CostoModelo & \DeltaCosto & \DeltaPctCosto\,\% \\
Km en vacío (\% de los km) & \PctVacioBase\,\% & \PctVacioModelo\,\% & \DeltaPpVacio{} pp & --- \\
Energía comprada (kWh) & \EnergiaBase & \EnergiaModelo & \DeltaEnergia & \DeltaPctEnergia\,\% \\
\bottomrule
\end{tabular}
\end{table}
```

### Tarea 8: Capítulo 4 — Caso base (2 págs.)

**Archivo:** `chapters/cap04_caso_base.tex`. **Spec:** ESQUEMA §4, capítulo 4.

- [ ] **Paso 1:** escribir las secciones `\section{Política miope por ruta con recarga}`, `\section{Por qué es una línea base defendible}`, `\section{Resultado del caso base}` y `\section{Sensibilidad al umbral de carga}`, y un párrafo final sobre el caso base presentado el 8 de octubre.
  - La política va como lista enumerada de 6 pasos.
  - Se dice explícitamente: mismas `\RutasMuestra` rutas y `\CorridasMuestra` corridas que el modelo, mismo horizonte y **el mismo auditor**.
- [ ] **Paso 2:** tabla de sensibilidad al umbral (0, 20, 30 y 50 %) con `\BusesBase`, `\BusesUmbralVeinte`… y su costo y % de km en vacío. Una frase justifica el 0 %.
- [ ] **Paso 3:** párrafo sobre el sin recargas (`\BusesSinRecargas`, `\CostoSinRecargas`): por qué se reemplazó (comentario del profesor y del ayudante) y qué muestra. Remitir a la sección de recarga nocturna (`\ref{ch:supuestos}`).
- [ ] **Paso 4:** compilar y revisar páginas según las reglas comunes. Esperado: capítulo 4 ≤ 2 págs.

### Tarea 9: Capítulo 7 — Resultados y análisis de KPIs (6 págs.)

**Archivo:** `chapters/cap07_resultados.tex`. **Spec:** ESQUEMA §4, capítulo 7 (subsecciones 7.1 a 7.9).

- [ ] **Paso 1:** sección de KPIs con la tabla principal (la plantilla de arriba) y una interpretación: qué indicador mueve el costo y por qué.
- [ ] **Paso 2:** composición del costo. Tabla con `\PctFlota{P}`, `\PctKm{P}`, `\PctEnergia{P}` y `\PctSesiones{P}` para los dos planes, más la interpretación (la flota domina).
- [ ] **Paso 3:** tabla por etapas (caso base → construcción → parejas → tríos → refinamiento), con `\AhorroBusesConstruccion`, `\AhorroBusesBusqueda` y `\PctAhorroConstruccion`. El texto responde «¿es tema del caso base o del modelo?» y explica qué cambia entre el miope y la construcción.
- [ ] **Paso 4:** energía.
  - `\includegraphics[width=\textwidth]{figures/energia_por_hora.pdf}`, en qué horarios se carga y cómo pesa la tarifa.
  - El costo ajustado por la energía final (`\Deficit{P}`, `\TarifaNocturna`, `\CostoAjustado{P}`, `\DeltaPctCostoAjustado`), explicando por qué hace falta.
- [ ] **Paso 5:** tabla de electroterminales (`\Plazas{E}{P}`, `\Conexiones{E}{P}`, `\Capacidad{E}`), con la lectura de que las plazas se saturan y las conexiones tienen holgura.
- [ ] **Paso 6:** variabilidad. `\includegraphics{figures/barrido.pdf}` con las medianas, una nota de «otro equipo» y la referencia al Anexo C (`\ref{an:barrido}`).
- [ ] **Paso 7:** cotas y brecha (`\CotaSimultaneidad` a las `\HoraCotaSimultaneidad`, `\PisoFaseUno`, `\FlotaFaseUno`, `\BrechaCostoPiso`, `\BrechaBusesFaseUno`), explicando por qué una cota no necesita ser factible.
- [ ] **Paso 8:** validez de los KPIs, limitaciones y mejoras.
- [ ] **Paso 9:** compilar y revisar. Esperado: capítulo 7 ≤ 6 págs.

### Tarea 10: Capítulo 6 — Implementación (2 págs.) y carpeta del repositorio

**Archivos**
- Escribir `chapters/cap06_implementacion.tex`.
- Crear `08-entrega2/informe2/REPOSITORIO.md`.

**Spec:** ESQUEMA §4, capítulo 6.

- [ ] **Paso 1:** diagrama de flujo en TikZ (el revisor no mira cifras dentro de `tikzpicture`):

```latex
\begin{figure}[htbp]
\centering
\begin{tikzpicture}[node distance=4mm and 6mm, caja/.style={draw, rounded corners, align=center,
  font=\footnotesize, minimum height=10mm, text width=22mm}, flecha/.style={-Stealth}]
\node[caja] (inst) {Instancia\\\scriptsize\texttt{instancia\_212/}};
\node[caja, right=of inst] (cons) {Construcción\\cronológica\\\scriptsize\texttt{caso\_base.py}};
\node[caja, right=of cons] (par) {Parejas\\\scriptsize\texttt{intercambios.py}};
\node[caja, right=of par] (tri) {Tríos\\\scriptsize\texttt{trios.py}};
\node[caja, below=of par] (milp) {MILP local\\\scriptsize\texttt{conjunta.py}, \texttt{recarga.py}};
\node[caja, below=of cons] (aud) {Auditoría\\\scriptsize\texttt{verificar.py}};
\node[caja, below=of inst] (exp) {Exportación\\\scriptsize\texttt{ejecutar.py}};
\draw[flecha] (inst) -- (cons); \draw[flecha] (cons) -- (par); \draw[flecha] (par) -- (tri);
\draw[flecha] (par) -- (milp); \draw[flecha] (tri) |- (milp);
\draw[flecha] (milp) -- node[above, font=\scriptsize]{solo si baja el costo} (aud);
\draw[flecha] (aud) -- (exp);
\end{tikzpicture}
\caption{Módulos del método híbrido y orden en que se ejecutan.}
\label{fig:flujo}
\end{figure}
```

- [ ] **Paso 2:** el texto:
  - herramientas (Python, NumPy, Gurobi 12 con licencia restringida: `\ModelosDescartados` de `\ModelosLocales` modelos descartados);
  - auditor, pruebas y protección de la mejor solución;
  - trazabilidad (huellas sha256);
  - cómo se reproduce el refinado (`\MinutosRefinado` min);
  - el enlace al repositorio como `\textcolor{red}{[POR COMPLETAR: enlace del repositorio]}`, para que el revisor lo cuente como pendiente.
- [ ] **Paso 3:** `REPOSITORIO.md` con las carpetas que van al repositorio:
  - `metodo_hibrido/` (sin `resultados/` pesados, salvo `mejor_20261006_refinamiento/` y `mejor_20261006_600/`);
  - `CODIGO apstone/tres_fases/caso_base.py` y sus dependencias;
  - `caso_base_simple_gurobi/`;
  - `08-entrega2/informe2/scripts/`;
  - un borrador del README raíz con cómo reproducir cada cifra.

  No se crea el repositorio: lo crea el grupo.
- [ ] **Paso 4:** compilar y revisar. Esperado: capítulo 6 ≤ 2 págs.

### Tarea 11: Capítulo 2 — Problema y datos (4 págs.), con la verificación 2

**Archivo:** `chapters/cap02_problema_datos.tex`. **Spec:** ESQUEMA §4, capítulo 2 (2.1 a 2.5).

- [ ] **Paso 1: verificación 2, el origen de T01–T04 y la exclusión de Los Acacios.**
  - Correr `graphify query "terminales de espera T01 T02 T03 T04 coordenadas origen Los Acacios"`.
  - Después buscar con `grep -rn "Acacios\|Pajaritos" "CODIGO apstone/fase1" "CODIGO apstone/tres_fases" 02-codigo --include=*.py`, revisando antes con `ls -lO` que los archivos no estén solo en iCloud.
  - Anotar en `salidas/origen_terminales.md`: de dónde salen, por qué hacen falta y por qué se excluyó Los Acacios.
  - **Si no se encuentra, preguntarle a la usuaria antes de escribir 2.4.**
- [ ] **Paso 2:** glosario como tabla (`tabularx`) con los 9 términos del esquema.
- [ ] **Paso 3:** problema en palabras, datos y preparación (tabla del GTFS a RED), y `figures/corridas_por_hora.pdf`.
- [ ] **Paso 4:** decisiones que condicionan el modelo: sectores, T01–T04, muestra de 212 rutas con su tabla de comparación entre muestra y red, y riesgos de sesgo.
  - La tabla de comparación (km medio por corrida y corridas por sector) se agrega a `cifras.py` como macros nuevas, con una prueba en `test_cifras_reales.py` que fije `CorridasMuestra` = 33.220.
- [ ] **Paso 5:** los 4 KPIs, con su fórmula en palabras y la regla de comparar siempre contra el caso base.
- [ ] **Paso 6:** compilar y revisar. Esperado: capítulo 2 ≤ 4 págs.

### Tarea 12: Capítulo 8 — Supuestos, riesgos y plan de sensibilidad (2 págs.)

**Archivo:** `chapters/cap08_supuestos.tex`. **Spec:** ESQUEMA §4, capítulo 8.

- [ ] **Paso 1:** tabla de supuestos (supuesto · fundamento · riesgo) con los 9 del esquema.
- [ ] **Paso 2:** recarga nocturna, con `\BusesConDeficit`, `\DeficitModelo`, `\HorasCargaParalelo`, `\HorasBusMasVacio`, `\RondasCarga` y `\PlazasTotales`. Conclusión: es un riesgo y queda como paso futuro.
- [ ] **Paso 3:** sensibilidad ya hecha: presupuesto, umbral y espera (`\CostoEsperaMinuto`, `\CostoEspera{P}`, `\DeltaPctCostoConEspera`).
- [ ] **Paso 4:** tabla del plan de sensibilidad (supuesto · rango · KPI · semana).
- [ ] **Paso 5:** compilar y revisar. Esperado: capítulo 8 ≤ 2 págs.

### Tarea 13: Capítulo 5 — Metodología híbrida (5 págs.), con la verificación 7

**Archivos**
- Escribir `chapters/cap05_metodologia.tex` y `chapters/anexo_a_notacion.tex`.
- Modificar `scripts/analisis.py`, `scripts/test_analisis.py` y `scripts/cifras.py`.

**Spec:** ESQUEMA §4, capítulo 5.

- [ ] **Paso 1: prueba de `contar_conexiones_factibles`, que falla.**

```python
    def test_conexiones_factibles(self):
        corridas = [
            {'corrida_id': 'a', 'sector_id': '1', 'inicio_s': '0', 'fin_s': '100', 'inicio_stop_id': 'X', 'fin_stop_id': 'Y'},
            {'corrida_id': 'b', 'sector_id': '1', 'inicio_s': '200', 'fin_s': '300', 'inicio_stop_id': 'Y', 'fin_stop_id': 'X'},
            {'corrida_id': 'c', 'sector_id': '1', 'inicio_s': '150', 'fin_s': '400', 'inicio_stop_id': 'Z', 'fin_stop_id': 'X'},
            {'corrida_id': 'd', 'sector_id': '2', 'inicio_s': '500', 'fin_s': '600', 'inicio_stop_id': 'Y', 'fin_stop_id': 'X'},
        ]
        tiempos = {('S:Y', 'S:Y'): 0, ('S:Y', 'S:Z'): 100, ('S:X', 'S:Y'): 50, ('S:X', 'S:Z'): 10_000}
        # a→b (Y→Y, 0 s, llega a 100 ≤ 200) sí; a→c (Y→Z, 100 s, llega a 200 > 150) no;
        # c→b no (b empieza antes del fin de c); d es de otro sector.
        self.assertEqual(analisis.contar_conexiones_factibles(corridas, tiempos), 1)
```

Correr `python3 -m unittest discover -s scripts -p 'test_analisis.py' -v`. Esperado: `AttributeError: ... 'contar_conexiones_factibles'`.

- [ ] **Paso 2: implementarla con numpy, por sector.**

```python
def contar_conexiones_factibles(corridas, tiempos):
    """Pares (i, j) del mismo sector en que un bus llega a tiempo de terminar i a empezar j."""
    import numpy as np
    por_sector = defaultdict(list)
    for c in corridas:
        por_sector[c['sector_id']].append(c)
    total = 0
    for grupo in por_sector.values():
        inicios = np.array([int(c['inicio_s']) for c in grupo])
        finales = [(int(c['fin_s']), 'S:' + c['fin_stop_id']) for c in grupo]
        paradas = ['S:' + c['inicio_stop_id'] for c in grupo]
        for fin, parada_fin in finales:
            traslado = np.array([tiempos.get((parada_fin, p), np.inf) for p in paradas], dtype=float)
            total += int(np.count_nonzero(fin + traslado <= inicios))
    return total
```

Correr la prueba. Esperado: `OK`.

Después agregar en `cifras.calcular()` la macro `ConexionesFactibles`. Para eso:
- armar `tiempos` desde `distancias.csv`, con `math.ceil(km * 3600 / VelocidadVacio)` y solo los pares con distancia;
- con 33.220 corridas el cálculo toma minutos. Si toma más de 10 min, guardar el resultado en `salidas/conexiones.json` y leerlo de ahí.

- [ ] **Paso 3:** modelo completo, siguiendo el esquema §5.1:
  - conjuntos, parámetros, variables, objetivo y restricciones en `align`, cada una numerada y explicada en una frase;
  - cada símbolo se define al aparecer;
  - el tamaño con `\ConexionesFactibles`, y por qué no se resuelve directo.
- [ ] **Paso 4:** el método híbrido: la construcción en 7 pasos, parejas, tríos, el **MILP local como el mismo modelo restringido a 1–3 jornadas** y la regla de aceptación.
- [ ] **Paso 5:** fortalezas, debilidades y propuestas de mejora.
- [ ] **Paso 6:** Anexo A con la tabla completa de notación.
- [ ] **Paso 7:** compilar y revisar. Esperado: capítulo 5 ≤ 5 págs.

### Tarea 14: Capítulo 3 — Evolución y discusión metodológica (3 págs.) y bibliografía verificada

**Archivos**
- Escribir `chapters/cap03_evolucion.tex` (y quitar `\nocite{*}`).
- Modificar `referencias.bib`.

**Spec:** ESQUEMA §4, capítulo 3.

- [ ] **Paso 1: verificar cada referencia nueva con búsqueda web** antes de agregarla a `referencias.bib`. Para cada una se confirma autor, año, título, revista o editorial y DOI:
  - despacho secuencial (el deck dice «Bodin et al., 1978»);
  - una revisión de programación de buses eléctricos;
  - una referencia de matheurísticas (heurística con MILP local).

  Si una no se puede confirmar, no se cita.
- [ ] **Paso 2:** las alternativas del informe 1 y la prueba de concepto (`\NodosFaseUno`, `\ArcosFaseUno`, `\FlotaFaseUno`, `\BusesPrototipoSinMejora` → `\BusesPrototipo`), presentada como **prueba de concepto, no como caso base**.
- [ ] **Paso 3:** el diagnóstico y por qué el híbrido. Discusión crítica con citas (`\citeA`, `\cite`); la carga lineal se presenta como supuesto del trabajo.
- [ ] **Paso 4:** quitar `\nocite{*}`, compilar y revisar. Esperado: capítulo 3 ≤ 3 págs., sin `??` en el PDF y sin el pendiente `\nocite`.

### Tarea 15: Capítulos 1, 9 y 10 y resumen

**Archivos:** `chapters/cap01_introduccion.tex`, `cap09_conclusiones.tex`, `cap10_pasos_futuros.tex` y `resumen.tex`. **Spec:** ESQUEMA §3 (resumen) y §4 (capítulos 1, 9 y 10).

- [ ] **Paso 1:** introducción.
  - Contexto separado del problema, y el objetivo del semestre **completo** (417 rutas, los tres tipos de día y los 5 E).
  - Qué se hizo ahora, qué cambió desde el informe 1 y la estructura del informe.
  - Sin porcentajes de costo en el objetivo.
- [ ] **Paso 2:** conclusiones. Cada una se apoya en una macro de los capítulos 7 u 8 y es accionable: aprendizajes, robustez, fortalezas, limitaciones, implicancias para RED y mejoras.
- [ ] **Paso 3:** pasos futuros.
  - Tabla de avance contra la Gantt del informe 1 (lámina 21).
  - Carta Gantt nueva en TikZ o como tabla, con hitos, dependencias y la columna de responsables como `[POR COMPLETAR: responsable]`.
  - Las fechas de la Entrega 3 y del informe final como `[POR COMPLETAR: fecha]`.
- [ ] **Paso 4:** resumen de 1 página como máximo: problema, alcance, motivación, objetivo, **entregable**, lo hecho, el resultado principal contra el caso base y la conclusión central.
- [ ] **Paso 5:** compilar y revisar. Esperado: capítulos 1, 9 y 10 ≤ 2 págs. cada uno y el resumen en 1 página.

### Tarea 16: Anexos B–E

**Archivos:** `chapters/anexo_b_correcciones.tex`, `anexo_c_barrido.tex`, `anexo_d_parametros.tex` y `anexo_e_declaracion_ia.tex`. **Spec:** ESQUEMA §4 (anexos) y §6.

- [ ] **Paso 1:** Anexo B. Pasar a `longtable` la tabla de la sección 6 del esquema, más el feedback de la presentación, con la sección exacta del informe (`\ref{...}`) donde se atiende cada comentario.
- [ ] **Paso 2:** Anexo C. Tabla con `\input{tablas/barrido.tex}` (presupuesto · repetición · buses evitados · ahorro USD) y una nota sobre el equipo.
- [ ] **Paso 3:** Anexo D. Tabla de parámetros con las macros de la Tarea 6 y la tabla de tarifas.
- [ ] **Paso 4:** Anexo E. La declaración con el formato de los lineamientos (texto en `graphify-out/converted/Lineamientos Entrega 2 2026-2_732eb170.md`, sección «Uso de herramientas de Inteligencia Artificial»):
  - marcada **SÍ**;
  - con los usos marcados: redacción, análisis de datos, desarrollo de código, análisis de resultados, figuras;
  - la herramienta: Claude;
  - la reflexión como `[POR COMPLETAR: reflexión del grupo]`;
  - los 7 nombres para firmar.
- [ ] **Paso 5:** compilar y revisar.

### Tarea 17: Revisión final y entrega del borrador al grupo

**Archivos:** todos (solo lectura y correcciones puntuales).

- [ ] **Paso 1:** `./compilar.sh` y después `python3 scripts/revisar.py --final`.

  Esperado:
  - 0 `ERROR`;
  - páginas del cuerpo ≤ 30;
  - los únicos `PENDIENTE` son los del grupo (enlace del repositorio, responsables, fechas y reflexión de IA).
- [ ] **Paso 2:** recorrer la tabla de la sección 6 del esquema y comprobar en el PDF cada corrección.
- [ ] **Paso 3:** leer el PDF completo una vez buscando:
  - coherencia entre capítulos (las mismas cifras dicen lo mismo);
  - siglas sin definir;
  - figuras sin citar;
  - erratas.
- [ ] **Paso 4:** correr todas las pruebas: `python3 -m unittest discover -s scripts -p 'test_*.py' -v`. Esperado: `OK`.
- [ ] **Paso 5:** enviar `informe2.pdf` a la usuaria con la lista de pendientes del grupo (esquema §10).
