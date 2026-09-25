# Cómo se calcula la liquidación

## 1. Todo en centavos enteros

Cada monto se convierte a la moneda base (`monto × tasa`) y se redondea a centavos (redondeo comercial). A partir de ahí se trabaja solo con enteros, así no aparecen errores del tipo `0.1 + 0.2 = 0.30000000000000004` y **la suma de todos los balances es exactamente 0** (el script lo verifica con un `assert`).

## 2. Reparto de cada gasto (método del resto mayor)

Para un gasto de `T` centavos con pesos `w₁…wₙ`:

1. Cada persona recibe `piso(T × wᵢ / Σw)`.
2. Los centavos que sobran (siempre menos que `n`) se dan de a uno a quienes tienen el mayor resto decimal; si hay empate, por orden alfabético.

Ejemplo: Bs 100.00 entre 3 → 3333 + 3333 + 3334 centavos. Nadie pierde ni gana más de 1 centavo y el total cuadra.

## 3. Balance por persona

```
balance = lo que pagó − lo que le corresponde (consumió)
```

- Positivo → el grupo le debe.
- Negativo → debe al grupo.

## 4. Transferencias mínimas (greedy)

1. Ordenar deudores (de mayor a menor deuda) y acreedores (de mayor a menor crédito).
2. El mayor deudor le paga al mayor acreedor `min(deuda, crédito)`.
3. Quien queda en 0 sale de la lista; repetir.

Cada paso deja al menos a una persona en cero, así que con `n` personas hay **como máximo `n − 1` transferencias** (en vez de que cada uno le pague a cada uno por cada gasto).

**Limitación honesta:** encontrar el mínimo absoluto de transferencias es un problema NP-difícil (equivale a buscar subgrupos que sumen cero). El greedy no siempre llega al óptimo, pero garantiza `≤ n − 1`, es determinista y es suficiente para grupos de amigos.

## Por qué estas decisiones

| Decisión | Motivo |
|---|---|
| Solo biblioteca estándar | Se instala copiando la carpeta; nada que falle con `pip`. |
| Validar todo antes de calcular | Un dato malo daría un reparto incorrecto en silencio. |
| Reportar todos los errores juntos | El usuario corrige una sola vez, no error por error. |
| Tasas y categorías en `assets/` | Se cambian sin tocar código. |
| HTML autocontenido | Se abre sin internet y se puede mandar por WhatsApp/correo. |
