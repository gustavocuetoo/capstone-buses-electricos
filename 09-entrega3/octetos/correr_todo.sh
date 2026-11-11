#!/bin/bash
# Corre el estudio de tamaños de grupo completo, en serie (mismo computador y mismo tiempo para todos).
# Si se corta, basta volver a ejecutarlo: cada etapa retoma con --continuar lo que ya está en su tabla.
# Uso, desde la raíz del proyecto:  bash 09-entrega3/octetos/correr_todo.sh
set -u
cd "$(dirname "$0")/../.."
PY=.venv-optimizacion/bin/python
CORRER=09-entrega3/octetos/correr_metodos.py
RES=09-entrega3/octetos/resultados
CASOS=09-entrega3/octetos/casos
MUY_CHICOS=$(ls -d $CASOS/muy_chico_*)
CHICOS=$(ls -d $CASOS/chico_*)
HEURISTICAS="solo_base pares pares_trios trios cuartetos quintetos octetos mezcla"
mkdir -p "$RES"

etapa() {  # etapa <nombre> <csv> <argumentos...>
    local nombre=$1 csv=$2; shift 2
    local seguir=""
    [ -f "$csv" ] && seguir="--continuar"
    echo "=== $(date '+%F %T') inicio: $nombre"
    "$PY" "$CORRER" "$@" --salida "$csv" $seguir
    echo "=== $(date '+%F %T') fin: $nombre (código $?)"
}

# 1. Casos muy chicos: todos los métodos, incluida la respuesta perfecta.
etapa "muy chicos" "$RES/casos_muy_chicos.csv" --instancias $MUY_CHICOS \
    --presupuestos 60 120 --presupuesto-exacta 1800
# 2. Casos chicos: todos los métodos menos la respuesta perfecta (va al final).
etapa "chicos" "$RES/casos_chicos.csv" --instancias $CHICOS --metodos $HEURISTICAS \
    --presupuestos 60 120
# 3. Red completa (417 rutas), día laboral: todos los métodos con 10, 20 y 40 minutos. Aquí se decide el método.
#    20 min es el tiempo de las corridas entregadas (10 de pares + 10 de tríos). Se guardan los planes (~74 MB c/u).
etapa "red completa L" "$RES/red_completa_417_L.csv" --instancias metodo_hibrido/instancia_417 \
    --metodos solo_base pares pares_trios trios cuartetos quintetos octetos mezcla --presupuestos 600 1200 2400 \
    --planes "$RES/planes_417_L"
# 4. Sábado y domingo: solo el método que ganó el día laboral (regla en elegir_metodo.py), con 40 minutos.
ELEGIDO=$("$PY" 09-entrega3/octetos/elegir_metodo.py "$RES/red_completa_417_L.csv") \
    || { echo "=== $(date '+%F %T') no se pudo elegir el método: se detiene"; exit 1; }
echo "=== $(date '+%F %T') para sábado y domingo: $ELEGIDO"
for dia in S D; do
    etapa "red completa $dia" "$RES/red_completa_417_$dia.csv" --instancias metodo_hibrido/instancia_417_$dia \
        $ELEGIDO --presupuestos 2400 --planes "$RES/planes_417_$dia"
done
# 4. Extra: la respuesta perfecta en los casos chicos, 30 minutos cada uno (cota para medir la distancia).
etapa "exacta en chicos" "$RES/casos_chicos_exacta.csv" --instancias $CHICOS --metodos exacta \
    --presupuestos 1800 --presupuesto-exacta 1800
echo "=== $(date '+%F %T') todo terminado"
