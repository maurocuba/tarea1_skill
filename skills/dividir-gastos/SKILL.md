---
name: dividir-gastos
description: Divide gastos compartidos entre varias personas (viajes, cenas, departamentos compartidos) a partir de un CSV, valida los datos, convierte monedas, calcula cuánto pagó y consumió cada uno y el mínimo de transferencias para quedar a mano, y genera un reporte HTML más un resumen para WhatsApp. Úsala cuando el usuario pida "dividir la cuenta", "quién le debe a quién", "sacar cuentas del viaje", "repartir gastos entre amigos/roomies" o entregue una lista/CSV de gastos con quién pagó.
---

# dividir-gastos

Convierte una lista de gastos compartidos en una liquidación clara: **quién le paga a quién y cuánto**, con el menor número de transferencias posible.

## Cuándo usarla

- El usuario tiene gastos de un grupo (viaje, salida, casa compartida) y quiere saber quién debe a quién.
- Hay gastos en varias monedas (ej. BOB y USD) y hay que unificarlos.
- No todos participan en todos los gastos, o alguien consume "doble" (pesos).

**No usarla** para contabilidad formal, impuestos o facturación: es una herramienta de reparto entre personas.

## Flujo (seguir en este orden)

1. **Conseguir el CSV.** Si el usuario da los gastos en texto libre, pásalos al formato de `assets/plantilla_csv.csv`. El formato completo está en `references/formato_csv.md` (léelo si hay dudas sobre participantes, pesos o monedas).
2. **Validar** (opcional por separado, el paso 4 ya valida):
   ```bash
   python scripts/validar.py gastos.csv [--personas "Ana,Luis,Carla"]
   ```
   Si el usuario sabe quiénes son todos, pasa `--personas` para detectar nombres mal escritos.
3. **Si hay errores** (códigos `E###`), NO inventes correcciones: consulta `references/errores.md`, explica al usuario cada error con su línea y pídele el dato correcto. Las advertencias (`W###`) no bloquean, pero menciónalas.
4. **Ejecutar el flujo completo:**
   ```bash
   python scripts/dividir_gastos.py gastos.csv --titulo "Viaje a Uyuni" --salida salida_gastos
   ```
5. **Entregar** al usuario:
   - `salida_gastos/reporte.html` (reporte visual),
   - las transferencias en el chat (están en la salida de consola y en `resumen_whatsapp.txt`),
   - `liquidacion.json` solo si lo pide.
6. Si preguntan *cómo* se calculó, explica con `references/algoritmo.md`.

## Scripts

| Script | Qué hace |
|---|---|
| `scripts/dividir_gastos.py` | Flujo completo: validar → liquidar → reporte. Es el que se usa normalmente. |
| `scripts/validar.py` | Solo valida el CSV. `--json` para salida estructurada. |
| `scripts/liquidar.py` | Valida y calcula balances/transferencias, guarda JSON (`-o`). |
| `scripts/reporte.py` | Genera HTML + resumen desde un `liquidacion.json`. |
| `scripts/comun.py` | Utilidades compartidas (centavos, formato, carga de assets). |

Códigos de salida: `0` OK · `1` CSV con errores (no se genera nada) · `2` archivo no encontrado.

## Assets

- `assets/tasas_cambio.json` — moneda base (BOB) y tasas de conversión. Si el usuario da otra tasa, edítala o pasa `--tasas`.
- `assets/categorias.json` — categorías válidas y sus colores en el reporte.
- `assets/plantilla_reporte.html` — plantilla del reporte (autocontenida, modo claro/oscuro).
- `assets/plantilla_resumen.txt` — plantilla del mensaje para WhatsApp.
- `assets/plantilla_csv.csv` — CSV vacío de ejemplo para el usuario.

## Referencias

- `references/formato_csv.md` — columnas, participantes, pesos, monedas, separadores.
- `references/errores.md` — catálogo de errores/advertencias y cómo corregirlos.
- `references/algoritmo.md` — reparto en centavos y transferencias mínimas.

## Requisitos

Python 3.8+ y nada más (solo biblioteca estándar).
