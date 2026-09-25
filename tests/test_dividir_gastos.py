"""Pruebas de la skill dividir-gastos.

Ejecutar desde la raíz del repositorio:
    python -m unittest discover -s tests -v
"""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPTS = RAIZ / "skills" / "dividir-gastos" / "scripts"
EJEMPLOS = RAIZ / "examples"
sys.path.insert(0, str(SCRIPTS))

import dividir_gastos  # noqa: E402
from liquidar import liquidar, repartir, transferencias_minimas  # noqa: E402
from validar import validar  # noqa: E402

CAB = "fecha,descripcion,monto,moneda,pagado_por,participantes,categoria\n"


def csv_temporal(contenido, encoding="utf-8"):
    f = tempfile.NamedTemporaryFile("wb", suffix=".csv", delete=False)
    f.write(contenido.encode(encoding))
    f.close()
    return f.name


def codigos(problemas):
    return sorted({p.codigo for p in problemas})


def silencioso(fn, *args):
    with redirect_stdout(io.StringIO()) as buf:
        codigo = fn(*args)
    return codigo, buf.getvalue()


class CasoExitoso(unittest.TestCase):
    def test_flujo_completo_viaje_uyuni(self):
        with tempfile.TemporaryDirectory() as out:
            codigo, salida = silencioso(dividir_gastos.main,
                                        [str(EJEMPLOS / "viaje_uyuni.csv"), "--titulo", "Uyuni", "--salida", out])
            self.assertEqual(codigo, 0, salida)
            for nombre in ("reporte.html", "liquidacion.json", "resumen_whatsapp.txt"):
                self.assertTrue((Path(out) / nombre).exists(), nombre)
            liq = json.loads((Path(out) / "liquidacion.json").read_text(encoding="utf-8"))
            self.assertEqual(sum(p["balance"] for p in liq["personas"]), 0)
            self.assertEqual(liq["total"], 516590)  # Bs 5 165.90 (USD a 6.96)
            self.assertLessEqual(len(liq["transferencias"]), len(liq["personas"]) - 1)
            html = (Path(out) / "reporte.html").read_text(encoding="utf-8")
            self.assertIn("Uyuni", html)
            self.assertNotIn("$", html.replace("$ ", ""))  # sin placeholders sin reemplazar

    def test_resultado_esperado_ejemplo_sencillo(self):
        gastos, miembros, problemas = validar(EJEMPLOS / "cena_sencilla.csv")
        self.assertEqual(codigos(problemas), [])
        liq = liquidar(gastos, miembros)
        trans = {(t["de"], t["a"]): t["monto"] for t in liq["transferencias"]}
        self.assertEqual(trans, {("Valeria", "Sofía"): 6083, ("Diego", "Sofía"): 4884})

    def test_transferencias_saldan_todo(self):
        balances = {"A": 5000, "B": -2000, "C": -3000, "D": 0}
        saldo = dict(balances)
        for de, a, m in transferencias_minimas(balances):
            saldo[de] += m
            saldo[a] -= m
        self.assertTrue(all(v == 0 for v in saldo.values()))


class Reparto(unittest.TestCase):
    def test_centavos_no_se_pierden(self):
        partes = repartir(10000, {"A": Decimal(1), "B": Decimal(1), "C": Decimal(1)})
        self.assertEqual(sum(partes.values()), 10000)
        self.assertEqual(sorted(partes.values()), [3333, 3333, 3334])

    def test_pesos(self):
        partes = repartir(24000, {"Ana": Decimal(1), "Luis": Decimal(2), "Carla": Decimal(1)})
        self.assertEqual(partes, {"Ana": 6000, "Luis": 12000, "Carla": 6000})

    def test_moneda_extranjera_y_coma_decimal(self):
        ruta = csv_temporal(CAB + "2026-01-01,x,\"10,5\",USD,Ana,Ana|Luis,comida\n")
        gastos, _, problemas = validar(ruta)
        self.assertEqual(codigos(problemas), [])
        self.assertEqual(gastos[0]["monto_base"], 7308)  # 10.5 * 6.96


class EntradasInvalidas(unittest.TestCase):
    def test_archivo_inexistente_devuelve_2(self):
        codigo, salida = silencioso(dividir_gastos.main, ["no_existe.csv"])
        self.assertEqual(codigo, 2)
        self.assertIn("E001", salida)

    def test_csv_con_errores_no_genera_reporte(self):
        with tempfile.TemporaryDirectory() as out:
            codigo, salida = silencioso(dividir_gastos.main,
                                        [str(EJEMPLOS / "gastos_con_errores.csv"), "--salida", out])
            self.assertEqual(codigo, 1)
            self.assertFalse((Path(out) / "reporte.html").exists())
            for c in ("E004", "E005", "E006", "E009", "E010", "W001", "W002", "W003"):
                self.assertIn(c, salida)

    def test_columnas_faltantes(self):
        _, _, problemas = validar(EJEMPLOS / "columnas_faltantes.csv")
        self.assertEqual(codigos(problemas), ["E003"])

    def test_archivo_vacio_y_solo_cabecera(self):
        self.assertEqual(codigos(validar(csv_temporal(""))[2]), ["E002"])
        self.assertEqual(codigos(validar(csv_temporal(CAB))[2]), ["E002"])

    def test_persona_fuera_de_lista(self):
        ruta = csv_temporal(CAB + "2026-01-01,x,10,BOB,Ana,Ana|Pedro,comida\n")
        _, _, problemas = validar(ruta, personas=["Ana", "Luis"])
        self.assertIn("E007", codigos(problemas))

    def test_participantes_vacio(self):
        ruta = csv_temporal(CAB + "2026-01-01,x,10,BOB,Ana,,comida\n")
        self.assertIn("E008", codigos(validar(ruta)[2]))

    def test_latin1_se_lee_con_advertencia(self):
        ruta = csv_temporal(CAB + "2026-01-01,Café,10,BOB,Sofía,todos,comida\n", encoding="latin-1")
        gastos, miembros, problemas = validar(ruta)
        self.assertEqual(codigos(problemas), ["W004"])
        self.assertEqual(miembros, ["Sofía"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
