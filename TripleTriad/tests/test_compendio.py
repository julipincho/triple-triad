"""Tests del Compendio dual: 250 entradas generadas de las cartas reales.

La propiedad que mas importa aca es la sincronia: el compendio se construye a
partir de `mazos.TODOS`, asi que si el pool de cartas cambia, el indice tiene
que seguir pegado. Hay tests devoted a eso.
"""

import os
import sys
import tempfile
import unittest

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_tests")
)
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import campana
import compendio
import facciones
import mazos
from reglas import rareza


class TestIndiceSincronizadoConElPool(unittest.TestCase):
    """El compendio se deriva de las cartas reales: no puede desfasarse."""

    def test_una_entrada_por_carta_del_juego(self):
        self.assertEqual(compendio.total(), len(mazos.TODOS_FLAT)
                         if hasattr(mazos, "TODOS_FLAT") else 250)

    def test_todas_las_cartas_tienen_entrada(self):
        faltantes = [c.nombre for lista in mazos.TODOS.values() for c in lista
                     if c.nombre not in compendio.ENTRADAS]
        self.assertEqual(faltantes, [], f"cartas sin entrada: {faltantes[:5]}")

    def test_no_hay_entradas_de_carta_inexistente(self):
        reales = {c.nombre for lista in mazos.TODOS.values() for c in lista}
        self.assertEqual(set(compendio.ENTRADAS) - reales, set())

    def test_las_entradas_declaran_su_faccion(self):
        for nombre, e in compendio.ENTRADAS.items():
            self.assertIn(e["faccion"], facciones.FACCIONES, nombre)
            reales = {c.nombre: c for lista in mazos.TODOS.values() for c in lista}
            self.assertEqual(reales[nombre].bando, e["faccion"], nombre)

    def test_las_entradas_declaran_su_rareza_real(self):
        reales = {c.nombre: rareza(c)[0] for lista in mazos.TODOS.values()
                  for c in lista}
        for nombre, e in compendio.ENTRADAS.items():
            self.assertEqual(e["rareza"], reales[nombre], nombre)

    def test_diez_cartas_por_faccion(self):
        for bando in facciones.orden_facciones():
            self.assertEqual(len(compendio.por_faccion(bando)), 25, bando)


class TestDescripcionesDuales(unittest.TestCase):
    def test_toda_entrada_tiene_las_dos_versiones(self):
        for nombre, e in compendio.ENTRADAS.items():
            self.assertTrue(e["juego"].strip(), f"{nombre}: sin version de juego")
            self.assertTrue(e["verdad"].strip(), f"{nombre}: sin verdad")

    def test_la_version_del_juego_difiere_de_la_verdad(self):
        """Si fueran iguales, el dual no estaria contando nada."""
        iguales = [n for n, e in compendio.ENTRADAS.items() if e["juego"] == e["verdad"]]
        self.assertEqual(iguales, [])

    def test_la_version_del_juego_nombra_la_carta(self):
        for nombre, e in compendio.ENTRADAS.items():
            self.assertTrue(e["juego"].startswith(nombre),
                            f"{nombre}: la version del juego no la nombra")

    def test_las_diez_facciones_tienen_su_propia_mentira(self):
        verdades = set()
        for bando in facciones.orden_facciones():
            self.assertTrue(compendio.MENTIRA_FACCION[bando]["juego"], bando)
            self.assertTrue(compendio.MENTIRA_FACCION[bando]["verdad"], bando)
            self.assertTrue(compendio.MENTIRA_FACCION[bando]["tema"], bando)
            verdades.add(compendio.MENTIRA_FACCION[bando]["verdad"])
        self.assertEqual(len(verdades), 10, "dos facciones comparten la misma verdad")

    def test_las_verdades_nombradas_apuntan_a_cartas_reales(self):
        """Se escribieron seis claves con nombres de duelista, no de carta."""
        huerfanas = [n for n in compendio.VERDADES_NOMBRADAS
                     if n not in compendio.ENTRADAS]
        self.assertEqual(huerfanas, [], f"verdades sin carta: {huerfanas}")

    def test_hay_una_verdad_nombrada_por_faccion(self):
        por_faccion = {}
        for nombre, e in compendio.ENTRADAS.items():
            if e["verdad_nombrada"]:
                por_faccion.setdefault(e["faccion"], []).append(nombre)
        for bando in facciones.orden_facciones():
            self.assertTrue(por_faccion.get(bando), f"{bando}: sin verdad nombrada")

    def test_las_rareza_marca_el_peso_de_la_historia(self):
        for nombre, e in compendio.ENTRADAS.items():
            if e["rareza"] == "LEGENDARIA":
                self.assertIn("pesa mas", e["verdad"], nombre)
            elif e["rareza"] == "RARA":
                self.assertIn("medio contarse", e["verdad"], nombre)


class TestRevelacionEnElEstado(unittest.TestCase):
    def test_revelar_agrega_una_historia(self):
        e = campana.nueva_campana("humano")
        self.assertEqual(campana.compendio_progreso(e), (0, 250))
        campana.compendio_revelar(e, "Rey Aldric")
        self.assertEqual(campana.compendio_progreso(e), (1, 250))

    def test_no_cuenta_dos_veces(self):
        e = campana.nueva_campana("humano")
        campana.compendio_revelar(e, "Rey Aldric")
        campana.compendio_revelar(e, "Rey Aldric")
        self.assertEqual(e["compendio"].count("Rey Aldric"), 1)

    def test_revelar_sube_el_conocimiento_del_umbral(self):
        e = campana.nueva_campana("humano")
        antes = campana.conocimiento_umbral(e)
        campana.compendio_revelar(e, "Rey Aldric")
        self.assertEqual(campana.conocimiento_umbral(e), antes + 1)

    def test_revelar_dos_veces_no_sube_dos_veces(self):
        e = campana.nueva_campana("humano")
        campana.compendio_revelar(e, "Rey Aldric")
        campana.compendio_revelar(e, "Rey Aldric")
        self.assertEqual(campana.conocimiento_umbral(e), 1)

    def test_carta_inexistente_no_rompe(self):
        e = campana.nueva_campana("humano")
        self.assertIsNone(campana.compendio_revelar(e, "no-existe"))
        self.assertEqual(e["compendio"], [])

    def test_el_conocimiento_tiene_tope(self):
        e = campana.nueva_campana("humano")
        for nombre in list(compendio.ENTRADAS)[:40]:
            campana.compendio_revelar(e, nombre)
        self.assertLessEqual(campana.conocimiento_umbral(e), 5)

    def test_la_partida_nueva_arranca_sin_historias(self):
        e = campana.nueva_campana("goblin")
        self.assertEqual(e["compendio"], [])
        self.assertEqual(campana.compendio_historias(e), [])

    def test_migrar_una_partida_vieja_agrega_el_campo(self):
        vieja = campana.nueva_campana("orco")
        vieja["version"] = 6
        vieja.pop("compendio", None)
        vieja["ruta"] = ["senda"]
        nueva = campana._migrar(vieja)
        self.assertEqual(nueva["compendio"], [])
        self.assertEqual(nueva["ruta"], ["senda"], "la migracion perdio progreso")


class TestTextoAscii(unittest.TestCase):
    """El texto que escribimos nosotros es ASCII.

    Los NOMBRES de carta no se comprueban aqui: 24 de ellos llevan tilde y son
    dato preexistente de `mazos.py`, no texto nuevo. La fuente PressStart2P
    dibuja las tildes igual, asi que no son un problema de render.
    """

    def test_el_texto_autorado_es_ascii(self):
        for nombre, e in compendio.ENTRADAS.items():
            # la verdad es 100% nuestra
            for ch in e["verdad"]:
                self.assertLessEqual(ord(ch), 127, f"{nombre}/verdad: {ch!r}")
            # la version del juego es el nombre (puede traer tilde) + la mentira
            sufijo = e["juego"][len(nombre):]
            for ch in sufijo:
                self.assertLessEqual(ord(ch), 127, f"{nombre}/juego: {ch!r}")
        for bando, d in compendio.MENTIRA_FACCION.items():
            for campo in ("tema", "juego", "verdad"):
                for ch in d[campo]:
                    self.assertLessEqual(ord(ch), 127, f"{bando}/{campo}: {ch!r}")

    def test_los_identificadores_no_llevan_espacios_rareza(self):
        """Los ids de revelacion se comparan como cadenas: no deben traer basura."""
        for bando, d in compendio.MENTIRA_FACCION.items():
            rid = d["revelacion"]
            self.assertTrue(rid.startswith("comp_"), rid)
            self.assertEqual(rid, rid.strip())
            self.assertNotIn(" ", rid, rid)


class TestSinCiclos(unittest.TestCase):
    def test_compendio_no_importa_campana(self):
        with open(os.path.join(RAIZ, "compendio.py"), encoding="utf-8") as fh:
            for linea in fh:
                limpio = linea.strip()
                if limpio.startswith(("import ", "from ")):
                    self.assertNotIn(" campana", " " + limpio, limpio)


if __name__ == "__main__":
    unittest.main()
