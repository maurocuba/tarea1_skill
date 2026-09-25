#!/usr/bin/env python3
"""Paso 2 del flujo: reparte cada gasto y calcula quién le paga a quién.

Uso:
    python liquidar.py gastos.csv [--personas "Ana,Luis"] [-o liquidacion.json]

Trabaja con centavos enteros para que la suma de balances sea exactamente 0.
Algoritmo explicado en references/algoritmo.md
"""
import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import cargar_tasas  # noqa: E402
from validar import validar  # noqa: E402


def repartir(total, pesos):
    """Divide `total` centavos según `pesos` {nombre: Decimal}.

    Método del resto mayor: cada uno recibe el piso de su parte y los centavos
    sobrantes van a quienes tienen el mayor resto (desempate por nombre).
    La suma devuelta es exactamente `total`.
    """
    suma = sum(pesos.values())
    base, restos = {}, []
    for n, w in pesos.items():
        exacto = Decimal(total) * w / suma
        piso = int(exacto)
        base[n] = piso
        restos.append((exacto - piso, n))
    sobrante = total - sum(base.values())
    for _, n in sorted(restos, key=lambda r: (-r[0], r[1]))[:sobrante]:
        base[n] += 1
    return base


def transferencias_minimas(balances):
    """Greedy: el mayor deudor le paga al mayor acreedor hasta saldar.

    Produce como máximo (n - 1) transferencias. Entrada: {nombre: centavos}
    (positivo = le deben). Devuelve lista de (de, a, centavos).
    """
    deudores = sorted(([-b, n] for n, b in balances.items() if b < 0), key=lambda x: (-x[0], x[1]))
    acreedores = sorted(([b, n] for n, b in balances.items() if b > 0), key=lambda x: (-x[0], x[1]))
    salida, i, j = [], 0, 0
    while i < len(deudores) and j < len(acreedores):
        monto = min(deudores[i][0], acreedores[j][0])
        salida.append((deudores[i][1], acreedores[j][1], monto))
        deudores[i][0] -= monto
        acreedores[j][0] -= monto
        if deudores[i][0] == 0:
            i += 1
        if acreedores[j][0] == 0:
            j += 1
    return salida


def liquidar(gastos, miembros, moneda_base="BOB"):
    pagado = {m: 0 for m in miembros}
    consumido = {m: 0 for m in miembros}
    por_categoria = {}
    detalle = []
    for g in gastos:
        partes = repartir(g["monto_base"], g["participantes"])
        pagado[g["pagado_por"]] += g["monto_base"]
        for n, c in partes.items():
            consumido[n] += c
        por_categoria[g["categoria"]] = por_categoria.get(g["categoria"], 0) + g["monto_base"]
        detalle.append({**g, "participantes": {k: str(v) for k, v in g["participantes"].items()},
                        "partes": partes})

    balances = {m: pagado[m] - consumido[m] for m in miembros}
    assert sum(balances.values()) == 0, "Los balances no cuadran (no debería pasar)"
    trans = transferencias_minimas(balances)
    return {
        "moneda_base": moneda_base,
        "unidad": "centavos",
        "total": sum(g["monto_base"] for g in gastos),
        "personas": [{"nombre": m, "pagado": pagado[m], "consumido": consumido[m],
                      "balance": balances[m]} for m in miembros],
        "transferencias": [{"de": d, "a": a, "monto": c} for d, a, c in trans],
        "por_categoria": dict(sorted(por_categoria.items(), key=lambda kv: -kv[1])),
        "gastos": detalle,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Calcula la liquidación de gastos compartidos.")
    ap.add_argument("csv")
    ap.add_argument("--personas")
    ap.add_argument("--tasas")
    ap.add_argument("-o", "--salida", help="Archivo JSON de salida (por defecto imprime en pantalla)")
    a = ap.parse_args(argv)
    tasas = cargar_tasas(a.tasas)
    personas = [p for p in (a.personas or "").split(",") if p.strip()] or None
    gastos, miembros, problemas = validar(a.csv, personas, tasas)
    errores = [p for p in problemas if p.es_error]
    if errores:
        for p in errores:
            print("ERROR   " + str(p), file=sys.stderr)
        print("\nCorrige el CSV (ver validar.py) antes de liquidar.", file=sys.stderr)
        return 1
    res = liquidar(gastos, miembros, tasas["moneda_base"])
    texto = json.dumps(res, ensure_ascii=False, indent=2)
    if a.salida:
        Path(a.salida).write_text(texto, encoding="utf-8")
        print(f"Liquidación guardada en {a.salida}")
    else:
        print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
