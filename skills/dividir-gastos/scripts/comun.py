"""Utilidades compartidas por los scripts de la skill dividir-gastos.

Solo usa la biblioteca estándar de Python (3.8+).
"""
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS = SKILL_DIR / "assets"

COLUMNAS = ["fecha", "descripcion", "monto", "moneda", "pagado_por", "participantes", "categoria"]


class Problema:
    """Un error (E###) o advertencia (W###) encontrado al validar."""

    def __init__(self, codigo, mensaje, linea=None):
        self.codigo = codigo
        self.mensaje = mensaje
        self.linea = linea

    @property
    def es_error(self):
        return self.codigo.startswith("E")

    def a_dict(self):
        return {"codigo": self.codigo, "linea": self.linea, "mensaje": self.mensaje}

    def __str__(self):
        donde = f"línea {self.linea}: " if self.linea else ""
        return f"[{self.codigo}] {donde}{self.mensaje}"


def cargar_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def cargar_tasas(ruta=None):
    return cargar_json(ruta or ASSETS / "tasas_cambio.json")


def cargar_categorias(ruta=None):
    return cargar_json(ruta or ASSETS / "categorias.json")


def a_centavos(valor):
    """Decimal -> entero en centavos, redondeo comercial."""
    return int((Decimal(valor) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def formato(centavos, simbolo="Bs"):
    """12345 -> 'Bs 123.45' ; -500 -> '-Bs 5.00'."""
    signo = "-" if centavos < 0 else ""
    c = abs(centavos)
    entero = f"{c // 100:,}".replace(",", " ")
    return f"{signo}{simbolo} {entero}.{c % 100:02d}"
