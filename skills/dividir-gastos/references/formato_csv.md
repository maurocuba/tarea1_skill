# Formato del CSV de gastos

Una fila por gasto. La primera fila es la cabecera (sin importar mayúsculas):

| Columna | Obligatoria | Ejemplo | Reglas |
|---|---|---|---|
| `fecha` | sí | `2026-08-15` | Formato `AAAA-MM-DD`. Fecha futura → advertencia W005. |
| `descripcion` | no | `Almuerzo en Colchani` | Texto libre. |
| `monto` | sí | `210.50` / `210,50` / `1.234,50` | Número mayor a 0. Acepta punto o coma decimal. |
| `moneda` | no | `BOB`, `USD` | Debe existir en `assets/tasas_cambio.json`. Vacía = moneda base. |
| `pagado_por` | sí | `Ana` | Una sola persona. |
| `participantes` | sí | `todos` / `Ana\|Luis` / `Ana\|Luis:2` | Ver abajo. |
| `categoria` | no | `comida` | Debe existir en `assets/categorias.json`; si no, se usa `otros` (W003). |

## Participantes y pesos

- `todos` (o `todas`, `*`): se divide entre **todas** las personas que aparecen en el archivo (o las de `--personas`).
- `Ana|Luis|Carla`: se divide en partes iguales solo entre ellos. El separador es la barra vertical `|`.
- `Ana|Luis:2|Carla`: pesos. Luis paga el doble que Ana y Carla (ej. pidió dos platos). Los pesos pueden ser decimales (`Ana:1.5`).
- Quien pagó no tiene que estar entre los participantes (ej. pagó un regalo para otros).

## Nombres

- Se comparan sin distinguir mayúsculas: `ana` y `Ana` son la misma persona (se usa la primera forma escrita).
- Nombres muy parecidos (`Mauro` / `Mauor`) generan la advertencia W002.
- Con `--personas "Ana,Luis"` cualquier otro nombre es error E007.

## Separador

Se detecta solo: coma (`,`) o punto y coma (`;`, típico de Excel en español). Con `;` puedes usar coma decimal sin comillas.

## Codificación

UTF-8 recomendado. Si el archivo viene de Excel en Latin-1 se lee igual con la advertencia W004.
