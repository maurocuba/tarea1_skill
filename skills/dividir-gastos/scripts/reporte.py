#!/usr/bin/env python3
"""Paso 3 del flujo: genera el reporte HTML y el resumen para WhatsApp.

Uso:
    python reporte.py liquidacion.json [--titulo "Viaje"] [--salida carpeta]

Usa assets/plantilla_reporte.html, assets/plantilla_resumen.txt y
assets/categorias.json. El HTML es autocontenido (sin internet).
"""
import argparse
import html
import json
import sys
from datetime import datetime
from pathlib import Path
from string import Template

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import ASSETS, cargar_categorias, cargar_tasas, formato  # noqa: E402

PALETA_PERSONAS = "#1F6F5C"


def _barras(items, total, simbolo):
    """items: lista de (etiqueta, centavos, color). Barras horizontales en HTML/CSS."""
    if not items:
        return "<p>Sin datos.</p>"
    maximo = max(c for _, c, _ in items) or 1
    filas = []
    for etiqueta, c, color in items:
        pct = 100 * c / maximo
        share = 100 * c / total if total else 0
        filas.append(
            f'<div class="bar-row"><span>{html.escape(etiqueta)}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div></div>'
            f'<span class="n">{formato(c, simbolo)} <small>({share:.0f}%)</small></span></div>')
    return "\n".join(filas)


def construir(liq, titulo, archivo="", simbolo="Bs", categorias=None):
    categorias = categorias or cargar_categorias()
    cats = categorias["categorias"]
    esc = html.escape
    f = lambda c: formato(c, simbolo)  # noqa: E731

    # Transferencias
    if liq["transferencias"]:
        trans_html = "\n".join(
            f'<div class="transfer"><strong>{esc(t["de"])}</strong><span class="arrow">paga a</span>'
            f'<strong>{esc(t["a"])}</strong><span class="amt">{f(t["monto"])}</span></div>'
            for t in liq["transferencias"])
    else:
        trans_html = "<p>Todos están a mano. No hace falta ninguna transferencia.</p>"

    # Balances
    filas_bal = []
    for p in sorted(liq["personas"], key=lambda p: -p["balance"]):
        clase = "pos" if p["balance"] > 0 else "neg" if p["balance"] < 0 else ""
        filas_bal.append(f'<tr><td>{esc(p["nombre"])}</td><td class="n">{f(p["pagado"])}</td>'
                         f'<td class="n">{f(p["consumido"])}</td><td class="n {clase}">{f(p["balance"])}</td></tr>')

    # Gráficos
    g_cat = _barras([(cats[k]["etiqueta"], v, cats[k]["color"]) for k, v in liq["por_categoria"].items()],
                    liq["total"], simbolo)
    g_per = _barras(sorted(((p["nombre"], p["consumido"], PALETA_PERSONAS) for p in liq["personas"]),
                           key=lambda x: -x[1]), liq["total"], simbolo)

    # Detalle
    filas_g = []
    for g in sorted(liq["gastos"], key=lambda g: (g["fecha"], g["linea"])):
        c = cats[g["categoria"]]
        parts = ", ".join(n if _es_peso_uno(w) else f"{n}×{w}" for n, w in g["participantes"].items())
        filas_g.append(
            f'<tr><td>{g["fecha"]}</td><td>{esc(g["descripcion"])}</td>'
            f'<td><span class="pill" style="background:{c["color"]}">{esc(c["etiqueta"])}</span></td>'
            f'<td>{esc(g["pagado_por"])}</td><td>{esc(parts)}</td>'
            f'<td class="n">{g["monto_original"]} {g["moneda"]}</td><td class="n">{f(g["monto_base"])}</td></tr>')

    avisos = liq.get("advertencias") or []
    avisos_html = ""
    if avisos:
        avisos_html = ('<div class="warn"><strong>Advertencias al validar</strong><ul>'
                       + "".join(f"<li>{esc(a)}</li>" for a in avisos) + "</ul></div>")

    plantilla = Template((ASSETS / "plantilla_reporte.html").read_text(encoding="utf-8"))
    return plantilla.safe_substitute(
        titulo=esc(titulo), fecha_generado=datetime.now().strftime("%Y-%m-%d %H:%M"),
        moneda_base=liq["moneda_base"], archivo=esc(archivo), total=f(liq["total"]),
        n_gastos=len(liq["gastos"]), n_personas=len(liq["personas"]),
        n_transferencias=len(liq["transferencias"]), advertencias=avisos_html,
        filas_transferencias=trans_html, filas_balances="\n".join(filas_bal),
        grafico_categorias=g_cat, grafico_personas=g_per, filas_gastos="\n".join(filas_g))


def _es_peso_uno(w):
    try:
        return float(w) == 1.0
    except ValueError:
        return False


def resumen_texto(liq, titulo, simbolo="Bs"):
    f = lambda c: formato(c, simbolo)  # noqa: E731
    bal = "\n".join(
        f"- {p['nombre']}: pagó {f(p['pagado'])}, le toca {f(p['consumido'])} → "
        + ("le deben " + f(p["balance"]) if p["balance"] > 0 else
           "debe " + f(-p["balance"]) if p["balance"] < 0 else "a mano")
        for p in liq["personas"])
    trans = "\n".join(f"{i}. {t['de']} → {t['a']}: {f(t['monto'])}"
                      for i, t in enumerate(liq["transferencias"], 1)) or "Todos están a mano."
    plantilla = Template((ASSETS / "plantilla_resumen.txt").read_text(encoding="utf-8"))
    return plantilla.safe_substitute(titulo=titulo, total=f(liq["total"]), n_gastos=len(liq["gastos"]),
                                     n_personas=len(liq["personas"]), balances=bal, transferencias=trans)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Genera reporte HTML y resumen desde una liquidación JSON.")
    ap.add_argument("liquidacion")
    ap.add_argument("--titulo", default="Gastos compartidos")
    ap.add_argument("--salida", default=".")
    a = ap.parse_args(argv)
    ruta = Path(a.liquidacion)
    if not ruta.exists():
        print(f"ERROR   El archivo '{ruta}' no existe. Genera uno con liquidar.py -o", file=sys.stderr)
        return 2
    try:
        liq = json.loads(ruta.read_text(encoding="utf-8"))
        liq["personas"], liq["transferencias"], liq["gastos"]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"ERROR   '{ruta}' no es una liquidación válida ({e}).", file=sys.stderr)
        return 1
    simbolo = cargar_tasas().get("simbolo_base", liq["moneda_base"])
    out = Path(a.salida)
    out.mkdir(parents=True, exist_ok=True)
    (out / "reporte.html").write_text(construir(liq, a.titulo, ruta.name, simbolo), encoding="utf-8")
    (out / "resumen_whatsapp.txt").write_text(resumen_texto(liq, a.titulo, simbolo), encoding="utf-8")
    print(f"Reporte: {out / 'reporte.html'}\nResumen: {out / 'resumen_whatsapp.txt'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
