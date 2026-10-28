# Caso base miope

Referencia intuitiva, sin optimización, para comparar el modelo de tres fases sobre **la misma instancia, el mismo horizonte y la misma auditoría** (`verificar.py`). Implementado el 5 de octubre de 2026 en `caso_base.py`.

## Política

1. Se recorren todas las corridas en orden de hora de salida.
2. Cada ruta tiene sus propios buses: no se comparten entre rutas, aunque estén en el mismo sector.
3. La corrida se asigna al bus de su ruta que lleva más tiempo libre y alcanza a llegar a tiempo.
4. Si la batería no le alcanza para la corrida y la reserva de regreso, antes va al electroterminal más cercano con cupo y carga al 100 %, a la tarifa que haya. Si ahí no cabe a tiempo, prueba el siguiente electroterminal.
5. Si ningún bus de la ruta puede, se agrega uno con batería llena desde el terminal común más cercano.
6. Después de su última corrida, cada bus vuelve al terminal común más cercano.

Con `--umbral` el bus además va a cargar apenas su batería baja de esa fracción. Por defecto es 0: solo carga cuando no le alcanza.

Se usan las mismas constantes que la Fase 3: 350 kWh, mínimo 35 kWh, 1,4 kWh/km, bloques de 5 minutos de hasta 15 kWh, 18 km/h en vacío, cuatro terminales comunes y el calendario compartido de plazas y conexiones (`fase3.Calendario`).

## Resultado en la muestra de 212 rutas

| Indicador | Caso base | Modelo (grupos de tres) | Variación |
|---|---:|---:|---:|
| Corridas cubiertas | 33.220 | 33.220 | — |
| Buses | 4.509 | 4.175 | −334 (−7,4 %) |
| Costo total USD/día | 1.601.774,92 | 1.459.572,80 | −142.202 (−8,9 %) |
| Km en vacío | 16,6 % | 12,3 % | −4,3 pp |
| Ocupación máxima de cargadores | 69 % (E2) | 14 % (E4) | −55 pp |

La diferencia de costo se reparte en 83.500 USD de flota, 20.773 de kilómetros, 39.229 de energía y −1.300 de sesiones. **La energía no es del todo comparable**: ninguno de los dos cobra la carga inicial de cada bus, y el caso base termina el día con más energía en las baterías porque siempre carga al 100 %. Sin la energía, el ahorro es de 102.973 USD/día.

Sensibilidad al umbral de recarga del caso base:

| Umbral | Buses | Costo USD/día | Km en vacío |
|---:|---:|---:|---:|
| 0 % | 4.509 | 1.601.775 | 16,6 % |
| 20 % | 4.516 | 1.604.873 | 16,7 % |
| 30 % | 4.822 | 1.718.697 | 18,0 % |
| 50 % | 5.518 | 1.986.474 | 23,0 % |

Para comparar se usa el umbral 0 %, el más favorable de los probados, para no inflar la ganancia del modelo.

## Ejecutar

```powershell
python tres_fases/caso_base.py --base output/tres_fases/muestra_212
python tres_fases/caso_base.py --base output/tres_fases/muestra_212 --umbral 0.3
python -m unittest tres_fases.test_caso_base
```

La ejecución toma unos 2 segundos y no necesita Gurobi. Lee las rutas de `seleccion_rutas.csv` y el horizonte de `resumen.json` de la carpeta base, y guarda `resumen.json`, `jornadas.csv`, `actividades.csv` y `recargas.csv` en `output/tres_fases/muestra_212_caso_base` (o `..._caso_base_<umbral>`).

Las seis pruebas cubren: que las rutas no compartan buses, que un bus libre se reutilice dentro de la ruta, la carga completa en el electroterminal más cercano, que se agregue un bus cuando la carga completa no cabe, el cambio al siguiente electroterminal cuando no hay cargador y el efecto del umbral.

`.deps` se agrega a la ruta de importación solo en Windows, porque contiene binarios de Windows. En otros sistemas se usa el NumPy instalado.
