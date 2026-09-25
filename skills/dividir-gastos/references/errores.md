# Catálogo de errores y advertencias

Los **errores (E)** detienen el flujo: no se genera ningún reporte (salida 1, o 2 si falta el archivo). Se listan **todos** los errores del archivo a la vez, con su número de línea, para corregirlos de una sola pasada.
Las **advertencias (W)** no detienen el flujo; aparecen en consola y en un recuadro amarillo del reporte.

| Código | Significado | Cómo corregir |
|---|---|---|
| E001 | El archivo no existe | Revisa la ruta. |
| E002 | Archivo vacío o sin filas de gastos | Agrega al menos un gasto bajo la cabecera. |
| E003 | Faltan columnas | Usa la cabecera de `assets/plantilla_csv.csv`. |
| E004 | Fecha inválida | Usa `AAAA-MM-DD` (ej. `2026-08-15`, no `15/08/2026`). |
| E005 | Monto inválido (texto, 0 o negativo) | Escribe un número > 0. Un reembolso se registra como gasto pagado por quien devuelve. |
| E006 | Moneda no soportada | Usa una moneda de `assets/tasas_cambio.json` o agrégala allí. |
| E007 | Persona fuera de la lista `--personas` | Corrige el nombre o agrégalo a `--personas`. |
| E008 | Participantes vacío | Pon `todos` o `Ana\|Luis`. |
| E009 | Peso inválido (`Luis:dos`, `Luis:0`) | El peso va en número > 0: `Luis:2`. |
| E010 | Falta `pagado_por` | Indica quién pagó. |
| W001 | Fila idéntica a otra | ¿Se registró dos veces? Si fue real (dos taxis iguales), cambia la descripción. |
| W002 | Dos nombres muy parecidos | Probable error de tipeo; unifica el nombre o usa `--personas`. |
| W003 | Categoría desconocida | Se usa `otros`. Usa una de `assets/categorias.json`. |
| W004 | Archivo no UTF-8 | Guarda como "CSV UTF-8" en Excel. |
| W005 | Fecha en el futuro | Revisa el año. |

## Qué debe hacer el agente ante un error

1. Mostrar al usuario los errores tal como salen (código + línea).
2. **No adivinar** montos, fechas ni nombres: preguntar el dato correcto.
3. Corregir el CSV con lo que diga el usuario y volver a ejecutar `dividir_gastos.py`.
