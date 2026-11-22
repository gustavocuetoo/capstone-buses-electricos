# Escenarios de sensibilidad

`crear_escenarios.py` crea copias de una instancia con otro `escenario.json`, una por escenario, más
un `indice.csv`. Las corridas y las distancias no cambian. El método híbrido corre estos escenarios sin
modificar su código, porque ya lee plazas, conexiones y tarifas desde `escenario.json`.

| Escenario | Cambio | Pregunta de gestión |
|---|---|---|
| `plazas_-20`, `plazas_+20`, `plazas_+50` | Plazas y conexiones de cada electroterminal × 0,8, 1,2 y 1,5 | ¿Cuánto vale ampliar o perder espacio, que hoy es el recurso que se llena? |
| `conexiones_-50` | La mitad de los cargadores, mismas plazas | ¿Hacen falta todos los cargadores? |
| `cierre_E1` … `cierre_E5` | Un electroterminal cerrado (0 plazas y 0 conexiones) | Resiliencia: ¿cuánto cuesta perder cada terminal? |
| `tarifa_punta_+50` | Precio de los tramos de punta × 1,5 | ¿Se mueve la carga de horario? |
| `plazas_por_demanda` | Las 700 plazas repartidas según las corridas de cada sector | El desbalance entre sectores que preguntó el profesor |

## Uso

```bash
python3 09-entrega3/sensibilidad/crear_escenarios.py --instancia metodo_hibrido/instancia_417 \
    --destino metodo_hibrido/sensibilidad_417_L
python3 -m pytest -q 09-entrega3/sensibilidad/test_crear_escenarios.py
```

La instancia completa (`metodo_hibrido/instancia_417`) no está en GitHub; se prepara con
`metodo_hibrido/preparar_completa.py`. Cada escenario se corre igual que la instancia base, con
`buscar_mejor.py` o `09-entrega3/octetos/correr_metodos.py --instancias ...`, y después se mide con
`09-entrega3/kpi/` agregando la carpeta del resultado en `PLANES`.

## Lo que todavía no cubre

- **Consumo, batería, estado de carga inicial y final, velocidad en vacío, potencia, costo por bus y
  costo por km.** Están fijos en el código de `metodo_hibrido/` (`calendario.py`, `recarga.py`,
  `conjunta.py`, `exacto.py`, `verificar.py` y `caso_base.py`), y `load_instance` rechaza un escenario
  que declare otros valores. Para variarlos hay que llevarlos a `escenario.json`.
- **El caso base en estos escenarios.** `codigo/tres_fases/caso_base.py` toma plazas y tarifas de
  `codigo/`, no de `escenario.json`.
