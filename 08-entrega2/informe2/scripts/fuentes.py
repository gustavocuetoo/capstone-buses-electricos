"""Rutas de los resultados que usa el informe y lectura con validación."""
import csv
import json
import os
from pathlib import Path

NOMBRES_CARPETA_CODIGO = ('codigo', 'CODIGO apstone')  # en el repositorio se llama «codigo»


def carpeta_codigo(raiz):
    for nombre in NOMBRES_CARPETA_CODIGO:
        if (raiz / nombre).is_dir():
            return raiz / nombre
    return raiz / NOMBRES_CARPETA_CODIGO[0]


RAIZ = Path(__file__).resolve().parents[3]
CODIGO = carpeta_codigo(RAIZ)
TRES_FASES = CODIGO / 'output/tres_fases'
REFINADO = RAIZ / 'metodo_hibrido/resultados/mejor_20261006_refinamiento'
BUSQUEDA_600 = RAIZ / 'metodo_hibrido/resultados/mejor_20261006_600'
MIOPE = TRES_FASES / 'muestra_212_caso_base'
MIOPE_UMBRAL = {20: TRES_FASES / 'muestra_212_caso_base_0.2',
                30: TRES_FASES / 'muestra_212_caso_base_0.3',
                50: TRES_FASES / 'muestra_212_caso_base_0.5'}
SIN_RECARGAS = RAIZ / 'caso_base_simple_gurobi/corrida_gurobi'
PROTOTIPO = TRES_FASES / 'muestra_212'
PROTOTIPO_MEJORADO = TRES_FASES / 'muestra_212_trios'
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
