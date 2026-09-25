#!/usr/bin/env python3
"""Flujo completo (el que usa la skill): validar -> liquidar -> reporte.

Uso:
    python dividir_gastos.py gastos.csv --titulo "Viaje a Uyuni" [--personas "Ana,Luis"] [--salida carpeta]

Genera en la carpeta de salida:
    reporte.html           reporte visual autocontenido
    liquidacion.json       datos calculados (montos en centavos)
    resumen_whatsapp.txt   texto listo para pegar en el grupo

Códigos de salida: 0 = OK, 1 = CSV con errores (no genera nada), 2 = archivo no encontrado.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import cargar_tasas, formato  # noqa: E402
from liquidar import liquidar  # noqa: E402
from reporte import construir, resumen_texto  # noqa: E402
from validar import validar  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description="Divide gastos compartidos y genera el reporte.")
    ap.add_argument("csv", help="CSV con columnas: fecha,descripcion,monto,moneda,pagado_por,participantes,categoria")
    ap.add_argument("--titulo", default="Gastos compartidos")
    ap.add_argument("--personas", help="Lista cerrada de personas (detecta nombres mal escritos)")
    ap.add_argument("--tasas", help="tasas_cambio.json alternativo")
    ap.add_argument("--salida", default="salida_gastos")
    a = ap.parse_args(argv)

    tasas = cargar_tasas(a.tasas)
    simbolo = tasas.get("simbolo_base", tasas["moneda_base"])
    personas = [p for p in (a.personas or "").split(",") if p.strip()] or None

    print(f"[1/3] Validando {a.csv} ...")
    gastos, miembros, problemas = validar(a.csv, personas, tasas)
    errores = [p for p in problemas if p.es_error]
    for p in problemas:
        print(("  ERROR  " if p.es_error else "  AVISO  ") + str(p))
    if errores:
        print(f"\nSe encontraron {len(errores)} error(es). No se generó ningún reporte.")
        print("Corrige el CSV y vuelve a ejecutar. Guía: references/errores.md")
        return 2 if any(p.codigo == "E001" for p in errores) else 1
    print(f"  OK: {len(gastos)} gastos, {len(miembros)} personas ({', '.join(miembros)})")

    print("[2/3] Calculando balances y transferencias ...")
    liq = liquidar(gastos, miembros, tasas["moneda_base"])
    liq["advertencias"] = [str(p) for p in problemas]
    for t in liq["transferencias"]:
        print(f"  {t['de']} -> {t['a']}: {formato(t['monto'], simbolo)}")
    if not liq["transferencias"]:
        print("  Todos están a mano.")

    print("[3/3] Generando reporte ...")
    out = Path(a.salida)
    out.mkdir(parents=True, exist_ok=True)
    (out / "liquidacion.json").write_text(json.dumps(liq, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "reporte.html").write_text(construir(liq, a.titulo, Path(a.csv).name, simbolo), encoding="utf-8")
    (out / "resumen_whatsapp.txt").write_text(resumen_texto(liq, a.titulo, simbolo), encoding="utf-8")
    print(f"  Total: {formato(liq['total'], simbolo)}")
    print(f"\nListo. Archivos en {out}/: reporte.html, liquidacion.json, resumen_whatsapp.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
