#!/bin/bash
# Escalera de casos medianos (200 a 400 corridas): ¿hasta dónde llega la respuesta perfecta y qué tan lejos
# quedan tríos y cuartetos de ella? Corre en serie; si se corta, basta volver a ejecutarlo (--continuar).
# Uso, desde la raíz del proyecto:  bash 09-entrega3/octetos/correr_medianos.sh
set -u
cd "$(dirname "$0")/../.."
PY=.venv-optimizacion/bin/python
CORRER=09-entrega3/octetos/correr_metodos.py
RES=09-entrega3/octetos/resultados
MEDIANOS=$(ls -d 09-entrega3/octetos/casos/mediano_*)
HEURISTICA_S=300     # 5 minutos por corrida, igual para todos los métodos
EXACTA_S=7200        # hasta 2 horas por caso; si no termina, queda la cota inferior
mkdir -p "$RES"

etapa() {  # etapa <nombre> <csv> <argumentos...>
    local nombre=$1 csv=$2; shift 2
    local seguir=""
    [ -f "$csv" ] && seguir="--continuar"
    echo "=== $(date '+%F %T') inicio: $nombre"
    "$PY" "$CORRER" "$@" --salida "$csv" $seguir
    echo "=== $(date '+%F %T') fin: $nombre (código $?)"
}

# 1. Heurísticas: plan inicial, pares+tríos (lo entregado), tríos y cuartetos al azar con 3 semillas.
etapa "medianos heurísticas" "$RES/casos_medianos.csv" --instancias $MEDIANOS \
    --metodos solo_base pares_trios trios cuartetos --selecciones azar --semillas 1 2 3 \
    --presupuestos $HEURISTICA_S
# 2. Respuesta perfecta, del caso más chico al más grande.
etapa "medianos exacta" "$RES/casos_medianos_exacta.csv" --instancias $MEDIANOS --metodos exacta \
    --presupuestos $EXACTA_S --presupuesto-exacta $EXACTA_S
echo "=== $(date '+%F %T') medianos terminado"
