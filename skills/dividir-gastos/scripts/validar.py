#!/usr/bin/env python3
"""Paso 1 del flujo: valida un CSV de gastos compartidos.

Uso:
    python validar.py gastos.csv [--personas "Ana,Luis,Mauro"] [--json]

Códigos de salida: 0 = válido (puede tener advertencias), 1 = hay errores,
2 = no se pudo leer el archivo. Catálogo de códigos en references/errores.md
"""
import argparse
import csv
import difflib
import io
import json
import sys
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import COLUMNAS, Problema, a_centavos, cargar_categorias, cargar_tasas  # noqa: E402

TODOS = {"todos", "todas", "all", "*"}


def _leer_texto(ruta, problemas):
    ruta = Path(ruta)
    if not ruta.exists():
        problemas.append(Problema("E001", f"El archivo '{ruta}' no existe."))
        return None
    datos = ruta.read_bytes()
    try:
        return datos.decode("utf-8-sig")
    except UnicodeDecodeError:
        problemas.append(Problema("W004", "El archivo no está en UTF-8; se leyó como Latin-1 (Excel). "
                                          "Revisa tildes y eñes en el reporte."))
        return datos.decode("latin-1")


def _parsear_monto(texto):
    t = texto.strip().replace(" ", "")
    if "," in t and "." in t:          # 1.234,50 o 1,234.50
        if t.rfind(",") > t.rfind("."):
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    elif "," in t:                     # 12,50
        t = t.replace(",", ".")
    return Decimal(t)


def _parsear_participantes(texto):
    """'Ana|Luis:2|Mauro' -> [('Ana',1),('Luis',2),('Mauro',1)] ; 'todos' -> 'TODOS'."""
    t = texto.strip()
    if t.lower() in TODOS:
        return "TODOS"
    salida = []
    for trozo in t.split("|"):
        trozo = trozo.strip()
        if not trozo:
            continue
        if ":" in trozo:
            nombre, peso = trozo.rsplit(":", 1)
            salida.append((nombre.strip(), peso.strip()))
        else:
            salida.append((trozo, "1"))
    return salida


def validar(ruta, personas=None, tasas=None, categorias=None):
    """Devuelve (gastos, miembros, problemas). Si hay errores, gastos puede venir incompleto."""
    tasas = tasas or cargar_tasas()
    categorias = categorias or cargar_categorias()
    problemas = []
    texto = _leer_texto(ruta, problemas)
    if texto is None:
        return [], [], problemas
    if not texto.strip():
        problemas.append(Problema("E002", "El archivo está vacío."))
        return [], [], problemas

    primera = texto.splitlines()[0]
    delim = ";" if primera.count(";") > primera.count(",") else ","
    lector = csv.DictReader(io.StringIO(texto), delimiter=delim)
    cabecera = [(c or "").strip().lower() for c in (lector.fieldnames or [])]
    lector.fieldnames = cabecera
    faltan = [c for c in COLUMNAS if c not in cabecera]
    if faltan:
        problemas.append(Problema("E003", f"Faltan columnas: {', '.join(faltan)}. "
                                          f"Se esperan: {', '.join(COLUMNAS)} (ver assets/plantilla_csv.csv)."))
        return [], [], problemas

    canon = {}  # nombre en minúsculas -> forma canónica (primera vista)
    if personas:
        for p in personas:
            canon.setdefault(p.strip().lower(), p.strip())

    def nombre(n, linea):
        clave = n.strip().lower()
        if personas and clave not in canon:
            problemas.append(Problema("E007", f"'{n.strip()}' no está en la lista de personas "
                                              f"({', '.join(personas)}).", linea))
        return canon.setdefault(clave, n.strip())

    moneda_ok = set(tasas["tasas"])
    cats = categorias["categorias"]
    gastos, vistos = [], {}
    hoy = date.today()

    for i, fila in enumerate(lector, start=2):
        fila = {k: (v or "").strip() for k, v in fila.items() if k}
        if not any(fila.values()):
            continue
        ok = True

        try:
            fecha = datetime.strptime(fila["fecha"], "%Y-%m-%d").date()
            if fecha > hoy:
                problemas.append(Problema("W005", f"La fecha {fecha} está en el futuro.", i))
        except ValueError:
            problemas.append(Problema("E004", f"Fecha inválida '{fila['fecha']}'. Usa AAAA-MM-DD.", i))
            ok, fecha = False, None

        try:
            monto = _parsear_monto(fila["monto"])
            if not monto.is_finite() or monto <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            problemas.append(Problema("E005", f"Monto inválido '{fila['monto']}'. Debe ser un número mayor a 0.", i))
            ok, monto = False, None

        moneda = fila["moneda"].upper() or tasas["moneda_base"]
        if moneda not in moneda_ok:
            problemas.append(Problema("E006", f"Moneda '{moneda}' no soportada. Disponibles: "
                                              f"{', '.join(sorted(moneda_ok))} (edita assets/tasas_cambio.json).", i))
            ok = False

        if not fila["pagado_por"]:
            problemas.append(Problema("E010", "Falta quién pagó (columna pagado_por).", i))
            ok, pagador = False, None
        else:
            pagador = nombre(fila["pagado_por"], i)

        parts = _parsear_participantes(fila["participantes"])
        if parts != "TODOS":
            if not parts:
                problemas.append(Problema("E008", "No hay participantes. Usa 'todos' o 'Ana|Luis'.", i))
                ok = False
            pesos = {}
            for n, p in parts:
                try:
                    peso = Decimal(p)
                    if not peso.is_finite() or peso <= 0:
                        raise InvalidOperation
                except InvalidOperation:
                    problemas.append(Problema("E009", f"Peso inválido '{p}' para {n}. Debe ser un número > 0 (ej. Luis:2).", i))
                    ok = False
                    continue
                cn = nombre(n, i)
                pesos[cn] = pesos.get(cn, Decimal(0)) + peso
            parts = pesos

        cat = fila["categoria"].lower() or categorias["por_defecto"]
        if cat not in cats:
            problemas.append(Problema("W003", f"Categoría '{fila['categoria']}' desconocida; se usa "
                                              f"'{categorias['por_defecto']}'.", i))
            cat = categorias["por_defecto"]

        firma = tuple(fila[c].lower() for c in COLUMNAS)
        if firma in vistos:
            problemas.append(Problema("W001", f"Fila idéntica a la línea {vistos[firma]} (¿gasto duplicado?).", i))
        else:
            vistos[firma] = i

        if ok:
            base = a_centavos(monto * Decimal(str(tasas["tasas"][moneda])))
            if base <= 0:
                problemas.append(Problema("E005", f"El monto convertido a {tasas['moneda_base']} es 0.", i))
                continue
            gastos.append({
                "linea": i, "fecha": fecha.isoformat(), "descripcion": fila["descripcion"] or "(sin descripción)",
                "monto_original": str(monto), "moneda": moneda, "monto_base": base,
                "pagado_por": pagador, "participantes": parts, "categoria": cat,
            })

    if not gastos and not any(p.es_error for p in problemas):
        problemas.append(Problema("E002", "El archivo tiene cabecera pero ninguna fila de gastos."))

    miembros = list(dict.fromkeys(canon.values()))
    for g in gastos:  # resolver 'todos' con la lista final de miembros
        if g["participantes"] == "TODOS":
            g["participantes"] = {m: Decimal(1) for m in miembros}

    # Nombres muy parecidos: probable error de tipeo (Mauro vs Mauor)
    for a_i, a in enumerate(miembros):
        for b in miembros[a_i + 1:]:
            if difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio() >= 0.8:
                problemas.append(Problema("W002", f"'{a}' y '{b}' se parecen mucho. ¿Es la misma persona?"))

    return gastos, miembros, problemas


def main(argv=None):
    ap = argparse.ArgumentParser(description="Valida un CSV de gastos compartidos.")
    ap.add_argument("csv")
    ap.add_argument("--personas", help="Lista cerrada de personas separadas por coma")
    ap.add_argument("--tasas", help="Ruta a un tasas_cambio.json alternativo")
    ap.add_argument("--json", action="store_true", help="Imprime el resultado en JSON")
    a = ap.parse_args(argv)
    personas = [p for p in (a.personas or "").split(",") if p.strip()] or None
    gastos, miembros, problemas = validar(a.csv, personas, cargar_tasas(a.tasas) if a.tasas else None)
    errores = [p for p in problemas if p.es_error]
    if a.json:
        print(json.dumps({"valido": not errores, "gastos": len(gastos), "personas": miembros,
                          "problemas": [p.a_dict() for p in problemas]}, ensure_ascii=False, indent=2))
    else:
        for p in problemas:
            print(("ERROR   " if p.es_error else "AVISO   ") + str(p))
        estado = "INVÁLIDO" if errores else "VÁLIDO"
        print(f"\n{estado}: {len(gastos)} gastos correctos, {len(errores)} errores, "
              f"{len(problemas) - len(errores)} advertencias. Personas: {', '.join(miembros) or '-'}")
    if any(p.codigo == "E001" for p in problemas):
        return 2
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
